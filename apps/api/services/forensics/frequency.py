"""
Spectral (2D-DCT) forensics.

GAN/diffusion generators leave statistically distinct traces in the
frequency domain: abnormal high-frequency energy ratios, altered spectral
slope, and periodic block artifacts from latent upsampling. This engine
extracts several complementary spectral descriptors from the face crop and
fuses them into a calibrated anomaly score.
"""
import cv2
import numpy as np
from scipy.fft import dctn
from typing import Dict

from core.config import ForensicConfig


class FrequencyForensicsEngine:

    @staticmethod
    def compute_frequency_features(face_crop_gray: np.ndarray) -> Dict[str, float]:
        try:
            size = ForensicConfig.DCT_SIZE
            img = cv2.resize(face_crop_gray, (size, size), interpolation=cv2.INTER_AREA)
            img = img.astype(np.float32)

            # Remove DC/low-frequency lighting bias to isolate texture spectrum
            img = img - img.mean()

            dct = dctn(img, norm="ortho")
            mag = np.abs(dct)
            total_energy = float(mag.mean()) + 1e-9

            # ── 1. High-frequency energy ratio (quadrant) ────────────────
            h, w = mag.shape
            high_freq_energy = float(mag[h // 2:, w // 2:].mean())
            high_ratio = high_freq_energy / total_energy

            # ── 2. Radially averaged power profile & spectral slope ──────
            yy, xx = np.mgrid[0:size, 0:size]
            radius = np.sqrt((yy - size // 2) ** 2 + (xx - size // 2) ** 2).astype(int)
            max_r = size // 2
            radial = np.bincount(radius.ravel(), weights=mag.ravel(), minlength=max_r + 1)
            counts = np.bincount(radius.ravel(), minlength=max_r + 1)
            radial_profile = radial / np.maximum(counts, 1)

            # Log-log slope over mid/high band: natural images fall off ~ -2;
            # GAN textures are typically flatter or noisier.
            r_lo, r_hi = int(max_r * 0.25), int(max_r * 0.95)
            x = np.log(np.arange(r_lo, r_hi) + 1.0)
            y = np.log(radial_profile[r_lo:r_hi] + 1e-9)
            if len(x) > 4 and np.std(x) > 0:
                slope = float(np.polyfit(x, y, 1)[0])
            else:
                slope = -2.0

            # ── 3. Spectral entropy of radial distribution ───────────────
            p = radial_profile / (radial_profile.sum() + 1e-9)
            entropy = float(-np.sum(p[p > 0] * np.log(p[p > 0])))
            max_entropy = float(np.log(max_r + 1))

            # ── 4. Block artifact periodicity (8x8 JPEG-like grid) ───────
            # Energy at DCT bins that are multiples of size/8 indicates
            # resampling / double-compression grid artifacts.
            block_axis = np.arange(size)
            grid_mask = ((block_axis % (size // 8)) == 0)
            grid_energy = float(mag[np.ix_(grid_mask, grid_mask)].mean())
            grid_ratio = grid_energy / total_energy

            # ── Fuse descriptors into one anomaly score ──────────────────
            # Each sub-score is squashed into [0,1] around empirically chosen
            # operating points; final score is a weighted blend.
            s_ratio = _squash(high_ratio, 0.10, 0.30)          # more HF => suspicious
            s_slope = _squash(slope + 3.5, -1.5, 0.5)          # flatter slope => suspicious
            s_entropy = _squash(entropy / max_entropy, 0.72, 0.92)
            s_grid = _squash(grid_ratio, 1.6, 4.0)             # strong grid peaks => suspicious

            freq_score = float(
                0.40 * s_ratio + 0.25 * s_slope + 0.20 * s_entropy + 0.15 * s_grid
            )

            return {
                "freq_score": freq_score,
                "high_ratio": float(high_ratio),
                "spectral_slope": slope,
                "spectral_entropy": entropy / max_entropy,
                "block_grid_ratio": float(grid_ratio),
                "low_energy": float(mag[:h // 4, :w // 4].mean()),
                "mid_energy": float(mag[h // 4:h // 2, w // 4:w // 2].mean()),
                "high_energy": high_freq_energy,
            }
        except Exception:
            return {
                "freq_score": 0.0,
                "high_ratio": 0.0,
                "spectral_slope": -2.0,
                "spectral_entropy": 0.0,
                "block_grid_ratio": 0.0,
                "low_energy": 0.0,
                "mid_energy": 0.0,
                "high_energy": 0.0,
            }


def _squash(value: float, lo: float, hi: float) -> float:
    """Linear map with clamping: value<=lo -> 0, >=hi -> 1."""
    if hi <= lo:
        return 0.0
    return float(min(1.0, max(0.0, (value - lo) / (hi - lo))))
