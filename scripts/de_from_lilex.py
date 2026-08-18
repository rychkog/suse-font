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

# The height, in o's own heights, of the knot the seam is cut inside. It has to
# clear the arm's underside where it meets the bowl at BOTH masters -- Thin
# meets at 0.84 and ExtraBold at 0.99, so anything above 0.99 leaves the two
# cuts inside one segment and the node count stops depending on the weight.
# None puts the knot back on the arm's root, which is what broke it.
#
# 1.28 rather than the 1.12 that also gives parity: it costs six nodes, 31
# against 37, on a letter whose o is 12 and where 34 was once a rejection. The
# only reading that pays for it is Thin's taper, 0.92 against a ceiling of
# 0.91 -- and that reading moves with where this knot is put rather than with
# the drawing, which is a probe following the fitting, not a letter changing.
DE_SEAM = 1.28

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

# The height, in o's own heights, at which the bowl's fitted right shoulder
# hands over to the donor's arm. It has to clear the donor's own crown: below
# that the donor is still turning out of ITS bowl, which is flatter than ours,
# and two near-parallel curves crossing at a shallow angle read as a flat with
# a nick in it.
DE_ARM = 1.02

# The arm's SIZE, over the size the donor drew it -- one scale, about the root
# it leaves the bowl at, so the donor's path is still the donor's path and only
# its extent is this face's.
#
# `fit` puts the donor's o onto ours and lets the arm follow at the donor's own
# proportion, and that was never checked against anything: height is not among
# the readings this script prints, and the eye caught it before a probe did.
# `tools/de_arm.py` over the eight ∂-form italics:
#
#   the arm's rise above the x-height, over o's height  0.33..0.50, median 0.40
#   the arm's reach across the bowl, 0 at its left edge 0.26..0.39, median 0.32
#
# Left at the donor's own size the letter read 0.51 rise at Thin and 0.56 at
# ExtraBold -- above every one of the eight -- while reaching to 0.22 and 0.15,
# further left than any of them. Both readings say one thing, that the arm is
# too big for this bowl, and both are affine in this one number: the donor is
# Monaspace Xenon, the tallest-armed face in the panel, and its WideExtraLight
# is wider again than the Xenon the panel reads. METHOD F19 -- the height was
# emergent, so nobody could interpolate it and nobody was answerable for it.
#
# The heavy master always rises about a twentieth of o's height further than
# the light one -- its wall is thicker, and half of that thickness sits on top
# of the spine -- so one number cannot put both on the median and 0.82 is where
# the pair straddles it. It is also one of the three sizes that keep the two
# masters on the same node count, 1.00 and 0.90 being the others, and the only
# one of those three that is in band: the sizes between break parity, which is
# the seam knot's doing and not the arm's.
DE_SIZE = 0.82          # rise 0.33..0.50   reach 0.26..0.39


def ramp(t):
    """An ease that is flat to SECOND order at both ends.

    The cubic smoothstep is flat only to first order: its second derivative is
    6 at one end and -6 at the other, so anything eased with it steps in
    CURVATURE where the ease starts and stops. On a round letter that is the
    reading the eye takes, and no gate here takes it.

    It is used on the floor dive, whose top has to leave the departure's
    tangency alone -- the dive is what carries the stroke inside o so `splice`
    has a crossing, and a cubic ease would put a curvature step exactly where
    the departure was solved to have none.

    It is NOT what fixed the hollow this letter was rejected for; swapping the
    cubic for it moved that reading by nothing at all. Recorded because the
    swap looked like the fix and was not -- the hollow was in the path, not in
    the ease over it."""
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

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
    oy = bbox(pr.paths("o"))
    oh = oy[3] - oy[1]
    _m, wall_w = wall(pr)

    root = spine[-1]
    mid, _w = wall(pr, root[1])
    spine = [(x + (mid[0] - root[0]), y + (mid[1] - root[1]))
             for x, y in spine]
    spine = [(mid[0] + (x - mid[0]) * DE_SIZE, mid[1] + (y - mid[1]) * DE_SIZE)
             for x, y in spine]

    # THE BOWL'S RIGHT SHOULDER IS NOT o's. IT IS DRAWN TO RECEIVE THE ARM.
    #
    # What the eye rejected in this letter, five times, was never a rough join.
    # It was a CONCAVITY, and the measurement that finds it is the lean of the
    # edge -- dx/dy -- read down the right side. On a letter whose edge turns
    # one way throughout, that lean only ever falls as you climb. Ours jumped:
    # o's edge leans -0.52 arriving at the arm's root and the arm leaves at
    # -0.17, so the edge slowed down where it should not have, and a slowing
    # edge is the hollow that kept being circled in red.
    #
    # The jump is not the join's fault and no join can absorb it. o's shoulder
    # is simply rounder than this arm can be received by: from its widest point
    # up to the arm's root o swings from level to -1.04 where the arm wants
    # -0.17. Seating the arm lower, where the two DO lean alike, removes the
    # concavity and was measured doing it -- one turning point, nothing bending
    # the wrong way -- but it drags the whole arm a fifth of the x-height down
    # into the bowl, and at ExtraBold the two merge into a blob.
    #
    # So the bowl gives way instead, which is what the references do and what
    # was agreed: from o's widest point up to the arm's root the right side is
    # not o's contour but one curve fitted between them, leaving o's widest
    # point level -- as o itself does -- and arriving along the arm's own lean.
    # The lean therefore falls the whole way with no step anywhere, the bowl
    # carries a little more weight on its upper right than o does, and the
    # right side reads as what the sketch drew: one curve from floor to tip.
    # Below the widest point it is o's own contour still, and so are the floor,
    # the left side and the counter.
    # The shoulder is not handed back at the arm's ROOT. Between its root and
    # its own crown the donor's stroke is still turning out of the donor's
    # bowl, and that bowl is flatter than ours -- carried over, that stretch
    # runs nearly parallel to our shoulder and the two cross at a shallow
    # angle. A shallow crossing of two near-parallel curves is a flat with a
    # nick in it, which is what the silhouette showed at 0.86..0.92 with the
    # join down at 0.73. Taking the shoulder all the way up to the donor's own
    # crown puts that whole stretch INSIDE one curve, and there is no crossing
    # left to nick.
    es = [(edge(pr, oy[1] + (j / 200.0) * oh), oy[1] + (j / 200.0) * oh)
          for j in range(6, 195)]
    widest = max((e, y) for e, y in es if e is not None)[1]

    acc = [0.0]
    for i in range(1, len(spine)):
        acc.append(acc[-1] + math.hypot(spine[i][0] - spine[i - 1][0],
                                        spine[i][1] - spine[i - 1][1]))
    total = acc[-1] or 1.0

    star = oy[1] + DE_ARM * oh
    j = next((i for i in range(1, len(spine)) if spine[i][1] <= star),
             len(spine) - 1)
    f = (star - spine[j - 1][1]) / ((spine[j][1] - spine[j - 1][1]) or 1.0)
    u = (acc[j - 1] + (acc[j] - acc[j - 1]) * f) / total
    k = max(2, len(spine) // 10)
    lo, hi = max(0, j - k), min(len(spine) - 1, j + k)

    y_lo, x_lo = widest, edge(pr, widest) + DE_OUT * wall_w
    x_hi = (spine[j - 1][0] + (spine[j][0] - spine[j - 1][0]) * f
            + 0.5 * wall_w * (DE_TIP + (DE_ROOT - DE_TIP) * u))
    m_hi = ((spine[hi][0] - spine[lo][0])
            / ((spine[hi][1] - spine[lo][1]) or -1.0))
    dy = (star - y_lo) or 1.0

    def shoulder(y):
        """o's widest point to the arm's root, level at one end and along the
        arm at the other -- the plain Hermite through both."""
        t = (y - y_lo) / dy
        tt = t * t
        return ((2.0 * t - 3.0) * tt + 1.0) * x_lo \
            + (3.0 - 2.0 * t) * tt * x_hi \
            + (tt * t - tt) * dy * m_hi

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
        if y > star:
            seated.append((x, y))
            continue
        if y >= y_lo or e is None:
            seated.append((shoulder(y) - h, y))
            continue
        # below o's widest point the edge is o's own contour, a hair outside,
        # diving inside at the floor so `splice` has a crossing to cut at.
        # `ramp` is flat to second order at the top of that dive, so it does
        # not disturb the shoulder handed to it there.
        t = (y - low) / max(1.0, y_lo - low)
        dive = ramp(1.0 - min(1.0, t / DE_DIVE))
        off = (DE_OUT - (DE_OUT + DE_INSET) * dive) * wall_w
        seated.append((e + off - h, y))

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

    # THE SEAM KNOT IS PLACED BY HEIGHT, NOT BY FRACTION OF THE RUN.
    #
    # Every other knot here is a fraction of the arm, which is right for them:
    # a fraction means the same place on the drawing at both masters. It is
    # wrong for the last one, because what happens near it is not a fraction of
    # anything -- it is `splice` cutting where the arm's underside enters the
    # bowl, and that height is set by how THICK the stroke is. The heavy master
    # meets its bowl a sixth of the x-height higher than the thin one, so a cut
    # that fell inside the last segment at Thin fell one segment earlier at
    # ExtraBold and the two kept a different number of nodes. Nine sweeps over
    # knot layout, burial, arm weight and the shoulder moved that by nothing,
    # because none of them was the quantity.
    #
    # A knot at a fixed HEIGHT fixes it by construction: put it clear above
    # both crossings and the only knot left below is the buried end, so both
    # masters cut inside the same single segment whatever their weight does.
    if DE_SEAM is not None:
        oy = bbox(pr.paths("o"))
        want = oy[1] + DE_SEAM * (oy[3] - oy[1])
        acc = [0.0]
        for i in range(1, len(spine)):
            acc.append(acc[-1] + math.hypot(spine[i][0] - spine[i - 1][0],
                                            spine[i][1] - spine[i - 1][1]))
        tot = acc[-1] or 1.0
        for i in range(1, len(spine)):
            lo, hi = spine[i - 1][1], spine[i][1]
            if (lo - want) * (hi - want) <= 0.0 and lo != hi:
                f = (want - lo) / (hi - lo)
                seam = (acc[i - 1] + (acc[i] - acc[i - 1]) * f) / tot
                ks = sorted({0.0, round(seam, 6)}
                            | {round(k, 6) for k in ks if k > seam + 1e-3})
                break
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
    """What the arm came out measuring: how far it goes, and how heavy.

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
    # how far the arm goes -- up, and across. Taken off the same raster and the
    # same x-height split, the way `tools/de_arm.py` takes them off the built
    # font, so `DE_SIZE` can be aimed before anything is built.
    bcols = np.where(m[split:].any(axis=0))[0]
    rise = (split - int(np.argmax(above.any(axis=1)))) / ((oy[3] - oy[1]) * scale)
    reach = (cols[0] - bcols[0]) / float(bcols[-1] + 1 - bcols[0])
    return (st.median(thick[k:-k]) / wl,
            2.0 * e[:split, cols[0] + lo_c:cols[0] + hi_c].max() / wl,
            st.median(thick[:k]) / st.median(thick[-k:]),
            W.width(W.edt(m)) / wl, rise, reach)


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
        armwt, tip, taper, jn, rise, reach = readings(sh, pr)
        # the width is measured, not aimed at -- see `fit`
        wide = leaning(pts_of(sh), pr.italic, pr.pivot) / leaning(
            [q for q in _flatten(max(pr.paths("o"), key=lambda q: abs(area(q))),
                                 16)], pr.italic, pr.pivot)
        print("  master %d  arm %.2f (0.87..0.97)  free end %.2f (0.79..1.09)"
              "  taper %.2f (0.81..0.91)  junction %.2f (1.13..1.34)"
              "  width %.2f (1.00..1.15)  rise %.2f (0.33..0.50)"
              "  reach %.2f (0.26..0.39)"
              % (mi, armwt, tip, taper, jn, wide, rise, reach))
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
