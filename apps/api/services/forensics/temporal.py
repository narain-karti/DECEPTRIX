import numpy as np
from typing import List, Dict

class TemporalForensicsEngine:
    def __init__(self):
        self.jitter_scores = []
        
    def add_jitter(self, eye_distance: float):
        self.jitter_scores.append(eye_distance)
        
    def extract_temporal_score(self) -> float:
        """
        Calculates high-frequency differential jitter.
        """
        if len(self.jitter_scores) < 4:
            return 0.0
            
        diffs = np.abs(np.diff(self.jitter_scores))
        mean_eye = np.mean(self.jitter_scores) + 1e-6
        rel_diffs = diffs / mean_eye
        
        # Reject shot-cuts or person switches (jumps > 0.20)
        valid_diffs = [d for d in rel_diffs if d < 0.20]
        if len(valid_diffs) >= 3:
            high_freq_flutter = float(np.mean(valid_diffs))
            # Natural human head motion < 0.05; synthetic face warping > 0.12
            visual_jitter_score = float(min(1.0, max(0.0, (high_freq_flutter - 0.05) / 0.08)))
        else:
            visual_jitter_score = 0.0
            
        return visual_jitter_score

    def clear(self):
        self.jitter_scores = []

def analyze_segment_consistency(visual_scores: List[float]) -> float:
    """Analyze the variance of the visual scores in a segment. High variance might indicate manipulation boundary."""
    if len(visual_scores) < 3:
        return 0.0
    variance = float(np.var(visual_scores))
    # Synthetic swaps often have high variance due to flickering or failure cases
    return min(1.0, variance * 10.0)
