import glob
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

processor = AutoImageProcessor.from_pretrained("dima806/deepfake_vs_real_image_detection")
model = AutoModelForImageClassification.from_pretrained("dima806/deepfake_vs_real_image_detection")
model.eval()

# Let's inspect the files in apps/api/storage
storage_vids = glob.glob("apps/api/storage/*.mp4")
print("Storage videos:", storage_vids)

# Let's test on the real video frames vs face crops
for vid in storage_vids:
    print("\n--- Testing video:", vid)
    cap = cv2.VideoCapture(vid)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Frames: {total_frames}, FPS: {fps}")
    
    # Read a few sample frames
    ret, frame = cap.read()
    if ret:
        h, w = frame.shape[:2]
        print(f"Frame size: {w}x{h}")
        # Test full frame or padded crops
    cap.release()
