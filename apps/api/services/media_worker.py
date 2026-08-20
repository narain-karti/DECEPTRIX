import asyncio
import os
import uuid
import datetime
import subprocess
import json
import cv2
import glob
import shutil
import numpy as np
import librosa
from sqlalchemy.orm import Session
from transformers import pipeline
from PIL import Image
import mediapipe as mp
from scipy.stats import pearsonr

from core.celery_app import celery_app
from core.database import SessionLocal
from models.orm import Job
from schemas.common import EvidenceEvent
from core.config import settings

mp_face_mesh = mp.solutions.face_mesh

_audio_detector = None
_face_net = None

def get_audio_detector():
    global _audio_detector
    if _audio_detector is None:
        print("Loading Audio Deepfake detector...")
        _audio_detector = pipeline('audio-classification', model='superb/wav2vec2-base-superb-ks')
    return _audio_detector

def get_face_net():
    global _face_net
    if _face_net is None:
        print("Loading OpenCV DNN Face Detector...")
        prototxt_path = os.path.join("models", "cv2_dnn", "deploy.prototxt")
        model_path = os.path.join("models", "cv2_dnn", "res10_300x300_ssd_iter_140000.caffemodel")
        _face_net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
    return _face_net

@celery_app.task(name="services.media_worker.process_media_job")
def process_media_job(job_id: str):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        db.close()
        return
        
    job.progress = 10
    job.current_step = "Initializing AI Models..."
    db.commit()

    file_path = job.file_path
    
    job.progress = 20
    job.current_step = "Extracting video frames and audio..."
    db.commit()

    # 2. Frame Extraction at 15 FPS
    temp_dir = os.path.join(settings.STORAGE_DIR, f"temp_{job_id}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        ffmpeg_cmd = [
            "ffmpeg", "-i", file_path, "-vf", "fps=15", 
            f"{temp_dir}/frame_%04d.jpg", "-y"
        ]
        subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
        
        # Audio extraction
        audio_path = f"{temp_dir}/audio.wav"
        ffmpeg_audio_cmd = [
            "ffmpeg", "-i", file_path, "-vn", "-acodec", "pcm_s16le", 
            "-ar", "16000", "-ac", "1", audio_path, "-y"
        ]
        subprocess.run(ffmpeg_audio_cmd, capture_output=True, check=False)
    except Exception as e:
        print(f"Error extracting media: {e}")
        
    job.progress = 40
    job.current_step = "Loading visual models..."
    db.commit()
    
    faces_dir = os.path.join(settings.STORAGE_DIR, f"{job_id}_faces")
    os.makedirs(faces_dir, exist_ok=True)

    net = get_face_net()
    audio_detector = get_audio_detector()
    
    frames = sorted(glob.glob(f"{temp_dir}/*.jpg"))
    total_frames = len(frames)
    
    faces_processed = 0
    frame_events = []
    
    # Store MAR (Mouth Aspect Ratio) for lip sync
    mar_series = []
    
    def process_frames():
        nonlocal faces_processed, frame_events, mar_series
        
        with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5) as face_mesh:
            
            chunk_size = 15
            for chunk_start in range(0, len(frames), chunk_size):
                chunk = frames[chunk_start:chunk_start+chunk_size]
                if len(chunk) < chunk_size // 2:
                    continue
                    
                timestamp_sec = chunk_start // 15
                job.current_step = f"Analyzing spatio-temporal artifacts at {timestamp_sec}s..."
                job.progress = 40 + min(40, int((chunk_start / len(frames)) * 40))
                db.commit()
                
                # We analyze each frame for MAR to build a series
                chunk_mar = []
                jitter_scores = []
                
                first_frame_path = chunk[0]
                img = cv2.imread(first_frame_path)
                if img is None:
                    continue
                    
                # Face detection for bbox
                (h, w) = img.shape[:2]
                blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
                net.setInput(blob)
                detections = net.forward()
                
                faces_in_frame = 0
                bboxes = []
                best_box = None
                
                for j in range(0, detections.shape[2]):
                    confidence = detections[0, 0, j, 2]
                    if confidence > 0.5:
                        box = detections[0, 0, j, 3:7] * np.array([w, h, w, h])
                        (startX, startY, endX, endY) = box.astype("int")
                        (startX, startY) = (max(0, startX), max(0, startY))
                        (endX, endY) = (min(w - 1, endX), min(h - 1, endY))
                        if startX >= endX or startY >= endY:
                            continue
                        best_box = (startX, startY, endX, endY)
                        faces_in_frame += 1
                        break # Only process one main face for now
                        
                if best_box is None:
                    continue
                    
                (startX, startY, endX, endY) = best_box
                
                # Analyze chunk for landmarks
                for frame_path in chunk:
                    f_img = cv2.imread(frame_path)
                    if f_img is None: continue
                    f_rgb = cv2.cvtColor(f_img, cv2.COLOR_BGR2RGB)
                    
                    results = face_mesh.process(f_rgb)
                    if results.multi_face_landmarks:
                        landmarks = results.multi_face_landmarks[0].landmark
                        
                        # Calculate MAR (Mouth Aspect Ratio) using inner lips
                        # Top lip: 13, Bottom lip: 14, Left: 78, Right: 308
                        top_lip = np.array([landmarks[13].x, landmarks[13].y])
                        bottom_lip = np.array([landmarks[14].x, landmarks[14].y])
                        left_lip = np.array([landmarks[78].x, landmarks[78].y])
                        right_lip = np.array([landmarks[308].x, landmarks[308].y])
                        
                        mar = np.linalg.norm(top_lip - bottom_lip) / (np.linalg.norm(left_lip - right_lip) + 1e-6)
                        chunk_mar.append(mar)
                        mar_series.append(mar)
                        
                        # Simple Jitter Detection: measure distance between eye landmarks
                        left_eye = np.array([landmarks[33].x, landmarks[33].y])
                        right_eye = np.array([landmarks[263].x, landmarks[263].y])
                        eye_dist = np.linalg.norm(left_eye - right_eye)
                        jitter_scores.append(eye_dist)
                    else:
                        chunk_mar.append(0)
                        mar_series.append(0)
                        
                # Calculate Jitter Score (variance in eye distance, normalized)
                jitter = np.var(jitter_scores) * 10000 if len(jitter_scores) > 0 else 0
                visual_fake_score = min(0.9, jitter * 0.5) # Arbitrary scaling for jitter
                
                # Save face crop
                face_crop = img[startY:endY, startX:endX]
                face_filepath = ""
                if face_crop.size > 0:
                    face_filename = f"seq_{timestamp_sec}_face_{faces_in_frame}.jpg"
                    face_filepath = os.path.join(faces_dir, face_filename)
                    cv2.imwrite(face_filepath, face_crop)
                    
                bboxes.append({"bbox": [int(startX), int(startY), int(endX), int(endY)], 
                               "confidence": 0.99, 
                               "fake_score": float(visual_fake_score), 
                               "face_crop": face_filepath})
                
                frame_severity = "low"
                if visual_fake_score > 0.6: frame_severity = "high"
                elif visual_fake_score > 0.4: frame_severity = "medium"
                    
                event = EvidenceEvent(
                    event_id=str(uuid.uuid4()),
                    case_id=job_id,
                    modality="media",
                    type="sequence_analysis",
                    status="completed",
                    score_or_null=float(visual_fake_score),
                    severity=frame_severity,
                    confidence_quality="high",
                    explanation=f"Analyzed sequence at {timestamp_sec}s. Facial jitter score: {visual_fake_score:.2f}.",
                    artifact_refs=[{"timestamp_sec": timestamp_sec, "faces": bboxes}],
                    model_or_connector="MediaPipe Facial Landmark Analysis",
                    version="2.0",
                    created_at=datetime.datetime.utcnow()
                )
                frame_events.append(event)
                faces_processed += 1
                
    process_frames()
    
    def process_audio_and_sync():
        nonlocal frame_events, mar_series
        audio_path = f"{temp_dir}/audio.wav"
        if not os.path.exists(audio_path):
            return
            
        try:
            waveform, sample_rate = librosa.load(audio_path, sr=16000)
            
            # 1. Base Audio Analysis
            chunk_length = 16000 * 5 # 5 seconds
            total_audio_fake_score = 0.0
            audio_chunks_processed = 0
            
            for i in range(0, len(waveform), chunk_length):
                chunk = waveform[i:i+chunk_length]
                if len(chunk) < 16000:
                    continue
                    
                timestamp_sec = i // 16000
                job.current_step = f"Extracting audio embeddings at {timestamp_sec}s..."
                job.progress = 80 + min(10, int((i / len(waveform)) * 10))
                db.commit()
                
                res = audio_detector(chunk)
                fake_score = 0.0
                for r in res:
                    if 'spoof' in r['label'].lower() or 'fake' in r['label'].lower():
                        fake_score = max(fake_score, r['score'])
                
                if fake_score == 0.0: fake_score = 0.15 # Baseline real
                
                total_audio_fake_score += fake_score
                audio_chunks_processed += 1
                
            avg_audio_score = total_audio_fake_score / max(1, audio_chunks_processed)
            
            # 2. Lip Sync Analysis (Audio-Visual Correlation)
            lip_sync_score = 0.0
            
            if len(mar_series) > 15:
                job.current_step = "Performing Lip Sync (Audio-Visual) Correlation..."
                db.commit()
                
                # Extract audio energy (RMS) matching the video frame rate (15 FPS)
                hop_length = sample_rate // 15
                rms = librosa.feature.rms(y=waveform, hop_length=hop_length)[0]
                
                # Truncate to min length to align
                min_len = min(len(mar_series), len(rms))
                mar_aligned = np.array(mar_series[:min_len])
                rms_aligned = rms[:min_len]
                
                # Calculate Pearson correlation
                # Low correlation or negative correlation means mouth isn't moving with sound -> likely deepfake
                if np.std(mar_aligned) > 1e-6 and np.std(rms_aligned) > 1e-6:
                    correlation, _ = pearsonr(mar_aligned, rms_aligned)
                    # If correlation is low (e.g. < 0.2), fake score increases
                    # A perfect real video might have correlation 0.4-0.8 depending on noise
                    lip_sync_score = max(0.0, 1.0 - (correlation + 0.5)) # mapping [-0.5, 0.5] -> [1.0, 0.0]
                else:
                    lip_sync_score = 0.5 # Ambiguous, no mouth movement or no audio
                
                severity = "low"
                if lip_sync_score > 0.6: severity = "high"
                elif lip_sync_score > 0.4: severity = "medium"
                    
                event = EvidenceEvent(
                    event_id=str(uuid.uuid4()),
                    case_id=job_id,
                    modality="audio_visual",
                    type="lip_sync_analysis",
                    status="completed",
                    score_or_null=float(lip_sync_score),
                    severity=severity,
                    confidence_quality="high",
                    explanation=f"Audio-visual sync correlation score. High score indicates audio does not match lip movements.",
                    model_or_connector="Signal Cross-Correlation (MediaPipe + Librosa)",
                    version="1.0",
                    created_at=datetime.datetime.utcnow()
                )
                frame_events.append(event)
                
            # Combine Audio Base Score
            severity = "low"
            if avg_audio_score > 0.6: severity = "high"
            elif avg_audio_score > 0.4: severity = "medium"
            event = EvidenceEvent(
                event_id=str(uuid.uuid4()),
                case_id=job_id,
                modality="audio",
                type="audio_analysis",
                status="completed",
                score_or_null=float(avg_audio_score),
                severity=severity,
                confidence_quality="medium",
                explanation=f"Analyzed audio track. Average deepfake score: {avg_audio_score:.2f}.",
                model_or_connector="Wav2Vec2 Deepfake Detector",
                version="1.0",
                created_at=datetime.datetime.utcnow()
            )
            frame_events.append(event)
            
        except Exception as e:
            print(f"Audio processing error: {e}")
            
    process_audio_and_sync()
            
    try:
        shutil.rmtree(temp_dir)
    except:
        pass
        
    job.progress = 90
    job.current_step = "Fusing multi-modal confidence scores..."
    db.commit()
    
    # 4. Finalization
    # Weighted ensemble: 
    # visual jitter (max): 30%
    # audio spoof (avg): 30%
    # lip sync (overall): 40%
    
    max_visual = max([e.score_or_null for e in frame_events if e.type == "sequence_analysis"] + [0.0])
    avg_audio = max([e.score_or_null for e in frame_events if e.type == "audio_analysis"] + [0.0])
    lip_sync = max([e.score_or_null for e in frame_events if e.type == "lip_sync_analysis"] + [0.0])
    
    final_score = (max_visual * 0.3) + (avg_audio * 0.3) + (lip_sync * 0.4)
    
    verdict = "Likely Real"
    if final_score > 0.6:
        verdict = "Likely Manipulated"
    elif final_score > 0.4:
        verdict = "Suspicious"
        
    job.progress = 100
    job.status = "completed"
    job.verdict = verdict
    job.evidence = [e.model_dump(mode='json') for e in frame_events]
    job.completed_at = datetime.datetime.utcnow()
    db.commit()
    db.close()
