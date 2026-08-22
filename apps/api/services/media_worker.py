"""
Central media forensic orchestration.

Pipeline stages:
  1. FFprobe metadata telemetry
  2. FFmpeg demux: frames @ ANALYSIS_FPS + 16 kHz mono PCM audio
     (falls back to OpenCV frame walking if ffmpeg is unavailable)
  3. Per-frame: face detect -> landmarks -> MAR/jitter feeds -> aligned
     ViT ensemble inference (calibrated) -> DCT spectral features
  4. Audio-visual lag-searched lip-sync correlation
  5. Log-odds Bayesian fusion with full explainability payload

All evidence events are persisted progressively so the frontend can live-
stream the analysis as it runs.
"""
import os
import glob
import shutil
import datetime
import subprocess

import cv2
import numpy as np
import mediapipe as mp
from sqlalchemy.orm.attributes import flag_modified

from core.celery_app import celery_app
from core.database import SessionLocal
from models.orm import Job
from schemas.common import EvidenceEvent
from core.config import settings, ForensicConfig

from services.detectors import get_detector
from services.forensics.face_tracking import (
    FaceTracker,
    preprocess_face_for_model,
    extract_eye_centers,
    compute_mar,
    landmarks_to_array,
)
from services.forensics.temporal import TemporalForensicsEngine
from services.forensics.frequency import FrequencyForensicsEngine
from services.forensics.lip_sync import AudioVisualSyncEngine
from services.forensics.metadata import MetadataEvidence
from services.forensics.fusion import EvidenceFusionEngine
from services.calibration.calibrator import ModelCalibrator
from services.evidence.builder import EvidenceBuilder

ANALYSIS_FPS = ForensicConfig.ANALYSIS_FPS


def _extract_frames_ffmpeg(file_path: str, temp_dir: str, fps: int) -> bool:
    try:
        cmd = [
            "ffmpeg", "-i", file_path, "-vf", f"fps={fps}",
            os.path.join(temp_dir, "frame_%05d.jpg"), "-y",
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=300)
        return True
    except Exception as e:
        print(f"[worker] ffmpeg frame extraction failed: {e}")
        return False


def _extract_frames_cv2(file_path: str, temp_dir: str, fps: int, max_frames: int) -> bool:
    """Fallback frame walker using OpenCV when ffmpeg is unavailable."""
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return False
        src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        step = max(1, int(round(src_fps / max(fps, 0.1))))
        idx = saved = 0
        while True:
            ok, frame = cap.read()
            if not ok or saved >= max_frames:
                break
            if idx % step == 0:
                cv2.imwrite(os.path.join(temp_dir, f"frame_{saved + 1:05d}.jpg"), frame)
                saved += 1
            idx += 1
        cap.release()
        return saved > 0
    except Exception as e:
        print(f"[worker] cv2 frame extraction failed: {e}")
        return False


@celery_app.task(name="services.media_worker.process_media_job")
def process_media_job(job_id: str):
    db = SessionLocal()
    temp_dir = os.path.join(settings.STORAGE_DIR, f"temp_{job_id}")
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job or not job.file_path or not os.path.exists(job.file_path):
            return

        # ── Stage 1: Metadata ────────────────────────────────────────
        job.status = "processing"
        job.progress = 5
        job.current_step = "Extracting technical metadata (FFprobe)..."
        db.commit()

        metadata, meta_score, meta_reasons = MetadataEvidence.extract(job.file_path)

        meta_explanation = "Technical metadata inspection. "
        if meta_reasons and "unavailable" not in meta_reasons[0]:
            meta_explanation += "Findings: " + "; ".join(meta_reasons) + "."
        else:
            meta_explanation += "No metadata anomalies detected."

        meta_evidence = EvidenceBuilder.build(
            modality="metadata",
            event_type="metadata_inspection",
            status="completed",
            score=float(meta_score),
            confidence=0.9,
            model="FFprobe Metadata Inspector",
            version="2.0",
            timestamp=None,
            severity="low" if meta_score < 0.2 else ("medium" if meta_score < 0.35 else "high"),
            explanation=meta_explanation,
            limitations=(
                "Metadata can be stripped or spoofed; anomalies are supportive "
                "signals, not standalone proof of manipulation."
            ),
            case_id=job_id,
        )
        frame_events = [EvidenceEvent(**meta_evidence)]

        job.report_data = {"metadata": metadata}
        job.evidence = [e.model_dump(mode="json") for e in frame_events]
        flag_modified(job, "report_data")
        flag_modified(job, "evidence")

        job.progress = 12
        job.current_step = f"Demuxing video ({ANALYSIS_FPS} FPS) and isolating audio..."
        db.commit()

        # ── Stage 2: Demux ───────────────────────────────────────────
        os.makedirs(temp_dir, exist_ok=True)
        extraction_ok = _extract_frames_ffmpeg(job.file_path, temp_dir, ANALYSIS_FPS)
        if not extraction_ok:
            extraction_ok = _extract_frames_cv2(
                job.file_path, temp_dir, ANALYSIS_FPS, ForensicConfig.MAX_FRAMES
            )
        if not extraction_ok:
            raise RuntimeError("Could not decode video frames with ffmpeg or OpenCV.")

        audio_path = os.path.join(temp_dir, "audio.wav")
        has_audio = True
        try:
            subprocess.run(
                ["ffmpeg", "-i", job.file_path, "-vn", "-acodec", "pcm_s16le",
                 "-ar", "16000", "-ac", "1", audio_path, "-y"],
                capture_output=True, check=True, timeout=300,
            )
        except Exception:
            has_audio = False

        frames = sorted(glob.glob(os.path.join(temp_dir, "frame_*.jpg")))
        if not frames:
            raise RuntimeError("Zero frames extracted from source video.")
        if len(frames) > ForensicConfig.MAX_FRAMES:
            frames = frames[: ForensicConfig.MAX_FRAMES]

        faces_dir = os.path.join(settings.STORAGE_DIR, f"{job_id}_faces")
        os.makedirs(faces_dir, exist_ok=True)

        job.progress = 20
        job.current_step = "Loading forensic engines..."
        db.commit()

        detector = get_detector()
        face_tracker = FaceTracker()
        temporal_engine = TemporalForensicsEngine()
        audio_engine = AudioVisualSyncEngine(fps=ANALYSIS_FPS)
        calibrator = ModelCalibrator()
        freq_engine = FrequencyForensicsEngine()

        mp_face_mesh = mp.solutions.face_mesh

        all_deepfake_scores: list = []
        all_freq_scores: list = []
        all_disagreements: list = []
        all_confidences: list = []

        total_frames = len(frames)

        # ── Stage 3: Frame loop ──────────────────────────────────────
        with mp_face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.5,
        ) as face_mesh:

            for i, frame_path in enumerate(frames):
                img = cv2.imread(frame_path)
                if img is None:
                    continue
                (fh, fw) = img.shape[:2]

                bbox = face_tracker.get_face_bbox(img)
                if not bbox:
                    continue

                f_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(f_rgb)

                landmarks_px = None
                eye_dist = None
                if results.multi_face_landmarks:
                    lms = results.multi_face_landmarks[0].landmark
                    eyes = extract_eye_centers(lms, fw, fh)
                    if eyes is not None:
                        eye_dist = float(np.linalg.norm(eyes[0] - eyes[1]))

                    mar = compute_mar(lms)
                    audio_engine.add_mar(mar if mar is not None else 0.0)

                    if eye_dist and eye_dist > 1.0:
                        landmarks_px = landmarks_to_array(lms) * np.array([fw, fh], dtype=np.float32)
                        temporal_engine.add_landmarks(landmarks_px, eye_dist)

                # Aligned crop for visual classifier
                pil_face = preprocess_face_for_model(img, bbox, landmarks=results.multi_face_landmarks[0].landmark if results.multi_face_landmarks else None)
                if pil_face is None:
                    continue

                gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                blur_variance = float(cv2.Laplacian(gray_full, cv2.CV_64F).var())

                result = detector.predict(pil_face)
                calibrated = calibrator.calibrate(
                    result["fake_score"],
                    result["model_name"],
                    blur_variance=blur_variance,
                )
                fake_score = calibrated["calibrated_score"]

                all_deepfake_scores.append(fake_score)
                all_confidences.append(result.get("confidence", 0.8))
                if "model_disagreement" in result:
                    all_disagreements.append(result["model_disagreement"])

                # Spectral features on the padded raw crop
                (sx, sy, ex, ey) = bbox
                half_pad = int(max(ex - sx, ey - sy) * 0.15)
                psx, psy = max(0, sx - half_pad), max(0, sy - half_pad)
                pex, pey = min(fw, ex + half_pad), min(fh, ey + half_pad)
                face_crop_bgr = img[psy:pey, psx:pex]

                freq_features = {"freq_score": 0.0}
                if face_crop_bgr.size > 0:
                    face_gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
                    freq_features = freq_engine.compute_frequency_features(face_gray)
                    all_freq_scores.append(freq_features["freq_score"])

                    face_filename = f"seq_{i:04d}_face.jpg"
                    face_filepath = os.path.join(faces_dir, face_filename)
                    cv2.imwrite(face_filepath, face_crop_bgr)

                chunk_ts = round(i / ANALYSIS_FPS, 2)

                vis_evidence = EvidenceBuilder.build(
                    modality="visual",
                    event_type="aligned_ensemble_frame",
                    status="completed",
                    score=float(fake_score),
                    confidence=float(result.get("confidence", 0.8)),
                    model=result.get("model_name", "Ensemble"),
                    version="3.0",
                    timestamp=chunk_ts,
                    severity="high" if fake_score > 0.62 else ("medium" if fake_score > 0.45 else "low"),
                    explanation=(
                        f"Calibrated ViT={fake_score:.2f} (raw {result['fake_score']:.2f}, "
                        f"{calibrated['method']}), Freq={freq_features['freq_score']:.2f}, "
                        f"BlurVar={blur_variance:.0f}"
                    ),
                    limitations="Single-frame image-level assessment; temporal signals fused separately.",
                    case_id=job_id,
                )
                ev_obj = EvidenceEvent(**vis_evidence)
                ev_obj.artifact_refs = [{
                    "timestamp_sec": chunk_ts,
                    "faces": [{
                        "bbox": [int(sx), int(sy), int(ex), int(ey)],
                        "confidence": float(result.get("confidence", 0.8)),
                        "fake_score": float(fake_score),
                        "raw_fake_score": float(result["fake_score"]),
                        "jitter_score": float(temporal_engine.window_scores[-1]) if temporal_engine.window_scores else 0.0,
                        "freq_score": float(freq_features.get("freq_score", 0.0)),
                        "blur_variance": float(blur_variance),
                        "eye_distance": float(eye_dist) if eye_dist else None,
                        "face_crop": face_filepath if face_crop_bgr.size > 0 else "",
                    }],
                }]
                frame_events.append(ev_obj)

                # Progressive persistence every 8 frames for live UI
                if i % 8 == 0 or i == total_frames - 1:
                    job.evidence = [e.model_dump(mode="json") for e in frame_events]
                    flag_modified(job, "evidence")
                    job.progress = 25 + min(50, int((i / max(total_frames, 1)) * 50))
                    job.current_step = (
                        f"Analyzing keyframe {i + 1}/{total_frames} "
                        f"(t={chunk_ts:.1f}s) — {len(all_deepfake_scores)} faces"
                    )
                    db.commit()

        if not all_deepfake_scores:
            raise RuntimeError("No analyzable faces found in any sampled frame.")

        # ── Stage 4: Lip sync ────────────────────────────────────────
        job.current_step = "Computing lag-searched audio-visual synchrony..."
        job.progress = 78
        db.commit()

        lip_sync_res = audio_engine.analyze(audio_path) if has_audio else \
            audio_engine._insufficient_evidence("No audio stream present in container.")

        audio_evidence = EvidenceBuilder.build(
            modality="audio_visual",
            event_type="lip_sync_lag_search",
            status="completed" if lip_sync_res["status"] == "COMPLETED" else "not_applicable",
            score=float(lip_sync_res["lip_sync_score"]),
            confidence=0.85 if lip_sync_res["status"] == "COMPLETED" else 0.0,
            model="MediaPipe MAR × Librosa RMS (lag-searched Pearson)",
            version="2.0",
            timestamp=None,
            severity="high" if lip_sync_res["lip_sync_score"] > 0.6 else "low",
            explanation=lip_sync_res["message"],
            limitations="Silent segments, music beds or non-speech audio reduce reliability.",
            case_id=job_id,
        )
        frame_events.append(EvidenceEvent(**audio_evidence))

        # ── Stage 5: Fusion ──────────────────────────────────────────
        job.current_step = "Fusing multi-modal evidence (log-odds Bayesian)..."
        job.progress = 90
        db.commit()

        df_overall = float(np.percentile(all_deepfake_scores, 85))
        fr_overall = float(np.percentile(all_freq_scores, 75)) if all_freq_scores else 0.0
        tp_overall = temporal_engine.extract_temporal_score()
        disagreement_overall = float(np.mean(all_disagreements)) if all_disagreements else 0.0
        visual_conf_overall = float(np.mean(all_confidences)) if all_confidences else 0.8

        fusion_result = EvidenceFusionEngine.fuse(
            visual_score=df_overall,
            visual_model_disagreement=disagreement_overall,
            temporal_score=tp_overall,
            frequency_score=fr_overall,
            lip_sync_score=float(lip_sync_res["lip_sync_score"]),
            metadata_score=float(meta_score),
            visual_available=True,
            temporal_available=len(temporal_engine.landmark_sequence) >= 4,
            frequency_available=len(all_freq_scores) > 0,
            lip_sync_available=(lip_sync_res["status"] == "COMPLETED"),
            metadata_available=bool(metadata),
            visual_confidence=visual_conf_overall,
        )

        suspicious_segments = EvidenceFusionEngine.detect_suspicious_segments(
            [e.model_dump(mode="json") for e in frame_events if e.modality == "visual"],
            fps=ANALYSIS_FPS,
        )

        job.progress = 100
        job.status = "completed"
        job.current_step = "Analysis complete."
        job.verdict = fusion_result["classification"]
        job.evidence = [e.model_dump(mode="json") for e in frame_events]

        report_data_dict = {
            "metadata": metadata,
            "final_score": fusion_result["final_score"],
            "final_log_odds": fusion_result["final_log_odds"],
            "assessment_confidence": fusion_result["confidence"],
            "evidence_quality": fusion_result["evidence_quality"],
            "signal_consensus": fusion_result["signal_consensus"],
            "elevated_signals": fusion_result["elevated_signals"],
            "contributions": fusion_result["contributions"],
            "suspicious_segments": suspicious_segments,
            "frames_analyzed": total_frames,
            "faces_analyzed": len(all_deepfake_scores),
            "signal_scores": {
                "visual": df_overall,
                "temporal": tp_overall,
                "lip_sync": float(lip_sync_res["lip_sync_score"]),
                "frequency": fr_overall,
                "metadata": float(meta_score),
            },
            "signal_detail": {
                "visual_disagreement": disagreement_overall,
                "visual_confidence": visual_conf_overall,
                "lip_correlation": float(lip_sync_res.get("correlation", 0.0)),
                "lip_status": lip_sync_res["status"],
                "temporal_windows": len(temporal_engine.window_scores),
            },
        }
        job.report_data = report_data_dict
        flag_modified(job, "report_data")
        flag_modified(job, "evidence")

        job.completed_at = datetime.datetime.utcnow()
        db.commit()
        print(f"[worker] Job {job_id} complete => {fusion_result['classification']} "
              f"({fusion_result['final_score']:.3f})")

    except Exception as e:
        print(f"[worker] Media worker fatal error: {e}")
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
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        db.close()
