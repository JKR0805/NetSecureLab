from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    ip = Column(String(100), nullable=False)
    hostname = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)  # up, down
    os = Column(String(255), nullable=True)
    discovered_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("scan_id", "ip", name="uq_asset_scan_ip"),
    )

    # Relationships
    scan = relationship("Scan", back_populates="assets")
    ports = relationship("Port", back_populates="asset", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="asset")
