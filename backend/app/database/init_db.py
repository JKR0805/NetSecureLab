from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database.connection import engine, Base, SessionLocal
import app.models  # ensure all models are registered
from app.models.scan import Scan
from app.utils.logger import logger


def run_auto_migrations(engine_obj):
    """Adds missing columns to SQLite database if they don't exist."""
    migrations = [
        ("targets", "schedule_interval", "VARCHAR(50)"),
        ("targets", "schedule_profile", "VARCHAR(50) DEFAULT 'standard'"),
        ("targets", "last_scheduled_at", "DATETIME"),
        ("targets", "next_scheduled_at", "DATETIME"),
        ("findings", "status", "VARCHAR(50) DEFAULT 'open'"),
        ("findings", "notes", "TEXT"),
        ("ports", "scripts", "TEXT"),
    ]
    with engine_obj.connect() as conn:
        for table, col, col_type in migrations:
            try:
                res = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                existing_cols = [r[1] for r in res]
                if existing_cols and col not in existing_cols:
                    logger.info(f"Adding missing column {col} to table {table}...")
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                    conn.commit()
            except Exception as e:
                logger.debug(f"Migration check for {table}.{col}: {e}")


def init_db():
    """Create all tables and perform startup maintenance."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    run_auto_migrations(engine)
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
