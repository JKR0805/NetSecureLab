from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from app.database.connection import SessionLocal
from app.models.scan import Scan
from app.models.target import Target
from app.config import settings
from app.utils.target_normalizer import TargetNormalizer, NormalizedTarget
from app.services.nmap.executor import execute_nmap_scan, execute_os_detection
from app.services.nmap.parser import parse_nmap_xml
from app.services.nmap.normalizer import normalize_and_store_nmap_results
from app.services.dns.service import collect_and_store_dns
from app.services.recon.service import collect_and_store_recon
from app.services.findings.engine import run_finding_engine
from app.services.web_security.scanner import run_web_assessment
from app.utils.logger import logger
from app.utils.event_manager import event_manager

def notify_scan_event(scan: Scan):
    try:
        event_manager.broadcast_sync({
            "event": "scan_status",
            "scan_id": scan.id,
            "target_id": scan.target_id,
            "status": scan.status,
            "nmap_status": scan.nmap_status,
            "dns_status": scan.dns_status,
            "recon_status": scan.recon_status,
            "duration": scan.duration,
            "error_message": scan.error_message,
        })
    except Exception:
        pass

def run_scan(scan_id: int):
    """
    Central scan orchestration workflow executed inside the worker thread.
    Coordinates independent collection modules, normalizes data, and runs finding engine.
    """
    db: Session = SessionLocal()
    start_time = datetime.now(timezone.utc)

    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            logger.error(f"Orchestrator: Scan id={scan_id} not found.")
            return

        # Check if already cancelled while queued
        if scan.cancel_requested or scan.status == "cancelled":
            scan.status = "cancelled"
            scan.completed_at = datetime.now(timezone.utc)
            scan.duration = 0.0
            db.commit()
            notify_scan_event(scan)
            logger.info(f"Scan {scan_id} was cancelled before execution started.")
            return

        target: Target = scan.target
        if not target:
            scan.status = "failed"
            scan.error_message = "Target record missing for this scan"
            db.commit()
            return

        # Double-check authorization technical control
        if not target.authorization_confirmed:
            scan.status = "failed"
            scan.error_message = "Scan aborted: target authorization is not confirmed"
            db.commit()
            logger.warning(f"Scan {scan_id} aborted: unauthorized target")
            return

        # 1. Update status to running
        scan.status = "running"
        scan.started_at = start_time
        db.commit()
        notify_scan_event(scan)

        # 2. Canonical target normalization
        normalized: NormalizedTarget = TargetNormalizer.normalize(target.target, target.target_type)
        logger.info(
            f"Starting scan {scan_id} for target '{target.target}' (type={target.target_type}, scan_target='{normalized.scan_target}')"
        )

        # Output paths
        xml_path = settings.SCANS_DIR / f"{scan_id}.xml"
        os_xml_path = settings.SCANS_DIR / f"{scan_id}_os.xml"

        # -------------------------------------------------------------
        # STAGE 1: Nmap Network Discovery & Service Enumeration
        # -------------------------------------------------------------
        logger.info(f"[Scan {scan_id}] Stage 1: Running Nmap ({scan.profile})...")
        nmap_result = execute_nmap_scan(
            scan_target=normalized.scan_target,
            profile=scan.profile,
            output_xml_path=xml_path,
            timeout=settings.SCAN_TIMEOUT,
        )

        if nmap_result.success and xml_path.exists():
            scan.nmap_status = "success"
            scan.raw_output_path = str(xml_path)
            parsed_data = parse_nmap_xml(xml_path)
            normalize_and_store_nmap_results(scan_id, parsed_data, db)
            db.commit()

            # Optional OS detection pass for 'full' profile
            if scan.profile == "full" and settings.OS_DETECTION_ENABLED:
                logger.info(f"[Scan {scan_id}] Running secondary OS detection pass...")
                os_result = execute_os_detection(
                    scan_target=normalized.scan_target,
                    output_xml_path=os_xml_path,
                    timeout=settings.SCAN_TIMEOUT,
                )
                if os_result.success and os_xml_path.exists():
                    os_parsed = parse_nmap_xml(os_xml_path)
                    # Merge OS findings
                    for h in os_parsed.get("hosts", []):
                        if h.get("os"):
                            for asset in scan.assets:
                                if asset.ip == h.get("ip"):
                                    asset.os = h.get("os")
                    db.commit()
        else:
            scan.nmap_status = "failed"
            scan.error_message = nmap_result.error_message
            logger.warning(f"[Scan {scan_id}] Nmap execution failed: {nmap_result.error_message}")
            db.commit()

        # Cancellation check between stages
        db.refresh(scan)
        if scan.cancel_requested:
            scan.status = "cancelled"
            scan.completed_at = datetime.now(timezone.utc)
            scan.duration = (scan.completed_at - start_time).total_seconds()
            db.commit()
            logger.info(f"[Scan {scan_id}] Cancelled between Nmap and DNS stages.")
            return

        # -------------------------------------------------------------
        # STAGE 2: DNS Intelligence (Independent module)
        # -------------------------------------------------------------
        logger.info(f"[Scan {scan_id}] Stage 2: DNS Intelligence...")
        try:
            dns_status = collect_and_store_dns(target.id, scan_id, normalized, db)
            scan.dns_status = dns_status
        except Exception as e:
            logger.error(f"[Scan {scan_id}] DNS collection uncaught error: {e}")
            scan.dns_status = "failed"
        db.commit()

        # Cancellation check between stages
        db.refresh(scan)
        if scan.cancel_requested:
            scan.status = "cancelled"
            scan.completed_at = datetime.now(timezone.utc)
            scan.duration = (scan.completed_at - start_time).total_seconds()
            db.commit()
            logger.info(f"[Scan {scan_id}] Cancelled between DNS and Recon stages.")
            return

        # -------------------------------------------------------------
        # STAGE 3: Passive Reconnaissance (Independent module)
        # -------------------------------------------------------------
        logger.info(f"[Scan {scan_id}] Stage 3: Passive Reconnaissance...")
        try:
            recon_status = collect_and_store_recon(target.id, scan_id, normalized, db)
            scan.recon_status = recon_status
        except Exception as e:
            logger.error(f"[Scan {scan_id}] Recon uncaught error: {e}")
            scan.recon_status = "failed"
        db.commit()

        # Cancellation check between stages
        db.refresh(scan)
        if scan.cancel_requested:
            scan.status = "cancelled"
            scan.completed_at = datetime.now(timezone.utc)
            scan.duration = (scan.completed_at - start_time).total_seconds()
            db.commit()
            notify_scan_event(scan)
            logger.info(f"[Scan {scan_id}] Cancelled between Recon and Finding Engine stages.")
            return

        # -------------------------------------------------------------
        # STAGE 4: Rule-based Finding Engine
        # -------------------------------------------------------------
        logger.info(f"[Scan {scan_id}] Stage 4: Running Finding Engine...")
        try:
            run_finding_engine(scan_id, db)
        except Exception as e:
            logger.error(f"[Scan {scan_id}] Finding engine error: {e}")

        # -------------------------------------------------------------
        # STAGE 5: Web Application Security Assessment (ZAP Module)
        # -------------------------------------------------------------
        if scan.profile in ("standard", "full") or getattr(target, "target_type", "") in ("domain", "hostname", "web_application"):
            logger.info(f"[Scan {scan_id}] Stage 5: Running Web Security Assessment...")
            try:
                run_web_assessment(scan_id, db)
            except Exception as e:
                logger.error(f"[Scan {scan_id}] Web security assessment error: {e}")

        # Scan completion
        end_time = datetime.now(timezone.utc)
        scan.completed_at = end_time
        scan.duration = round((end_time - start_time).total_seconds(), 2)

        # Mark completed unless Nmap timed out or was completely fatal
        if scan.nmap_status == "failed" and scan.dns_status in ("failed", "skipped") and scan.recon_status in ("failed", "skipped"):
            scan.status = "failed"
        else:
            scan.status = "completed"

        db.commit()
        notify_scan_event(scan)
        logger.info(
            f"[Scan {scan_id}] Finished with status={scan.status} in {scan.duration}s. "
            f"(Nmap: {scan.nmap_status}, DNS: {scan.dns_status}, Recon: {scan.recon_status})"
        )

    except Exception as e:
        logger.exception(f"Unhandled exception in scan orchestrator for scan {scan_id}: {e}")
        try:
            scan = db.query(Scan).filter(Scan.id == scan_id).first()
            if scan:
                scan.status = "failed"
                scan.error_message = f"Internal orchestrator error: {str(e)}"
                scan.completed_at = datetime.now(timezone.utc)
                scan.duration = round((scan.completed_at - start_time).total_seconds(), 2)
                db.commit()
                notify_scan_event(scan)
        except Exception:
            pass
    finally:
        db.close()
