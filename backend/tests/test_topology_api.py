import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.target import Target
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.port import Port
from app.models.finding import Finding


def test_get_topology_empty(client):
    resp = client.get("/topology")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "links" in data
    assert "stats" in data
    assert data["stats"]["targets"] == 0


def test_get_topology_with_assets_and_findings(client, db_session):

    # 1. Create target
    target = Target(
        name="Topology Target",
        target="192.168.1.100",
        target_type="ip",
        authorization_confirmed=True,
    )
    db_session.add(target)
    db_session.commit()

    # 2. Completed scan
    scan = Scan(target_id=target.id, profile="quick", status="completed")
    db_session.add(scan)
    db_session.commit()

    # 3. Discovered asset and port
    asset = Asset(scan_id=scan.id, ip="192.168.1.100", hostname="gateway.local")
    db_session.add(asset)
    db_session.commit()

    port = Port(asset_id=asset.id, port_number=443, protocol="tcp", state="open", service="https")
    db_session.add(port)
    db_session.commit()

    # 4. Finding linked to port
    finding = Finding(
        scan_id=scan.id,
        asset_id=asset.id,
        rule_id="WEB-001",
        category="Web Security",
        title="Missing HSTS",
        description="Strict transport security header missing",
        severity="medium",
        evidence="Headers check",
        source="zap",
        recommendation="Enable HSTS",
    )
    db_session.add(finding)
    db_session.commit()

    # Query topology
    resp = client.get(f"/topology?target_id={target.id}")
    assert resp.status_code == 200
    data = resp.json()

    node_types = [n["type"] for n in data["nodes"]]
    assert "target" in node_types
    assert "host" in node_types
    assert "service" in node_types
    assert "vulnerability" in node_types

    assert data["stats"]["targets"] == 1
    assert data["stats"]["hosts"] == 1
    assert data["stats"]["services"] == 1
    assert data["stats"]["vulnerabilities"] == 1
    assert len(data["links"]) >= 3
