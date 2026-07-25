#!/usr/bin/env python3
"""Step 4 — Render a terminal-style info panel as animated SVG.

Each row appears with a delay-and-fade, like a terminal printing line by line.

Usage:
    python tools/render_panel.py           # writes sysinfo.svg
    PREVIEW=1 python tools/render_panel.py  # static preview (no animation)
"""
import os
import sys
from pathlib import Path

ROWS = [
    ("Identity", "Adaptable Full-Stack Engineer"),
    ("Passion", "Building Products From the Ground Up"),
    ("Superpower", "Aggressively learning whatever it takes to drive growth"),
    ("Mission", "Demystifying AI literacy & developer tools"),
]

LABEL_COLOR = "#7d8590"
VALUE_COLOR = "#e6edf3"
CURSOR_COLOR = "#a5d8ff"
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
FONT_SIZE = 13
LINE_HEIGHT = 28
PADDING = 20
HEADER_HEIGHT = 34
ROW_DELAY_MS = 180
TYPE_DURATION_MS = 300
PREVIEW = os.environ.get("PREVIEW", "0") == "1"


def main():
    max_label = max(len(k) for k, _ in ROWS)
    max_value = max(len(v) for _, v in ROWS)
    char_w = FONT_SIZE * 0.6
    svg_w = int((max_label + max_value + 4) * char_w) + PADDING * 2
    svg_h = PADDING + HEADER_HEIGHT + len(ROWS) * LINE_HEIGHT + PADDING

    content_lines = []

    # Header bar
    content_lines.append(
        f'<rect x="0" y="0" width="{svg_w}" height="{HEADER_HEIGHT}" rx="8" ry="8" fill="#161b22" />'
    )
    # Dots
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        cx = PADDING + i * 20
        content_lines.append(f'<circle cx="{cx}" cy="{HEADER_HEIGHT // 2}" r="5" fill="{color}" />')
    content_lines.append(
        f'<text x="{svg_w // 2}" y="{HEADER_HEIGHT // 2 + 4}" text-anchor="middle" '
        f'font-family="ui-monospace, monospace" font-size="11" fill="{LABEL_COLOR}">sysinfo</text>'
    )

    # Rows
    for i, (label, value) in enumerate(ROWS):
        y = PADDING + HEADER_HEIGHT + i * LINE_HEIGHT + FONT_SIZE
        delay = i * ROW_DELAY_MS

        label_text = f'<tspan fill="{LABEL_COLOR}">{label}: </tspan>'
        value_text = f'<tspan fill="{VALUE_COLOR}">{_escape(value)}</tspan>'

        if PREVIEW:
            opacity_attr = ""
        else:
            opacity_attr = (
                f' opacity="0"'
                f' style="animation: fadeRow {TYPE_DURATION_MS}ms {delay}ms both;"'
            )

        content_lines.append(
            f'<text x="{PADDING}" y="{y}" '
            f'font-family="ui-monospace, monospace" font-size="{FONT_SIZE}"'
            f'{opacity_attr}>{label_text}{value_text}</text>'
        )

        # Cursor blink at end of value
        if not PREVIEW:
            cursor_x = PADDING + (len(label) + 2 + len(value)) * char_w
            content_lines.append(
                f'<rect x="{cursor_x:.0f}" y="{y - FONT_SIZE}" width="{char_w:.0f}" height="{FONT_SIZE + 2}" '
                f'fill="{CURSOR_COLOR}" opacity="0" style="animation: blink 1s {delay + TYPE_DURATION_MS}ms 3;">'
                f'</rect>'
            )

    # Style block
    if PREVIEW:
        style = ""
    else:
        style = f"""  <style>
    text {{ font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; }}
    @keyframes fadeRow {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes blink {{ 0%,100% {{ opacity: 0; }} 50% {{ opacity: 1; }} }}
    @media (prefers-reduced-motion) {{ * {{ animation: none !important; opacity: 1; }} }}
  </style>"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}">
{style}
  <rect width="{svg_w}" height="{svg_h}" rx="8" fill="{BG_COLOR}" stroke="{BORDER_COLOR}"/>
{chr(10).join('  ' + l for l in content_lines)}
</svg>
"""
    out = Path(__file__).resolve().parent.parent / "sysinfo.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out}")


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    main()
