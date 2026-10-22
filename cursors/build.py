#!/usr/bin/python3
"""Build the Rosary XCursor theme.

The pointer is a small crucifix: an antique-gold Latin cross with an ivory
corpus, hanging from the hotspot at the top of the beam. The hand carries a
tiny cross at the wrist, and the wait cursor is the cross inside a ring of
rosary beads with one bead travelling around it. Shapes not drawn here inherit
from Adwaita.

    ./build.py             -> Rosary/ next to this script
    ./build.py --install   -> also copy to ~/.local/share/icons/Rosary

Needs rsvg-convert, python-numpy and python-pillow.
"""
from __future__ import annotations

import io
import math
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "Rosary"
PREVIEW = HERE / "preview.png"
SIZES = (24, 32, 48, 64)

INK = "#0b0d15"
NIGHT = "#151a2a"
IVORY = "#efe6d4"
PARCHMENT = "#d8cbb0"
GOLD = "#d9b45b"
GOLD_PALE = "#f2dfa4"
GOLD_DEEP = "#a67c2e"
OXBLOOD = "#a84a54"
ULTRAMARINE = "#4f6fae"

DEFS = f"""
<defs>
  <linearGradient id="gold" x1="0" y1="0" x2="0.9" y2="1">
    <stop offset="0" stop-color="{GOLD_PALE}"/>
    <stop offset="0.45" stop-color="{GOLD}"/>
    <stop offset="1" stop-color="{GOLD_DEEP}"/>
  </linearGradient>
  <linearGradient id="ivory" x1="0" y1="0" x2="0.4" y2="1">
    <stop offset="0" stop-color="#f8f1e3"/>
    <stop offset="1" stop-color="{PARCHMENT}"/>
  </linearGradient>
  <radialGradient id="glow">
    <stop offset="0" stop-color="{GOLD_PALE}" stop-opacity="0.75"/>
    <stop offset="0.55" stop-color="{GOLD}" stop-opacity="0.28"/>
    <stop offset="1" stop-color="{GOLD}" stop-opacity="0"/>
  </radialGradient>
  <filter id="shadow" x="-60%" y="-60%" width="220%" height="220%">
    <feDropShadow dx="0.35" dy="0.7" stdDeviation="0.55" flood-color="#000" flood-opacity="0.65"/>
  </filter>
</defs>
"""


def svg(body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" '
            f'viewBox="0 0 32 32">{DEFS}{body}</svg>')


def crucifix(cx: float, cy: float, h: float, corpus: bool = True, glow: bool = True,
             ring: bool = False) -> str:
    """A Latin cross whose top is at (cx, cy), height h, with a small ivory corpus."""
    w = h * 0.115              # beam thickness
    arm_y = cy + h * 0.26
    arm_w = h * 0.62
    parts = []
    if glow:
        parts.append(f'<circle cx="{cx:.2f}" cy="{cy + h * 0.42:.2f}" r="{h * 0.52:.2f}" fill="url(#glow)" opacity="0.8"/>')
    if ring:
        parts.append(f'<circle cx="{cx:.2f}" cy="{cy + h * 0.5:.2f}" r="{h * 0.78:.2f}" '
                     f'fill="none" stroke="{GOLD}" stroke-width="{max(0.35, h*0.035):.2f}" opacity="0.35"/>')

    parts.append('<g filter="url(#shadow)">')
    # beams
    parts.append(f'<rect x="{cx - w/2:.2f}" y="{cy:.2f}" width="{w:.2f}" height="{h:.2f}" '
                 f'rx="{w*0.18:.2f}" fill="url(#gold)" stroke="{INK}" stroke-width="{max(0.45, h*0.045):.2f}"/>')
    parts.append(f'<rect x="{cx - arm_w/2:.2f}" y="{arm_y - w/2:.2f}" width="{arm_w:.2f}" height="{w:.2f}" '
                 f'rx="{w*0.18:.2f}" fill="url(#gold)" stroke="{INK}" stroke-width="{max(0.45, h*0.045):.2f}"/>')
    # flared ends
    for ex, ey, ew, eh in (
        (cx - arm_w / 2 - w * 0.22, arm_y - w * 0.7, w * 0.42, w * 1.4),
        (cx + arm_w / 2 - w * 0.2, arm_y - w * 0.7, w * 0.42, w * 1.4),
    ):
        parts.append(f'<rect x="{ex:.2f}" y="{ey:.2f}" width="{ew:.2f}" height="{eh:.2f}" '
                     f'rx="{w*0.15:.2f}" fill="url(#gold)" stroke="{INK}" stroke-width="{max(0.4, h*0.04):.2f}"/>')

    if corpus and h >= 12:
        head_y = cy + h * 0.20
        head_r = h * 0.055
        torso_top = head_y + head_r * 1.2
        torso_bot = cy + h * 0.66
        limb = max(0.65, h * 0.055)
        parts.append(f'<g stroke="{INK}" stroke-width="{max(0.35, limb*0.38):.2f}" '
                     f'stroke-linejoin="round" stroke-linecap="round" fill="url(#ivory)">')
        parts.append(f'<circle cx="{cx:.2f}" cy="{head_y:.2f}" r="{head_r:.2f}"/>')
        parts.append(f'<path d="M{cx:.2f},{torso_top:.2f} L{cx:.2f},{torso_bot:.2f}" '
                     f'stroke="{PARCHMENT}" stroke-width="{limb:.2f}"/>')
        parts.append(f'<path d="M{cx - arm_w*0.30:.2f},{arm_y - h*0.012:.2f} L{cx + arm_w*0.30:.2f},{arm_y - h*0.012:.2f}" '
                     f'stroke="{PARCHMENT}" stroke-width="{limb*0.8:.2f}"/>')
        parts.append(f'<path d="M{cx:.2f},{torso_bot:.2f} l{-h*0.055:.2f},{h*0.13:.2f} '
                     f'M{cx:.2f},{torso_bot:.2f} l{h*0.055:.2f},{h*0.13:.2f}" '
                     f'stroke="{PARCHMENT}" stroke-width="{limb*0.7:.2f}"/>')
        # re-ink the thin limbs so they read at 24 px
        parts.append(f'<path d="M{cx:.2f},{torso_top:.2f} L{cx:.2f},{torso_bot:.2f}" '
                     f'stroke="{INK}" stroke-width="{max(0.25, limb*0.24):.2f}" opacity="0.55" fill="none"/>')
        parts.append('</g>')
    parts.append('</g>')
    return "".join(parts)


def pointer() -> str:
    return svg(crucifix(6.0, 1.6, 23.0, corpus=True) +
               f'<circle cx="6" cy="1.6" r="0.9" fill="{GOLD_PALE}"/>')


def point_hand() -> str:
    hand = ("M10.6,5 Q10.6,2.8 12.7,2.8 Q14.8,2.8 14.8,5 L14.8,12.2 "
            "Q14.8,10.6 16.6,10.6 Q18.4,10.6 18.4,12.2 L18.4,13.1 "
            "Q18.4,11.7 20.1,11.7 Q21.8,11.7 21.8,13.3 L21.8,14.3 "
            "Q21.8,13 23.4,13 Q25,13 25,14.7 L25,20.6 Q25,28.2 18.4,28.2 L15.4,28.2 "
            "Q11.6,28.2 9.6,24.4 L6.4,18.4 Q5.6,16.7 7.1,16 Q8.6,15.3 9.6,16.8 L10.6,18.4 Z")
    return svg(f'<circle cx="12.7" cy="3.6" r="3.6" fill="url(#glow)" opacity="0.55"/>'
               f'<g filter="url(#shadow)"><path d="{hand}" fill="url(#ivory)" stroke="{INK}" '
               f'stroke-width="1.3" stroke-linejoin="round"/></g>'
               + crucifix(24.0, 4.2, 7.2, corpus=False, glow=False))


def hand(closed=False) -> str:
    if closed:
        d = ("M8.5,15.5 Q8.5,12.6 11,12.6 Q11.2,10.4 13.1,10.4 Q14.9,10.4 15.1,11.6 "
             "Q15.5,9.9 17.3,9.9 Q19.1,9.9 19.3,11.5 Q19.7,10.5 21.3,10.5 Q23.2,10.5 23.2,12.8 "
             "L23.2,20 Q23.2,27.5 16.6,27.5 L14.6,27.5 Q10.5,27.5 8.5,22 Z")
        lines = (f'<path d="M11.2,13 L11.2,16.4 M15.1,11.8 L15.1,15.6 M19.3,11.6 L19.3,15.4" '
                 f'stroke="{INK}" stroke-width="0.9" stroke-linecap="round" opacity="0.6"/>')
    else:
        d = ("M8.5,15 Q8.5,12.5 10.8,12.5 L10.8,7 Q10.8,5 12.8,5 Q14.8,5 14.8,7 L14.8,11 "
             "L14.8,5.5 Q14.8,3.5 16.8,3.5 Q18.8,3.5 18.8,5.5 L18.8,11 L18.8,6.5 Q18.8,4.5 20.8,4.5 "
             "Q22.8,4.5 22.8,6.5 L22.8,20 Q22.8,27.5 16.5,27.5 L14.5,27.5 Q10.5,27.5 8.5,22 Z")
        lines = ""
    return svg(f'<g filter="url(#shadow)"><path d="{d}" fill="url(#ivory)" stroke="{INK}" '
               f'stroke-width="1.3" stroke-linejoin="round"/></g>{lines}')


def text_beam() -> str:
    d = "M11,4 Q16,4 16,7 Q16,4 21,4 M16,7 L16,25 M11,28 Q16,28 16,25 Q16,28 21,28 M13,16 L19,16"
    return svg(f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="3.9" stroke-linecap="round"/>'
               f'<path d="{d}" fill="none" stroke="{GOLD}" stroke-width="1.9" stroke-linecap="round"/>'
               f'<path d="{d}" fill="none" stroke="{IVORY}" stroke-width="0.85" stroke-linecap="round"/>')


def crosshair() -> str:
    d = "M16,2.5 L16,11.5 M16,20.5 L16,29.5 M2.5,16 L11.5,16 M20.5,16 L29.5,16"
    return svg(f'<path d="{d}" stroke="{INK}" stroke-width="3.6" stroke-linecap="round"/>'
               f'<path d="{d}" stroke="{GOLD}" stroke-width="1.5" stroke-linecap="round"/>'
               + crucifix(16, 12.9, 6.4, corpus=False, glow=False))


def not_allowed() -> str:
    return svg(f'<g filter="url(#shadow)"><circle cx="16" cy="16" r="10" fill="{INK}" fill-opacity="0.6" '
               f'stroke="{INK}" stroke-width="4.4"/>'
               f'<circle cx="16" cy="16" r="10" fill="none" stroke="{OXBLOOD}" stroke-width="2.4"/>'
               f'<path d="M9,23 L23,9" stroke="{INK}" stroke-width="4.4" stroke-linecap="round"/>'
               f'<path d="M9,23 L23,9" stroke="{OXBLOOD}" stroke-width="2.4" stroke-linecap="round"/></g>')


def double_arrow(angle: float) -> str:
    d = ("M4,16 L10,10.5 L10,13.9 L22,13.9 L22,10.5 L28,16 L22,21.5 L22,18.1 "
         "L10,18.1 L10,21.5 Z")
    return svg(f'<g transform="rotate({angle} 16 16)" filter="url(#shadow)"><path d="{d}" '
               f'fill="url(#ivory)" stroke="{INK}" stroke-width="1.3" stroke-linejoin="round"/></g>'
               f'<circle cx="16" cy="16" r="1.5" fill="{GOLD}" stroke="{INK}" stroke-width="0.6"/>')


def move() -> str:
    d = ("M16,3 L20.5,8 L17.6,8 L17.6,14.4 L24,14.4 L24,11.5 L29,16 L24,20.5 L24,17.6 "
         "L17.6,17.6 L17.6,24 L20.5,24 L16,29 L11.5,24 L14.4,24 L14.4,17.6 L8,17.6 "
         "L8,20.5 L3,16 L8,11.5 L8,14.4 L14.4,14.4 L14.4,8 L11.5,8 Z")
    return svg(f'<g filter="url(#shadow)"><path d="{d}" fill="url(#ivory)" stroke="{INK}" '
               f'stroke-width="1.2" stroke-linejoin="round"/></g>'
               f'<circle cx="16" cy="16" r="2.1" fill="{GOLD}" stroke="{INK}" stroke-width="0.6"/>'
               + crucifix(16, 12.9, 6.2, corpus=False, glow=False))


def wait_ring(i: int, n: int) -> str:
    """The crucifix in a ring of rosary beads; one bead travels around."""
    parts = [crucifix(16, 8.6, 14.4, corpus=True, glow=True, ring=True)]
    cx, cy, r = 16, 15.8, 11.2
    for k in range(10):
        a = -math.pi / 2 + 2 * math.pi * k / 10
        bx, by = cx + r * math.cos(a), cy + r * math.sin(a)
        active = (k == i % 10)
        rr = 1.55 if active else 0.85
        fill = GOLD_PALE if active else GOLD
        parts.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{rr:.2f}" fill="{fill}" '
                     f'stroke="{INK}" stroke-width="{0.55 if active else 0.35:.2f}"/>')
    return svg("".join(parts))


def progress(i: int, n: int) -> str:
    """The pointer cross with a bead travelling around its foot."""
    parts = [crucifix(6.0, 1.6, 23.0, corpus=True)]
    a = -math.pi / 2 + 2 * math.pi * i / n
    bx, by = 6.0 + 4.4 * math.cos(a), 22.4 + 4.4 * math.sin(a)
    parts.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="1.5" fill="{GOLD_PALE}" '
                 f'stroke="{INK}" stroke-width="0.5"/>')
    return svg("".join(parts))


WAIT = 16
CURSORS = {
    "default": ([pointer()], (6, 2), 0),
    "pointer": ([point_hand()], (12.7, 2.8), 0),
    "text": ([text_beam()], (16, 16), 0),
    "crosshair": ([crosshair()], (16, 16), 0),
    "not-allowed": ([not_allowed()], (16, 16), 0),
    "move": ([move()], (16, 16), 0),
    "grab": ([hand(False)], (16, 14), 0),
    "grabbing": ([hand(True)], (16, 16), 0),
    "ew-resize": ([double_arrow(0)], (16, 16), 0),
    "ns-resize": ([double_arrow(90)], (16, 16), 0),
    "nwse-resize": ([double_arrow(45)], (16, 16), 0),
    "nesw-resize": ([double_arrow(-45)], (16, 16), 0),
    "wait": ([wait_ring(i, WAIT) for i in range(WAIT)], (16, 12), 90),
    "progress": ([progress(i, WAIT) for i in range(WAIT)], (6, 2), 90),
}

ALIASES = {
    "default": ["left_ptr", "arrow", "top_left_arrow", "context-menu", "copy", "alias"],
    "pointer": ["hand1", "hand2", "pointing_hand", "e29285e634086352946a0e7090d73106",
                "9d800788f1b08800ae810202380a0822"],
    "text": ["xterm", "ibeam", "vertical-text"],
    "crosshair": ["cross", "tcross", "cell", "color-picker"],
    "not-allowed": ["no-drop", "forbidden", "circle", "crossed_circle", "03b6e0fcb3499374a867c041f52298f0"],
    "move": ["fleur", "all-scroll", "size_all", "all-resize"],
    "grab": ["openhand", "5aca4d189052212118709018842178c0"],
    "grabbing": ["closedhand", "dnd-move", "dnd-none", "208530c400c041818281048008011002"],
    "ew-resize": ["col-resize", "sb_h_double_arrow", "h_double_arrow", "size_hor", "e-resize",
                  "w-resize", "left_side", "right_side", "split_h", "14fef782d02440884392942c11205230"],
    "ns-resize": ["row-resize", "sb_v_double_arrow", "v_double_arrow", "size_ver", "n-resize",
                  "s-resize", "top_side", "bottom_side", "split_v", "2870a09082c103050810ffdffffe0204"],
    "nwse-resize": ["size_fdiag", "bd_double_arrow", "nw-resize", "se-resize", "top_left_corner",
                    "bottom_right_corner", "c7088f0f3e6c8088236ef8e1e3e70000"],
    "nesw-resize": ["size_bdiag", "fd_double_arrow", "ne-resize", "sw-resize", "top_right_corner",
                    "bottom_left_corner", "fcf1c3c7cd4491d801f1e1c78f100000"],
    "wait": ["watch", "clock"],
    "progress": ["left_ptr_watch", "half-busy", "00000000000000020006000e7e9ffc3f",
                 "08e8e1c95fe2fc01f976f1e063a24ccd", "3ecb610c1bf2410f44200f48c40d3599"],
}


def render(svg_text: str, size: int) -> Image.Image:
    png = subprocess.run(["rsvg-convert", "-w", str(size), "-h", str(size)],
                         input=svg_text.encode(), capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(png)).convert("RGBA")


def xcursor(frames, hotspot, delay):
    images = []
    for size in SIZES:
        hx, hy = (round(c * size / 32) for c in hotspot)
        for svg_text in frames:
            rgba = np.asarray(render(svg_text, size), dtype=np.uint32)
            a = rgba[..., 3]
            argb = (a << 24) | (rgba[..., 0] * a // 255 << 16) | (rgba[..., 1] * a // 255 << 8) | (rgba[..., 2] * a // 255)
            images.append((size, size, size, hx, hy, delay, argb.astype("<u4").tobytes()))
    out = bytearray(struct.pack("<4sIII", b"Xcur", 16, 0x10000, len(images)))
    pos = 16 + 12 * len(images)
    for nominal, w, h, *_rest, px in images:
        out += struct.pack("<III", 0xFFFD0002, nominal, pos)
        pos += 36 + len(px)
    for nominal, w, h, hx, hy, dl, px in images:
        out += struct.pack("<IIIIIIIII", 36, 0xFFFD0002, nominal, 1, w, h, hx, hy, dl)
        out += px
    return bytes(out)


def contact_sheet():
    names = list(CURSORS)
    cell = 84
    rows = [((11, 13, 21, 255), 24), ((11, 13, 21, 255), 64), ((239, 230, 212, 255), 24), ((239, 230, 212, 255), 64)]
    anim = ["wait", "progress"]
    width = max(len(names) * cell, max(len(CURSORS[n][0]) for n in anim) * cell)
    sheet = Image.new("RGBA", (width, cell * (len(rows) + len(anim))), (11, 13, 21, 255))
    for r, (bg, size) in enumerate(rows):
        sheet.paste(Image.new("RGBA", (width, cell), bg), (0, r * cell))
        for i, name in enumerate(names):
            im = render(CURSORS[name][0][0], size)
            if size == 24:
                im = im.resize((48, 48), Image.NEAREST)
            sheet.alpha_composite(im, (i * cell + (cell - im.width) // 2, r * cell + (cell - im.height) // 2))
    for r, name in enumerate(anim):
        y = (len(rows) + r) * cell
        for i, f in enumerate(CURSORS[name][0]):
            im = render(f, 64)
            sheet.alpha_composite(im, (i * cell + 10, y + 10))
    sheet.save(PREVIEW)


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    cdir = OUT / "cursors"
    cdir.mkdir(parents=True)
    for name, (frames, hotspot, delay) in CURSORS.items():
        (cdir / name).write_bytes(xcursor(frames, hotspot, delay))
        for alias in ALIASES.get(name, []):
            if not (cdir / alias).exists():
                (cdir / alias).symlink_to(name)
    (OUT / "index.theme").write_text(
        "[Icon Theme]\nName=Rosary\nComment=Rosary cursors: antique gold, ivory, and a small crucifix pointer\nInherits=Adwaita\n")
    (OUT / "cursor.theme").write_text("[Icon Theme]\nInherits=Rosary\n")
    contact_sheet()

    if "--install" in sys.argv:
        dest = Path.home() / ".local/share/icons/Rosary"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(OUT, dest, symlinks=True)
        print(f"installed to {dest}")
    print(f"built {len(CURSORS)} cursors, {sum(len(v) for v in ALIASES.values())} aliases")


if __name__ == "__main__":
    main()
