"""
Pure forensic pipeline — no DB, no Celery, no framework coupling.

This module is the single source of truth for media analysis. It is called
by:
  - services/media_worker.py  (Celery task wrapper persisting to Job rows)
  - scripts/eval_pipeline.py  (benchmark harness, in-process)

Contract:
    run_forensic_pipeline(job_id, file_path, faces_dir=None, on_progress=None)
      -> {
        "error": None | str,
        "verdict": str,
        "evidence": [EvidenceEvent dicts],
        "report_data": {...},
      }
"""
import os
import glob
import shutil
import subprocess

import cv2
import numpy as np
import mediapipe as mp

from core.config import ForensicConfig

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
from schemas.common import EvidenceEvent


def _extract_frames_ffmpeg(file_path: str, temp_dir: str, fps: int) -> bool:
    try:
        cmd = [
            "ffmpeg", "-i", file_path, "-vf", f"fps={fps}",
            os.path.join(temp_dir, "frame_%05d.jpg"), "-y",
        ]
        subprocess.run(cmd, capture_output=True, check=True, timeout=300)
        return True
    except Exception as e:
        print(f"[pipeline] ffmpeg frame extraction failed: {e}")
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
        print(f"[pipeline] cv2 frame extraction failed: {e}")
        return False


def run_forensic_pipeline(
    job_id: str,
    file_path: str,
    faces_dir: str = None,
    on_progress=None,
):
    """
    Execute the full 7-signal forensic analysis on a video file.

    on_progress(progress:int 0-100, step:str) fires at stage boundaries.
    faces_dir: when set, per-face crops are written there (UI/report needs).
    """
    ANALYSIS_FPS = ForensicConfig.ANALYSIS_FPS

    def _report(pct, step):
        if on_progress:
            try:
                on_progress(int(pct), step)
            except Exception:
                pass

    result = {
        "error": None,
        "verdict": None,
        "evidence": [],
        "report_data": {},
    }
    temp_dir = os.path.join(os.path.dirname(file_path), f"_bench_tmp_{os.getpid()}")

    try:
        # ── Stage 1: Metadata ────────────────────────────────────────
        _report(5, "Extracting technical metadata (FFprobe)...")
        metadata, meta_score, meta_reasons = MetadataEvidence.extract(file_path)

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
        frame_events = [meta_evidence]
        result["evidence"].append(meta_evidence)
        result["report_data"] = {"metadata": metadata}

        # ── Stage 2: Demux ───────────────────────────────────────────
        _report(10, f"Demuxing video ({ANALYSIS_FPS} FPS)...")
        os.makedirs(temp_dir, exist_ok=True)
        extraction_ok = _extract_frames_ffmpeg(file_path, temp_dir, ANALYSIS_FPS)
        if not extraction_ok:
            extraction_ok = _extract_frames_cv2(
                file_path, temp_dir, ANALYSIS_FPS, ForensicConfig.MAX_FRAMES
            )
        if not extraction_ok:
            raise RuntimeError("Could not decode video frames with ffmpeg or OpenCV.")

        audio_path = os.path.join(temp_dir, "audio.wav")
        has_audio = True
        try:
            subprocess.run(
                ["ffmpeg", "-i", file_path, "-vn", "-acodec", "pcm_s16le",
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

        if faces_dir:
            os.makedirs(faces_dir, exist_ok=True)

        _report(18, "Loading forensic engines...")

        detector = get_detector()
        face_tracker = MultiFaceTracker(max_faces=3)
        audio_engine = AudioVisualSyncEngine(fps=ANALYSIS_FPS)
        spoof_engine = AudioSpoofEngine()
        calibrator = ModelCalibrator()
        freq_engine = FrequencyForensicsEngine()

        track_engines, track_scores, track_blends = {}, {}, {}
        all_freq_scores, all_disagreements, all_confidences = [], [], []

        def _engine_for(tid):
            if tid not in track_engines:
                track_engines[tid] = TemporalForensicsEngine()
                track_scores[tid] = []
                track_blends[tid] = []
            return track_engines[tid]

        total_frames = len(frames)
        mp_face_mesh = mp.solutions.face_mesh

        # ── Stage 3: Multi-face frame loop ───────────────────────────
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

                lm_sets = []
                if mesh_results and mesh_results.multi_face_landmarks:
                    for lms in mesh_results.multi_face_landmarks:
                        arr = np.array(
                            [[p.x * fw, p.y * fh] for p in lms.landmark], dtype=np.float32
                        )
                        lm_sets.append({"center": arr.mean(axis=0), "landmarks": lms, "px": arr})

                frame_faces_payload = []
                for rank, tr in enumerate(tracks):
                    tid = tr["track_id"]
                    bbox = tuple(int(v) for v in tr["bbox"])
                    sx, sy, ex, ey = bbox
                    is_primary = rank == 0

                    t_engine = _engine_for(tid)
                    box_center = np.array([(sx + ex) / 2.0, (sy + ey) / 2.0], dtype=np.float32)

                    landmarks = None
                    landmarks_px = None
                    best_d = 1e12
                    for ls in lm_sets:
                        d = float(np.linalg.norm(ls["center"] - box_center))
                        if d < best_d:
                            best_d = d
                            landmarks = ls["landmarks"]
                            landmarks_px = ls["px"]
                    if best_d > max(ex - sx, ey - sy):
                        landmarks = None
                        landmarks_px = None

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

                    blend_res = BlendingAnalyzer.analyze(img, bbox)
                    blend_score = (
                        float(blend_res["blending_score"])
                        if blend_res.get("status") == "COMPLETED" else None
                    )
                    if blend_score is not None:
                        track_blends[tid].append(blend_score)

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
                        if faces_dir:
                            face_filename = f"seq_{i:04d}_t{tid}.jpg"
                            face_filepath = os.path.join(faces_dir, face_filename)
                            cv2.imwrite(face_filepath, face_crop_bgr)

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

                        det_result = detector.predict(pil_face)
                        calibrated = calibrator.calibrate(
                            det_result["fake_score"],
                            det_result["model_name"],
                            blur_variance=blur_variance,
                        )
                        fake_score = calibrated["calibrated_score"]
                        raw_score = float(det_result["fake_score"])
                        confidence = float(det_result.get("confidence", 0.8))
                        disagreement = float(det_result.get("model_disagreement", 0.0))

                        track_scores[tid].append(fake_score)
                        all_confidences.append(confidence)
                        all_disagreements.append(disagreement)

                    frame_faces_payload.append({
                        "track_id": tid,
                        "is_primary": is_primary,
                        "bbox": [sx, sy, ex, ey],
                        "confidence": confidence,
                        "fake_score": fake_score,
                        "raw_fake_score": raw_score,
                        "jitter_score": float(t_engine.window_scores[-1])
                                        if t_engine.window_scores else 0.0,
                        "freq_score": float(freq_features.get("freq_score", 0.0)),
                        "blending_score": blend_score,
                        "blur_variance": float(blur_variance) if blur_variance is not None else None,
                        "eye_distance": float(eye_dist) if eye_dist else None,
                        "face_crop": face_filepath,
                    })

                if not frame_faces_payload:
                    continue

                chunk_ts = round(i / ANALYSIS_FPS, 2)
                scored = [f for f in frame_faces_payload if f["fake_score"] is not None]
                frame_vis_score = max((f["fake_score"] for f in scored), default=0.0)

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
                vis_evidence_obj = dict(vis_evidence)
                vis_evidence_obj["artifact_refs"] = [
                    {"timestamp_sec": chunk_ts, "faces": frame_faces_payload}
                ]
                frame_events.append(vis_evidence_obj)
                result["evidence"].append(vis_evidence_obj)

                if i % 8 == 0 or i == total_frames - 1:
                    _report(
                        22 + min(48, int((i / max(total_frames, 1)) * 48)),
                        f"Keyframe {i + 1}/{total_frames} (t={chunk_ts:.1f}s) — "
                        f"{len(track_engines)} face(s) under analysis",
                    )

        any_visual_scores = [s for lst in track_scores.values() for s in lst]
        if not any_visual_scores:
            raise RuntimeError("No analyzable faces found in any sampled frame.")

        # ── Stage 4: Audio analyses ──────────────────────────────────
        _report(74, "Computing lag-searched lip-sync + audio-forensics scan...")

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
        frame_events.append(audio_evidence)
        result["evidence"].append(audio_evidence)

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
        frame_events.append(spoof_evidence)
        result["evidence"].append(spoof_evidence)

        # ── Stage 5: Fusion ──────────────────────────────────────────
        _report(90, "Fusing 7-signal evidence (log-odds Bayesian)...")

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
            [e for e in result["evidence"] if e.get("modality") == "visual"],
            fps=ANALYSIS_FPS,
        )

        result["verdict"] = fusion_result["classification"]
        result["error"] = None
        result["report_data"] = {
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

        _report(100, "Analysis complete.")
        print(f"[pipeline] {job_id}: {fusion_result['classification']} "
              f"({fusion_result['final_score']:.3f})")

    except Exception as e:
        import traceback
        traceback.print_exc()
        result["error"] = str(e)[:300]

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return result
