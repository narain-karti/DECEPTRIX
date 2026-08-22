from typing import Dict, Any, Optional
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification
from .base import VisualDeepfakeDetector
from core.config import ForensicConfig


class PrithivDeepFakeV2Detector(VisualDeepfakeDetector):
    """
    ViT deepfake classifier v2 (prithivMLmods/Deep-Fake-Detector-v2-Model).
    Supports test-time augmentation (horizontal flip averaging).
    """

    def __init__(self):
        self.processor = None
        self.model = None
        self.model_name = "prithivMLmods/Deep-Fake-Detector-v2-Model"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.use_tta = ForensicConfig.USE_TTA

    def load_model(self) -> None:
        if self.model is None:
            print(f"[detector] Loading {self.model_name} on {self.device}...")
            self.processor = AutoImageProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForImageClassification.from_pretrained(self.model_name).to(self.device)
            self.model.eval()

    def _forward(self, images) -> torch.Tensor:
        inputs = self.processor(images=images, return_tensors="pt").to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            return torch.softmax(logits, dim=-1)

    def predict(self, face_image: Any) -> Dict[str, Any]:
        self.load_model()
        pil_imgs = [face_image] if isinstance(face_image, Image.Image) else [face_image]

        batch = list(pil_imgs)
        if self.use_tta:
            batch = batch + [img.transpose(Image.FLIP_LEFT_RIGHT) for img in pil_imgs]

        probs = self._forward(batch)
        n = len(pil_imgs)
        probs = probs[:n] if not self.use_tta else (probs[:n] + probs[n:]) / 2.0
        probs = probs[0]

        labels = self.model.config.id2label
        fake_idx = next((int(k) for k, v in labels.items() if "fake" in str(v).lower()), 1)
        real_idx = next((int(k) for k, v in labels.items() if "real" in str(v).lower()), 0)

        fake_score = float(probs[fake_idx].item())
        real_score = float(probs[real_idx].item())

        return {
            "fake_score": max(0.0, min(1.0, fake_score)),
            "real_score": max(0.0, min(1.0, real_score)),
            "confidence": max(fake_score, real_score),
            "model_name": "PrithivV2-ViT",
            "raw_logits": probs.cpu().tolist(),
        }
