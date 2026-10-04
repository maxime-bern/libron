#!/usr/bin/env python3
"""Force a font to a single advance width (monospace).

Every glyph is redrawn into one cell of `--cell-em` ems: glyphs whose ink is
wider than the cell are condensed horizontally to fit, and all ink is centred
in the cell. Kerning is dropped (it has no meaning on a monospaced grid) and
hinting is discarded, because the outlines move.

No glyph is redrawn by hand: this is a mechanical conversion, so wide capitals
end up lighter than a designer would draw them.

Usage (fntbld container, see AGENTS.md):

  python3 scripts/make_mono.py out/ttf/Libron-Regular.ttf out/mono/Libron-Regular.ttf
  python3 scripts/make_mono.py --cell-em 0.75 in.ttf out.ttf
  python3 scripts/make_mono.py --min-ink 0.55 out/ttf/Libron-Regular.ttf out/mono/Libron-Regular.ttf
"""

import argparse
import os
import sys

from fontTools.misc.roundTools import otRound
from fontTools.misc.transform import Transform
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

INK_SHARE = 0.98  # share of the cell a glyph's ink may occupy


def outlines_and_bounds(glyphset, order):
    """Capture every glyph as flat contours, before any glyph is rewritten."""
    outlines, boxes = {}, {}
    for name in order:
        recording = DecomposingRecordingPen(glyphset)
        glyphset[name].draw(recording)
        outlines[name] = recording
        pen = BoundsPen(None)
        recording.replay(pen)
        boxes[name] = pen.bounds
    return outlines, boxes


def bounds(glyphset, name):
    pen = BoundsPen(glyphset)
    glyphset[name].draw(pen)
    return pen.bounds


def strip_kern(font):
    if "kern" in font:
        del font["kern"]
    if "GPOS" not in font:
        return
    features = font["GPOS"].table.FeatureList.FeatureRecord
    kept = [f for f in features if f.FeatureTag != "kern"]
    font["GPOS"].table.FeatureList.FeatureRecord = kept
    font["GPOS"].table.FeatureList.FeatureCount = len(kept)


def make_mono(font, cell, min_ink=0.0, max_stretch=1.0):
    """Rewrite every glyph to fit `cell`; return the condensed and stretched ones."""
    glyphset = font.getGlyphSet()
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    order = font.getGlyphOrder()
    condensed, stretched = [], []

    codepoints = {}
    for codepoint, name in font.getBestCmap().items():
        codepoints.setdefault(name, []).append(codepoint)

    outlines, boxes = outlines_and_bounds(glyphset, order)

    for name in order:
        advance, _ = hmtx[name]
        if advance == 0:
            continue  # combining marks and friends: keep them on top of their base
        box = boxes[name]
        pen = TTGlyphPen(None)
        if box is not None:
            xmin, _, xmax, _ = box
            ink = xmax - xmin
            scale = 1.0 if ink <= cell * INK_SHARE else (cell * INK_SHARE) / ink
            if scale != 1.0:
                condensed.append((name, scale))
            # Only ASCII sets the reading rhythm: growing accents and punctuation
            # outside it would just make those glyphs heavier than their base letters.
            ascii_only = codepoints.get(name) and all(0x21 <= cp <= 0x7E for cp in codepoints[name])
            if ascii_only and ink > 0 and ink < min_ink * cell:
                grow = min(min_ink * cell / ink, max_stretch)
                if grow > 1.0:
                    scale *= grow
                    stretched.append((name, grow))
            dx = (cell - ink * scale) / 2 - xmin * scale
            outlines[name].replay(TransformPen(pen, Transform(scale, 0, 0, 1, dx, 0)))
        glyph = pen.glyph()
        assert not glyph.isComposite(), f"{name}: not decomposed"
        glyph.coordinates = GlyphCoordinates([(otRound(x), otRound(y)) for x, y in glyph.coordinates])
        glyph.recalcBounds(glyf)
        glyf[name] = glyph
        hmtx[name] = (cell, glyph.xMin)

    font["hhea"].advanceWidthMax = cell
    font["post"].isFixedPitch = 1
    font["OS/2"].panose.bProportion = 9
    if font["OS/2"].version >= 3:
        font["OS/2"].xAvgCharWidth = cell
    strip_kern(font)
    return condensed, stretched


def check(font, cell):
    """Fail loudly if the result is not a monospaced grid."""
    glyphset = font.getGlyphSet()
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    for name in font.getGlyphOrder():
        advance, lsb = hmtx[name]
        if advance not in (0, cell):
            raise AssertionError(f"{name}: advance {advance} != {cell}")
        if advance == 0:
            continue
        box = bounds(glyphset, name)
        if box is None:
            continue
        xmin, _, xmax, _ = box
        if xmin < -0.5 or xmax > cell + 0.5:
            raise AssertionError(f"{name}: ink {xmin}..{xmax} escapes cell 0..{cell}")
        # recalcBounds (control-point bbox) is what hmtx must agree with
        if lsb != glyf[name].xMin:
            raise AssertionError(f"{name}: lsb {lsb} != xMin {glyf[name].xMin}")
    if "kern" in font:
        raise AssertionError("kern table still present")
    if not font["post"].isFixedPitch:
        raise AssertionError("post.isFixedPitch not set")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source")
    parser.add_argument("dest")
    parser.add_argument("--cell-em", type=float, default=0.636,
                        help="advance width as a fraction of the em (default: 0.636, DepartureMono Mono)")
    parser.add_argument("--min-ink", type=float, default=0.0,
                        help="grow ASCII glyphs whose ink is below this share of the cell (default: off)")
    parser.add_argument("--max-stretch", type=float, default=1.35,
                        help="cap on how far --min-ink may widen a glyph (default: 1.35)")
    args = parser.parse_args()

    font = TTFont(args.source)
    upem = font["head"].unitsPerEm
    cell = otRound(upem * args.cell_em)
    condensed, stretched = make_mono(font, cell, args.min_ink, args.max_stretch)
    check(font, cell)

    os.makedirs(os.path.dirname(os.path.abspath(args.dest)), exist_ok=True)
    font.save(args.dest)
    worst = sorted(condensed, key=lambda item: item[1])[:8]
    grown = sorted(stretched, key=lambda item: item[1], reverse=True)[:8]
    print(f"  {os.path.basename(args.dest)}: cell {cell} ({cell / upem:.3f}em), "
          f"{len(condensed)} condensed, narrowest: "
          + " ".join(f"{name}({scale:.2f})" for name, scale in worst))
    print(f"    {len(stretched)} grown, widest: "
          + " ".join(f"{name}({scale:.2f})" for name, scale in grown))
    return 0


if __name__ == "__main__":
    sys.exit(main())
