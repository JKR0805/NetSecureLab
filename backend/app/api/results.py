from typing import List, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.connection import get_db
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.port import Port
from app.models.dns_record import DNSRecord
from app.models.recon_result import ReconResult
from app.schemas.asset import AssetResponse
from app.schemas.port import PortResponse
from app.schemas.dns_record import DNSRecordResponse
from app.schemas.recon_result import ReconResultResponse
from app.config import settings

router = APIRouter(prefix="/scans/{scan_id}", tags=["results"])

@router.get("/hosts", response_model=List[AssetResponse])
def get_scan_hosts(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    assets = db.query(Asset).filter(Asset.scan_id == scan_id).all()
    return assets

@router.get("/ports", response_model=List[PortResponse])
def get_scan_ports(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    ports = (
        db.query(Port)
        .join(Asset, Port.asset_id == Asset.id)
        .filter(Asset.scan_id == scan_id)
        .all()
    )
    return ports

@router.get("/services")
def get_scan_services(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    services_query = (
        db.query(
            Port.service,
            Port.product,
            Port.version,
            func.count(Port.id).label("count")
        )
        .join(Asset, Port.asset_id == Asset.id)
        .filter(Asset.scan_id == scan_id, Port.state == "open")
        .group_by(Port.service, Port.product, Port.version)
        .all()
    )

    return [
        {
            "service": s[0] or "unknown",
            "product": s[1] or "",
            "version": s[2] or "",
            "count": s[3],
        }
        for s in services_query
    ]

@router.get("/dns", response_model=List[DNSRecordResponse])
def get_scan_dns(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    records = db.query(DNSRecord).filter(DNSRecord.scan_id == scan_id).all()
    return records

@router.get("/recon", response_model=List[ReconResultResponse])
def get_scan_recon(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    results = db.query(ReconResult).filter(ReconResult.scan_id == scan_id).all()
    return results

@router.get("/raw")
def get_raw_scan_output(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    # Secure path resolution — strictly validate file is within SCANS_DIR
    target_filename = f"{scan_id}.xml"
    safe_base = settings.SCANS_DIR.resolve()
    target_path = (safe_base / target_filename).resolve()

    try:
        # Check if target_path is relative to safe_base (prevents traversal)
        target_path.relative_to(safe_base)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file path")

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Raw Nmap XML output is not available for this scan"
        )

    return FileResponse(
        path=str(target_path),
        media_type="application/xml",
        filename=f"scan_{scan_id}_nmap.xml",
    )
