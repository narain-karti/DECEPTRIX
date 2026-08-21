import cv2
import numpy as np
from scipy.fft import dctn
from typing import Dict

class FrequencyForensicsEngine:
    @staticmethod
    def compute_frequency_features(face_crop_gray: np.ndarray) -> Dict[str, float]:
        """
        Detect GAN/Manipulation artifacts in frequency domain via DCT.
        Calculates low, mid, and high frequency energies.
        Returns multiple features rather than a single heuristic.
        """
        try:
            resized = cv2.resize(face_crop_gray, (128, 128))
            dct = dctn(resized.astype(np.float32), norm='ortho')
            h, w = dct.shape
            
            # Split into bands
            low_freq = np.mean(np.abs(dct[0:h//4, 0:w//4]))
            mid_freq = np.mean(np.abs(dct[h//4:h//2, w//4:w//2]))
            high_freq_energy = np.mean(np.abs(dct[h // 2:, w // 2:]))
            
            total_energy = np.mean(np.abs(dct)) + 1e-6
            
            high_ratio = high_freq_energy / total_energy
            
            # Real faces: ratio ~0.1-0.2; GAN faces: ratio often >0.3
            freq_anomaly_score = min(1.0, max(0.0, (high_ratio - 0.1) / 0.3))
            
            return {
                "freq_score": float(freq_anomaly_score),
                "low_energy": float(low_freq),
                "mid_energy": float(mid_freq),
                "high_energy": float(high_freq_energy),
                "high_ratio": float(high_ratio)
            }
        except Exception:
            return {
                "freq_score": 0.0,
                "low_energy": 0.0,
                "mid_energy": 0.0,
                "high_energy": 0.0,
                "high_ratio": 0.0
            }
