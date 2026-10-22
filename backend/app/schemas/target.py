from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field

TargetType = Literal["ip", "hostname", "domain", "web_application"]
ScheduleIntervalType = Literal["none", "daily", "weekly", "monthly"]

class TargetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    target: str = Field(..., min_length=1, max_length=255)
    target_type: TargetType
    description: Optional[str] = None

class TargetCreate(TargetBase):
    authorization_confirmed: bool = Field(..., description="Technical confirmation that scanning is authorized")
    schedule_interval: Optional[ScheduleIntervalType] = None
    schedule_profile: Optional[str] = "standard"

class TargetScheduleUpdate(BaseModel):
    schedule_interval: Optional[ScheduleIntervalType] = None
    schedule_profile: Optional[str] = "standard"

class TargetResponse(TargetBase):
    id: int
    authorization_confirmed: bool
    created_at: datetime
    scan_count: int = 0
    schedule_interval: Optional[str] = None
    schedule_profile: Optional[str] = "standard"
    last_scheduled_at: Optional[datetime] = None
    next_scheduled_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
