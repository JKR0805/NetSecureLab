import pytest
import csv
import io
import json
from app.models.target import Target
from app.models.scan import Scan
from app.models.finding import Finding

def test_findings_workflow_and_exports(client, db_session):
    # 1. Setup target, scan, and test finding
    target = Target(
        name="Finding Test Target",
        target="192.168.1.100",
        target_type="ip",
        authorization_confirmed=True,
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)

    scan = Scan(
        target_id=target.id,
        profile="standard",
        status="completed",
    )
    db_session.add(scan)
    db_session.commit()
    db_session.refresh(scan)

    finding = Finding(
        scan_id=scan.id,
        rule_id="R001",
        category="Service Exposure",
        title="Insecure Plaintext Telnet Port 23 Open",
        description="Telnet transmits authentication credentials in unencrypted plaintext.",
        severity="high",
        status="open",
        evidence="Port 23/tcp open (telnet)",
        source="nmap",
        recommendation="Disable Telnet daemon and enforce SSH.",
    )
    db_session.add(finding)
    db_session.commit()
    db_session.refresh(finding)

    # 2. Test GET /findings
    res = client.get("/findings")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    target_f = next(f for f in items if f["id"] == finding.id)
    assert target_f["status"] == "open"
    assert target_f["notes"] is None

    # 3. Test PATCH /findings/{id} to update status and notes
    patch_payload = {
        "status": "remediated",
        "notes": "Telnet service disabled via systemctl and firewall rule updated",
    }
    patch_res = client.patch(f"/findings/{finding.id}", json=patch_payload)
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["status"] == "remediated"
    assert updated_data["notes"] == patch_payload["notes"]

    # Verify DB persistence
    db_session.refresh(finding)
    assert finding.status == "remediated"
    assert finding.notes == patch_payload["notes"]

    # 4. Test GET /findings/export/csv
    csv_res = client.get("/findings/export/csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    csv_reader = csv.reader(io.StringIO(csv_res.text))
    rows = list(csv_reader)
    assert len(rows) >= 2  # Header + at least 1 finding row
    header = rows[0]
    assert "Rule ID" in header
    assert "Status" in header
    assert "Recommendation" in header
    assert any("R001" in row for row in rows[1:])

    # 5. Test GET /findings/export/json
    json_res = client.get("/findings/export/json")
    assert json_res.status_code == 200
    assert "application/json" in json_res.headers["content-type"]
    json_data = json_res.json()
    assert isinstance(json_data, list)
    assert any(f["rule_id"] == "R001" and f["status"] == "remediated" for f in json_data)
