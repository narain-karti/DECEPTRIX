import glob
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

processor = AutoImageProcessor.from_pretrained("dima806/deepfake_vs_real_image_detection")
model = AutoModelForImageClassification.from_pretrained("dima806/deepfake_vs_real_image_detection")
model.eval()

prototxt_path = "apps/api/models/cv2_dnn/deploy.prototxt"
model_path = "apps/api/models/cv2_dnn/res10_300x300_ssd_iter_140000.caffemodel"
net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)

def score_deepfake_face_calibrated(pil_image):
    inputs = processor(images=pil_image, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits[0]
        # Logit delta: fake - real
        # id2label: {0: 'Real', 1: 'Fake'}
        delta = float((logits[1] - logits[0]).item())
        # Sigmoid calibration centered at delta=2.0
        calibrated_score = 1.0 / (1.0 + np.exp(-0.9 * (delta - 2.5)))
        return float(max(0.0, min(1.0, calibrated_score))), delta

# Let's test on the two videos:
# 1. AI Video: "WhatsApp Video 2026-08-20 at 5.26.11 PM.mp4"
# 2. Real Video uploaded in storage
vids = glob.glob("apps/api/storage/*.mp4")
print("Storage videos:", vids)

for vid in vids[-2:]:
    print(f"\n================ Testing Video: {vid} ================")
    cap = cv2.VideoCapture(vid)
    scores = []
    deltas = []
    
    for i in range(15):
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()
        
        for j in range(0, detections.shape[2]):
            confidence = detections[0, 0, j, 2]
            if confidence > 0.5:
                box = detections[0, 0, j, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                # Padded crop
                box_w = endX - startX
                box_h = endY - startY
                center_x = (startX + endX) // 2
                center_y = (startY + endY) // 2
                crop_size = int(max(box_w, box_h) * 1.35)
                
                p_startX = max(0, center_x - crop_size // 2)
                p_startY = max(0, center_y - crop_size // 2)
                p_endX = min(w, center_x + crop_size // 2)
                p_endY = min(h, center_y + crop_size // 2)
                
                face_crop = frame[p_startY:p_endY, p_startX:p_endX]
                if face_crop.size > 0:
                    pil_img = Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
                    sc, d = score_deepfake_face_calibrated(pil_img)
                    scores.append(sc)
                    deltas.append(d)
                break
    cap.release()
    print(f"Mean Score: {np.mean(scores):.4f}, Max Score: {np.max(scores):.4f}, Mean Delta: {np.mean(deltas):.2f}")
