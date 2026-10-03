from app.models.target import Target
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.port import Port
from app.models.dns_record import DNSRecord
from app.services.findings.engine import run_finding_engine

def test_finding_engine_triggers_rules(db_session):
    target = Target(name="Lab Host", target="192.168.1.50", target_type="ip", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan = Scan(
        target_id=target.id,
        profile="standard",
        status="running",
        nmap_status="success",
        dns_status="skipped",
        recon_status="skipped",
    )
    db_session.add(scan)
    db_session.commit()

    asset = Asset(
        scan_id=scan.id,
        ip="192.168.1.50",
        hostname="lab-srv01.local",
        status="up",
        os="Linux 5.4",
    )
    db_session.add(asset)
    db_session.commit()

    # Ports: 21 (FTP), 22 (SSH), 80 (HTTP), 3306 (MySQL)
    p21 = Port(asset_id=asset.id, port_number=21, protocol="tcp", state="open", service="ftp", product="vsftpd", version="3.0.3")
    p22 = Port(asset_id=asset.id, port_number=22, protocol="tcp", state="open", service="ssh", product="OpenSSH", version="8.2p1")
    p80 = Port(asset_id=asset.id, port_number=80, protocol="tcp", state="open", service="http", product="Apache", version="2.4.41")
    p3306 = Port(asset_id=asset.id, port_number=3306, protocol="tcp", state="open", service="mysql", product="MySQL", version="8.0.28")

    db_session.add_all([p21, p22, p80, p3306])
    db_session.commit()

    findings = run_finding_engine(scan.id, db_session)
    rule_ids = {f.rule_id for f in findings}

    # Verify expected rules triggered
    assert "R001" in rule_ids  # FTP
    assert "R003" in rule_ids  # MySQL Database
    assert "R006" in rule_ids  # Web HTTP
    assert "R007" in rule_ids  # SSH
    assert "R008" in rule_ids  # Service Version
    assert "R009" in rule_ids  # OS Fingerprint

    # Verify all findings have rule_id, evidence, severity
    for f in findings:
        assert f.rule_id.startswith("R")
        assert f.evidence is not None and len(f.evidence) > 0
        assert f.severity in ("high", "medium", "low", "informational")

def test_finding_engine_module_awareness_skips_failed_nmap(db_session):
    target = Target(name="Lab Host", target="192.168.1.50", target_type="ip", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    # Scan where Nmap failed
    scan = Scan(
        target_id=target.id,
        profile="standard",
        status="running",
        nmap_status="failed",  # Module failed!
        dns_status="skipped",
        recon_status="skipped",
    )
    db_session.add(scan)
    db_session.commit()

    asset = Asset(scan_id=scan.id, ip="192.168.1.50", status="up")
    db_session.add(asset)
    db_session.commit()

    p21 = Port(asset_id=asset.id, port_number=21, protocol="tcp", state="open", service="ftp")
    db_session.add(p21)
    db_session.commit()

    findings = run_finding_engine(scan.id, db_session)
    # Rules requiring Nmap must be skipped because nmap_status == "failed"
    assert len(findings) == 0

def test_dns_rules_apply_only_to_domain_targets(db_session):
    # Domain target with missing SPF and DMARC
    target = Target(name="Test Domain", target="example.org", target_type="domain", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan = Scan(
        target_id=target.id,
        profile="quick",
        status="running",
        nmap_status="skipped",
        dns_status="success",
        recon_status="skipped",
    )
    db_session.add(scan)
    db_session.commit()

    findings = run_finding_engine(scan.id, db_session)
    rule_ids = {f.rule_id for f in findings}

    assert "R010" in rule_ids  # SPF missing
    assert "R011" in rule_ids  # DMARC missing
