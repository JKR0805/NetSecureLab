from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.connection import Base

class DNSRecord(Base):
    __tablename__ = "dns_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = Column(Integer, ForeignKey("targets.id", ondelete="CASCADE"), nullable=False)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=True)
    record_type = Column(String(20), nullable=False)  # A, AAAA, NS, MX, TXT, CNAME, SOA, PTR
    name = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    ttl = Column(Integer, nullable=True)
    collected_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("scan_id", "record_type", "name", "value", name="uq_dns_scan_type_name_val"),
    )

    # Relationships
    target = relationship("Target", back_populates="dns_records")
    scan = relationship("Scan", back_populates="dns_records")
