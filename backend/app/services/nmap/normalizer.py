from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.models.port import Port
from app.utils.logger import logger

def normalize_and_store_nmap_results(
    scan_id: int,
    parsed_data: Dict[str, Any],
    db: Session,
) -> List[Asset]:
    """
    Normalizes parsed Nmap output into Asset and Port ORM records.
    Ensures uniqueness constraints are respected and commits to DB.
    """
    saved_assets = []

    for host in parsed_data.get("hosts", []):
        ip = host.get("ip")
        if not ip:
            continue

        # Look up existing asset for this scan and IP
        asset = (
            db.query(Asset)
            .filter(Asset.scan_id == scan_id, Asset.ip == ip)
            .first()
        )

        if not asset:
            asset = Asset(
                scan_id=scan_id,
                ip=ip,
                hostname=host.get("hostname"),
                status=host.get("status", "unknown"),
                os=host.get("os"),
            )
            db.add(asset)
            db.flush()  # assign ID
        else:
            # Update attributes if discovered
            if host.get("hostname"):
                asset.hostname = host.get("hostname")
            if host.get("status"):
                asset.status = host.get("status")
            if host.get("os"):
                asset.os = host.get("os")

        # Process ports
        for p in host.get("ports", []):
            port_num = p.get("port_number")
            proto = p.get("protocol", "tcp")
            if port_num is None:
                continue

            existing_port = (
                db.query(Port)
                .filter(
                    Port.asset_id == asset.id,
                    Port.port_number == port_num,
                    Port.protocol == proto,
                )
                .first()
            )

            if not existing_port:
                new_port = Port(
                    asset_id=asset.id,
                    port_number=port_num,
                    protocol=proto,
                    state=p.get("state", "open"),
                    service=p.get("service"),
                    product=p.get("product"),
                    version=p.get("version"),
                    extra_info=p.get("extra_info"),
                )
                db.add(new_port)
            else:
                existing_port.state = p.get("state", existing_port.state)
                existing_port.service = p.get("service", existing_port.service)
                existing_port.product = p.get("product", existing_port.product)
                existing_port.version = p.get("version", existing_port.version)
                existing_port.extra_info = p.get("extra_info", existing_port.extra_info)

        saved_assets.append(asset)

    db.commit()
    logger.info(f"Normalized and stored {len(saved_assets)} asset snapshots for scan id={scan_id}")
    return saved_assets
