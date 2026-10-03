from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.database.connection import get_db
from app.models.target import Target
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.port import Port
from app.models.finding import Finding
from app.schemas.scan import ScanResponse
from app.api.scans import build_scan_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_targets = db.query(Target).count()
    
    # Distinct IP addresses discovered
    total_hosts = db.query(func.count(distinct(Asset.ip))).scalar() or 0
    
    # Total open ports
    total_open_ports = db.query(Port).filter(Port.state == "open").count()
    
    # Total distinct services
    total_services = (
        db.query(func.count(distinct(Port.service)))
        .filter(Port.state == "open", Port.service.isnot(None), Port.service != "")
        .scalar()
        or 0
    )
    
    total_findings = db.query(Finding).count()

    # Findings by severity
    severity_counts_query = (
        db.query(Finding.severity, func.count(Finding.id))
        .group_by(Finding.severity)
        .all()
    )
    findings_by_severity = {
        "high": 0,
        "medium": 0,
        "low": 0,
        "informational": 0,
    }
    for sev, count in severity_counts_query:
        if sev in findings_by_severity:
            findings_by_severity[sev] = count

    # Recent scans (last 5)
    recent_scans_query = db.query(Scan).order_by(Scan.id.desc()).limit(5).all()
    recent_scans = [build_scan_response(s) for s in recent_scans_query]

    return {
        "total_targets": total_targets,
        "total_hosts": total_hosts,
        "total_open_ports": total_open_ports,
        "total_services": total_services,
        "total_findings": total_findings,
        "findings_by_severity": findings_by_severity,
        "recent_scans": recent_scans,
    }
