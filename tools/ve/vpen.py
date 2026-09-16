"""в as a pen would lay it: three overlapping strokes of one width.

Built as two closed spine loops it pinched where they met, because two curves
through one shared point touch there and nothing more. A pen passing the same
place twice leaves ink that overlaps over a RUN, which is what reads as one
continuous stroke.

So the ink is the union of three strokes, each the same width:
  * the loop, closed;
  * the bowl's sweep, from the crossing round to the curl;
  * the closure, from the curl back to the descending stroke.
The counters are whatever white the three leave between them.
"""
import math
import sys
import numpy as np
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
from PIL import Image, ImageDraw
from vspine import raster, spine, branches, to_units
from vstroke import smooth
from verode import load, _unit, LIGHT, BOLD


def paths(which, height, wide=1.0):
    """The three strokes, in font units.

    `wide` stretches the spine horizontally. This face's own rule is that the
    letter widens FIRST, then counters give way, then stroke weight -- and at
    ExtraBold it draws its o a quarter heavier, relative to the x-height,
    than Radon draws its heaviest. Laid at our weight on Radon's own bold
    spine the counters shut. So the spine gets the room instead.
    """
    segs, _k = load(height, which)
    m, k, org = raster(segs)
    brs, _j = branches(spine(m))
    brs.sort(key=len, reverse=True)
    stretch = lambda ps: [(p[0] * wide, p[1]) for p in ps]
    loop = smooth(stretch(to_units(brs[0], k, org)))
    sweep = smooth(stretch(to_units(brs[1], k, org)), step=6, closed=False)
    # the sweep is walked from the crossing, so its own early points ARE the
    # descending stroke; the closure comes back to whichever of them sits at
    # the curl's height
    # A straight chord from the curl to the stem trapped a sliver between
    # itself and the descending stroke, and met the sweep at a kink. The
    # closure leaves along the sweep's OWN direction instead and curves in,
    # so it grows out of the stroke it finishes.
    tip = sweep[-1]
    head = sweep[:max(3, len(sweep) // 4)]
    q = min(range(len(head)), key=lambda i: abs(head[i][1] - tip[1]))
    Q = head[q]
    t = _unit(tip[0] - sweep[-4][0], tip[1] - sweep[-4][1]) or (-1.0, 0.0)
    span = math.hypot(Q[0] - tip[0], Q[1] - tip[1])
    c = (tip[0] + t[0] * span * 0.55, tip[1] + t[1] * span * 0.55)
    arc = [((1 - u) ** 2 * tip[0] + 2 * (1 - u) * u * c[0] + u * u * Q[0],
            (1 - u) ** 2 * tip[1] + 2 * (1 - u) * u * c[1] + u * u * Q[1])
           for u in [i / 20.0 for i in range(1, 20)]]
    # The bowl is one CLOSED curve -- its sweep from the closure point round
    # and the closure itself -- and it is smoothed as one. Smoothed in pieces
    # the closure met the sweep at a kink and left the bowl's top lumpy.
    bowl = smooth(sweep[q:] + arc, win=9, step=1)
    stub = sweep[:q + 1]
    return loop, bowl, stub


def ink(strokes, w, px=900.0, pad=None):
    xs = [p[0] for s, _c in strokes for p in s]
    ys = [p[1] for s, _c in strokes for p in s]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    k = px / (y1 - y0)
    # the ink reaches half a width past the spine, so the margin has to
    # clear that -- at ExtraBold a fixed 40px cropped the letter
    if pad is None:
        pad = int(w * k / 2.0) + 20
    W = int((x1 - x0) * k) + 2 * pad
    H = int((y1 - y0) * k) + 2 * pad
    # A thick polyline rasteriser leaves pinholes at its joints -- nine
    # spurious counters at Thin and a hundred and seventy-five at ExtraBold.
    # The pen is a DISC swept along the path, so the path is drawn one pixel
    # wide and then everything within half a width of it is ink. That is an
    # exact Euclidean dilation and it cannot leave a gap.
    img = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(img)
    to = lambda p: (pad + (p[0] - x0) * k, H - pad - (p[1] - y0) * k)
    for pts, closed in strokes:
        xy = [to(p) for p in pts] + ([to(pts[0])] if closed else [])
        dr.line(xy, fill=255, width=1)
    from scipy import ndimage as _nd
    far = _nd.distance_transform_edt(~(np.asarray(img) > 127))
    return far <= w * k / 2.0, k


if __name__ == "__main__":
    from scipy import ndimage
    from weights import edt, BIAS
    for name, which, h, w, wide in (("Thin", LIGHT, 740.0, 26.5, 1.0),
                                    ("ExtraBold", BOLD, 730.0, 132.0, 1.45)):
        loop, bowl, stub = paths(which, h, wide)
        m, k = ink([(loop, True), (bowl, True), (stub, False)], w)
        d = edt(m)
        top = ndimage.maximum_filter(d, size=3)
        keep = (d >= top - 1e-9) & (d > 1.5)
        ws = np.sort((2.0 * d[keep] - BIAS) / k)
        q = lambda f: ws[int(f * (len(ws) - 1))]
        holes = ndimage.label(ndimage.binary_fill_holes(m) & ~m,
                              structure=np.ones((3, 3)))[1]
        print("%-10s width %.0f -> q1 %5.1f med %5.1f q3 %5.1f  q3/q1 %.2f   "
              "counters %d" % (name, w, q(.25), q(.5), q(.75),
                               q(.75) / q(.25), holes))
        Image.fromarray((m * 255).astype("uint8")).save(
            "/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
            "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/vpen-%s.png" % name)


def ink_oval(strokes, sx, sy, px=900.0, box=None, pad=None):
    """`ink` with an OVAL pen: `sx` thick on upright strokes, `sy` on level ones.

    The heavy o is drawn with exactly such a pen -- its sides are thicker
    than its top and bottom -- and a round pen laid the level parts of в as
    heavy as its sides, which is what closed its counters at ExtraBold.
    """
    xs = [p[0] for s, _c in strokes for p in s]
    ys = [p[1] for s, _c in strokes for p in s]
    x0, y0, x1, y1 = box or (min(xs), min(ys), max(xs), max(ys))
    k = px / (y1 - y0)
    if pad is None:
        pad = int(max(sx, sy) * k / 2.0) + 20
    W = int((x1 - x0) * k) + 2 * pad
    H = int((y1 - y0) * k) + 2 * pad
    img = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(img)
    to = lambda p: (pad + (p[0] - x0) * k, H - pad - (p[1] - y0) * k)
    for pts, closed in strokes:
        xy = [to(p) for p in pts] + ([to(pts[0])] if closed else [])
        dr.line(xy, fill=255, width=1)
    from scipy import ndimage as _nd
    # rows count sx/sy times as far, so the reach is an oval sx wide, sy tall
    far = _nd.distance_transform_edt(~(np.asarray(img) > 127), sampling=(sx / sy, 1.0))
    return far <= sx * k / 2.0, k
