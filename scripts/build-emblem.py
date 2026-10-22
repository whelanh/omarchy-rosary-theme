#!/usr/bin/python3
"""Draw the Rosary emblem: unlock.png, the Plymouth logo and the fastfetch mark.

The emblem is a gold crucifix in a thin ring, with a quiet ivory corpus and a
small INRI scroll. Everything is vector, rendered with rsvg-convert, so the
same drawing serves a 512 px lock-screen badge and a 20-line terminal logo.

    ./build-emblem.py
"""
from __future__ import annotations

import io
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

INK = "#0b0d15"
IVORY = "#efe6d4"
PARCHMENT = "#d8cbb0"
GOLD = "#d9b45b"
GOLD_PALE = "#f2dfa4"
GOLD_DEEP = "#a67c2e"
OXBLOOD = "#8f3f48"

SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
<defs>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{GOLD_PALE}"/>
    <stop offset="0.38" stop-color="{GOLD}"/>
    <stop offset="0.72" stop-color="{GOLD_DEEP}"/>
    <stop offset="1" stop-color="{GOLD_PALE}"/>
  </linearGradient>
  <linearGradient id="goldv" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{GOLD_PALE}"/>
    <stop offset="0.45" stop-color="{GOLD}"/>
    <stop offset="1" stop-color="{GOLD_DEEP}"/>
  </linearGradient>
  <linearGradient id="ivory" x1="0" y1="0" x2="0.4" y2="1">
    <stop offset="0" stop-color="#f7f0e2"/>
    <stop offset="1" stop-color="{PARCHMENT}"/>
  </linearGradient>
  <radialGradient id="halo">
    <stop offset="0" stop-color="{GOLD}" stop-opacity="0.30"/>
    <stop offset="0.68" stop-color="{GOLD}" stop-opacity="0.06"/>
    <stop offset="1" stop-color="{GOLD}" stop-opacity="0"/>
  </radialGradient>
  <filter id="soft" x="-40%" y="-40%" width="180%" height="180%">
    <feDropShadow dx="0" dy="4" stdDeviation="7" flood-color="#000" flood-opacity="0.55"/>
  </filter>
  <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="5"/>
  </filter>
</defs>

<!-- halo and ring -->
<circle cx="256" cy="256" r="246" fill="url(#halo)"/>
<circle cx="256" cy="256" r="220" fill="none" stroke="{GOLD}" stroke-width="2" opacity="0.42"/>
<circle cx="256" cy="256" r="212" fill="none" stroke="{GOLD_PALE}" stroke-width="1" opacity="0.18"/>
<g opacity="0.8" fill="{GOLD}">
  <circle cx="256" cy="36" r="4"/>
  <circle cx="256" cy="476" r="4"/>
  <circle cx="36" cy="256" r="4"/>
  <circle cx="476" cy="256" r="4"/>
</g>

<g filter="url(#soft)">
  <!-- cross beams, with flared ends -->
  <path d="M242 118 h28 v300 h-28 z" fill="url(#goldv)" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
  <path d="M156 196 h200 v28 h-200 z" fill="url(#gold)" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>
  <path d="M242 106 h28 v20 h-28 z" fill="url(#goldv)" stroke="{INK}" stroke-width="4"/>
  <path d="M148 196 h16 v28 h-16 z" fill="url(#gold)" stroke="{INK}" stroke-width="4"/>
  <path d="M348 196 h16 v28 h-16 z" fill="url(#gold)" stroke="{INK}" stroke-width="4"/>
  <path d="M242 406 h28 v24 h-28 z" fill="url(#goldv)" stroke="{INK}" stroke-width="4"/>

  <!-- INRI scroll -->
  <path d="M204 78 q52 -16 104 0 l-8 30 q-44 -12 -88 0 z" fill="url(#gold)" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>
  <text x="256" y="101" text-anchor="middle" font-family="Noto Serif" font-size="18"
        letter-spacing="2.5" fill="{INK}">INRI</text>

  <!-- corpus: a quiet ivory figure, drawn in front of the beams -->
  <circle cx="256" cy="173" r="35" fill="url(#halo)"/>
  <g stroke="{INK}" stroke-width="4.2" stroke-linejoin="round" stroke-linecap="round" fill="url(#ivory)">
    <circle cx="256" cy="173" r="16"/>
    <path d="M249 188 h14 v16 h-14 z"/>
    <!-- arms along the crossbar, wrists turned down -->
    <path d="M206 212 Q228 205 247 207 L247 222 Q228 220 208 230 Z"/>
    <path d="M306 212 Q284 205 265 207 L265 222 Q284 220 304 230 Z"/>
    <!-- torso -->
    <path d="M243 203 Q256 198 269 203 L264 286 Q256 292 248 286 Z"/>
    <!-- legs -->
    <path d="M248 312 Q246 344 232 372 L244 379 Q256 351 256 322 Z"/>
    <path d="M264 312 Q266 344 280 372 L268 379 Q256 351 256 322 Z"/>
    <!-- feet, crossed at the ankles -->
    <path d="M229 369 q-9 4 -5 12 h22 v-9 z"/>
    <path d="M283 369 q9 4 5 12 h-22 v-9 z"/>
  </g>
  <!-- loincloth -->
  <path d="M240 276 Q256 270 272 276 L277 317 Q256 324 235 317 Z"
        fill="url(#gold)" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>
  <!-- wounds -->
  <g fill="{OXBLOOD}">
    <circle cx="208" cy="220" r="3.6"/><circle cx="304" cy="220" r="3.6"/>
    <circle cx="240" cy="374" r="3.4"/><circle cx="272" cy="374" r="3.4"/>
    <path d="M252 326 q4 5 8 0" fill="none" stroke="{OXBLOOD}" stroke-width="2.6"/>
  </g>
</g>
</svg>
"""


def rsvg(svg: str, size: int) -> Image.Image:
    png = subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size)],
        input=svg.encode(), capture_output=True, check=True,
    ).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


def fastfetch_logo(img: Image.Image, rows: int = 20) -> str:
    """Half-block ANSI art, using the same ▀ trick as Omarchy's own logos."""
    width = max(1, round(img.width / img.height * rows * 2))
    small = img.resize((width, rows * 2), Image.LANCZOS)
    out = []
    for y in range(0, small.height, 2):
        line = []
        for x in range(small.width):
            top = small.getpixel((x, y))
            bottom = small.getpixel((x, y + 1))
            if top[3] < 48 and bottom[3] < 48:
                line.append(" ")
                continue
            # composite on ink so partial alpha reads correctly
            def onink(p):
                a = p[3] / 255
                return tuple(round(p[i] * a + (11, 13, 21)[i] * (1 - a)) for i in range(3))
            t, b = onink(top), onink(bottom)
            line.append(
                f"\x1b[38;2;{t[0]};{t[1]};{t[2]}m"
                f"\x1b[48;2;{b[0]};{b[1]};{b[2]}m▀\x1b[0m"
            )
        out.append("".join(line).rstrip())
    return "\n".join(out) + "\n"


def main():
    img = rsvg(SVG, 512)
    img.save(ROOT / "unlock.png", optimize=True)
    print("wrote unlock.png")

    # Terminal badge: 20 rows of half blocks, transparent background.
    logo = fastfetch_logo(img, rows=20)
    (ROOT / "extras" / "fastfetch-logo.txt").write_text(logo)
    print(f"wrote extras/fastfetch-logo.txt ({len(logo.splitlines())} lines)")


if __name__ == "__main__":
    main()
