from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

SeverityType = Literal["high", "medium", "low", "informational"]
FindingStatusType = Literal["open", "acknowledged", "accepted_risk", "remediated"]

class FindingUpdate(BaseModel):
    status: Optional[FindingStatusType] = None
    notes: Optional[str] = None

class FindingResponse(BaseModel):
    id: int
    scan_id: int
    asset_id: Optional[int] = None
    rule_id: str
    category: str
    title: str
    description: str
    severity: SeverityType
    status: str = "open"
    notes: Optional[str] = None
    evidence: str
    source: str
    recommendation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
