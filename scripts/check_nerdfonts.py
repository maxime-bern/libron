#!/usr/bin/env python3
"""Sanity-check the Nerd Fonts variants in ./out/nerd and ./out/nerd-mono.

Run after `build.py --with-nerdfonts --with-nerdfonts-mono` (or inside the
fntbld container):

  podman run --rm -v "$PWD":/work -w /work \
    ghcr.io/nicoverbruggen/fntbld-oci:latest python3 scripts/check_nerdfonts.py
"""

import glob
import os
import sys

from fontTools.ttLib import TTFont

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STYLES = ["Regular", "Bold", "Italic", "BoldItalic"]

# One representative codepoint per major glyph set the patcher adds.
REQUIRED = {
    0xE0B0: "Powerline",
    0xF015: "Font Awesome",
    0xE718: "Devicons",
}

# Only patched in when the source font is detected as monospaced.
MONO_REQUIRED = {
    0x2500: "box drawing",
    0x2588: "block elements",
    0x2801: "braille",
}

# (directory, family, filename, monospaced)
VARIANTS = [
    ("nerd", "Libron Nerd Font", "LibronNerdFont-{style}.ttf", False),
    ("nerd-mono", "Libron Nerd Font Mono", "LibronNerdFontMono-{style}.ttf", True),
]


def ascii_advances(font, cmap):
    hmtx = font["hmtx"]
    return {hmtx[cmap[c]][0] for c in range(0x21, 0x7F) if c in cmap}


def check(path, family, mono):
    font = TTFont(path)
    cmap = font.getBestCmap()

    required = dict(REQUIRED)
    if mono:
        required.update(MONO_REQUIRED)
    missing = [name for cp, name in required.items() if cp not in cmap]
    if missing:
        raise AssertionError(f"{path}: missing glyph sets {missing}")

    actual = font["name"].getDebugName(1)
    if actual != family:
        raise AssertionError(f"{path}: family is {actual!r}, expected {family!r}")

    advances = ascii_advances(font, cmap)
    if mono:
        if len(advances) != 1:
            raise AssertionError(f"{path}: not monospaced, ASCII advances {sorted(advances)}")
        if not font["post"].isFixedPitch or font["OS/2"].panose.bProportion != 9:
            raise AssertionError(f"{path}: monospace flags not set")
        if "kern" in font:
            raise AssertionError(f"{path}: kern table still present")
    elif len(advances) < 2:
        raise AssertionError(f"{path}: proportional variant has a single advance {advances}")

    return len(font.getGlyphOrder())


def main():
    status = 0
    for directory, family, pattern, mono in VARIANTS:
        paths = sorted(glob.glob(os.path.join(REPO_DIR, "out", directory, "*.ttf")))
        if not paths:
            flag = "--with-nerdfonts-mono" if mono else "--with-nerdfonts"
            print(f"skip: no out/{directory} -- build with {flag}", file=sys.stderr)
            continue

        for path in paths:
            try:
                glyphs = check(path, family, mono)
            except AssertionError as error:
                print(f"FAIL: {error}", file=sys.stderr)
                status = 1
                continue
            print(f"  {directory}/{os.path.basename(path)}: {glyphs} glyphs")

        found = {os.path.basename(path) for path in paths}
        expected = {pattern.format(style=style) for style in STYLES}
        if not expected.issubset(found):
            print(f"FAIL: out/{directory} missing styles {sorted(expected - found)}", file=sys.stderr)
            status = 1

    return status


if __name__ == "__main__":
    sys.exit(main())
