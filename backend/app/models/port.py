from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Port(Base):
    __tablename__ = "ports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    port_number = Column(Integer, nullable=False)
    protocol = Column(String(20), nullable=False)  # tcp, udp
    state = Column(String(50), nullable=False)     # open, closed, filtered
    service = Column(String(100), nullable=True)
    product = Column(String(100), nullable=True)
    version = Column(String(100), nullable=True)
    extra_info = Column(String(255), nullable=True)
    scripts = Column(Text, nullable=True)  # JSON-encoded array of NSE script outputs: [{id, output}]

    __table_args__ = (
        UniqueConstraint("asset_id", "port_number", "protocol", name="uq_port_asset_port_protocol"),
    )

    # Relationships
    asset = relationship("Asset", back_populates="ports")
