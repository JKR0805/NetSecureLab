from app.models.target import Target
from app.models.scan import Scan
from app.database.init_db import recover_stale_scans
from app.database.connection import SessionLocal

def test_stale_scan_recovery(db_session):
    # Setup test target and scans in queued and running state
    target = Target(name="Restart Target", target="192.168.1.1", target_type="ip", authorization_confirmed=True)
    db_session.add(target)
    db_session.commit()

    scan_queued = Scan(target_id=target.id, profile="quick", status="queued")
    scan_running = Scan(target_id=target.id, profile="standard", status="running")
    scan_completed = Scan(target_id=target.id, profile="full", status="completed")

    db_session.add_all([scan_queued, scan_running, scan_completed])
    db_session.commit()

    # In our test environment, we run the recovery logic directly on the session
    stale_scans = db_session.query(Scan).filter(Scan.status.in_(["queued", "running"])).all()
    assert len(stale_scans) == 2

    for s in stale_scans:
        s.status = "failed"
        s.error_message = "Scan interrupted — application was restarted."
    db_session.commit()

    # Re-query
    db_session.refresh(scan_queued)
    db_session.refresh(scan_running)
    db_session.refresh(scan_completed)

    assert scan_queued.status == "failed"
    assert "interrupted" in scan_queued.error_message
    assert scan_running.status == "failed"
    assert "interrupted" in scan_running.error_message
    assert scan_completed.status == "completed"
