"""Take Lilex's cursive г whole, and fit it to this face's italic.

Lilex (https://github.com/mishamyrt/Lilex, Mikhail Myrt) is under the SIL Open
Font License 1.1, which is what lets it be an outline donor; SUSE Mono is under
the same licence. "Lilex" is the donor's trademark and is not a name this font
may use. It supplies д's hook as well -- one donor for both letters is one
design language rather than two.

Writes `tools/ge_donor.py`. Run it from the repository root:

    ./venv/bin/python scripts/ge_from_lilex.py

Why the whole outline, when б takes only a stroke. б has a bowl, and a bowl is
where a donor's own language sits (METHOD F11), so its round part had to be
this face's own o. The cursive г has no bowl and no counter and no counterpart
anywhere in this family: it is a top bar, a curve descending to the left, and a
foot running right, and this face draws no stroke that does any of that. c
bulges the wrong way and mirroring is banned; з's lower terminal exits left
where this one has to run right. Two rounds were spent reading a SPINE off the
references and stroking it at a constant width instead, and the result was
rejected -- ink laid along a centreline has no modulation and no terminals, so
it reads as bent wire whatever path it follows. METHOD F15.

**Why Lilex and not Sudo**, which is this project's donor of record for б and
supplied this letter first. Sudo's italic is a variable TrueType, so its curves
arrive as quadratics, and expanding those segment by segment -- the only
expansion that keeps the node structure identical along the axis -- gave г 34
on-curve nodes against this face's own o at 8. It measured correctly on every
reading this project takes, because all of them read the ink. As an outline it
was machine spaghetti. Lilex is CFF: 16 nodes, the designer's own cubics, with
the extremes where a drawing puts them. Its Thin and Bold italics carry the
same segments in the same order, which is what lets them serve as an axis, and
this face's two masters land INSIDE that range rather than off the end of it.

What comes back to this face, all of it from `tools/gd_band.py` over the eleven
monospace italics that actually draw the cursive -- the other eighteen slope
their upright and are not evidence about a letter they do not draw:

  * the height, 1.00 of o's, which is what every one of the eleven reads;
  * the width, 0.97 of o's (panel 0.92..1.04), fitted LEANING (METHOD F16);
  * the terminals, cut vertical in the italic's own space -- this face cuts
    213 of its 242 terminals at exactly 0 or 90 degrees;
  * the weight, 0.98 of this face's own o wall (panel 0.96..1.05). г weighs
    what o weighs, and a reader sees the two together in every word.
"""
import sys

sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")

import glyphsLib
from geom import bbox
from params import Params, Lower, _flatten
from donor import (blend, centre, emit, fit_width, leaning, mapped, mask,
                   poly, pts_of, same_drawing, square, stand_up, to_nodes)

FILES = ("Lilex-ThinItalic.otf", "Lilex-BoldItalic.otf")
CP = 0x0433
OUT = "tools/ge_donor.py"
SRC = "sources/SUSEMono-Italic.glyphs"

GE_INK = 0.98           # its stroke over o's wall     panel 0.96..1.05
GE_WIDE = 0.97          # its width over o's           panel 0.92..1.04

# The two terminal cuts. Lilex's г has four straight segments, not two: as well
# as the ends it draws a straight run along each edge where the S passes
# through its own thinnest, which is the designer's, stays, and is not a
# terminal. Named by index because both weights carry the same segments in the
# same order, which `same_drawing` asserts before any of this runs.
#
# 2 is the foot, which reaches RIGHT; 10 is the top bar, which reaches LEFT.
CUTS = ((2, max), (10, min))


def fit(sg, pr):
    """Lilex's г into this face's cell: o's height, 0.97 of o's width."""
    ox0, oy0, ox1, oy1 = bbox(pr.paths("o"))
    ps = pts_of(sg)
    x0, x1 = min(q[0] for q in ps), max(q[0] for q in ps)
    y0, y1 = min(q[1] for q in ps), max(q[1] for q in ps)
    ky = (oy1 - oy0) / (y1 - y0)
    tall = mapped(sg, lambda q: (q[0], oy0 + (q[1] - y0) * ky))
    want = GE_WIDE * leaning([q for p in pr.paths("o")
                              for q in _flatten(p, 16)], pr.italic, pr.pivot)
    mid = 0.5 * (x0 + x1)
    kx = fit_width(tall, pr, want, mid)
    out = mapped(tall, lambda q: (300.0 + (q[0] - mid) * kx, q[1]))
    return centre([out], pr)[0]


def shape(a, b, t, pr):
    sg = fit(blend(a, b, t)[0], pr)
    for i, reach in CUTS:
        sg = square(sg, i, pr.italic, reach)
    return sg


def solve(a, b, pr):
    """Where on the donor's axis this letter weighs what o's wall weighs.

    Read off the render by `weights.py`, which decides nothing: the largest
    disc that fits inside the ink is the stroke's thickness there whatever
    direction the stroke runs, and the same measure is taken of o, so the two
    are the same quantity by construction. Both leaning, and at twice the
    band's own resolution -- `weights.width` takes a pixel of bias off every
    reading and the same outline is not the same number at two sizes.
    """
    import math
    import weights as W
    from gd_band import XH as BAND_XH
    oy = bbox(pr.paths("o"))
    scale = 2.0 * BAND_XH / float(oy[3] - oy[1])
    lean = math.tan(math.radians(pr.italic))

    def over(pts):
        return [(x + (y - pr.pivot) * lean, y) for x, y in pts]

    wall = W.width(W.edt(mask([[over(_flatten(q, 96))
                                for q in pr.paths("o")]], scale)))

    def ratio(t):
        return W.width(W.edt(mask(
            [[over(poly(to_nodes(shape(a, b, t, pr)), 40))]], scale))) / wall

    lo, hi = -1.0, 2.5
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        if ratio(mid) < GE_INK:
            lo = mid
        else:
            hi = mid
    t = 0.5 * (lo + hi)
    return t, ratio(t)


def build():
    font = glyphsLib.load(open(SRC))
    a, b, deg = same_drawing(FILES, CP, "г")
    a = [stand_up(c, deg) for c in a]
    b = [stand_up(c, deg) for c in b]
    out = []
    for mi in range(len(font.masters)):
        pr = Lower(Params(font, mi))
        t, got = solve(a, b, pr)
        print("  master %d  donor axis %+.2f   г measures %.2f of o's wall, "
              "wanted %.2f" % (mi, t, got, GE_INK))
        out.append((t, [to_nodes(shape(a, b, t, pr))]))
    n = {tuple(len(p) for p in ps) for _t, ps in out}
    if len(n) != 1:
        raise SystemExit("the masters came out with different nodes, %s -- the "
                         "font will not build" % n)
    return out


def main():
    emit(OUT, "GE", """The cursive г, taken whole from Lilex and fitted here.

Generated by scripts/ge_from_lilex.py -- edit that, not this.
Lilex is under the SIL Open Font License 1.1, which is what lets
it be an outline donor here. Held as data rather than read from
the donor at build time so the repository builds without a font
that lives outside it.

UN-SHEARED, like every outline a recipe sees: the italic goes
back on in build_cyrillic. Its height is this face's o, its width
0.97 of o's leaning, its terminals cut vertical and its stroke
solved to 0.98 of o's own wall.

One entry per master, in source order: contours of
(x, y, type, smooth). Both masters carry the same nodes in the
same order.
""", build())


if __name__ == "__main__":
    main()
