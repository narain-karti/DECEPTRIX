import os
from .base import VisualDeepfakeDetector
from .dima_detector import Dima806Detector
from .prithiv_detector import PrithivDeepFakeV2Detector
from .ensemble import EnsembleVisualDetector

_DETECTOR_SINGLETON: VisualDeepfakeDetector | None = None


def get_detector() -> VisualDeepfakeDetector:
    """Return a process-wide detector singleton (models load once)."""
    global _DETECTOR_SINGLETON
    if _DETECTOR_SINGLETON is None:
        mode = os.environ.get("VISUAL_MODEL_MODE", "ensemble").lower()
        if mode == "dima":
            _DETECTOR_SINGLETON = Dima806Detector()
        elif mode == "prithiv":
            _DETECTOR_SINGLETON = PrithivDeepFakeV2Detector()
        else:
            _DETECTOR_SINGLETON = EnsembleVisualDetector()
    return _DETECTOR_SINGLETON
