"""
Central media forensic orchestration — v4.0 (7-signal, multi-face).

Pipeline stages:
  1. FFprobe metadata telemetry
  2. FFmpeg demux: frames @ ANALYSIS_FPS + 16 kHz mono PCM audio
     (falls back to OpenCV frame walking if ffmpeg is unavailable)
  3. Per-frame multi-face tracking (up to 3 faces):
       - MediaPipe FaceMesh landmarks -> MAR + normalized mesh jitter feeds
       - Eye-aligned ViT ensemble inference (calibrated)   [primary face
         every frame; secondary faces every other frame for CPU budget]
       - Seam-blending boundary analysis per face
       - DCT spectral features per face
  4. Lag-searched audio-visual lip-sync correlation
  5. Classical audio-spoof forensics (vocoder/clone artifacts)
  6. Log-odds Bayesian fusion of up to 7 signals with explainability

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
    MultiFaceTracker,
    preprocess_face_for_model,
    extract_eye_centers,
    compute_mar,
    landmarks_to_array,
)
from services.forensics.temporal import TemporalForensicsEngine
from services.forensics.frequency import FrequencyForensicsEngine
from services.forensics.lip_sync import AudioVisualSyncEngine
from services.forensics.audio_spoof import AudioSpoofEngine
from services.forensics.blending import BlendingAnalyzer
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

        job.progress = 10
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

        job.progress = 18
        job.current_step = "Loading forensic engines..."
        db.commit()

        detector = get_detector()
        face_tracker = MultiFaceTracker(max_faces=3)
        audio_engine = AudioVisualSyncEngine(fps=ANALYSIS_FPS)
        spoof_engine = AudioSpoofEngine()
        calibrator = ModelCalibrator()
        freq_engine = FrequencyForensicsEngine()

        # Per-track state
        track_engines: dict = {}      # tid -> TemporalForensicsEngine
        track_scores: dict = {}       # tid -> list of calibrated fake scores
        track_blends: dict = {}       # tid -> list of blending scores
        all_freq_scores: list = []
        all_disagreements: list = []
        all_confidences: list = []

        def _engine_for(tid: int) -> TemporalForensicsEngine:
            if tid not in track_engines:
                track_engines[tid] = TemporalForensicsEngine()
                track_scores[tid] = []
                track_blends[tid] = []
            return track_engines[tid]

        total_frames = len(frames)
        mp_face_mesh = mp.solutions.face_mesh

        # ── Stage 3: Frame loop (multi-face) ─────────────────────────
        with mp_face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=3,
            refine_landmarks=True, min_detection_confidence=0.5,
        ) as face_mesh:

            for i, frame_path in enumerate(frames):
                img = cv2.imread(frame_path)
                if img is None:
                    continue
                (fh, fw) = img.shape[:2]

                tracks = face_tracker.update(img)

                f_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                mesh_results = face_mesh.process(f_rgb) if tracks else None

                # Associate each FaceMesh landmark set to nearest track centre
                lm_sets = []
                if mesh_results and mesh_results.multi_face_landmarks:
                    for lms in mesh_results.multi_face_landmarks:
                        arr = np.array([[p.x * fw, p.y * fh] for p in lms.landmark], dtype=np.float32)
                        lm_sets.append({"center": arr.mean(axis=0), "landmarks": lms, "px": arr})

                frame_faces_payload = []
                for rank, tr in enumerate(tracks):
                    tid = tr["track_id"]
                    bbox = tuple(int(v) for v in tr["bbox"])
                    sx, sy, ex, ey = bbox
                    is_primary = rank == 0

                    t_engine = _engine_for(tid)
                    box_center = np.array([(sx + ex) / 2.0, (sy + ey) / 2.0], dtype=np.float32)

                    # Nearest landmark set to this track
                    landmarks = None
                    landmarks_px = None
                    best_d = 1e12
                    for ls in lm_sets:
                        d = float(np.linalg.norm(ls["center"] - box_center))
                        if d < best_d:
                            best_d = d
                            landmarks = ls["landmarks"]
                            landmarks_px = ls["px"]
                    if best_d > max(ex - sx, ey - sy):   # too far => unrelated
                        landmarks = None
                        landmarks_px = None

                    # Feeds
                    eye_dist = None
                    if landmarks is not None and landmarks_px is not None:
                        eyes = extract_eye_centers(landmarks, fw, fh)
                        if eyes is not None:
                            eye_dist = float(np.linalg.norm(eyes[0] - eyes[1]))
                        if is_primary:
                            mar = compute_mar(landmarks)
                            audio_engine.add_mar(mar if mar is not None else 0.0)
                        if eye_dist and eye_dist > 1.0:
                            t_engine.add_landmarks(landmarks_px, eye_dist)

                    # Seam-blending analysis (cheap; every frame, every face)
                    blend_res = BlendingAnalyzer.analyze(img, bbox)
                    if blend_res.get("status") == "COMPLETED":
                        track_blends[tid].append(float(blend_res["blending_score"]))

                    # Spectral features on padded raw crop
                    half_pad = int(max(ex - sx, ey - sy) * 0.15)
                    psx, psy = max(0, sx - half_pad), max(0, sy - half_pad)
                    pex, pey = min(fw, ex + half_pad), min(fh, ey + half_pad)
                    face_crop_bgr = img[psy:pey, psx:pex]

                    freq_features = {"freq_score": 0.0}
                    face_filepath = ""
                    if face_crop_bgr.size > 0:
                        face_gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
                        freq_features = freq_engine.compute_frequency_features(face_gray)
                        all_freq_scores.append(freq_features["freq_score"])
                        face_filename = f"seq_{i:04d}_t{tid}.jpg"
                        face_filepath = os.path.join(faces_dir, face_filename)
                        cv2.imwrite(face_filepath, face_crop_bgr)

                    # ViT ensemble — primary every frame, secondary every 2nd (CPU budget)
                    fake_score = None
                    raw_score = None
                    confidence = 0.8
                    disagreement = 0.0
                    blur_variance = None

                    run_vit = is_primary or (i % 2 == 0)
                    pil_face = (
                        preprocess_face_for_model(
                            img, bbox,
                            landmarks=landmarks if landmarks is not None else None,
                        )
                        if run_vit else None
                    )

                    if run_vit and pil_face is not None:
                        gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        blur_variance = float(cv2.Laplacian(gray_full, cv2.CV_64F).var())

                        result = detector.predict(pil_face)
                        calibrated = calibrator.calibrate(
                            result["fake_score"],
                            result["model_name"],
                            blur_variance=blur_variance,
                        )
                        fake_score = calibrated["calibrated_score"]
                        raw_score = float(result["fake_score"])
                        confidence = float(result.get("confidence", 0.8))
                        disagreement = float(result.get("model_disagreement", 0.0))

                        track_scores[tid].append(fake_score)
                        all_confidences.append(confidence)
                        all_disagreements.append(disagreement)

                    entry = {
                        "track_id": tid,
                        "is_primary": is_primary,
                        "bbox": [sx, sy, ex, ey],
                        "confidence": confidence,
                        "fake_score": float(fake_score) if fake_score is not None else None,
                        "raw_fake_score": raw_score,
                        "jitter_score": float(t_engine.window_scores[-1]) if t_engine.window_scores else 0.0,
                        "freq_score": float(freq_features.get("freq_score", 0.0)),
                        "blending_score": float(blend_res.get("blending_score", 0.0))
                                          if blend_res.get("status") == "COMPLETED" else None,
                        "blur_variance": float(blur_variance) if blur_variance is not None else None,
                        "eye_distance": float(eye_dist) if eye_dist else None,
                        "face_crop": face_filepath,
                    }
                    frame_faces_payload.append(entry)

                if not frame_faces_payload:
                    continue

                chunk_ts = round(i / ANALYSIS_FPS, 2)

                scored = [f for f in frame_faces_payload if f["fake_score"] is not None]
                frame_vis_score = (
                    max(f["fake_score"] for f in scored) if scored else 0.0
                )

                vis_evidence = EvidenceBuilder.build(
                    modality="visual",
                    event_type="multiface_frame",
                    status="completed" if scored else "not_applicable",
                    score=float(frame_vis_score),
                    confidence=float(np.mean(all_confidences)) if all_confidences else 0.8,
                    model=detector.__class__.__name__,
                    version="4.0",
                    timestamp=chunk_ts,
                    severity="high" if frame_vis_score > 0.62 else ("medium" if frame_vis_score > 0.45 else "low"),
                    explanation=(
                        f"{len(frame_faces_payload)} face(s) tracked; "
                        f"max calibrated ViT={frame_vis_score:.2f}, "
                        f"blend={max((f['blending_score'] or 0) for f in frame_faces_payload):.2f}"
                    ),
                    limitations="Frame-level assessment; temporal/spectral/audio signals fused separately.",
                    case_id=job_id,
                )
                ev_obj = EvidenceEvent(**vis_evidence)
                ev_obj.artifact_refs = [{"timestamp_sec": chunk_ts, "faces": frame_faces_payload}]
                frame_events.append(ev_obj)

                # Progressive persistence every 8 frames for live UI
                if i % 8 == 0 or i == total_frames - 1:
                    job.evidence = [e.model_dump(mode="json") for e in frame_events]
                    flag_modified(job, "evidence")
                    n_faces_seen = len(track_engines)
                    job.progress = 22 + min(48, int((i / max(total_frames, 1)) * 48))
                    job.current_step = (
                        f"Keyframe {i + 1}/{total_frames} (t={chunk_ts:.1f}s) — "
                        f"{n_faces_seen} face(s) under analysis"
                    )
                    db.commit()

        any_visual_scores = [s for lst in track_scores.values() for s in lst]
        if not any_visual_scores:
            raise RuntimeError("No analyzable faces found in any sampled frame.")

        # ── Stage 4: Audio-visual sync + audio spoof ─────────────────
        job.current_step = "Computing lag-searched lip-sync + audio-forensics scan..."
        job.progress = 74
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

        spoof_res = spoof_engine.analyze(audio_path) if has_audio else \
            spoof_engine._insufficient("No audio stream present in container.")

        spoof_evidence = EvidenceBuilder.build(
            modality="audio_spoof",
            event_type="vocoder_artifact_scan",
            status="completed" if spoof_res["status"] == "COMPLETED" else "not_applicable",
            score=float(spoof_res["audio_spoof_score"]),
            confidence=0.75 if spoof_res["status"] == "COMPLETED" else 0.0,
            model="Classical cepstral/pitch-statistics spoof detector",
            version="1.0",
            timestamp=None,
            severity="high" if spoof_res["audio_spoof_score"] > 0.6 else "low",
            explanation=spoof_res["message"],
            limitations=(
                "Heuristic operating points pending benchmark calibration; heavy "
                "background noise or music reduces reliability."
            ),
            case_id=job_id,
        )
        frame_events.append(EvidenceEvent(**spoof_evidence))

        # ── Stage 5: Fusion ──────────────────────────────────────────
        job.current_step = "Fusing 7-signal evidence (log-odds Bayesian)..."
        job.progress = 90
        db.commit()

        df_overall = float(np.percentile(any_visual_scores, 85))
        fr_overall = float(np.percentile(all_freq_scores, 75)) if all_freq_scores else 0.0
        tp_overall = max(
            (eng.extract_temporal_score() for eng in track_engines.values()), default=0.0
        )
        blend_overall = (
            float(np.percentile([b for lst in track_blends.values() for b in lst], 85))
            if any(track_blends.values()) else 0.0
        )
        disagreement_overall = float(np.mean(all_disagreements)) if all_disagreements else 0.0
        visual_conf_overall = float(np.mean(all_confidences)) if all_confidences else 0.8

        fusion_result = EvidenceFusionEngine.fuse(
            {
                "visual": df_overall,
                "blending": blend_overall,
                "temporal": tp_overall,
                "frequency": fr_overall,
                "lip_sync": float(lip_sync_res["lip_sync_score"])
                            if lip_sync_res["status"] == "COMPLETED" else None,
                "audio_spoof": float(spoof_res["audio_spoof_score"])
                               if spoof_res["status"] == "COMPLETED" else None,
                "metadata": float(meta_score),
            },
            visual_model_disagreement=disagreement_overall,
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
            "faces_analyzed": len(any_visual_scores),
            "tracks_detected": len(track_engines),
            "signal_scores": {
                "visual": df_overall,
                "blending": blend_overall,
                "temporal": tp_overall,
                "frequency": fr_overall,
                "lip_sync": float(lip_sync_res["lip_sync_score"]),
                "audio_spoof": float(spoof_res["audio_spoof_score"]),
                "metadata": float(meta_score),
            },
            "signal_detail": {
                "visual_disagreement": disagreement_overall,
                "visual_confidence": visual_conf_overall,
                "lip_correlation": float(lip_sync_res.get("correlation", 0.0)),
                "lip_status": lip_sync_res["status"],
                "spoof_status": spoof_res["status"],
                "spoof_features": spoof_res.get("features", {}),
                "temporal_tracks": len(track_engines),
            },
        }
        job.report_data = report_data_dict
        flag_modified(job, "report_data")
        flag_modified(job, "evidence")

        job.completed_at = datetime.datetime.utcnow()
        db.commit()
        print(f"[worker] Job {job_id} complete => {fusion_result['classification']} "
              f"({fusion_result['final_score']:.3f}) | signals={report_data_dict['signal_scores']}")

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
