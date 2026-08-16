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
import os
import sys

sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")

import glyphsLib
from geom import area, bbox
from params import Params, Lower, _flatten
from donor import (arm_of, centre, dissect, emit, find, leaning, mapped,
                   mask, poly, pts_of, resample, segments_of, splice,
                   stand_up, stroke, trim, to_nodes, to_segs)

# The donor, and it is a PATH donor: only where its stroke RUNS comes across,
# so what has to suit this face is the bowl it was drawn to leave. Override
# with SUSE_DE_DONOR to try another. `tools/de_paths.py` lays every candidate's
# own stroke over this face's o; `tools/de_seam.py` shows what each does where
# the arm lands, which is where a badly suited path shows first.
#
# It must be OFL, and it should be CFF: a variable TrueType arrives as
# quadratics with a node every few units, and the spine is read off the nodes.
DONOR = os.environ.get("SUSE_DE_DONOR",
                       "MonaspaceXenon-WideExtraLightItalic.otf")
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
DE_TIP = 0.82           # at the free end   panel 0.79..1.09
DE_ROOT = 0.86          # where it leaves the bowl's own wall

# How far the spine carries on DOWN the bowl's wall past the donor's root,
# over o's height. The stroke has to start well inside the bowl's ink so that
# `splice` has an unambiguous crossing to cut at on each side; none of this run
# is ever seen. Its width closes down over the same run so it stays inside the
# wall rather than sitting on it, which is what makes the crossing a crossing.
DE_DEEP = 0.46


# Where the two edges get a node, as fractions of the VISIBLE arm. Three
# cubics an edge, and the first of them starts down in the buried run --
# `splice` throws away whatever is inside the bowl, so a knot spent down there
# is a knot spent on nothing. The letter comes out at 16 nodes against o's 8;
# г shipped at 34 once and was rejected for it.
KNOTS = (0.0, 0.26, 0.52, 0.76, 1.0)
# Whether the departure gets a node of its own. It does, and it has to, for a
# reason that is about the fitting and not about the drawing: without one, the
# lowest cubic of each edge spans the seated run AND the free arm, and a curve
# fitted across a piece of o's own contour and a piece of the donor's path
# averages the two into a straight line. Read down the right edge, the samples
# bending the wrong way go from six to two once the departure has a node.
#
# It was tried once BEFORE the arm was seated on o and it made things worse --
# a bulge that took the widest disc to 1.57 of o's wall -- which is the usual
# shape of things: a fix aimed at a symptom moves it, and the same fix aimed at
# a cause works. METHOD F19.
DE_ROOT_KNOT = True

# Over how much of o's height the path is handed over from the donor's bowl to
# this face's, just below the crown. Wide is wrong: spread all the way down to
# the donor's own root, the hand-over is still only half done where the arm
# actually leaves the bowl, so the two edges part company with a curvature
# break -- a visible corner with the arm bulging four units outside o, and the
# straight stretch below it (which is o's own wall, and correct) reading as
# part of the same fault. Kept to a band just under the crown, the letter is
# this face's own o everywhere below the departure and the join has nothing to
# break.
DE_HAND = 0.20

# How far INSIDE o's own outer contour the seated arm sits, in walls. Seated
# exactly on it, the two outlines are tangent for a long run and `splice` has
# no crossing to cut at -- it reports the arm as unattached. A hair inside, the
# outline below the crown is o's own and nothing else, which is the point.
DE_INSET = 0.22         # how far INSIDE o the stroke dives at the floor

# How far OUTSIDE o's own contour the stroke's outer edge rides up the bowl's
# right side, in walls. A hair is enough: it only has to be the outline rather
# than sit under it. And over what share of the run from the floor to the crown
# it climbs out of the dive.
DE_OUT = 0.02
DE_DIVE = 0.55

def fit(sg, o, pr):
    """The donor's own o onto this face's o, at ONE scale in both directions.

    Its own **o** and not its bowl. A д's bowl is not a shape two faces agree
    on -- that is the whole reason this letter has been hard -- and an o is.
    Everything else, how far the arm rises and how far left it reaches, then
    follows at the donor's own proportion.

    **One scale**, and fitting x and y separately was one of this letter's
    faults: the height went onto o and the width onto the panel's, and x came
    out 0.966 of y at Thin and 0.850 at ExtraBold. A donated outline squashed
    in one direction is no longer the drawing that was donated -- every stroke
    is re-weighted by the direction it happens to run in and every diagonal is
    at a new angle. METHOD F18. The width is not fitted at all now; `build`
    measures it against the panel's 1.00..1.15.
    """
    ox0, oy0, ox1, oy1 = bbox(pr.paths("o"))
    ps = [q for c in o for q in pts_of(c)]
    dy0, dy1 = min(q[1] for q in ps), max(q[1] for q in ps)
    dx0, dx1 = min(q[0] for q in ps), max(q[0] for q in ps)
    k = (oy1 - oy0) / float(dy1 - dy0)
    mid = 0.5 * (dx0 + dx1)

    def put(c):
        return mapped(c, lambda q: (300.0 + (q[0] - mid) * k,
                                    oy0 + (q[1] - dy0) * k))

    out = [put(c) for c in sg] + [put(c) for c in o]
    # centred on the donor's own o, so the arm lands over this face's bowl
    both = centre(out, pr, len(sg), 0.5 * (ox0 + ox1))
    return both[:len(sg)], both[len(sg):]


def _cross(poly, y):
    """Where a closed polyline crosses the height `y`, as x values."""
    out = []
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ay > y) != (by > y):
            out.append(ax + (y - ay) * (bx - ax) / ((by - ay) or 1e-12))
    return out


def edge(pr, y):
    """Where this face's own o has its right-hand OUTER edge at height `y`."""
    ps = sorted(pr.paths("o"), key=lambda q: -abs(area(q)))
    xs = _cross([q for q in _flatten(ps[0], 48)], y)
    return max(xs) if xs else None


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
    return ((0.5 * (a[0] + b[0]), 0.5 * (a[1] + b[1])),
            math.hypot(a[0] - b[0], a[1] - b[1]))


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


def arm(sg, runs, pr):
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
    spine, _half = dissect(sg, *runs)                        # free end -> root
    root = spine[-1]
    mid, _w = wall(pr, root[1])
    spine = [(x + (mid[0] - root[0]), y + (mid[1] - root[1]))
             for x, y in spine]
    root = spine[-1]

    # THE LETTER'S WHOLE RIGHT-HAND SIDE IS ONE STROKE.
    #
    # Not a bowl with a leg attached to it -- that construction cannot draw
    # what the references draw, and four rounds were spent proving it. A bowl
    # and an arm joined together bulge where they meet, whatever the join is
    # made of: with the seam spliced, with the seam merely overlapped, with the
    # arm seated on the wall, seated on the contour, floored against the bowl's
    # own circle or held under it, the letter's right edge turned the wrong way
    # by the same amount in the same place every time. Read down that edge, the
    # five reference д's never turn the wrong way once in eighteen samples.
    # They have no join there to turn at.
    #
    # So the stroke runs the whole way: from the arm's tip, down the right side
    # of the bowl, to its floor. Its outer edge sits a hair OUTSIDE this face's
    # o all the way, so that edge -- one continuous drawn curve -- is what the
    # letter shows, and o supplies the floor, the left side and the crown. At
    # the very bottom the stroke dives inside o so `splice` has a crossing to
    # cut at, and that dive is buried in the bowl's own ink.
    #
    # Seated on the middle of the wall instead -- which is where it was -- the
    # arm is narrower than the wall, so it runs up INSIDE o and then has to
    # push out through it at the departure and come back in. That is an
    # inflection, and an inflection is a flat spot where it turns over. Read
    # down the right edge at ExtraBold: o's own wall bends steadily at -2 to
    # -3 units per twentieth of its height, the arm leaves at 0.80 bending
    # **+2.8, the other way**, passes through zero at the x-height and comes
    # back. That reversal is what this letter was rejected for twice, and the
    # second time it was named -- "for some reason that part is flat".
    #
    # With the outer edge on o's own contour there is nothing to push through
    # and nothing to come back from: the bowl's right side and the arm are one
    # curve, bending one way throughout. That is what the references draw. The
    # donor's own д does not stand on a plain o either -- its right side IS the
    # stroke coming down, and it was chosen for exactly that. The counter is
    # still this face's o, untouched, and so is the bowl everywhere else.
    #
    # The widths have to be known before the arm can be seated, and they are
    # measured along the spine, so it goes round twice: place, measure, seat,
    # measure again. Both passes are arithmetic on 160 points.
    oy = bbox(pr.paths("o"))
    oh = oy[3] - oy[1]
    crown = oy[3] - 0.04 * oh
    span = DE_HAND * oh
    _m, wall_w = wall(pr)

    def with_bury(sp):
        low = sp[-1][1] - DE_DEEP * oh
        return sp + [wall(pr, y)[0]
                     for y in [sp[-1][1] - (sp[-1][1] - low) * k / 12.0
                               for k in range(1, 13)]]

    def widths(pts, n):
        run = [0.0]
        for i in range(1, len(pts)):
            run.append(run[-1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                            pts[i][1] - pts[i - 1][1]))
        seen = run[n - 1] or 1.0
        hs = []
        for d in run:
            u = d / seen
            if u <= 1.0:
                k = DE_TIP + (DE_ROOT - DE_TIP) * u
            else:
                k = DE_ROOT * max(0.70, 1.0 - 0.9 * (u - 1.0))
            hs.append(0.5 * wall_w * k)
        return run, seen, hs

    n = len(spine)
    pts = with_bury(spine)
    _run, _seen, hs = widths(pts, n)

    low = pts[-1][1]
    seated = []
    for (x, y), h in zip(pts, hs):
        e = edge(pr, y)
        if y >= crown or e is None:
            seated.append((x, y))
            continue
        # how far outside o's own contour this stretch of the stroke sits:
        # a hair out over the bowl's side, diving inside at the floor
        t = (y - low) / max(1.0, crown - low)
        dive = 1.0 - min(1.0, t / DE_DIVE)
        dive = dive * dive * (3.0 - 2.0 * dive)
        off = (DE_OUT - (DE_OUT + DE_INSET) * dive) * wall_w
        u = min(1.0, (crown - y) / span)
        u = u * u * (3.0 - 2.0 * u)
        seated.append((x + ((e - h + off) - x) * u, y))

    run, seen, hs = widths(seated, n)
    pts, hs = _along(seated, hs, 160)
    return pts[::-1], hs[::-1], seen / (run[-1] or 1.0)


def shape(donor, o, runs, pr):
    """The letter: this face's o with the arm drawn out of its own wall.

    One outer contour, as before -- `splice` cuts the bowl where the stroke
    leaves it and where it comes back, keeps the piece between, and turns the
    departure onto the bowl's own tangent so the wall becomes the arm without
    a corner. What is spliced in is no longer a piece of somebody else's
    letter, though: it is a stroke of this face's own weight drawn along the
    donor's path, which is the answer to a tail that was neither this face's
    nor the donor's but what four transformations left of one.
    """
    sg, _o = fit(donor, o, pr)
    spine, half, seen = arm(sg[0], runs, pr)
    # the knots are laid over the VISIBLE arm and the buried run gets one, so
    # the same fractions mean the same places at both masters
    at_root = 1.0 - seen
    ks = [at_root + (1.0 - at_root) * k for k in KNOTS]
    ks = [0.0] + (list(ks) if DE_ROOT_KNOT else ks[1:])
    st = stroke(spine, half, ks)
    st = trim(st, len(ks) - 1, pr.italic)
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
    path = find(DONOR)
    a, deg = segments_of(path, CP)
    o, _ = segments_of(path, ord("o"))
    a = [stand_up(c, deg) for c in a]
    o = [stand_up(c, deg) for c in o]
    ys = [q[1] for c in o for q in pts_of(c)]
    # a margin, because a bowl's own crown can poke a unit or two above the
    # o's top and a segment ending there is not arm. Monaspace Xenon's does,
    # and its terminal was found on the bowl.
    crown = max(ys) + 0.05 * (max(ys) - min(ys))
    # the outer contour: the one whose box holds the others
    outer = max(a, key=lambda c: (max(q[0] for q in pts_of(c))
                                  - min(q[0] for q in pts_of(c)))
                * (max(q[1] for q in pts_of(c))
                   - min(q[1] for q in pts_of(c))))
    a = [outer] + [c for c in a if c is not outer]
    runs = arm_of(outer, crown)
    print("  %s: the arm is segments %s and %s of its outer contour"
          % (DONOR, runs[0], runs[1]))
    out = []
    for mi in range(len(font.masters)):
        pr = Lower(Params(font, mi))
        sh = shape(a, o, runs, pr)
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
