"""
Celery task wrapper: persists pipeline results to Job rows and streams
progress to the polling frontend. All forensic logic lives in
services/pipeline.py.
"""
import os
import shutil
import datetime

from sqlalchemy.orm.attributes import flag_modified

from core.celery_app import celery_app
from core.database import SessionLocal
from models.orm import Job
from core.config import settings


@celery_app.task(name="services.media_worker.process_media_job")
def process_media_job(job_id: str):
    # Imported here so the pure pipeline module stays import-safe standalone
    from services.pipeline import run_forensic_pipeline

    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or not job.file_path or not os.path.exists(job.file_path):
            return

        job.status = "processing"
        job.progress = 3
        job.current_step = "Initializing forensic extractors..."
        db.commit()

        faces_dir = os.path.join(settings.STORAGE_DIR, f"{job_id}_faces")

        def on_progress(pct, step):
            """Persist progress/step so the polling UI stays live."""
            try:
                fresh = db.query(Job).filter(Job.id == job_id).first()
                if not fresh:
                    return
                fresh.progress = max(fresh.progress or 0, min(int(pct), 99))
                fresh.current_step = step
                db.commit()
            except Exception:
                pass

        result = run_forensic_pipeline(
            job_id,
            job.file_path,
            faces_dir=faces_dir,
            on_progress=on_progress,
        )

        if result["error"]:
            raise RuntimeError(result["error"])

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.progress = 100
        job.status = "completed"
        job.current_step = "Analysis complete."
        job.verdict = result["verdict"]
        job.evidence = result["evidence"]
        job.report_data = result["report_data"]
        flag_modified(job, "evidence")
        flag_modified(job, "report_data")
        job.completed_at = datetime.datetime.utcnow()
        db.commit()
        print(f"[worker] Job {job_id} completed => {job.verdict}")

    except Exception as e:
        print(f"[worker] Media worker fatal error: {e}")
        import traceback
        traceback.print_exc()
        try:
            failed = db.query(Job).filter(Job.id == job_id).first()
            if failed:
                failed.status = "failed"
                failed.current_step = f"Error: {str(e)[:200]}"
                db.commit()
        except Exception:
            pass
    finally:
        temp_dir = os.path.join(settings.STORAGE_DIR, f"temp_{job_id}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        db.close()
