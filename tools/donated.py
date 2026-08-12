"""Is every letter the Latin donates still exactly the Latin's?

    ./venv/bin/python tools/donated.py

Twenty-five Cyrillic characters are not drawn at all: they are the face's own
Latin, referenced as a component, so they follow it through the weight axis
and carry its optical fitting for nothing. That is the cheapest correct answer
this project has, and it stays correct only as long as three things hold.

1. **Each is a single component of its declared donor, at the origin, in both
   masters.** A decomposed donation looks identical on the day it happens and
   then stops tracking the Latin -- silently, because nothing else compares
   them.
2. **Each is byte-identical to its donor in every built weight.** The source
   can be right and the build wrong.
3. **No letter this project DREW is secretly a Latin letter**, or a Latin
   letter mirrored. The first would be a redraw of something already in the
   font; the second breaks the face's own rule -- И, Я, Э are not flipped N, R
   and C, and a mirror would show up here as an exact match under reflection.

The donation list itself is a design judgement and is not checked here, only
declared: А В Е І К М Н О Р С Т Х Ѕ Ј and а е і о р с у х ѕ ј. What makes it
honest is that every one is a letter Cyrillic and Latin genuinely share. The
letters that only LOOK shareable are drawn instead, and that is the whole
list: т is not the Latin t, п is not n, и is not a mirrored N, м is not m,
н is not h, к takes only k's arm and leg.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import glyphsLib                                              # noqa: E402
from fontTools.ttLib import TTFont                            # noqa: E402

from probe import contours                                    # noqa: E402
from classify import TIERS                                    # noqa: E402

WEIGHTS = ("Thin", "Regular", "Bold", "ExtraBold")
F = "fonts/ttf/SUSEMono-%s.ttf"
SRC = "sources/SUSEMono.glyphs"


def declared():
    """(letter, glyph name, donor glyph) for every tier 1 entry.

    The Ukrainian apostrophe is tier 1 too and takes `quoteright`, which is a
    glyph name rather than the character it draws -- the built-font half of
    the check reads characters, so it is compared in the source only.
    """
    return [(chr(cp), name, note) for cp, name, tier, note in TIERS
            if tier == 1]


def as_component(font, name, donor):
    out = []
    for mi, _ in enumerate(font.masters):
        layer = font.glyphs[name].layers[mi]
        pos = layer.components[0].position if len(layer.components) == 1 else None
        if (layer.paths or len(layer.components) != 1
                or layer.components[0].name != donor
                or (pos and tuple(pos) != (0, 0))):
            out.append("%s master %d is not a plain component of %s"
                       % (name, mi, donor))
    return out


def same_built(cy, donor):
    out = []
    for w in WEIGHTS:
        f = TTFont(F % w, lazy=True)
        try:
            cm, gs = f.getBestCmap(), f.getGlyphSet()
            if ord(cy) not in cm or ord(donor) not in cm:
                out.append("%s or %s missing from %s" % (cy, donor, w))
                continue
            a, b = cm[ord(cy)], cm[ord(donor)]
            if contours(f, a, cm, gs) != contours(f, b, cm, gs):
                out.append("%s differs from %s at %s" % (cy, donor, w))
            if f["hmtx"][a][0] != f["hmtx"][b][0]:
                out.append("%s and %s have different advances at %s"
                           % (cy, donor, w))
        finally:
            f.close()
    return out


def undeclared(donated):
    """Anything drawn that is a Latin letter, or one mirrored."""
    f = TTFont(F % "Regular", lazy=True)
    out = []
    try:
        cm, gs = f.getBestCmap(), f.getGlyphSet()
        latin = {chr(c): contours(f, cm[c], cm, gs) for c in cm
                 if 0x41 <= c <= 0x7A and chr(c).isalpha()}

        def flip(cs):
            xs = [p[0] for c in cs for p in c]
            m = min(xs) + max(xs)
            return sorted(tuple(sorted((m - x, y) for x, y in c)) for c in cs)

        for cp, name, tier, note in TIERS:
            ch = chr(cp)
            if ch in donated or cp not in cm:
                continue
            ours = contours(f, cm[cp], cm, gs)
            if not ours:
                continue
            for ln, lc in latin.items():
                if ours == lc:
                    out.append("%s is exactly %s but is drawn (%s)"
                               % (ch, ln, note))
                elif flip(ours) == flip(lc):
                    out.append("%s is %s MIRRORED (%s)" % (ch, ln, note))
    finally:
        f.close()
    return out


def main():
    font = glyphsLib.load(open(SRC))
    rows = declared()
    bad = []
    for cy, name, donor_glyph in rows:
        bad += as_component(font, name, donor_glyph)
    for cy, name, donor_glyph in rows:
        if len(donor_glyph) == 1:
            bad += same_built(cy, donor_glyph)
    bad += undeclared({cy for cy, _, _ in rows})
    print("   %d donated: %s"
          % (len(rows), " ".join(cy for cy, _, _ in rows)))
    if bad:
        print("\n".join("   !! " + b for b in bad))
        raise SystemExit(1)
    print("   every one a plain component of its donor in both masters, and "
          "identical to it in all four built weights")
    print("   nothing drawn is a Latin letter, or a Latin letter mirrored")


if __name__ == "__main__":
    main()
