"""
One-time script to generate edgar-frontend/og-image.png
Run from edgar-api/: .venv/bin/python generate_og_image.py
"""

from PIL import Image, ImageDraw, ImageFont
import pathlib

W, H = 1200, 630
OUT = pathlib.Path(__file__).parent.parent / "edgar-frontend" / "og-image.png"

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = (15,  17,  23)
SURFACE = (26,  29,  39)
BORDER  = (46,  51,  82)
TEXT    = (232, 234, 246)
MUTED   = (139, 144, 184)
ACCENT  = (79,  142, 247)
RED     = (248, 113, 113)
RED_BG  = (45,  22,  22)
YELLOW  = (251, 191,  36)
YEL_BG  = (45,  38,  15)
GREEN   = (52,  211, 153)

# ── Fonts ─────────────────────────────────────────────────────────────────────
def load(path, size):
    return ImageFont.truetype(path, size)

FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
try:
    f72 = load(FONT, 72)
    f52 = load(FONT, 52)
    f38 = load(FONT, 38)
    f28 = load(FONT, 28)
    f22 = load(FONT, 22)
    f18 = load(FONT, 18)
    f15 = load(FONT, 15)
    f13 = load(FONT, 13)
except Exception as e:
    raise SystemExit(f"Font not found: {e}")

# ── Canvas ────────────────────────────────────────────────────────────────────
img  = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

def rect(x1, y1, x2, y2, fill=None, outline=None, radius=0):
    if radius:
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline)
    else:
        draw.rectangle([x1, y1, x2, y2], fill=fill, outline=outline)

def text(s, x, y, font, fill, anchor="la"):
    draw.text((x, y), s, font=font, fill=fill, anchor=anchor)

# ── Left accent strip ─────────────────────────────────────────────────────────
rect(0, 0, 6, H, fill=ACCENT)

# ── Logo mark ─────────────────────────────────────────────────────────────────
rect(72, 78, 140, 146, fill=ACCENT, radius=14)
text("E", 106, 112, f52, (255, 255, 255), anchor="mm")

# ── Brand name ───────────────────────────────────────────────────────────────
text("EdgarWolf", 158, 78, f52, TEXT)

# ── Separator under logo ──────────────────────────────────────────────────────
rect(72, 168, 660, 170, fill=BORDER)

# ── Main headline ─────────────────────────────────────────────────────────────
text("Know what's in the filing",  72, 198, f38, TEXT)
text("before the market does.",    72, 248, f38, TEXT)

# ── Sub-copy ──────────────────────────────────────────────────────────────────
text("Z-score anomaly flags, Filing Stress Scores, and 8-quarter", 72, 312, f22, MUTED)
text("financial trends pulled live from SEC EDGAR. Free to start.", 72, 342, f22, MUTED)

# ── Feature pills ─────────────────────────────────────────────────────────────
pills = ["⚑  Exception Flags", "◈  Filing Stress Score", "▨  8-Quarter Trends"]
px = 72
for label in pills:
    bbox = draw.textbbox((0, 0), label, font=f18)
    pw = bbox[2] - bbox[0] + 32
    rect(px, 400, px + pw, 434, fill=SURFACE, outline=BORDER, radius=17)
    text(label, px + 16, 417, f18, ACCENT, anchor="lm")
    px += pw + 14

# ── URL ───────────────────────────────────────────────────────────────────────
text("edgarwolf.com", 72, 575, f22, ACCENT)

# ── Right panel ───────────────────────────────────────────────────────────────
PX1, PY1, PX2, PY2 = 718, 50, 1148, 578
rect(PX1, PY1, PX2, PY2, fill=SURFACE, outline=BORDER, radius=14)

cx = PX1 + 28   # left margin inside panel

# Company header
text("$GIS  ·  General Mills", cx, PY1 + 32, f22, TEXT)

rect(PX1 + 28, PY1 + 66, PX2 - 28, PY1 + 68, fill=BORDER)

# Filing Stress Score block
text("FILING STRESS SCORE", cx, PY1 + 82, f13, MUTED)
text("100", cx, PY1 + 110, f72, TEXT)

# /100
text("/ 100", cx + 122, PY1 + 152, f22, MUTED)

# ELEVATED badge
rect(cx, PY1 + 165, cx + 110, PY1 + 189, fill=RED_BG, outline=RED, radius=10)
text("ELEVATED", cx + 55, PY1 + 177, f13, RED, anchor="mm")

rect(cx, PY1 + 202, PX2 - 28, PY1 + 204, fill=BORDER)

# Exception Flags header
text("EXCEPTION FLAGS", cx, PY1 + 214, f13, MUTED)

flags = [
    ("Gross Margin %",       "3.1σ below avg", RED,    RED_BG),
    ("Operating Margin %",   "2.8σ below avg", RED,    RED_BG),
    ("Revenue Growth YoY %", "3.3σ below avg", YELLOW, YEL_BG),
]

fy = PY1 + 234
for label, note, color, bg in flags:
    rect(cx, fy, cx + 6, fy + 36, fill=color, radius=3)
    text(label, cx + 16, fy + 6,  f18, TEXT)
    text(note,  cx + 16, fy + 24, f15, color)
    fy += 48

rect(cx, fy + 4, PX2 - 28, fy + 6, fill=BORDER)

# Revenue trend mini chart
text("REVENUE TREND (8Q)", cx, fy + 16, f13, MUTED)

bars = [5.2, 5.0, 4.9, 4.8, 4.6, 4.4, 4.2, 3.8]
bw, bg_h = 34, 60
bx = cx
by_base = fy + 96
max_val = max(bars)
for i, v in enumerate(bars):
    bh = int(v / max_val * bg_h)
    shade = ACCENT if i == len(bars) - 1 else (60, 100, 180)
    rect(bx + i * (bw + 6), by_base - bh, bx + i * (bw + 6) + bw, by_base,
         fill=shade, radius=3)

text("Revenue $B (quarterly)", cx, by_base + 10, f13, MUTED)

# ── Save ──────────────────────────────────────────────────────────────────────
img.save(OUT, "PNG", optimize=True)
print(f"Saved → {OUT}  ({W}×{H}px)")
