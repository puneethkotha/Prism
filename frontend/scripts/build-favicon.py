#!/usr/bin/env python3
"""Build favicons: white Intona mark on a purple circle (matches Prism brand)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "public" / "Intona.png"

# Tailwind `prism-600` — solid circle behind the glyph
PURPLE_BG = (67, 71, 237, 255)


def crop_to_alpha(im: Image.Image) -> Image.Image:
    alpha = im.split()[3]
    bbox = alpha.getbbox()
    if not bbox:
        return im
    return im.crop(bbox)


def to_white_glyph(im: Image.Image) -> Image.Image:
    """Keep alpha; set RGB to white (purple → white)."""
    im = im.convert("RGBA")
    _, _, _, a = im.split()
    w = Image.new("L", im.size, 255)
    return Image.merge("RGBA", (w, w, w, a))


def make_icon(size: int, *, inner_ratio: float) -> Image.Image:
    im = Image.open(SRC).convert("RGBA")
    im = crop_to_alpha(im)
    im = to_white_glyph(im)
    inner = max(1, int(size * inner_ratio))
    thumb = im.copy()
    thumb.thumbnail((inner, inner), Image.Resampling.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(out)
    draw.ellipse((0, 0, size - 1, size - 1), fill=PURPLE_BG)

    x = (size - thumb.width) // 2
    y = (size - thumb.height) // 2
    out.paste(thumb, (x, y), thumb)
    return out


def main() -> None:
    public = ROOT / "public"
    make_icon(32, inner_ratio=0.58).save(public / "favicon-32.png", optimize=True)
    make_icon(48, inner_ratio=0.58).save(public / "favicon-48.png", optimize=True)
    make_icon(180, inner_ratio=0.56).save(public / "apple-touch-icon.png", optimize=True)
    print("Wrote favicon-32.png, favicon-48.png, apple-touch-icon.png")


if __name__ == "__main__":
    main()
