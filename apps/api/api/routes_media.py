from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import uuid
import os
import hashlib

from core.database import get_db
from core.config import settings
from models.orm import Job
from schemas.media import MediaJobResponse, MediaResultResponse
from schemas.common import EvidenceEvent
from services.media_worker import process_media_job

router = APIRouter()

ALLOWED_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
ALLOWED_EXTS = {".mp4", ".webm", ".mov"}
MAX_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB

@router.post("/jobs", response_model=MediaJobResponse)
async def create_media_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}. Accepted: MP4, WebM, MOV.")

    # Validate extension
    _, ext = os.path.splitext(file.filename or "")
    ext = ext.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}. Accepted: .mp4, .webm, .mov")

    job_id = str(uuid.uuid4())

    # Save file with safe name (job_id + validated extension)
    safe_filename = f"{job_id}{ext}"
    file_path = os.path.join(settings.STORAGE_DIR, safe_filename)

    sha256_hash = hashlib.sha256()
    with open(file_path, "wb") as buffer:
        total_size = 0
        while chunk := await file.read(65536):
            total_size += len(chunk)
            if total_size > MAX_SIZE_BYTES:
                buffer.close()
                os.remove(file_path)
                raise HTTPException(status_code=400, detail=f"File too large. Maximum size: 200 MB.")
            buffer.write(chunk)
            sha256_hash.update(chunk)

    job = Job(
        id=job_id,
        modality="media",
        status="pending",
        progress=0,
        filename=file.filename,
        file_path=file_path,
        sha256=sha256_hash.hexdigest()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch to Celery worker (not in-process)
    process_media_job.delay(job_id)

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
        
    evidence_events = []
    if job.evidence:
        evidence_events = [EvidenceEvent(**e) for e in job.evidence]

    return MediaJobResponse(
        id=job.id,
        status=job.status,
        progress=job.progress or 0,
        filename=job.filename,
        sha256=job.sha256,
        current_step=job.current_step,
        evidence=evidence_events,
        report_data=job.report_data
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
        report_data=job.report_data,
        report_links={
            "json": f"/api/v1/reports/{job.id}.json",
            "pdf": f"/api/v1/reports/{job.id}.pdf"
        }
    )
