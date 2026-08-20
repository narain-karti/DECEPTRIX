from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class EvidenceEvent(BaseModel):
    event_id: str
    case_id: str
    modality: str
    type: str
    status: str # completed, unavailable, failed, not_applicable
    score_or_null: Optional[float] = None
    severity: Optional[str] = None
    confidence_quality: Optional[str] = None
    scope: Optional[str] = None
    explanation: Optional[str] = None
    source_refs: Optional[List[Dict[str, Any]]] = None
    artifact_refs: Optional[List[Dict[str, Any]]] = None
    model_or_connector: str
    version: str
    limitations: Optional[str] = None
    created_at: datetime
