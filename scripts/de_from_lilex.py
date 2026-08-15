"""The cursive д: this face's own o, with the arm drawn out of its own wall.

Lilex (https://github.com/mishamyrt/Lilex, Mikhail Myrt) is under the SIL Open
Font License 1.1, which is what lets it be an outline donor; SUSE Mono is under
the same licence. "Lilex" is the donor's trademark and is not a name this font
may use.

Writes `tools/de_donor.py`. Run it from the repository root:

    ./venv/bin/python scripts/de_from_lilex.py

**What is donated here is a PATH, not an outline.** Three rounds were spent
fitting Lilex's own hook onto this face -- scaling it, blending its two weights
along an axis solved for weight, cutting its terminal, splicing its root into
o -- and the tail was rejected each time. `tools/de_arm.py` says what those
four steps left: the arm's free end came out **six times as thick as its root
at Thin and half as thick at ExtraBold**, from one donor, and the flat blunt
bar that produced reads as an awning laid over the bowl rather than a stroke
leaving it. Every step moved an end of the arm and not one of them was
answerable for how thick it was anywhere. A quantity nobody sets is a quantity
nobody can interpolate. METHOD F19.

So the donor is taken apart into the two things a donation actually carries --
where the stroke GOES, and how thick it is along the way. `donor.dissect`
pairs the arm's two edges off against each other and returns its spine and its
half-width. The spine is kept: no reading this project takes can be turned
into a path, and this face draws no stroke that does what this one does. The
half-width is thrown away and set here instead, against this face's own o
wall, because a donated thickness is a donated wall and this face has one of
its own. `donor.stroke` then draws the two edges back out as cubics.

This is not METHOD F15, which rejected a centreline stroked at a CONSTANT width
with its ends cut off square -- that has no modulation and no terminal and
reads as bent wire. This one is thicker at the root than at the free end by
the amount the panel says, and ends in the cut this face cuts.

What comes back from that:

  * the letter is ONE outline, and the arm is the bowl's own wall carrying on
    upward. The spine starts on the middle of o's right-hand wall and `splice`
    turns the departure onto the bowl's own tangent, so there is no seam;
  * the arm's weight and its taper are the constants below, and its reach,
    rise, terminal and junction are then MEASURED against the panel rather
    than aimed at -- `build` prints all five every run;
  * the bowl is this face's own o, untouched, which settles the counter, the
    overshoot, the x-height and the fitting for nothing. The panel says that
    is the right bowl: its д's right-hand side is as round as its own o's
    (0.110 against 0.141 of dev over run) and nothing like its own d's stem
    (0.009). `tools/de_vs_d.py`. д is not d;
  * no weight solve, no donor axis, no bracket guard, no absorbed stub. All
    four existed to keep an emergent thickness in band and none of them has
    anything to do any more.

Why Lilex and not Sudo, which is this project's donor of record and supplied
г. Sudo draws the OTHER cursive д, the one with a descender, shaped like a g.
Both forms are real and this face has settled on the ∂ form, so Sudo's is the
wrong letter here -- rule 9, METHOD F13. And Lilex is CFF, so its curves are
the designer's own cubics rather than quadratics expanded to a node every few
units, which matters when a spine is being read off them.
"""
import math
import sys

sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")

import glyphsLib
from geom import area, bbox
from params import Params, Lower, _flatten
from donor import (centre, dissect, emit, leaning, mapped, mask, poly,
                   pts_of, resample, same_drawing, splice, stand_up, stroke,
                   trim, to_nodes, to_segs)

FILES = ("Lilex-ThinItalic.otf", "Lilex-BoldItalic.otf")
CP = 0x0434
OUT = "tools/de_donor.py"
SRC = "sources/SUSEMono-Italic.glyphs"

# The arm's own weight, over this face's own o wall, at each end of it. These
# are SET, and everything else about the arm is measured against the panel
# afterwards -- which is the whole change. They used to be emergent: the arm's
# thickness was whatever survived a fit, a two-weight blend, a terminal cut and
# a splice, and `tools/de_arm.py` caught what that produced -- the free end six
# times the root at Thin and half of it at ExtraBold, from one donor. A
# quantity nobody sets is a quantity nobody can interpolate.
#
# The panel, over the eight monospace italics that draw the ∂ form:
#   the free end  0.79..1.09 of o's wall, median 0.88
#   the arm       0.87..0.97, median 0.93
#   free end over root, along the arm  0.81..0.91, median 0.86
#
# The free end is barely lighter than the wall: this letter does not taper
# away to a point in any of them, it thins by about a tenth and is then cut.
# That figure was 0.72 an hour ago and it was the probe, not the panel --
# `de_arm` read the widest disc that fits within a band at the very end of the
# arm, and no disc within `w` of a cut end is wider than `w`, so the band was
# being measured instead of the terminal. Read an eighth of the arm back from
# the end, clear of the corner, the same eight faces say 0.88.
DE_TIP = 0.86           # at the free end   panel 0.79..1.09
DE_ROOT = 0.98          # where it leaves the bowl's own wall

# How far the spine carries on DOWN the bowl's wall past the donor's root,
# over o's height. The stroke has to start well inside the bowl's ink so that
# `splice` has an unambiguous crossing to cut at on each side; none of this run
# is ever seen. Its width closes down over the same run so it stays inside the
# wall rather than sitting on it, which is what makes the crossing a crossing.
DE_DEEP = 0.34

# Where the two edges get a node, as fractions of the VISIBLE arm. Three
# cubics an edge, and the first of them starts down in the buried run --
# `splice` throws away whatever is inside the bowl, so a knot spent down there
# is a knot spent on nothing. The letter comes out at 16 nodes against o's 8;
# г shipped at 34 once and was rejected for it.
KNOTS = (0.0, 0.38, 0.70, 1.0)
TERM = len(KNOTS) - 1   # the terminal is the segment after the last one up

# The segments of Lilex's own outer contour that are ARM rather than bowl.
# `HOOK` is what `bowl_top` reads to know where the donor's crown stops rising,
# which is what `fit` scales onto this face's o. The two runs given to
# `dissect` are the arm's two edges, each in the direction that runs from the
# free end back towards the root: negative means that segment walked backwards.
#
# 5 is the terminal, and it is not read. Lilex's Thin cuts it 19 units long,
# straight across the stroke; its Bold cuts 126 at a shallow slant. Pairing two
# edges off either side of an oblique cut is a guess at one end, which is the
# second reason only the Thin is used here.
HOOK = (3, 4, 5, 6, 7, 8, 9)
OUTER = (-4, -3)
UNDER = (6, 7, 8, 9)


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

    The letter's width is therefore not fitted at all now. It is what the
    donor draws at the size its bowl has to be, and `build` measures it against
    the panel's 1.00..1.15 rather than aiming at it.
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


def _cross(poly, y):
    """Where a closed polyline crosses the height `y`, as x values."""
    out = []
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y):
            out.append(ax + (y - ay) * (bx - ax) / ((by - ay) or 1e-12))
    return out


def wall(pr, y=None):
    """This face's own o, read at height `y`: the middle of its right-hand
    wall, and how thick that wall is ACROSS itself.

    The arm is the bowl's wall carrying on upward, so the wall is both where
    the stroke starts and what it weighs.

    Across itself and not along a row. A row through a wall is only the wall's
    own thickness where the wall stands upright, and the arm leaves near the
    top of the bowl where it has already begun to turn: read by rows there, o's
    wall came out half again as thick as it is and its middle a long way
    outside itself, which put the arm's root off the wall and left a lump where
    the two met -- the widest disc in the letter read 1.79 of the wall at Thin
    against a panel ceiling of 1.34. METHOD F16 is the same mistake in the
    other direction: measure the quantity, not a section of it that happens to
    be easy. So take the point on the outer contour at that height and the
    point on the counter NEAREST to it, which is across the wall by
    construction wherever the wall happens to be pointing.
    """
    ps = sorted(pr.paths("o"), key=lambda q: -abs(area(q)))
    out = [q for q in _flatten(ps[0], 48)]
    inn = [q for q in _flatten(ps[1], 48)]
    if y is None:
        ys = [q[1] for q in out]
        y = 0.5 * (min(ys) + max(ys))
    xs = _cross(out, y)
    if not xs:
        raise SystemExit("this face's o has no right-hand wall at %.0f -- the "
                         "arm has nowhere to start" % y)
    a = (max(xs), y)
    b = min(inn, key=lambda q: (q[0] - a[0]) ** 2 + (q[1] - a[1]) ** 2)
    return (0.5 * (a[0] + b[0]), 0.5 * (a[1] + b[1])), math.hypot(
        a[0] - b[0], a[1] - b[1])


def _along(pts, hs, n):
    """A polyline and a width carried along it, re-cut evenly by length."""
    out = resample(pts, n)
    keep = []
    run = [0.0]
    for i in range(1, len(pts)):
        run.append(run[-1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                        pts[i][1] - pts[i - 1][1]))
    total = run[-1] or 1.0
    for k in range(n):
        want = total * k / float(n - 1)
        j = 1
        while j < len(run) - 1 and run[j] < want:
            j += 1
        f = (want - run[j - 1]) / ((run[j] - run[j - 1]) or 1.0)
        keep.append(hs[j - 1] + (hs[j] - hs[j - 1]) * f)
    return out, keep


def arm(sg, pr):
    """The arm's spine, and how thick the arm is along it.

    The spine is the donor's -- where the stroke GOES is what a donation is
    for, and no reading this project takes can be turned into a path. The
    thickness is not: it is this face's own wall at each end, tapering between
    them, because a donated thickness is a donated wall and this face has one
    of its own.

    Lilex's THIN italic and not its Bold, and one weight rather than the two
    read as an axis. Two reasons, both measured. Its Thin cuts the terminal 19
    units long, straight across the stroke, where its Bold cuts 126 units at a
    shallow slant -- and a spine is found by pairing the two edges off, which
    an oblique cut makes a guess at one end. And the axis is what stopped the
    letter interpolating: the same blend that put the donor at +0.11 for one
    master and +1.07 for the other carried Lilex's own taper, 0.25 at Thin
    against 0.80 at Bold, into two masters that then had to be one drawing.

    Below the donor's root the spine carries on down the middle of this face's
    own wall -- not along the donor's tangent, which leaves the wall as soon as
    the wall turns. That run is buried in the bowl and only exists so `splice`
    has something to cut.
    """
    spine, _half = dissect(sg, OUTER, UNDER)                 # free end -> root
    root = spine[-1]
    mid, _w = wall(pr, root[1])
    spine = [(x + (mid[0] - root[0]), y + (mid[1] - root[1]))
             for x, y in spine]
    root = spine[-1]

    oy = bbox(pr.paths("o"))
    deep = root[1] - DE_DEEP * (oy[3] - oy[1])
    bury = [wall(pr, y)[0]
            for y in [root[1] - (root[1] - deep) * k / 12.0
                      for k in range(1, 13)]]

    _m, wall_w = wall(pr)
    pts = spine + bury
    run = [0.0]
    for i in range(1, len(pts)):
        run.append(run[-1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                        pts[i][1] - pts[i - 1][1]))
    seen = run[len(spine) - 1] or 1.0
    hs = []
    for d in run:
        s = d / seen
        if s <= 1.0:
            k = DE_TIP + (DE_ROOT - DE_TIP) * s
        else:
            k = DE_ROOT * max(0.70, 1.0 - 0.9 * (s - 1.0))
        hs.append(0.5 * wall_w * k)
    pts, hs = _along(pts, hs, 160)
    return pts[::-1], hs[::-1], seen / (run[-1] or 1.0)


def shape(donor, pr):
    """The letter: this face's o with the arm drawn out of its own wall.

    One outer contour, as before -- `splice` cuts the bowl where the stroke
    leaves it and where it comes back, keeps the piece between, and turns the
    departure onto the bowl's own tangent so the wall becomes the arm without
    a corner. What is spliced in is no longer a piece of somebody else's
    letter, though: it is a stroke of this face's own weight drawn along the
    donor's path, which is the answer to a tail that was neither this face's
    nor the donor's but what four transformations left of one.
    """
    sg = fit([donor], pr)[0]
    spine, half, seen = arm(sg, pr)
    # the knots are laid over the VISIBLE arm and the buried run gets one, so
    # the same fractions mean the same places at both masters
    at_root = 1.0 - seen
    ks = [at_root + (1.0 - at_root) * k for k in KNOTS]
    st = stroke(spine, half, [0.0] + ks[1:])
    st = trim(st, TERM, pr.italic)
    ps = sorted(pr.paths("o"), key=lambda q: -abs(area(q)))
    got = splice(to_segs(ps[0]), (st[-1][1][-1], list(st)),
                 tidy=False)
    if got is None:
        raise SystemExit("the arm does not cross this face's o twice -- it is "
                         "not attached to the bowl and the letter would come "
                         "out in two pieces")
    start, segs = got
    return [("start", [start])] + segs


def readings(sh, pr):
    """What the arm came out measuring: its weight, its free end, its taper.

    Set the width and measure the rest -- these are the readings `DE_TIP` and
    `DE_ROOT` are answerable for, taken the same way `tools/de_arm.py` takes
    them off the built font, so the two can be compared before a build.
    """
    import statistics as st
    import numpy as np
    import weights as W
    from gd_band import XH as BAND_XH
    oy = bbox(pr.paths("o"))
    scale = 2.0 * BAND_XH / float(oy[3] - oy[1])
    lean = math.tan(math.radians(pr.italic))

    def over(pts):
        return [(x + (y - pr.pivot) * lean, y) for x, y in pts]

    bowl = [over(_flatten(q, 96)) for q in pr.paths("o")]
    wl = W.width(W.edt(mask([bowl], scale)))
    hole = over(_flatten(sorted(pr.paths("o"),
                                key=lambda q: -abs(area(q)))[1], 96))
    m = mask([[over(poly(to_nodes(sh), 40)), hole]], scale)
    ys, _xs = np.where(m)
    split = ys.max() + 1 - int(round((oy[3] - oy[1]) * scale))
    above = m[:split]
    e = W.edt(m)
    cols = np.where(above.any(axis=0))[0]
    k = max(1, len(cols) // 6)
    thick = [2.0 * e[:split, c].max() for c in cols]
    # the free end read the way `tools/de_arm.py` reads it -- the widest disc
    # in the few columns at the very end, not a median over a sixth of the arm,
    # which asks about the run behind the terminal and not about the terminal
    lo_c, hi_c = max(2, int(0.08 * len(cols))), max(4, int(0.20 * len(cols)))
    return (st.median(thick[k:-k]) / wl,
            2.0 * e[:split, cols[0] + lo_c:cols[0] + hi_c].max() / wl,
            st.median(thick[:k]) / st.median(thick[-k:]),
            W.width(W.edt(m)) / wl)


def build():
    font = glyphsLib.load(open(SRC))
    a, _b, deg = same_drawing(FILES, CP, "д")
    a = [stand_up(c, deg) for c in a]
    out = []
    for mi in range(len(font.masters)):
        pr = Lower(Params(font, mi))
        sh = shape(a[0], pr)
        armwt, tip, taper, jn = readings(sh, pr)
        # the width is measured, not aimed at -- see `fit`
        wide = leaning(pts_of(sh), pr.italic, pr.pivot) / leaning(
            [q for q in _flatten(max(pr.paths("o"), key=lambda q: abs(area(q))),
                                 16)], pr.italic, pr.pivot)
        print("  master %d  arm %.2f (0.87..0.97)  free end %.2f (0.79..1.09)"
              "  taper %.2f (0.81..0.91)  junction %.2f (1.13..1.34)"
              "  width %.2f (1.00..1.15)"
              % (mi, armwt, tip, taper, jn, wide))
        out.append((0.0, [to_nodes(sh)]))
    n = {tuple(len(p) for p in ps) for _t, ps in out}
    if len(n) != 1:
        raise SystemExit("the masters came out with different nodes, %s -- the "
                         "font will not build" % n)
    return out


def main():
    emit(OUT, "DE", """The cursive д, drawn here along a path taken from Lilex.

Generated by scripts/de_from_lilex.py -- edit that, not this.
Lilex is under the SIL Open Font License 1.1, which is what
lets it be an outline donor here. Held as data rather than read
from the donor at build time so the repository builds without a
font that lives outside it.

ONE contour plus o's own counter: the bowl is this face's o and
the arm is a stroke of this face's own weight grown out of its
right-hand wall, spliced so the wall carries on into it without
a seam. Nothing of the donor's own outline survives -- only the
line its arm travels along.

UN-SHEARED, like every outline a recipe sees. One entry per
master, in source order: contours of (x, y, type, smooth).
""", build())


if __name__ == "__main__":
    main()
