import glob
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

processor = AutoImageProcessor.from_pretrained("dima806/deepfake_vs_real_image_detection")
model = AutoModelForImageClassification.from_pretrained("dima806/deepfake_vs_real_image_detection")
model.eval()

folders = glob.glob("apps/api/storage/*_faces")
for folder in folders:
    print("\n=== Folder:", folder)
    face_files = glob.glob(f"{folder}/*.jpg")
    for f in face_files[:3]:
        img = Image.open(f).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]
        p_real = probs[0].item()
        p_fake = probs[1].item()
        print(f"  {f} => Real: {p_real:.4f}, Fake: {p_fake:.4f}")
