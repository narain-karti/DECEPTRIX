"""
Container & stream metadata telemetry.

Metadata anomalies are TECHNICAL signals — supportive evidence, never
standalone proof. This engine extracts richer telemetry than the legacy
version (encoder tags, bitrate sanity, resolution class, timebase) and
returns a bounded anomaly score with human-readable reasons.
"""
import subprocess
import json
import os
from typing import Dict, Any, Tuple, List


class MetadataEvidence:
    @staticmethod
    def extract(file_path: str) -> Tuple[Dict[str, Any], float, List[str]]:
        if not os.path.exists(file_path):
            return {}, 0.0, ["TECHNICAL ANOMALY: File not found for FFprobe"]

        try:
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", file_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            probe = json.loads(result.stdout or "{}")

            fmt = probe.get("format", {})
            streams = probe.get("streams", [])

            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

            # Parse FPS safely
            fps_val = 0.0
            if video_stream:
                fps_str = video_stream.get("r_frame_rate", "0/1")
                try:
                    if "/" in str(fps_str):
                        num, den = str(fps_str).split("/")
                        fps_val = int(num) / max(1, int(den))
                    else:
                        fps_val = float(fps_str)
                except Exception:
                    fps_val = 0.0

            tags = fmt.get("tags", {}) or {}
            encoder_tag = (
                video_stream.get("tags", {}).get("encoder")
                or tags.get("encoder")
                or tags.get("handler_name")
                or ""
            )

            bitrate = int(fmt.get("bit_rate", 0) or 0)
            duration = float(fmt.get("duration", 0) or 0)
            width = int(video_stream.get("width", 0)) if video_stream else 0
            height = int(video_stream.get("height", 0)) if video_stream else 0

            metadata: Dict[str, Any] = {
                "duration": duration,
                "bitrate": bitrate,
                "format_name": fmt.get("format_name", "unknown"),
                "container": fmt.get("format_long_name", "unknown"),
                "video_codec": video_stream.get("codec_name", "none") if video_stream else "none",
                "pix_fmt": video_stream.get("pix_fmt", "unknown") if video_stream else "unknown",
                "profile": video_stream.get("profile", "") if video_stream else "",
                "encoder_tag": encoder_tag,
                "nb_frames": int(video_stream.get("nb_frames", 0) or 0),
                "time_base": video_stream.get("time_base", "") if video_stream else "",
                "width": width,
                "height": height,
                "fps": round(fps_val, 3),
                "audio_codec": audio_stream.get("codec_name", "none") if audio_stream else "none",
                "audio_sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else 0,
                "has_creation_date": bool(tags.get("creation_time")),
            }

            anomaly_score = 0.0
            reasons: List[str] = []

            if not metadata["has_creation_date"]:
                anomaly_score += 0.12
                reasons.append("TECHNICAL ANOMALY: No creation date in container metadata")

            known_encoders = ("gstreamer", "lavf", "ffmpeg", "handbrake", "adobe", "apple",
                              "google", "samsung", "android", "iphone", "hevc", "h264",
                              "avc coding", "vivo", "xiaomi", "oppo", "instagram", "tiktok", "whatsapp")
            enc_lower = metadata["encoder_tag"].lower()
            if metadata["encoder_tag"] and not any(k in enc_lower for k in known_encoders):
                anomaly_score += 0.08
                reasons.append(f"TECHNICAL ANOMALY: Unusual encoder tag '{metadata['encoder_tag']}'")

            standard_codecs = ("h264", "hevc", "vp8", "vp9", "av1", "mpeg4")
            if metadata["video_codec"] not in standard_codecs:
                anomaly_score += 0.10
                reasons.append(f"TECHNICAL ANOMALY: Unusual video codec '{metadata['video_codec']}'")

            if 0 < duration < 1.0:
                anomaly_score += 0.10
                reasons.append("TECHNICAL ANOMALY: Very short duration (<1s)")

            # Bitrate sanity: extremely low bitrate at high resolution hints
            # at heavy transcoding pipelines common to synthetic content.
            if width and height and bitrate:
                px_per_bit = (width * height * max(fps_val, 1e-3)) / max(bitrate, 1)
                if px_per_bit > 40:
                    anomaly_score += 0.10
                    reasons.append(
                        f"TECHNICAL ANOMALY: Extreme compression (px/bit ratio {px_per_bit:.1f})"
                    )

            return metadata, min(1.0, anomaly_score), reasons

        except FileNotFoundError:
            return {}, 0.0, ["TECHNICAL ANOMALY: FFprobe binary not available"]
        except Exception as e:
            print(f"FFprobe error: {e}")
            return {}, 0.0, ["TECHNICAL ANOMALY: FFprobe inspection failed"]
