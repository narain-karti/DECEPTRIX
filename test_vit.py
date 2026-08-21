import cv2
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification
import numpy as np

processor = AutoImageProcessor.from_pretrained("dima806/deepfake_vs_real_image_detection")
model = AutoModelForImageClassification.from_pretrained("dima806/deepfake_vs_real_image_detection")
model.eval()

print("Model id2label:", model.config.id2label)
print("Model label2id:", model.config.label2id)

# Test on a dummy face / actual extracted faces in storage
import glob
face_files = glob.glob("storage/*_faces/*.jpg")
print(f"Found {len(face_files)} face files in storage.")

for f in face_files[:5]:
    img = Image.open(f).convert("RGB")
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]
    
    # Check prob 0 and prob 1
    p0 = probs[0].item()
    p1 = probs[1].item()
    print(f"{f} -> Class 0 ({model.config.id2label.get(0, '0')}): {p0:.4f}, Class 1 ({model.config.id2label.get(1, '1')}): {p1:.4f}")
