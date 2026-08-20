# 🎬 DECEPTRIX Media Pipeline Updates

This document summarizes the recent updates and improvements made to the DECEPTRIX deepfake detection pipeline and UI.

## 1. Real Face Detection & Dynamic UI Terminal
**The Problem:**
- The UI indicators for "Analyzing Sequence..." were hardcoded loops that felt static.
- The output PDF lacked original identifications, and the `0.50` deepfake score was a static placeholder threshold because the visual pipeline wasn't properly correlating audio and mouth movements.

**The Solution:**
- **Dynamic Terminal Logs**: We replaced the static `[sys] init workers pool` CSS loop in `MediaAudit.tsx` with a dynamic state that maps precisely to the real backend progress of Celery! It now outputs real-time metrics (e.g. `[task] Extracting video frames and audio...`).
- **MediaPipe Facial Landmark Mapping**: Instead of using the generic VideoMAE model, the pipeline now extracts the face dynamically. This allows the backend to crop the **actual faces** from the video and save them. 
- **PDF Face Embeddings**: These newly extracted face crops are now seamlessly passed into `routes_reports.py`, so the final PDF accurately embeds the original faces identified in the video instead of mock data!

## 2. Multi-Modal Lip Sync & Deepfake Scoring
**The Problem:**
- Real videos were returning false positive scores because the deepfake threshold fallback was `0.50` for general Audio Classification (since the current audio model was intended for keyword spotting, not deepfake spoofing).

**The Solution:**
- **Audio-Visual Pearson Correlation (Lip Sync)**: I implemented a new multi-modal check in `media_worker.py`! The pipeline now measures the `Mouth Aspect Ratio (MAR)` using `MediaPipe FaceMesh` and correlates it with the `Audio Energy (RMS)` using `librosa`. 
- If the audio does not match the lip movements (low correlation), the deepfake score increases.
- **Facial Jitter Detection**: Analyzes eye distance variance across frames to detect common deepfake flickering and blending artifacts.
- The `0.50` static threshold was removed, giving a much more accurate scale that will reduce false positives for real videos!

## 3. Infrastructure Stability
- The `mediapipe`, `librosa`, and `scipy` dependencies were successfully installed in the backend.
- The `opencv-contrib-python` dependency was correctly pegged to `<5.x` to maintain support for legacy `cv2.dnn.readNetFromCaffe` loaders used in the inference pipeline.
- The FPDF library calls were patched to be fully compatible with both `fpdf` and `fpdf2` standard engines, preventing IDE errors and ensuring crash-free PDF generation.
