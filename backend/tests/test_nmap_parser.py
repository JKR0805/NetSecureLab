from pathlib import Path
from app.services.nmap.parser import parse_nmap_xml
from app.services.nmap.normalizer import normalize_and_store_nmap_results
from app.models.scan import Scan
from app.models.target import Target

FIXTURE_XML = Path(__file__).parent / "fixtures" / "sample_scan.xml"

def test_parse_sample_scan_xml():
    assert FIXTURE_XML.exists()
    parsed = parse_nmap_xml(FIXTURE_XML)
    hosts = parsed.get("hosts", [])
    assert len(hosts) == 1

    host = hosts[0]
    assert host["ip"] == "192.168.1.50"
    assert host["hostname"] == "lab-srv01.local"
    assert host["status"] == "up"
    assert host["os"] == "Linux 5.4"

    ports = host["ports"]
    assert len(ports) == 4

    port_map = {p["port_number"]: p for p in ports}
    assert 21 in port_map
    assert port_map[21]["service"] == "ftp"
    assert port_map[21]["product"] == "vsftpd"
    assert port_map[21]["version"] == "3.0.3"

    assert 3306 in port_map
    assert port_map[3306]["service"] == "mysql"

def test_normalize_and_store_nmap_results(db_session):
    target = Target(name="Test Target", target="192.168.1.50", target_type="ip", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan = Scan(target_id=target.id, profile="standard", status="running")
    db_session.add(scan)
    db_session.commit()

    parsed = parse_nmap_xml(FIXTURE_XML)
    assets = normalize_and_store_nmap_results(scan.id, parsed, db_session)
    assert len(assets) == 1
    assert assets[0].ip == "192.168.1.50"
    assert len(assets[0].ports) == 4
