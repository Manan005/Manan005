#!/usr/bin/env python3
"""Step 5a — Pull GitHub contributions without an OAuth token.

Fetches the plain HTML fragment of the contribution calendar from:
    https://github.com/users/<username>/contributions

Parses day cells and saves counts plus derived stats.

Usage:
    python tools/pull_contributions.py
    # writes assets/contributions.json
"""
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import httpx
from lxml import html

USERNAME = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Manan005"
URL = f"https://github.com/users/{USERNAME}/contributions"


def main():
    print(f"Fetching contributions from {URL} ...")
    resp = httpx.get(URL, follow_redirects=True, timeout=30, headers={
        "User-Agent": f"contribution-graph/{USERNAME}"
    })
    resp.raise_for_status()

    tree = html.fromstring(resp.text)

    # Each day cell: <td class="ContributionCalendar-day" ... data-date="YYYY-MM-DD" data-level="0-4">...</td>
    cells = tree.cssselect("td.ContributionCalendar-day")
    days = []
    for cell in cells:
        date_str = cell.get("data-date")
        level = cell.get("data-level")
        if not date_str or level is None:
            continue
        # Extract count from tooltip or inner text
        count_text = cell.text_content().strip()
        count = 0
        if "contribution" in count_text:
            m = re.search(r"(\d+)", count_text)
            if m:
                count = int(m.group(1))
        days.append({
            "date": date_str,
            "level": int(level),
            "count": count,
        })

    if not days:
        sys.exit("No contribution cells found — page structure may have changed.")

    # Compute stats
    counts = [d["count"] for d in days]
    total = sum(counts)

    # Current streak (from today backwards)
    today = datetime.now(timezone.utc).date()
    current_streak = 0
    for d in reversed(days):
        dt = datetime.fromisoformat(d["date"]).date()
        if d["count"] > 0 and dt <= today:
            current_streak += 1
        else:
            break

    # Longest streak
    longest_streak = 0
    streak = 0
    for d in days:
        if d["count"] > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    # Busiest day of week
    dow_counts = Counter()
    for d in days:
        dt = datetime.fromisoformat(d["date"])
        dow_counts[dt.strftime("%A")] += d["count"]
    busiest_day = dow_counts.most_common(1)[0] if dow_counts else ("N/A", 0)

    result = {
        "username": USERNAME,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "busiest_day": {"day": busiest_day[0], "count": busiest_day[1]},
        "days": days,
    }

    out_dir = Path(__file__).resolve().parent.parent / "assets"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "contributions.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"  Total: {total} | Current streak: {current_streak} | Longest: {longest_streak}")


if __name__ == "__main__":
    main()
