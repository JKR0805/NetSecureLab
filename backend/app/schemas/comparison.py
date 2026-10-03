from typing import List, Dict, Any
from pydantic import BaseModel
from app.schemas.finding import FindingResponse

class ComparisonResponse(BaseModel):
    scan1_id: int
    scan2_id: int
    target_id: int
    target_name: str
    target_str: str
    added_hosts: List[str] = []
    removed_hosts: List[str] = []
    unchanged_hosts: List[str] = []
    added_ports: List[Dict[str, Any]] = []
    removed_ports: List[Dict[str, Any]] = []
    changed_services: List[Dict[str, Any]] = []
    new_findings: List[FindingResponse] = []
    resolved_findings: List[FindingResponse] = []
    persistent_findings: List[FindingResponse] = []
