import pytest
from app.models.target import Target
from app.models.scan import Scan

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "NetSecureLab"

def test_create_valid_authorized_target(client):
    payload = {
        "name": "Local Lab Subnet",
        "target": "192.168.1.10",
        "target_type": "ip",
        "description": "Internal test machine",
        "authorization_confirmed": True,
    }
    response = client.post("/targets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Local Lab Subnet"
    assert data["authorization_confirmed"] is True

def test_create_target_invalid_input(client):
    # Invalid IP format
    payload = {
        "name": "Bad IP",
        "target": "999.999.999.999",
        "target_type": "ip",
        "authorization_confirmed": True,
    }
    response = client.post("/targets", json=payload)
    assert response.status_code == 422

    # Shell injection attempt
    payload_injection = {
        "name": "Injection Test",
        "target": "192.168.1.1; cat /etc/passwd",
        "target_type": "ip",
        "authorization_confirmed": True,
    }
    response2 = client.post("/targets", json=payload_injection)
    assert response2.status_code == 422

def test_unauthorized_target_scan_rejection(client):
    # Create target with authorization_confirmed = False
    payload = {
        "name": "Unauthorized Target",
        "target": "192.168.1.20",
        "target_type": "ip",
        "authorization_confirmed": False,
    }
    res = client.post("/targets", json=payload)
    target_id = res.json()["id"]

    # Attempt to start scan
    scan_payload = {
        "target_id": target_id,
        "profile": "standard",
    }
    scan_res = client.post("/scans", json=scan_payload)
    assert scan_res.status_code == 403
    assert "Authorization required" in scan_res.json()["detail"]

def test_target_deletion_restriction_with_scans(client, db_session):
    # Create authorized target
    t = Target(
        name="Target with Scan",
        target="10.0.0.5",
        target_type="ip",
        authorization_confirmed=True,
    )
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)

    # Attach a scan
    s = Scan(
        target_id=t.id,
        profile="quick",
        status="completed",
    )
    db_session.add(s)
    db_session.commit()

    # Try to delete target
    del_res = client.delete(f"/targets/{t.id}")
    assert del_res.status_code == 409
    assert "associated scan" in del_res.json()["detail"]
