import sys
import os
import datetime
import math

sys.path.insert(0, os.path.abspath("apps/api"))

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Font Registration with Resilient Fallback ---
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_MEDIUM = "Helvetica"
FONT_MONO = "Courier"
FONT_MONO_BOLD = "Courier-Bold"

def init_fonts():
    global FONT_REGULAR, FONT_BOLD, FONT_MEDIUM, FONT_MONO, FONT_MONO_BOLD
    
    # 1. Try Mono fonts (IBM Plex Mono)
    mono_reg = os.path.abspath(os.path.join("apps", "api", "fonts", "IBMPlexMono-Regular.ttf"))
    mono_bld = os.path.abspath(os.path.join("apps", "api", "fonts", "IBMPlexMono-Bold.ttf"))
    mono_med = os.path.abspath(os.path.join("apps", "api", "fonts", "IBMPlexMono-Medium.ttf"))
    
    if os.path.exists(mono_reg) and os.path.exists(mono_bld):
        try:
            pdfmetrics.registerFont(TTFont("IBMPlexMono-Regular", mono_reg))
            pdfmetrics.registerFont(TTFont("IBMPlexMono-Bold", mono_bld))
            FONT_MONO = "IBMPlexMono-Regular"
            FONT_MONO_BOLD = "IBMPlexMono-Bold"
        except Exception:
            pass
            
    # 2. Try Sans fonts (Segoe UI or DejaVu or Helvetica)
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

# --- Design Tokens ---
PAGE_WIDTH, PAGE_HEIGHT = A4  # 595.27 x 841.89 pt
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

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        # Draw top subtle rule and case reference
        self.saveState()
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(MARGIN_LEFT, PAGE_HEIGHT - 48, MARGIN_RIGHT, PAGE_HEIGHT - 48)
        
        # Top brand & case label
        self.setFont(FONT_BOLD, 8)
        self.setFillColor(COLOR_ACCENT_ORANGE)
        self.drawString(MARGIN_LEFT, PAGE_HEIGHT - 42, "DECEPTRIX")
        
        self.setFont(FONT_MONO, 7.5)
        self.setFillColor(COLOR_MUTED_TEXT)
        case_txt = f"CASE: {self.job_data.get('id', '')[:24]}...  |  FORENSIC INTELLIGENCE DOSSIER"
        self.drawRightString(MARGIN_RIGHT, PAGE_HEIGHT - 42, case_txt)
        
        # Bottom Footer
        self.line(MARGIN_LEFT, 45, MARGIN_RIGHT, 45)
        self.setFont(FONT_REGULAR, 7.5)
        self.setFillColor(COLOR_MUTED_TEXT)
        self.drawString(MARGIN_LEFT, 32, "DECEPTRIX v2.0  ·  Tamper-Evident Multi-Modal Forensic Record  ·  SIH 2026")
        
        page_num_str = f"Page {self._pageNumber} of {page_count}"
        self.setFont(FONT_MONO, 7.5)
        self.drawRightString(MARGIN_RIGHT, 32, page_num_str)
        self.restoreState()

print("NumberedCanvas initialized successfully.")
