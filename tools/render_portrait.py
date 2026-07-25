#!/usr/bin/env python3
"""Stage 3b — Map cleaned photo pixels to ASCII characters and render as animated SVG.

Downscales the cleaned image to a small character grid and picks a glyph per cell
based on brightness. Animates a top-to-bottom reveal with staggered row timing.

Usage:
    python tools/render_portrait.py
    # reads assets/photo-ready.png, writes portrait.svg
"""
import math
import sys
from pathlib import Path

import cv2
import numpy as np

# Light (empty) -> dark (dense)
GLYPHS = " '.,:;~+*xXO#"
ACCENT = "#a5d8ff"
BG_COLOR = "#0d1117"
COLS = 48
FONT_SIZE = 11
ROW_STAGGER_MS = 40
REVEAL_DURATION_MS = 600


def brightness_to_char(val: float) -> str:
    idx = int(val / 255 * (len(GLYPHS) - 1))
    return GLYPHS[min(idx, len(GLYPHS) - 1)]


def main():
    img_path = Path(__file__).resolve().parent.parent / "assets" / "photo-ready.png"
    if not img_path.exists():
        sys.exit(f"Photo not found at {img_path}\nRun: python tools/clean_photo.py <your-photo.jpg>")

    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit("Failed to read image")

    h, w = img.shape
    rows = int(COLS * (h / w) * 0.5)  # ~0.5 aspect ratio correction for terminal chars
    cell_w = w / COLS
    cell_h = h / rows

    grid = []
    for r in range(rows):
        row = []
        for c in range(COLS):
            y1, y2 = int(r * cell_h), int((r + 1) * cell_h)
            x1, x2 = int(c * cell_w), int((c + 1) * cell_w)
            patch = img[y1:y2, x1:x2]
            avg = float(patch.mean())
            row.append(brightness_to_char(avg))
        grid.append("".join(row))

    # Calculate SVG dimensions
    char_w = FONT_SIZE * 0.6
    svg_w = int(COLS * char_w) + 20
    svg_h = int(rows * FONT_SIZE * 1.3) + 20

    # Build animated SVG
    total_ms = ROW_STAGGER_MS * rows + REVEAL_DURATION_MS

    style_lines = [
        f"  <style>",
        f"    text {{ font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: {FONT_SIZE}px; fill: {ACCENT}; }}",
        f"    @media (prefers-reduced-motion) {{ .row {{ animation: none !important; opacity: 1; }} }}",
    ]

    text_els = []
    for i, line in enumerate(grid):
        cls = f"r{i}"
        delay = i * ROW_STAGGER_MS
        style_lines.append(
            f"    .{cls} {{ animation: reveal {REVEAL_DURATION_MS}ms {delay}ms both; }}"
        )
        y = 14 + i * FONT_SIZE * 1.3
        text_els.append(f'  <text class="row {cls}" x="10" y="{y:.1f}">{_escape(line)}</text>')

    style_lines.append(
        f"    @keyframes reveal {{ from {{ clip-path: inset(0 100% 0 0); }} to {{ clip-path: inset(0 0 0 0); }} }}"
    )
    style_lines.append("  </style>")

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}">
{chr(10).join(style_lines)}
{chr(10).join(text_els)}
</svg>
"""
    out = Path(__file__).resolve().parent.parent / "portrait.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out} ({COLS}x{rows} chars)")


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    main()
