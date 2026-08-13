"""Take Lilex's hook for the cursive д, and build the bowl from this face's o.

Lilex (https://github.com/mishamyrt/Lilex, Mikhail Myrt) is under the SIL Open
Font License 1.1, which is what lets it be an outline donor; SUSE Mono is under
the same licence. "Lilex" is the donor's trademark and is not a name this font
may use.

Writes `tools/de_donor.py`. Run it from the repository root:

    ./venv/bin/python scripts/de_from_lilex.py

This is б's recipe, part for part, and for the same reason. д is a bowl and one
stroke, and a bowl is where a donor's own design language sits (METHOD F11), so
the bowl is this face's own o and only the hook is donated. Unlike б the hook
is not spliced onto the oval: it is kept as its own closed contour overlapping
o, which is what the letter already did and what the pipeline already accepts,
so there is no landing angle to solve and no seam to assert. Where the hook's
root swells past the plain oval it is meant to -- that swell IS the junction,
and every reference draws it.

Why Lilex and not Sudo, which is this project's donor of record and supplied
г. Sudo draws the OTHER cursive д, the one with a descender, shaped like a g.
Both forms are real and this face has settled on the ∂ form, so Sudo's is the
wrong letter here -- rule 9, METHOD F13. Of the OFL italics on this machine
that draw the ∂ form, Lilex is the one whose weights are structurally
identical: its Thin and Bold italics carry the same segments in the same order,
which is what lets them serve as a weight axis. The static families that do not
(JetBrains Mono, Ioskeley) differ by a node or two per contour, and a font
whose masters disagree on node count does not build.

What comes back to this face, all of it measured by `tools/gd_band.py` over
the eleven monospace italics that actually draw the cursive:

  * the bowl -- this face's own o, untouched, which settles the counter, the
    overshoot, the x-height and the fitting for nothing;
  * the height, 1.38 of o's (panel 1.31..1.50), which is where Lilex already
    draws it;
  * the width, 1.04 of o's (panel 1.00..1.15), fitted LEANING -- see METHOD
    F16, and note the letter this replaces read 1.25;
  * the hook's weight, 0.89 of o's own wall (panel 0.86..0.93), solved on
    Lilex's own two weights read as an axis. Almost exactly what б's branch
    weighs against the same bowl, which is worth noticing: the two letters are
    the same construction in mirror and the panel says so.
"""
import math
import os
import sys

sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")

import glyphsLib
from geom import area, bbox
from params import Params, Lower, _flatten
from donor import (blend, centre, emit, leaning, mapped, mask,
                   poly, pts_of, same_drawing, splice, stand_up, trim,
                   to_nodes, to_segs)

FILES = ("Lilex-ThinItalic.otf", "Lilex-BoldItalic.otf")
CP = 0x0434
OUT = "tools/de_donor.py"
SRC = "sources/SUSEMono-Italic.glyphs"

# What the letter should measure, over this face's own o -- `tools/gd_band.py`.
DE_HOOK = 0.89          # the hook's weight over o's wall   panel 0.86..0.93
DE_WIDE = 1.04          # the whole letter's width over o's panel 1.00..1.15

# Lilex draws this letter as one stroke: up the bowl's right side, on over the
# top and back to the left, ending in a cut terminal. These are the segments of
# its outer contour that are HOOK rather than bowl -- from where the bowl's
# right wall carries on upward, round the top, and back down the hook's
# underside. Counted off by index because the two weights carry the same
# segments in the same order, which `same_drawing` asserts before anything
# else runs.
#
# Lilex's own segments 8 and 9 -- a three-unit notch where the underside meets
# the bowl's crown -- are kept, and `tools/outlines.py` flags the shorter of
# them. Dropping them was tried and is worse: the closing chord then runs from
# the underside straight to the departure point across the stroke's corner,
# which turned a 3-unit segment into a 126-degree kink and an extreme missed by
# 19 units. The whole root sits buried inside the bowl's ink and comes out in
# the overlap removal, which is the answer to all three findings there.
HOOK = (3, 4, 5, 6, 7, 8, 9)

# The terminal is the one straight segment inside the hook.
CUT = 5

# What the junction measures. The swell where the stroke grows out of the bowl
# runs 1.13 to 1.41 of o's own wall across the eleven references, median 1.21.
#
# It is not a number that is solved for -- it is what the splice produces. A
# stroke merely OVERLAPPING the oval, which is what this was, has no swell at
# all: 1.13 / 1.01 / 1.00 at Thin, Regular and ExtraBold, under everything
# measured, and it reads as a stroke grazing a bowl rather than growing out of
# one. The swell lives in the piece of the donor's outline between where its
# stroke leaves the bowl and where it comes back, and that is exactly the piece
# an overlap throws away. Spliced, it is the donor's own.
#
# The splice's own cuts land wherever the two outlines cross, and when that is
# near the end of one of the donor's segments the leftover is a STUB: at Thin
# the departure fell at 0.94 and left 36 units with a bow of 0.02, a dead
# straight piece of curve carrying its own node, which beside the arc's cut end
# made three nodes strung along one straight run. Visible at any zoom and
# invisible to every ink reading. `donor.absorb` carries the arc's last segment
# on to the stub's far end instead, which is also where the Thin junction's
# 1.34 became 1.49 -- above the panel's ceiling, and the one figure here still
# outside it.
#
# Carrying the root further down the wall was tried first, before the splice,
# and is recorded because the way it failed is worth keeping: the chord closing
# the contour then ran from the wall's inner edge to its outer one, straight
# across the counter, filling part of it in and leaving a wedge at the
# junction. The junction probe read the wedge, both masters moved toward the
# target, and the letter got worse. METHOD F6, from the other end.


def bowl_top(sg):
    """The top of the donor's own bowl -- where its crown stops rising.

    The letter's own highest point is the hook, so this is read off the segment
    that ends on the crown, which is the one the hook's notch hands over to.
    """
    return sg[HOOK[-1] + 1][1][-1][1]


def fit(sg, pr):
    """The donor's BOWL onto this face's o, at ONE scale in both directions.

    The bowl and not the letter: the bowl is what has to end up sitting on this
    face's own o, and everything else -- how far the hook rises, how far left it
    reaches -- follows at the donor's own proportion, which `tools/gd_band.py`
    puts inside the panel already.

    **One scale, and this is the whole of what was wrong with the letter.** The
    height was fitted onto o and the width fitted separately onto the panel's,
    and two independent fits are a squash: x came out 0.966 of y at Thin and
    **0.850 at ExtraBold**. A donated outline squashed in one direction is no
    longer the drawing that was donated -- it re-weights every stroke by the
    direction that stroke happens to run in, so the bowl's upright walls lost a
    seventh of their weight while the arm, which runs nearly flat where it
    ends, kept all of its, and every edge in between got steeper. That is what
    turned the terminal into an acute spike: `tools/de_arm.py` read the ink at
    the tip as 1.01 of o's wall at Thin against 0.21 at ExtraBold, over a panel
    holding 0.60..0.97, and the arm's reach fell from 0.34 to 0.26 across the
    same masters. Three readings moving together with the squash, and Thin --
    the master that was nearly square -- was the one that looked right.

    The letter's width is therefore not fitted at all now. It is what the donor
    draws at the size its bowl has to be, and it is measured rather than aimed
    at; `DE_WIDE` records the panel band it has to land in.
    """
    ox0, oy0, ox1, oy1 = bbox(pr.paths("o"))
    ps = pts_of(sg[0])
    y0 = min(q[1] for q in ps)
    k = (oy1 - oy0) / (bowl_top(sg[0]) - y0)
    mid = 0.5 * (min(q[0] for q in ps) + max(q[0] for q in ps))
    out = [mapped(c, lambda q: (300.0 + (q[0] - mid) * k,
                                oy0 + (q[1] - y0) * k)) for c in sg]
    # centred on the BOWL, so the hook lands on o and not beside it
    return centre(out, pr, 0, 0.5 * (ox0 + ox1))


def shape(a, b, t, pr):
    """The letter's outer contour: this face's o with the stroke grown out of it.

    Not the stroke laid over the bowl, which is what this was and what the
    junction reading found wanting -- a stroke that merely overlaps an oval
    meets it with no swell at all, 1.00 of the bowl's own wall at the heavy
    master against a panel that runs 1.13 to 1.41. The swell is the donor's
    and it lives in the piece of its outline between where the stroke leaves
    the bowl and where it comes back, which is exactly the piece an overlap
    throws away. `donor.splice` keeps it.

    The terminal is cut before the splice rather than after: it only moves two
    points, they are the far end of the letter from the junction, and doing it
    here means naming the segment by the index it has in the donor's own
    contour instead of the one it ends up with.
    """
    sg = fit(blend(a, b, t), pr)
    outer = trim(sg[0], CUT, pr.italic)
    ps = sorted(pr.paths("o"), key=lambda q: -abs(area(q)))
    got = splice(to_segs(ps[0]), (outer[0][1][-1], list(outer[1:])))
    if got is None:
        raise SystemExit("the stroke does not cross this face's o twice -- it "
                         "is not attached to the bowl and the letter would "
                         "come out in two pieces")
    start, segs = got
    return [("start", [start])] + segs


def solve(a, b, pr):
    """Where on the donor's two weights the hook weighs what the panel says.

    Read off the render with the bowl in place, because `weights.branch_of`
    finds the hook by where the counter stops -- the stroke above the bowl's
    own crown, trimmed at each end by the bowl's wall so the terminal's cut and
    the junction do not decide the answer. Both leaning, and at twice the
    band's own resolution: METHOD F16.
    """
    import statistics as st
    import weights as W
    from gd_band import XH as BAND_XH
    oy = bbox(pr.paths("o"))
    scale = 2.0 * BAND_XH / float(oy[3] - oy[1])
    lean = math.tan(math.radians(pr.italic))

    def over(pts):
        return [(x + (y - pr.pivot) * lean, y) for x, y in pts]

    bowl = [over(_flatten(q, 96)) for q in pr.paths("o")]
    wall = W.width(W.edt(mask([bowl], scale)))
    hole = over(_flatten(sorted(pr.paths("o"),
                                key=lambda q: -abs(area(q)))[1], 96))

    # one group, XORed: the letter is a single outer contour now, with o's own
    # counter punched out of it, and that is what the built font fills
    def ink(t):
        return mask([[over(poly(to_nodes(shape(a, b, t, pr)), 40)), hole]],
                    scale)

    def ratio(t):
        rows = W.branch_of(ink(t))
        return (st.median(rows) / wall) if rows else 99.0

    lo, hi = -1.2, 3.0
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        if ratio(mid) < DE_HOOK:
            lo = mid
        else:
            hi = mid
    t = 0.5 * (lo + hi)
    return t, ratio(t), W.width(W.edt(ink(t))) / wall


def build():
    font = glyphsLib.load(open(SRC))
    a, b, deg = same_drawing(FILES, CP, "д")
    a = [stand_up(c, deg) for c in a]
    b = [stand_up(c, deg) for c in b]
    out = []
    for mi in range(len(font.masters)):
        pr = Lower(Params(font, mi))
        t, got, jn = solve(a, b, pr)
        sh = shape(a, b, t, pr)
        # the width is measured now, not aimed at -- see `fit`
        wide = leaning(pts_of(sh), pr.italic, pr.pivot) / leaning(
            [q for q in _flatten(max(pr.paths("o"), key=lambda q: abs(area(q))),
                                 16)], pr.italic, pr.pivot)
        print("  master %d  donor axis %+.2f   hook %.2f (wanted %.2f)   "
              "junction %.2f (panel 1.13..1.41 -- see DE_JOIN)   "
              "width %.2f (panel 1.00..1.15)"
              % (mi, t, got, DE_HOOK, jn, wide))
        out.append((t, [to_nodes(sh)]))
    n = {tuple(len(p) for p in ps) for _t, ps in out}
    if len(n) != 1:
        raise SystemExit("the masters came out with different nodes, %s -- the "
                         "font will not build" % n)
    return out


def main():
    emit(OUT, "DE", """The cursive д's hook, taken from Lilex and fitted here.

Generated by scripts/de_from_lilex.py -- edit that, not this.
Lilex is under the SIL Open Font License 1.1, which is what lets
it be an outline donor here. Held as data rather than read from
the donor at build time so the repository builds without a font
that lives outside it.

The BOWL is not here: it is this face's own o, added by the
recipe. Only the hook is the donor's, closed off across its own
root and left to overlap the bowl.

UN-SHEARED, like every outline a recipe sees. One entry per
master, in source order: contours of (x, y, type, smooth).
""", build())


if __name__ == "__main__":
    main()
