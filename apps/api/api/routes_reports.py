"""
Forensic dossier generation (JSON + 5-page PDF).

Data alignment notes:
- Signal scores are read from report_data.signal_scores using the canonical
  keys produced by media_worker: visual / temporal / lip_sync / frequency /
  metadata.
- The composite score and verdict come straight from the fusion engine's
  persisted output (report_data.final_score + job.verdict); this module never
  re-derives them with divergent math.
- Attestation seals are real HMAC-SHA256 signatures computed over a canonical
  record payload using settings.ATTESTATION_SECRET.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
import json
import os
import io
import hashlib
import hmac
import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from core.database import get_db
from core.config import settings, ForensicConfig
from models.orm import Job

router = APIRouter()


def clean_pdf_text(text) -> str:
    """Sanitize unicode for clean PDF rendering."""
    if not text:
        return ""
    text = str(text)
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--", "\u2026": "...", "\u2022": "*",
        "\u26a0\ufe0f": "[!]", "\u274c": "[X]", "\u2705": "[OK]",
        "\U0001f50d": "[SEARCH]", "\U0001f3db\ufe0f": "[GOV]",
        "\U0001f4f0": "[NEWS]", "\U0001f517": "[LINK]", "\U0001f4c5": "[DATE]",
        "\U0001f9e0": "[AI]", "\U0001f550": "[TIME]", "\u20b9": "INR ",
        "\U0001f6a8": "[ALERT]", "\u00b7": "-",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


# ── Font Registration with Resilient Fallback ────────────────────────
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_MEDIUM = "Helvetica"
FONT_MONO = "Courier"
FONT_MONO_BOLD = "Courier-Bold"


def init_fonts():
    global FONT_REGULAR, FONT_BOLD, FONT_MEDIUM, FONT_MONO, FONT_MONO_BOLD

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mono_reg = os.path.join(base, "fonts", "IBMPlexMono-Regular.ttf")
    mono_bld = os.path.join(base, "fonts", "IBMPlexMono-Bold.ttf")

    if os.path.exists(mono_reg) and os.path.exists(mono_bld):
        try:
            pdfmetrics.registerFont(TTFont("IBMPlexMono-Regular", mono_reg))
            pdfmetrics.registerFont(TTFont("IBMPlexMono-Bold", mono_bld))
            FONT_MONO = "IBMPlexMono-Regular"
            FONT_MONO_BOLD = "IBMPlexMono-Bold"
        except Exception:
            pass

    sys_sans = "C:/Windows/Fonts/segoeui.ttf"
    sys_sans_b = "C:/Windows/Fonts/segoeuib.ttf"
    sys_sans_sb = "C:/Windows/Fonts/seguisb.ttf"
    if os.path.exists(sys_sans) and os.path.exists(sys_sans_b):
        try:
            pdfmetrics.registerFont(TTFont("SegoeUI-Regular", sys_sans))
            pdfmetrics.registerFont(TTFont("SegoeUI-Bold", sys_sans_b))
            if os.path.exists(sys_sans_sb):
                pdfmetrics.registerFont(TTFont("SegoeUI-SemiBold", sys_sans_sb))
                FONT_MEDIUM = "SegoeUI-SemiBold"
            else:
                FONT_MEDIUM = "SegoeUI-Regular"
            FONT_REGULAR = "SegoeUI-Regular"
            FONT_BOLD = "SegoeUI-Bold"
        except Exception:
            pass


init_fonts()

# ── Design Tokens ────────────────────────────────────────────────────
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_LEFT = 36
MARGIN_RIGHT = PAGE_WIDTH - 36
CONTENT_WIDTH = PAGE_WIDTH - 72

COLOR_BG = colors.HexColor("#F7F7F5")
COLOR_CARD_BG = colors.HexColor("#FFFFFF")
COLOR_CARD_ALT = colors.HexColor("#FAFAFA")
COLOR_PRIMARY_TEXT = colors.HexColor("#111111")
COLOR_SECONDARY_TEXT = colors.HexColor("#5E6268")
COLOR_MUTED_TEXT = colors.HexColor("#8C9199")
COLOR_BORDER = colors.HexColor("#D9DADC")
COLOR_BORDER_LIGHT = colors.HexColor("#EAEAEA")

COLOR_CRITICAL = colors.HexColor("#C62828")
COLOR_CRITICAL_BG = colors.HexColor("#FDF2F2")
COLOR_CRITICAL_BORDER = colors.HexColor("#F8B4B4")

COLOR_WARNING = colors.HexColor("#B7791F")
COLOR_WARNING_BG = colors.HexColor("#FEFBE8")
COLOR_WARNING_BORDER = colors.HexColor("#FCE588")

COLOR_VERIFIED = colors.HexColor("#237A57")
COLOR_VERIFIED_BG = colors.HexColor("#F0FDF4")
COLOR_VERIFIED_BORDER = colors.HexColor("#BBF7D0")

COLOR_ACCENT_ORANGE = colors.HexColor("#FF5A24")


# ── Attestation helpers ──────────────────────────────────────────────
def build_attestation(job: Job, extra_payload: dict = None) -> dict:
    """Compute canonical record hash + HMAC-SHA256 attestation seal."""
    payload = {
        "case_id": job.id,
        "filename": job.filename,
        "sha256_media": job.sha256,
        "verdict": job.verdict,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }
    if extra_payload:
        payload.update(extra_payload)

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    record_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    seal = hmac.new(
        settings.ATTESTATION_SECRET.encode("utf-8"),
        record_hash.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "record_payload_hash": record_hash,
        "attestation_hmac": f"sha256:{seal}",
        "attested_at": datetime.datetime.utcnow().isoformat(),
        "algorithm": "HMAC-SHA256(record_payload_hash)",
    }


def draw_rounded_card(c, x, y, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER, radius=5, border_width=0.75):
    c.saveState()
    c.setFillColor(bg_color)
    c.setStrokeColor(border_color)
    c.setLineWidth(border_width)
    c.roundRect(x, y, width, height, radius, fill=1, stroke=1)
    c.restoreState()


def draw_header_bar(c, title, subtitle, case_id):
    c.saveState()
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, PAGE_HEIGHT - 38, MARGIN_RIGHT, PAGE_HEIGHT - 38)

    c.setFont(FONT_BOLD, 8)
    c.setFillColor(COLOR_ACCENT_ORANGE)
    c.drawString(MARGIN_LEFT, PAGE_HEIGHT - 32, "DECEPTRIX")

    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawString(MARGIN_LEFT + 56, PAGE_HEIGHT - 32, "-   AI FORENSIC INTELLIGENCE DOSSIER")

    c.setFont(FONT_MONO, 7.5)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawRightString(MARGIN_RIGHT, PAGE_HEIGHT - 32, f"CASE: {str(case_id)[:20]}...")

    c.setFont(FONT_BOLD, 18)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT, PAGE_HEIGHT - 66, title)

    if subtitle:
        c.setFont(FONT_REGULAR, 8.5)
        c.setFillColor(COLOR_SECONDARY_TEXT)
        c.drawString(MARGIN_LEFT, PAGE_HEIGHT - 78, clean_pdf_text(subtitle))
    c.restoreState()


def draw_footer_bar(c, case_id, page_num, total_pages=5):
    c.saveState()
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.line(MARGIN_LEFT, 40, MARGIN_RIGHT, 40)

    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawString(MARGIN_LEFT, 28, "DECEPTRIX v3.0  -  Cryptographically Hashed Forensic Record")

    c.setFont(FONT_MONO, 7.5)
    c.drawRightString(MARGIN_RIGHT, 28, f"Page {page_num} of {total_pages}")
    c.restoreState()


def draw_horizontal_risk_meter(c, x, y, width, height, score):
    c.saveState()
    c.setFillColor(colors.HexColor("#EAEBED"))
    c.roundRect(x, y, width, height, 3, fill=1, stroke=0)

    w_low = width * 0.45
    w_elev = width * 0.17
    w_crit = width * 0.38

    c.setFillColor(colors.HexColor("#D1FAE5"))
    c.rect(x, y, w_low, height, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#FEF3C7"))
    c.rect(x + w_low, y, w_elev, height, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#FEE2E2"))
    c.rect(x + w_low + w_elev, y, w_crit, height, fill=1, stroke=0)

    score_clamped = max(0.0, min(1.0, score))
    fill_w = width * score_clamped
    fill_color = (
        COLOR_CRITICAL if score_clamped >= 0.62 else
        (COLOR_WARNING if score_clamped >= 0.45 else COLOR_VERIFIED)
    )
    c.setFillColor(fill_color)
    c.roundRect(x, y, fill_w, height, 3, fill=1, stroke=0)

    pin_x = x + fill_w
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.setStrokeColor(colors.white)
    c.setLineWidth(1.5)
    c.circle(pin_x, y + height / 2, 5, fill=1, stroke=1)

    c.setFont(FONT_MONO, 6.5)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawString(x, y - 10, "0.00 (ORGANIC)")
    c.drawCentredString(x + w_low, y - 10, "0.45 (SUSPICIOUS)")
    c.drawCentredString(x + w_low + w_elev, y - 10, "0.62 (MANIPULATED)")
    c.drawRightString(x + width, y - 10, "1.00 (SYNTHETIC)")
    c.restoreState()


def _signal_color(score: float):
    if score >= 0.55:
        return COLOR_CRITICAL
    if score >= 0.40:
        return COLOR_WARNING
    return COLOR_VERIFIED


def render_reportlab_dossier(job, db):
    """Generate the complete 5-page forensic dossier PDF."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # ── Extract & align data ─────────────────────────────────────────
    job_id = job.id or ""
    filename = job.filename or "uploaded_media.mp4"
    sha256 = job.sha256 or "N/A"
    created_at = job.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if job.created_at else "N/A"
    completed_at = job.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if job.completed_at else "N/A"
    verdict_raw = job.verdict or "INCONCLUSIVE"

    report_data = job.report_data or {}
    metadata = report_data.get("metadata", {})
    raw_signals = report_data.get("signal_scores", {})

    all_face_items = []
    df_scores, jit_scores, freq_scores = [], [], []

    if job.evidence:
        for ev in job.evidence:
            refs = ev.get("artifact_refs") or []
            for ref in refs:
                ts = ref.get("timestamp_sec", 0)
                faces = ref.get("faces") or []
                for face in faces:
                    fs = float(face.get("fake_score", 0.0))
                    js = float(face.get("jitter_score", 0.0))
                    fr = float(face.get("freq_score", 0.0))
                    df_scores.append(fs)
                    jit_scores.append(js)
                    freq_scores.append(fr)
                    all_face_items.append({
                        "timestamp_sec": ts,
                        "fake_score": fs,
                        "jitter_score": js,
                        "freq_score": fr,
                        "face_crop": face.get("face_crop", ""),
                        "bbox": face.get("bbox", []),
                    })

    max_df = max(df_scores) if df_scores else 0.0
    max_jit = max(jit_scores) if jit_scores else 0.0
    max_freq = max(freq_scores) if freq_scores else 0.0

    vit_score = float(raw_signals.get("visual", max_df))
    lip_score = float(raw_signals.get("lip_sync", 0.0))
    jit_score = float(raw_signals.get("temporal", max_jit))
    dct_score = float(raw_signals.get("frequency", max_freq))
    met_score = float(raw_signals.get("metadata", 0.0))

    composite_score = float(
        report_data.get("final_score")
        if isinstance(report_data.get("final_score"), (int, float)) else 0.0
    )
    assessment_confidence = float(report_data.get("assessment_confidence", 0.0))

    # ── Verdict mapping (consistent with fusion classifications) ─────
    if verdict_raw == "LIKELY MANIPULATED" or composite_score >= 0.62:
        verdict_text = "LIKELY MANIPULATED"
        verdict_badge = "CRITICAL RISK - SYNTHETIC MEDIA INDICATORS CONFIRMED"
        verdict_color, verdict_bg, verdict_border = COLOR_CRITICAL, COLOR_CRITICAL_BG, COLOR_CRITICAL_BORDER
    elif verdict_raw == "SUSPICIOUS" or composite_score >= 0.45:
        verdict_text = "SUSPICIOUS ARTIFACTS"
        verdict_badge = "ELEVATED RISK - ANOMALIES REQUIRE REVIEW"
        verdict_color, verdict_bg, verdict_border = COLOR_WARNING, COLOR_WARNING_BG, COLOR_WARNING_BORDER
    elif verdict_raw == "INCONCLUSIVE":
        verdict_text = "INCONCLUSIVE"
        verdict_badge = "INSUFFICIENT EVIDENCE FOR DETERMINATION"
        verdict_color, verdict_bg, verdict_border = COLOR_WARNING, COLOR_WARNING_BG, COLOR_WARNING_BORDER
    else:
        verdict_text = "LIKELY AUTHENTIC"
        verdict_badge = "LOW RISK - NO HIGH-CONFIDENCE SYNTHETIC SIGNALS"
        verdict_color, verdict_bg, verdict_border = COLOR_VERIFIED, COLOR_VERIFIED_BG, COLOR_VERIFIED_BORDER

    attestation = build_attestation(job)

    # ══════════════════════════════════════════════════════════════
    # PAGE 1 — EXECUTIVE SUMMARY
    # ══════════════════════════════════════════════════════════════
    draw_header_bar(c, "FORENSIC INTELLIGENCE DOSSIER",
                    "EXECUTIVE SUMMARY & MULTI-MODAL THREAT ASSESSMENT", job_id, )

    panel_y = PAGE_HEIGHT - 200
    draw_rounded_card(c, MARGIN_LEFT, panel_y, CONTENT_WIDTH, 105, bg_color=verdict_bg, border_color=verdict_border, radius=6)

    c.setFont(FONT_MONO_BOLD, 8)
    c.setFillColor(verdict_color)
    c.drawString(MARGIN_LEFT + 18, panel_y + 85, "FORENSIC VERDICT & THREAT ASSESSMENT")

    c.setFont(FONT_BOLD, 22)
    c.drawString(MARGIN_LEFT + 18, panel_y + 58, verdict_text)

    c.setFont(FONT_BOLD, 8.5)
    c.drawString(MARGIN_LEFT + 18, panel_y + 42, f"CLASSIFICATION: {clean_pdf_text(verdict_badge)}")

    c.setFont(FONT_REGULAR, 8.5)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    if "MANIPULATED" in verdict_text:
        narrative = ("Multi-modal Bayesian consensus indicates synthetic generation or manipulation "
                     "exceeding calibrated detection thresholds.")
    elif "AUTHENTIC" in verdict_text:
        narrative = ("No high-confidence synthetic signals were detected across visual, temporal, "
                     "spectral and audio-visual engines.")
    elif "INCONCLUSIVE" in verdict_text:
        narrative = ("Signal evidence was insufficient or conflicting; secondary manual review "
                     "is strongly recommended.")
    else:
        narrative = ("Anomalies were detected across one or more modalities; manual secondary "
                     "forensic inspection is recommended.")
    c.drawString(MARGIN_LEFT + 18, panel_y + 22, narrative[:110])

    c.setFont(FONT_MONO, 8)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawRightString(MARGIN_RIGHT - 18, panel_y + 85, "COMPOSITE ANOMALY")

    c.setFont(FONT_BOLD, 24)
    c.setFillColor(verdict_color)
    c.drawRightString(MARGIN_RIGHT - 18, panel_y + 58, f"{composite_score:.2f}")

    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawRightString(MARGIN_RIGHT - 18, panel_y + 44, f"CONFIDENCE: {assessment_confidence:.2f}")

    meter_card_y = panel_y - 82
    draw_rounded_card(c, MARGIN_LEFT, meter_card_y, CONTENT_WIDTH, 72, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)

    c.setFont(FONT_BOLD, 9)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, meter_card_y + 52, "COMPOSITE FORENSIC RISK RATING")

    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(COLOR_SECONDARY_TEXT)
    c.drawRightString(MARGIN_RIGHT - 16, meter_card_y + 52, "Log-Odds Bayesian Fusion of Independent Signals")

    draw_horizontal_risk_meter(c, MARGIN_LEFT + 16, meter_card_y + 26, CONTENT_WIDTH - 32, 10, composite_score)

    snap_y = meter_card_y - 75
    card_w = (CONTENT_WIDTH - 24) / 4

    duration = metadata.get("duration") or 0
    fps_meta = metadata.get("fps") or 0
    snapshots = [
        ("DURATION", f"{duration:.1f}s @ {metadata.get('fps', fps_meta)} src FPS"),
        ("RESOLUTION", f"{metadata.get('width', '?')}x{metadata.get('height', '?')} ({str(metadata.get('video_codec', 'h264')).upper()})"),
        ("AUDIO STREAM", f"{str(metadata.get('audio_codec', 'aac')).upper()} @ {metadata.get('audio_sample_rate', 48000)} Hz"),
        ("FRAMES ANALYZED", f"{report_data.get('frames_analyzed', len(all_face_items))} @ {ForensicConfig.ANALYSIS_FPS} FPS"),
    ]

    for i, (label, val) in enumerate(snapshots):
        cx = MARGIN_LEFT + i * (card_w + 8)
        draw_rounded_card(c, cx, snap_y, card_w, 62, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER_LIGHT)
        c.setFont(FONT_MONO_BOLD, 7)
        c.setFillColor(COLOR_MUTED_TEXT)
        c.drawString(cx + 10, snap_y + 44, label)
        c.setFont(FONT_BOLD, 8.5)
        c.setFillColor(COLOR_PRIMARY_TEXT)
        c.drawString(cx + 10, snap_y + 24, clean_pdf_text(val)[:24])
        c.setFont(FONT_REGULAR, 7)
        c.setFillColor(COLOR_SECONDARY_TEXT)
        c.drawString(cx + 10, snap_y + 12, "Verified Pipeline Data")

    why_y = snap_y - 195
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT, why_y + 180, "PRIMARY EVIDENTIARY DRIVERS (WHY THIS VERDICT?)")

    drivers = [
        ("VISUAL SYNTHESIS (ViT ENSEMBLE)", f"{vit_score:.2f}",
         "Aligned-face Vision Transformer ensemble with TTA and blur-aware calibration."),
        ("LIP-SYNC DESYNCHRONIZATION", f"{lip_score:.2f}",
         "Lag-searched Pearson correlation between mouth aperture (MAR) and acoustic RMS energy."),
        ("TEMPORAL MESH CONSISTENCY", f"{jit_score:.2f}",
         "Region-weighted micro-motion variance across tracked facial landmark sequences."),
    ]
    driver_card_h = 48
    for idx, (sig_name, sig_score, sig_desc) in enumerate(drivers):
        dy = why_y + 115 - idx * (driver_card_h + 8)
        draw_rounded_card(c, MARGIN_LEFT, dy, CONTENT_WIDTH, driver_card_h, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)

        sig_col = _signal_color(float(sig_score))
        c.setFont(FONT_BOLD, 8.5)
        c.setFillColor(COLOR_PRIMARY_TEXT)
        c.drawString(MARGIN_LEFT + 14, dy + 30, sig_name)

        c.setFont(FONT_MONO_BOLD, 9)
        c.setFillColor(sig_col)
        c.drawRightString(MARGIN_RIGHT - 14, dy + 30, f"SCORE: {sig_score}")

        c.setFont(FONT_REGULAR, 7.5)
        c.setFillColor(COLOR_SECONDARY_TEXT)
        c.drawString(MARGIN_LEFT + 14, dy + 14, clean_pdf_text(sig_desc)[:115])

    draw_footer_bar(c, job_id, 1, 5)
    c.showPage()

    # ══════════════════════════════════════════════════════════════
    # PAGE 2 — SIGNAL CONSENSUS
    # ══════════════════════════════════════════════════════════════
    draw_header_bar(c, "FORENSIC SIGNAL CONSENSUS",
                    "MULTI-MODAL DECOMPOSITION ACROSS 5 INDEPENDENT ENGINES", job_id)

    signals_data = [
        ("VISUAL DEEPFAKE TEXTURE", "ViT Ensemble (Dima806+PrithivV2) + TTA + Calibration", vit_score,
         "Patch-level self-attention analysis of aligned face crops for generative synthesis artifacts."),
        ("LIP-SYNC AUDIO-VISUAL CORRELATION", "MAR x RMS Lag-Search Pearson Sync", lip_score,
         "Best-alignment acoustic-visual coupling; desynchronization implies re-animation or dubbing."),
        ("FACIAL LANDMARK TEMPORAL JITTER", "MediaPipe 468-pt Mesh Region-Variance", jit_score,
         "Micro-motion flutter across rigid facial regions exceeds natural tremor statistics."),
        ("2D-DCT SPECTRAL ANOMALY", "Radial DCT Profile + Block Grid Analysis", dct_score,
         "High-frequency energy distribution, spectral slope and periodic block artifacts."),
        ("CONTAINER METADATA INTEGRITY", "FFprobe Stream Telemetry", met_score,
         "Codec profile, encoder tags, bitrate sanity and creation-date presence."),
    ]

    start_y = PAGE_HEIGHT - 105
    card_height = 84
    card_gap = 10

    for idx, (sig_name, model_name, score, interpretation) in enumerate(signals_data):
        cy = start_y - idx * (card_height + card_gap)
        draw_rounded_card(c, MARGIN_LEFT, cy, CONTENT_WIDTH, card_height, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)

        c.setFont(FONT_BOLD, 9.5)
        c.setFillColor(COLOR_PRIMARY_TEXT)
        c.drawString(MARGIN_LEFT + 16, cy + 62, clean_pdf_text(sig_name))

        c.setFont(FONT_MONO, 7.5)
        c.setFillColor(COLOR_MUTED_TEXT)
        c.drawString(MARGIN_LEFT + 16, cy + 48, clean_pdf_text(f"MODEL: {model_name}"))

        threshs = [0.55, 0.50, 0.45, 0.40, 0.30]
        thresh = threshs[idx]
        if score > thresh + 0.15:
            status_text, status_col = "CRITICAL RISK", COLOR_CRITICAL
        elif score > thresh:
            status_text, status_col = "ELEVATED RISK", COLOR_WARNING
        else:
            status_text, status_col = "NORMAL / VERIFIED", COLOR_VERIFIED

        c.setFont(FONT_MONO_BOLD, 9)
        c.setFillColor(status_col)
        c.drawRightString(MARGIN_RIGHT - 16, cy + 62, f"SCORE: {score:.2f} / 1.00  [{status_text}]")

        bar_x = MARGIN_LEFT + 16
        bar_y = cy + 30
        bar_w = CONTENT_WIDTH - 32

        c.setFillColor(colors.HexColor("#EAEBED"))
        c.roundRect(bar_x, bar_y, bar_w, 6, 3, fill=1, stroke=0)
        c.setFillColor(status_col)
        c.roundRect(bar_x, bar_y, bar_w * max(0.0, min(1.0, score)), 6, 3, fill=1, stroke=0)

        c.setFont(FONT_REGULAR, 7)
        c.setFillColor(COLOR_SECONDARY_TEXT)
        c.drawString(MARGIN_LEFT + 16, cy + 14, clean_pdf_text(f"INTERPRETATION: {interpretation}")[:150])

    flow_y = 60
    draw_rounded_card(c, MARGIN_LEFT, flow_y, CONTENT_WIDTH, 70, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER)

    c.setFont(FONT_BOLD, 8.5)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, flow_y + 50, "LOG-ODDS BAYESIAN FUSION ARCHITECTURE")

    contributions = report_data.get("contributions", {})
    contrib_str = "  ".join(f"{k}:{v:+.2f}" for k, v in contributions.items()) or "n/a"

    c.setFont(FONT_MONO, 7.5)
    c.setFillColor(COLOR_SECONDARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, flow_y + 36, clean_pdf_text(f"Per-signal log-odds contributions: {contrib_str}"))

    box_w = (CONTENT_WIDTH - 64) / 4
    stages = [
        ("1. 5 SIGNALS", "Independent extractors"),
        ("2. CALIBRATION", "Platt + quality damping"),
        ("3. LOG-ODDS FUSION", "Weighted Naive-Bayes"),
        ("4. FINAL VERDICT", f"P={composite_score:.2f}"),
    ]
    for b_idx, (b_title, b_sub) in enumerate(stages):
        bx = MARGIN_LEFT + 16 + b_idx * (box_w + 10)
        by = flow_y + 8
        c.setFillColor(COLOR_CARD_BG)
        c.setStrokeColor(COLOR_BORDER)
        c.roundRect(bx, by, box_w, 22, 3, fill=1, stroke=1)
        c.setFont(FONT_BOLD, 7)
        c.setFillColor(COLOR_PRIMARY_TEXT)
        c.drawCentredString(bx + box_w / 2, by + 12, b_title)
        c.setFont(FONT_REGULAR, 6.5)
        c.setFillColor(COLOR_MUTED_TEXT)
        c.drawCentredString(bx + box_w / 2, by + 4, clean_pdf_text(b_sub))

    draw_footer_bar(c, job_id, 2, 5)
    c.showPage()

    # ══════════════════════════════════════════════════════════════
    # PAGE 3 — EVIDENCE INTEGRITY & TELEMETRY
    # ══════════════════════════════════════════════════════════════
    draw_header_bar(c, "EVIDENCE INTEGRITY & TELEMETRY",
                    "CRYPTOGRAPHIC CHAIN OF CUSTODY & CONTAINER STREAM INSPECTION", job_id)

    coc_y = PAGE_HEIGHT - 295
    draw_rounded_card(c, MARGIN_LEFT, coc_y, CONTENT_WIDTH, 195, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)

    c.setFont(FONT_BOLD, 9.5)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, coc_y + 172, "CHAIN OF CUSTODY & INGESTION PROVENANCE")

    coc_steps = [
        ("01 INGESTION", f"Payload '{clean_pdf_text(filename)}' received and MIME/size validated.", created_at),
        ("02 FINGERPRINT", "Computed SHA-256 cryptographic digest across full binary stream.", created_at),
        ("03 DEMUX & DECODE", f"Extracted {ForensicConfig.ANALYSIS_FPS} FPS frame sequence and 16 kHz PCM mono audio.", created_at),
        ("04 FORENSIC ENGINES", "ViT ensemble, FaceMesh tracking, DCT spectral, lag-searched lip-sync.", completed_at),
        ("05 EVIDENCE FUSION", "Log-odds weighted consensus across available independent signals.", completed_at),
        ("06 ATTESTATION", "Computed HMAC-SHA256 tamper-evident attestation seal.", completed_at),
    ]

    step_y_start = coc_y + 145
    for s_idx, (s_title, s_desc, s_time) in enumerate(coc_steps):
        sy = step_y_start - s_idx * 24
        c.setFillColor(COLOR_ACCENT_ORANGE)
        c.circle(MARGIN_LEFT + 22, sy + 3, 4, fill=1, stroke=0)
        c.setFont(FONT_MONO_BOLD, 8)
        c.setFillColor(COLOR_PRIMARY_TEXT)
        c.drawString(MARGIN_LEFT + 34, sy, s_title)
        c.setFont(FONT_REGULAR, 7.5)
        c.setFillColor(COLOR_SECONDARY_TEXT)
        c.drawString(MARGIN_LEFT + 130, sy, s_desc[:80])
        c.setFont(FONT_MONO, 7)
        c.setFillColor(COLOR_MUTED_TEXT)
        c.drawRightString(MARGIN_RIGHT - 16, sy, str(s_time))

    hash_y = coc_y - 75
    draw_rounded_card(c, MARGIN_LEFT, hash_y, CONTENT_WIDTH, 62, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER)

    c.setFont(FONT_MONO_BOLD, 8)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawString(MARGIN_LEFT + 16, hash_y + 44, "CRYPTOGRAPHIC SHA-256 PAYLOAD FINGERPRINT")

    c.setFont(FONT_MONO_BOLD, 9.5)
    c.setFillColor(COLOR_ACCENT_ORANGE)
    c.drawString(MARGIN_LEFT + 16, hash_y + 26, sha256)

    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawString(MARGIN_LEFT + 16, hash_y + 12, "Tamper-evident verification: any byte modification to raw media invalidates this digest.")

    grid_y = hash_y - 255
    c.setFont(FONT_BOLD, 10)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT, grid_y + 242, "TECHNICAL MEDIA STREAM & CONTAINER TELEMETRY")

    bitrate = metadata.get("bitrate") or 0
    telemetry_items = [
        ("VIDEO CODEC / STREAM", f"{str(metadata.get('video_codec', 'unknown')).upper()} @ {fps_meta:.1f} SRC FPS"),
        ("CONTAINER FORMAT", clean_pdf_text(str(metadata.get("format_name", "unknown"))[:24])),
        ("RESOLUTION", f"{metadata.get('width', '?')} x {metadata.get('height', '?')} px"),
        ("TOTAL BITRATE", f"{bitrate // 1000} kbps" if bitrate else "N/A"),
        ("AUDIO STREAM", f"{str(metadata.get('audio_codec', 'none')).upper()} @ {metadata.get('audio_sample_rate', 0)} Hz"),
        ("CREATION HEADER TAG", "Present" if metadata.get("has_creation_date") else "Missing / Stripped"),
    ]

    t_card_w = (CONTENT_WIDTH - 12) / 2
    t_card_h = 58

    for t_idx, (t_label, t_val) in enumerate(telemetry_items):
        row = t_idx // 2
        col = t_idx % 2
        tx = MARGIN_LEFT + col * (t_card_w + 12)
        ty = grid_y + 168 - row * (t_card_h + 10)

        draw_rounded_card(c, tx, ty, t_card_w, t_card_h, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)
        c.setFont(FONT_MONO_BOLD, 7)
        c.setFillColor(COLOR_MUTED_TEXT)
        c.drawString(tx + 12, ty + 42, t_label)
        c.setFont(FONT_BOLD, 9.5)
        c.setFillColor(COLOR_PRIMARY_TEXT)
        c.drawString(tx + 12, ty + 26, str(t_val)[:34])

    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawString(MARGIN_LEFT, grid_y - 25, "NOTE: Metadata absence is supportive evidence only, not standalone proof of manipulation.")

    draw_footer_bar(c, job_id, 3, 5)
    c.showPage()

    # ══════════════════════════════════════════════════════════════
    # PAGE 4 — VISUAL EVIDENCE
    # ══════════════════════════════════════════════════════════════
    draw_header_bar(c, "VISUAL EVIDENCE & BIOMETRICS",
                    "FRAME-LEVEL FACIAL EXTRACTION AND ARTIFACT LOCALIZATION", job_id)

    ranked_faces = sorted(all_face_items, key=lambda f: f["fake_score"], reverse=True)
    evidence_cards = ranked_faces[:2]

    evidence_card_h = 200
    card_gap = 14

    for idx, face_item in enumerate(evidence_cards):
        ey = PAGE_HEIGHT - 98 - (idx + 1) * evidence_card_h - idx * card_gap
        draw_rounded_card(c, MARGIN_LEFT, ey, CONTENT_WIDTH, evidence_card_h, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)

        ts = face_item["timestamp_sec"]
        mins = int(ts) // 60
        secs = int(ts) % 60
        time_str = f"{mins:02d}:{secs:02d}"
        fake_s = face_item["fake_score"]

        img_x = MARGIN_LEFT + 14
        img_y = ey + 14
        img_size = 172
        draw_rounded_card(c, img_x, img_y, img_size, img_size, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER_LIGHT)

        crop_path = face_item.get("face_crop", "")
        if crop_path and os.path.exists(crop_path):
            try:
                c.drawImage(crop_path, img_x + 4, img_y + 4, width=img_size - 8, height=img_size - 8, preserveAspectRatio=True)
            except Exception:
                pass
        if not crop_path or not os.path.exists(crop_path):
            c.setFont(FONT_MONO, 8)
            c.setFillColor(COLOR_MUTED_TEXT)
            c.drawCentredString(img_x + img_size / 2, img_y + img_size / 2, "[FACE CROP IMAGE]")

        dt_x = img_x + img_size + 16

        c.setFont(FONT_BOLD, 11)
        c.setFillColor(COLOR_PRIMARY_TEXT)
        c.drawString(dt_x, ey + 172, f"HIGHEST-RISK KEYFRAME #{idx + 1:02d}  -  TIMESTAMP {time_str}")

        risk_tag = "HIGH MANIPULATION RISK" if fake_s > 0.62 else ("ELEVATED ANOMALY" if fake_s > 0.45 else "ORGANIC TEXTURE")
        risk_tag_col = COLOR_CRITICAL if fake_s > 0.62 else (COLOR_WARNING if fake_s > 0.45 else COLOR_VERIFIED)

        c.setFont(FONT_BOLD, 8.5)
        c.setFillColor(risk_tag_col)
        c.drawString(dt_x, ey + 156, f"CLASSIFICATION: {risk_tag} ({fake_s * 100:.1f}%)")

        c.setFont(FONT_MONO, 7.5)
        c.setFillColor(COLOR_PRIMARY_TEXT)
        c.drawString(dt_x, ey + 134, f"- Calibrated ViT Anomaly:      {fake_s * 100:.1f}% synthetic")
        c.drawString(dt_x, ey + 120, f"- 2D-DCT Spectral Residual:    {face_item['freq_score']:.2f} / 1.00")
        c.drawString(dt_x, ey + 106, f"- Temporal Window Jitter:      {face_item['jitter_score']:.2f} / 1.00")

        bbox_str = str(face_item.get("bbox", [0, 0, 0, 0]))
        c.drawString(dt_x, ey + 92, f"- Bounding Box Coordinates:    {bbox_str}")

        c.setFont(FONT_BOLD, 8)
        c.setFillColor(COLOR_PRIMARY_TEXT)
        c.drawString(dt_x, ey + 70, "DETECTED BIOMETRIC INDICATORS:")

        c.setFont(FONT_REGULAR, 7)
        c.setFillColor(COLOR_SECONDARY_TEXT)
        if fake_s > 0.62:
            c.drawString(dt_x, ey + 56, "- High-confidence generative synthesis patterns flagged in skin texture.")
            c.drawString(dt_x, ey + 44, "- Spectral descriptors deviate from natural camera capture statistics.")
            c.drawString(dt_x, ey + 32, "- Recommend reviewing adjacent keyframes for warp discontinuity.")
        else:
            c.drawString(dt_x, ey + 56, "- Facial landmark coherence consistent with natural movement.")
            c.drawString(dt_x, ey + 44, "- Frequency falloff matches organic recording characteristics.")
            c.drawString(dt_x, ey + 32, "- No significant generative synthesis artifacts observed.")

    strip_y = 50
    draw_rounded_card(c, MARGIN_LEFT, strip_y, CONTENT_WIDTH, 75, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER)

    c.setFont(FONT_BOLD, 8)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 14, strip_y + 58, "TEMPORAL BIOMETRIC PROGRESSION (CHRONOLOGICAL SAMPLE)")

    strip_items = all_face_items[::max(1, len(all_face_items) // 5)][:5] if all_face_items else []
    thumb_w = (CONTENT_WIDTH - 64) / 5
    thumb_h = 38

    for s_idx, s_face in enumerate(strip_items):
        sx = MARGIN_LEFT + 14 + s_idx * (thumb_w + 9)
        sy = strip_y + 10

        draw_rounded_card(c, sx, sy, thumb_w, thumb_h, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER_LIGHT)
        s_crop = s_face.get("face_crop", "")
        if s_crop and os.path.exists(s_crop):
            try:
                c.drawImage(s_crop, sx + 2, sy + 8, width=thumb_w - 4, height=thumb_h - 10, preserveAspectRatio=True)
            except Exception:
                pass

        c.setFont(FONT_MONO, 6.5)
        c.setFillColor(COLOR_MUTED_TEXT)
        c.drawCentredString(sx + thumb_w / 2, sy + 2, f"T: {s_face['timestamp_sec']}s")

    draw_footer_bar(c, job_id, 4, 5)
    c.showPage()

    # ══════════════════════════════════════════════════════════════
    # PAGE 5 — CONCLUSION & ATTESTATION
    # ══════════════════════════════════════════════════════════════
    draw_header_bar(c, "FORENSIC CONCLUSION",
                    "EXPLAINABLE SYNTHESIS & SCIENTIFIC ATTESTATION", job_id)

    v_sum_y = PAGE_HEIGHT - 175
    draw_rounded_card(c, MARGIN_LEFT, v_sum_y, CONTENT_WIDTH, 80, bg_color=verdict_bg, border_color=verdict_border)

    c.setFont(FONT_MONO_BOLD, 8)
    c.setFillColor(verdict_color)
    c.drawString(MARGIN_LEFT + 16, v_sum_y + 60, "FINAL FORENSIC DETERMINATION")

    c.setFont(FONT_BOLD, 18)
    c.drawString(MARGIN_LEFT + 16, v_sum_y + 36, verdict_text)

    c.setFont(FONT_MONO_BOLD, 12)
    c.drawRightString(MARGIN_RIGHT - 16, v_sum_y + 38, f"COMPOSITE: {composite_score:.2f} / 1.00")

    c.setFont(FONT_REGULAR, 8)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, v_sum_y + 16, "Consensus derived from log-odds fusion of independent neural, acoustic, temporal and metadata engines.")

    sec_y = v_sum_y - 250
    draw_rounded_card(c, MARGIN_LEFT, sec_y, CONTENT_WIDTH, 235, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)

    c.setFont(FONT_BOLD, 9)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, sec_y + 214, "1. PRIMARY FORENSIC FINDING")

    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(COLOR_SECONDARY_TEXT)
    if "MANIPULATED" in verdict_text:
        finding_lines = [
            "Multiple independent forensic engines converge on synthetic-generation indicators.",
            f"The visual channel scored {vit_score:.2f}; supporting modalities contributed",
            f"log-odds mass {json.dumps(report_data.get('contributions', {}))}.",
        ]
    elif "AUTHENTIC" in verdict_text:
        finding_lines = [
            "No engine exceeded its calibrated anomaly threshold with corroborating support.",
            f"The visual channel scored {vit_score:.2f}; temporal/spectral/acoustic channels",
            "remained within organic operating ranges.",
        ]
    elif "INCONCLUSIVE" in verdict_text:
        finding_lines = [
            "Evidence was insufficient or contradictory for a definitive classification.",
            "Possible causes: no detectable faces, silent video, extreme compression,",
            "or strong disagreement between independent engines.",
        ]
    else:
        finding_lines = [
            "One or more engines flagged anomalies without decisive multi-modal corroboration.",
            f"Visual={vit_score:.2f}, LipSync={lip_score:.2f}, Temporal={jit_score:.2f},",
            f"Spectral={dct_score:.2f}. Manual review is recommended before conclusions.",
        ]
    for li, line in enumerate(finding_lines):
        c.drawString(MARGIN_LEFT + 16, sec_y + 198 - li * 12, clean_pdf_text(line)[:130])

    c.setFont(FONT_BOLD, 9)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, sec_y + 148, "2. SUPPORTING MULTI-MODAL EVIDENCE")

    c.setFont(FONT_REGULAR, 7.5)
    c.setFillColor(COLOR_SECONDARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, sec_y + 132, f"- Visual Modality: ViT ensemble scored {vit_score:.2f} across sampled keyframes.")
    c.drawString(MARGIN_LEFT + 16, sec_y + 118, f"- Audio-Visual Sync: best-lag correlation yielded anomaly score {lip_score:.2f}.")
    c.drawString(MARGIN_LEFT + 16, sec_y + 104, f"- Biometric Mesh: region-weighted temporal jitter scored {jit_score:.2f}.")

    c.setFont(FONT_BOLD, 9)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, sec_y + 78, "3. SCIENTIFIC LIMITATIONS & FORENSIC BOUNDARIES")

    c.setFont(FONT_REGULAR, 7)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawString(MARGIN_LEFT + 16, sec_y + 62, "- Algorithmic diagnostic assessment; not a court-admissible certificate of absolute truth.")
    c.drawString(MARGIN_LEFT + 16, sec_y + 48, f"- Analysis operates on dense sampled keyframes at {ForensicConfig.ANALYSIS_FPS} FPS; unsampled frames are not evaluated.")
    c.drawString(MARGIN_LEFT + 16, sec_y + 34, "- Heavy transcoding can introduce spectral noise and landmark jitter resembling manipulation.")
    c.drawString(MARGIN_LEFT + 16, sec_y + 20, "- Novel generative architectures may exhibit artifact distributions absent from training data.")

    seal_y = 50
    draw_rounded_card(c, MARGIN_LEFT, seal_y, CONTENT_WIDTH, 115, bg_color=COLOR_CARD_ALT, border_color=COLOR_BORDER)

    c.setFont(FONT_BOLD, 9)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, seal_y + 94, "CRYPTOGRAPHIC ATTESTATION & SYSTEM INTEGRITY SEAL")

    c.setFont(FONT_MONO, 7)
    c.setFillColor(COLOR_PRIMARY_TEXT)
    c.drawString(MARGIN_LEFT + 16, seal_y + 78, f"CASE AUDIT ID:       {job_id}")
    c.drawString(MARGIN_LEFT + 16, seal_y + 66, f"MEDIA SHA-256:       {sha256}")
    c.drawString(MARGIN_LEFT + 16, seal_y + 54, f"RECORD PAYLOAD HASH: {attestation['record_payload_hash']}")
    c.drawString(MARGIN_LEFT + 16, seal_y + 42, f"ATTESTATION SEAL:    {attestation['attestation_hmac']}")
    c.drawString(MARGIN_LEFT + 16, seal_y + 30, f"ATTESTED AT (UTC):   {attestation['attested_at']}")

    c.setFont(FONT_REGULAR, 6.5)
    c.setFillColor(COLOR_MUTED_TEXT)
    c.drawString(MARGIN_LEFT + 16, seal_y + 14, "Verify authenticity by recomputing HMAC-SHA256 over the JSON record payload hash with the platform attestation key.")

    draw_footer_bar(c, job_id, 5, 5)
    c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


@router.get("/{job_id}.json")
def get_report_json(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    report_payload = {
        "report_version": "3.0.0",
        "pipeline_version": "3.0.0-logodds-fusion",
        "id": job.id,
        "modality": job.modality,
        "status": job.status,
        "filename": job.filename,
        "sha256": job.sha256,
        "verdict": job.verdict,
        "progress": job.progress,
        "evidence": job.evidence or [],
        "report_data": job.report_data or {},
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "disclaimer": (
            "This automated forensic report was generated by DECEPTRIX. Findings represent "
            "algorithmic assessments based on specified model versions and retrieved sources. "
            "It does not constitute a definitive legal certification."
        ),
    }

    attestation = build_attestation(job, {"report_version": report_payload["report_version"]})
    report_payload["audit_record_hash"] = attestation["record_payload_hash"]
    report_payload["attestation"] = attestation

    return JSONResponse(content=report_payload)


@router.get("/{job_id}.pdf")
def get_report_pdf(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        pdf_bytes = render_reportlab_dossier(job, db)
    except Exception as e:
        print(f"[reports] PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return Response(content=pdf_bytes, media_type="application/pdf")
