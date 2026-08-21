import uuid
import os
import subprocess
from core.database import SessionLocal, Base, engine
from models.orm import Job
from services.media_worker import process_media_job
from api.routes_reports import get_report_pdf, get_report_json

def test_media_pipeline():
    # Setup DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create a mock video file for testing
    video_path = "test_video.mp4"
    if not os.path.exists(video_path):
        subprocess.run(["ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=3:size=1280x720:rate=15", "-f", "lavfi", "-i", "sine=frequency=1000:duration=3", "-pix_fmt", "yuv420p", video_path, "-y"])

    job_id = str(uuid.uuid4())
    job = Job(id=job_id, modality='media', file_path=video_path, filename="test_video.mp4", sha256="mock_sha256_hash_1234567890", status='pending', progress=0)
    db.add(job)
    db.commit()

    print(f"Running media audit on job {job_id}...")
    process_media_job(job_id)

    db.refresh(job)
    print("Test Completed!")
    print(f"Status: {job.status}")
    print(f"Verdict: {job.verdict}")
    print(f"Evidence Events: {len(job.evidence) if job.evidence else 0}")
    print(f"Signal Scores: {job.report_data.get('signal_scores') if job.report_data else None}")
    
    # Verify PDF generation
    try:
        pdf_res = get_report_pdf(job_id, db)
        print(f"PDF generated successfully (bytes: {len(pdf_res.body)}).")
        with open("test_output_report.pdf", "wb") as f:
            f.write(pdf_res.body)
        print("Saved test_output_report.pdf successfully.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"PDF generation failed: {e}")

    # Verify JSON generation
    try:
        json_res = get_report_json(job_id, db)
        print("JSON report generated successfully.")
    except Exception as e:
        print(f"JSON generation failed: {e}")

    db.close()

if __name__ == "__main__":
    test_media_pipeline()
