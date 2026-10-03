from sqlalchemy.orm import Session
from app.database.connection import engine, Base, SessionLocal
import app.models  # ensure all models are registered
from app.models.scan import Scan
from app.utils.logger import logger

def init_db():
    """Create all tables and perform startup maintenance."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

def recover_stale_scans():
    """Recover scans left in queued or running states after application restart."""
    db: Session = SessionLocal()
    try:
        stale_scans = db.query(Scan).filter(Scan.status.in_(["queued", "running"])).all()
        if stale_scans:
            logger.warning(f"Found {len(stale_scans)} stale scan(s) from previous run. Marking as failed.")
            for scan in stale_scans:
                scan.status = "failed"
                scan.error_message = "Scan interrupted — application was restarted."
            db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error during stale scan recovery: {e}")
    finally:
        db.close()
