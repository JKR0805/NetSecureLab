from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.port import Port
from app.models.finding import Finding
from app.schemas.comparison import ComparisonResponse
from app.schemas.finding import FindingResponse

def compare_scans(scan1_id: int, scan2_id: int, db: Session) -> ComparisonResponse:
    """
    Compares two scans of the same target using normalized snapshots.
    scan1 is considered baseline/previous, scan2 is current/latest.
    """
    scan1 = db.query(Scan).filter(Scan.id == scan1_id).first()
    scan2 = db.query(Scan).filter(Scan.id == scan2_id).first()

    if not scan1 or not scan2:
        raise ValueError("One or both scans not found")

    if scan1.target_id != scan2.target_id:
        raise ValueError(
            f"Scans belong to different targets (target {scan1.target_id} vs {scan2.target_id}). Comparison is only valid for the same target."
        )

    # 1. Compare Hosts
    assets1 = db.query(Asset).filter(Asset.scan_id == scan1_id).all()
    assets2 = db.query(Asset).filter(Asset.scan_id == scan2_id).all()

    hosts1_map = {a.ip: a for a in assets1}
    hosts2_map = {a.ip: a for a in assets2}

    ips1 = set(hosts1_map.keys())
    ips2 = set(hosts2_map.keys())

    added_hosts = sorted(list(ips2 - ips1))
    removed_hosts = sorted(list(ips1 - ips2))
    unchanged_hosts = sorted(list(ips1 & ips2))

    # 2. Compare Ports & Services
    ports1 = (
        db.query(Port, Asset.ip)
        .join(Asset, Port.asset_id == Asset.id)
        .filter(Asset.scan_id == scan1_id, Port.state == "open")
        .all()
    )
    ports2 = (
        db.query(Port, Asset.ip)
        .join(Asset, Port.asset_id == Asset.id)
        .filter(Asset.scan_id == scan2_id, Port.state == "open")
        .all()
    )

    port1_dict = {
        (ip, p.port_number, p.protocol): p
        for p, ip in ports1
    }
    port2_dict = {
        (ip, p.port_number, p.protocol): p
        for p, ip in ports2
    }

    keys1 = set(port1_dict.keys())
    keys2 = set(port2_dict.keys())

    added_ports = []
    for k in sorted(keys2 - keys1):
        p = port2_dict[k]
        added_ports.append({
            "ip": k[0],
            "port_number": k[1],
            "protocol": k[2],
            "service": p.service,
            "product": p.product,
            "version": p.version,
        })

    removed_ports = []
    for k in sorted(keys1 - keys2):
        p = port1_dict[k]
        removed_ports.append({
            "ip": k[0],
            "port_number": k[1],
            "protocol": k[2],
            "service": p.service,
            "product": p.product,
            "version": p.version,
        })

    changed_services = []
    for k in sorted(keys1 & keys2):
        p1 = port1_dict[k]
        p2 = port2_dict[k]
        if (p1.service != p2.service) or (p1.product != p2.product) or (p1.version != p2.version):
            changed_services.append({
                "ip": k[0],
                "port_number": k[1],
                "protocol": k[2],
                "before": {
                    "service": p1.service,
                    "product": p1.product,
                    "version": p1.version,
                },
                "after": {
                    "service": p2.service,
                    "product": p2.product,
                    "version": p2.version,
                }
            })

    # 3. Compare Findings (matched by rule_id and asset IP if applicable)
    findings1 = db.query(Finding).filter(Finding.scan_id == scan1_id).all()
    findings2 = db.query(Finding).filter(Finding.scan_id == scan2_id).all()

    # Map finding to a comparison key: (rule_id, asset_ip or 'global')
    def finding_key(f: Finding) -> tuple:
        asset_ip = f.asset.ip if f.asset else "global"
        return (f.rule_id, asset_ip)

    f1_map = {finding_key(f): f for f in findings1}
    f2_map = {finding_key(f): f for f in findings2}

    f1_keys = set(f1_map.keys())
    f2_keys = set(f2_map.keys())

    new_findings = [FindingResponse.model_validate(f2_map[k]) for k in (f2_keys - f1_keys)]
    resolved_findings = [FindingResponse.model_validate(f1_map[k]) for k in (f1_keys - f2_keys)]
    persistent_findings = [FindingResponse.model_validate(f2_map[k]) for k in (f1_keys & f2_keys)]

    return ComparisonResponse(
        scan1_id=scan1_id,
        scan2_id=scan2_id,
        target_id=scan1.target_id,
        target_name=scan1.target.name if scan1.target else "Target",
        target_str=scan1.target.target if scan1.target else "",
        added_hosts=added_hosts,
        removed_hosts=removed_hosts,
        unchanged_hosts=unchanged_hosts,
        added_ports=added_ports,
        removed_ports=removed_ports,
        changed_services=changed_services,
        new_findings=new_findings,
        resolved_findings=resolved_findings,
        persistent_findings=persistent_findings,
    )
