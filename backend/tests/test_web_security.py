import pytest
from unittest.mock import MagicMock, patch
from app.services.web_security.scanner import inspect_http_endpoint, run_web_assessment
from app.models.target import Target
from app.models.scan import Scan
from app.models.asset import Asset
from app.models.port import Port
from app.models.finding import Finding


def test_inspect_http_endpoint_detects_missing_headers():
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Headers missing HSTS, CSP, XFO, X-Content-Type-Options
    mock_response.headers = {
        "Server": "Apache/2.4.41 (Ubuntu)",
        "X-Powered-By": "PHP/7.4.3",
    }
    mock_response.cookies.jar = []
    mock_response.text = "Welcome to test"

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_cls.return_value = mock_client

        findings = inspect_http_endpoint("https://example.com")

        rule_ids = [f["rule_id"] for f in findings]
        assert "WEB-001" in rule_ids  # Missing HSTS on HTTPS
        assert "WEB-002" in rule_ids  # Missing CSP
        assert "WEB-003" in rule_ids  # Missing Clickjacking protection
        assert "WEB-004" in rule_ids  # Missing X-Content-Type-Options
        assert "WEB-005" in rule_ids  # Server banner disclosure

        for f in findings:
            assert f["source"] == "zap"


def test_run_web_assessment_integration(db_session, monkeypatch):
    target = Target(name="Web Target", target="127.0.0.1", target_type="ip", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan = Scan(target_id=target.id, profile="standard", status="running")
    db_session.add(scan)
    db_session.commit()

    asset = Asset(scan_id=scan.id, ip="127.0.0.1")
    db_session.add(asset)
    db_session.commit()

    port = Port(asset_id=asset.id, port_number=80, protocol="tcp", state="open", service="http")
    db_session.add(port)
    db_session.commit()

    mock_findings = [
        {
            "rule_id": "WEB-002",
            "category": "Web Security",
            "title": "Missing Content Security Policy (CSP)",
            "description": "No CSP found.",
            "severity": "medium",
            "evidence": "Headers empty",
            "source": "zap",
            "recommendation": "Add CSP header",
        }
    ]

    monkeypatch.setattr("app.services.web_security.scanner.inspect_http_endpoint", lambda url: mock_findings)

    created = run_web_assessment(scan.id, db_session)
    assert len(created) == 1
    assert created[0].rule_id == "WEB-002"
    assert created[0].source == "zap"

    stored = db_session.query(Finding).filter(Finding.scan_id == scan.id).all()
    assert len(stored) == 1
    assert stored[0].source == "zap"
