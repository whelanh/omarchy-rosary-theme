#!/usr/bin/python3
"""Draw the Rosary emblem: unlock.png, the Plymouth logo and the fastfetch mark.

The emblem is a gold crucifix in a thin ring, with a quiet ivory corpus and a
small INRI scroll. Everything is vector, rendered with rsvg-convert, so the
same drawing serves a 512 px lock-screen badge and a 20-line terminal logo.

The terminal mark is not the badge shrunk down. At 20 rows the halo, glow,
drop shadow and lettering turn into mud, and the badge's framing leaves the
cross only a dozen pixels wide. TERMINAL_SVG redraws the same crucifix for the
small canvas: no halo or shadow, a cross that fills the frame, and a bolder
corpus. The ring is drawn separately in braille (TERMINAL_RING_SVG), which
gives the circle 80×80 dots instead of 40×40 half-block pixels; at that size
it reads as a string of rosary beads rather than a jagged 1 px outline.

    ./build-emblem.py
"""
from __future__ import annotations

import io
import math
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

INK = "#0b0d15"
INK_RGB = (0x0B, 0x0D, 0x15)
IVORY = "#efe6d4"
PARCHMENT = "#d8cbb0"
GOLD = "#d9b45b"
GOLD_PALE = "#f2dfa4"
GOLD_DEEP = "#a67c2e"
OXBLOOD = "#8f3f48"

DEFS = f"""<defs>
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
  <!-- At 40 px the pale top of #goldv would swallow the ivory head, so the
       terminal cross keeps its beams in the mid-gold. -->
  <linearGradient id="gold-small" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{GOLD}"/>
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
</defs>"""

SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
{DEFS}

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

# The fastfetch mark, drawn directly for the 40×40 pixel canvas that 20 rows
# of half blocks gives us. It keeps the badge's gold cross and ivory corpus,
# but drops the halo, shadow, scroll and lettering, all of which only become
# muddy at this size. Strokes are heavier so they survive the downsample.
# The ring is rendered separately in braille (see TERMINAL_RING_SVG): a 1 px
# circle in half blocks is a staircase, while braille gives 80×80 dots.
TERMINAL_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
{DEFS}
<g stroke="{INK}" stroke-width="1.8" stroke-linejoin="round">
  <path d="M27.5 4 h9 v56 h-9 z" fill="url(#gold-small)"/>
  <path d="M7 16.5 h50 v9.5 h-50 z" fill="url(#gold)"/>
</g>
<path d="M27.9 4.4 h0.9 v55 h-0.9 z" fill="{GOLD_PALE}" opacity="0.7"/>
<path d="M7.5 16.9 h49 v1 h-49 z" fill="{GOLD_PALE}" opacity="0.6"/>
<g fill="url(#ivory)">
  <circle cx="32" cy="11.8" r="4.4"/>
  <path d="M29.3 16.4 h5.4 v20 h-5.4 z"/>
  <path d="M16.5 19.35 h31 v3.8 h-31 z"/>
  <path d="M30 36.5 q-1.4 4.6 -4.6 8.1 l2.6 1.5 q3 -3.7 4 -8.8 z"/>
  <path d="M34 36.5 q1.4 4.6 4.6 8.1 l-2.6 1.5 q-3 -3.7 -4 -8.8 z"/>
</g>
<path d="M28.7 32.8 h6.6 v4.4 h-6.6 z" fill="{OXBLOOD}"/>
</svg>
"""

# Just the ring, for the braille pass. Braille is a 2×4 dot grid per cell, so
# at 40×20 cells this is an 80×80 canvas: the circle gets twice the steps of
# the half-block cross and reads as a string of small beads rather than a
# jagged 1 px outline.
TERMINAL_RING_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
{DEFS}
<circle cx="32" cy="32" r="30" fill="none" stroke="{GOLD}" stroke-width="2.2" opacity="0.85"/>
</svg>
"""


def rsvg(svg: str, size: int) -> Image.Image:
    png = subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size)],
        input=svg.encode(), capture_output=True, check=True,
    ).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


ANSI_RE = re.compile(r"\x1b\[([0-9;]*)m")
BRAILLE_DOTS = (
    (0, 0, 0x01), (0, 1, 0x02), (0, 2, 0x04), (0, 3, 0x40),
    (1, 0, 0x08), (1, 1, 0x10), (1, 2, 0x20), (1, 3, 0x80),
)


def onink(p):
    a = p[3] / 255
    return tuple(round(p[i] * a + INK_RGB[i] * (1 - a)) for i in range(3))


def fastfetch_logo(img: Image.Image, rows: int = 20, alpha_cut: int = 64) -> str:
    """Half-block ANSI art for the cross, using Omarchy's ▀ trick.

    Only halves with real coverage are painted, so the mark keeps a transparent
    background. Edge pixels are blended onto the theme's ink rather than
    thresholded hard, which keeps the small corpus from looking chipped.
    """
    width = max(1, round(img.width / img.height * rows * 2))
    small = img.resize((width, rows * 2), Image.LANCZOS)

    out = []
    for y in range(0, small.height, 2):
        line = []
        for x in range(small.width):
            top = small.getpixel((x, y))
            bottom = small.getpixel((x, y + 1))
            top_on = top[3] >= alpha_cut
            bottom_on = bottom[3] >= alpha_cut
            if not top_on and not bottom_on:
                line.append(" ")
            elif top_on and bottom_on:
                t, b = onink(top), onink(bottom)
                line.append(
                    f"\x1b[38;2;{t[0]};{t[1]};{t[2]}m"
                    f"\x1b[48;2;{b[0]};{b[1]};{b[2]}m▀\x1b[0m"
                )
            elif top_on:
                t = onink(top)
                line.append(f"\x1b[38;2;{t[0]};{t[1]};{t[2]}m▀\x1b[0m")
            else:
                b = onink(bottom)
                line.append(f"\x1b[38;2;{b[0]};{b[1]};{b[2]}m▄\x1b[0m")
        out.append("".join(line).rstrip())
    return "\n".join(out) + "\n"


def parse_logo(logo: str) -> dict:
    """Turn a half-block logo back into a cell grid."""
    grid = {}
    for y, line in enumerate(logo.splitlines()):
        x = 0
        fg = bg = None
        i = 0
        while i < len(line):
            m = ANSI_RE.match(line, i)
            if m:
                parts = [p for p in m.group(1).split(";") if p]
                if not parts or parts == ["0"]:
                    fg = bg = None
                elif parts[0] == "38":
                    fg = tuple(int(v) for v in parts[2:5])
                elif parts[0] == "48":
                    bg = tuple(int(v) for v in parts[2:5])
                i = m.end()
                continue
            grid[(x, y)] = (line[i], fg, bg)
            x += 1
            i += 1
    return grid


def braille_ring(img: Image.Image, cols: int = 40, rows: int = 20,
                 alpha_cut: int = 64) -> dict:
    """Sample the ring into 2×4 braille dots, giving it 80×80 resolution."""
    grid = {}
    for cy in range(rows):
        for cx in range(cols):
            bits = 0
            colors = []
            for dx, dy, bit in BRAILLE_DOTS:
                p = img.getpixel((min(img.width - 1, cx * 2 + dx),
                                  min(img.height - 1, cy * 4 + dy)))
                if p[3] < alpha_cut:
                    continue
                bits |= bit
                colors.append(onink(p))
            if bits:
                fg = tuple(round(sum(c[i] for c in colors) / len(colors))
                           for i in range(3))
                grid[(cx, cy)] = (chr(0x2800 + bits), fg, None)
    return grid


def terminal_logo(rows: int = 20) -> str:
    """Half-block cross plus the braille-bead ring, in one ANSI logo."""
    cols = rows * 2
    cross = parse_logo(fastfetch_logo(rsvg(TERMINAL_SVG, 512), rows))
    ring = braille_ring(rsvg(TERMINAL_RING_SVG, rows * 4), cols=cols, rows=rows)
    out = []
    for y in range(rows):
        line = []
        for x in range(cols):
            cell = cross.get((x, y))
            if cell and cell[0] != " ":
                glyph, fg, bg = cell
                s = f"\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m"
                if bg:
                    s += f"\x1b[48;2;{bg[0]};{bg[1]};{bg[2]}m"
                line.append(f"{s}{glyph}\x1b[0m")
            elif (x, y) in ring:
                glyph, fg, _ = ring[(x, y)]
                line.append(f"\x1b[38;2;{fg[0]};{fg[1]};{fg[2]}m{glyph}\x1b[0m")
            else:
                line.append(" ")
        out.append("".join(line).rstrip())
    return "\n".join(out) + "\n"


def main():
    img = rsvg(SVG, 512)
    img.save(ROOT / "unlock.png", optimize=True)
    print("wrote unlock.png")

    # Terminal badge: half-block cross, braille-bead ring, transparent bg.
    logo = terminal_logo(rows=20)
    (ROOT / "extras" / "fastfetch-logo.txt").write_text(logo)
    print(f"wrote extras/fastfetch-logo.txt ({len(logo.splitlines())} lines)")


if __name__ == "__main__":
    main()
