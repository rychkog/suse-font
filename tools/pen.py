"""A centreline swept by an oval pen, written as outlines.

The cursive в is one pen movement (`tools/ve/README.md`). The probes drew it by
sweeping a pen over a raster, which a font cannot use: it needs contours, with
the same nodes in every master. So each stretch of the path is given as a
function, its two edges are where the pen reaches either side of it, and each
edge is fitted with ONE cubic per stretch. The stretches come from the
construction, never from the shape, which is what keeps the masters
compatible.

Stretches that overlap are left overlapping; the union comes out on the way to
the font, as it does for El, Pe and д. Where one part leaves another, both
carry a node at that point with the same direction, so the union meets there
without a kink.
"""
import math

from geom import node, path, area, reverse, CURVE, LINE, OFFCURVE


def _unit(x, y):
    m = math.hypot(x, y) or 1.0
    return x / m, y / m


def reach(nx, ny, pen):
    """Where an oval pen, `pen` = (wide, tall), reaches along the normal (nx, ny).

    The heavy o is drawn with such a pen: its sides are thicker than its top
    and bottom. Along any direction of travel both edges stay parallel to the
    path, so an edge's extremes sit where the path's do.
    """
    a2, b2 = (pen[0] / 2.0) ** 2, (pen[1] / 2.0) ** 2
    d = math.sqrt(a2 * nx * nx + b2 * ny * ny) or 1.0
    return a2 * nx / d, b2 * ny / d


class Stretch:
    """One piece of the pen's path: position and velocity for u in [0, 1]."""

    def __init__(self, at, vel):
        self.at, self.vel = at, vel

    def edge(self, side, pen):
        def e(u):
            x, y = self.at(u)
            dx, dy = _unit(*self.vel(u))
            rx, ry = reach(-dy * side, dx * side, pen)
            return x + rx, y + ry
        return e


def part(s, u0, u1):
    """The stretch from u0 to u1 of `s`, as a stretch of its own."""
    d = u1 - u0
    return Stretch(lambda u: s.at(u0 + d * u),
                   lambda u: tuple(v * d for v in s.vel(u0 + d * u)))


def x_turns(s, n=400):
    """Where a stretch travels straight up or down -- its x extremes."""
    out = []
    us = [i / float(n) for i in range(n + 1)]
    vs = [s.vel(u)[0] for u in us]
    for a, b, va, vb in zip(us[1:], us[2:], vs[1:], vs[2:]):
        if va * vb < 0:
            lo, hi = a, b
            for _ in range(40):
                mid = (lo + hi) / 2.0
                if s.vel(lo)[0] * s.vel(mid)[0] <= 0:
                    hi = mid
                else:
                    lo = mid
            out.append((lo + hi) / 2.0)
    return out


def line(a, b):
    return Stretch(lambda u: (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u),
                   lambda u: (b[0] - a[0], b[1] - a[1]))


def bezier(p0, p1, p2, p3):
    def at(u):
        r = 1.0 - u
        return (r ** 3 * p0[0] + 3 * r * r * u * p1[0] + 3 * r * u * u * p2[0] + u ** 3 * p3[0],
                r ** 3 * p0[1] + 3 * r * r * u * p1[1] + 3 * r * u * u * p2[1] + u ** 3 * p3[1])

    def vel(u):
        r = 1.0 - u
        return (3 * r * r * (p1[0] - p0[0]) + 6 * r * u * (p2[0] - p1[0]) + 3 * u * u * (p3[0] - p2[0]),
                3 * r * r * (p1[1] - p0[1]) + 6 * r * u * (p2[1] - p1[1]) + 3 * u * u * (p3[1] - p2[1]))
    return Stretch(at, vel)


def arc(c, rad, e1, e2, f0, f1):
    """A circle of radius `rad` about `c`, drawn in the frame (e1, e2), from
    angle f0 to f1 -- the loop's top is a circle in its own leaning frame."""
    def at(u):
        f = f0 + (f1 - f0) * u
        return (c[0] + rad * (math.cos(f) * e1[0] + math.sin(f) * e2[0]),
                c[1] + rad * (math.cos(f) * e1[1] + math.sin(f) * e2[1]))

    def vel(u):
        f = f0 + (f1 - f0) * u
        s = rad * (f1 - f0)
        return (s * (-math.sin(f) * e1[0] + math.cos(f) * e2[0]),
                s * (-math.sin(f) * e1[1] + math.cos(f) * e2[1]))
    return Stretch(at, vel)


def along(curve, t0, t1):
    """A span of a closed curve given as (at, vel) of its own parameter."""
    at, vel = curve
    d = t1 - t0
    return Stretch(lambda u: at(t0 + d * u),
                   lambda u: tuple(v * d for v in vel(t0 + d * u)))


def _bez(p0, c1, c2, p3, u):
    r = 1.0 - u
    return (r ** 3 * p0[0] + 3 * r * r * u * c1[0] + 3 * r * u * u * c2[0] + u ** 3 * p3[0],
            r ** 3 * p0[1] + 3 * r * r * u * c1[1] + 3 * r * u * u * c2[1] + u ** 3 * p3[1])


def _dbez(p0, c1, c2, p3, u):
    r = 1.0 - u
    return (3 * r * r * (c1[0] - p0[0]) + 6 * r * u * (c2[0] - c1[0]) + 3 * u * u * (p3[0] - c2[0]),
            3 * r * r * (c1[1] - p0[1]) + 6 * r * u * (c2[1] - c1[1]) + 3 * u * u * (p3[1] - c2[1]))


def fit(e, n=40):
    """One cubic through e(0) and e(1), leaving and arriving along e's own
    direction, with handle lengths by least squares. Returns the two handles
    and the largest distance from any sample to the cubic."""
    pts = [e(i / float(n)) for i in range(n + 1)]
    p0, p3 = pts[0], pts[-1]
    h = 1e-4
    q0, q1 = e(h), e(1.0 - h)
    t0 = _unit(q0[0] - p0[0], q0[1] - p0[1])
    t1 = _unit(p3[0] - q1[0], p3[1] - q1[1])
    d = [0.0]
    for a, b in zip(pts, pts[1:]):
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    us = [x / (d[-1] or 1.0) for x in d]
    chord = d[-1] or 1.0
    al = be = chord / 3.0
    for _ in range(6):
        c11 = c12 = c22 = x1 = x2 = 0.0
        for u, p in zip(us, pts):
            r = 1.0 - u
            b0, b1, b2, b3 = r ** 3, 3 * r * r * u, 3 * r * u * u, u ** 3
            a1 = (b1 * t0[0], b1 * t0[1])
            a2 = (-b2 * t1[0], -b2 * t1[1])
            rx = p[0] - (p0[0] * (b0 + b1) + p3[0] * (b2 + b3))
            ry = p[1] - (p0[1] * (b0 + b1) + p3[1] * (b2 + b3))
            c11 += a1[0] * a1[0] + a1[1] * a1[1]
            c12 += a1[0] * a2[0] + a1[1] * a2[1]
            c22 += a2[0] * a2[0] + a2[1] * a2[1]
            x1 += a1[0] * rx + a1[1] * ry
            x2 += a2[0] * rx + a2[1] * ry
        det = c11 * c22 - c12 * c12
        if abs(det) > 1e-9:
            al, be = (x1 * c22 - x2 * c12) / det, (c11 * x2 - c12 * x1) / det
        if al <= 0 or be <= 0:
            al = be = chord / 3.0
        c1 = (p0[0] + t0[0] * al, p0[1] + t0[1] * al)
        c2 = (p3[0] - t1[0] * be, p3[1] - t1[1] * be)
        # move each sample's parameter to its nearest point on the cubic
        nu = []
        for u, p in zip(us, pts):
            for _ in range(3):
                b = _bez(p0, c1, c2, p3, u)
                db = _dbez(p0, c1, c2, p3, u)
                den = db[0] * db[0] + db[1] * db[1]
                if den < 1e-12:
                    break
                u = min(1.0, max(0.0, u - ((b[0] - p[0]) * db[0] + (b[1] - p[1]) * db[1]) / den))
            nu.append(u)
        us = nu
    err = max(math.hypot(*(a - b for a, b in zip(_bez(p0, c1, c2, p3, u), p)))
              for u, p in zip(us, pts))
    return c1, c2, err


def _reversed(e):
    return lambda u: e(1.0 - u)


def _closed(runs):
    """Nodes for a closed contour from runs of edge functions.

    Each run is ("curve", e) or ("line", e); a run starts where the one before
    it ended, and the last ends where the first began. A node is smooth when
    the curve passes through it without turning.
    """
    segs, worst = [], 0.0
    for kind, e in runs:
        if kind == "line":
            segs.append(("line", e(0.0), None, None, e(1.0)))
        else:
            c1, c2, err = fit(e)
            worst = max(worst, err)
            segs.append(("curve", e(0.0), c1, c2, e(1.0)))
    nodes = []
    for j, (kind, p0, c1, c2, p3) in enumerate(segs):
        nxt = segs[(j + 1) % len(segs)]
        tin = _unit(p3[0] - (c2 or p0)[0], p3[1] - (c2 or p0)[1])
        out_to = nxt[2] or nxt[4]
        tout = _unit(out_to[0] - p3[0], out_to[1] - p3[1])
        smooth = tin[0] * tout[0] + tin[1] * tout[1] > math.cos(math.radians(1.0))
        if kind == "curve":
            nodes.append(node(c1[0], c1[1], OFFCURVE))
            nodes.append(node(c2[0], c2[1], OFFCURVE))
            nodes.append(node(p3[0], p3[1], CURVE, smooth))
        else:
            nodes.append(node(p3[0], p3[1], LINE, smooth))
    return path(nodes), worst


def _kind(s):
    return "line" if getattr(s, "straight", False) else "curve"


def ribbon(stretches, pen):
    """One stroke with square ends: along the right edge, back along the left.

    Wound the way the face winds a filled contour, so overlap removal fills it.
    """
    runs = [(_kind(s), s.edge(-1, pen)) for s in stretches]
    runs.append(("line", _join(stretches[-1].edge(-1, pen)(1.0),
                               stretches[-1].edge(1, pen)(1.0))))
    runs += [(_kind(s), _reversed(s.edge(1, pen))) for s in reversed(stretches)]
    runs.append(("line", _join(stretches[0].edge(1, pen)(0.0),
                               stretches[0].edge(-1, pen)(0.0))))
    p, err = _closed(runs)
    if area(p) < 0:
        p = reverse(p)
    return p, err


def ring(stretches, pen):
    """A closed stroke: its outer edge, and its inner edge wound as a hole."""
    out = []
    worst = 0.0
    for side in (1, -1):
        p, err = _closed([(_kind(s), s.edge(side, pen)) for s in stretches])
        worst = max(worst, err)
        out.append(p)
    out.sort(key=lambda p: -abs(area(p)))
    if area(out[0]) < 0:
        out[0] = reverse(out[0])
    if area(out[1]) > 0:
        out[1] = reverse(out[1])
    return out, worst


def _join(a, b):
    return lambda u: (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)


def straight(s):
    s.straight = True
    return s


# ---- the round letter's centreline -------------------------------------

def flatten(p, steps=24):
    """A closed Glyphs path as a polyline."""
    ns = list(p.nodes)
    last = max(i for i, n in enumerate(ns) if n.type != OFFCURVE)
    ns = ns[last + 1:] + ns[:last + 1]
    cur = (ns[-1].position.x, ns[-1].position.y)
    out, off = [], []
    for n in ns:
        q = (n.position.x, n.position.y)
        if n.type == OFFCURVE:
            off.append(q)
            continue
        if n.type == CURVE and len(off) == 2:
            for i in range(1, steps + 1):
                out.append(_bez(cur, off[0], off[1], q, i / float(steps)))
        else:
            out.append(q)
        cur, off = q, []
    return out


def _cross(poly, c, ang):
    """How far the ray from `c` at `ang` travels to reach `poly`."""
    dx, dy = math.cos(ang), math.sin(ang)
    best = None
    for a, b in zip(poly, poly[1:] + poly[:1]):
        sx, sy = b[0] - a[0], b[1] - a[1]
        den = dx * sy - dy * sx
        if abs(den) < 1e-12:
            continue
        s = ((a[0] - c[0]) * sy - (a[1] - c[1]) * sx) / den
        t = ((a[0] - c[0]) * dy - (a[1] - c[1]) * dx) / den
        if s > 0 and 0.0 <= t <= 1.0 and (best is None or s < best):
            best = s
    return best


def centreline(outer, counter, n=360, harmonics=12):
    """The round letter's centreline, half way between its edge and its counter.

    Read as rays from the middle, then smoothed into a Fourier series of the
    ray's length, so that the curve and its direction are both exact functions
    of the angle -- the pen needs the direction, and a polyline's is noisy.
    Returns (at, vel) of the angle, running counter-clockwise.
    """
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    c = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
    angs, rads = [], []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        ro, ri = _cross(outer, c, a), _cross(counter, c, a)
        if ro is not None and ri is not None:
            angs.append(a)
            rads.append((ro + ri) / 2.0)
    m = len(angs)
    coef = [(sum(r * math.cos(k * a) for a, r in zip(angs, rads)) * 2.0 / m,
             sum(r * math.sin(k * a) for a, r in zip(angs, rads)) * 2.0 / m)
            for k in range(harmonics + 1)]

    def rad(t):
        return coef[0][0] / 2.0 + sum(ck * math.cos(k * t) + sk * math.sin(k * t)
                                      for k, (ck, sk) in enumerate(coef) if k)

    def drad(t):
        return sum(k * (sk * math.cos(k * t) - ck * math.sin(k * t))
                   for k, (ck, sk) in enumerate(coef) if k)

    def at(t):
        r = rad(t)
        return c[0] + r * math.cos(t), c[1] + r * math.sin(t)

    def vel(t):
        r, dr = rad(t), drad(t)
        return (dr * math.cos(t) - r * math.sin(t), dr * math.sin(t) + r * math.cos(t))
    return at, vel


def scaled(curve, origin, kx, ky):
    at, vel = curve

    def at2(t):
        x, y = at(t)
        return origin[0] + (x - origin[0]) * kx, origin[1] + (y - origin[1]) * ky

    def vel2(t):
        dx, dy = vel(t)
        return dx * kx, dy * ky
    return at2, vel2


def turns(curve, n=1440):
    """The angles where a closed curve is leftmost, rightmost, lowest, highest."""
    at, vel = curve
    out = []
    ts = [2.0 * math.pi * i / n for i in range(n + 1)]
    for axis in (0, 1):
        vs = [vel(t)[axis] for t in ts]
        for a, b, va, vb in zip(ts, ts[1:], vs, vs[1:]):
            if va == 0 or va * vb < 0:
                lo, hi = a, b
                for _ in range(40):
                    mid = (lo + hi) / 2.0
                    if vel(lo)[axis] * vel(mid)[axis] <= 0:
                        hi = mid
                    else:
                        lo = mid
                out.append((lo + hi) / 2.0)
    return sorted(set(round(t, 9) for t in out))


def length(curve, t0, t1, n=200):
    at = curve[0]
    pts = [at(t0 + (t1 - t0) * i / float(n)) for i in range(n + 1)]
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
