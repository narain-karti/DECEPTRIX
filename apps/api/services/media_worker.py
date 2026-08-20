import asyncio
from sqlalchemy.orm import Session
import uuid
import datetime

from models.orm import Job
from schemas.common import EvidenceEvent

async def process_media_job(job_id: str, db: Session):
    # Simulate processing stages
    # 1. Validation & Metadata extraction
    await asyncio.sleep(2)
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return
    job.progress = 20
    db.commit()
    
    # 2. Frame Extraction
    await asyncio.sleep(2)
    job.progress = 50
    db.commit()
    
    # 3. Model Inference (Mock)
    await asyncio.sleep(2)
    
    evidence = EvidenceEvent(
        event_id=str(uuid.uuid4()),
        case_id=job_id,
        modality="media",
        type="visual_manipulation",
        status="completed",
        score_or_null=0.85,
        severity="high",
        confidence_quality="high",
        explanation="Detected inconsistent shadows and unnatural facial boundary blending.",
        model_or_connector="MockDetector-v1",
        version="1.0",
        created_at=datetime.datetime.utcnow()
    )
    
    job.progress = 90
    db.commit()
    
    # 4. Finalization
    await asyncio.sleep(1)
    
    job.progress = 100
    job.status = "completed"
    job.verdict = "Likely Manipulated"
    job.evidence = [evidence.model_dump()]
    job.completed_at = datetime.datetime.utcnow()
    db.commit()
