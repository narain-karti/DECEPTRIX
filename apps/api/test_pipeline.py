import asyncio
from core.database import SessionLocal, Base, engine
from models.orm import Job
from services.text_worker import process_text_audit
import uuid

async def test_text_pipeline():
    # Setup DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create a test job
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, modality='text', text_content='The earth is flat.', status='pending', progress=0)
    db.add(job)
    db.commit()

    print(f"Running text audit on job {job_id}...")
    await process_text_audit(job_id, db)

    # Check result
    db.refresh(job)
    print("Test Completed!")
    print(f"Verdict: {job.verdict}")
    print(f"Evidence: {job.evidence}")

if __name__ == "__main__":
    asyncio.run(test_text_pipeline())
