from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)
    rule_id = Column(String(50), nullable=False)        # e.g., R001
    category = Column(String(100), nullable=False)      # e.g., service_exposure, fingerprinting, dns_security
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False)       # high, medium, low, informational
    evidence = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)         # nmap, dns, recon, zap
    recommendation = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    scan = relationship("Scan", back_populates="findings")
    asset = relationship("Asset", back_populates="findings")
