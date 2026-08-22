"""
Audio-visual synchrony forensics.

Real speech exhibits a tight coupling between acoustic energy onsets and
mouth-opening (MAR). Audio-driven re-animation (Wav2Lip, SadTalker, etc.)
or dubbed audio breaks this coupling. Instead of naive zero-lag Pearson
correlation, this engine searches the best alignment lag within +/-0.5 s,
which removes false desync verdicts caused by container timestamp skew.
"""
import numpy as np
import librosa
from scipy.stats import pearsonr
from typing import Dict, List, Any

from core.config import ForensicConfig


class AudioVisualSyncEngine:
    def __init__(self, fps: int = None):
        self.fps = fps or ForensicConfig.ANALYSIS_FPS
        self.mar_series: List[float] = []

    def add_mar(self, mar: float):
        self.mar_series.append(float(mar))

    # ------------------------------------------------------------------
    @staticmethod
    def _best_lag_correlation(a: np.ndarray, b: np.ndarray, max_lag: int) -> float:
        """Return max |Pearson r| over all integer lags in [-max_lag, max_lag]."""
        n = len(a)
        best = 0.0
        best_signed = 0.0
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                seg_a, seg_b = a[-lag:], b[:n + lag]
            elif lag > 0:
                seg_a, seg_b = a[:n - lag], b[lag:]
            else:
                seg_a, seg_b = a, b
            if len(seg_a) < 10:
                continue
            if np.std(seg_a) < 1e-6 or np.std(seg_b) < 1e-6:
                continue
            r, _ = pearsonr(seg_a, seg_b)
            if not np.isnan(r) and abs(r) > abs(best):
                best = abs(r)
                best_signed = float(r)
        return best_signed

    # ------------------------------------------------------------------
    def analyze(self, audio_path: str) -> Dict[str, Any]:
        """
        Returns dict with:
          lip_sync_score : [0,1] anomaly score (high => desync => suspicious)
          correlation    : best signed correlation found
          lag_frames     : alignment offset that produced it
          status         : COMPLETED | INSUFFICIENT_EVIDENCE
        """
        import os
        if not self.mar_series or len(self.mar_series) < self.fps:
            return self._insufficient_evidence("Not enough facial frames.")

        if not os.path.exists(audio_path):
            return self._insufficient_evidence("No audio track extracted (silent or missing stream).")

        try:
            waveform, sample_rate = librosa.load(audio_path, sr=16000)
            hop_length = max(1, sample_rate // self.fps)
            rms = librosa.feature.rms(y=waveform, hop_length=hop_length)[0]

            min_len = min(len(self.mar_series), len(rms))
            if min_len < self.fps:
                return self._insufficient_evidence("Audio shorter than visual sequence.")

            mar_aligned = np.array(self.mar_series[:min_len])
            rms_aligned = rms[:min_len]

            if np.std(mar_aligned) <= 1e-5:
                return self._insufficient_evidence("No significant mouth movement detected.")
            if np.std(rms_aligned) <= 1e-5:
                return self._insufficient_evidence("No significant audio energy detected (silent video).")

            max_lag = int(round(ForensicConfig.LIP_MAX_LAG_SEC * self.fps))
            correlation = self._best_lag_correlation(mar_aligned, rms_aligned, max_lag)

            if correlation is None or np.isnan(correlation):
                return self._insufficient_evidence("Correlation could not be computed.")

            lip_sync_score = self._score_from_correlation(correlation)

            return {
                "lip_sync_score": float(lip_sync_score),
                "correlation": float(correlation),
                "lag_frames": int(max_lag),
                "status": "COMPLETED",
                "message": (
                    f"Best audio-visual alignment r={correlation:.3f} "
                    f"within ±{ForensicConfig.LIP_MAX_LAG_SEC}s."
                ),
            }

        except Exception as e:
            return self._insufficient_evidence(f"Error processing audio: {e}")

    # ------------------------------------------------------------------
    def _score_from_correlation(self, corr: float) -> float:
        """
        Map signed best-lag correlation to an anomaly score.
        Strong positive sync  -> low score (authentic)
        Weak / negative sync  -> high score (suspicious)
        """
        c = ForensicConfig
        if corr >= c.LIP_STRONG_CORR:
            # 0.35 -> ~0.15 ; 0.8 -> ~0.0
            return float(max(0.0, 0.25 - corr * 0.30))
        if corr >= c.LIP_WEAK_CORR:
            # Interpolation zone: ambiguous
            t = (corr - c.LIP_WEAK_CORR) / (c.LIP_STRONG_CORR - c.LIP_WEAK_CORR)
            return float(0.50 - t * 0.22)
        # Below weak threshold: treat as desynced; negative corr is worst
        base = 0.62 + min(abs(min(corr, 0.0)), 0.5) * 0.5
        return float(min(0.98, base))

    # ------------------------------------------------------------------
    def _insufficient_evidence(self, reason: str) -> Dict[str, Any]:
        return {
            "lip_sync_score": 0.0,
            "correlation": 0.0,
            "lag_frames": 0,
            "status": "INSUFFICIENT_EVIDENCE",
            "message": reason,
        }
