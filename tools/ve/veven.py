"""Set в's stroke to ONE width instead of inheriting the donor's.

Radon's в is a script letter and varies 20% at its light master and 32% at
its bold, where its own o holds 7-10% and this face's o holds 5% at Thin.
Thinning it by a flat amount keeps all of that: *"why does the stroke have
different width at different parts of the glyph?"*

So the edge is walked at a fine step, the ribbon measured ACROSS at each
step, and each sample moved by half of however much it is out -- a wide spot
gives up more than a narrow one. The donor's shape, path and topology are
untouched; only its weight is overwritten, which is the one thing about it
that was never ours.

Near the crossing the ray genuinely leaves the ribbon, and the ink there IS
thicker because two strokes lie on top of each other. Those samples are left
where they are rather than thinned to a stroke.
"""
import math
import sys
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
from verode import (load, rejoin, nodes_of, signed_area, _flat, across,
                    _unit, LIGHT, BOLD)

STEP = 4.0              # how finely the edge is walked, in units
KEEP = (0.55, 1.7)      # widths outside this share of the median are junctions


def walk(contour, step=STEP):
    poly = _flat(contour, 32)
    out, carry = [], 0.0
    for i in range(len(poly) - 1):
        (ax, ay), (bx, by) = poly[i], poly[i + 1]
        seg = math.hypot(bx - ax, by - ay)
        if seg < 1e-9:
            continue
        t = carry
        while t < seg:
            u = t / seg
            out.append(((ax + (bx - ax) * u, ay + (by - ay) * u),
                        ((bx - ax) / seg, (by - ay) / seg)))
            t += step
        carry = t - seg
    return out


def even(segs, target):
    """Every contour re-walked and moved so the ribbon is `target` wide."""
    polys = [_flat(c, 32) for c in segs]
    out = []
    for c in segs:
        pts, _h = nodes_of(c)
        s = 1.0 if signed_area(pts) > 0 else -1.0
        sam = walk(c)
        raw = []
        for p, d in sam:
            n = (-s * d[1], s * d[0])
            raw.append((p, n, across(polys, p, n)))
        ws = sorted(w for _p, _n, w in raw)
        med = ws[len(ws) // 2]
        lo, hi = KEEP[0] * med, KEEP[1] * med
        # Where the ray leaves the ribbon the sample gets no reading of its
        # own, and left unmoved it kept the donor's weight while everything
        # around it thinned -- the junction then measured twice the stroke.
        # The move is carried ACROSS such a run from the good samples either
        # side of it, so the edge stays smooth and the junction thins with
        # the rest of the letter.
        ds = [None if not (lo < w < hi) else (w - target) / 2.0
              for _p, _n, w in raw]
        m = len(ds)
        good = [i for i, d in enumerate(ds) if d is not None]
        if not good:
            raise ValueError("ve: no sample on this contour read a width")
        for i, d in enumerate(ds):
            if d is not None:
                continue
            back = max((j for j in good if j <= i), default=good[-1])
            fwd = min((j for j in good if j >= i), default=good[0])
            gap = (fwd - back) % m or 1
            t = ((i - back) % m) / gap
            ds[i] = ds[back] * (1.0 - t) + ds[fwd] * t
        moved = [(p[0] + n[0] * d, p[1] + n[1] * d)
                 for (p, n, _w), d in zip(raw, ds)]
        out.append(moved)
    return out


def spread_of(polys, target=None):
    """The width along a set of polylines, for the check."""
    res = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            ax, ay = poly[i]
            bx, by = poly[(i + 1) % n]
            u = _unit(bx - ax, by - ay)
            if u is None:
                continue
            res.append((poly[i], u))
    return res


if __name__ == "__main__":
    from vwidth import spread
    print("setting the width instead of inheriting it:")
    segs, _k = load(740.0, LIGHT)
    segs = [rejoin(segs[0])] + segs[1:]
    spread(segs, "Radon light, rejoined")
    for t in (26.0,):
        polys = even(segs, t)
        # measured back off the moved polylines themselves
        from verode import across as _ac
        import statistics
        ws = []
        for pi, poly in enumerate(polys):
            s = 1.0 if signed_area([(x, y) for x, y in poly]) > 0 else -1.0
            for i in range(0, len(poly), 3):
                ax, ay = poly[i]
                bx, by = poly[(i + 1) % len(poly)]
                u = _unit(bx - ax, by - ay)
                if u is None:
                    continue
                w = _ac(polys, (ax, ay), (-s * u[1], s * u[0]))
                if w < 400:
                    ws.append(w)
        ws.sort()
        q = lambda f: ws[int(f * (len(ws) - 1))]
        print("  target %.0f -> q1 %5.1f  med %5.1f  q3 %5.1f   q3/q1 %.2f"
              % (t, q(.25), q(.5), q(.75), q(.75) / q(.25)))
