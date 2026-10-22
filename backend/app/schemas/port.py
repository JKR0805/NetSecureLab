from typing import Optional
from pydantic import BaseModel, ConfigDict

class PortResponse(BaseModel):
    id: int
    asset_id: int
    port_number: int
    protocol: str
    state: str
    service: Optional[str] = None
    product: Optional[str] = None
    version: Optional[str] = None
    extra_info: Optional[str] = None
    scripts: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
