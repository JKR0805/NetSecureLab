from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

if "sqlite" in settings.DB_URL and "///" in settings.DB_URL:
    db_file_str = settings.DB_URL.replace("sqlite:///", "")
    if db_file_str and ":memory:" not in db_file_str:
        Path(db_file_str).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.DB_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DB_URL else {},
    echo=settings.DEBUG,
)

# Enable foreign key constraint checking in SQLite on every connection
if "sqlite" in settings.DB_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
