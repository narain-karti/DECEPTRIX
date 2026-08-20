from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import uuid
import os
import shutil

from core.database import get_db
from core.config import settings
from models.orm import Job
from schemas.media import MediaJobResponse, MediaResultResponse
from schemas.common import EvidenceEvent
from services.media_worker import process_media_job

router = APIRouter()

@router.post("/jobs", response_model=MediaJobResponse)
async def create_media_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    
    # Save file
    file_path = os.path.join(settings.STORAGE_DIR, f"{job_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    job = Job(
        id=job_id,
        modality="media",
        status="pending",
        progress=0,
        filename=file.filename,
        file_path=file_path,
        sha256="simulated-hash-12345"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    def process_media_job_wrapper(jid: str):
        try:
            process_media_job(jid)
        except Exception as e:
            import traceback
            traceback.print_exc()
            from core.database import SessionLocal
            db_local = SessionLocal()
            failed_job = db_local.query(Job).filter(Job.id == jid).first()
            if failed_job:
                failed_job.status = "failed"
                db_local.commit()
            db_local.close()

    background_tasks.add_task(process_media_job_wrapper, job_id)
    
    return MediaJobResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        filename=job.filename,
        sha256=job.sha256,
        current_step=job.current_step
    )

@router.get("/jobs/{job_id}", response_model=MediaJobResponse)
async def get_media_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return MediaJobResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        filename=job.filename,
        sha256=job.sha256,
        current_step=job.current_step
    )

@router.get("/jobs/{job_id}/result", response_model=MediaResultResponse)
async def get_media_job_result(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job or job.status != "completed":
        raise HTTPException(status_code=404, detail="Result not ready or job not found")
        
    evidence_events = []
    if job.evidence:
        evidence_events = [EvidenceEvent(**e) for e in job.evidence]
        
    return MediaResultResponse(
        id=job.id,
        verdict=job.verdict,
        timeline_evidence=evidence_events,
        report_links={
            "json": f"/api/v1/reports/{job.id}.json",
            "pdf": f"/api/v1/reports/{job.id}.pdf"
        }
    )
