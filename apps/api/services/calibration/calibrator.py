"""
Score calibration.

Raw ViT outputs are not true probabilities: they are systematically
overconfident on blurry/compressed frames. This calibrator applies:

1. Per-model Platt scaling  p = sigmoid(A * raw + B)   when calibration
   parameters exist in services/calibration/params/<model>.json
   (fit offline with calibrate_models.py on labelled validation data).
2. Blur-aware damping driven by Laplacian variance, smoothly interpolated
   between BLUR_FLOOR and BLUR_CEILING instead of a binary cliff.
3. Compression-awareness: heavily blocky frames receive additional gentle
   suppression of high visual scores.
"""
import os
import json
import math
from typing import Dict, Any, Optional

from core.config import ForensicConfig

_PARAMS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "params")


def _load_params(model_name: str) -> Optional[Dict[str, float]]:
    for candidate in (model_name, model_name.split("(")[0].strip()):
        path = os.path.join(_PARAMS_DIR, f"{candidate}.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as fh:
                    data = json.load(fh)
                if "A" in data and "B" in data:
                    return {"A": float(data["A"]), "B": float(data["B"])}
            except Exception:
                pass
    return None


class ModelCalibrator:
    def __init__(self, calibration_version: str = "2.0-platt-blur"):
        self.calibration_version = calibration_version
        self._param_cache: Dict[str, Optional[Dict[str, float]]] = {}

    # ------------------------------------------------------------------
    def _platt(self, raw_score: float, model_name: str) -> tuple:
        if model_name not in self._param_cache:
            self._param_cache[model_name] = _load_params(model_name)
        params = self._param_cache[model_name]
        if params is None:
            return raw_score, False
        z = params["A"] * raw_score + params["B"]
        p = 1.0 / (1.0 + math.exp(-z))
        return max(0.0, min(1.0, p)), True

    # ------------------------------------------------------------------
    def calibrate(
        self,
        raw_score: float,
        model_name: str,
        blur_variance: Optional[float] = None,
        blockiness: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Returns calibrated score in [0,1] plus the methods applied, so the
        evidence trail records exactly what transformation occurred.
        """
        calibrated = max(0.0, min(1.0, float(raw_score)))
        methods = []

        # 1. Platt scaling when fitted parameters exist
        platted, applied = self._platt(calibrated, model_name)
        if applied:
            calibrated = platted
            methods.append("platt")

        # 2. Smooth blur-aware damping of HIGH fake scores only.
        #    Blurry genuine footage is the #1 source of ViT false positives;
        #    we never boost scores upward from blur.
        if blur_variance is not None and calibrated > 0.5:
            lo = ForensicConfig.BLUR_FLOOR
            hi = ForensicConfig.BLUR_CEILING
            t = max(0.0, min(1.0, (float(blur_variance) - lo) / max(hi - lo, 1e-6)))
            # t=0 (very blurry) => full suppression; t=1 (sharp) => none
            suppression = ForensicConfig.BLUR_MAX_SUPPRESSION * (1.0 - t)
            distance_from_neutral = calibrated - 0.5
            calibrated = calibrated - distance_from_neutral * suppression
            if suppression > 0.01:
                methods.append(f"blur_damp({suppression:.2f})")

        # 3. Blockiness damping (double-compressed / low-bitrate frames)
        if blockiness is not None and calibrated > 0.5 and blockiness > 0.5:
            damp = min(0.10, (blockiness - 0.5) * 0.08)
            distance_from_neutral = calibrated - 0.5
            calibrated = calibrated - distance_from_neutral * damp * 2.0
            methods.append(f"block_damp({damp:.2f})")

        return {
            "calibrated_score": round(max(0.0, min(1.0, calibrated)), 4),
            "calibration_version": self.calibration_version,
            "method": "+".join(methods) if methods else "passthrough",
        }
