import sys
import os

# Add apps/api to path
api_dir = os.path.join(os.path.dirname(__file__), "apps", "api")
if os.path.exists(api_dir):
    sys.path.insert(0, api_dir)
    os.chdir(api_dir)

from core.database import SessionLocal
from models.orm import Job
from api.routes_reports import get_report_pdf

db = SessionLocal()
latest_job = db.query(Job).filter(Job.modality == "media", Job.status == "completed").order_by(Job.created_at.desc()).first()

if not latest_job:
    print("No completed media job found.")
    sys.exit(1)

print(f"Generating PDF for Job ID: {latest_job.id}")
resp = get_report_pdf(latest_job.id, db)
pdf_content = resp.body

# Output locations
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
out_path = os.path.join(root_dir, "DECEPTRIX_Forensic_Audit_Report.pdf")
with open(out_path, "wb") as f:
    f.write(pdf_content)

artifact_path = r"C:\Users\pnara\.gemini\antigravity-ide\brain\5bcb579f-75c0-492b-b488-fc28408706a0\DECEPTRIX_Forensic_Audit_Report.pdf"
with open(artifact_path, "wb") as f:
    f.write(pdf_content)

print(f"Successfully generated and saved PDF to {out_path} ({len(pdf_content)} bytes)")
