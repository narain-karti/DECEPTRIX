import os
from typing import Dict, Any, Optional
from .base import VisualDeepfakeDetector
from .dima_detector import Dima806Detector
from .prithiv_detector import PrithivDeepFakeV2Detector

class EnsembleVisualDetector(VisualDeepfakeDetector):
    def __init__(self):
        self.dima_detector = Dima806Detector()
        self.prithiv_detector = PrithivDeepFakeV2Detector()
        
        # Make weights configurable
        self.dima_weight = float(os.environ.get("DIMA_WEIGHT", "0.5"))
        self.prithiv_weight = float(os.environ.get("PRITHIV_WEIGHT", "0.5"))

    def load_model(self) -> None:
        self.dima_detector.load_model()
        self.prithiv_detector.load_model()

    def predict(self, face_image: Any) -> Dict[str, Any]:
        self.load_model()
        
        dima_result = self.dima_detector.predict(face_image)
        prithiv_result = self.prithiv_detector.predict(face_image)
        
        dima_score = dima_result["fake_score"]
        prithiv_score = prithiv_result["fake_score"]
        
        ensemble_score = (dima_score * self.dima_weight) + (prithiv_score * self.prithiv_weight)
        
        model_disagreement = abs(dima_score - prithiv_score)
        
        # Calculate an overall confidence based on the models' individual confidences and their disagreement
        avg_confidence = (dima_result["confidence"] + prithiv_result["confidence"]) / 2.0
        
        # If models disagree strongly, overall confidence drops
        overall_confidence = avg_confidence * (1.0 - (model_disagreement * 0.5))
        
        return {
            "fake_score": ensemble_score,
            "real_score": 1.0 - ensemble_score,
            "confidence": overall_confidence,
            "model_name": "Ensemble (Dima + Prithiv)",
            "dima_score": dima_score,
            "prithiv_score": prithiv_score,
            "model_disagreement": model_disagreement
        }
