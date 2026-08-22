"""
Face detection, tracking and alignment pipeline.

Strategy
--------
1. Primary detector: OpenCV DNN ResNet-SSD (fast, robust) if model files exist.
2. Fallback detector: MediaPipe FaceDetection (always available with mediapipe).
3. Landmarks: MediaPipe FaceMesh (468 pts, refined irises when available).
4. Tracking: IoU association + exponential moving average smoothing.
5. Alignment: similarity warp driven by eye centres -> upright 224x224 crop,
   which measurably improves ViT classifier stability vs. naive crops.
"""
import os
import math
import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple
from PIL import Image

from core.config import ForensicConfig

# Canonical MediaPipe FaceMesh landmark indices
LM_LEFT_EYE_OUTER = 33
LM_RIGHT_EYE_OUTER = 263
LM_LEFT_IRIS = 468      # requires refine_landmarks=True
LM_RIGHT_IRIS = 473
LM_TOP_LIP_INNER = 13
LM_BOTTOM_LIP_INNER = 14
LM_LEFT_LIP_CORNER = 78
LM_RIGHT_LIP_CORNER = 308


class FaceTracker:
    """
    Stateful primary-face detector/tracker.

    Returns smoothed bounding boxes (startX, startY, endX, endY) and can
    coast over short detection drop-outs (<= max_coast_frames).
    """

    def __init__(self, confidence_threshold: float = None, iou_threshold: float = 0.3):
        self.confidence_threshold = confidence_threshold or ForensicConfig.FACE_DET_CONFIDENCE
        self.iou_threshold = iou_threshold
        self._face_net = None
        self._mp_detection = None

        self.last_bbox: Optional[Tuple[int, int, int, int]] = None
        self.frames_since_detection = 0
        self.max_coast_frames = 3

    # ------------------------------------------------------------------
    # Backends
    # ------------------------------------------------------------------
    def _get_face_net(self):
        if self._face_net is None:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            prototxt_path = os.path.join(base, "models", "cv2_dnn", "deploy.prototxt")
            model_path = os.path.join(base, "models", "cv2_dnn", "res10_300x300_ssd_iter_140000.caffemodel")
            if os.path.exists(prototxt_path) and os.path.exists(model_path):
                try:
                    self._face_net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
                except Exception:
                    self._face_net = None
        return self._face_net

    def _detect_dnn(self, img_bgr: np.ndarray) -> list:
        """Detect faces with the Caffe SSD model; returns raw boxes."""
        net = self._get_face_net()
        if net is None:
            return []
        (h, w) = img_bgr.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(img_bgr, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()
        boxes = []
        for j in range(detections.shape[2]):
            conf = float(detections[0, 0, j, 2])
            if conf > self.confidence_threshold:
                box = detections[0, 0, j, 3:7] * np.array([w, h, w, h])
                sx, sy, ex, ey = box.astype("int")
                sx, sy = max(0, sx), max(0, sy)
                ex, ey = min(w - 1, ex), min(h - 1, ey)
                if ex > sx and ey > sy:
                    boxes.append((sx, sy, ex, ey))
        return boxes

    def _detect_mediapipe(self, img_bgr: np.ndarray) -> list:
        """Fallback detector using MediaPipe FaceDetection."""
        try:
            import mediapipe as mp
        except ImportError:
            return []
        if self._mp_detection is None:
            self._mp_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=self.confidence_threshold
            )
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        res = self._mp_detection.process(rgb)
        boxes = []
        if res.detections:
            (h, w) = img_bgr.shape[:2]
            for det in res.detections:
                bb = det.location_data.relative_bounding_box
                sx = max(0, int(bb.xmin * w))
                sy = max(0, int(bb.ymin * h))
                ex = min(w - 1, int((bb.xmin + bb.width) * w))
                ey = min(h - 1, int((bb.ymin + bb.height) * h))
                if ex > sx and ey > sy:
                    boxes.append((sx, sy, ex, ey))
        return boxes

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_iou(boxA, boxB) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
        boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
        return interArea / float(boxAArea + boxBArea - interArea + 1e-6)

    def _smooth(self, new_bbox) -> Tuple[int, int, int, int]:
        """Exponential moving average on bbox corners for temporal stability."""
        a = ForensicConfig.FACE_EMA_ALPHA
        if self.last_bbox is None or a >= 1.0:
            smoothed = new_bbox
        else:
            smoothed = tuple(
                int(round(a * n + (1 - a) * o)) for n, o in zip(new_bbox, self.last_bbox)
            )
        return smoothed

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_face_bbox(self, img_bgr: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Return the tracked primary-face bbox, or None after losing track."""
        boxes = self._detect_dnn(img_bgr)
        if not boxes:
            boxes = self._detect_mediapipe(img_bgr)

        best_box = None
        best_iou = 0.0
        for current_box in boxes:
            if self.last_bbox is not None:
                iou = self.calculate_iou(self.last_bbox, current_box)
                if iou > best_iou:
                    best_iou = iou
                    best_box = current_box
            else:
                # No track yet: pick the largest face in frame
                if best_box is None:
                    best_box = current_box
                else:
                    area_cur = (current_box[2] - current_box[0]) * (current_box[3] - current_box[1])
                    area_best = (best_box[2] - best_box[0]) * (best_box[3] - best_box[1])
                    if area_cur > area_best:
                        best_box = current_box

        if best_box is not None:
            self.last_bbox = self._smooth(best_box)
            self.frames_since_detection = 0
            return self.last_bbox

        if self.last_bbox is not None and self.frames_since_detection < self.max_coast_frames:
            self.frames_since_detection += 1
            return self.last_bbox

        self.last_bbox = None
        return None

    def reset(self) -> None:
        self.last_bbox = None
        self.frames_since_detection = 0


class MultiFaceTracker:
    """
    Tracks up to `max_faces` simultaneous faces with greedy IoU association.
    Each track carries a stable id, EMA-smoothed bbox, and miss counter.
    """

    def __init__(self, max_faces: int = 3, coast_frames: int = 4):
        self.max_faces = max_faces
        self.coast_frames = coast_frames
        self._detector = FaceTracker()   # reuses detection backends
        self.tracks: Dict[int, Dict[str, Any]] = {}
        self._next_id = 0

    def _detect_all(self, img_bgr: np.ndarray) -> list:
        boxes = self._detector._detect_dnn(img_bgr)
        if not boxes:
            boxes = self._detector._detect_mediapipe(img_bgr)
        # Rank by area descending, cap at max_faces
        boxes.sort(key=lambda b: (b[2] - b[0]) * (b[3] - b[1]), reverse=True)
        return boxes[: self.max_faces]

    def update(self, img_bgr: np.ndarray) -> list:
        """
        Advance tracker one frame.
        Returns list of {"track_id", "bbox"} sorted by area (primary first).
        """
        detections = self._detect_all(img_bgr)

        # Greedy IoU matching: best overlap wins per detection
        unmatched_tracks = set(self.tracks.keys())
        assignments: Dict[int, int] = {}  # track_id -> det index
        for d_idx, det in enumerate(detections):
            best_iou, best_t = 0.30, None   # min association threshold 0.3
            for t_id in unmatched_tracks:
                iou = FaceTracker.calculate_iou(self.tracks[t_id]["bbox"], det)
                if iou > best_iou:
                    best_iou, best_t = iou, t_id
            if best_t is not None:
                assignments[best_t] = d_idx
                unmatched_tracks.discard(best_t)

        # Update matched tracks with EMA smoothing
        for t_id, d_idx in assignments.items():
            tr = self.tracks[t_id]
            a = ForensicConfig.FACE_EMA_ALPHA
            tr["bbox"] = tuple(
                int(round(a * n + (1 - a) * o))
                for n, o in zip(detections[d_idx], tr["bbox"])
            )
            tr["missed"] = 0

        # Age out unmatched tracks
        for t_id in list(unmatched_tracks):
            self.tracks[t_id]["missed"] += 1
            if self.tracks[t_id]["missed"] > self.coast_frames:
                del self.tracks[t_id]

        # Spawn new tracks for unmatched detections (capacity permitting)
        assigned_dets = set(assignments.values())
        for d_idx, det in enumerate(detections):
            if d_idx in assigned_dets:
                continue
            if len(self.tracks) >= self.max_faces:
                break
            tid = self._next_id
            self._next_id += 1
            self.tracks[tid] = {"bbox": det, "missed": 0}

        out = [
            {"track_id": tid, "bbox": tr["bbox"]}
            for tid, tr in sorted(
                self.tracks.items(),
                key=lambda kv: (kv[1]["bbox"][2] - kv[1]["bbox"][0]) * (kv[1]["bbox"][3] - kv[1]["bbox"][1]),
                reverse=True,
            )
        ]
        return out

    def reset(self) -> None:
        self.tracks.clear()
        self._next_id = 0


def extract_eye_centers(landmarks, width: int, height: int) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Return sub-pixel left/right eye centres in pixel coords."""
    try:
        n_lm = len(landmarks)
        if n_lm > LM_RIGHT_IRIS:
            l = landmarks[LM_LEFT_IRIS]
            r = landmarks[LM_RIGHT_IRIS]
        elif n_lm > LM_RIGHT_EYE_OUTER:
            l = landmarks[LM_LEFT_EYE_OUTER]
            r = landmarks[LM_RIGHT_EYE_OUTER]
        else:
            return None
        left = np.array([l.x * width, l.y * height], dtype=np.float32)
        right = np.array([r.x * width, r.y * height], dtype=np.float32)
        return left, right
    except Exception:
        return None


def compute_mar(landmarks) -> Optional[float]:
    """Mouth Aspect Ratio: vertical gap / horizontal width of inner lips."""
    try:
        top = np.array([landmarks[LM_TOP_LIP_INNER].x, landmarks[LM_TOP_LIP_INNER].y])
        bottom = np.array([landmarks[LM_BOTTOM_LIP_INNER].x, landmarks[LM_BOTTOM_LIP_INNER].y])
        left = np.array([landmarks[LM_LEFT_LIP_CORNER].x, landmarks[LM_LEFT_LIP_CORNER].y])
        right = np.array([landmarks[LM_RIGHT_LIP_CORNER].x, landmarks[LM_RIGHT_LIP_CORNER].y])
        return float(np.linalg.norm(top - bottom) / (np.linalg.norm(left - right) + 1e-6))
    except Exception:
        return None


def landmarks_to_array(landmarks) -> np.ndarray:
    """Convert mediapipe landmark list into an (N, 2) float array."""
    return np.array([[p.x, p.y] for p in landmarks], dtype=np.float32)


def preprocess_face_for_model(
    img_bgr: np.ndarray,
    bbox: Optional[Tuple[int, int, int, int]] = None,
    padding_ratio: float = None,
    landmarks=None,
) -> Optional[Image.Image]:
    """
    Produce the canonical RGB face crop fed to visual classifiers.

    If landmarks are supplied, performs eye-line roll correction (uprighting),
    which removes head-roll variance and significantly stabilizes ViT scores
    frame-to-frame. Falls back to a plain padded square crop otherwise.
    """
    (h, w) = img_bgr.shape[:2]
    padding_ratio = padding_ratio or ForensicConfig.FACE_CROP_PADDING
    out_size = ForensicConfig.MODEL_INPUT_SIZE

    if bbox is None:
        return None
    (startX, startY, endX, endY) = bbox

    box_w = endX - startX
    box_h = endY - startY
    if box_w <= 4 or box_h <= 4:
        return None
    center_x = (startX + endX) / 2.0
    center_y = (startY + endY) / 2.0
    crop_size = max(box_w, box_h) * padding_ratio

    eyes = extract_eye_centers(landmarks, w, h) if landmarks is not None else None

    if eyes is not None:
        left, right = eyes
        dx = float(right[0] - left[0])
        dy = float(right[1] - left[1])
        angle = math.degrees(math.atan2(dy, dx))

        # Rotate so the eye line is horizontal, centred on face-box centre
        M = cv2.getRotationMatrix2D((center_x, center_y), angle, 1.0)
        rotated = cv2.warpAffine(img_bgr, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

        half = crop_size / 2.0
        p_startX = int(max(0, center_x - half))
        p_startY = int(max(0, center_y - half))
        p_endX = int(min(w, center_x + half))
        p_endY = int(min(h, center_y + half))
        face_crop = rotated[p_startY:p_endY, p_startX:p_endX]
    else:
        half = crop_size / 2.0
        p_startX = int(max(0, center_x - half))
        p_startY = int(max(0, center_y - half))
        p_endX = int(min(w, center_x + half))
        p_endY = int(min(h, center_y + half))
        face_crop = img_bgr[p_startY:p_endY, p_startX:p_endX]

    if face_crop.size == 0:
        return None

    face_rgb = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(face_rgb).resize((out_size, out_size), Image.LANCZOS)
    return pil
