from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import json

from core.database import get_db
from models.orm import Job

router = APIRouter()

@router.get("/{report_id}.json")
async def get_report_json(report_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == report_id).first()
    if not job or job.status != "completed":
        raise HTTPException(status_code=404, detail="Report not ready or not found")
        
    report = {
        "report_id": job.id,
        "modality": job.modality,
        "created_at": job.completed_at.isoformat() if job.completed_at else None,
        "verdict": job.verdict,
        "evidence": job.evidence,
        "details": job.report_data
    }
    
    return Response(content=json.dumps(report, indent=2), media_type="application/json")

@router.get("/{report_id}.pdf")
async def get_report_pdf(report_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == report_id).first()
    if not job or job.status != "completed":
        raise HTTPException(status_code=404, detail="Report not ready or not found")
        
    # Mock PDF response for MVP
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    return Response(content=pdf_content, media_type="application/pdf")
