import json
from dataclasses import dataclass
from typing import Callable, List, Dict, Any, Optional

@dataclass
class Rule:
    id: str
    name: str
    description: str
    severity: str
    category: str
    source: str
    required_module: str  # 'nmap' or 'dns' or 'recon'
    check_function: Callable[[Dict[str, Any]], List[Dict[str, Any]]]

def check_r001_ftp(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R001: FTP Service Reachable (TCP/21 open)"""
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if port.protocol == "tcp" and port.port_number == 21 and port.state == "open":
                findings.append({
                    "rule_id": "R001",
                    "asset_id": asset.id,
                    "category": "Service Exposure",
                    "title": "FTP Service Reachable",
                    "description": "TCP port 21 is open and identified as an FTP service. Unencrypted FTP transmits credentials in cleartext.",
                    "severity": "medium",
                    "evidence": f"Host {asset.ip} exposes open TCP/21 ({port.service or 'ftp'} {port.product or ''} {port.version or ''}).",
                    "source": "nmap",
                    "recommendation": "Verify whether unencrypted FTP exposure is required. Consider migrating to SFTP or FTPS to protect authentication credentials.",
                })
    return findings

def check_r002_telnet(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R002: Telnet Service Reachable (TCP/23 open)"""
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if port.protocol == "tcp" and port.port_number == 23 and port.state == "open":
                findings.append({
                    "rule_id": "R002",
                    "asset_id": asset.id,
                    "category": "Service Exposure",
                    "title": "Telnet Service Reachable",
                    "description": "TCP port 23 is open and running Telnet. Telnet transmits all data, including credentials, in cleartext.",
                    "severity": "medium",
                    "evidence": f"Host {asset.ip} exposes open TCP/23 ({port.service or 'telnet'} {port.product or ''} {port.version or ''}).",
                    "source": "nmap",
                    "recommendation": "Disable Telnet and mandate encrypted remote administration protocols such as SSH.",
                })
    return findings

def check_r003_database(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R003: Database Service Reachable (TCP 3306, 5432, 1433, 1521, 27017 open)"""
    db_ports = {
        3306: "MySQL",
        5432: "PostgreSQL",
        1433: "MSSQL",
        1521: "Oracle",
        27017: "MongoDB",
    }
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if port.protocol == "tcp" and port.port_number in db_ports and port.state == "open":
                db_name = db_ports[port.port_number]
                findings.append({
                    "rule_id": "R003",
                    "asset_id": asset.id,
                    "category": "Service Exposure",
                    "title": f"Database Service Reachable ({db_name})",
                    "description": f"Direct external exposure of database port TCP/{port.port_number} ({db_name}) observed.",
                    "severity": "medium",
                    "evidence": f"Host {asset.ip} exposes database port TCP/{port.port_number} ({db_name}, state={port.state}, service={port.service or ''}).",
                    "source": "nmap",
                    "recommendation": f"Verify whether direct network reachability to {db_name} is intended. Place database instances in isolated internal subnets and restrict access via firewalls.",
                })
    return findings

def check_r004_smb(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R004: SMB/NetBIOS Service Reachable (TCP 139, 445 open)"""
    smb_ports = {139: "NetBIOS", 445: "SMB/CIFS"}
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if port.protocol == "tcp" and port.port_number in smb_ports and port.state == "open":
                srv = smb_ports[port.port_number]
                findings.append({
                    "rule_id": "R004",
                    "asset_id": asset.id,
                    "category": "Service Exposure",
                    "title": f"SMB/NetBIOS Service Reachable ({srv})",
                    "description": f"File sharing service port TCP/{port.port_number} ({srv}) is open and reachable.",
                    "severity": "medium",
                    "evidence": f"Host {asset.ip} exposes file sharing port TCP/{port.port_number} ({srv}, service={port.service or ''}).",
                    "source": "nmap",
                    "recommendation": "Restrict SMB/NetBIOS port reachability to trusted internal network boundaries.",
                })
    return findings

def check_r005_rdp(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R005: RDP Service Reachable (TCP 3389 open)"""
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if port.protocol == "tcp" and port.port_number == 3389 and port.state == "open":
                findings.append({
                    "rule_id": "R005",
                    "asset_id": asset.id,
                    "category": "Service Exposure",
                    "title": "RDP Service Reachable",
                    "description": "Remote Desktop Protocol (RDP) on TCP/3389 is exposed.",
                    "severity": "low",
                    "evidence": f"Host {asset.ip} exposes open TCP/3389 (RDP).",
                    "source": "nmap",
                    "recommendation": "Ensure RDP is protected behind a VPN or gateway, with Network Level Authentication (NLA) and multi-factor authentication enabled.",
                })
    return findings

def check_r006_web(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R006: Web Service Detected (TCP 80, 443, 8080, 8443 open)"""
    web_ports = {80, 443, 8080, 8443}
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if port.protocol == "tcp" and port.state == "open" and (port.port_number in web_ports or "http" in (port.service or "").lower()):
                findings.append({
                    "rule_id": "R006",
                    "asset_id": asset.id,
                    "category": "Web Discovery",
                    "title": f"Web Service Detected (TCP/{port.port_number})",
                    "description": f"HTTP/HTTPS service detected on TCP/{port.port_number}.",
                    "severity": "informational",
                    "evidence": f"Host {asset.ip} runs web service on port {port.port_number} (Service: {port.service}, Product: {port.product or 'unknown'}, Version: {port.version or 'unknown'}).",
                    "source": "nmap",
                    "recommendation": "Record web endpoint in asset inventory. Review application security configuration and TLS settings.",
                })
    return findings

def check_r007_ssh(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R007: SSH Service Detected (TCP 22 open)"""
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if port.protocol == "tcp" and port.port_number == 22 and port.state == "open":
                findings.append({
                    "rule_id": "R007",
                    "asset_id": asset.id,
                    "category": "Service Info",
                    "title": "SSH Service Detected",
                    "description": "Secure Shell (SSH) service detected on TCP/22.",
                    "severity": "informational",
                    "evidence": f"Host {asset.ip} exposes TCP/22 (Product: {port.product or 'OpenSSH'}, Version: {port.version or 'unknown'}).",
                    "source": "nmap",
                    "recommendation": "Ensure SSH password authentication is disabled in favor of key-based authentication, and keep software updated.",
                })
    return findings

def check_r008_service_version(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R008: Service Version Identified"""
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if port.state == "open" and port.version:
                findings.append({
                    "rule_id": "R008",
                    "asset_id": asset.id,
                    "category": "Fingerprinting",
                    "title": f"Service Version Identified ({port.service or 'service'} on port {port.port_number})",
                    "description": f"Service version string was identified by banner grabbing / probe analysis.",
                    "severity": "informational",
                    "evidence": f"Port {port.port_number}/{port.protocol}: {port.product or ''} version {port.version} {port.extra_info or ''}".strip(),
                    "source": "nmap",
                    "recommendation": "Maintain inventory of running service versions. Verify whether vendor security patches are up to date.",
                })
    return findings

def check_r009_os_fingerprint(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R009: OS Fingerprint Identified"""
    findings = []
    for asset in context.get("assets", []):
        if asset.os:
            findings.append({
                "rule_id": "R009",
                "asset_id": asset.id,
                "category": "Fingerprinting",
                "title": f"OS Fingerprint Identified for {asset.ip}",
                "description": "Operating system signature detected via TCP/IP stack fingerprinting.",
                "severity": "informational",
                "evidence": f"Host {asset.ip} fingerprinted as: {asset.os}",
                "source": "nmap",
                "recommendation": "Verify host OS aligns with approved baseline images and support lifecycles.",
            })
    return findings

def check_r010_spf(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    R010: SPF Record Not Found
    Domain-level rule only: applies exclusively to target_type=domain.
    Requires dns_status in ('success', 'partial').
    """
    target = context.get("target")
    if not target or target.target_type != "domain":
        return []

    dns_records = context.get("dns_records", [])
    has_spf = False
    for r in dns_records:
        if r.record_type == "TXT" and "v=spf1" in r.value.lower():
            has_spf = True
            break

    if not has_spf:
        return [{
            "rule_id": "R010",
            "asset_id": None,
            "category": "DNS Security",
            "title": "SPF Record Not Found",
            "description": f"No Sender Policy Framework (SPF) TXT record starting with 'v=spf1' was found for {target.target}.",
            "severity": "low",
            "evidence": f"Queried TXT records for domain '{target.target}'; no record with 'v=spf1' observed.",
            "source": "dns",
            "recommendation": "Publish an SPF record to specify authorized mail sending infrastructure and mitigate email spoofing.",
        }]
    return []

def check_r011_dmarc(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    R011: DMARC Record Not Found
    Domain-level rule only: applies exclusively to target_type=domain.
    Requires dns_status in ('success', 'partial').
    Queried from _dmarc.<domain>.
    """
    target = context.get("target")
    if not target or target.target_type != "domain":
        return []

    dns_records = context.get("dns_records", [])
    has_dmarc = False
    expected_prefix = f"_dmarc.{target.target}".lower()

    for r in dns_records:
        if r.record_type == "TXT" and expected_prefix in r.name.lower() and "v=dmarc1" in r.value.lower():
            has_dmarc = True
            break

    if not has_dmarc:
        return [{
            "rule_id": "R011",
            "asset_id": None,
            "category": "DNS Security",
            "title": "DMARC Record Not Found",
            "description": f"No DMARC policy record (v=DMARC1) found at _dmarc.{target.target}.",
            "severity": "low",
            "evidence": f"Queried TXT records for '_dmarc.{target.target}'; no DMARC record found.",
            "source": "dns",
            "recommendation": "Implement a DMARC policy record at _dmarc.<domain> to protect domain reputation and prevent unauthorized email spoofing.",
        }]
    return []

def check_r012_multiple_mx(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    R012: Multiple MX Servers
    Domain-level rule only: applies exclusively to target_type=domain.
    """
    target = context.get("target")
    if not target or target.target_type != "domain":
        return []

    dns_records = context.get("dns_records", [])
    mx_records = [r for r in dns_records if r.record_type == "MX"]

    if len(mx_records) > 1:
        values = ", ".join([r.value for r in mx_records])
        return [{
            "rule_id": "R012",
            "asset_id": None,
            "category": "Mail Infrastructure",
            "title": "Multiple Mail Exchange (MX) Servers Detected",
            "description": "Domain specifies redundant Mail Exchange (MX) records.",
            "severity": "informational",
            "evidence": f"Found {len(mx_records)} MX records for {target.target}: {values}.",
            "source": "dns",
            "recommendation": "Ensure mail routing priorities and server configurations are synchronized across all MX endpoints.",
        }]
    return []

def check_r013_ssl_script(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R013: Insecure SSL/TLS or Weak Cipher Suites from NSE Script Output"""
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if not port.scripts:
                continue
            try:
                scripts_list = json.loads(port.scripts) if isinstance(port.scripts, str) else port.scripts
            except Exception:
                continue

            for s in scripts_list:
                s_id = s.get("id", "")
                output = s.get("output", "")
                out_lower = output.lower()

                if s_id in ("ssl-enum-ciphers", "ssl-cert"):
                    weak_indicators = ["rc4", "des", "3des", "export", "null cipher", "sslv2", "sslv3", "tlsv1.0", "expired"]
                    matched = [w for w in weak_indicators if w in out_lower]
                    if matched:
                        findings.append({
                            "rule_id": "R013",
                            "asset_id": asset.id,
                            "category": "Cryptographic Security",
                            "title": "Insecure SSL/TLS or Weak Cipher Suites Detected",
                            "description": f"NSE script '{s_id}' observed weak or obsolete SSL/TLS configurations ({', '.join(matched)}).",
                            "severity": "medium",
                            "evidence": f"Host {asset.ip}:{port.port_number} script '{s_id}' reported:\n{output[:300]}",
                            "source": "nmap",
                            "recommendation": "Disable legacy protocol versions (SSLv3, TLS 1.0, TLS 1.1) and disable weak ciphers (RC4, DES, 3DES). Enforce TLS 1.2+ with modern AEAD cipher suites.",
                        })
                        break
    return findings

def check_r014_http_methods(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """R014: Dangerous HTTP Methods Enabled (PUT, DELETE, TRACE) from NSE Script Output"""
    findings = []
    for asset in context.get("assets", []):
        for port in asset.ports:
            if not port.scripts:
                continue
            try:
                scripts_list = json.loads(port.scripts) if isinstance(port.scripts, str) else port.scripts
            except Exception:
                continue

            for s in scripts_list:
                if s.get("id") == "http-methods":
                    output = s.get("output", "")
                    risky_methods = [m for m in ["PUT", "DELETE", "TRACE"] if m in output.upper()]
                    if risky_methods:
                        findings.append({
                            "rule_id": "R014",
                            "asset_id": asset.id,
                            "category": "Web Security",
                            "title": f"Potentially Dangerous HTTP Methods Enabled ({', '.join(risky_methods)})",
                            "description": f"HTTP methods {', '.join(risky_methods)} are permitted on the web server according to NSE http-methods.",
                            "severity": "low",
                            "evidence": f"Host {asset.ip}:{port.port_number} http-methods:\n{output[:300]}",
                            "source": "nmap",
                            "recommendation": "Disable unnecessary HTTP methods (such as TRACE, PUT, DELETE) in web server configurations unless strictly required by application APIs.",
                        })
                        break
    return findings

RULES_CATALOG: List[Rule] = [
    Rule("R001", "FTP Service Reachable", "FTP port open", "medium", "Service Exposure", "nmap", "nmap", check_r001_ftp),
    Rule("R002", "Telnet Service Reachable", "Telnet port open", "medium", "Service Exposure", "nmap", "nmap", check_r002_telnet),
    Rule("R003", "Database Service Reachable", "Database port open", "medium", "Service Exposure", "nmap", "nmap", check_r003_database),
    Rule("R004", "SMB/NetBIOS Service Reachable", "SMB/NetBIOS port open", "medium", "Service Exposure", "nmap", "nmap", check_r004_smb),
    Rule("R005", "RDP Service Reachable", "RDP port open", "low", "Service Exposure", "nmap", "nmap", check_r005_rdp),
    Rule("R006", "Web Service Detected", "Web server detected", "informational", "Web Discovery", "nmap", "nmap", check_r006_web),
    Rule("R007", "SSH Service Detected", "SSH port open", "informational", "Service Info", "nmap", "nmap", check_r007_ssh),
    Rule("R008", "Service Version Identified", "Version string extracted", "informational", "Fingerprinting", "nmap", "nmap", check_r008_service_version),
    Rule("R009", "OS Fingerprint Identified", "OS fingerprint detected", "informational", "Fingerprinting", "nmap", "nmap", check_r009_os_fingerprint),
    Rule("R010", "SPF Record Not Found", "Missing SPF record", "low", "DNS Security", "dns", "dns", check_r010_spf),
    Rule("R011", "DMARC Record Not Found", "Missing DMARC record", "low", "DNS Security", "dns", "dns", check_r011_dmarc),
    Rule("R012", "Multiple MX Servers", "Multiple MX records", "informational", "Mail Infrastructure", "dns", "dns", check_r012_multiple_mx),
    Rule("R013", "Insecure SSL/TLS or Weak Cipher Suites", "Weak cipher suites in NSE output", "medium", "Cryptographic Security", "nmap", "nmap", check_r013_ssl_script),
    Rule("R014", "Dangerous HTTP Methods Enabled", "Risky HTTP methods in NSE output", "low", "Web Security", "nmap", "nmap", check_r014_http_methods),
]
