from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from core.database import get_db
from models.orm import Job
import json
import os
from fpdf import FPDF

router = APIRouter()

@router.get("/{job_id}.json")
def get_report_json(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return JSONResponse(content={
        "id": job.id,
        "modality": job.modality,
        "status": job.status,
        "verdict": job.verdict,
        "evidence": job.evidence,
        "report_data": job.report_data,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    })

@router.get("/{job_id}.pdf")
def get_report_pdf(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(200, 10, txt=f"DECEPTRIX Audit Report", ln=True, align='C')
    
    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, txt=f"Job ID: {job.id}", ln=True)
    pdf.cell(200, 10, txt=f"Modality: {job.modality}", ln=True)
    pdf.cell(200, 10, txt=f"Status: {job.status}", ln=True)
    pdf.cell(200, 10, txt=f"Verdict: {job.verdict}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(200, 10, txt="Evidence Timeline", ln=True)
    
    pdf.set_font("Helvetica", size=10)
    if job.evidence:
        for ev in job.evidence:
            typ = ev.get("type", "Unknown")
            score = ev.get("score_or_null")
            expl = ev.get("explanation", "")
            pdf.multi_cell(0, 10, txt=f"- {typ}: {expl} (Score: {score})")
            # If there's frame analysis, we can dump artifact refs
            refs = ev.get("artifact_refs")
            if refs:
                for ref in refs:
                    ts = ref.get("timestamp_sec")
                    faces = ref.get("faces", [])
                    if ts is not None:
                        pdf.cell(0, 5, txt=f"   Frame {ts}s - Faces detected: {len(faces)}", ln=True)
                        for face in faces:
                            face_crop_path = face.get("face_crop")
                            fake_score = face.get("fake_score", 0)
                            if face_crop_path and os.path.exists(face_crop_path):
                                pdf.cell(0, 5, txt=f"      Face Deepfake Score: {fake_score:.2f}", ln=True)
                                try:
                                    pdf.image(face_crop_path, w=30)
                                    pdf.ln(2)
                                except Exception as e:
                                    pdf.cell(0, 5, txt=f"      [Failed to embed image]", ln=True)
            pdf.ln(2)
    else:
        pdf.cell(200, 10, txt="No evidence collected.", ln=True)
        
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return Response(content=pdf_bytes, media_type="application/pdf")
