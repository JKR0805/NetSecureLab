from datetime import datetime
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.orm import Session
from app.config import settings
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.dns_record import DNSRecord
from app.models.recon_result import ReconResult
from app.models.finding import Finding
from app.services.comparison.service import compare_scans
from app.utils.logger import logger

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

def generate_scan_report(
    scan_id: int,
    db: Session,
    compare_scan_id: Optional[int] = None,
) -> Path:
    """
    Generates a structured, standalone HTML security assessment report.
    """
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise ValueError(f"Scan id={scan_id} not found")

    target = scan.target
    assets = db.query(Asset).filter(Asset.scan_id == scan_id).all()
    dns_records = db.query(DNSRecord).filter(DNSRecord.scan_id == scan_id).all()
    recon_results = db.query(ReconResult).filter(ReconResult.scan_id == scan_id).all()
    findings = db.query(Finding).filter(Finding.scan_id == scan_id).order_by(Finding.id.asc()).all()

    comparison_data = None
    if compare_scan_id:
        try:
            comparison_data = compare_scans(compare_scan_id, scan_id, db)
        except Exception as e:
            logger.warning(f"Report comparison generation failed: {e}")

    template = jinja_env.get_template("report.html")
    rendered_html = template.render(
        scan=scan,
        target=target,
        assets=assets,
        dns_records=dns_records,
        recon_results=recon_results,
        findings=findings,
        comparison=comparison_data,
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
    )

    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = settings.REPORTS_DIR / f"report_{scan_id}.html"
    report_file.write_text(rendered_html, encoding="utf-8")

    logger.info(f"Report successfully generated at: {report_file}")
    return report_file
