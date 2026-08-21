from typing import Dict, Any, List

class EvidenceFusionEngine:
    @staticmethod
    def fuse(
        visual_score: float,
        visual_model_disagreement: float,
        temporal_score: float,
        frequency_score: float,
        lip_sync_score: float,
        metadata_score: float
    ) -> Dict[str, Any]:
        """
        Fuses independent forensic signals into a final assessment.
        """
        # Determine base signal strength
        corroboration = (lip_sync_score * 0.30) + (temporal_score * 0.25) + (frequency_score * 0.20) + (metadata_score * 0.10)
        
        # Calculate final score
        final_score = (visual_score * 0.65) + (corroboration * 0.35)
        final_score = float(max(0.0, min(1.0, final_score)))
        
        # Determine confidence
        # High model disagreement lowers confidence
        confidence = 1.0 - (visual_model_disagreement * 0.4)
        
        elevated_signals = sum([
            1 if visual_score > 0.50 else 0,
            1 if lip_sync_score > 0.45 else 0,
            1 if temporal_score > 0.40 else 0,
            1 if frequency_score > 0.35 else 0,
        ])
        
        # Determine classification
        if confidence < 0.35:
            classification = "INCONCLUSIVE"
            evidence_quality = "LOW"
        elif final_score >= 0.70 and elevated_signals >= 2:
            classification = "LIKELY MANIPULATED"
            evidence_quality = "HIGH" if confidence > 0.7 else "MODERATE"
        elif final_score >= 0.55:
            classification = "SUSPICIOUS"
            evidence_quality = "MODERATE"
        elif final_score <= 0.45:
            classification = "LIKELY AUTHENTIC"
            evidence_quality = "HIGH" if confidence > 0.7 else "MODERATE"
        else:
            classification = "INCONCLUSIVE"
            evidence_quality = "MODERATE"
            
        signal_consensus = float(elevated_signals / 4.0)

        return {
            "final_score": final_score,
            "classification": classification,
            "confidence": float(confidence),
            "evidence_quality": evidence_quality,
            "signal_consensus": signal_consensus
        }

    @staticmethod
    def detect_suspicious_segments(frame_events: List[Dict[str, Any]], fps: float) -> List[Dict[str, Any]]:
        """
        Creates continuous suspicious segments from frame-level events.
        """
        segments = []
        current_segment = None
        
        for event in frame_events:
            # We assume events have a timestamp and score
            ts = event.get("timestamp", 0.0)
            score = event.get("score", 0.0)
            
            if score > 0.55:
                if current_segment is None:
                    current_segment = {
                        "start_time": ts,
                        "end_time": ts,
                        "visual_score": score,
                        "severity": "high" if score > 0.75 else "medium",
                        "frame_count": 1
                    }
                else:
                    current_segment["end_time"] = ts
                    current_segment["visual_score"] = max(current_segment["visual_score"], score)
                    current_segment["frame_count"] += 1
                    if score > 0.75:
                        current_segment["severity"] = "high"
            else:
                if current_segment is not None:
                    # Close the segment if it's long enough
                    if current_segment["frame_count"] >= 3:
                        segments.append(current_segment)
                    current_segment = None
                    
        if current_segment is not None and current_segment["frame_count"] >= 3:
            segments.append(current_segment)
            
        return segments
