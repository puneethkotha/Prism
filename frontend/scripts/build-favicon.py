#!/usr/bin/env python3
"""Composite Intona.png onto a light tile so the favicon reads on dark browser tabs."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "public" / "Intona.png"


def crop_to_alpha(im: Image.Image) -> Image.Image:
    alpha = im.split()[3]
    bbox = alpha.getbbox()
    if not bbox:
        return im
    return im.crop(bbox)


def make_favicon(size: int, *, corner_radius: int | None = None) -> Image.Image:
    im = Image.open(SRC).convert("RGBA")
    im = crop_to_alpha(im)
    inner = max(1, int(size * 0.72))
    thumb = im.copy()
    thumb.thumbnail((inner, inner), Image.Resampling.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    r = corner_radius if corner_radius is not None else max(size // 5, 3)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=r, fill=255)

    # Light tile (white) — strong contrast on dark tab UI
    tile = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    out = Image.composite(tile, out, mask)

    x = (size - thumb.width) // 2
    y = (size - thumb.height) // 2
    out.paste(thumb, (x, y), thumb)
    return out


def main() -> None:
    public = ROOT / "public"
    make_favicon(32).save(public / "favicon-32.png", optimize=True)
    make_favicon(48).save(public / "favicon-48.png", optimize=True)
    make_favicon(180).save(public / "apple-touch-icon.png", optimize=True)
    print("Wrote favicon-32.png, favicon-48.png, apple-touch-icon.png")


if __name__ == "__main__":
    main()
