"""Is a bowl this face's bowl? Read the counter, against the face's own o.

    ./venv/bin/python tools/bowls.py            # б в ь ъ ю ф я
    ./venv/bin/python tools/bowls.py б ю        # named letters only

A counter is the honest witness to a bowl's shape. It is its own contour, so
it needs no guessing about where one stroke stops and the next begins, and how
much of its own box it fills says directly what the outline is doing: a true
oval fills pi/4 = 0.785, a rounded rectangle with straight sides fills well
over 0.8, and a bowl cut off by something growing out of it fills less.

The reading that matters is not the fill but the DIFFERENCE from the same
face's o. That difference is the most unanimous thing the panel has been asked:
for б, sixty faces hold it inside 0.014, median 0.001, at a counter width
median of exactly 1.00 of o's. It says a bowl's shape is not a design decision
a Cyrillic letter gets to make -- the face already made it, in o.

Height is the part that IS a decision: the panel's median counter height is
0.95 of o's and falls to about 0.85 at the heavy end, so a shorter bowl is
ordinary and a differently-shaped one is not.

Not a gate, because most of the letters below have a bowl only in the loose
sense and the reading is only sharp for the ones that carry a real oval. It is
the check that would have caught F11 a day earlier.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from fontTools.ttLib import TTFont

from panel import families
from probe import compare, contours, stem_of

LETTERS = "бвьъюфя"


def shoelace(p):
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1)
                     in zip(p, p[1:] + p[:1]))


def counter(ps):
    """The largest hole -- the contour wound against the biggest one."""
    if not ps or len(ps) < 2:
        return None
    ar = sorted(((abs(shoelace(p)), shoelace(p), p) for p in ps),
                key=lambda t: -t[0])
    holes = [t for t in ar[1:] if (t[1] > 0) != (ar[0][1] > 0)]
    return holes[0][2] if holes else None


def read(ps):
    c = counter(ps)
    if c is None:
        return None
    xs = [q[0] for q in c]
    ys = [q[1] for q in c]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    if w <= 0 or h <= 0:
        return None
    return abs(shoelace(c)) / (w * h), w, h


def gather(letters):
    """{letter: [(stem over em, (fill difference, width, height)), ...]}

    The stem comes back with every reading because the comparison has to be
    bucketed by weight: a bowl's height is not a flat proportion -- the panel
    holds 0.95 of o at the light end and about 0.85 at the heavy -- and a flat
    band over all sixty faces would call a correct heavy bowl an outlier. That
    is F4, and this probe exists to catch F11, not to commit F4.
    """
    out = {ch: [] for ch in letters}
    for _fam, path in families():
        f = TTFont(path, fontNumber=0, lazy=True)
        try:
            cm, gs = f.getBestCmap(), f.getGlyphSet()
            s = stem_of(f, cm, gs)
            o = read(contours(f, "o", cm, gs) or [])
            if not s or not o:
                continue
            s /= float(f["head"].unitsPerEm)
            for ch in letters:
                v = read(contours(f, ch, cm, gs) or [])
                if v:
                    out[ch].append((s, (v[0] - o[0], v[1] / o[1],
                                        v[2] / o[2])))
        except Exception:
            pass
        finally:
            f.close()
    return out


WHAT = ("fill vs own o", "width of o's", "height of o's")


def main():
    letters = "".join(sys.argv[1:]) or LETTERS
    panel = gather(letters)

    import glyphsLib
    from params import Params, Lower, _flatten
    import recipes as RU
    from classify import TIERS
    font = glyphsLib.load(open("sources/SUSEMono.glyphs"))
    names = {chr(cp): n for cp, n, _t, _note in TIERS if n in RU.RECIPES}

    for ch in letters:
        rows = panel.get(ch) or []
        if len(rows) < 8:
            print("%s  only %d panel faces draw it -- not read"
                  % (ch, len(rows)))
            continue
        print("=" * 72)
        for mi in range(len(font.masters)):
            pr = Lower(Params(font, mi))
            fn = RU.RECIPES.get(names.get(ch, ""))
            ps = ([_flatten(p, 48) for p in fn(pr._pr)] if fn else
                  [_flatten(p, 48) for p in pr.paths(ch)])
            mine = read(ps)
            o = read([_flatten(p, 48) for p in pr.paths("o")])
            if not mine or not o:
                continue
            got = (mine[0] - o[0], mine[1] / o[1], mine[2] / o[2])
            stem = pr._pr.stem / float(font.upm)
            for i, what in enumerate(WHAT):
                pts = [(s, v[i]) for s, v in rows]
                c = compare(pts, stem, got[i])
                if c is None:
                    continue
                med, lo, hi, inside = c
                print("%s %-10s %-14s %+.3f   panel %+.3f .. %+.3f "
                      "median %+.3f%s"
                      % (ch, font.masters[mi].name, what, got[i], lo, hi, med,
                         "" if inside else "   OUTSIDE THE PANEL"))


if __name__ == "__main__":
    main()
