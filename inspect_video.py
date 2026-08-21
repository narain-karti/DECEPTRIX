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

latest_vid = "apps/api/storage/087dfd58-1cb4-4c61-926e-8a0b0c1b4667.mp4"
print("Inspecting video:", latest_vid)

cap = cv2.VideoCapture(latest_vid)
fps = cap.get(cv2.CAP_PROP_FPS) or 24
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"Total frames: {total_frames}, FPS: {fps}")

frame_idx = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    if frame_idx % 15 == 0:
        sec = frame_idx // 15
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()
        
        # Count all detected faces
        detected_faces = []
        for j in range(0, detections.shape[2]):
            confidence = detections[0, 0, j, 2]
            if confidence > 0.5:
                box = detections[0, 0, j, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                detected_faces.append((confidence, (startX, startY, endX, endY)))
        
        if detected_faces:
            conf, (startX, startY, endX, endY) = detected_faces[0]
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
                inputs = processor(images=pil_img, return_tensors="pt")
                with torch.no_grad():
                    logits = model(**inputs).logits[0]
                l_real = float(logits[0].item())
                l_fake = float(logits[1].item())
                delta = l_fake - l_real
                print(f"Sec {sec:02d}s | Faces: {len(detected_faces)} | Logits: Real={l_real:6.2f}, Fake={l_fake:6.2f}, Delta={delta:6.2f} | BBox: ({startX},{startY})-({endX},{endY})")
    frame_idx += 1

cap.release()
