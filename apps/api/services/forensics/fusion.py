"""
Bayesian evidentiary fusion.

Each forensic signal is converted to log-odds space, scaled by a per-signal
prior strength and reliability weight, then summed — the textbook
independent-evidence Naive-Bayes combination. Signals with insufficient
evidence are excluded and remaining weights renormalized, so a silent video
never silently drags the verdict toward "authentic" (a critical flaw of
naive averaging).

The result includes a full per-signal contribution breakdown so every
verdict is explainable down to individual log-odds contributions.
"""
import math
from typing import Dict, Any, Optional

from core.config import ForensicConfig


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _logit(p: float) -> float:
    p = _clamp01(p)
    p = max(1e-4, min(1.0 - 1e-4, p))
    return math.log(p / (1.0 - p))


def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


class EvidenceFusionEngine:

    @staticmethod
    def fuse(
        signals: Dict[str, Optional[float]],
        visual_model_disagreement: float = 0.0,
        visual_confidence: float = 0.8,
    ) -> Dict[str, Any]:
        """
        Fuse independent forensic signals into a calibrated probability that
        the media is manipulated.

        signals : mapping of signal name -> anomaly score in [0,1], or None
                  if evidence was unavailable (excluded + renormalized).
        """
        cfg = ForensicConfig
        weights = cfg.normalized_fusion_weights()

        normalized: Dict[str, Dict[str, Any]] = {}
        for key in cfg.FUSION_WEIGHTS.keys():
            raw = signals.get(key)
            available = raw is not None and isinstance(raw, (int, float))
            normalized[key] = {
                "score": _clamp01(float(raw)) if available else 0.0,
                "available": available,
                "weight": weights.get(key, 0.05),
                "prior": cfg.SIGNAL_PRIOR_ODDS.get(key, 1.0),
            }

        # Reliability multipliers
        disagreement = _clamp01(float(visual_model_disagreement))
        confidence = _clamp01(float(visual_confidence))
        reliability_map: Dict[str, float] = {k: 1.0 for k in normalized}
        reliability_map["visual"] = (1.0 - 0.5 * disagreement) * (0.55 + 0.45 * confidence)

        # Renormalize weights over available signals only
        available_keys = [k for k, s in normalized.items() if s["available"]]
        if not available_keys:
            available_keys = ["visual"]
        w_total = sum(normalized[k]["weight"] for k in available_keys) or 1.0

        # ── Log-odds accumulation ────────────────────────────────────
        log_odds = 0.0
        contributions: Dict[str, float] = {}

        for key in available_keys:
            s = normalized[key]
            w = (s["weight"] / w_total)
            rel = reliability_map.get(key, 1.0)

            z = _logit(s["score"])
            contribution = w * rel * s["prior"] * z
            log_odds += contribution
            contributions[key] = round(contribution, 4)

        final_prob = _sigmoid(log_odds)

        # ── Consensus counting ───────────────────────────────────────
        elevated_signals = sum(
            1 for k, t in cfg.ELEVATED_THRESHOLDS.items()
            if normalized.get(k, {}).get("available") and normalized[k]["score"] > t
        )
        n_thresholds = len(cfg.ELEVATED_THRESHOLDS) or 7
        signal_consensus = elevated_signals / float(n_thresholds)

        # Confidence in the assessment itself
        n_avail = len(available_keys)
        base_confidence = 0.30 + 0.095 * n_avail
        base_confidence *= (1.0 - 0.35 * disagreement)
        if not normalized["visual"]["available"]:
            base_confidence *= 0.6
        assessment_confidence = _clamp01(base_confidence)

        # ── Classification ───────────────────────────────────────────
        if final_prob >= cfg.T_MANIPULATED:
            classification = "LIKELY MANIPULATED"
            evidence_quality = "HIGH" if assessment_confidence > 0.7 else "MODERATE"
        elif final_prob >= cfg.T_SUSPICIOUS:
            classification = "SUSPICIOUS"
            evidence_quality = "MODERATE"
        else:
            classification = "LIKELY AUTHENTIC"
            evidence_quality = (
                "HIGH" if assessment_confidence > 0.7 and elevated_signals == 0 else "MODERATE"
            )

        if assessment_confidence < 0.42 and final_prob < cfg.T_MANIPULATED:
            classification = "INCONCLUSIVE"
            evidence_quality = "LOW"

        return {
            "final_score": round(final_prob, 4),
            "final_log_odds": round(log_odds, 4),
            "classification": classification,
            "confidence": round(assessment_confidence, 3),
            "evidence_quality": evidence_quality,
            "signal_consensus": round(signal_consensus, 3),
            "elevated_signals": elevated_signals,
            "contributions": contributions,
            "visual_reliability": round(reliability_map["visual"], 3),
        }

    # ------------------------------------------------------------------
    @staticmethod
    def detect_suspicious_segments(frame_events: list, fps: float) -> list:
        """Group consecutive above-threshold visual events into segments."""
        segments = []
        current_segment = None

        for event in sorted(frame_events, key=lambda e: e.get("timestamp") or 0.0):
            ts = event.get("timestamp", 0.0) or 0.0
            score = event.get("score_or_null") or event.get("score") or 0.0

            if score > 0.55:
                if current_segment is None:
                    current_segment = {
                        "start_time": ts,
                        "end_time": ts,
                        "visual_score": score,
                        "severity": "high" if score > 0.75 else "medium",
                        "frame_count": 1,
                    }
                else:
                    current_segment["end_time"] = ts
                    current_segment["visual_score"] = max(current_segment["visual_score"], score)
                    current_segment["frame_count"] += 1
                    if score > 0.75:
                        current_segment["severity"] = "high"
            else:
                if current_segment is not None:
                    if current_segment["frame_count"] >= 2:
                        segments.append(current_segment)
                    current_segment = None

        if current_segment is not None and current_segment["frame_count"] >= 2:
            segments.append(current_segment)

        return segments
