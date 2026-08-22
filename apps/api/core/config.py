import os
from typing import Dict, List
from pydantic_settings import BaseSettings


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class Settings(BaseSettings):
    PROJECT_NAME: str = "DECEPTRIX API"
    API_V1_STR: str = "/api/v1"

    # SQLite local DB
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./deceptrix.db"

    # Local Storage for MVP
    STORAGE_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage")

    # CORS origins (comma separated env override supported)
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000", "http://localhost:3001",
        "http://127.0.0.1:3000", "http://127.0.0.1:3001",
    ]

    # Attestation secret for HMAC report seals (set in production!)
    ATTESTATION_SECRET: str = os.environ.get("ATTESTATION_SECRET", "deceptrix-dev-secret-change-me")


settings = Settings()

if os.environ.get("CORS_ORIGINS"):
    settings.CORS_ORIGINS = [o.strip() for o in os.environ["CORS_ORIGINS"].split(",") if o.strip()]

# Ensure storage directory exists
os.makedirs(settings.STORAGE_DIR, exist_ok=True)


class ForensicConfig:
    """
    Centralized forensic tuning. Every weight/threshold used across the
    detection pipeline lives here so results are reproducible and auditable.
    All values can be overridden via environment variables.
    """

    # ── Sampling ────────────────────────────────────────────────
    ANALYSIS_FPS: int = _env_int("ANALYSIS_FPS", 15)
    MAX_FRAMES: int = _env_int("MAX_FRAMES", 900)          # cap very long videos
    MIN_CHUNK_SIZE: int = _env_int("MIN_CHUNK_SIZE", 4)     # frames per temporal window

    # ── Visual detector ensemble ────────────────────────────────
    DIMA_WEIGHT: float = _env_float("DIMA_WEIGHT", 0.5)
    PRITHIV_WEIGHT: float = _env_float("PRITHIV_WEIGHT", 0.5)
    USE_TTA: bool = os.environ.get("USE_TTA", "true").lower() == "true"

    # ── Fusion weights (log-odds space) — renormalized automatically ──
    FUSION_WEIGHTS: Dict[str, float] = {
        "visual":      _env_float("FUSION_W_VISUAL", 0.30),
        "blending":    _env_float("FUSION_W_BLENDING", 0.16),
        "lip_sync":    _env_float("FUSION_W_LIPSYNC", 0.15),
        "temporal":    _env_float("FUSION_W_TEMPORAL", 0.13),
        "frequency":   _env_float("FUSION_W_FREQUENCY", 0.11),
        "audio_spoof": _env_float("FUSION_W_AUDIO_SPOOF", 0.10),
        "metadata":    _env_float("FUSION_W_METADATA", 0.05),
    }

    # Per-signal prior odds that the signal alone implies manipulation.
    # A score of 0.5 is neutral (log-odds 0). These scale each signal's
    # contribution in log-odds space before weighting.
    SIGNAL_PRIOR_ODDS: Dict[str, float] = {
        "visual":      _env_float("PRIOR_VISUAL", 2.0),
        "blending":    _env_float("PRIOR_BLENDING", 1.6),
        "lip_sync":    _env_float("PRIOR_LIPSYNC", 1.4),
        "temporal":    _env_float("PRIOR_TEMPORAL", 1.2),
        "frequency":   _env_float("PRIOR_FREQUENCY", 1.1),
        "audio_spoof": _env_float("PRIOR_AUDIO_SPOOF", 1.3),
        "metadata":    _env_float("PRIOR_METADATA", 0.7),
    }

    # Classification thresholds on fused probability
    T_MANIPULATED: float = _env_float("T_MANIPULATED", 0.62)
    T_SUSPICIOUS: float = _env_float("T_SUSPICIOUS", 0.45)
    # Below T_SUSPICIOUS => LIKELY AUTHENTIC

    # Per-signal "elevated" thresholds for consensus counting
    ELEVATED_THRESHOLDS: Dict[str, float] = {
        "visual":      0.55,
        "blending":    0.50,
        "lip_sync":    0.50,
        "temporal":    0.45,
        "frequency":   0.40,
        "audio_spoof": 0.50,
        "metadata":    0.30,
    }

    # ── Temporal jitter engine ──────────────────────────────────
    JITTER_WINDOW: int = _env_int("JITTER_WINDOW", 32)       # frames per window
    JITTER_SHOT_CUT: float = _env_float("JITTER_SHOT_CUT", 0.20)   # reject jumps above
    JITTER_NATURAL: float = _env_float("JITTER_NATURAL", 0.006)    # natural micro-motion floor
    JITTER_SYNTHETIC: float = _env_float("JITTER_SYNTHETIC", 0.028)  # synthetic warp ceiling
    # Frozen-face detection: real faces NEVER hold perfectly rigid geometry
    # (pulse-driven skin deformation + muscle tremor persist even in tripod
    # shots). A pasted static photo moved by affine zoom/pan shows ~zero
    # relative landmark motion after pose/scale normalization => puppet tell.
    JITTER_FROZEN_FLOOR: float = _env_float("JITTER_FROZEN_FLOOR", 0.0016)
    JITTER_FROZEN_SCORE: float = _env_float("JITTER_FROZEN_SCORE", 0.80)

    # ── Frequency engine ────────────────────────────────────────
    DCT_SIZE: int = _env_int("DCT_SIZE", 128)

    # ── Lip sync engine ─────────────────────────────────────────
    LIP_MAX_LAG_SEC: float = _env_float("LIP_MAX_LAG_SEC", 0.5)
    LIP_STRONG_CORR: float = _env_float("LIP_STRONG_CORR", 0.35)
    LIP_WEAK_CORR: float = _env_float("LIP_WEAK_CORR", 0.12)

    # ── Calibration ─────────────────────────────────────────────
    BLUR_FLOOR: float = _env_float("BLUR_FLOOR", 60.0)       # Laplacian var considered unusable
    BLUR_CEILING: float = _env_float("BLUR_CEILING", 400.0)  # Laplacian var considered sharp
    BLUR_MAX_SUPPRESSION: float = _env_float("BLUR_MAX_SUPPRESSION", 0.35)

    # ── Face pipeline ───────────────────────────────────────────
    FACE_DET_CONFIDENCE: float = _env_float("FACE_DET_CONFIDENCE", 0.5)
    FACE_CROP_PADDING: float = _env_float("FACE_CROP_PADDING", 1.30)
    FACE_EMA_ALPHA: float = _env_float("FACE_EMA_ALPHA", 0.6)   # bbox smoothing
    MODEL_INPUT_SIZE: int = 224

    @classmethod
    def normalized_fusion_weights(cls) -> Dict[str, float]:
        total = sum(cls.FUSION_WEIGHTS.values()) or 1.0
        return {k: v / total for k, v in cls.FUSION_WEIGHTS.items()}
