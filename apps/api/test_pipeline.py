import uuid
from core.database import SessionLocal, Base, engine
from models.orm import Job
from services.text_worker import process_text_audit

def test_text_pipeline():
    # Setup DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create a test job
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, modality='text', text_content='The earth is flat. New RBI rules mandate digital rupee.', status='pending', progress=0)
    db.add(job)
    db.commit()

    print(f"Running text audit on job {job_id}...")
    process_text_audit(job_id)

    # Check result
    db.refresh(job)
    print("Test Completed!")
    print(f"Status: {job.status}")
    print(f"Verdict: {job.verdict}")
    print(f"Extracted Claims: {job.report_data.get('extracted_claims') if job.report_data else None}")
    print(f"Evidence: {job.evidence}")
    db.close()

if __name__ == "__main__":
    test_text_pipeline()
