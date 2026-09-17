"""в closed at the crossing: the bowl's closure runs INTO the junction.

vpen closed the bowl at the curl's own height, on the stem below the
crossing. That left a length of bare stem between the loop and the bowl,
and a white slot between the loop's underside and the bowl's lid.
Here the closure is aimed at the crossing and leaves it along the loop's
upper-left arm, so the pen passes through: a real X, nothing between.
"""
import math
import sys
import numpy as np
sys.path.insert(0, "tools")
from PIL import Image
from vspine import raster, spine, branches, to_units
from vstroke import smooth
from verode import load, _unit, LIGHT, BOLD
from vpen import ink


def arclen_cut(pts, d):
    """Drop `d` units of length off the path's end."""
    acc = 0.0
    for i in range(len(pts) - 1, 0, -1):
        acc += math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
        if acc >= d:
            return pts[:i]
    return pts[:2]


def paths(which, height, wide=1.0, cut=0.0, pull=(0.45, 0.45), bend=1.0):
    segs, _k = load(height, which)
    m, k, org = raster(segs)
    brs, junc = branches(spine(m))
    brs.sort(key=len, reverse=True)
    stretch = lambda ps: [(p[0] * wide, p[1]) for p in ps]
    jr = sum(p[0] for p in junc) / len(junc)
    jc = sum(p[1] for p in junc) / len(junc)
    C = stretch(to_units([(jr, jc)], k, org))[0]
    loop = stretch(to_units(brs[0], k, org))
    sweep = stretch(to_units(brs[1], k, org))
    d = lambda p: math.hypot(p[0] - C[0], p[1] - C[1])
    if d(sweep[0]) > d(sweep[-1]):
        sweep = sweep[::-1]
    # the loop is an open run from the junction back to it; smoothing it
    # CLOSED rounded that corner away and floated the loop off the stem
    loop = [C] + smooth(loop, step=6, closed=False) + [C]
    sweep = [C] + smooth(sweep, step=6, closed=False)
    sweep = arclen_cut(sweep, cut)
    # which of the loop's two arms climbs: the closure continues into it
    a1, a2 = loop[3], loop[-4]
    up = a1 if a1[1] > a2[1] else a2
    u = _unit(up[0] - C[0], up[1] - C[1])
    e = sweep[-1]
    t = _unit(e[0] - sweep[-3][0], e[1] - sweep[-3][1])
    span = d(e)
    p1 = (e[0] + t[0] * span * pull[0], e[1] + t[1] * span * pull[0])
    # arriving straight up the loop's arm forces the lid to dip under the
    # crossing first; `bend` blends that direction with the plain chord
    ch = _unit(C[0] - e[0], C[1] - e[1])
    v = _unit(bend * u[0] + (1 - bend) * ch[0], bend * u[1] + (1 - bend) * ch[1])
    p2 = (C[0] - v[0] * span * pull[1], C[1] - v[1] * span * pull[1])
    arc = []
    for i in range(1, 41):
        s = i / 40.0
        r = 1 - s
        arc.append((r**3 * e[0] + 3*r*r*s * p1[0] + 3*r*s*s * p2[0] + s**3 * C[0],
                    r**3 * e[1] + 3*r*r*s * p1[1] + 3*r*s*s * p2[1] + s**3 * C[1]))
    # carry the pen a little past the crossing along the arm, so the join
    # is a crossing and not two ends butted together
    over = [(C[0] + v[0] * f, C[1] + v[1] * f) for f in (4.0, 8.0)]
    return loop, sweep + arc + over, C


def measure(m, k):
    from scipy import ndimage
    from weights import edt, BIAS
    d = edt(m)
    top = ndimage.maximum_filter(d, size=3)
    keep = (d >= top - 1e-9) & (d > 1.5)
    ws = np.sort((2.0 * d[keep] - BIAS) / k)
    q = lambda f: ws[int(f * (len(ws) - 1))]
    holes = ndimage.label(ndimage.binary_fill_holes(m) & ~m,
                          structure=np.ones((3, 3)))[1]
    return q(.25), q(.5), q(.75), holes


if __name__ == "__main__":
    tiles = []
    for spec in sys.argv[1:]:
        cut, bend, pa, pb = (float(x) for x in spec.split(","))
        loop, bowl, C = paths(LIGHT, 740.0, 1.0, cut, (pa, pb), bend)
        m, k = ink([(loop, False), (bowl, False)], 26.5, px=420.0)
        q1, med, q3, holes = measure(m, k)
        print("%-18s q3/q1 %.2f  counters %d" % (spec, q3 / q1, holes))
        tiles.append(Image.fromarray(((~m) * 255).astype("uint8")))
    W = sum(t.width for t in tiles) + 20 * len(tiles)
    out = Image.new("L", (W, max(t.height for t in tiles)), 255)
    x = 0
    for t in tiles:
        out.paste(t, (x, 0)); x += t.width + 20
    out.save("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
             "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/vpen2.png")


def fill_specks(m, k, w, share=0.5):
    """Fill enclosed white smaller than `share` of a stroke squared.

    Where three strokes converge they can trap a speck of white. It is not a
    counter -- real counters are hundreds of times larger -- and no drawn
    letter would keep it.
    """
    import numpy as np
    from scipy import ndimage
    holes = ndimage.binary_fill_holes(m) & ~m
    lbl, n = ndimage.label(holes, structure=np.ones((3, 3)))
    if not n:
        return m
    sizes = ndimage.sum(holes, lbl, range(1, n + 1))
    small = [i + 1 for i, a in enumerate(sizes) if a < share * (w * k) ** 2]
    return m | np.isin(lbl, small)
