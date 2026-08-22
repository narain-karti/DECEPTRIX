"""
Temporal consistency forensics.

Tracks the full normalized facial landmark mesh across frames and measures
region-wise micro-motion variance. Face-swap pipelines (Roop/InSwapper,
FaceFusion, etc.) fail to reproduce natural per-landmark micro-tremor and
instead exhibit spatially correlated warping noise, which this engine picks
up. Scores are computed over sliding windows and shot-cuts are rejected.
"""
import numpy as np
from typing import List, Dict, Optional

from core.config import ForensicConfig

# Region definitions in MediaPipe FaceMesh landmark indices
REGIONS: Dict[str, List[int]] = {
    "eyes": [33, 133, 159, 145, 362, 263, 386, 374],
    "eyebrows": [70, 63, 105, 66, 300, 293, 334, 296],
    "nose": [1, 4, 5, 6, 168, 197, 195, 2],
    "mouth": [13, 14, 78, 308, 61, 291, 0, 17],
    "jaw": [172, 136, 150, 149, 176, 148, 152, 377],
    "cheeks": [50, 101, 118, 205, 280, 330, 347, 425],
}

# Natural stability weighting: rigid regions (eyes/nose) should move coherently
# with head pose; soft regions (mouth/jaw) legitimately deform more during
# speech, so they receive lower weight.
REGION_WEIGHTS: Dict[str, float] = {
    "eyes": 1.25,
    "eyebrows": 1.10,
    "nose": 1.20,
    "mouth": 0.70,
    "jaw": 0.80,
    "cheeks": 1.00,
}


class TemporalForensicsEngine:
    """
    Accumulates per-frame normalized landmark sets and produces a windowed
    temporal-consistency anomaly score in [0, 1].
    """

    def __init__(self):
        self.landmark_sequence: List[np.ndarray] = []   # each (468, 2), normalized
        self.window_scores: List[float] = []
        self._window_landmarks: List[np.ndarray] = []

    # ------------------------------------------------------------------
    def add_landmarks(self, landmarks_xy: np.ndarray, eye_dist_px: float) -> None:
        """
        Add one frame of landmarks.

        landmarks_xy : (N, 2) array of landmark coords in PIXEL space
        eye_dist_px  : inter-ocular distance in pixels (pose/scale normalizer)
        """
        if landmarks_xy is None or len(landmarks_xy) < 300 or eye_dist_px < 1e-3:
            return
        # Normalize translation + scale using eye distance so head motion
        # does not masquerade as jitter.
        centroid = landmarks_xy.mean(axis=0)
        normed = (landmarks_xy - centroid) / eye_dist_px
        self.landmark_sequence.append(normed)
        self._window_landmarks.append(normed)
        if len(self._window_landmarks) >= ForensicConfig.JITTER_WINDOW:
            score = self._score_window(self._window_landmarks)
            if score is not None:
                self.window_scores.append(score)
            self._window_landmarks = []

    # ------------------------------------------------------------------
    def _score_window(self, seq: List[np.ndarray]) -> Optional[float]:
        """Compute jitter anomaly score for a window of landmark frames."""
        n = len(seq)
        if n < ForensicConfig.MIN_CHUNK_SIZE:
            return None

        arr = np.stack(seq)                      # (T, N, 2)
        diffs = np.diff(arr, axis=0)             # (T-1, N, 2)
        step_mags = np.linalg.norm(diffs, axis=2)  # (T-1, N)

        # Global median step to reject shot-cuts / person switches
        global_step = float(np.median(step_mags))
        valid_mask = step_mags < max(ForensicConfig.JITTER_SHOT_CUT, global_step * 6.0)
        if valid_mask.sum() < 10:
            return None

        # ── Frozen-face check (puppet/static-photo tell) ────────────
        # After pose+scale normalization a LIVE face still exhibits
        # non-rigid micro-motion. Near-zero median step across the whole
        # mesh means the "face" is a rigidly moved static image.
        if global_step < ForensicConfig.JITTER_FROZEN_FLOOR:
            return float(ForensicConfig.JITTER_FROZEN_SCORE)

        region_scores: Dict[str, float] = {}
        for region_name, idxs in REGIONS.items():
            idxs = [i for i in idxs if i < arr.shape[1]]
            if len(idxs) < 3:
                continue
            region_diffs = diffs[:, idxs, :]     # (T-1, R, 2)
            # Spatial coherence: how synchronized are landmarks within region?
            # Deepfake warping tends to move neighbours inconsistently.
            per_lm_mag = np.linalg.norm(region_diffs, axis=2)   # (T-1, R)
            vmask = valid_mask[:, idxs]
            if vmask.sum() < 5:
                continue
            mags = per_lm_mag[vmask]
            mean_mag = float(mags.mean())
            var_mag = float(mags.var())
            # Flutter metric combines magnitude of micro-motion with its variance
            flutter = mean_mag + np.sqrt(var_mag)
            region_scores[region_name] = flutter

        if not region_scores:
            return None

        weighted = sum(
            region_scores[r] * REGION_WEIGHTS.get(r, 1.0) for r in region_scores
        ) / sum(REGION_WEIGHTS.get(r, 1.0) for r in region_scores)

        # Map flutter into [0,1]: below JITTER_NATURAL => 0, above SYNTHETIC => 1
        lo = ForensicConfig.JITTER_NATURAL
        hi = ForensicConfig.JITTER_SYNTHETIC
        score = float(min(1.0, max(0.0, (weighted - lo) / (hi - lo))))
        return score

    # ------------------------------------------------------------------
    def extract_temporal_score(self) -> float:
        """Aggregate all completed windows; flush partial window first."""
        if self._window_landmarks:
            score = self._score_window(self._window_landmarks)
            if score is not None:
                self.window_scores.append(score)
            self._window_landmarks = []

        if not self.window_scores:
            return 0.0
        # Use the 85th percentile: manipulation is intermittent, mean dilutes it
        return float(np.percentile(self.window_scores, 85))

    def get_region_report(self) -> Dict[str, float]:
        """Latest per-region flutter values (for explainability)."""
        out: Dict[str, float] = {}
        if self._window_landmarks:
            self._flush_partial()
        # recompute on full sequence at coarse level for reporting
        if len(self.landmark_sequence) >= ForensicConfig.MIN_CHUNK_SIZE:
            score = self._score_window(self.landmark_sequence[-ForensicConfig.JITTER_WINDOW:])
            if score is not None:
                out["overall"] = score
        return out

    def _flush_partial(self) -> None:
        score = self._score_window(self._window_landmarks)
        if score is not None:
            self.window_scores.append(score)
        self._window_landmarks = []

    def clear(self) -> None:
        self.landmark_sequence = []
        self.window_scores = []
        self._window_landmarks = []


def analyze_segment_consistency(visual_scores: List[float]) -> float:
    """High variance in visual scores across a segment hints at splice boundaries."""
    if len(visual_scores) < 3:
        return 0.0
    variance = float(np.var(visual_scores))
    return min(1.0, variance * 10.0)
