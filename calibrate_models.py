import glob
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

processor = AutoImageProcessor.from_pretrained("dima806/deepfake_vs_real_image_detection")
model = AutoModelForImageClassification.from_pretrained("dima806/deepfake_vs_real_image_detection")
model.eval()

# Let's check the raw logits of the model on the storage face crops!
face_files = glob.glob("apps/api/storage/*_faces/*.jpg")[:10]

for f in face_files:
    img = Image.open(f).convert("RGB")
    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits[0]
        # Raw logits:
        l_real = logits[0].item()
        l_fake = logits[1].item()
        
        # Softmax without temperature
        p_raw = torch.softmax(logits, dim=-1)[1].item()
        
        # Temperature scaled softmax (T=2.0, 3.0)
        p_t2 = torch.softmax(logits / 2.0, dim=-1)[1].item()
        p_t3 = torch.softmax(logits / 3.0, dim=-1)[1].item()
        
        print(f"{f[-25:]} | Logits: Real={l_real:.2f}, Fake={l_fake:.2f} | Raw Fake Prob={p_raw:.4f} | T=2 Fake={p_t2:.4f} | T=3 Fake={p_t3:.4f}")
