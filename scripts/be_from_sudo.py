"""Take Sudo's б for its branch, and build the bowl from this face's own o.

Sudo (https://github.com/jenskutilek/sudo-font, Jens Kutilek) is under the SIL
Open Font License 1.1, which is what lets it be an outline donor; SUSE Mono is
under the same licence. "Sudo" is the donor's trademark and is not a name this
font may use.

Writes `tools/be_donor.py`. Run it from the repository root:

    ./venv/bin/python scripts/be_from_sudo.py

What it does, in order:

  * takes the donor at its own two weights and no further, one for each master.
    Its axis used to be extrapolated, which is right when the donor supplies
    the whole letter and wrong now that it supplies one stroke: this face's
    Thin wants a branch 0.92 of a 29-unit bowl wall and Sudo's own lightest,
    fitted to this cell, draws 2.0 of it, so reaching this face's weight that
    way means extrapolating until the stroke falls apart -- which it does,
    the root collapsing and the terminal thinning to a hairline;
  * anchors the outline on two heights this face owns, the baseline under the
    bowl and the top of o, so the overshoot and the x-height are this face's;
  * stretches what is above the x-height on its own to reach this face's
    ascender, because Sudo's б stands 1.34 x-heights and this face's lowercase
    stands 1.50 to 1.57;
  * fits the width to o's, because the cell is not optional;
  * squares the terminal, because this face cuts 213 of its 242 terminals at
    exactly 0 or 90 degrees and the donor cuts this one oblique;
  * and then throws the donor's bowl away and keeps only its branch, because
    the bowl is where a donor's own design language sits. Sudo draws rounded
    rectangles: its counter fills 0.854 of its own box and so does its o's, so
    the letter is right for Sudo and wrong here, where o fills 0.810. Across
    sixty faces б's counter matches its OWN o to within 0.014 -- median 0.001,
    width ratio 1.00 -- which makes it the one relation about this letter the
    panel is unanimous on. So the bowl is built from this face's o, squashed
    to the height the donor gave the bowl, and the branch is spliced onto it;
  * and reweights the branch to this face, by moving its underside toward its
    outer edge -- each point by a share of its OWN distance across the stroke,
    so the taper survives. The panel puts a branch at 0.92 of its own bowl's
    wall at this face's Thin and 0.97 at its ExtraBold, taken
    nearest-neighbour by stem.
"""
import math
import sys

sys.path.insert(0, "tools")

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

import glyphsLib
from geom import area, bbox
from params import Params, Lower, _flatten
from probe import contours, runs, vruns

SUDO = ("/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/"
        "Sudo[YTDE,wght].ttf")
LO, HI = 200, 700
OUT = "tools/be_donor.py"


def load(w):
    return instantiateVariableFont(TTFont(SUDO), {"wght": w}, inplace=False,
                                   updateFontNames=False)


def be_glyph(f):
    return f["glyf"][f.getBestCmap()[0x0431]]


def o_wall(polys):
    """o's left wall over its own height, at half height.

    Read off o and not off б. Measured on б the same scanline crosses the
    wall where the branch grows out of it, which is thicker: solved against
    that, the letter came out an eighth heavier than the panel's heaviest б
    at every master.
    """
    ys = [q[1] for p in polys for q in p]
    r = runs(polys, (min(ys) + max(ys)) / 2.0)
    return (r[0][1] - r[0][0]) / (max(ys) - min(ys))


def donor_wall(f):
    return o_wall(contours(f, "o", f.getBestCmap(), f.getGlyphSet()))


def blend(a, b, t, into):
    for i in range(len(a)):
        into.coordinates[i] = (a[i][0] + (b[i][0] - a[i][0]) * t,
                               a[i][1] + (b[i][1] - a[i][1]) * t)


def segments(w):
    """The donor's contours as (kind, points) segments, quadratics expanded.

    Not qu2cu. A fitted conversion splits where the curvature asks it to and
    the two ends of the axis ask differently -- the same glyph came out 28
    nodes at one weight and 25 at the other, which is a font that will not
    build. A quadratic converts to a cubic exactly and TrueType's implied
    on-curve points are midpoints, so expanding those gives the same node for
    the same node at every weight.
    """
    pen = RecordingPen()
    be_glyph(w).draw(pen, w["glyf"])
    out, cur, at = [], None, (0.0, 0.0)
    for verb, pts in pen.value:
        if verb == "moveTo":
            cur, at = [("start", [pts[0]])], pts[0]
        elif verb == "lineTo":
            cur.append(("line", [pts[0]]))
            at = pts[0]
        elif verb == "qCurveTo":
            offs, end = list(pts[:-1]), pts[-1]
            if end is None:
                end = ((offs[0][0] + offs[-1][0]) / 2.0,
                       (offs[0][1] + offs[-1][1]) / 2.0)
            for i, c in enumerate(offs):
                nxt = end if i == len(offs) - 1 else (
                    (c[0] + offs[i + 1][0]) / 2.0,
                    (c[1] + offs[i + 1][1]) / 2.0)
                cur.append(("curve", [
                    (at[0] + 2.0 / 3.0 * (c[0] - at[0]),
                     at[1] + 2.0 / 3.0 * (c[1] - at[1])),
                    (nxt[0] + 2.0 / 3.0 * (c[0] - nxt[0]),
                     nxt[1] + 2.0 / 3.0 * (c[1] - nxt[1])),
                    nxt]))
                at = nxt
        elif verb in ("closePath", "endPath"):
            out.append(cur)
            cur = None
    return out


def degenerate(a, b):
    """Segment indices that collapse to nothing in EITHER master.

    Dropped in both, so the two layers keep the same nodes. Left in, they are
    two nodes on top of each other, which the mechanical check reports and
    which Glyphs treats as a nick in the outline.
    """
    bad = set()
    for ci, (ca, cb) in enumerate(zip(a, b)):
        at_a, at_b = ca[0][1][0], cb[0][1][0]
        for si in range(1, len(ca)):
            ea, eb = ca[si][1][-1], cb[si][1][-1]
            if (abs(ea[0] - at_a[0]) < 0.6 and abs(ea[1] - at_a[1]) < 0.6) or \
               (abs(eb[0] - at_b[0]) < 0.6 and abs(eb[1] - at_b[1]) < 0.6):
                bad.add((ci, si))
            else:
                at_a, at_b = ea, eb
    return bad


def closes_on_start(contour):
    """True when the last segment already ends on the contour's start point.

    The donor's counter does. Kept as well as the start node it lands on, the
    two sit exactly on top of each other and the mechanical check reports a
    coincident pair; dropping the start node instead leaves the closing curve
    to do the closing, which is what the format is for.
    """
    a, b = contour[0][1][0], contour[-1][1][-1]
    return abs(a[0] - b[0]) < 0.7 and abs(a[1] - b[1]) < 0.7


def to_nodes(contour, drop, ci):
    out = []
    skip0 = closes_on_start(contour)
    for si, (kind, pts) in enumerate(contour):
        if (ci, si) in drop or (si == 0 and skip0):
            continue
        if kind == "curve":
            out += [(pts[0][0], pts[0][1], "offcurve", False),
                    (pts[1][0], pts[1][1], "offcurve", False),
                    (pts[2][0], pts[2][1], "curve", True)]
        else:
            out.append((pts[0][0], pts[0][1], "line", False))
    return out


def remap(paths, sbot, stop, obot, otop, asc, fx0, fx1):
    """Two vertical anchors, then the ascender, then the width."""
    k = (otop - obot) / (stop - sbot)
    pts = [[(x, obot + (y - sbot) * k, ty, sm) for x, y, ty, sm in p]
           for p in paths]
    top = max(y for p in pts for _, y, _, _ in p)
    pts = [[(x, y if y <= otop else otop + (y - otop) * (asc - otop)
             / (top - otop), ty, sm) for x, y, ty, sm in p] for p in pts]
    lo = min(x for p in pts for x, _, _, _ in p)
    hi = max(x for p in pts for x, _, _, _ in p)
    kx = (fx1 - fx0) / (hi - lo)
    return [[(fx0 + (x - lo) * kx, y, ty, sm) for x, y, ty, sm in p]
            for p in pts]


def fit_segs(sg, work, pr):
    """The donor's segments in this face's units -- `remap`, on segments.

    The solve reads the donor's own bowl and so runs on node lists, but the
    splice has to cut curves and needs them whole; the three moves are the
    same ones, in the same order.
    """
    be = contours(work, "б", work.getBestCmap(), work.getGlyphSet())
    o = contours(work, "o", work.getBestCmap(), work.getGlyphSet())
    sbot = min(q[1] for p in be for q in p)
    stop = max(q[1] for p in o for q in p)
    ox0, oy0, ox1, oy1 = bbox(pr.paths("o"))
    k = (oy1 - oy0) / (stop - sbot)
    top = max(oy0 + (q[1] - sbot) * k
              for c in sg for _kind, ps in c for q in ps)
    xs = [q[0] for c in sg for _kind, ps in c for q in ps]
    lo, hi = min(xs), max(xs)
    kx = (ox1 - ox0) / (hi - lo)

    def f(q):
        y = oy0 + (q[1] - sbot) * k
        if y > oy1:
            y = oy1 + (y - oy1) * (pr.asc - oy1) / (top - oy1)
        return (ox0 + (q[0] - lo) * kx, y)

    return [[(kind, [f(q) for q in ps]) for kind, ps in c] for c in sg]


def square_terminal(sg):
    """The terminal is the outline's own closing segment -- pull it upright.

    The donor starts its outer contour at one end of the cut and finishes at
    the other, so the two points to move are the contour's first and last.
    Both go to the outer one, which keeps the letter's reach rather than
    shortening it.
    """
    a, b = sg[0][1][0], seg_end(sg[-1])
    x = max(a[0], b[0])
    sg[0] = ("start", [(x, a[1])])
    kind, pts = sg[-1]
    sg[-1] = (kind, pts[:-1] + [(x, b[1])])
    return sg


def poly(nodes, steps=24):
    ns = nodes[:]
    start = next(i for i, n in enumerate(ns) if n[2] != "offcurve")
    ns = ns[start:] + ns[:start]
    pts, cur, i = [(ns[0][0], ns[0][1])], (ns[0][0], ns[0][1]), 1
    ring = ns[1:] + [ns[0]]
    while i <= len(ring):
        n = ring[i - 1]
        if n[2] == "offcurve":
            c1, c2, e = n, ring[i], ring[i + 1]
            for s in range(1, steps + 1):
                u = s / float(steps)
                m = 1 - u
                pts.append((m ** 3 * cur[0] + 3 * m * m * u * c1[0]
                            + 3 * m * u * u * c2[0] + u ** 3 * e[0],
                            m ** 3 * cur[1] + 3 * m * m * u * c1[1]
                            + 3 * m * u * u * c2[1] + u ** 3 * e[1]))
            cur = (e[0], e[1])
            i += 3
        else:
            cur = (n[0], n[1])
            pts.append(cur)
            i += 1
    return pts


# --- splicing the donor's branch onto this face's own bowl -----------------

# The donor's outer contour is a single loop through both the bowl and the
# branch, and its segment k ends on on-curve node 3k. The bowl's arc is
# segments 6..14: it begins where the branch's underside comes back down onto
# the bowl and ends at the letter's leftmost node, which is where the bowl's
# left wall stops being the bowl and becomes the branch's outer edge. Those
# two segments are the seam.
LAND, LEAVE = 5, 14

# Where the branch's underside comes down onto the oval, in degrees round it.
# None means "wherever the branch itself reaches it" -- see `land_on`. A number
# overrides that, which is what the sweep in `tools/seam.py` needs; it is not
# how the letter is built.
#
# The landing used to be the donor's own angle, with the underside's end point
# TRANSLATED onto the oval and the move faded out over the three points above
# it. Both halves of that are gone. The translation is what forced the
# exemption below, and the exemption is what put the blob at the junction.
LANDING = (None, None)

# What the branch should weigh, over the bowl's own wall. The panel's median
# taken nearest-neighbour by stem, per master -- the reading is not flat, and
# a flat one would be F4. The comparison is against the bowl rather than
# against the stem because that is the one a reader actually makes: the two
# strokes are adjacent and each is seen against the other.
#
# Re-derived once weights.py could be trusted. The earlier pair, 0.92 and
# 0.97, came from a reading that called the bowl's own crown "branch"; the
# bands themselves moved with it, and at ExtraBold 0.97 sits outside a band
# that actually runs 0.74 to 0.91.
BRANCH = (0.88, 0.86)

# Which point on the donor's own axis each master takes its SHAPE from. Its
# ends, and no further: the axis is clamped to the range it was fitted over
# (METHOD §1) and the weight comes from `reweight` instead.
#
# It used to be extrapolated, which is what a donor's axis is for when it is
# supplying the whole letter. It is not any more -- only the branch is the
# donor's -- and the branch cannot be bought this way. This face's Thin wants a
# branch 0.92 of a 29-unit bowl wall; Sudo's own lightest, fitted to this cell,
# draws 2.19 of it, so reaching this face's weight means extrapolating until
# the stroke falls apart. It does: between t -0.8 and t -1.0 the branch's root
# drops from 1.30 to 0.74 and its terminal thins to a hairline, which is the
# outline degenerating rather than getting lighter.
T = (0.0, 1.0)


def seg_end(s):
    return s[1][-1]


def rev(start, segs):
    """A run of segments walked backwards -> (start, segments)."""
    pts = [start] + [seg_end(s) for s in segs]
    out = []
    for i in range(len(segs) - 1, -1, -1):
        kind, p = segs[i]
        out.append(("curve", [p[1], p[0], pts[i]]) if kind == "curve"
                   else ("line", [pts[i]]))
    return pts[-1], out


def to_segs(p):
    """A Glyphs contour in the same (start, segments) shape `segments` gives."""
    ns = list(p.nodes)
    k = next(i for i, n in enumerate(ns) if n.type != "offcurve")
    ns = ns[k:] + ns[:k]
    out, pend = [], []
    for n in ns[1:] + [ns[0]]:
        q = (n.position.x, n.position.y)
        if n.type == "offcurve":
            pend.append(q)
        elif pend:
            out.append(("curve", pend + [q]))
            pend = []
        else:
            out.append(("line", [q]))
    return (ns[0].position.x, ns[0].position.y), out


def bez(p0, p1, p2, p3, t):
    u = 1.0 - t
    return (u**3 * p0[0] + 3*u*u*t * p1[0] + 3*u*t*t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3*u*u*t * p1[1] + 3*u*t*t * p2[1] + t**3 * p3[1])


def split(p0, seg, t):
    """de Casteljau. Returns the controls of the piece before t, ending on it."""
    p1, p2, p3 = seg[1]
    m = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a0, a1, a2 = m(p0, p1), m(p1, p2), m(p2, p3)
    b0, b1 = m(a0, a1), m(a1, a2)
    return [a0, b0, m(b0, b1)]


def clock(pt, c):
    """Where a point sits round the bowl, in degrees, 0 at three o'clock."""
    cx, cy, ax, ay = c
    return math.degrees(math.atan2((pt[1] - cy) / ay,
                                   (pt[0] - cx) / ax)) % 360.0


def bowl(pr, top):
    """This face's own o, squashed to the height the donor gave the bowl.

    A squash is affine, so the counter keeps o's fill exactly -- which is the
    whole point, that figure being the one the panel is unanimous on. What it
    does not keep is the horizontal at the bowl's floor, and `thicken_floor`
    puts that back afterwards by squeezing the counter, which is affine again.
    """
    ps = sorted(pr.paths("o"), key=lambda p: -abs(area(p)))
    _x0, y0, _x1, y1 = bbox(ps)
    k = (top - y0) / (y1 - y0)

    def f(q):
        return (q[0], y0 + (q[1] - y0) * k)

    return [(f(s), [(kind, [f(q) for q in pts]) for kind, pts in sg])
            for s, sg in (to_segs(p) for p in ps)]


# Every landing angle `splice` has solved this run, so `build` can report the
# one that ended up in the outline. It is not chosen any more, so the only way
# to know where the branch meets the bowl is to read it back.
LANDED = []


def land_on(l0, branch, os_, osg):
    """Where the underside, carried on along its own tangent, meets the oval.

    The underside has to end on the bowl and, once it has been thinned to this
    face's weight, it does not. What used to happen is that its end point was
    TRANSLATED there and the move faded out over the three points above it --
    which meant the end point could not be thinned at all, because the
    translation would only drag it back out again. So the last stretch of the
    stroke kept the donor's own weight while the rest of it was cut to a
    third, and the junction carried a blob 2.4 times the bowl's wall at Thin
    against a panel holding 1.06 to 1.39. It was not a fillet and it was not
    the landing angle: it was the donor's root, unthinned, sitting in the
    corner. Both masters showed it in proportion to how much thinning they
    needed -- Thin 2.44, ExtraBold, which needs none, 1.28.

    So nothing is translated. The stroke is thinned through to its end and
    then simply continues in the direction it was already going until it
    reaches the oval, which is what a stroke growing out of a bowl does. Where
    it lands falls out of that rather than being chosen, and it lands lower
    the lighter the master, which is also what the panel draws.

    Cast both ways along the tangent and take the nearer crossing: at Thin the
    thinned end sits outside the oval and the stroke runs on to meet it, at
    ExtraBold it needs no thinning and already sits a little inside, where
    running on would only take it deeper.
    """
    kind, pts = branch[0]
    dx, dy = l0[0] - pts[0][0], l0[1] - pts[0][1]
    h = math.hypot(dx, dy) or 1.0
    d = (dx / h, dy / h)
    oval = walk(os_, osg, 24)
    fwd, back = ray(l0, d, oval), ray(l0, (-d[0], -d[1]), oval)
    if fwd is None and back is None:
        return l0
    if back is not None and (fwd is None or back < fwd):
        return (l0[0] - d[0] * back, l0[1] - d[1] * back)
    return (l0[0] + d[0] * fwd, l0[1] + d[1] * fwd)


def splice(donor, pr, _land=None):
    """The donor's branch, carried onto an arc of this face's own o.

    The branch is kept whole and the bowl is thrown away. The arc runs from
    the bowl's leftmost node the long way round -- down, right, over the top --
    to where the branch's underside comes back down, so the letter reads as a
    complete oval with a stroke growing out of its upper left, which is what
    every face in the panel draws.
    """
    top = max(seg_end(s)[1] for s in donor[LAND + 1:LEAVE + 1])
    (os_, osg), (cs, csg) = bowl(pr, top)
    xs = [q[0] for _k, pts in osg for q in pts]
    ys = [q[1] for _k, pts in osg for q in pts]
    c = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0,
         (max(xs) - min(xs)) / 2.0, (max(ys) - min(ys)) / 2.0)

    b_start = seg_end(donor[LEAVE])
    b_segs = donor[LEAVE + 1:] + [("line", [donor[0][1][0]])] \
        + donor[1:LAND + 1]
    l0, branch = rev(b_start, b_segs)

    # Where the underside reaches the oval, not where the donor's own did.
    # The branch has just been thinned to this face's weight, which at Thin is
    # a third of what the donor drew, so its end no longer sits on the oval at
    # all -- and the letter's whole seam fault was in what used to be done
    # about that. See `land_on`.
    want = clock(land_on(l0, branch, os_, osg), c) if _land is None else _land

    # The segment of the oval the landing falls in. This has to be the SAME
    # segment at both masters, and it is no longer obvious that it is: the
    # landing used to be the donor's own angle at both, and now it is solved
    # per master and comes out 41 degrees apart. `arc` is rotated to start
    # just past j, so a different j would give the two masters the same node
    # COUNT with node five meaning a different place on the bowl -- which
    # every mechanical check would pass and every interpolated weight would
    # be wrong. `build` asserts the two agree.
    at, j = os_, None
    for i, s in enumerate(osg):
        a, b = clock(at, c), clock(seg_end(s), c)
        if a < want < b:
            j = i
            break
        at = seg_end(s)
    LANDED.append((want, j))

    # the oval, split there. Its angle rather than its point, so that a
    # landing solved on one master and one solved on the other are the same
    # relation to the bowl rather than two arbitrary coordinates.
    lo, hi = 0.0, 1.0
    for _ in range(40):
        t = 0.5 * (lo + hi)
        if clock(bez(at, *osg[j][1], t), c) < want:
            lo = t
        else:
            hi = t
    part = split(at, osg[j], 0.5 * (lo + hi))
    arc = osg[j + 1:] + osg[:j] + [("curve", part)]

    # and the underside runs on to meet it. A line, because it is the
    # underside's own tangent carried on, so the angle the stroke enters the
    # bowl at is the donor's exactly -- which is what the translation could
    # not do. The branch itself is not moved at all any more.
    return [[("start", [seg_end(osg[j])])] + arc + [("line", [l0])] + branch,
            [("start", [cs])] + csg]


def shape(a, b, t, work, pr, drop=frozenset()):
    """The finished node lists at one point on the donor's axis."""
    blend(a, b, t, be_glyph(work))
    sg = segments(work)
    paths = [to_nodes(c, drop, ci) for ci, c in enumerate(sg)]
    be = contours(work, "б", work.getBestCmap(), work.getGlyphSet())
    o = contours(work, "o", work.getBestCmap(), work.getGlyphSet())
    sbot = min(q[1] for p in be for q in p)
    stop = max(q[1] for p in o for q in p)
    ox0, oy0, ox1, oy1 = bbox(pr.paths("o"))
    return sg, remap(paths, sbot, stop, oy0, oy1, pr.asc, ox0, ox1)


def floor_and_wall(ps):
    """A bowl's own two weights: the ink under its counter, and its side.

    Both read straight off the outline rather than through signature's bar
    finder, which returns nothing at all for this letter at the heavy master
    -- the branch's horizontal is too short to persist and the bowl's own is
    too tall to count as a bar. A bisection against a measure that can return
    zero runs to the end of its bracket, which is how the counter came to be
    closed up entirely.

    The side is read on the RIGHT. On the left the same scanline crosses
    where the branch grows out of the bowl, which is thicker.
    """
    xs = [q[0] for p in ps for q in p]
    ys = [q[1] for p in ps for q in p]
    v = vruns(ps, (min(xs) + max(xs)) / 2.0)
    r = runs(ps, min(ys) + (max(ys) - min(ys)) * 0.45)
    return ((v[0][1] - v[0][0]) if v else 0.0,
            (r[-1][1] - r[-1][0]) if r else 0.0)


def measure(paths, pr):
    return floor_and_wall([poly(p) for p in paths])


def branch_weight(paths, wall):
    """The branch's own thickness, where it runs clear of the bowl.

    Read above the bowl and below the terminal, and corrected for the run's
    own lean, so a stroke crossing the scanline at an angle reads its real
    thickness and not its horizontal footprint. The median of the samples
    rather than any one of them: the branch tapers, and one scanline picked by
    hand is a landmark squeezed out of a curve. (F10.)
    """
    ps = [poly(p) for p in paths]
    hole = sorted(ps, key=lambda p: -abs(_area(p)))[1]
    top = max(q[1] for q in hole) + wall
    hi = max(q[1] for p in ps for q in p)
    step = (hi - top) * 0.02
    out = []
    for i in range(1, 20):
        y = top + (hi - top) * i / 20.0
        r, r2 = runs(ps, y), runs(ps, y + step)
        if len(r) != 1 or len(r2) != 1:
            continue
        w = r[0][1] - r[0][0]
        dx = 0.5 * ((r2[0][0] + r2[0][1]) - (r[0][0] + r[0][1]))
        out.append(w * step / math.hypot(dx, step))
    return sorted(out)[len(out) // 2] if out else 0.0


def _area(p):
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1)
                     in zip(p, p[1:] + p[:1]))


def walk(start, segs, steps=12):
    """A run of segments as a polyline."""
    pts, at = [start], start
    for kind, p in segs:
        if kind == "curve":
            for s in range(1, steps + 1):
                pts.append(bez(at, p[0], p[1], p[2], s / float(steps)))
            at = p[2]
        else:
            pts.append(p[0])
            at = p[0]
    return pts


def ray(o, d, poly):
    """How far from o, along d, the polyline is. None if it is not ahead."""
    best = None
    for i in range(len(poly) - 1):
        ax, ay = poly[i]
        ex, ey = poly[i + 1][0] - ax, poly[i + 1][1] - ay
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-9:
            continue
        fx, fy = ax - o[0], ay - o[1]
        s = (fx * ey - fy * ex) / den
        u = (fx * d[1] - fy * d[0]) / den
        if s > 1e-6 and -1e-9 <= u <= 1.0 + 1e-9 and (best is None or s < best):
            best = s
    return best


def gauge(sg):
    """The branch's own thickness, and the normals it was measured along.

    Straight off the outline: from each point of the underside, along its own
    inward normal, to the outer edge. That is the stroke's real thickness
    wherever it is taken, and it needs no scanline and no slope correction --
    the correction was the unreliable part, reading a near-horizontal stroke as
    four times its own weight and moving barely at all when the stroke was
    thinned to a sliver.
    """
    outer = walk(seg_end(sg[LEAVE]), sg[LEAVE + 1:])
    pts = [sg[0][1][0]] + [q for _kind, ps in sg[1:LAND + 1] for q in ps]
    out = []
    for i, q in enumerate(pts):
        p0, p1 = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        h = math.hypot(dx, dy) or 1.0
        n = (dy / h, -dx / h)
        out.append((q, n, ray((q[0], q[1]), n, outer)))
    d = sorted(v[2] for v in out if v[2])
    return d[len(d) // 2], out


def reweight(sg, k):
    """Scale the branch's thickness by k, moving only its underside.

    Proportionally, not by a fixed offset. The branch tapers -- twice as thick
    at its middle as at its terminal -- so taking a constant off both leaves
    the terminal a hairline while the middle is still right. Each point moves
    along its own inward normal by a share of its own distance to the outer
    edge, which is a change of weight rather than of shape, and is what the
    face's own з does to the digit three.
    """
    rows = gauge(sg)[1]
    out = []
    for _i, (q, n, d) in enumerate(rows):
        # Every point moves, the landing included. It used to be held back,
        # because the splice then translated it onto the oval and that drag
        # undid the thinning; now the splice does not translate anything, so
        # the exemption has nothing left to protect and the blob it left at
        # the junction is gone. The panel agrees there is nothing to protect:
        # a branch weighs 0.89 of the bowl's wall at its heel against 0.86
        # along its body, which is flat within the noise.
        s = (1.0 - k) * d if d else 0.0
        out.append((q[0] + n[0] * s, q[1] + n[1] * s))
    new = list(sg)
    new[0] = ("start", [out[0]])
    i = 1
    for si in range(1, LAND + 1):
        kind, ps = sg[si]
        new[si] = (kind, out[i:i + len(ps)])
        i += len(ps)
    return new


def solve(a, b, work, pr, mi):
    """How much the branch has to be thinned to weigh what it should.

    The axis is no longer the lever -- it is clamped to the donor's own ends
    and only buys the shape. What is left is one number, in closed form: each
    point of the underside keeps k of its own distance to the outer edge, so
    the stroke ends up k times as thick, everywhere, and k is what the face
    wants over what the donor drew.
    """
    import weights as W
    scale = W.XH / float(pr.cap)
    wall = W.width(W.edt(W.mask_of([_flatten(q, 96) for q in pr.paths("o")],
                                   scale)))
    blend(a, b, T[mi], be_glyph(work))
    sg = fit_segs(segments(work), work, pr)[0]

    def ratio(k):
        cs = splice(square_terminal(reweight(sg, k)), pr, LANDING[mi])
        ps = [poly(to_nodes(c, frozenset(), ci), 40)
              for ci, c in enumerate(cs)]
        rows = W.branch_of(W.mask_of(ps, scale))
        return sorted(v / wall for v in rows)[len(rows) // 2]

    lo_k, hi_k = 0.05, 1.6
    for _ in range(14):
        mid = 0.5 * (lo_k + hi_k)
        if ratio(mid) < BRANCH[mi]:
            lo_k = mid
        else:
            hi_k = mid
    k = 0.5 * (lo_k + hi_k)
    return k, ratio(k), 1.0


def thicken_floor(paths, want):
    """Squeeze the counter vertically until the bowl's floor is this face's.

    The axis sets the walls and this sets the floor, because the donor does
    not hold the two in this face's proportion and no single point on its
    weight axis can be made to. Squeezing the counter moves only the ink above
    and below it, so the walls the axis just solved stay where they are.
    """
    p = paths[1]
    ys = [y for _x, y, _t, _s in p]
    mid = (min(ys) + max(ys)) / 2.0

    def at(k):
        return paths[:1] + [[(x, mid + (y - mid) * k, ty, sm)
                             for x, y, ty, sm in p]] + paths[2:]

    # bisected rather than stepped. A step small enough not to overshoot is a
    # step small enough to be slow, and overshooting by one step put the
    # horizontal at 30 against this face's own 28 -- which the signature
    # reads as a weight error, because it is one.
    lo, hi = 0.7, 1.0
    for _ in range(24):
        k = 0.5 * (lo + hi)
        if floor_and_wall([poly(q) for q in at(k)])[0] < want:
            hi = k
        else:
            lo = k
    return at(0.5 * (lo + hi))


def want_wall(pr):
    return floor_and_wall([_flatten(q, 48) for q in pr.paths("o")])[1]


def build():
    lo, hi = load(LO), load(HI)
    a, b = list(be_glyph(lo).coordinates), list(be_glyph(hi).coordinates)
    font = glyphsLib.load(open("sources/SUSEMono.glyphs"))
    work = load(LO)
    made, landed = [], []
    for mi in range(len(font.masters)):
        pr = Lower(Params(font, mi))
        k, got, wall = solve(a, b, work, pr, mi)
        print("  master %d  donor axis %.2f  thinned to %.2f"
              "   branch measures %.2f of the bowl's wall, wanted %.2f"
              % (mi, T[mi], k, got, BRANCH[mi]))
        blend(a, b, T[mi], be_glyph(work))
        sg = reweight(fit_segs(segments(work), work, pr)[0], k)
        del LANDED[:]
        made.append((k, splice(square_terminal(sg), pr, LANDING[mi]), pr))
        landed.append(LANDED[-1])
        print("            lands at %.0f degrees round the bowl, in the "
              "bowl's segment %d" % LANDED[-1])
    if len({j for _a, j in landed}) != 1:
        raise SystemExit("the masters landed in different segments of the "
                         "bowl, %s -- their nodes no longer mean the same "
                         "thing and the interpolation is nonsense" % landed)
    drop = degenerate(made[0][1], made[1][1])
    out = []
    for t, cs, pr in made:
        want = floor_and_wall([_flatten(q, 48) for q in pr.paths("o")])[0]
        out.append((t, thicken_floor(
            [to_nodes(c, drop, ci) for ci, c in enumerate(cs)], want)))
    return out


def main():
    head = ['"""б\'s outline, taken from Sudo and fitted to this face.\n',
            '\n',
            'Generated by scripts/be_from_sudo.py -- edit that, not this.\n',
            'Sudo is under the SIL Open Font License 1.1, which is what lets\n',
            'it be an outline donor here. Held as data rather than read from\n',
            'the donor at build time so the repository builds without a font\n',
            'that lives outside it.\n',
            '\n',
            'The bowl is this face\'s own o, squashed to the height the donor\n',
            'gave it; only the branch is the donor\'s.\n',
            '\n',
            'One entry per master, in source order: contours of\n',
            '(x, y, type, smooth). Both masters carry the same nodes in the\n',
            'same order.\n',
            '"""\n\nBE = [\n']
    body = []
    made = build()
    for t, paths in made:
        body.append("    # the donor's own weight axis at %.3f\n    [\n" % t)
        for p in paths:
            body.append("        [\n")
            for x, y, ty, sm in p:
                body.append("            (%.1f, %.1f, %r, %r),\n"
                            % (x, y, ty, sm))
            body.append("        ],\n")
        body.append("    ],\n")
    open(OUT, "w").write("".join(head) + "".join(body) + "]\n")
    print("%s  %s" % (OUT, [[len(p) for p in ps] for _, ps in made]))


if __name__ == "__main__":
    main()
