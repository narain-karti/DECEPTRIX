from typing import Dict, Any, Optional
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
from .base import VisualDeepfakeDetector

class Dima806Detector(VisualDeepfakeDetector):
    def __init__(self):
        self.processor = None
        self.model = None
        self.model_name = "dima806/deepfake_vs_real_image_detection"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_model(self) -> None:
        if self.model is None:
            print(f"Loading {self.model_name} on {self.device}...")
            self.processor = AutoImageProcessor.from_pretrained(self.model_name)
            self.model = AutoModelForImageClassification.from_pretrained(self.model_name).to(self.device)
            self.model.eval()

    def predict(self, face_image: Any) -> Dict[str, Any]:
        self.load_model()
        inputs = self.processor(images=[face_image], return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits[0]
            probs = torch.softmax(logits, dim=-1)

        labels = self.model.config.id2label
        fake_idx = next((k for k, v in labels.items() if 'fake' in str(v).lower()), 1)
        real_idx = next((k for k, v in labels.items() if 'real' in str(v).lower()), 0)
        
        fake_score = float(probs[fake_idx].item())
        real_score = float(probs[real_idx].item())

        return {
            "fake_score": max(0.0, min(1.0, fake_score)),
            "real_score": max(0.0, min(1.0, real_score)),
            "confidence": max(fake_score, real_score),
            "model_name": "Dima806",
            "raw_logits": logits.cpu().tolist()
        }
