"""
Audio deepfake (spoof) forensics.

Neural vocoders (HiFi-GAN, WaveNet, VITS) and TTS systems leave classical
signal traces that differ from human phonation:
  - Unnaturally stable F0 (pitch) within voiced segments
  - Reduced MFCC-delta variability (over-smoothed spectral trajectories)
  - Abnormal spectral flatness / envelope regularity
  - Atypical zero-crossing-rate dynamics

This engine extracts those descriptors from the 16 kHz mono PCM track and
fuses them into a bounded anomaly score. It is deliberately lightweight
(<0.5 s per video on CPU). When a GPU becomes available, an optional
wav2vec2-ASVspoof model can be layered in via env flag without changing
the interface.
"""
import os
import numpy as np
import librosa
from typing import Dict, Any


class AudioSpoofEngine:

    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate

    # ------------------------------------------------------------------
    def analyze(self, audio_path: str) -> Dict[str, Any]:
        if not os.path.exists(audio_path):
            return self._insufficient("No audio stream present.")

        try:
            y, sr = librosa.load(audio_path, sr=self.sr)
        except Exception as e:
            return self._insufficient(f"Audio decode failed: {e}")

        duration = len(y) / sr
        if duration < 1.5:
            return self._insufficient("Audio too short for spoof analysis.")

        rms = librosa.feature.rms(y=y)[0]
        if float(np.mean(rms)) < 1e-4 or float(np.std(rms)) < 5e-5:
            return self._insufficient("Silent or near-silent audio.")

        try:
            features = self._extract_features(y)
            score = self._score(features)
        except Exception as e:
            return self._insufficient(f"Feature extraction failed: {e}")

        return {
            "audio_spoof_score": float(score),
            "features": features,
            "status": "COMPLETED",
            "duration_sec": round(duration, 2),
            "message": f"Classical audio-forensics scan complete ({duration:.1f}s speech region).",
        }

    # ------------------------------------------------------------------
    def _extract_features(self, y: np.ndarray) -> Dict[str, float]:
        stft = np.abs(librosa.stft(y, n_fft=1024, hop_length=256))

        # ── MFCC trajectory statistics ───────────────────────────────
        mfcc = librosa.feature.mfcc(y=y, sr=self.sr, n_mfcc=20)
        mfcc_means = mfcc.mean(axis=1)
        # Delta variability: natural articulation varies more frame-to-frame
        deltas = librosa.feature.delta(mfcc)
        delta_var = float(deltas.var())

        # ── Spectral flatness (geometric/arithmetic mean ratio) ──────
        flatness = librosa.feature.spectral_flatness(y=y)
        flat_mean = float(flatness.mean())
        flat_std = float(flatness.std())

        # ── Spectral rolloff variance ────────────────────────────────
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=self.sr)
        rolloff_cv = float(rolloff.std() / (rolloff.mean() + 1e-6))

        # ── Zero crossing rate dynamics ──────────────────────────────
        zcr = librosa.feature.zero_crossing_rate(y)
        zcr_std = float(zcr.std())

        # ── Pitch (F0) stability — key vocoder tell ──────────────────
        f0 = librosa.yin(
            y, fmin=65, fmax=400, sr=self.sr,
            frame_length=1024, hop_length=256,
        )
        voiced = f0[(f0 > 65) & (f0 < 400)]
        if len(voiced) > 10:
            # Jitter proxy: relative std of consecutive F0 differences
            f0_diffs = np.abs(np.diff(voiced))
            jitter = float(np.mean(f0_diffs) / (np.mean(voiced) + 1e-6))
            f0_cov = float(voiced.std() / (voiced.mean() + 1e-6))
        else:
            jitter = 0.05   # neutral defaults when unvoiced
            f0_cov = 0.10

        # ── Spectral flux regularity (vocoder frames too uniform) ────
        flux = librosa.onset.onset_strength(y=y, sr=self.sr, hop_length=256)
        flux_cv = float(flux.std() / (flux.mean() + 1e-6))

        return {
            "mfcc_delta_var": delta_var,
            "flatness_mean": flat_mean,
            "flatness_std": flat_std,
            "rolloff_cv": rolloff_cv,
            "zcr_std": zcr_std,
            "f0_jitter": jitter,
            "f0_cov": f0_cov,
            "flux_cv": flux_cv,
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _score(f: Dict[str, float]) -> float:
        """
        Map feature vector to anomaly score.

        Operating points are conservative priors pending benchmark fitting;
        eval_pipeline.py refits these weights empirically.
        """
        def squash(v: float, lo: float, hi: float) -> float:
            return float(min(1.0, max(0.0, (v - lo) / max(hi - lo, 1e-9))))

        s_jitter = 1.0 - squash(f["f0_jitter"], 0.010, 0.045)   # TOO stable => suspicious
        s_f0cov  = 1.0 - squash(f["f0_cov"], 0.08, 0.25)         # narrow F0 range => suspicious
        s_delta  = 1.0 - squash(f["mfcc_delta_var"], 8.0, 40.0)  # over-smoothed => suspicious
        s_flat   = squash(f["flatness_mean"], 0.005, 0.030)      # buzzy flat spectrum => suspicious
        s_rolloff = 1.0 - squash(f["rolloff_cv"], 0.03, 0.12)    # static bandwidth => suspicious

        return float(
            0.28 * s_jitter + 0.22 * s_f0cov + 0.20 * s_delta +
            0.15 * s_flat + 0.15 * s_rolloff
        )

    # ------------------------------------------------------------------
    def _insufficient(self, reason: str) -> Dict[str, Any]:
        return {
            "audio_spoof_score": 0.0,
            "features": {},
            "status": "INSUFFICIENT_EVIDENCE",
            "duration_sec": 0.0,
            "message": reason,
        }
