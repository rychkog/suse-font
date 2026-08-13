"""Shared machinery for taking an outline from another face and fitting it.

Not a design decision anywhere in here -- the two letters that use it, г and д,
each make their own, and this is only the plumbing they both need: read a CFF
glyph as segments, check two weights are the same drawing, blend between them,
stand the donor up, lean a measurement over, and write the result out.

**CFF and not TrueType**, and that is the one thing in this file worth
reading. Sudo supplied г first and Sudo is a variable TrueType, so its curves
arrive as quadratics; expanding those segment by segment -- which is the only
expansion that keeps the node structure identical across the axis -- gave г
**34 on-curve nodes where this face's own o has 8**. It measured correctly on
every reading this project takes, because every one of them reads the ink. As
an outline it was machine spaghetti: a node every few units, handles too short
to control anything, and no relation to where the curve's extremes are. A CFF
donor's outline is the designer's own cubics -- Lilex draws the same letter in
16 -- and its statics interpolate node for node when the family was built from
one source, which `same_drawing` checks rather than assumes.
"""
import math
import os
import sys

sys.path.insert(0, "tools")

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont


def find(name):
    from panel import families
    for r in sorted({os.path.dirname(p) for _f, p in families()}):
        p = os.path.join(r, name)
        if os.path.exists(p):
            return p
    raise SystemExit("%s is not installed -- it is the outline donor" % name)


def segments_of(path, cp):
    """A CFF glyph's contours as (kind, points) segments, and its slope.

    No quadratic expansion and no curve fitting: CFF is already cubic, so what
    the pen reports is what the designer drew, node for node.
    """
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        pen = RecordingPen()
        f.getGlyphSet()[f.getBestCmap()[cp]].draw(pen)
        deg = float(f["post"].italicAngle)
    finally:
        f.close()
    out, cur = [], None
    for verb, pts in pen.value:
        if verb == "moveTo":
            cur = [("start", [pts[0]])]
        elif verb == "lineTo":
            cur.append(("line", [pts[0]]))
        elif verb == "curveTo":
            cur.append(("curve", list(pts)))
        elif verb in ("closePath", "endPath"):
            out.append(cur)
            cur = None
    return out, deg


def same_drawing(files, cp, what):
    """The donor's two weights, checked to be the same drawing before use."""
    a, deg = segments_of(find(files[0]), cp)
    b, _ = segments_of(find(files[1]), cp)
    sa = [[k for k, _p in c] for c in a]
    sb = [[k for k, _p in c] for c in b]
    if sa != sb:
        raise SystemExit("the donor's two italics no longer carry the same "
                         "segments for %s -- %s against %s" % (what, sa, sb))
    return a, b, deg


def blend(a, b, t):
    return [[(k, [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
                  for p, q in zip(ps, qs)])
             for (k, ps), (_k, qs) in zip(ca, cb)]
            for ca, cb in zip(a, b)]


def mapped(sg, f):
    return [(kind, [f(q) for q in pts]) for kind, pts in sg]


def pts_of(sg):
    return [q for _kind, ps in sg for q in ps]


def stand_up(sg, deg):
    """The donor's own slope taken out. `deg` is its `italicAngle`, which is
    negative for a face leaning right, so the shear is applied as it stands."""
    t = math.tan(math.radians(deg))
    return mapped(sg, lambda q: (q[0] + q[1] * t, q[1]))


def leaning(pts, deg, pivot):
    """How wide a set of points is once the italic goes back on.

    Everything here is built standing up and leaned over on write, and a shear
    does not widen every letter alike -- an oval gains four per cent, a letter
    reaching furthest at two different heights on opposite sides gains fifteen.
    Fit where the reading is taken. METHOD F16.
    """
    t = math.tan(math.radians(deg))
    xs = [q[0] + (q[1] - pivot) * t for q in pts]
    return max(xs) - min(xs)


def fit_width(sg, pr, want, mid):
    """Scale x about `mid` until the contour is `want` wide LEANING.

    Bisected rather than solved: under a shear the extremes change hands as the
    scale changes, and a closed form would have to know which points win.
    """
    def at(kx):
        return leaning([(300.0 + (q[0] - mid) * kx, q[1]) for q in pts_of(sg)],
                       pr.italic, pr.pivot)

    lo, hi = 0.05, 4.0
    for _ in range(30):
        kx = 0.5 * (lo + hi)
        if at(kx) < want:
            lo = kx
        else:
            hi = kx
    return 0.5 * (lo + hi)


def centre(cs, pr, on=0, to=300.0):
    """Slide the whole letter so contour `on` is centred where it is READ."""
    t = math.tan(math.radians(pr.italic))
    xs = [q[0] + (q[1] - pr.pivot) * t for q in pts_of(cs[on])]
    dx = to - 0.5 * (min(xs) + max(xs))
    return [mapped(c, lambda q: (q[0] + dx, q[1])) for c in cs]


def square(sg, i, angle, reach=min):
    """One terminal cut vertical in the italic's own space.

    This face cuts 213 of its 242 terminals at exactly 0 or 90 degrees, and
    everything here stands up, so a cut that should be vertical in the font has
    to lean by the italic's own angle here. Both ends of the cut go to whichever
    reaches further -- `min` for a terminal that reaches left, `max` for one
    that reaches right -- which keeps the letter's extent rather than
    shortening it.
    """
    t = math.tan(math.radians(angle))
    a, b = sg[i - 1][1][-1], sg[i][1][-1]
    e = reach(a[0] - a[1] * t, b[0] - b[1] * t)
    out = list(sg)
    out[i] = (out[i][0], [(e + b[1] * t, b[1])])
    kind, ps = out[i - 1]
    out[i - 1] = (kind, ps[:-1] + [(e + a[1] * t, a[1])])
    return out


def bez(p0, c1, c2, p3, t):
    u = 1.0 - t
    return (u**3 * p0[0] + 3*u*u*t * c1[0] + 3*u*t*t * c2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3*u*u*t * c1[1] + 3*u*t*t * c2[1] + t**3 * p3[1])


def smooth_at(prev, node, nxt, tol=3.0):
    """Is this join smooth? Read off the handles rather than declared.

    Every curve node used to be written out smooth, terminals included, which
    is a lie about the drawing: a corner marked smooth is a corner an editor
    will straighten and a rounding pass will treat as continuous.
    """
    v1 = (node[0] - prev[0], node[1] - prev[1])
    v2 = (nxt[0] - node[0], nxt[1] - node[1])
    if math.hypot(*v1) < 1e-6 or math.hypot(*v2) < 1e-6:
        return False
    d = math.degrees(abs(math.atan2(v1[0] * v2[1] - v1[1] * v2[0],
                                    v1[0] * v2[0] + v1[1] * v2[1])))
    return d <= tol


def to_nodes(sg):
    """(x, y, type, smooth) per node, the smooth flag read off the handles."""
    out = []
    n = len(sg)
    for i in range(1, n):
        kind, pts = sg[i]
        if kind == "curve":
            nxt = sg[i + 1] if i + 1 < n else sg[1]
            after = nxt[1][0] if nxt[0] == "curve" else nxt[1][-1]
            out += [(pts[0][0], pts[0][1], "offcurve", False),
                    (pts[1][0], pts[1][1], "offcurve", False),
                    (pts[2][0], pts[2][1], "curve",
                     smooth_at(pts[1], pts[2], after))]
        else:
            out.append((pts[0][0], pts[0][1], "line", False))
    return out


def poly(nodes, steps=24):
    """Nodes flattened to a polygon, for measuring."""
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
                pts.append(bez(cur, c1, c2, e, s / float(steps)))
            cur = (e[0], e[1])
            i += 3
        else:
            cur = (n[0], n[1])
            pts.append(cur)
            i += 1
    return pts


def mask(groups, k):
    """Contours XORed inside a group, groups ORed together.

    `weights.mask_of` XORs everything, which is right for a letter drawn as one
    outline with counters punched out of it and wrong for one where a stroke
    OVERLAPS a bowl: XORing those takes the overlap back out again, a bite out
    of the junction, in exactly the region a junction reading is about. The
    built font unions them, because TrueType fills by non-zero winding.
    """
    import numpy as np
    from PIL import Image, ImageDraw, ImageChops
    xs = [q[0] for g in groups for p in g for q in p]
    ys = [q[1] for g in groups for p in g for q in p]
    w = int((max(xs) - min(xs)) * k) + 8
    h = int((max(ys) - min(ys)) * k) + 8
    total = Image.new("1", (w, h), 0)
    for g in groups:
        img = Image.new("1", (w, h), 0)
        for pl in g:
            lay = Image.new("1", (w, h), 0)
            ImageDraw.Draw(lay).polygon(
                [(4 + (x - min(xs)) * k, h - 4 - (y - min(ys)) * k)
                 for x, y in pl], fill=1)
            img = ImageChops.logical_xor(img, lay)
        total = ImageChops.logical_or(total, img)
    import numpy as np                                          # noqa: F811
    return np.asarray(total) > 0


def emit(out, name, head, made):
    body = []
    for t, paths in made:
        body.append("    # the donor's own Thin to Bold at %+.3f\n    [\n" % t)
        for p in paths:
            body.append("        [\n")
            for x, y, ty, sm in p:
                body.append("            (%.1f, %.1f, %r, %r),\n"
                            % (x, y, ty, sm))
            body.append("        ],\n")
        body.append("    ],\n")
    open(out, "w").write('"""' + head + '"""\n\n%s = [\n' % name
                         + "".join(body) + "]\n")
    print("%s  %s" % (out, [[len(p) for p in ps] for _, ps in made]))


# --- splicing a donated stroke into the host's own bowl ---------------------
#
# Copied in spirit from `scripts/be_from_sudo.py`, which solved this for б and
# is approved: a stroke laid OVER a bowl and a stroke growing OUT of one are
# not the same letter, and the difference is the swell at the junction, which
# every reference draws and no overlap can invent. What is different here is
# where the cuts come from. б chooses its landing by carrying the branch's own
# tangent on until it reaches the oval; this finds both cuts by asking where
# the donor's outline actually CROSSES the host's, which needs no angle and no
# choice, and gives the departure the same way as the landing.


def to_segs(p):
    """A Glyphs contour as (start, segments), the shape everything here uses."""
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


def at(start, segs, i, t):
    """The point at parameter t along segment i."""
    p0 = start if i == 0 else segs[i - 1][1][-1]
    kind, ps = segs[i]
    if kind == "curve":
        return bez(p0, ps[0], ps[1], ps[2], t)
    return (p0[0] + (ps[0][0] - p0[0]) * t, p0[1] + (ps[0][1] - p0[1]) * t)


def walk(start, segs, steps=16):
    """A run of segments as a polyline, its start included."""
    pts = [start]
    for i in range(len(segs)):
        for s in range(1, steps + 1):
            pts.append(at(start, segs, i, s / float(steps)))
    return pts


def inside(q, poly):
    """Ray casting. `poly` is closed implicitly."""
    x, y = q
    n = len(poly)
    hit = False
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        if (ay > y) != (by > y) and \
                x < ax + (y - ay) * (bx - ax) / ((by - ay) or 1e-12):
            hit = not hit
    return hit


def crossing(start, segs, poly, want_out, first=True, after=None):
    """Where this run of segments crosses `poly`, as (segment, t).

    Bisected on the segment's own parameter after a coarse sweep, so the cut
    lands on the curve rather than on a sample of it. `want_out` picks the
    direction -- leaving the bowl for the departure, entering it for the
    landing -- and `after` restricts the search to what comes later, which is
    what the landing needs: a donated д crosses the host's oval six times,
    because the donor's own bowl crown sits lower than the host's o, and the
    landing is the first re-entry AFTER the stroke has left, not the last one
    anywhere.
    """
    found = []
    for i in range(len(segs)):
        was = inside(at(start, segs, i, 0.0), poly)
        for s in range(1, 33):
            t = s / 32.0
            now = inside(at(start, segs, i, t), poly)
            if now != was and was == want_out:
                lo, hi = (s - 1) / 32.0, t
                for _ in range(24):
                    m = 0.5 * (lo + hi)
                    if inside(at(start, segs, i, m), poly) == was:
                        lo = m
                    else:
                        hi = m
                found.append((i, 0.5 * (lo + hi)))
            was = now
    if after is not None:
        found = [f for f in found if f > after]
    if not found:
        return None
    return found[0] if first else found[-1]


def cut(p0, seg, t):
    """de Casteljau. Returns (the piece before t, the piece after t)."""
    kind, ps = seg
    if kind != "curve":
        m = (p0[0] + (ps[0][0] - p0[0]) * t, p0[1] + (ps[0][1] - p0[1]) * t)
        return ("line", [m]), ("line", [ps[0]]), m
    p1, p2, p3 = ps

    def mix(u, v):
        return (u[0] + (v[0] - u[0]) * t, u[1] + (v[1] - u[1]) * t)

    a0, a1, a2 = mix(p0, p1), mix(p1, p2), mix(p2, p3)
    b0, b1 = mix(a0, a1), mix(a1, a2)
    c0 = mix(b0, b1)
    return ("curve", [a0, b0, c0]), ("curve", [b1, a2, p3]), c0


def reverse_run(start, segs):
    """A run of segments walked backwards -> (its new start, segments)."""
    pts = [start] + [s[1][-1] for s in segs]
    out = []
    for i in range(len(segs) - 1, -1, -1):
        kind, p = segs[i]
        out.append(("curve", [p[1], p[0], pts[i]]) if kind == "curve"
                   else ("line", [pts[i]]))
    return pts[-1], out


def arc(bs, bsegs, frm, to):
    """The run of a closed contour from parameter `frm` forward to `to`.

    Forward means the contour's own direction, wrapping past its start if it
    has to, so `arc(a, b)` and `arc(b, a)` are the two ways round between the
    same pair of cuts and the caller picks which one it wants.
    """
    i0, t0 = frm
    i1, t1 = to
    p = bs if i0 == 0 else bsegs[i0 - 1][1][-1]
    _before, aft, s0 = cut(p, bsegs[i0], t0)
    if i0 == i1 and t1 > t0:
        head, _a, _b = cut(s0, aft, (t1 - t0) / (1.0 - t0))
        return s0, [head]
    out = [aft]
    i = (i0 + 1) % len(bsegs)
    while i != i1:
        out.append(bsegs[i])
        i = (i + 1) % len(bsegs)
    p = bs if i1 == 0 else bsegs[i1 - 1][1][-1]
    head, _a, _b = cut(p, bsegs[i1], t1)
    return s0, out + [head]


def bow(p0, seg, steps=16):
    """How far a segment departs from its own chord, in units.

    Zero means a straight line drawn as a curve, which is a node doing nothing
    and a place the outline cannot be edited sensibly.
    """
    kind, ps = seg
    if kind != "curve":
        return 0.0
    p1 = ps[-1]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy) or 1.0
    worst = 0.0
    for s in range(1, steps):
        q = bez(p0, ps[0], ps[1], p1, s / float(steps))
        worst = max(worst, abs((q[0] - p0[0]) * dy - (q[1] - p0[1]) * dx) / n)
    return worst


def absorb(arc, stroke, D, flat=1.0):
    """Take a straight stub off the front of the stroke into the arc.

    A cut lands wherever the two outlines cross, and when that is near the end
    of one of the donor's own segments what is left over is a stub: at Thin the
    departure fell at 0.94 of its segment and left 36 units with a bow of
    0.02 -- a dead straight piece of curve carrying its own node, and beside
    the arc's own cut end that made three nodes strung along one straight run.
    It is visible at any zoom and no ink reading can see it.

    Absorbed rather than dropped: the arc's last segment is carried on to the
    stub's far end, its final handle moved by the same amount so the tangent
    there is unchanged. The stub is straight and very nearly along the oval's
    own tangent -- it has just left it -- so this is a continuation and not a
    redrawing, and where it does bend the oval outward is the junction, which
    is where the letter is supposed to bend outward.
    """
    if len(stroke) < 2 or bow(D, stroke[0]) > flat:
        return arc, stroke, D
    E = stroke[0][1][-1]
    dx, dy = E[0] - D[0], E[1] - D[1]
    kind, ps = arc[-1]
    if kind == "curve":
        arc = arc[:-1] + [(kind, [ps[0], (ps[1][0] + dx, ps[1][1] + dy), E])]
    else:
        arc = arc[:-1] + [(kind, [E])]
    return arc, stroke[1:], E


def splice(bowl, hook, steps=16):
    """One contour: the host's bowl with the donor's stroke growing out of it.

    `bowl` and `hook` are both (start, segments). The stroke's outer edge
    leaves the bowl somewhere and its underside comes back to it somewhere;
    both are found as CROSSINGS of the two outlines, which needs no landing
    angle and no choice, and gives the departure the same way as the landing.
    The piece of the bowl between them -- the piece the stroke covers -- is the
    only part of the host's oval thrown away; everything else is the host's.

    Returns (start, segments), or None when the two do not cross twice, which
    means the stroke is not attached and the caller should say so rather than
    emit a letter in two pieces.
    """
    bs, bsegs = bowl
    hs, hsegs = hook
    ring = walk(bs, bsegs, steps)

    out = crossing(hs, hsegs, ring, True, True)            # where it leaves
    back = crossing(hs, hsegs, ring, False, True, out)     # and comes back
    if out is None or back is None or out >= back:
        return None

    (i, ti), (j, tj) = out, back
    p0 = hs if i == 0 else hsegs[i - 1][1][-1]
    _b, after, D = cut(p0, hsegs[i], ti)
    q0 = hs if j == 0 else hsegs[j - 1][1][-1]
    before, _a, L = cut(q0, hsegs[j], tj)
    stroke = [after] + hsegs[i + 1:j] + [before]
    skin = walk(D, stroke, steps)

    # of the two ways round the bowl between the same two cuts, keep the one
    # that is NOT under the stroke -- decided by looking, not by assuming the
    # cuts came in a particular order
    cd, cl = _nearest(bs, bsegs, D), _nearest(bs, bsegs, L)
    best = None
    for frm, to, tail in ((cl, cd, stroke), (cd, cl, None)):
        s0, segs = arc(bs, bsegs, frm, to)
        pts = walk(s0, segs, 6)
        if inside(pts[len(pts) // 2], skin):
            continue
        if tail is None:
            _s, rev = reverse_run(D, stroke)
            segs, rev, _e = absorb(segs, rev, L)
            best = (s0, segs + rev)
        else:
            segs, tail, _e = absorb(segs, tail, D)
            best = (s0, segs + tail)
        break
    return best


def _nearest(start, segs, q, steps=64):
    """(segment, t) of the point on this contour closest to q."""
    best = None
    for i in range(len(segs)):
        for s in range(steps + 1):
            t = s / float(steps)
            p = at(start, segs, i, t)
            d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
            if best is None or d < best[0]:
                best = (d, i, t)
    _d, i, t = best
    lo, hi = max(0.0, t - 1.0 / steps), min(1.0, t + 1.0 / steps)
    for _ in range(24):
        m1, m2 = lo + (hi - lo) / 3.0, hi - (hi - lo) / 3.0
        p1, p2 = at(start, segs, i, m1), at(start, segs, i, m2)
        if (p1[0] - q[0]) ** 2 + (p1[1] - q[1]) ** 2 < \
                (p2[0] - q[0]) ** 2 + (p2[1] - q[1]) ** 2:
            hi = m2
        else:
            lo = m1
    return i, 0.5 * (lo + hi)
