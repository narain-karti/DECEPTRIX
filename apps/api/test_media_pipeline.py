import asyncio
from core.database import SessionLocal, Base, engine
from models.orm import Job
from services.media_worker import process_media_job
import uuid
import os

async def test_media_pipeline():
    # Setup DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create a mock video file for testing
    video_path = "test_video.mp4"
    if not os.path.exists(video_path):
        import subprocess
        subprocess.run(["ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=3:size=1280x720:rate=1", video_path, "-y"])

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, modality='media', file_path=video_path, status='pending', progress=0)
    db.add(job)
    db.commit()

    print(f"Running media audit on job {job_id}...")
    process_media_job(job_id)

    db.refresh(job)
    print("Test Completed!")
    print(f"Verdict: {job.verdict}")
    print(f"Evidence Length: {len(job.evidence) if job.evidence else 0}")
    
    # Try fetching the PDF route logically
    from api.routes_reports import get_report_pdf
    try:
        res = get_report_pdf(job_id, db)
        print("PDF generated successfully.")
    except Exception as e:
        print(f"PDF generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_media_pipeline())
