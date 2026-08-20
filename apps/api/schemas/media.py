from pydantic import BaseModel
from typing import Optional, List, Any

from schemas.common import EvidenceEvent

class MediaJobResponse(BaseModel):
    id: str
    status: str
    progress: int
    filename: Optional[str] = None
    sha256: Optional[str] = None
    current_step: Optional[str] = None

class MediaResultResponse(BaseModel):
    id: str
    verdict: Optional[str]
    timeline_evidence: List[EvidenceEvent] = []
    provenance: Optional[Any] = None
    report_links: dict
