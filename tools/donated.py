"""Is every letter the Latin donates still exactly the Latin's?

    ./venv/bin/python tools/donated.py

Twenty-four Cyrillic characters are not drawn at all: they are the face's own
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
declared: А В Е І М Н О Р С Т Х Ѕ Ј and а е і о р с у х ѕ ј. What makes it
honest is that every one is a letter Cyrillic and Latin genuinely share. The
letters that only LOOK shareable are drawn instead, and that is the whole
list: т is not the Latin t, п is not n, и is not a mirrored N, м is not m,
н is not h.

**К and к were on this list and came off it on 2026-08-13.** They were the one
pair the panel argued about -- 31 of 65 faces draw К apart from K -- and the
reason turned out to be structural rather than a matter of fitting. K branches:
its leg leaves the arm out in the counter and the arm carries on to the stem
underneath it. Cyrillic К does not branch; its arm and leg run together as one
neck off the stem, at the middle of the height. Of the panel faces whose Latin
K branches and which redrew the Cyrillic rather than donating it, thirteen made
exactly that change and the nine that did not are serif or display faces. So
this list is now twenty-four, and К к are built in `recipes.py: Ka` out of K's
and k's own arms and legs -- still the host's drawing, one tier down.
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


def panel():
    """How the panel solves the same 25 -- donate, or draw?

    Three answers are possible in a font file and they are not the same
    decision, so they are counted apart:

    - **one glyph**: both codepoints map to the SAME glyph. The face has
      decided the two letters are one letter, which is what this project does.
    - **two glyphs, one shape**: separate glyphs with identical outlines. The
      same design decision, kept as two glyphs so either can be moved later.
    - **drawn apart**: the outlines differ, by however little.

    A face that has no Cyrillic at all is not a vote either way and is left
    out of the count, which is why the totals differ per letter.
    """
    from panel import families
    pairs = [(cy, note) for cy, _n, note in declared() if len(note) == 1]
    tally = {cy: [0, 0, 0] for cy, _ in pairs}
    seen = 0
    apart = {cy: [] for cy, _ in pairs}
    for fam, path in families():
        try:
            f = TTFont(path, fontNumber=0, lazy=True)
        except Exception:
            continue
        try:
            cm, gs = f.getBestCmap(), f.getGlyphSet()
            if not any(ord(cy) in cm for cy, _ in pairs):
                continue
            seen += 1
            for cy, la in pairs:
                if ord(cy) not in cm or ord(la) not in cm:
                    continue
                if cm[ord(cy)] == cm[ord(la)]:
                    tally[cy][0] += 1
                elif contours(f, cm[ord(cy)], cm, gs) == \
                        contours(f, cm[ord(la)], cm, gs):
                    tally[cy][1] += 1
                else:
                    tally[cy][2] += 1
                    apart[cy].append(fam)
        except Exception:
            continue
        finally:
            f.close()
    print("   %d panel faces carry Cyrillic\n" % seen)
    print("   %-4s %-9s %-16s %-11s %s"
          % ("", "one glyph", "two, same shape", "drawn apart", "share same"))
    for cy, la in pairs:
        one, two, off = tally[cy]
        tot = one + two + off
        if not tot:
            continue
        print("   %s=%s  %-9d %-16d %-11d %.0f%%"
              % (cy, la, one, two, off, 100.0 * (one + two) / tot))
    print()
    for cy, la in pairs:
        if apart[cy]:
            print("   %s drawn apart from %s in: %s"
                  % (cy, la, ", ".join(sorted(apart[cy]))))


def main():
    if "--panel" in sys.argv:
        return panel()
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
