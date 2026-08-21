import subprocess
import json
from typing import Dict, Any, Tuple, List

class MetadataEvidence:
    @staticmethod
    def extract(file_path: str) -> Tuple[Dict[str, Any], float, List[str]]:
        """
        Run ffprobe and return structured metadata + anomaly score. 
        Note that metadata anomalies are TECHNICAL ANOMALIES, not necessarily MANIPULATION EVIDENCE.
        """
        try:
            cmd = ["ffprobe", "-v", "quiet", "-print_format", "json",
                   "-show_format", "-show_streams", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            probe = json.loads(result.stdout)

            fmt = probe.get("format", {})
            streams = probe.get("streams", [])

            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

            # Parse FPS safely
            fps_val = 0
            if video_stream:
                fps_str = video_stream.get("r_frame_rate", "0/1")
                if "/" in str(fps_str):
                    parts = str(fps_str).split("/")
                    fps_val = int(parts[0]) / max(1, int(parts[1]))
                else:
                    fps_val = float(fps_str)

            metadata = {
                "duration": float(fmt.get("duration", 0)),
                "format_name": fmt.get("format_name", "unknown"),
                "container": fmt.get("format_long_name", "unknown"),
                "video_codec": video_stream.get("codec_name", "unknown") if video_stream else "none",
                "width": int(video_stream.get("width", 0)) if video_stream else 0,
                "height": int(video_stream.get("height", 0)) if video_stream else 0,
                "fps": fps_val,
                "audio_codec": audio_stream.get("codec_name", "none") if audio_stream else "none",
                "audio_sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
                "has_creation_date": bool(fmt.get("tags", {}).get("creation_time")),
            }

            # Technical Anomaly scoring - intentionally kept low impact for deepfake detection
            anomaly_score = 0.0
            reasons = []
            if not metadata["has_creation_date"]:
                anomaly_score += 0.15
                reasons.append("TECHNICAL ANOMALY: No creation date in metadata")
            if metadata["video_codec"] not in ("h264", "hevc", "vp8", "vp9", "av1"):
                anomaly_score += 0.1
                reasons.append(f"TECHNICAL ANOMALY: Unusual codec: {metadata['video_codec']}")
            if metadata["duration"] < 1.0:
                anomaly_score += 0.1
                reasons.append("TECHNICAL ANOMALY: Very short duration")

            return metadata, min(1.0, anomaly_score), reasons
        except Exception as e:
            print(f"FFprobe error: {e}")
            return {}, 0.0, ["TECHNICAL ANOMALY: FFprobe unavailable"]
