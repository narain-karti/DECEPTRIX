import os
from typing import Dict, Any
from .base import VisualDeepfakeDetector
from .dima_detector import Dima806Detector
from .prithiv_detector import PrithivDeepFakeV2Detector
from core.config import ForensicConfig


class EnsembleVisualDetector(VisualDeepfakeDetector):
    """
    Weighted soft-voting ensemble with explicit model-disagreement tracking.
    Disagreement is surfaced to the fusion engine so conflicting expert
    opinions lower the overall assessment confidence.
    """

    def __init__(self):
        self.dima_detector = Dima806Detector()
        self.prithiv_detector = PrithivDeepFakeV2Detector()
        self.dima_weight = ForensicConfig.DIMA_WEIGHT
        self.prithiv_weight = ForensicConfig.PRITHIV_WEIGHT

    def load_model(self) -> None:
        self.dima_detector.load_model()
        self.prithiv_detector.load_model()

    def predict(self, face_image: Any) -> Dict[str, Any]:
        self.load_model()

        dima_result = self.dima_detector.predict(face_image)
        prithiv_result = self.prithiv_detector.predict(face_image)

        dima_score = dima_result["fake_score"]
        prithiv_score = prithiv_result["fake_score"]

        w_total = (self.dima_weight + self.prithiv_weight) or 1.0
        ensemble_score = (dima_score * self.dima_weight + prithiv_score * self.prithiv_weight) / w_total

        # Disagreement: 0 when identical, 1 when maximally opposed.
        model_disagreement = abs(dima_score - prithiv_score)

        avg_confidence = (dima_result["confidence"] + prithiv_result["confidence"]) / 2.0
        overall_confidence = avg_confidence * (1.0 - 0.5 * model_disagreement)

        return {
            "fake_score": max(0.0, min(1.0, ensemble_score)),
            "real_score": 1.0 - ensemble_score,
            "confidence": max(0.0, min(1.0, overall_confidence)),
            "model_name": "Ensemble(Dima806+PrithivV2)+TTA",
            "dima_score": dima_score,
            "prithiv_score": prithiv_score,
            "model_disagreement": model_disagreement,
        }
