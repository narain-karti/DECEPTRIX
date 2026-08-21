from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from core.database import get_db
from models.orm import Job
from schemas.text import TextAuditRequest, TextAuditResponse, ClaimItem
from schemas.common import EvidenceEvent
from services.text_worker import process_text_audit

router = APIRouter()

@router.post("/audits", response_model=TextAuditResponse)
async def create_text_audit(
    request: TextAuditRequest,
    db: Session = Depends(get_db)
):
    job_id = str(uuid.uuid4())
    
    job = Job(
        id=job_id,
        modality="text",
        status="pending",
        progress=0,
        text_content=request.text
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    process_text_audit.delay(job_id)
    
    return TextAuditResponse(
        id=job.id,
        status=job.status,
        extracted_claims=[],
        audit_trail=[]
    )

@router.get("/audits/{audit_id}", response_model=TextAuditResponse)
async def get_text_audit(audit_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == audit_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Audit not found")
        
    claims = []
    if job.report_data and "extracted_claims" in job.report_data:
        claims = [ClaimItem(**c) for c in job.report_data["extracted_claims"]]
        
    evidence_events = []
    if job.evidence:
        evidence_events = [EvidenceEvent(**e) for e in job.evidence]
        
    return TextAuditResponse(
        id=job.id,
        status=job.status,
        progress=job.progress or 0,
        current_step=job.current_step,
        extracted_claims=claims,
        audit_trail=evidence_events,
        report_links={
            "json": f"/api/v1/reports/{job.id}.json",
            "pdf": f"/api/v1/reports/{job.id}.pdf"
        } if job.status == "completed" else None
    )
