from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from schemas.common import EvidenceEvent

class TextAuditRequest(BaseModel):
    text: str

class ClaimItem(BaseModel):
    claim_id: str
    text: str
    outcome: Optional[str] = None
    citations: List[Dict[str, Any]] = []

class TextAuditResponse(BaseModel):
    id: str
    status: str
    extracted_claims: List[ClaimItem] = []
    audit_trail: List[EvidenceEvent] = []
    report_links: Optional[dict] = None
