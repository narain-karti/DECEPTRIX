import asyncio
from sqlalchemy.orm import Session
import uuid
import datetime

from models.orm import Job
from schemas.common import EvidenceEvent
from schemas.text import ClaimItem

async def process_text_audit(job_id: str, db: Session):
    # Simulate text audit stages
    await asyncio.sleep(1)
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return
    
    job.progress = 25
    db.commit()
    
    # Simulate claim extraction and evidence retrieval
    await asyncio.sleep(2)
    
    job.progress = 75
    db.commit()
    
    await asyncio.sleep(1)
    
    # Mock evidence
    evidence = EvidenceEvent(
        event_id=str(uuid.uuid4()),
        case_id=job_id,
        modality="text",
        type="source_retrieval",
        status="completed",
        explanation="Found authoritative contradiction in Tier 1 sources.",
        model_or_connector="SearchFusion-v1",
        version="1.0",
        created_at=datetime.datetime.utcnow()
    )
    
    mock_claims = [
        ClaimItem(
            claim_id=str(uuid.uuid4()),
            text="The government has announced a new digital currency.",
            outcome="Contradicted",
            citations=[{"url": "https://gov.example.com", "tier": 1}]
        ).model_dump()
    ]
    
    job.progress = 100
    job.status = "completed"
    job.verdict = "Contradicted"
    job.evidence = [evidence.model_dump()]
    job.report_data = {"extracted_claims": mock_claims}
    job.completed_at = datetime.datetime.utcnow()
    db.commit()
