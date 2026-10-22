import time
import threading
from datetime import datetime, timezone, timedelta
from app.database.connection import SessionLocal
from app.models.target import Target
from app.models.scan import Scan
from app.workers.scan_worker import scan_worker
from app.utils.logger import logger

class ScanScheduler:
    def __init__(self, check_interval_seconds: int = 30):
        self.check_interval = check_interval_seconds
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="ScanScheduler", daemon=True)
        self._thread.start()
        logger.info("ScanScheduler started.")

    def shutdown(self):
        logger.info("Shutting down ScanScheduler...")
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        logger.info("ScanScheduler stopped.")

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.check_and_trigger_scheduled_scans()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
            
            # Wait for next interval or stop event
            self._stop_event.wait(timeout=self.check_interval)

    def check_and_trigger_scheduled_scans(self):
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            due_targets = db.query(Target).filter(
                Target.schedule_interval.isnot(None),
                Target.authorization_confirmed == True,
                Target.next_scheduled_at <= now,
            ).all()

            for target in due_targets:
                # Concurrency check: skip if an active scan is already queued or running
                active_count = db.query(Scan).filter(
                    Scan.target_id == target.id,
                    Scan.status.in_(["queued", "running"])
                ).count()

                if active_count > 0:
                    logger.info(f"Scheduler: Target {target.id} ({target.name}) already has active scan. Postponing.")
                    continue

                profile = target.schedule_profile or "standard"
                new_scan = Scan(
                    target_id=target.id,
                    profile=profile,
                    status="queued",
                    cancel_requested=False,
                    nmap_status="pending",
                    dns_status="pending",
                    recon_status="pending",
                )
                db.add(new_scan)
                db.commit()
                db.refresh(new_scan)

                logger.info(f"Scheduler triggered automated scan {new_scan.id} for target {target.id} ({profile})")
                scan_worker.submit(new_scan.id)

                # Calculate next run timestamp
                target.last_scheduled_at = now
                if target.schedule_interval == "daily":
                    target.next_scheduled_at = now + timedelta(days=1)
                elif target.schedule_interval == "weekly":
                    target.next_scheduled_at = now + timedelta(weeks=1)
                elif target.schedule_interval == "monthly":
                    target.next_scheduled_at = now + timedelta(days=30)
                else:
                    target.next_scheduled_at = None

                db.commit()
        finally:
            db.close()

scan_scheduler = ScanScheduler()
