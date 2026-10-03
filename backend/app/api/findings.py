from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.scan import Scan
from app.models.finding import Finding
from app.schemas.finding import FindingResponse

router = APIRouter(tags=["findings"])

@router.get("/findings", response_model=List[FindingResponse])
def list_all_findings(
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Finding)
    if severity:
        query = query.filter(Finding.severity == severity.lower())
    if category:
        query = query.filter(Finding.category == category)
    if source:
        query = query.filter(Finding.source == source)
    
    findings = query.order_by(Finding.id.desc()).all()
    return findings

@router.get("/scans/{scan_id}/findings", response_model=List[FindingResponse])
def get_scan_findings(
    scan_id: int,
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    query = db.query(Finding).filter(Finding.scan_id == scan_id)
    if severity:
        query = query.filter(Finding.severity == severity.lower())
    if category:
        query = query.filter(Finding.category == category)
    if source:
        query = query.filter(Finding.source == source)

    findings = query.order_by(Finding.id.desc()).all()
    return findings
