from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class DNSRecordResponse(BaseModel):
    id: int
    target_id: int
    scan_id: Optional[int] = None
    record_type: str
    name: str
    value: str
    ttl: Optional[int] = None
    collected_at: datetime

    model_config = ConfigDict(from_attributes=True)
