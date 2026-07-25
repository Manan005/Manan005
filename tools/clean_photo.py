#!/usr/bin/env python3
"""Stage 3a — Clean up a source photo for ASCII portrait conversion.

Steps:
  1. Remove background with rembg
  2. Even out lighting with OpenCV CLAHE
  3. Drop onto a white canvas

Usage:
    python tools/clean_photo.py my-photo.jpg
    # writes assets/photo-ready.png
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python clean_photo.py <input.jpg>")

    src = Path(sys.argv[1])
    if not src.exists():
        sys.exit(f"File not found: {src}")

    out_dir = Path(__file__).resolve().parent.parent / "assets"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "photo-ready.png"

    # --- Step 1: Remove background ---
    print("Removing background...")
    with open(src, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    img_nobg = Image.open(__import__("io").BytesIO(output_bytes)).convert("RGBA")

    # --- Step 2: CLAHE on the luminance channel ---
    print("Applying CLAHE (adaptive histogram equalization)...")
    img_bgr = cv2.cvtColor(np.array(img_nobg), cv2.COLOR_RGBA2BGR)
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0]

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(l_channel)
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    # --- Step 3: Composite onto white canvas ---
    print("Placing on white canvas...")
    alpha = np.array(img_nobg)[:, :, 3] / 255.0
    white = np.full_like(enhanced, 255)
    blended = (enhanced * alpha[:, :, None] + white * (1 - alpha[:, :, None])).astype(np.uint8)

    result = Image.fromarray(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB))
    result.save(out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
