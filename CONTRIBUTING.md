# Contributing to DECEPTRIX

Thank you for your interest in contributing to **DECEPTRIX** — the Explainable Multi-Modal AI Forensic Intelligence Platform.

## 🛠️ Development Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/narain-karti/DECEPTRIX.git
   cd DECEPTRIX
   ```

2. **Backend Setup:**
   ```bash
   cd apps/api
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   CELERY_TASK_ALWAYS_EAGER=true uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. **Frontend Setup:**
   ```bash
   cd apps/web
   npm install
   cp .env.example .env.local
   npm run dev
   ```

## 📐 Forensic Standards

- **Explainability First:** All diagnostic models must emit verifiable artifact references (bounding boxes, timestamps, intermediate scores) rather than uncalibrated scalar outputs.
- **Bayesian Multi-Modal Ensemble:** Any new signal extractor must define its Bayesian fusion weight and cross-correlation boundaries.
- **Deterministic Attestation:** Document generation layers must maintain strict SHA-256 fingerprinting for chain-of-custody compliance.

## 🚀 Submitting Pull Requests

1. Fork the repo and create your feature branch: `git checkout -b feature/my-enhancement`
2. Run test suites and verify TypeScript builds: `npm run build`
3. Commit with semantic commit messages: `feat: ...`, `fix: ...`, `docs: ...`
4. Open a Pull Request on GitHub with a clear description and testing evidence.
