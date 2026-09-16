"""в built the way route A says: Radon's spine, this face's width.

The spine comes off the donor's raster, is CLOSED at the bowl (Radon leaves
it a spiral), is smoothed -- which a spine may be and an edge may not -- and
then has ink laid along it at one constant width. Even by construction,
because the width is a number rather than a measurement.
"""
import math
import sys
import numpy as np
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
from PIL import Image, ImageDraw
from vspine import raster, spine, branches, to_units
from verode import load, LIGHT, BOLD

SMOOTH = 55             # the spine's smoothing window, in raster pixels
STEP = 14               # and how often it is sampled after that


def cycles(which, height):
    """The two spine loops, in font units: the upper loop and the bowl."""
    segs, _k = load(height, which)
    m, k, org = raster(segs)
    brs, junc = branches(spine(m))
    brs.sort(key=len, reverse=True)
    loop = to_units(brs[0], k, org)
    sweep = to_units(brs[1], k, org)
    # Radon's bowl ends in a spiral. Closing it on the SPINE costs nothing --
    # a spine join is a point, not an edge, so smoothing rounds it away. The
    # same join taken on the OUTLINE left a lid with a nick in it.
    sweep = sweep + [loop[0]]
    return [smooth(loop), smooth(sweep)]


def smooth(pts, win=SMOOTH, step=STEP, closed=True):
    """A moving average along the path.

    `closed` matters. Wrapped round on an OPEN path the window averages the
    start with the END, so the bowl sweep's first point was dragged toward
    the curl tip and left a horizontal spur across the letter. An open path
    holds its endpoints instead.
    """
    n = len(pts)
    w = max(3, min(win, n // 3))
    h = w // 2
    out = []
    for i in range(0, n, step):
        xs = ys = 0.0
        c = 0
        for j in range(-h, h + 1):
            k = (i + j) % n if closed else min(n - 1, max(0, i + j))
            xs += pts[k][0]
            ys += pts[k][1]
            c += 1
        out.append((xs / c, ys / c))
    return out


def stroke(cycle, w):
    """Ink along a closed spine: the two offsets, half a width each side.

    The two loops come off the skeleton walked in whatever direction the pixel
    order happened to give, so one of them ran clockwise and its two offsets
    came out swapped -- the bowl drew nothing at all, its "outer" sitting
    inside its "inner". Each cycle is turned the same way first.
    """
    n = len(cycle)
    area = 0.5 * sum(cycle[i][0] * cycle[(i + 1) % n][1]
                     - cycle[(i + 1) % n][0] * cycle[i][1] for i in range(n))
    if area > 0:
        cycle = cycle[::-1]
    outer, inner = [], []
    for i in range(n):
        ax, ay = cycle[(i - 1) % n]
        bx, by = cycle[(i + 1) % n]
        m = math.hypot(bx - ax, by - ay) or 1.0
        nx, ny = -(by - ay) / m, (bx - ax) / m
        p = cycle[i]
        outer.append((p[0] + nx * w / 2.0, p[1] + ny * w / 2.0))
        inner.append((p[0] - nx * w / 2.0, p[1] - ny * w / 2.0))
    return outer, inner


def mask_of(rings, box, px=900.0, pad=30):
    x0, y0, x1, y1 = box
    k = px / (y1 - y0)
    W = int((x1 - x0) * k) + 2 * pad
    H = int((y1 - y0) * k) + 2 * pad
    ink = np.zeros((H, W), dtype=bool)
    to = lambda p: (pad + (p[0] - x0) * k, H - pad - (p[1] - y0) * k)
    for outer, inner in rings:
        a = Image.new("L", (W, H), 0)
        ImageDraw.Draw(a).polygon([to(p) for p in outer], fill=255)
        b = Image.new("L", (W, H), 0)
        ImageDraw.Draw(b).polygon([to(p) for p in inner], fill=255)
        ink |= (np.asarray(a) > 127) & ~(np.asarray(b) > 127)
    return ink


def box_of(rings):
    xs = [p[0] for o, i in rings for p in o]
    ys = [p[1] for o, i in rings for p in o]
    return min(xs), min(ys), max(xs), max(ys)


if __name__ == "__main__":
    from scipy import ndimage
    from weights import edt, BIAS
    for name, which, h, w in (("Thin", LIGHT, 740.0, 26.5),
                              ("ExtraBold", BOLD, 730.0, 132.0)):
        cs = cycles(which, h)
        rings = [stroke(c, w) for c in cs]
        ink = mask_of(rings, box_of(rings))
        d = edt(ink)
        top = ndimage.maximum_filter(d, size=3)
        keep = (d >= top - 1e-9) & (d > 1.5)
        k = 900.0 / (box_of(rings)[3] - box_of(rings)[1])
        ws = np.sort((2.0 * d[keep] - BIAS) / k)
        q = lambda f: ws[int(f * (len(ws) - 1))]
        print("%-10s spine loops %s   width asked %.0f -> "
              "q1 %5.1f med %5.1f q3 %5.1f   q3/q1 %.2f"
              % (name, [len(c) for c in cs], w,
                 q(.25), q(.5), q(.75), q(.75) / q(.25)))
        Image.fromarray((ink * 255).astype("uint8")).save(
            "/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
            "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/vstroke-%s.png"
            % name)
