import asyncio
import os
import uuid
import datetime
import subprocess
import json
import cv2
import glob
import shutil
from sqlalchemy.orm import Session
from transformers import pipeline
from PIL import Image

from models.orm import Job
from schemas.common import EvidenceEvent
from core.config import settings

_deepfake_detector = None
def get_deepfake_detector():
    global _deepfake_detector
    if _deepfake_detector is None:
        print("Loading FaceForensics++ Deepfake detector...")
        _deepfake_detector = pipeline('image-classification', model='HrutikAdsare/deepfake-detector-faceforensics')
    return _deepfake_detector

async def process_media_job(job_id: str, db: Session):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return
        
    job.progress = 10
    db.commit()

    file_path = job.file_path
    
    # 1. Metadata Extraction
    try:
        probe_cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", file_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(result.stdout)
        duration = float(probe_data.get('format', {}).get('duration', 0))
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        duration = 0
        
    job.progress = 20
    db.commit()

    # 2. Frame Extraction
    temp_dir = os.path.join(settings.STORAGE_DIR, f"temp_{job_id}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        ffmpeg_cmd = [
            "ffmpeg", "-i", file_path, "-vf", "fps=1", 
            f"{temp_dir}/frame_%04d.jpg", "-y"
        ]
        subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
    except Exception as e:
        print(f"Error extracting frames: {e}")
        
    job.progress = 40
    db.commit()

    # 3. Face Detection & Deepfake Inference
    detector = get_deepfake_detector()
    
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    frames = glob.glob(f"{temp_dir}/*.jpg")
    total_frames = len(frames)
    
    faces_processed = 0
    fake_scores = []
    
    # Run the processing in a thread to avoid blocking the async event loop
    def process_frames():
        nonlocal faces_processed
        for i, frame_path in enumerate(frames):
            img = cv2.imread(frame_path)
            if img is None:
                continue
                
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            for (x, y, w, h) in faces:
                margin_x = int(w * 0.1)
                margin_y = int(h * 0.1)
                x1 = max(0, x - margin_x)
                y1 = max(0, y - margin_y)
                x2 = min(img.shape[1], x + w + margin_x)
                y2 = min(img.shape[0], y + h + margin_y)
                
                face_img = img[y1:y2, x1:x2]
                face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(face_rgb)
                
                res = detector(pil_img)
                
                # Based on the model, extract fake score. If real is the only top label, use 1 - score.
                fake_score = 0.0
                for r in res:
                    label = r['label'].lower()
                    if 'fake' in label or 'manipulated' in label:
                        fake_score = max(fake_score, r['score'])
                    elif 'real' in label or 'original' in label:
                        # Sometimes only top label is returned
                        if len(res) == 1:
                            fake_score = 1.0 - r['score']
                
                if not any('fake' in r['label'].lower() or 'real' in r['label'].lower() for r in res):
                     # fallback assumption if label format is unexpected (e.g. LABEL_0, LABEL_1)
                     # HrutikAdsare model typically outputs fake/real. If it's LABEL_1 (fake), LABEL_0 (real)
                     for r in res:
                        if r['label'] == 'LABEL_1':
                            fake_score = max(fake_score, r['score'])
                        elif r['label'] == 'LABEL_0' and len(res) == 1:
                            fake_score = 1.0 - r['score']
                
                fake_scores.append(fake_score)
                faces_processed += 1
                
    # Run blocking operations in executor
    await asyncio.to_thread(process_frames)
            
    try:
        shutil.rmtree(temp_dir)
    except:
        pass
        
    job.progress = 90
    db.commit()
    
    # 4. Finalization
    avg_fake_score = sum(fake_scores) / len(fake_scores) if fake_scores else 0.0
    
    verdict = "Likely Real"
    if avg_fake_score > 0.6:
        verdict = "Likely Manipulated"
    elif avg_fake_score > 0.4:
        verdict = "Suspicious"
        
    severity = "low"
    if avg_fake_score > 0.6:
        severity = "high"
    elif avg_fake_score > 0.4:
        severity = "medium"

    explanation = f"Analyzed {faces_processed} faces across {total_frames} frames."
    if avg_fake_score > 0.6:
        explanation += " High probability of facial manipulation (e.g., FaceSwap, Face2Face) detected."
    elif avg_fake_score > 0.4:
        explanation += " Some suspicious facial artifacts detected."
    else:
        explanation += " No significant signs of facial manipulation detected."

    evidence = EvidenceEvent(
        event_id=str(uuid.uuid4()),
        case_id=job_id,
        modality="media",
        type="visual_manipulation",
        status="completed",
        score_or_null=avg_fake_score,
        severity=severity,
        confidence_quality="high" if faces_processed > 5 else "low",
        explanation=explanation,
        model_or_connector="FaceForensics++ Deepfake Detector",
        version="1.0",
        created_at=datetime.datetime.utcnow()
    )
    
    job.progress = 100
    job.status = "completed"
    job.verdict = verdict
    job.evidence = [evidence.model_dump()]
    job.completed_at = datetime.datetime.utcnow()
    db.commit()
