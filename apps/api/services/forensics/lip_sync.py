import numpy as np
import librosa
from scipy.stats import pearsonr
from typing import Dict, List, Any

class AudioVisualSyncEngine:
    def __init__(self, fps: int = 15):
        self.fps = fps
        self.mar_series: List[float] = []

    def add_mar(self, mar: float):
        self.mar_series.append(mar)

    def analyze(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyzes correlation between Mouth Aspect Ratio (MAR) and audio RMS energy.
        Returns INSUFFICIENT_EVIDENCE if video is silent, face doesn't move, or audio is missing.
        """
        if not self.mar_series or len(self.mar_series) < self.fps:
            return self._insufficient_evidence("Not enough facial frames.")

        try:
            waveform, sample_rate = librosa.load(audio_path, sr=16000)
            hop_length = sample_rate // self.fps
            rms = librosa.feature.rms(y=waveform, hop_length=hop_length)[0]

            min_len = min(len(self.mar_series), len(rms))
            mar_aligned = np.array(self.mar_series[:min_len])
            rms_aligned = rms[:min_len]

            if np.std(mar_aligned) <= 1e-5:
                return self._insufficient_evidence("No significant mouth movement detected.")
                
            if np.std(rms_aligned) <= 1e-5:
                return self._insufficient_evidence("No significant audio energy detected (silent video).")

            correlation, _ = pearsonr(mar_aligned, rms_aligned)
            if np.isnan(correlation):
                return self._insufficient_evidence("Correlation could not be computed.")

            # Calculate score (invert the correlation logic so low correlation = high deepfake score)
            lip_sync_score = 0.50
            if correlation > 0.40:
                # Strong correlation -> real video
                lip_sync_score = max(0.00, 0.20 - (correlation * 0.2))
            elif correlation > 0.15:
                # Moderate correlation -> suspicious
                lip_sync_score = 0.45
            else:
                # Low/negative correlation -> high probability of deepfake
                lip_sync_score = min(0.98, 0.85 - (correlation * 0.5))
                
            return {
                "lip_sync_score": float(lip_sync_score),
                "correlation": float(correlation),
                "status": "COMPLETED",
                "message": "Successful lip-sync correlation."
            }

        except Exception as e:
            return self._insufficient_evidence(f"Error processing audio: {e}")

    def _insufficient_evidence(self, reason: str) -> Dict[str, Any]:
        return {
            "lip_sync_score": 0.0,
            "correlation": 0.0,
            "status": "INSUFFICIENT_EVIDENCE",
            "message": reason
        }
