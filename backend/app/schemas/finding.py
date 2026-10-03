from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

SeverityType = Literal["high", "medium", "low", "informational"]

class FindingResponse(BaseModel):
    id: int
    scan_id: int
    asset_id: Optional[int] = None
    rule_id: str
    category: str
    title: str
    description: str
    severity: SeverityType
    evidence: str
    source: str
    recommendation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
