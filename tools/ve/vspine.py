"""Radon's в reduced to the path the pen walked, and that path's shape read
off it: how many loops, where they meet, how many ends.

The spine is the one part of a donated letter this project may keep without
keeping its weight, because weight is exactly what dividing it out removes.
METHOD F15 rejected a spine STROKED AT A CONSTANT WIDTH for the cursive г --
"no modulation and no terminals". Neither objection reaches в: this face's
own o holds its width to within 5% at Thin, so constant IS its modulation
there, and a closed в has no free terminal to cut.
"""
import sys
import numpy as np
sys.path.insert(0, "tools")
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.morphology import skeletonize
from verode import load, _flat, LIGHT, BOLD

PX = 900.0


def raster(segs, pad=30):
    polys = [_flat(c, 40) for c in segs]
    xs = [x for p in polys for x, _y in p]
    ys = [y for p in polys for _x, y in p]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    k = PX / (y1 - y0)
    w = int((x1 - x0) * k) + 2 * pad
    h = int((y1 - y0) * k) + 2 * pad
    img = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(img)
    order = sorted(polys, key=lambda p: -abs(_area(p)))
    for i, poly in enumerate(order):
        dr.polygon([(pad + (x - x0) * k, h - pad - (y - y0) * k)
                    for x, y in poly], fill=255 if i == 0 else 0)
    return np.asarray(img) > 127, k, (x0, y0, pad, h)


def _area(poly):
    n = len(poly)
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % n][1]
                     - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))


def spine(mask):
    return skeletonize(mask)


def graph(sk):
    """Each skeleton pixel's neighbour count -- 1 is an end, 3+ a junction."""
    k = np.ones((3, 3), dtype=int)
    deg = ndimage.convolve(sk.astype(int), k, mode="constant") - 1
    deg[~sk] = 0
    ends = int(((deg == 1) & sk).sum())
    junc = int(((deg >= 3) & sk).sum())
    return deg, ends, junc


if __name__ == "__main__":
    for name, which, h in (("light", LIGHT, 740.0), ("bold", BOLD, 730.0)):
        segs, _k = load(h, which)
        m, k, _o = raster(segs)
        sk = spine(m)
        deg, ends, junc = graph(sk)
        lbl, n = ndimage.label(sk, structure=np.ones((3, 3)))
        # loops: Euler characteristic of the skeleton, 1 component
        print("%-6s skeleton %d px, %d component(s), %d free end(s), "
              "%d junction px" % (name, int(sk.sum()), n, ends, junc))
def branches(sk):
    """The skeleton cut at its junctions, each piece ordered end to end."""
    deg, _e, _j = graph(sk)
    junc = (deg >= 3) & sk
    body = sk & ~junc
    lbl, n = ndimage.label(body, structure=np.ones((3, 3)))
    out = []
    for i in range(1, n + 1):
        px = list(zip(*np.where(lbl == i)))
        if len(px) < 8:
            continue
        out.append(order(set(px)))
    return out, [tuple(p) for p in zip(*np.where(junc))]


def order(px):
    """Walk a thin pixel set from one end to the other."""
    nb = lambda p: [(p[0] + dy, p[1] + dx)
                    for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                    if (dy or dx) and (p[0] + dy, p[1] + dx) in px]
    ends = [p for p in px if len(nb(p)) == 1]
    start = ends[0] if ends else next(iter(px))
    path, seen = [start], {start}
    while True:
        nxt = [q for q in nb(path[-1]) if q not in seen]
        if not nxt:
            break
        # prefer a straight continuation over a diagonal shortcut
        nxt.sort(key=lambda q: abs(q[0] - path[-1][0]) + abs(q[1] - path[-1][1]))
        path.append(nxt[0])
        seen.add(nxt[0])
    return path


def to_units(path, k, org):
    x0, y0, pad, h = org
    return [(x0 + (c - pad) / k, y0 + (h - pad - r) / k) for r, c in path]


if __name__ == "__main__":
    pass
