import glob
import os
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "api"))
os.environ["DATABASE_URL"] = "sqlite:///./apps/api/deceptrix.db"

from core.database import SessionLocal, engine
from models.orm import Job
import numpy as np
from services.media_worker import process_media_job

db = SessionLocal()
jobs = db.query(Job).filter(Job.modality == "media").order_by(Job.created_at.desc()).limit(5).all()

print(f"Found {len(jobs)} recent media jobs in database:")
for j in jobs:
    print(f"\n--- Job ID: {j.id} | Filename: {j.filename}")
    if os.path.exists(j.file_path):
        # Re-run calibrated processing
        print("Re-evaluating with calibrated ensemble pipeline...")
        process_media_job(j.id)
        db.refresh(j)
        rd = j.report_data or {}
        print(f"Result -> Verdict: {j.verdict} | Final Score: {rd.get('final_score', 0):.2f}")
        print(f"Signals -> {rd.get('signal_scores')}")
    else:
        print(f"File not found: {j.file_path}")

db.close()
