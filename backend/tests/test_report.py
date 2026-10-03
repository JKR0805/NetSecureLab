from app.models.target import Target
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.port import Port
from app.models.finding import Finding
from app.services.reporting.service import generate_scan_report

def test_generate_scan_report_html(db_session):
    target = Target(name="Report Demo Corp", target="10.10.10.5", target_type="ip", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan = Scan(
        target_id=target.id,
        profile="standard",
        status="completed",
        nmap_status="success",
        dns_status="skipped",
        recon_status="success",
        duration=12.4,
    )
    db_session.add(scan)
    db_session.commit()

    asset = Asset(scan_id=scan.id, ip="10.10.10.5", status="up")
    db_session.add(asset)
    db_session.commit()

    port = Port(asset_id=asset.id, port_number=443, protocol="tcp", state="open", service="https", product="nginx", version="1.18.0")
    db_session.add(port)

    finding = Finding(
        scan_id=scan.id,
        asset_id=asset.id,
        rule_id="R006",
        category="Web Discovery",
        title="Web Service Detected",
        description="HTTPS service detected on TCP/443",
        severity="informational",
        evidence="Port 443 open (nginx 1.18.0)",
        source="nmap",
        recommendation="Verify TLS certificates",
    )
    db_session.add(finding)
    db_session.commit()

    report_path = generate_scan_report(scan.id, db_session)
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")

    assert "Report Demo Corp" in content
    assert "10.10.10.5" in content
    assert "Executive Summary &amp; Target Profile" in content or "Executive Summary" in content
    assert "Assessment Modules Outcome" in content
    assert "Assessment Limitations &amp; Methodology Scope" in content or "Limitations" in content
    assert "R006" in content
