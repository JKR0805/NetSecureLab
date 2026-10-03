from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    target = Column(String(255), nullable=False)
    target_type = Column(String(50), nullable=False)  # ip, hostname, domain, web_application
    description = Column(Text, nullable=True)
    authorization_confirmed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    scans = relationship("Scan", back_populates="target", cascade="all, delete-orphan")
    dns_records = relationship("DNSRecord", back_populates="target", cascade="all, delete-orphan")
    recon_results = relationship("ReconResult", back_populates="target", cascade="all, delete-orphan")
