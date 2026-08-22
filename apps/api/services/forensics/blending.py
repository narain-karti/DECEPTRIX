"""
Blending-boundary forensics (Face-X-ray inspired).

Face swaps are composited: a generated inner face is pasted onto the
original head, then color-matched and feathered. Even when the swapped
interior fools texture classifiers, the SEAM between the generated region
and the original skin carries statistical discontinuities:

  - Color/brightness offset between inner ellipse and outer ring
  - Gradient-energy discontinuity at the boundary
  - Sharpness mismatch (GAN output is over-smooth vs camera noise)
  - High-pass residual (noise) statistics difference

This engine measures those seam descriptors directly on the full frame,
making it generator-agnostic — exactly the property that generalizes to
unseen deepfake architectures.
"""
import cv2
import numpy as np
from typing import Dict, Any, Tuple


class BlendingAnalyzer:

    @staticmethod
    def analyze(img_bgr: np.ndarray, bbox: Tuple[int, int, int, int]) -> Dict[str, Any]:
        """
        img_bgr : full frame (context around the face matters!)
        bbox    : face box (startX, startY, endX, endY)
        """
        try:
            fh, fw = img_bgr.shape[:2]
            sx, sy, ex, ey = bbox
            cx, cy = (sx + ex) / 2.0, (sy + ey) / 2.0
            ax = max((ex - sx) / 2.0, 4)
            ay = max((ey - sy) / 2.0, 4)

            # Inner ellipse mask (core face interior)
            inner = _ellipse_mask(fw, fh, cx, cy, ax * 0.62, ay * 0.62)
            # Outer ring mask (surrounding band just past the jaw/hairline)
            ring = _ellipse_mask(fw, fh, cx, cy, ax * 1.05, ay * 1.10) & ~_ellipse_mask(
                fw, fh, cx, cy, ax * 0.80, ay * 0.85
            )

            if inner.sum() < 400 or ring.sum() < 400:
                return {"blending_score": 0.0, "status": "INSUFFICIENT_EVIDENCE",
                        "message": "Face too small for seam analysis."}

            lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)

            # ── 1. Color offset across the seam (L channel dominant) ────
            l_inner_mean = lab[..., 0][inner].mean()
            l_ring_mean = lab[..., 0][ring].mean()
            l_delta = abs(l_inner_mean - l_ring_mean)

            a_delta = abs(lab[..., 1][inner].mean() - lab[..., 1][ring].mean())
            b_delta = abs(lab[..., 2][inner].mean() - lab[..., 2][ring].mean())
            color_delta = float(l_delta * 1.0 + a_delta * 0.5 + b_delta * 0.5)

            # Normalize by overall scene contrast so dark scenes don't inflate
            l_scene_std = lab[..., 0].std() + 1e-6
            color_rel = color_delta / max(l_scene_std, 8.0)

            # ── 2. Gradient energy discontinuity ────────────────────────
            gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            grad_mag = np.sqrt(gx ** 2 + gy ** 2)

            g_inner = float(grad_mag[inner].mean())
            g_ring = float(grad_mag[ring].mean())
            grad_ratio = max(g_inner, g_ring) / (min(g_inner, g_ring) + 1e-3)

            # ── 3. Sharpness mismatch (Laplacian variance ratio) ────────
            lap = cv2.Laplacian(gray, cv2.CV_32F)
            sharp_in = float(np.var(lap[inner]))
            sharp_ring = float(np.var(lap[ring]))
            sharp_ratio = max(sharp_in, sharp_ring) / (min(sharp_in, sharp_ring) + 1e-2)

            # ── 4. Noise residual difference (denoised interior tell) ───
            hp = gray - cv2.GaussianBlur(gray, (0, 0), 2.0)
            noise_in = float(hp[inner].std())
            noise_ring = float(hp[ring].std())
            noise_ratio = max(noise_in, noise_ring) / (min(noise_in, noise_ring) + 1e-4)

            score = float(
                0.30 * _squash(color_rel, 0.06, 0.45) +
                0.25 * _squash(grad_ratio, 1.25, 2.60) +
                0.25 * _squash(sharp_ratio, 1.40, 3.50) +
                0.20 * _squash(noise_ratio, 1.35, 3.00)
            )

            return {
                "blending_score": round(score, 4),
                "status": "COMPLETED",
                "features": {
                    "color_delta_rel": round(float(color_rel), 4),
                    "gradient_ratio": round(grad_ratio, 4),
                    "sharpness_ratio": round(sharp_ratio, 4),
                    "noise_ratio": round(noise_ratio, 4),
                },
                "message": "Seam statistics measured across face-boundary ellipse.",
            }
        except Exception as e:
            return {"blending_score": 0.0, "status": "INSUFFICIENT_EVIDENCE",
                    "message": f"Blending analysis failed: {e}"}


def _ellipse_mask(w: int, h: int, cx: float, cy: float, ax: float, ay: float) -> np.ndarray:
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(mask, (int(cx), int(cy)), (int(ax), int(ay)), 0, 0, 360, 1, -1)
    return mask.astype(bool)


def _squash(v: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return float(min(1.0, max(0.0, (v - lo) / (hi - lo))))
