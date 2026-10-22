#!/usr/bin/python3
"""Build the Rosary wallpaper set from the original paintings.

Each painting becomes a 21:9 gallery plate: a blurred, deeply darkened copy of
the painting as the backdrop, the painting itself held in a thin antique-gold
frame, and a quiet caption naming the mystery, its set and its scripture. The
wide shape survives Omarchy's PreserveAspectCrop on both 21:9 and 16:9 screens.

    ./build-wallpapers.py                          # 3440x1440 into ../paintings/
    ./build-wallpapers.py --width 2560 --height 1080  # smaller build
    ./build-wallpapers.py --preview                # also write ../preview.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ART = ROOT / "art" / "originals"
OUT = ROOT / "paintings"

SET_NAMES = {
    "joyful": "The Joyful Mysteries",
    "sorrowful": "The Sorrowful Mysteries",
    "glorious": "The Glorious Mysteries",
    "luminous": "The Luminous Mysteries",
}

# Weekday -> the set traditionally prayed that day.
DAY_SETS = {
    0: "joyful",      # Monday
    1: "sorrowful",   # Tuesday
    2: "glorious",    # Wednesday
    3: "luminous",    # Thursday
    4: "sorrowful",   # Friday
    5: "joyful",      # Saturday
    6: "glorious",    # Sunday
}

# crop = (top, bottom, left, right) in pixels; the vintage prints carry a
# cream paper border that the other scans do not.
MYSTERIES = [
    dict(set="joyful", n=1, slug="annunciation", file="annunciation.jpg",
         title="The Annunciation", ref="Luke 1:26–38"),
    dict(set="joyful", n=2, slug="visitation", file="visitation.jpg",
         title="The Visitation", ref="Luke 1:39–56"),
    dict(set="joyful", n=3, slug="nativity", file="birth.jpg",
         title="The Nativity", ref="Luke 2:1–20", crop=(15, 16, 12, 13)),
    dict(set="joyful", n=4, slug="presentation", file="presentation.jpg",
         title="The Presentation", ref="Luke 2:22–38"),
    dict(set="joyful", n=5, slug="finding", file="finding.jpg",
         title="The Finding in the Temple", ref="Luke 2:41–52"),

    dict(set="sorrowful", n=1, slug="agony-in-the-garden", file="AgonyGarden.jpeg",
         title="The Agony in the Garden", ref="Matthew 26:36–46"),
    dict(set="sorrowful", n=2, slug="scourging", file="scourging.jpeg",
         title="The Scourging at the Pillar", ref="John 19:1"),
    dict(set="sorrowful", n=3, slug="crowning-with-thorns", file="crowningThorns.jpg",
         title="The Crowning with Thorns", ref="Matthew 27:27–31"),
    dict(set="sorrowful", n=4, slug="carrying-the-cross", file="carryingCross.jpg",
         title="The Carrying of the Cross", ref="Luke 23:26–32"),
    dict(set="sorrowful", n=5, slug="crucifixion", file="crucifixion.jpg",
         title="The Crucifixion", ref="John 19:17–30"),

    dict(set="glorious", n=1, slug="resurrection", file="resurrection.jpg",
         title="The Resurrection", ref="Matthew 28:1–10", crop=(15, 20, 13, 15)),
    dict(set="glorious", n=2, slug="ascension", file="Ascension.jpeg",
         title="The Ascension", ref="Acts 1:6–11"),
    dict(set="glorious", n=3, slug="descent-of-the-holy-spirit", file="descentHolySpirit.jpg",
         title="The Descent of the Holy Spirit", ref="Acts 2:1–13"),
    dict(set="glorious", n=4, slug="assumption", file="AssumptionMary.jpeg",
         title="The Assumption", ref="Revelation 12:1"),
    dict(set="glorious", n=5, slug="coronation", file="coronation.jpg",
         title="The Coronation of Mary", ref="Revelation 12:1"),

    dict(set="luminous", n=1, slug="baptism", file="baptismJesus.jpg",
         title="The Baptism in the Jordan", ref="Matthew 3:13–17"),
    dict(set="luminous", n=2, slug="cana", file="Cana.jpeg",
         title="The Wedding at Cana", ref="John 2:1–12"),
    dict(set="luminous", n=3, slug="proclamation", file="proclamationKingdom.jpg",
         title="The Proclamation of the Kingdom", ref="Mark 1:14–15"),
    dict(set="luminous", n=4, slug="transfiguration", file="transfiguration.jpeg",
         title="The Transfiguration", ref="Matthew 17:1–9"),
    dict(set="luminous", n=5, slug="eucharist", file="institutionEucharist.jpg",
         title="The Institution of the Eucharist", ref="Luke 22:14–20", crop=(16, 15, 13, 15)),
]

INK = (11, 13, 21)
INK_SOFT = (18, 21, 33)
GOLD = (217, 180, 91)
GOLD_DIM = (166, 124, 46)
IVORY = (233, 223, 204)
PARCHMENT = (184, 174, 155)
SERIF = "/usr/share/fonts/noto/NotoSerifDisplay-Light.ttf"


def load(entry):
    img = Image.open(ART / entry["file"]).convert("RGB")
    # Every scan carries a pixel or two of paper or scanner edge; take a hair
    # off all round before applying any larger, per-painting crop.
    img = img.crop((2, 2, img.width - 2, img.height - 2))
    if entry.get("crop"):
        top, bottom, left, right = entry["crop"]
        img = img.crop((left, top, img.width - right, img.height - bottom))
    return img


def backdrop(img, width, height):
    """A blurred, muted echo of the painting, sunk deep into an ink wash."""
    bg = ImageOps.fit(img, (width, height), method=Image.LANCZOS, centering=(0.5, 0.42))
    bg = bg.filter(ImageFilter.GaussianBlur(max(24, width // 30)))
    bg = ImageEnhance.Color(bg).enhance(0.55)
    bg = ImageEnhance.Brightness(bg).enhance(0.62)
    bg = Image.blend(bg, Image.new("RGB", bg.size, INK), 0.62)

    # Ink wash, strongest at the edges, so the frame sits in quiet darkness.
    yy, xx = np.mgrid[0:height, 0:width]
    cx, cy = width * 0.5, height * 0.44
    radius = np.sqrt(((xx - cx) / (width * 0.58)) ** 2 + ((yy - cy) / (height * 0.58)) ** 2)
    alpha = np.clip((radius - 0.05) * 1.35, 0, 1) ** 1.2
    alpha = (alpha * 238).astype(np.uint8)
    wash = Image.new("RGBA", (width, height), INK + (0,))
    wash.putalpha(Image.fromarray(alpha, "L"))
    return Image.alpha_composite(bg.convert("RGBA"), wash).convert("RGB")


def fit_painting(img, width, height):
    max_w, max_h = int(width * 0.615), int(height * 0.705)
    scale = min(max_w / img.width, max_h / img.height)
    size = (max(1, round(img.width * scale)), max(1, round(img.height * scale)))
    out = img.resize(size, Image.LANCZOS)
    if scale > 1.35:  # small scans benefit from a whisper of sharpening
        out = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))
    return out


def spaced_width(draw, text, font, tracking):
    return sum(draw.textlength(ch, font=font) for ch in text) + tracking * max(0, len(text) - 1)


def draw_spaced(draw, xy, text, font, fill, tracking, anchor="lt"):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill, anchor=anchor)
        x += draw.textlength(ch, font=font) + tracking


def caption(canvas, entry, width, height, top):
    draw = ImageDraw.Draw(canvas)
    title_size = max(20, round(width / 78))
    sub_size = max(13, round(width / 138))
    tracking_title = title_size * 0.17
    tracking_sub = sub_size * 0.16
    title_font = ImageFont.truetype(SERIF, title_size)
    sub_font = ImageFont.truetype(SERIF, sub_size)

    title = entry["title"].upper()
    sub = f"{SET_NAMES[entry['set']].upper()}  ·  {entry['ref'].upper()}"

    tw = spaced_width(draw, title, title_font, tracking_title)
    sw = spaced_width(draw, sub, sub_font, tracking_sub)
    cx = width / 2

    draw_spaced(draw, (cx - tw / 2, top), title, title_font, GOLD, tracking_title)
    title_bottom = top + title_size * 1.28
    draw_spaced(draw, (cx - sw / 2, title_bottom), sub, sub_font, PARCHMENT, tracking_sub)

    # A hairline rule each side of the caption, ending in a small diamond.
    rule_y = top + title_size * 0.57
    gap = tw / 2 + title_size * 1.3
    rule_len = width * 0.055
    for direction in (-1, 1):
        x0 = cx + direction * gap
        x1 = cx + direction * (gap + rule_len)
        draw.line((x0, rule_y, x1, rule_y), fill=GOLD_DIM + (170,), width=max(1, width // 1400))
        d = max(3, width // 500)
        draw.polygon([(x1 + direction * d, rule_y), (x1, rule_y - d), (x1 - direction * d * 0.2, rule_y),
                      (x1, rule_y + d)], fill=GOLD + (210,))


def plate(img, entry, width, height):
    canvas = backdrop(img, width, height).convert("RGBA")
    art = fit_painting(img, width, height)

    mat = max(6, round(width * 0.0055))
    border = max(2, round(width * 0.0011))
    outer = (art.width + mat * 2, art.height + mat * 2)
    framed = Image.new("RGBA", outer, INK_SOFT + (255,))
    framed.paste(art, (mat, mat))

    fd = ImageDraw.Draw(framed)
    fd.rectangle((0, 0, outer[0] - 1, outer[1] - 1), outline=GOLD_DIM + (255,), width=border)
    fd.rectangle((border, border, outer[0] - 1 - border, outer[1] - 1 - border),
                 outline=GOLD + (110,), width=max(1, border // 2))

    # Caption block is measured first so the plate can sit optically centred.
    title_size = max(20, round(width / 78))
    sub_size = max(13, round(width / 138))
    gap = round(title_size * 1.6)
    cap_height = round(title_size * 1.28 + sub_size * 1.5)
    block_h = outer[1] + gap + cap_height
    top = round((height - block_h) / 2)
    left = round((width - outer[0]) / 2)

    # Soft shadow under the frame.
    shadow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    pad = round(width * 0.008)
    sd.rectangle((left - pad, top + round(height * 0.008), left + outer[0] + pad, top + outer[1] + pad),
                 fill=(0, 0, 0, 165))
    shadow = shadow.filter(ImageFilter.GaussianBlur(round(width * 0.012)))
    canvas = Image.alpha_composite(canvas, shadow)

    canvas.alpha_composite(framed, (left, top))
    caption(canvas, entry, width, height, top + outer[1] + gap)
    return canvas.convert("RGB")


def preview(width=1280, height=720):
    """A theme-switcher preview: four plates on a 2x2 grid, with the palette."""
    picks = ["annunciation", "crucifixion", "resurrection", "transfiguration"]
    by_slug = {m["slug"]: m for m in MYSTERIES}
    cell_w, cell_h = width // 2, height // 2
    sheet = Image.new("RGB", (width, height), INK)
    for i, slug in enumerate(picks):
        img = load(by_slug[slug])
        plate_img = plate(img, by_slug[slug], cell_w, cell_h)
        sheet.paste(plate_img, ((i % 2) * cell_w, (i // 2) * cell_h))
    # Ink the middle seam so the four plates read as one window.
    d = ImageDraw.Draw(sheet, "RGBA")
    d.line((cell_w, 0, cell_w, height), fill=INK + (210,), width=4)
    d.line((0, cell_h, width, cell_h), fill=INK + (210,), width=4)
    sheet.save(ROOT / "preview.png", optimize=True)
    print(f"wrote {ROOT / 'preview.png'}")


def main():
    ap = argparse.ArgumentParser()
    # Omarchy crops wallpapers with PreserveAspectCrop. 21:9 is the widest
    # common desktop, so building at that shape means 16:9 screens only lose
    # ink at the sides, never the painting or its caption.
    ap.add_argument("--width", type=int, default=3440)
    ap.add_argument("--height", type=int, default=1440)
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    width = args.width
    height = args.height
    OUT.mkdir(parents=True, exist_ok=True)

    for entry in MYSTERIES:
        name = f"{entry['set']}-{entry['n']:02d}-{entry['slug']}.jpg"
        path = OUT / name
        img = load(entry)
        out = plate(img, entry, width, height)
        out.save(path, quality=91, optimize=True, progressive=True)
        print(f"{name:52s} {out.width}x{out.height}  {path.stat().st_size / 1e6:.1f} MB")

    if args.preview:
        preview()


if __name__ == "__main__":
    main()
