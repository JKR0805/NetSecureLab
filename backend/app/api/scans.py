from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.target import Target
from app.models.scan import Scan
from app.schemas.scan import ScanCreate, ScanResponse, ScanStatusResponse
from app.schemas.target import TargetResponse
from app.config import settings
from app.workers.scan_worker import scan_worker
from app.utils.logger import logger

router = APIRouter(prefix="/scans", tags=["scans"])

def build_scan_response(scan: Scan) -> ScanResponse:
    raw_available = False
    if scan.raw_output_path:
        raw_path = Path(scan.raw_output_path)
        raw_available = raw_path.exists() and raw_path.is_file()

    resp = ScanResponse.model_validate(scan)
    resp.raw_output_available = raw_available
    resp.findings_count = len(scan.findings) if scan.findings else 0
    resp.assets_count = len(scan.assets) if scan.assets else 0
    if scan.target:
        t_resp = TargetResponse.model_validate(scan.target)
        t_resp.scan_count = len(scan.target.scans) if scan.target.scans else 0
        resp.target = t_resp
    return resp

@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
def create_scan(payload: ScanCreate, db: Session = Depends(get_db)):
    target = db.query(Target).filter(Target.id == payload.target_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    # Backend-enforced authorization check (Rule 5 & Task 2.6)
    if not target.authorization_confirmed:
        logger.warning(f"Scan rejected for unauthorized target id={target.id} ({target.target})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization required: target has not been confirmed for authorized security assessment."
        )

    # Validate profile
    if payload.profile not in settings.SCAN_PROFILES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid profile '{payload.profile}'. Allowed: {list(settings.SCAN_PROFILES.keys())}"
        )

    scan_obj = Scan(
        target_id=target.id,
        profile=payload.profile,
        status="queued",
        cancel_requested=False,
        nmap_status="pending",
        dns_status="pending",
        recon_status="pending",
    )
    db.add(scan_obj)
    db.commit()
    db.refresh(scan_obj)

    logger.info(f"Created scan id={scan_obj.id} for target id={target.id} with profile={payload.profile}")
    
    # Submit to ScanWorker thread
    scan_worker.submit(scan_obj.id)

    return build_scan_response(scan_obj)

@router.get("", response_model=List[ScanResponse])
def list_scans(target_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Scan)
    if target_id is not None:
        query = query.filter(Scan.target_id == target_id)
    scans = query.order_by(Scan.id.desc()).all()
    return [build_scan_response(s) for s in scans]

@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return build_scan_response(scan)

@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
def get_scan_status(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return ScanStatusResponse.model_validate(scan)

@router.post("/{scan_id}/cancel", response_model=ScanResponse)
def cancel_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    if scan.status in ("completed", "failed", "cancelled"):
        return build_scan_response(scan)

    scan.cancel_requested = True
    if scan.status == "queued":
        scan.status = "cancelled"
        scan.error_message = "Scan cancelled by user before execution."

    db.commit()
    db.refresh(scan)
    logger.info(f"Cancellation requested for scan id={scan_id}. Current status: {scan.status}")
    return build_scan_response(scan)
