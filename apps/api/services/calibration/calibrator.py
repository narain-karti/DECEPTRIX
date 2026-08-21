from typing import Dict, Any

class ModelCalibrator:
    def __init__(self, calibration_version="1.0-stub"):
        self.calibration_version = calibration_version

    def calibrate(self, raw_score: float, model_name: str, blur_variance: float = None) -> Dict[str, Any]:
        """
        Applies calibration to the raw score.
        Specifically handles the issue where image-based models (like ViT)
        hallucinate synthetic artifacts on blurry video frames.
        """
        calibrated = float(raw_score)
        method = "uncalibrated_raw"
        
        # Penalize score if the frame is blurry to prevent ViT hallucinations,
        # but don't penalize so heavily that actual deepfakes pass through as real.
        if blur_variance is not None and blur_variance < 100.0:
            confidence_penalty = (100.0 - blur_variance) / 100.0 
            # Suppress high fake scores caused by blur, but only slightly (max 20% reduction)
            if calibrated > 0.5:
                calibrated = calibrated - (calibrated * confidence_penalty * 0.2)
            method = "heuristic_blur_penalty_light"

        return {
            "calibrated_score": max(0.0, min(1.0, calibrated)),
            "calibration_version": self.calibration_version,
            "method": method
        }
