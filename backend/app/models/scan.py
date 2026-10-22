from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="RESTRICT"), nullable=False)
    profile = Column(String(50), nullable=False)  # quick, standard, full
    status = Column(String(50), nullable=False, default="created")  # created, queued, running, completed, failed, cancelled
    cancel_requested = Column(Boolean, nullable=False, default=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # seconds
    nmap_status = Column(String(50), nullable=False, default="pending")  # pending, success, failed, skipped
    dns_status = Column(String(50), nullable=False, default="pending")   # pending, success, partial, failed, skipped
    recon_status = Column(String(50), nullable=False, default="pending") # pending, success, partial, failed, skipped
    raw_output_path = Column(String(512), nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    target = relationship("Target", back_populates="scans")
    assets = relationship("Asset", back_populates="scan", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
    dns_records = relationship("DNSRecord", back_populates="scan", cascade="all, delete-orphan")
    recon_results = relationship("ReconResult", back_populates="scan", cascade="all, delete-orphan")
