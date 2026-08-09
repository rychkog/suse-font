"""Take Sudo's б, extrapolate it to this face's weights and fit it to its box.

Sudo (https://github.com/jenskutilek/sudo-font, Jens Kutilek) is under the SIL
Open Font License 1.1, which is what lets it be an outline donor; SUSE Mono is
under the same licence. "Sudo" is the donor's trademark and is not a name this
font may use.

Writes `tools/be_donor.py`. Run it from the repository root:

    ./venv/bin/python scripts/be_from_sudo.py

What it does, in order:

  * solves the donor's own weight axis so its o's wall matches this face's, by
    extrapolating point for point past both ends of that axis -- Sudo runs
    from a wall a tenth of the x-height to just under a quarter, and this face
    needs a sixteenth at Thin and three tenths at ExtraBold;
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
    to the height the donor gave the bowl, and the branch is spliced onto it.
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

# How far up the branch the landing's move is felt. The underside has to end
# on the oval and the donor ends it somewhere else, so the last stretch of it
# moves -- and moving only the end point drags that stretch straight. What it
# costs is the FLARE: the donor widens the branch as it enters the bowl, which
# is what makes the stroke look grown out of the bowl rather than laid across
# it, and dragging the end point turned a segment leaning 78 degrees into one
# standing at 88 and parallel to the branch's own outer edge. So the whole
# root moves rigidly and the move fades out over the segments above it.
ROOT = 12


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


def splice(donor, pr):
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

    # the segment of the oval the landing falls in -- the upper left quadrant
    # at both masters, so the two layers split the same segment and keep the
    # same nodes
    at, j = os_, None
    for i, s in enumerate(osg):
        a, b = clock(at, c), clock(seg_end(s), c)
        if a < clock(l0, c) < b:
            j = i
            break
        at = seg_end(s)

    # the oval, split where the donor's own underside comes down. Its angle
    # rather than its point: the donor lands 16 per cent outside the oval at
    # Thin and 3 per cent inside it at ExtraBold, and an angle is the same
    # relation at both.
    want = clock(l0, c)
    lo, hi = 0.0, 1.0
    for _ in range(40):
        t = 0.5 * (lo + hi)
        if clock(bez(at, *osg[j][1], t), c) < want:
            lo = t
        else:
            hi = t
    part = split(at, osg[j], 0.5 * (lo + hi))
    arc = osg[j + 1:] + osg[:j] + [("curve", part)]

    # The root moves onto the oval whole, and the move fades out above it, so
    # the branch keeps the shape it enters the bowl with.
    dx, dy = part[2][0] - l0[0], part[2][1] - l0[1]
    out, i = [], 0
    for kind, pts in branch:
        moved = []
        for q in pts:
            w = 1.0 if i < 3 else max(0.0, 1.0 - (i - 3) / float(ROOT))
            moved.append((q[0] + dx * w, q[1] + dy * w))
            i += 1
        out.append((kind, moved))

    return [[("start", [seg_end(osg[j])])] + arc + out,
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


def solve(a, b, work, pr):
    """Weight from the horizontal, width from the wall -- in that order.

    They separate cleanly and that is the whole trick. A horizontal does not
    care how wide the letter is stretched, so the donor's axis can be solved
    against it alone; a vertical wall scales exactly with the stretch, so the
    width follows in closed form once the weight is fixed.

    Solved the other way round -- weight against the wall, width against the
    cell -- neither lands: the fit stretches this letter a fifth wider than
    the donor drew it, a fifth thickens every vertical by the same amount,
    and the horizontal is left an eighth heavy at Thin and a third heavy at
    ExtraBold.
    """
    wf, ww = floor_and_wall([_flatten(q, 48) for q in pr.paths("o")])
    lo_t, hi_t = -1.2, 2.6
    for _ in range(22):
        mid = 0.5 * (lo_t + hi_t)
        _, paths = shape(a, b, mid, work, pr)
        f, w = measure(paths, pr)
        # Weighted to the WALL, not evenly between wall and floor. The floor
        # has room to go heavy and the wall does not have room to go light:
        # the face's own letters hold their horizontal between 0.94 and 1.05
        # of its own at Thin but between 1.00 and 1.13 at ExtraBold, so a
        # horizontal that runs heavy is inside the face's habit at the end of
        # the axis where this letter was reading thin next to в and о.
        if w < ww:
            lo_t = mid
        else:
            hi_t = mid
    t = 0.5 * (lo_t + hi_t)
    _, paths = shape(a, b, t, work, pr)
    return (t, 1.0) + measure(paths, pr)


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
    made = []
    for mi in range(len(font.masters)):
        pr = Lower(Params(font, mi))
        t, _k, floor, wall = solve(a, b, work, pr)
        print("  master %d  axis %.3f  donor floor %.1f  wall %.1f"
              % (mi, t, floor, wall))
        blend(a, b, t, be_glyph(work))
        sg = fit_segs(segments(work), work, pr)
        made.append((t, splice(square_terminal(sg[0]), pr), pr))
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
