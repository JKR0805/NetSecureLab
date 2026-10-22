import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.utils.logger import logger

def parse_nmap_xml(xml_path: Path) -> Dict[str, Any]:
    """
    Parses Nmap XML output file into normalized Python structures.
    Returns:
    {
        "hosts": [
            {
                "ip": "...",
                "hostname": "...",
                "status": "up"|"down",
                "os": "...",
                "ports": [
                    {
                        "port_number": 80,
                        "protocol": "tcp",
                        "state": "open",
                        "service": "http",
                        "product": "Apache httpd",
                        "version": "2.4.41",
                        "extra_info": "(Ubuntu)"
                    }
                ]
            }
        ]
    }
    """
    if not xml_path.exists():
        logger.error(f"XML file not found: {xml_path}")
        return {"hosts": []}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        logger.error(f"Failed to parse Nmap XML {xml_path}: {e}")
        return {"hosts": []}

    hosts_data = []

    for host_elem in root.findall("host"):
        # 1. Host status
        status_elem = host_elem.find("status")
        host_status = status_elem.get("state", "unknown") if status_elem is not None else "unknown"

        # 2. IP Address
        ip_addr = None
        for addr_elem in host_elem.findall("address"):
            addr_type = addr_elem.get("addrtype", "")
            if addr_type in ("ipv4", "ipv6") and not ip_addr:
                ip_addr = addr_elem.get("addr")
            elif addr_type == "ipv4":
                # Prefer ipv4
                ip_addr = addr_elem.get("addr")

        if not ip_addr:
            continue

        # 3. Hostname
        hostname = None
        hostnames_elem = host_elem.find("hostnames")
        if hostnames_elem is not None:
            for hn in hostnames_elem.findall("hostname"):
                name = hn.get("name")
                if name:
                    hostname = name
                    break

        # 4. OS Match
        os_name = None
        os_elem = host_elem.find("os")
        if os_elem is not None:
            os_match = os_elem.find("osmatch")
            if os_match is not None:
                os_name = os_match.get("name")

        # 5. Ports
        ports_data = []
        ports_elem = host_elem.find("ports")
        if ports_elem is not None:
            for port_elem in ports_elem.findall("port"):
                try:
                    port_id = int(port_elem.get("portid", 0))
                except ValueError:
                    continue

                protocol = port_elem.get("protocol", "tcp").lower()

                state_elem = port_elem.find("state")
                state = state_elem.get("state", "unknown") if state_elem is not None else "unknown"

                service_name = None
                product = None
                version = None
                extra_info = None

                service_elem = port_elem.find("service")
                if service_elem is not None:
                    service_name = service_elem.get("name")
                    product = service_elem.get("product")
                    version = service_elem.get("version")
                    extra_info = service_elem.get("extrainfo")

                # NSE Script results on port
                scripts_data = []
                for s_elem in port_elem.findall("script"):
                    s_id = s_elem.get("id")
                    s_out = s_elem.get("output") or s_elem.text or ""
                    if s_id:
                        scripts_data.append({"id": s_id, "output": s_out.strip()})

                ports_data.append({
                    "port_number": port_id,
                    "protocol": protocol,
                    "state": state,
                    "service": service_name,
                    "product": product,
                    "version": version,
                    "extra_info": extra_info,
                    "scripts": scripts_data,
                })

        # Host-level NSE Scripts
        host_scripts = []
        hostscript_elem = host_elem.find("hostscript")
        if hostscript_elem is not None:
            for s_elem in hostscript_elem.findall("script"):
                s_id = s_elem.get("id")
                s_out = s_elem.get("output") or s_elem.text or ""
                if s_id:
                    host_scripts.append({"id": s_id, "output": s_out.strip()})

        hosts_data.append({
            "ip": ip_addr,
            "hostname": hostname,
            "status": host_status,
            "os": os_name,
            "ports": ports_data,
            "scripts": host_scripts,
        })

    return {"hosts": hosts_data}
