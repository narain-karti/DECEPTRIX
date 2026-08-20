import cv2
import numpy as np
from transformers import pipeline
from PIL import Image

detector = pipeline('image-classification', model='dima806/deepfake_vs_real_image_detection')

# Create a dummy image
img = np.zeros((300, 300, 3), dtype=np.uint8)
pil_img = Image.fromarray(img)

res = detector(pil_img)
print(res)
