import cv2
import os
import numpy as np
from typing import Dict, Any, List, Optional
from PIL import Image

class FaceTracker:
    def __init__(self, confidence_threshold=0.5, iou_threshold=0.3):
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self._face_net = None
        
        # Keep track of the last known bounding box
        self.last_bbox = None
        self.frames_since_detection = 0
        self.max_coast_frames = 3

    def get_face_net(self):
        if self._face_net is None:
            prototxt_path = os.path.join("models", "cv2_dnn", "deploy.prototxt")
            model_path = os.path.join("models", "cv2_dnn", "res10_300x300_ssd_iter_140000.caffemodel")
            if os.path.exists(prototxt_path) and os.path.exists(model_path):
                self._face_net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
        return self._face_net

    def calculate_iou(self, boxA, boxB):
        # Calculate intersection over union to track the same face
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou

    def get_face_bbox(self, img_bgr: np.ndarray) -> Optional[tuple]:
        """Returns (startX, startY, endX, endY) for the primary tracked face."""
        net = self.get_face_net()
        if net is None:
            return None

        (h, w) = img_bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(img_bgr, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        best_box = None
        best_iou = 0.0

        for j in range(0, detections.shape[2]):
            confidence = detections[0, 0, j, 2]
            if confidence > self.confidence_threshold:
                box = detections[0, 0, j, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                (startX, startY) = (max(0, startX), max(0, startY))
                (endX, endY) = (min(w - 1, endX), min(h - 1, endY))
                
                if startX >= endX or startY >= endY:
                    continue
                
                current_box = (startX, startY, endX, endY)

                if self.last_bbox is not None:
                    iou = self.calculate_iou(self.last_bbox, current_box)
                    if iou > best_iou:
                        best_iou = iou
                        best_box = current_box
                else:
                    best_box = current_box
                    break

        if best_box is not None:
            self.last_bbox = best_box
            self.frames_since_detection = 0
            return best_box
        else:
            if self.last_bbox is not None and self.frames_since_detection < self.max_coast_frames:
                self.frames_since_detection += 1
                return self.last_bbox
            else:
                self.last_bbox = None
                return None

def preprocess_face_for_model(img_bgr: np.ndarray, bbox: tuple, padding_ratio: float = 1.35) -> Optional[Image.Image]:
    """
    Crops the face preserving aspect ratio, converts to RGB, and returns a PIL Image.
    """
    (startX, startY, endX, endY) = bbox
    (h, w) = img_bgr.shape[:2]

    box_w = endX - startX
    box_h = endY - startY
    center_x = (startX + endX) // 2
    center_y = (startY + endY) // 2
    
    # Force a square crop preserving aspect ratio
    crop_size = int(max(box_w, box_h) * padding_ratio)

    p_startX = max(0, center_x - crop_size // 2)
    p_startY = max(0, center_y - crop_size // 2)
    p_endX = min(w, center_x + crop_size // 2)
    p_endY = min(h, center_y + crop_size // 2)
    
    face_crop = img_bgr[p_startY:p_endY, p_startX:p_endX]
    
    if face_crop.size == 0:
        return None
        
    face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    return Image.fromarray(face_rgb)
