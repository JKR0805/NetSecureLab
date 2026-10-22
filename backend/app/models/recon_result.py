from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.connection import Base

class ReconResult(Base):
    __tablename__ = "recon_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=True)
    category = Column(String(100), nullable=False)  # domain_info, registrar, nameserver, geolocation, etc.
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)     # whois, dns, ip_api, etc.
    collected_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("scan_id", "category", "key", "value", "source", name="uq_recon_scan_cat_key_val_src"),
    )

    # Relationships
    target = relationship("Target", back_populates="recon_results")
    scan = relationship("Scan", back_populates="recon_results")
