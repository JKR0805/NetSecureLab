from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from tests.conftest import TestingSessionLocal
from app.workers.scheduler import ScanScheduler
from app.models.target import Target
from app.models.scan import Scan


def test_scheduler_triggers_due_scan(db_session, monkeypatch):
    scheduler = ScanScheduler(check_interval_seconds=10)
    now = datetime.now(timezone.utc)

    # 1. Target with schedule due in the past
    target = Target(
        name="Scheduled Target",
        target="10.0.0.1",
        target_type="ip",
        authorization_confirmed=True,
        schedule_interval="daily",
        schedule_profile="quick",
        next_scheduled_at=now - timedelta(hours=1),
    )
    db_session.add(target)
    db_session.commit()
    target_id = target.id

    monkeypatch.setattr("app.workers.scheduler.SessionLocal", TestingSessionLocal)
    mock_submit = MagicMock()
    monkeypatch.setattr("app.workers.scheduler.scan_worker.submit", mock_submit)

    scheduler.check_and_trigger_scheduled_scans()

    # Verify a new scan was queued and submitted
    scans = db_session.query(Scan).filter(Scan.target_id == target_id).all()
    assert len(scans) == 1
    assert scans[0].profile == "quick"
    assert scans[0].status == "queued"
    assert mock_submit.call_count == 1

    # Verify target's next_scheduled_at was updated to future
    db_session.expire_all()
    refreshed_target = db_session.query(Target).filter(Target.id == target_id).first()
    next_dt = refreshed_target.next_scheduled_at
    if next_dt.tzinfo is None:
        next_dt = next_dt.replace(tzinfo=timezone.utc)
    assert next_dt > now


def test_scheduler_skips_when_active_scan_exists(db_session, monkeypatch):
    scheduler = ScanScheduler(check_interval_seconds=10)
    now = datetime.now(timezone.utc)

    target = Target(
        name="Busy Target",
        target="10.0.0.2",
        target_type="ip",
        authorization_confirmed=True,
        schedule_interval="weekly",
        next_scheduled_at=now - timedelta(minutes=5),
    )
    db_session.add(target)
    db_session.commit()

    target_id = target.id

    # Pre-existing active scan
    existing_scan = Scan(target_id=target.id, profile="standard", status="running")
    db_session.add(existing_scan)
    db_session.commit()

    monkeypatch.setattr("app.workers.scheduler.SessionLocal", TestingSessionLocal)
    mock_submit = MagicMock()
    monkeypatch.setattr("app.workers.scheduler.scan_worker.submit", mock_submit)

    scheduler.check_and_trigger_scheduled_scans()

    # Should not queue a duplicate scan
    scans = db_session.query(Scan).filter(Scan.target_id == target_id).all()
    assert len(scans) == 1
    assert mock_submit.call_count == 0
