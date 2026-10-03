from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ReconResultResponse(BaseModel):
    id: int
    target_id: int
    scan_id: Optional[int] = None
    category: str
    key: str
    value: str
    source: str
    collected_at: datetime

    model_config = ConfigDict(from_attributes=True)
