import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.scan import Scan
from app.models.finding import Finding
from app.schemas.finding import FindingResponse, FindingUpdate

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

@router.get("/findings/export/csv")
def export_findings_csv(
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Finding)
    if severity:
        query = query.filter(Finding.severity == severity.lower())
    if category:
        query = query.filter(Finding.category == category)

    findings = query.order_by(Finding.id.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Scan ID", "Rule ID", "Severity", "Status",
        "Category", "Title", "Description", "Source", "Recommendation", "Created At", "Notes"
    ])
    for f in findings:
        writer.writerow([
            f.id,
            f.scan_id,
            f.rule_id,
            f.severity,
            f.status,
            f.category,
            f.title,
            f.description,
            f.source,
            f.recommendation,
            f.created_at.isoformat() if f.created_at else "",
            f.notes or "",
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="netsecurelab_findings.csv"'},
    )

@router.get("/findings/export/json")
def export_findings_json(
    severity: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Finding)
    if severity:
        query = query.filter(Finding.severity == severity.lower())
    if category:
        query = query.filter(Finding.category == category)

    findings = query.order_by(Finding.id.desc()).all()
    data = [FindingResponse.model_validate(f).model_dump(mode="json") for f in findings]
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="netsecurelab_findings.json"'},
    )

@router.patch("/findings/{finding_id}", response_model=FindingResponse)
def update_finding(
    finding_id: int,
    payload: FindingUpdate,
    db: Session = Depends(get_db),
):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")

    if payload.status is not None:
        finding.status = payload.status
    if payload.notes is not None:
        finding.notes = payload.notes

    db.commit()
    db.refresh(finding)
    return finding

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
