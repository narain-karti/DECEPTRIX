import os
import uuid
import datetime
import subprocess
import glob
import shutil
import cv2
import numpy as np
import mediapipe as mp
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from core.celery_app import celery_app
from core.database import SessionLocal
from models.orm import Job
from schemas.common import EvidenceEvent
from core.config import settings

from services.detectors import get_detector
from services.forensics.face_tracking import FaceTracker, preprocess_face_for_model
from services.forensics.temporal import TemporalForensicsEngine, analyze_segment_consistency
from services.forensics.frequency import FrequencyForensicsEngine
from services.forensics.lip_sync import AudioVisualSyncEngine
from services.forensics.metadata import MetadataEvidence
from services.forensics.fusion import EvidenceFusionEngine
from services.calibration.calibrator import ModelCalibrator
from services.evidence.builder import EvidenceBuilder

mp_face_mesh = mp.solutions.face_mesh
ANALYSIS_FPS = int(os.environ.get("ANALYSIS_FPS", "8"))

@celery_app.task(name="services.media_worker.process_media_job")
def process_media_job(job_id: str):
    db = SessionLocal()
    temp_dir = os.path.join(settings.STORAGE_DIR, f"temp_{job_id}")
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        job.progress = 5
        job.current_step = "Extracting technical metadata (FFprobe)..."
        db.commit()

        frame_events = []

        # -- Step 1: Metadata Extraction --
        metadata, meta_score, meta_reasons = MetadataEvidence.extract(job.file_path)

        meta_explanation = "Technical metadata inspection. "
        if meta_reasons and not "unavailable" in meta_reasons[0]:
            meta_explanation += "Anomalies: " + "; ".join(meta_reasons) + "."
        else:
            meta_explanation += "No metadata anomalies detected."

        meta_evidence = EvidenceBuilder.build(
            modality="metadata",
            event_type="metadata_inspection",
            status="completed",
            score=float(meta_score),
            confidence=0.9,
            model="FFprobe Metadata Inspector",
            version="1.0",
            timestamp=None,
            severity="low" if meta_score < 0.2 else "medium",
            explanation=meta_explanation,
            limitations="Metadata can be stripped or modified; absence is informational, not conclusive.",
            case_id=job_id
        )
        frame_events.append(EvidenceEvent(**meta_evidence))

        job.report_data = {"metadata": metadata}
        job.evidence = [e.model_dump(mode='json') for e in frame_events]
        flag_modified(job, "report_data")
        flag_modified(job, "evidence")
        
        job.progress = 15
        job.current_step = f"Extracting video frames and audio ({ANALYSIS_FPS} FPS)..."
        db.commit()

        # -- Step 2: Frame & Audio Extraction --
        os.makedirs(temp_dir, exist_ok=True)
        try:
            ffmpeg_cmd = [
                "ffmpeg", "-i", job.file_path, "-vf", f"fps={ANALYSIS_FPS}",
                f"{temp_dir}/frame_%04d.jpg", "-y"
            ]
            subprocess.run(ffmpeg_cmd, capture_output=True, check=True, timeout=120)

            audio_path = f"{temp_dir}/audio.wav"
            ffmpeg_audio_cmd = [
                "ffmpeg", "-i", job.file_path, "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1", audio_path, "-y"
            ]
            subprocess.run(ffmpeg_audio_cmd, capture_output=True, check=False, timeout=120)
        except Exception as e:
            print(f"Error extracting media: {e}")

        job.progress = 30
        job.current_step = "Initializing Forensics Engines..."
        db.commit()

        faces_dir = os.path.join(settings.STORAGE_DIR, f"{job_id}_faces")
        os.makedirs(faces_dir, exist_ok=True)

        detector = get_detector()
        face_tracker = FaceTracker()
        temporal_engine = TemporalForensicsEngine()
        audio_engine = AudioVisualSyncEngine(fps=ANALYSIS_FPS)
        calibrator = ModelCalibrator()

        frames = sorted(glob.glob(f"{temp_dir}/*.jpg"))
        all_deepfake_scores = []
        all_freq_scores = []

        # -- Step 3: Sequence Analysis (Visual + Temporal + Frequency) --
        with mp_face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.5) as face_mesh:

            chunk_size = ANALYSIS_FPS
            for chunk_start in range(0, len(frames), chunk_size):
                chunk = frames[chunk_start:chunk_start + chunk_size]
                if len(chunk) < chunk_size // 2:
                    continue

                timestamp_sec = chunk_start / ANALYSIS_FPS
                job.current_step = f"Analyzing sequences at {timestamp_sec:.1f}s..."
                job.progress = 30 + min(40, int((chunk_start / max(len(frames), 1)) * 40))
                db.commit()

                chunk_deepfake_scores = []
                chunk_freq_scores = []
                bboxes_evidence = []
                model_disagreement = 0.0

                for frame_path in chunk:
                    img = cv2.imread(frame_path)
                    if img is None: continue
                    
                    bbox = face_tracker.get_face_bbox(img)
                    if not bbox: continue

                    # Landmarks for temporal and audio engines
                    f_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(f_rgb)
                    if results.multi_face_landmarks:
                        landmarks = results.multi_face_landmarks[0].landmark
                        
                        top_lip = np.array([landmarks[13].x, landmarks[13].y])
                        bottom_lip = np.array([landmarks[14].x, landmarks[14].y])
                        left_lip = np.array([landmarks[78].x, landmarks[78].y])
                        right_lip = np.array([landmarks[308].x, landmarks[308].y])
                        mar = np.linalg.norm(top_lip - bottom_lip) / (np.linalg.norm(left_lip - right_lip) + 1e-6)
                        audio_engine.add_mar(mar)

                        left_eye = np.array([landmarks[33].x, landmarks[33].y])
                        right_eye = np.array([landmarks[263].x, landmarks[263].y])
                        eye_dist = np.linalg.norm(left_eye - right_eye)
                        temporal_engine.add_jitter(eye_dist)
                    else:
                        audio_engine.add_mar(0)

                    # Crop and Predict
                    pil_face = preprocess_face_for_model(img, bbox)
                    if pil_face:
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        blur_variance = cv2.Laplacian(gray, cv2.CV_64F).var()

                        result = detector.predict(pil_face)
                        calibrated = calibrator.calibrate(
                            result["fake_score"], 
                            result["model_name"],
                            blur_variance=blur_variance
                        )
                        fake_score = calibrated["calibrated_score"]
                        model_disagreement = result.get("model_disagreement", 0.0)
                        
                        chunk_deepfake_scores.append(fake_score)
                        all_deepfake_scores.append(fake_score)

                        # Frequency
                        (startX, startY, endX, endY) = bbox
                        face_crop = img[startY:endY, startX:endX]
                        if face_crop.size > 0:
                            face_gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
                            freq_features = FrequencyForensicsEngine.compute_frequency_features(face_gray)
                            chunk_freq_scores.append(freq_features["freq_score"])
                            all_freq_scores.append(freq_features["freq_score"])

                            face_filename = f"seq_{timestamp_sec:.1f}_face.jpg"
                            face_filepath = os.path.join(faces_dir, face_filename)
                            cv2.imwrite(face_filepath, face_crop)

                            bboxes_evidence.append({
                                "bbox": [int(startX), int(startY), int(endX), int(endY)],
                                "confidence": result["confidence"],
                                "fake_score": float(fake_score),
                                "freq_score": float(freq_features["freq_score"]),
                                "face_crop": face_filepath
                            })

                if not chunk_deepfake_scores:
                    continue

                chunk_df_score = float(np.mean(chunk_deepfake_scores))
                chunk_fr_score = float(np.mean(chunk_freq_scores))
                chunk_tmp_score = temporal_engine.extract_temporal_score()
                
                combined = (chunk_df_score * 0.6) + (chunk_tmp_score * 0.2) + (chunk_fr_score * 0.2)
                
                # Visual Evidence Event
                vis_evidence = EvidenceBuilder.build(
                    modality="visual",
                    event_type="ensemble_classifier",
                    status="completed",
                    score=float(combined),
                    confidence=1.0 - model_disagreement,
                    model=detector.__class__.__name__,
                    version="2.0",
                    timestamp=timestamp_sec,
                    severity="high" if combined > 0.6 else ("medium" if combined > 0.4 else "low"),
                    explanation=f"Visual={chunk_df_score:.2f}, Temp={chunk_tmp_score:.2f}, Freq={chunk_fr_score:.2f}",
                    limitations="Image-level detector; temporal consistency is evaluated separately.",
                    case_id=job_id
                )
                
                ev_obj = EvidenceEvent(**vis_evidence)
                ev_obj.artifact_refs = [{"timestamp_sec": timestamp_sec, "faces": bboxes_evidence}]
                frame_events.append(ev_obj)

                job.evidence = [e.model_dump(mode='json') for e in frame_events]
                flag_modified(job, "evidence")
                db.commit()

        # -- Step 4: Audio-Visual Sync --
        job.current_step = "Computing audio-visual sync..."
        job.progress = 80
        db.commit()
        
        lip_sync_res = audio_engine.analyze(f"{temp_dir}/audio.wav")
        audio_evidence = EvidenceBuilder.build(
            modality="audio_visual",
            event_type="lip_sync",
            status="completed" if lip_sync_res["status"] == "COMPLETED" else "not_applicable",
            score=lip_sync_res["lip_sync_score"],
            confidence=1.0 if lip_sync_res["status"] == "COMPLETED" else 0.0,
            model="MediaPipe MAR + Librosa RMS Correlation",
            version="1.0",
            timestamp=None,
            severity="high" if lip_sync_res["lip_sync_score"] > 0.6 else "low",
            explanation=lip_sync_res["message"],
            limitations="Silent segments or non-speech audio reduce reliability.",
            case_id=job_id
        )
        frame_events.append(EvidenceEvent(**audio_evidence))

        # -- Step 5: Evidence Fusion --
        job.current_step = "Fusing multi-modal evidence..."
        job.progress = 90
        db.commit()

        df_overall = float(np.percentile(all_deepfake_scores, 85)) if all_deepfake_scores else 0.0
        fr_overall = float(np.mean(all_freq_scores)) if all_freq_scores else 0.0
        tp_overall = temporal_engine.extract_temporal_score()
        
        # Calculate overall model disagreement
        disagreement_overall = 0.0 # Could track from frames, fallback to default

        fusion_result = EvidenceFusionEngine.fuse(
            visual_score=df_overall,
            visual_model_disagreement=disagreement_overall,
            temporal_score=tp_overall,
            frequency_score=fr_overall,
            lip_sync_score=lip_sync_res["lip_sync_score"],
            metadata_score=meta_score
        )
        
        suspicious_segments = EvidenceFusionEngine.detect_suspicious_segments([e.model_dump(mode='json') for e in frame_events if e.modality == "visual"], fps=ANALYSIS_FPS)

        job.progress = 100
        job.status = "completed"
        job.current_step = "Analysis complete."
        job.verdict = fusion_result["classification"]
        job.evidence = [e.model_dump(mode='json') for e in frame_events]
        
        report_data_dict = {
            "metadata": metadata,
            "final_score": fusion_result["final_score"],
            "assessment_confidence": fusion_result["confidence"],
            "evidence_quality": fusion_result["evidence_quality"],
            "signal_consensus": fusion_result["signal_consensus"],
            "suspicious_segments": suspicious_segments,
            "signal_scores": {
                "visual": df_overall,
                "temporal": tp_overall,
                "lip_sync": lip_sync_res["lip_sync_score"],
                "frequency": fr_overall,
                "metadata": meta_score
            }
        }
        job.report_data = report_data_dict
        flag_modified(job, "report_data")
        flag_modified(job, "evidence")
        
        job.completed_at = datetime.datetime.utcnow()
        db.commit()

    except Exception as e:
        print(f"Media worker fatal error: {e}")
        import traceback
        traceback.print_exc()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.current_step = f"Error: {str(e)[:200]}"
                db.commit()
        except Exception:
            pass
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
        db.close()
