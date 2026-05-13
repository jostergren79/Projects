"""
Generate edgar-frontend/favicon.png (192x192) and favicon-32.png (32x32).
Run from edgar-api/: .venv/bin/python generate_favicon.py
"""

from PIL import Image, ImageDraw, ImageFont
import pathlib

OUT_DIR = pathlib.Path(__file__).parent.parent / "edgar-frontend"
BG     = (15, 17, 23)
ACCENT = (79, 142, 247)
WHITE  = (255, 255, 255)
FONT   = "/System/Library/Fonts/HelveticaNeue.ttc"


def make_favicon(size, font_size, out_name):
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = size // 5
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG)
    try:
        font = ImageFont.truetype(FONT, font_size)
    except Exception as e:
        raise SystemExit(f"Font not found: {e}")
    draw.text((size // 2, size // 2), "EW", font=font, fill=ACCENT, anchor="mm")
    out = OUT_DIR / out_name
    img.save(out, "PNG", optimize=True)
    print(f"Saved → {out}  ({size}×{size}px)")


make_favicon(192, 88, "favicon.png")
make_favicon(32,  16, "favicon-32.png")
