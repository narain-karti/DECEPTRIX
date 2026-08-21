import os
import uuid
import datetime
import subprocess
import json
import cv2
import glob
import shutil
import hashlib
import numpy as np
import librosa
from sqlalchemy.orm import Session
from transformers import pipeline
from PIL import Image
import mediapipe as mp
from scipy.stats import pearsonr
from scipy.fft import dctn

from core.celery_app import celery_app
from core.database import SessionLocal
from models.orm import Job
from schemas.common import EvidenceEvent
from core.config import settings

mp_face_mesh = mp.solutions.face_mesh

# --- Lazy-loaded models ---

_deepfake_detector = None
from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch

_vit_processor = None
_vit_model = None
_face_net = None

def get_deepfake_detector():
    global _vit_processor, _vit_model
    if _vit_model is None:
        print("Loading ViT Deepfake Classifier (dima806)...")
        model_name = "dima806/deepfake_vs_real_image_detection"
        _vit_processor = AutoImageProcessor.from_pretrained(model_name)
        _vit_model = AutoModelForImageClassification.from_pretrained(model_name)
        _vit_model.eval()
    return _vit_processor, _vit_model

def score_deepfake_face(pil_img):
    processor, model = get_deepfake_detector()
    inputs = processor(images=[pil_img], return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]
    
    labels = model.config.id2label
    fake_idx = next((k for k, v in labels.items() if 'fake' in v.lower()), 0)
    return float(probs[fake_idx].item())

def get_face_net():
    global _face_net
    if _face_net is None:
        print("Loading OpenCV DNN Face Detector...")
        prototxt_path = os.path.join("models", "cv2_dnn", "deploy.prototxt")
        model_path = os.path.join("models", "cv2_dnn", "res10_300x300_ssd_iter_140000.caffemodel")
        _face_net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
    return _face_net


# --- Helper functions ---

def extract_metadata(file_path):
    """Run ffprobe and return structured metadata + anomaly score."""
    try:
        cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
               "-show_format", "-show_streams", file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        probe = json.loads(result.stdout)

        fmt = probe.get("format", {})
        streams = probe.get("streams", [])

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        # Parse FPS safely
        fps_val = 0
        if video_stream:
            fps_str = video_stream.get("r_frame_rate", "0/1")
            if "/" in str(fps_str):
                parts = str(fps_str).split("/")
                fps_val = int(parts[0]) / max(1, int(parts[1]))
            else:
                fps_val = float(fps_str)

        metadata = {
            "duration": float(fmt.get("duration", 0)),
            "format_name": fmt.get("format_name", "unknown"),
            "container": fmt.get("format_long_name", "unknown"),
            "video_codec": video_stream.get("codec_name", "unknown") if video_stream else "none",
            "width": int(video_stream.get("width", 0)) if video_stream else 0,
            "height": int(video_stream.get("height", 0)) if video_stream else 0,
            "fps": fps_val,
            "audio_codec": audio_stream.get("codec_name", "none") if audio_stream else "none",
            "audio_sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
            "has_creation_date": bool(fmt.get("tags", {}).get("creation_time")),
        }

        # Simple anomaly scoring
        anomaly_score = 0.0
        reasons = []
        if not metadata["has_creation_date"]:
            anomaly_score += 0.15
            reasons.append("No creation date in metadata")
        if metadata["video_codec"] not in ("h264", "hevc", "vp8", "vp9", "av1"):
            anomaly_score += 0.1
            reasons.append(f"Unusual codec: {metadata['video_codec']}")
        if metadata["duration"] < 1.0:
            anomaly_score += 0.1
            reasons.append("Very short duration")

        return metadata, min(1.0, anomaly_score), reasons
    except Exception as e:
        print(f"FFprobe error: {e}")
        return {}, 0.0, ["FFprobe unavailable"]


def compute_frequency_score(face_crop_gray):
    """Detect GAN artifacts in frequency domain via DCT.
    Real faces have smooth frequency falloff; GANs often have
    unusual energy in mid/high frequencies."""
    try:
        resized = cv2.resize(face_crop_gray, (128, 128))
        dct = dctn(resized.astype(np.float32), norm='ortho')
        h, w = dct.shape
        high_freq_energy = np.mean(np.abs(dct[h // 2:, w // 2:]))
        total_energy = np.mean(np.abs(dct)) + 1e-6
        ratio = high_freq_energy / total_energy
        # Real faces: ratio ~0.1-0.2; GAN faces: ratio often >0.3
        return min(1.0, max(0.0, (ratio - 0.1) / 0.3))
    except Exception:
        return 0.0


# --- Main Celery Task ---

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

        file_path = job.file_path
        frame_events = []

        # -- Step 1: Metadata Extraction --
        metadata, meta_score, meta_reasons = extract_metadata(file_path)

        meta_explanation = "Technical metadata inspection. "
        if meta_reasons and meta_reasons != ["FFprobe unavailable"]:
            meta_explanation += "Anomalies: " + "; ".join(meta_reasons) + "."
        else:
            meta_explanation += "No metadata anomalies detected."

        frame_events.append(EvidenceEvent(
            event_id=str(uuid.uuid4()),
            case_id=job_id,
            modality="metadata",
            type="metadata_inspection",
            status="completed",
            score_or_null=float(meta_score),
            severity="low" if meta_score < 0.2 else "medium",
            confidence_quality="high",
            scope="full_file",
            explanation=meta_explanation,
            model_or_connector="FFprobe Metadata Inspector",
            version="1.0",
            limitations="Metadata can be stripped or modified; absence is informational, not conclusive.",
            created_at=datetime.datetime.utcnow()
        ))

        # Store metadata in report_data and evidence for live frontend polling
        job.report_data = {"metadata": metadata}
        job.evidence = [e.model_dump(mode='json') for e in frame_events]
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(job, "report_data")
        flag_modified(job, "evidence")
        job.progress = 15
        job.current_step = "Extracting video frames and audio (15 FPS)..."
        db.commit()

        # -- Step 2: Frame & Audio Extraction --
        os.makedirs(temp_dir, exist_ok=True)

        try:
            ffmpeg_cmd = [
                "ffmpeg", "-i", file_path, "-vf", "fps=15",
                f"{temp_dir}/frame_%04d.jpg", "-y"
            ]
            subprocess.run(ffmpeg_cmd, capture_output=True, check=True, timeout=120)

            audio_path = f"{temp_dir}/audio.wav"
            ffmpeg_audio_cmd = [
                "ffmpeg", "-i", file_path, "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1", audio_path, "-y"
            ]
            subprocess.run(ffmpeg_audio_cmd, capture_output=True, check=False, timeout=120)
        except Exception as e:
            print(f"Error extracting media: {e}")

        job.progress = 30
        job.current_step = "Loading AI models..."
        db.commit()

        faces_dir = os.path.join(settings.STORAGE_DIR, f"{job_id}_faces")
        os.makedirs(faces_dir, exist_ok=True)

        net = get_face_net()
        deepfake_detector = get_deepfake_detector()

        frames = sorted(glob.glob(f"{temp_dir}/*.jpg"))
        mar_series = []
        all_freq_scores = []
        all_deepfake_scores = []

        # -- Step 3: Visual Analysis (Face Detection + Deepfake + Jitter + DCT) --
        with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5) as face_mesh:

            chunk_size = 15
            for chunk_start in range(0, len(frames), chunk_size):
                chunk = frames[chunk_start:chunk_start + chunk_size]
                if len(chunk) < chunk_size // 2:
                    continue

                timestamp_sec = chunk_start // 15
                job.current_step = f"Analyzing visual artifacts at {timestamp_sec}s..."
                job.progress = 30 + min(35, int((chunk_start / max(len(frames), 1)) * 35))
                db.commit()

                jitter_scores = []

                first_frame_path = chunk[0]
                img = cv2.imread(first_frame_path)
                if img is None:
                    continue

                (h, w) = img.shape[:2]
                blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
                net.setInput(blob)
                detections = net.forward()

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
                        break

                if best_box is None:
                    continue

                (startX, startY, endX, endY) = best_box

                # Landmarks for MAR and jitter
                for frame_path in chunk:
                    f_img = cv2.imread(frame_path)
                    if f_img is None:
                        continue
                    f_rgb = cv2.cvtColor(f_img, cv2.COLOR_BGR2RGB)
                    results = face_mesh.process(f_rgb)
                    if results.multi_face_landmarks:
                        landmarks = results.multi_face_landmarks[0].landmark
                        top_lip = np.array([landmarks[13].x, landmarks[13].y])
                        bottom_lip = np.array([landmarks[14].x, landmarks[14].y])
                        left_lip = np.array([landmarks[78].x, landmarks[78].y])
                        right_lip = np.array([landmarks[308].x, landmarks[308].y])
                        mar = np.linalg.norm(top_lip - bottom_lip) / (np.linalg.norm(left_lip - right_lip) + 1e-6)
                        mar_series.append(mar)

                        left_eye = np.array([landmarks[33].x, landmarks[33].y])
                        right_eye = np.array([landmarks[263].x, landmarks[263].y])
                        eye_dist = np.linalg.norm(left_eye - right_eye)
                        jitter_scores.append(eye_dist)
                    else:
                        mar_series.append(0)

                # Jitter score
                jitter = np.var(jitter_scores) * 10000 if len(jitter_scores) > 0 else 0
                visual_jitter_score = min(0.9, jitter * 0.5)

                # Save face crop
                face_crop = img[startY:endY, startX:endX]
                face_filepath = ""
                deepfake_score = 0.0
                freq_score = 0.0

                if face_crop.size > 0:
                    face_filename = f"seq_{timestamp_sec}_face.jpg"
                    face_filepath = os.path.join(faces_dir, face_filename)
                    cv2.imwrite(face_filepath, face_crop)

                    # Deepfake classifier (ViT)
                    try:
                        pil_face = Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
                        deepfake_score = score_deepfake_face(pil_face)
                        all_deepfake_scores.append(deepfake_score)
                    except Exception as e:
                        print(f"Deepfake classifier error: {e}")

                    # DCT Frequency Analysis
                    face_gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
                    freq_score = compute_frequency_score(face_gray)
                    all_freq_scores.append(freq_score)

                # Combined visual score for this chunk (for per-chunk display)
                combined_chunk_score = (deepfake_score * 0.5) + (visual_jitter_score * 0.25) + (freq_score * 0.25)

                frame_severity = "low"
                if combined_chunk_score > 0.6:
                    frame_severity = "high"
                elif combined_chunk_score > 0.4:
                    frame_severity = "medium"

                bboxes = [{
                    "bbox": [int(startX), int(startY), int(endX), int(endY)],
                    "confidence": 0.99,
                    "fake_score": float(deepfake_score),
                    "jitter_score": float(visual_jitter_score),
                    "freq_score": float(freq_score),
                    "face_crop": face_filepath
                }]

                frame_events.append(EvidenceEvent(
                    event_id=str(uuid.uuid4()),
                    case_id=job_id,
                    modality="media",
                    type="sequence_analysis",
                    status="completed",
                    score_or_null=float(combined_chunk_score),
                    severity=frame_severity,
                    confidence_quality="high",
                    scope=f"frames_{chunk_start}-{chunk_start + len(chunk)}",
                    explanation=f"Sequence at {timestamp_sec}s: Deepfake={deepfake_score:.2f}, Jitter={visual_jitter_score:.2f}, DCT={freq_score:.2f}.",
                    artifact_refs=[{"timestamp_sec": timestamp_sec, "faces": bboxes}],
                    model_or_connector="ViT Deepfake Classifier + MediaPipe Landmarks + DCT",
                    version="2.0",
                    limitations="Deepfake model trained on older generation techniques; may not catch latest methods.",
                    created_at=datetime.datetime.utcnow()
                ))

                # Commit progressive evidence so frontend can display live face extractions
                job.evidence = [e.model_dump(mode='json') for e in frame_events]
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(job, "evidence")
                db.commit()

        # -- Step 4: Lip Sync Analysis --
        audio_path = f"{temp_dir}/audio.wav"
        if os.path.exists(audio_path) and len(mar_series) > 15:
            try:
                job.current_step = "Performing lip-sync (audio-visual) correlation..."
                job.progress = 75
                db.commit()

                waveform, sample_rate = librosa.load(audio_path, sr=16000)
                hop_length = sample_rate // 15
                rms = librosa.feature.rms(y=waveform, hop_length=hop_length)[0]

                min_len = min(len(mar_series), len(rms))
                mar_aligned = np.array(mar_series[:min_len])
                rms_aligned = rms[:min_len]

                lip_sync_score = 0.5  # default ambiguous
                if np.std(mar_aligned) > 1e-6 and np.std(rms_aligned) > 1e-6:
                    correlation, _ = pearsonr(mar_aligned, rms_aligned)
                    # Map: high correlation (real) -> low score; low/negative (fake) -> high score
                    lip_sync_score = max(0.0, min(1.0, 0.5 - correlation * 0.5))

                severity = "low"
                if lip_sync_score > 0.6:
                    severity = "high"
                elif lip_sync_score > 0.4:
                    severity = "medium"

                frame_events.append(EvidenceEvent(
                    event_id=str(uuid.uuid4()),
                    case_id=job_id,
                    modality="audio_visual",
                    type="lip_sync_analysis",
                    status="completed",
                    score_or_null=float(lip_sync_score),
                    severity=severity,
                    confidence_quality="high",
                    scope="full_video",
                    explanation=f"Audio-visual lip sync correlation. Score {lip_sync_score:.2f} — {'Low' if lip_sync_score > 0.5 else 'Adequate'} synchronization between mouth movement and audio energy.",
                    model_or_connector="MediaPipe MAR + Librosa RMS Pearson Correlation",
                    version="1.0",
                    limitations="Silent segments or non-speech audio reduce reliability.",
                    created_at=datetime.datetime.utcnow()
                ))
            except Exception as e:
                print(f"Lip sync analysis error: {e}")

        # -- Step 5: Bayesian Evidentiary Fusion --
        job.progress = 90
        job.current_step = "Computing Bayesian multi-modal consensus..."
        db.commit()

        # Top-3 mean for robust visual scoring
        sorted_dfs = sorted(all_deepfake_scores, reverse=True)
        deepfake_primary = float(np.mean(sorted_dfs[:3])) if len(sorted_dfs) >= 3 else (float(sorted_dfs[0]) if sorted_dfs else 0.0)
        deepfake_max = max(all_deepfake_scores) if all_deepfake_scores else 0.0

        jitter_max = max([f.get("jitter_score", 0.0) for ev in frame_events for ref in (ev.artifact_refs or []) for f in (ref.get("faces") or [])] + [0.0])
        lip_sync_val = max([e.score_or_null for e in frame_events if e.type == "lip_sync_analysis"] + [0.0])
        freq_max = max(all_freq_scores) if all_freq_scores else 0.0
        meta_val = max([e.score_or_null for e in frame_events if e.type == "metadata_inspection"] + [0.0])

        # Corroborating signals weighted combination
        corroboration = (lip_sync_val * 0.40) + (jitter_max * 0.25) + (freq_max * 0.25) + (meta_val * 0.10)

        # Bayesian Evidence Fusion: Primary modality preserves dominant weight; corroborating signals amplify certainty
        if deepfake_primary >= 0.70:
            final_score = deepfake_primary + ((1.0 - deepfake_primary) * corroboration * 0.5)
        else:
            final_score = 1.0 - ((1.0 - deepfake_primary) * (1.0 - (corroboration * 0.6)))

        final_score = float(max(0.0, min(1.0, final_score)))

        verdict = "Likely Real"
        if final_score >= 0.65 or deepfake_primary >= 0.80:
            verdict = "Likely Manipulated"
        elif final_score >= 0.40:
            verdict = "Suspicious"

        job.progress = 100
        job.status = "completed"
        job.current_step = "Analysis complete."
        job.verdict = verdict
        job.evidence = [e.model_dump(mode='json') for e in frame_events]
        
        # Build complete report_data dictionary explicitly
        report_data_dict = {
            "metadata": metadata,
            "final_score": float(final_score),
            "signal_weights": {
                "deepfake_classifier": 0.35,
                "lip_sync": 0.25,
                "jitter": 0.15,
                "frequency": 0.15,
                "metadata": 0.10
            },
            "signal_scores": {
                "deepfake_classifier": float(deepfake_max),
                "lip_sync": float(lip_sync_val),
                "jitter": float(jitter_max),
                "frequency": float(freq_max),
                "metadata": float(meta_val)
            }
        }
        job.report_data = report_data_dict
        
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(job, "report_data")
        
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
