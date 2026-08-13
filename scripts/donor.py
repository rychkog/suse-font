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
