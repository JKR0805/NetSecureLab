from app.models.target import Target
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.port import Port
from app.models.finding import Finding
from app.services.comparison.service import compare_scans

def test_compare_scans_detects_deltas(db_session):
    target = Target(name="Delta Target", target="192.168.1.100", target_type="ip", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    # Scan 1: Baseline
    scan1 = Scan(target_id=target.id, profile="standard", status="completed")
    db_session.add(scan1)
    db_session.commit()

    a1 = Asset(scan_id=scan1.id, ip="192.168.1.100", status="up")
    db_session.add(a1)
    db_session.commit()

    p22 = Port(asset_id=a1.id, port_number=22, protocol="tcp", state="open", service="ssh", version="8.0")
    p80 = Port(asset_id=a1.id, port_number=80, protocol="tcp", state="open", service="http", version="2.4.41")
    db_session.add_all([p22, p80])

    f1 = Finding(
        scan_id=scan1.id,
        asset_id=a1.id,
        rule_id="R007",
        category="Service Info",
        title="SSH Service Detected",
        description="SSH on port 22",
        severity="informational",
        evidence="Port 22 open",
        source="nmap",
        recommendation="Review SSH",
    )
    db_session.add(f1)
    db_session.commit()

    # Scan 2: Current (Port 80 closed/removed, Port 21 added, SSH version updated to 8.4)
    scan2 = Scan(target_id=target.id, profile="standard", status="completed")
    db_session.add(scan2)
    db_session.commit()

    a2 = Asset(scan_id=scan2.id, ip="192.168.1.100", status="up")
    db_session.add(a2)
    db_session.commit()

    p22_new = Port(asset_id=a2.id, port_number=22, protocol="tcp", state="open", service="ssh", version="8.4")
    p21_new = Port(asset_id=a2.id, port_number=21, protocol="tcp", state="open", service="ftp", version="3.0.3")
    db_session.add_all([p22_new, p21_new])

    f_ftp = Finding(
        scan_id=scan2.id,
        asset_id=a2.id,
        rule_id="R001",
        category="Service Exposure",
        title="FTP Service Reachable",
        description="FTP open",
        severity="medium",
        evidence="Port 21 open",
        source="nmap",
        recommendation="Review FTP",
    )
    f_ssh_persistent = Finding(
        scan_id=scan2.id,
        asset_id=a2.id,
        rule_id="R007",
        category="Service Info",
        title="SSH Service Detected",
        description="SSH on port 22",
        severity="informational",
        evidence="Port 22 open",
        source="nmap",
        recommendation="Review SSH",
    )
    db_session.add_all([f_ftp, f_ssh_persistent])
    db_session.commit()

    # Run comparison
    diff = compare_scans(scan1.id, scan2.id, db_session)

    # Verify hosts
    assert diff.unchanged_hosts == ["192.168.1.100"]

    # Verify added ports (port 21 added)
    added_port_nums = [p["port_number"] for p in diff.added_ports]
    assert 21 in added_port_nums

    # Verify removed ports (port 80 removed)
    removed_port_nums = [p["port_number"] for p in diff.removed_ports]
    assert 80 in removed_port_nums

    # Verify changed services (SSH version 8.0 -> 8.4)
    assert len(diff.changed_services) == 1
    assert diff.changed_services[0]["before"]["version"] == "8.0"
    assert diff.changed_services[0]["after"]["version"] == "8.4"

    # Verify findings delta
    new_rule_ids = [f.rule_id for f in diff.new_findings]
    assert "R001" in new_rule_ids

    persistent_rule_ids = [f.rule_id for f in diff.persistent_findings]
    assert "R007" in persistent_rule_ids
