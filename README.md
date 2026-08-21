# ⚡ DECEPTRIX — Explainable Multi-Modal AI Forensic Intelligence Platform

> **Smart India Hackathon 2026 (SIH) | Problem Category: AI Forensics & Information Integrity**  
> *"Evidence Before Conclusions"* — Next-generation multi-modal deepfake detection and claim verification engine producing court-admissible forensic intelligence dossiers.

---

## 🎯 Executive Overview

**DECEPTRIX** is an enterprise-grade AI forensic intelligence platform designed for law enforcement, investigative journalism, content moderation platforms, and cybersecurity laboratories. Unlike black-box detectors that return arbitrary real/fake percentages, DECEPTRIX performs **dense multi-modal forensic decomposition** across 5 independent neural and statistical signal layers, combined via **Bayesian Evidentiary Fusion**, and generates **cryptographically attestation-sealed 5-page forensic dossiers**.

---

## 🔬 5-Signal Multi-Modal Bayesian Ensemble Architecture

```
                                  [ RAW MEDIA INTAKE ]
                                            │
                                ┌───────────┴───────────┐
                                │   SHA-256 Fingerprint │
                                └───────────┬───────────┘
                                            ▼
                    [ FFmpeg Dense 15 FPS Demux & 16 kHz PCM Audio ]
                                            │
         ┌──────────────────┬───────────────┼───────────────┬──────────────────┐
         ▼                  ▼               ▼               ▼                  ▼
┌──────────────────┐┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────────┐
│ ViT Classifier   ││ Lip-Sync     ││ 468-pt Mesh  ││ 2D-DCT Sub-  ││ FFprobe Container│
│ (dima806 Patch16)││ MAR vs. RMS  ││ Face Jitter  ││ Pixel FFT    ││ & Stream Metadata│
│ Weight: 35%      ││ Weight: 25%  ││ Weight: 15%  ││ Weight: 15%  ││ Weight: 10%      │
└────────┬─────────┘└──────┬───────┘└──────┬───────┘└──────┬───────┘└────────┬─────────┘
         │                 │               │               │                 │
         └─────────────────┴───────┬───────┴───────────────┴─────────────────┘
                                   ▼
                   [ BAYESIAN EVIDENTIARY FUSION ]
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
   [ Interactive Web Studio ]               [ 5-Page Forensic Dossier ]
  • Live Extracted Face HUD                 • Executive Threat Panel
  • Audio-Visual Oscilloscope               • Signal Consensus Radar
  • 2D-DCT Spectral Scope                   • Biometric Keyframe Cards
  • Lightbox Face Inspector                 • Cryptographic Attestation
```

### Forensic Signal Layer Specifications:
1. **Vision Transformer (ViT-Patch16):** Patch-level self-attention texture classifier (`dima806/deepfake_vs_real_image_detection`) detecting generative neural network skin synthesis and boundary artifacts.
2. **Audio-Visual Lip Synchrony Correlation:** Cross-modal Pearson correlation measuring Mouth Aspect Ratio (MAR) against acoustic Root Mean Square (RMS) energy envelopes.
3. **MediaPipe 468-Point FaceMesh Landmark Jitter:** Measures inter-frame spatial variance and biometric coordinate dispersion across consecutive video frames.
4. **2D-DCT Spectral Frequency Analysis:** Computes discrete cosine transform high-frequency energy falloff to expose GAN frequency residuals.
5. **FFprobe Container & Stream Telemetry:** Inspects codec profiles, frame rates, audio sample rates, and creation metadata headers.

---

## ✨ Key Features

* **Real-Time Extracted Keyframes Sliding Stream:** Live continuous horizontal face extraction ticker with neon laser scanlines and cyber reticles during background processing.
* **Bayesian Evidentiary Fusion:** Prevents dilution of high-confidence visual findings ($99.8\%$ deepfake signals accurately produce $1.00$ Critical Risk ratings).
* **5-Page AI Forensic Intelligence Dossier (ReportLab):**
  * **Page 1 — Executive Summary:** Threat classification, composite risk meter, case snapshot, and primary evidentiary drivers.
  * **Page 2 — Forensic Signal Consensus:** Analytical signal cards with progress bars and Bayesian fusion architecture.
  * **Page 3 — Evidence Integrity & Telemetry:** 6-stage chain-of-custody timeline, full SHA-256 fingerprint, and container telemetry grid.
  * **Page 4 — Visual Evidence & Biometrics:** High-resolution face crop cards with bounding boxes, anomaly metrics, and temporal progression filmstrip.
  * **Page 5 — Forensic Conclusion & Attestation:** Primary findings, supporting evidence, scientific limitations, and HMAC-SHA256 attestation seal.
* **Rumour & Text Fact-Checking Pipeline:** Atomic claim decomposition, Tavily search connector with multi-tier source credibility classification (Tier 1 Gov/Fact-Check, Tier 2 News, Tier 3 Web).

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend UI** | Next.js 16 (App Router), TypeScript, Vanilla CSS Design System, Lucide Icons |
| **Backend API** | FastAPI, Python 3.10+, SQLAlchemy (SQLite/PostgreSQL), Celery |
| **AI & Forensics** | PyTorch, HuggingFace Transformers (ViT), MediaPipe, Librosa, OpenCV DNN, Scipy (DCT) |
| **Document Generation** | ReportLab 4.x (TrueType Font Embedding: IBM Plex Sans & IBM Plex Mono) |
| **Container & Stream** | FFmpeg, FFprobe |

---

## 🚀 Quickstart Guide

### Prerequisites
* Python 3.10+
* Node.js 18+ & npm
* FFmpeg & FFprobe installed and available in `PATH`

### 1. Backend Setup
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start API Server (Runs in zero-dependency eager mode locally)
CELERY_TASK_ALWAYS_EAGER=true uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
* API Health Check: `http://127.0.0.1:8000/health`
* Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
cd apps/web
npm install
npm run dev
```
* Web Studio: `http://localhost:3000`
* Media Audit Studio: `http://localhost:3000/media`
* Rumour Fact-Checker: `http://localhost:3000/rumour`

---

## 📁 Repository Structure

```
DECEPTRIX/
├── apps/
│   ├── api/
│   │   ├── api/
│   │   │   ├── routes_media.py     # Media upload and polling endpoints
│   │   │   ├── routes_text.py      # Rumour text fact-checking endpoints
│   │   │   └── routes_reports.py   # ReportLab 5-page forensic dossier generator
│   │   ├── core/
│   │   │   ├── config.py           # Application settings
│   │   │   ├── database.py         # SQLAlchemy engine & session
│   │   │   └── celery_app.py       # Celery task queue configuration
│   │   ├── fonts/                  # TrueType IBM Plex Sans & Mono fonts
│   │   ├── models/                 # ORM models and OpenCV DNN weights
│   │   ├── schemas/                # Pydantic data schemas
│   │   ├── services/
│   │   │   ├── media_worker.py     # 5-Signal ensemble video forensic worker
│   │   │   └── text_worker.py      # Multi-tier claim verification worker
│   │   └── main.py                 # FastAPI application root
│   └── web/
│       ├── src/
│       │   ├── app/                # Next.js App Router pages (/, /media, /rumour)
│       │   ├── components/         # MediaAudit, RumourAudit, AppShell, EvidenceCards
│       │   └── styles/             # globals.css (Dark mode design tokens)
│       └── package.json
└── README.md
```

---

## ⚖️ Forensic Scope & Disclaimers

DECEPTRIX is built on the principle of **explainable diagnostics**. Algorithmic assessments represent mathematical and neural evidence evaluations derived from specified model architectures and do not replace legal chain-of-custody protocols.

---

## 👥 Contributors & SIH 2026 Team

Developed with precision for **Smart India Hackathon 2026**.  
*Repository:* [https://github.com/narain-karti/DECEPTRIX](https://github.com/narain-karti/DECEPTRIX)
