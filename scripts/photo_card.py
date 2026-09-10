#!/usr/bin/env python3
"""Annotate the board photo with matrix positions and shared aliases.

Reads the calibrated key centers below plus the shared vocabulary from
config/key-labels/hillside_d50.h, and writes docs/hillside50dactyl-annotated.png.

Local tool: requires Pillow outside the Nix shell (the Nix Python's Pillow is
not usable), and the output is committed rather than CI-checked because font
rasterization differs across platforms.

    env -u PYTHONPATH /opt/homebrew/bin/python3 scripts/photo_card.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import layout_card

ROOT = Path(__file__).resolve().parent.parent
PHOTO = ROOT / "docs/hillside50dactyl.png"
OUT = ROOT / "docs/hillside50dactyl-annotated.png"
HEADER = ROOT / "config/key-labels/hillside_d50.h"

SCALE = 2

GROUPS = {
    "main": (247, 247, 247),
    "raise": (255, 227, 191),
    "upper": (211, 233, 251),
    "lower": (217, 239, 217),
}

FONT_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

# Calibrated key centers in source-photo pixels (1024x474); position -> (x, y).
# Detected from the white/colored keycaps and verified key-by-key against the
# generated position map.
CENTERS = {
    0: (105, 63), 1: (153, 77), 2: (229, 65), 3: (293, 74), 4: (332, 110), 5: (383, 131),
    6: (660, 132), 7: (708, 111), 8: (740, 76), 9: (800, 68), 10: (883, 73), 11: (919, 60),
    12: (90, 113), 13: (137, 129), 14: (212, 118), 15: (276, 123), 16: (311, 162), 17: (362, 183),
    18: (680, 184), 19: (728, 162), 20: (756, 122), 21: (816, 116), 22: (895, 124), 23: (931, 111),
    24: (64, 162), 25: (116, 179), 26: (190, 165), 27: (252, 170), 28: (282, 210), 29: (338, 233),
    30: (709, 233), 31: (757, 208), 32: (784, 168), 33: (839, 163), 34: (898, 170), 35: (974, 164),
    36: (159, 209), 37: (225, 214), 38: (290, 293), 39: (377, 293), 40: (673, 290), 41: (750, 303),
    42: (813, 211), 43: (874, 204), 44: (330, 340), 45: (370, 387), 46: (420, 350), 47: (637, 330),
    48: (670, 380), 49: (710, 340),
}


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size)


def main() -> None:
    defines = layout_card.parse_defines(HEADER)
    aliases = layout_card.parse_positions(defines, layout_card.ALIAS_RE)
    assert set(aliases) == set(CENTERS) == set(range(50))

    photo = Image.open(PHOTO).convert("RGB")
    img = photo.resize((photo.width * SCALE, photo.height * SCALE), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    number_font = load_font(22)
    alias_font = load_font(13)

    for pos in range(50):
        x, y = (value * SCALE for value in CENTERS[pos])
        alias = aliases[pos]
        fill = GROUPS[layout_card.group(alias)]

        radius = 15
        draw.ellipse(
            [x - radius, y - radius - 6, x + radius, y + radius - 6],
            fill=fill,
            outline=(60, 60, 60),
            width=2,
        )
        label = str(pos)
        box = draw.textbbox((0, 0), label, font=number_font)
        draw.text(
            (x - (box[2] - box[0]) / 2, y - 6 - (box[3] - box[1]) / 2 - box[1]),
            label,
            font=number_font,
            fill=(20, 20, 20),
        )

        lines = layout_card.alias_lines(alias, limit=12)
        for index, line in enumerate(lines):
            box = draw.textbbox((0, 0), line, font=alias_font)
            draw.text(
                (x - (box[2] - box[0]) / 2, y + 14 + index * 15),
                line,
                font=alias_font,
                fill=(255, 255, 255),
                stroke_width=2,
                stroke_fill=(30, 30, 30),
            )

    img.save(OUT)
    print(f"photo card: wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
