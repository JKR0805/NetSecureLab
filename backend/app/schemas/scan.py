from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.target import TargetResponse

ProfileType = Literal["quick", "standard", "full"]

class ScanCreate(BaseModel):
    target_id: int
    profile: ProfileType = "standard"

class ScanResponse(BaseModel):
    id: int
    target_id: int
    profile: str
    status: str
    cancel_requested: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    nmap_status: str = "pending"
    dns_status: str = "pending"
    recon_status: str = "pending"
    raw_output_available: bool = False
    error_message: Optional[str] = None
    target: Optional[TargetResponse] = None
    findings_count: int = 0
    assets_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class ScanStatusResponse(BaseModel):
    id: int
    status: str
    cancel_requested: bool
    nmap_status: str
    dns_status: str
    recon_status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
