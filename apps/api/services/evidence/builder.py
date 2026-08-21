from typing import Dict, Any, Optional
import datetime
import uuid

class EvidenceBuilder:
    @staticmethod
    def build(
        modality: str,
        event_type: str,
        status: str,
        score: float,
        confidence: float,
        model: str,
        version: str,
        timestamp: Optional[float],
        severity: str,
        explanation: str,
        limitations: str,
        case_id: str
    ) -> Dict[str, Any]:
        """
        Creates a structured evidence JSON node as requested.
        """
        return {
            "event_id": str(uuid.uuid4()),
            "case_id": case_id,
            "modality": modality,
            "type": event_type,
            "status": status,
            "score_or_null": score,
            "confidence_quality": "high" if confidence > 0.7 else "medium",
            "model_or_connector": model,
            "version": version,
            "scope": f"timestamp_{timestamp}" if timestamp is not None else "full_file",
            "timestamp": timestamp,
            "severity": severity,
            "explanation": explanation,
            "limitations": limitations,
            "created_at": datetime.datetime.utcnow().isoformat()
        }
