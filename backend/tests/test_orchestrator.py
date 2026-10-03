from unittest.mock import patch, MagicMock
from app.models.target import Target
from app.models.scan import Scan
from app.services.scan_orchestrator import run_scan
from app.services.nmap.executor import NmapExecutionResult

from tests.conftest import TestingSessionLocal

def test_orchestrator_all_success(db_session, monkeypatch):
    target = Target(name="Orch Target", target="example.com", target_type="domain", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan = Scan(target_id=target.id, profile="quick", status="queued")
    db_session.add(scan)
    db_session.commit()

    # Use TestingSessionLocal so run_scan gets a connection to the shared test DB
    monkeypatch.setattr("app.services.scan_orchestrator.SessionLocal", TestingSessionLocal)

    # Mock Nmap executor
    def fake_nmap(scan_target, profile, output_xml_path, timeout=None):
        output_xml_path.parent.mkdir(parents=True, exist_ok=True)
        output_xml_path.write_text("<nmaprun></nmaprun>")
        return NmapExecutionResult(success=True, xml_path=output_xml_path)

    monkeypatch.setattr("app.services.scan_orchestrator.execute_nmap_scan", fake_nmap)
    monkeypatch.setattr("app.services.scan_orchestrator.parse_nmap_xml", lambda p: {"hosts": []})
    monkeypatch.setattr("app.services.scan_orchestrator.collect_and_store_dns", lambda tid, sid, norm, db: "success")
    monkeypatch.setattr("app.services.scan_orchestrator.collect_and_store_recon", lambda tid, sid, norm, db: "success")

    run_scan(scan.id)

    db_session.refresh(scan)
    assert scan.status == "completed"
    assert scan.nmap_status == "success"
    assert scan.dns_status == "success"
    assert scan.recon_status == "success"
    assert scan.duration is not None

def test_orchestrator_independent_modules_nmap_fails_dns_succeeds(db_session, monkeypatch):
    target = Target(name="Partial Failure Target", target="example.com", target_type="domain", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan = Scan(target_id=target.id, profile="quick", status="queued")
    db_session.add(scan)
    db_session.commit()

    monkeypatch.setattr("app.services.scan_orchestrator.SessionLocal", TestingSessionLocal)

    # Simulate Nmap failure (e.g. timeout / binary missing)
    mock_nmap = MagicMock(return_value=NmapExecutionResult(success=False, error_message="Nmap binary not found"))
    monkeypatch.setattr("app.services.scan_orchestrator.execute_nmap_scan", mock_nmap)
    monkeypatch.setattr("app.services.scan_orchestrator.collect_and_store_dns", lambda tid, sid, norm, db: "success")
    monkeypatch.setattr("app.services.scan_orchestrator.collect_and_store_recon", lambda tid, sid, norm, db: "success")

    run_scan(scan.id)

    db_session.refresh(scan)
    # Scan completed overall because DNS and Recon succeeded; Nmap failed independently
    assert scan.status == "completed"
    assert scan.nmap_status == "failed"
    assert scan.dns_status == "success"
    assert scan.recon_status == "success"
    assert "Nmap binary not found" in scan.error_message

def test_orchestrator_cancellation(db_session, monkeypatch):
    target = Target(name="Cancel Target", target="10.0.0.1", target_type="ip", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan = Scan(target_id=target.id, profile="quick", status="queued", cancel_requested=True)
    db_session.add(scan)
    db_session.commit()

    monkeypatch.setattr("app.services.scan_orchestrator.SessionLocal", TestingSessionLocal)

    run_scan(scan.id)

    db_session.refresh(scan)
    assert scan.status == "cancelled"
