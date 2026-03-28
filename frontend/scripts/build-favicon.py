#!/usr/bin/env python3
"""Build favicons: purple Intona mark → white on transparent (good on dark tabs)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "public" / "Intona.png"

# Homescreen icon: dark tile so white glyph stays visible on light iOS backgrounds
APPLE_BG = (31, 41, 55, 255)  # slate-800


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


def make_tab_favicon(size: int) -> Image.Image:
    im = Image.open(SRC).convert("RGBA")
    im = crop_to_alpha(im)
    im = to_white_glyph(im)
    inner = max(1, int(size * 0.78))
    thumb = im.copy()
    thumb.thumbnail((inner, inner), Image.Resampling.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - thumb.width) // 2
    y = (size - thumb.height) // 2
    out.paste(thumb, (x, y), thumb)
    return out


def make_apple_touch_icon(size: int) -> Image.Image:
    """White mark on dark rounded square (readable on light springboard)."""
    im = Image.open(SRC).convert("RGBA")
    im = crop_to_alpha(im)
    im = to_white_glyph(im)
    inner = max(1, int(size * 0.62))
    thumb = im.copy()
    thumb.thumbnail((inner, inner), Image.Resampling.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    r = max(size // 5, 12)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=r, fill=255)

    tile = Image.new("RGBA", (size, size), APPLE_BG)
    out = Image.composite(tile, out, mask)

    x = (size - thumb.width) // 2
    y = (size - thumb.height) // 2
    out.paste(thumb, (x, y), thumb)
    return out


def main() -> None:
    public = ROOT / "public"
    make_tab_favicon(32).save(public / "favicon-32.png", optimize=True)
    make_tab_favicon(48).save(public / "favicon-48.png", optimize=True)
    make_apple_touch_icon(180).save(public / "apple-touch-icon.png", optimize=True)
    print("Wrote favicon-32.png, favicon-48.png, apple-touch-icon.png")


if __name__ == "__main__":
    main()
