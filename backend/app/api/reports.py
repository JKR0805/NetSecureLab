from typing import Optional
from pathlib import Path
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.scan import Scan
from app.services.reporting.service import generate_scan_report
from app.config import settings

router = APIRouter(prefix="/reports", tags=["reports"])

class GenerateReportRequest(BaseModel):
    compare_with: Optional[int] = None

@router.post("/{scan_id}/generate")
def create_report(
    scan_id: int,
    payload: Optional[GenerateReportRequest] = None,
    db: Session = Depends(get_db),
):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    compare_id = payload.compare_with if payload else None
    try:
        report_path = generate_scan_report(scan_id, db, compare_scan_id=compare_id)
        return {
            "status": "success",
            "scan_id": scan_id,
            "filename": report_path.name,
            "view_url": f"/reports/{scan_id}",
            "download_url": f"/reports/{scan_id}/download",
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate report: {str(e)}")

@router.get("/{scan_id}", response_class=HTMLResponse)
def view_report(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    report_file = settings.REPORTS_DIR / f"report_{scan_id}.html"
    if not report_file.exists():
        # Auto-generate if not yet generated
        try:
            report_file = generate_scan_report(scan_id, db)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report could not be generated: {e}")

    return HTMLResponse(content=report_file.read_text(encoding="utf-8"))

@router.get("/{scan_id}/download")
def download_report(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    report_file = settings.REPORTS_DIR / f"report_{scan_id}.html"
    if not report_file.exists():
        try:
            report_file = generate_scan_report(scan_id, db)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Report could not be generated: {e}")

    return FileResponse(
        path=str(report_file),
        media_type="text/html",
        filename=f"NetSecureLab_Report_Scan_{scan_id}.html",
    )
