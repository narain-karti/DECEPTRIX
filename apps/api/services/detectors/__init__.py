import os
from .base import VisualDeepfakeDetector
from .dima_detector import Dima806Detector
from .prithiv_detector import PrithivDeepFakeV2Detector
from .ensemble import EnsembleVisualDetector

def get_detector() -> VisualDeepfakeDetector:
    mode = os.environ.get("VISUAL_MODEL_MODE", "ensemble").lower()
    
    if mode == "dima":
        return Dima806Detector()
    elif mode == "prithiv":
        return PrithivDeepFakeV2Detector()
    else:
        return EnsembleVisualDetector()
