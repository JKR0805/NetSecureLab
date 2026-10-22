from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.target import Target
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.port import Port
from app.models.finding import Finding

router = APIRouter(prefix="/topology", tags=["topology"])


@router.get("")
def get_network_topology(
    target_id: Optional[int] = Query(None, description="Optional target ID to focus topology on"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns a unified network graph (nodes and links) representing:
    Targets -> Discovered Hosts/Assets -> Exposed Services/Ports -> Vulnerabilities/Findings
    """
    nodes: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []

    targets_query = db.query(Target)
    if target_id:
        targets_query = targets_query.filter(Target.id == target_id)
    targets = targets_query.all()

    for target in targets:
        # Get latest completed scan for this target
        latest_scan = (
            db.query(Scan)
            .filter(Scan.target_id == target.id, Scan.status == "completed")
            .order_by(Scan.id.desc())
            .first()
        )

        target_findings = (
            db.query(Finding)
            .join(Scan, Finding.scan_id == Scan.id)
            .filter(Scan.target_id == target.id)
            .all()
        )

        findings_summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for f in target_findings:
            if f.severity in findings_summary:
                findings_summary[f.severity] += 1

        target_node_id = f"target-{target.id}"
        nodes.append({
            "id": target_node_id,
            "label": target.target,
            "type": "target",
            "target_type": target.target_type,
            "description": target.description or "",
            "authorization_confirmed": target.authorization_confirmed,
            "findings_count": findings_summary,
            "has_scans": latest_scan is not None,
        })

        if latest_scan:
            assets = db.query(Asset).filter(Asset.scan_id == latest_scan.id).all()
            for asset in assets:
                asset_node_id = f"asset-{asset.id}"
                nodes.append({
                    "id": asset_node_id,
                    "label": f"{asset.ip}" + (f" ({asset.hostname})" if asset.hostname else ""),
                    "ip": asset.ip,
                    "hostname": asset.hostname,
                    "os": asset.os or "Unknown OS",
                    "status": asset.status or "up",
                    "type": "host",
                    "parent_id": target_node_id,
                })
                links.append({
                    "source": target_node_id,
                    "target": asset_node_id,
                    "relation": "discovers",
                })

                # Ports for this asset
                ports = db.query(Port).filter(Port.asset_id == asset.id).all()
                for port in ports:
                    port_node_id = f"port-{port.id}"
                    nodes.append({
                        "id": port_node_id,
                        "label": f"{port.port_number}/{port.protocol} ({port.service or 'unknown'})",
                        "port_number": port.port_number,
                        "protocol": port.protocol,
                        "service": port.service or "unknown",
                        "state": port.state,
                        "product": port.product or "",
                        "version": port.version or "",
                        "type": "service",
                        "parent_id": asset_node_id,
                    })
                    links.append({
                        "source": asset_node_id,
                        "target": port_node_id,
                        "relation": "exposes",
                    })

            # Findings associated with this scan
            findings = db.query(Finding).filter(Finding.scan_id == latest_scan.id).all()
            for finding in findings:
                finding_node_id = f"finding-{finding.id}"
                parent_id = f"asset-{finding.asset_id}" if finding.asset_id else target_node_id
                nodes.append({
                    "id": finding_node_id,
                    "label": finding.title,
                    "severity": finding.severity,
                    "rule_id": finding.rule_id,
                    "status": finding.status,
                    "source": finding.source,
                    "type": "vulnerability",
                    "parent_id": parent_id,
                })

                links.append({
                    "source": parent_id,
                    "target": finding_node_id,
                    "relation": "vulnerability_in",
                })

    return {
        "nodes": nodes,
        "links": links,
        "stats": {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "targets": sum(1 for n in nodes if n["type"] == "target"),
            "hosts": sum(1 for n in nodes if n["type"] == "host"),
            "services": sum(1 for n in nodes if n["type"] == "service"),
            "vulnerabilities": sum(1 for n in nodes if n["type"] == "vulnerability"),
        },
    }
