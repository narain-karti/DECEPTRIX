# 🎬 DECEPTRIX Media Pipeline Updates (SOTA AI Video Forensics Upgrade)

This document summarizes the massive recent upgrades and architecture refactoring that transitioned DECEPTRIX from a naive image-based deepfake classifier into a robust, multi-modal **SOTA AI Video Forensics Pipeline**. 

The system no longer analyzes isolated frames out of context. It uses a **Bayesian evidence fusion approach** across 5 independent signals to determine manipulation likelihood.

## 1. Refactored Engine Architecture
**The Problem:**
- The `media_worker.py` was highly monolithic, containing hundreds of lines of inline analysis for video logic, making it impossible to scale or track independent AI modules.

**The Solution:**
- **Decoupled Engines**: Broken down into a scalable architecture under `apps/api/services`:
  - `detectors/`: Abstract `VisualDeepfakeDetector` interface supporting implementations like `Dima806Detector`, `PrithivDeepFakeV2Detector`, and an `EnsembleVisualDetector`.
  - `forensics/temporal.py`: Extracted temporal jitter logic based on MediaPipe FaceMesh to measure structural inconsistencies.
  - `forensics/frequency.py`: Implemented a 2D-DCT (Discrete Cosine Transform) high-frequency analysis engine to detect GAN artifacts in the spectral domain.
  - `forensics/lip_sync.py`: Audio-Visual Synchronization engine computing the Pearson correlation between Mouth Aspect Ratio (MAR) and Librosa audio RMS energy.
  - `forensics/metadata.py`: Extracted FFprobe stream analysis into its own engine.
  - `forensics/fusion.py`: Created an `EvidenceFusionEngine` to perform Bayesian evidence fusion across all modalities.

## 2. ViT Deepfake Hallucination Mitigation (Laplacian Blur Penalty)
**The Problem:**
- Image-based classifiers (like `dima806` or `prithivMLmods`) are trained on pristine, static AI generated images. When running on standard video frames, they frequently hallucinate "synthetic artifacts" due to natural motion blur and H.264 compression, yielding extreme false positives for real videos.

**The Solution:**
- **Laplacian Variance Blur Detector**: Implemented inside `media_worker.py` and linked to a new `ModelCalibrator`. 
- When a frame is detected as blurry (variance < 100), the system actively penalizes and suppresses the ViT's "fake score", preventing 0.95 hallucinated scores from motion blur.
- Combined with the 5-Signal Bayesian Fusion, even if the visual classifier falsely flags an artifact, the temporal stability, lip-sync, and DCT frequencies will drag the score back to an authentic/inconclusive classification.

## 3. Upgraded Frontend Intelligence HUD & PDF Dossier
- Upgraded the Next.js `MediaAudit.tsx` component to parse and render the **5-Signal Ensemble Decomposition**.
- The `routes_reports.py` PDF generation logic dynamically scales to support the multi-modal signals and correctly reflects the final multi-modal consensus.
- Re-labeled "Primary ViT Detector" dynamically to "Primary Visual Detector", ensuring that local component cards correctly reflect their isolated scores, avoiding visual confusion with the global composite anomaly score.
