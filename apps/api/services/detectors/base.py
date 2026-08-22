from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class VisualDeepfakeDetector(ABC):
    """Base class for all visual deepfake detectors."""

    @abstractmethod
    def load_model(self) -> None:
        """Lazy load the model into memory."""
        ...

    @abstractmethod
    def predict(self, face_image: Any) -> Dict[str, Any]:
        """
        Run inference on a single cropped face image (PIL or numpy array).
        Returns:
        {
            "fake_score": float in [0,1],
            "real_score": float in [0,1],
            "confidence": float in [0,1],
            "model_name": str,
            "raw_logits": Optional[list]
        }
        """
        ...
