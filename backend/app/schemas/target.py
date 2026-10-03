from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

TargetType = Literal["ip", "hostname", "domain", "web_application"]

class TargetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    target: str = Field(..., min_length=1, max_length=255)
    target_type: TargetType
    description: Optional[str] = None

class TargetCreate(TargetBase):
    authorization_confirmed: bool = Field(..., description="Technical confirmation that scanning is authorized")

class TargetResponse(TargetBase):
    id: int
    authorization_confirmed: bool
    created_at: datetime
    scan_count: int = 0

    model_config = ConfigDict(from_attributes=True)
