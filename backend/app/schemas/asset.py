from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.schemas.port import PortResponse

class AssetResponse(BaseModel):
    id: int
    scan_id: int
    ip: str
    hostname: Optional[str] = None
    status: Optional[str] = None
    os: Optional[str] = None
    discovered_at: datetime
    ports: List[PortResponse] = []

    model_config = ConfigDict(from_attributes=True)
