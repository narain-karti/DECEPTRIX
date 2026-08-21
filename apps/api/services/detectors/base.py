from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class VisualDeepfakeDetector(ABC):
    @abstractmethod
    def load_model(self) -> None:
        """Lazy load the model into memory."""
        pass

    @abstractmethod
    def predict(self, face_image: Any) -> Dict[str, Any]:
        """
        Run inference on a single cropped face image (PIL or numpy array).
        Returns a dictionary with:
        {
            "fake_score": float,
            "real_score": float,
            "confidence": float,
            "model_name": str,
            "raw_logits": Optional[Any]
        }
        """
        pass
