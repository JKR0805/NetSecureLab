from typing import List
from sqlalchemy.orm import Session
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.dns_record import DNSRecord
from app.models.recon_result import ReconResult
from app.models.finding import Finding
from app.services.findings.rules import RULES_CATALOG
from app.utils.logger import logger

def run_finding_engine(scan_id: int, db: Session) -> List[Finding]:
    """
    Executes the rule-based security assessment engine.
    Ensures findings are evidence-backed and skip rules when required modules failed.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        logger.error(f"Scan {scan_id} not found for finding engine")
        return []

    # Load normalized datasets
    assets = db.query(Asset).filter(Asset.scan_id == scan_id).all()
    dns_records = db.query(DNSRecord).filter(DNSRecord.scan_id == scan_id).all()
    recon_results = db.query(ReconResult).filter(ReconResult.scan_id == scan_id).all()

    context = {
        "scan": scan,
        "target": scan.target,
        "assets": assets,
        "dns_records": dns_records,
        "recon_results": recon_results,
    }

    generated_findings = []

    for rule in RULES_CATALOG:
        # Check module readiness
        if rule.required_module == "nmap" and scan.nmap_status != "success":
            logger.info(f"Skipping rule {rule.id} ({rule.name}): Nmap status is '{scan.nmap_status}'")
            continue

        if rule.required_module == "dns" and scan.dns_status not in ("success", "partial"):
            logger.info(f"Skipping rule {rule.id} ({rule.name}): DNS status is '{scan.dns_status}'")
            continue

        if rule.required_module == "recon" and scan.recon_status not in ("success", "partial"):
            logger.info(f"Skipping rule {rule.id} ({rule.name}): Recon status is '{scan.recon_status}'")
            continue

        try:
            rule_findings = rule.check_function(context)
            for f_dict in rule_findings:
                finding = Finding(
                    scan_id=scan_id,
                    asset_id=f_dict.get("asset_id"),
                    rule_id=f_dict["rule_id"],
                    category=f_dict["category"],
                    title=f_dict["title"],
                    description=f_dict["description"],
                    severity=f_dict["severity"],
                    evidence=f_dict["evidence"],
                    source=f_dict["source"],
                    recommendation=f_dict["recommendation"],
                )
                db.add(finding)
                generated_findings.append(finding)
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.id} ({rule.name}): {e}")

    db.commit()
    logger.info(f"Finding engine generated {len(generated_findings)} findings for scan id={scan_id}")
    return generated_findings
