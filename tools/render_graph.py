#!/usr/bin/env python3
"""Step 5b — Draw the contribution grid as an animated SVG.

Renders 52 weeks x 7 days as rounded squares with a custom color ramp.
Animates squares in by column (week) for a wave-like reveal.

Usage:
    python tools/render_graph.py
    # reads assets/contributions.json, writes graph.svg
"""
import json
import math
import os
import sys
from pathlib import Path

# Custom color ramp — matches portrait accent
LEVELS = ["#1a1a2e", "#16537e", "#1c7ed6", "#4dabf7", "#a5d8ff"]

CELL = 11
GAP = 3
PITCH = CELL + GAP
MX = 28
MTOP = 26
MBOT = 56
MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

COL_STAGGER_MS = 30
REVEAL_DURATION_MS = 400


def main():
    json_path = Path(__file__).resolve().parent.parent / "assets" / "contributions.json"
    if not json_path.exists():
        sys.exit(f"Run pull_contributions.py first to create {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    days = data["days"]

    # Build week grid (columns) from flat day list
    # GitHub's HTML gives us 52-53 weeks, 7 days each
    weeks = []
    current_week = []
    for d in days:
        current_week.append(d)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
    if current_week:
        while len(current_week) < 7:
            current_week.append({"level": 0, "count": 0})
        weeks.append(current_week)

    ncols = len(weeks)
    nrows = 7

    # Month labels
    month_labels = []
    seen_month = None
    for c, week in enumerate(weeks):
        first_date = week[0].get("date", "")
        if first_date:
            parts = first_date.split("-")
            if len(parts) == 3:
                month = int(parts[1])
                if month != seen_month:
                    month_labels.append((c, MONTHS[month]))
                    seen_month = month

    # SVG dimensions
    svg_w = MX * 2 + ncols * PITCH - GAP
    svg_h = MTOP + nrows * PITCH - GAP + MBOT

    # Build animated elements
    style_lines = [
        "  <style>",
        "    rect.cell { rx: 2.5; ry: 2.5; }",
        f"    text {{ font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace; font-size: 9.5px; fill: #7d8590; }}",
        "    @media (prefers-reduced-motion) { .cell { animation: none !important; opacity: 1; } }",
    ]
    rects = []
    cell_idx = 0

    for c, week in enumerate(weeks):
        for r, day in enumerate(week):
            x = MX + c * PITCH
            y = MTOP + r * PITCH
            level = day.get("level", 0)
            fill = LEVELS[min(level, len(LEVELS) - 1)]
            count = day.get("count", 0)
            date_str = day.get("date", "")
            delay = c * COL_STAGGER_MS
            cls = f"cell{c}_{r}"

            style_lines.append(
                f"    .{cls} {{ animation: reveal {REVEAL_DURATION_MS}ms {delay}ms both; }}"
            )

            # Tooltip via <title>
            tooltip = f"{count} contribution{'s' if count != 1 else ''} on {date_str}" if date_str else ""
            rects.append(
                f'  <rect class="cell {cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{fill}">'
                f'<title>{tooltip}</title></rect>'
            )
            cell_idx += 1

    style_lines.append(
        "    @keyframes reveal { from { opacity: 0; transform: scale(0.3); } to { opacity: 1; transform: scale(1); } }"
    )
    style_lines.append("  </style>")

    # Month labels
    labels = []
    for c, label in month_labels:
        x = MX + c * PITCH
        labels.append(f'  <text x="{x}" y="14">{label}</text>')

    # Day labels
    day_labels = ["Mon", "Wed", "Fri"]
    day_indices = [0, 2, 4]
    for label, idx in zip(day_labels, day_indices):
        y = MTOP + idx * PITCH + CELL - 1
        labels.append(f'  <text x="0" y="{y}">{label}</text>')

    # Legend + stats
    ly = MTOP + 7 * PITCH + 12
    legend_x = MX
    labels.append(f'  <text x="{legend_x}" y="{ly + 9}">Less</text>')
    for i in range(5):
        lx = legend_x + 30 + i * (CELL + 3)
        labels.append(f'  <rect x="{lx}" y="{ly}" width="{CELL}" height="{CELL}" rx="2.5" fill="{LEVELS[i]}"/>')
    labels.append(f'  <text x="{legend_x + 30 + 5 * (CELL + 3) + 8}" y="{ly + 9}">More</text>')

    # Stats line
    total = data.get("total_contributions", 0)
    current = data.get("current_streak", 0)
    longest = data.get("longest_streak", 0)
    stats = f"{total} contributions · {current} day streak · best day: {data.get('busiest_day', {}).get('day', 'N/A')}"
    labels.append(f'  <text x="{MX}" y="{ly + 28}" fill="#e6edf3">{stats}</text>')

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}">
{chr(10).join(style_lines)}
{chr(10).join(rects)}
{chr(10).join(labels)}
</svg>
"""
    out = Path(__file__).resolve().parent.parent / "graph.svg"
    out.write_text(svg, encoding="utf-8")
    print(f"Wrote {out} ({ncols} weeks, {ncols * 7} cells)")


if __name__ == "__main__":
    main()
