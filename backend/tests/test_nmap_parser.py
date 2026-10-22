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

def test_parse_and_evaluate_nse_scripts(tmp_path, db_session):
    from app.services.findings.rules import check_r013_ssl_script, check_r014_http_methods
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<nmaprun scanner="nmap" args="nmap -sV -sC -oX out.xml 192.168.1.99" start="1600000000" version="7.92">
  <host>
    <status state="up"/>
    <address addr="192.168.1.99" addrtype="ipv4"/>
    <hostnames><hostname name="crypto-test.lab"/></hostnames>
    <ports>
      <port protocol="tcp" portid="443">
        <state state="open"/>
        <service name="https" product="nginx" version="1.18.0"/>
        <script id="ssl-enum-ciphers" output="TLSv1.0: ciphers: TLS_RSA_WITH_RC4_128_SHA (broken)"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http" product="Apache" version="2.4"/>
        <script id="http-methods" output="Supported Methods: GET HEAD POST PUT DELETE TRACE"/>
      </port>
    </ports>
  </host>
</nmaprun>
"""
    xml_file = tmp_path / "nse_test.xml"
    xml_file.write_text(xml_content, encoding="utf-8")

    parsed = parse_nmap_xml(xml_file)
    assert len(parsed["hosts"]) == 1
    ports = parsed["hosts"][0]["ports"]
    assert len(ports) == 2

    p443 = next(p for p in ports if p["port_number"] == 443)
    assert len(p443["scripts"]) == 1
    assert p443["scripts"][0]["id"] == "ssl-enum-ciphers"

    # Normalize into DB
    target = Target(name="NSE Target", target="192.168.1.99", target_type="ip", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan = Scan(target_id=target.id, profile="full", status="running", nmap_status="success")
    db_session.add(scan)
    db_session.commit()

    assets = normalize_and_store_nmap_results(scan.id, parsed, db_session)
    assert len(assets) == 1
    db_ports = assets[0].ports
    assert len(db_ports) == 2

    # Verify rule checks
    context = {"assets": assets, "scan": scan, "target": target}
    ssl_findings = check_r013_ssl_script(context)
    assert len(ssl_findings) == 1
    assert ssl_findings[0]["rule_id"] == "R013"
    assert "Insecure SSL/TLS" in ssl_findings[0]["title"]

    http_findings = check_r014_http_methods(context)
    assert len(http_findings) == 1
    assert http_findings[0]["rule_id"] == "R014"
    assert "Dangerous HTTP Methods" in http_findings[0]["title"]

