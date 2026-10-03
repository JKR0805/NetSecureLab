import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database.connection import Base, get_db
import app.models  # register all models in Base.metadata
from app.main import app

import os
from pathlib import Path

TEST_DB_FILE = Path(__file__).parent / "test_netsecurelab.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"

engine_test = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)

@event.listens_for(engine_test, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope="function")
def db_session():
    """Provides a fresh database session for a test with tables created."""
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)
        if TEST_DB_FILE.exists():
            try:
                TEST_DB_FILE.unlink()
            except Exception:
                pass

@pytest.fixture(scope="function")
def client(db_session):
    """Provides TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
