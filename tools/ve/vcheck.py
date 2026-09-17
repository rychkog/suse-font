"""The evened letter measured the way Radon was: ridge width off the ink."""
import sys
import numpy as np
sys.path.insert(0, "tools")
from PIL import Image, ImageDraw
from scipy import ndimage
from weights import edt, BIAS
from verode import load, rejoin, LIGHT, BOLD
from veven import even

PX = 700.0


def raster(polys, box):
    x0, y0, x1, y1 = box
    k = PX / (y1 - y0)
    w = int((x1 - x0) * k) + 40
    h = int((y1 - y0) * k) + 40
    img = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(img)
    # outer first, then the counters knocked back out
    order = sorted(polys, key=lambda p: -abs(_area(p)))
    for i, poly in enumerate(order):
        xy = [(20 + (x - x0) * k, h - 20 - (y - y0) * k) for x, y in poly]
        dr.polygon(xy, fill=255 if i == 0 else 0)
    return np.asarray(img) > 127, k


def _area(poly):
    n = len(poly)
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % n][1]
                     - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))


def ridge(mask, k):
    d = edt(mask)
    top = ndimage.maximum_filter(d, size=3)
    keep = (d >= top - 1e-9) & (d > 1.5)
    return np.sort((2.0 * d[keep] - BIAS) / k)


def report(polys, box, label):
    m, k = raster(polys, box)
    w = ridge(m, k)
    q = lambda f: w[int(f * (len(w) - 1))]
    print("  %-28s q1 %5.1f  med %5.1f  q3 %5.1f   q3/q1 %.2f"
          % (label, q(.25), q(.5), q(.75), q(.75) / q(.25)))


def box_of(polys):
    xs = [x for p in polys for x, _y in p]
    ys = [y for p in polys for _x, y in p]
    return min(xs), min(ys), max(xs), max(ys)


if __name__ == "__main__":
    from veven import walk
    from verode import _flat
    print("ridge width, the same reading Radon was given:")
    for name, which, height, target in (("our Thin", LIGHT, 740.0, 26.0),
                                        ("our ExtraBold", BOLD, 730.0, 140.0)):
        segs, _k = load(height, which)
        segs = [rejoin(segs[0])] + segs[1:]
        donor = [_flat(c, 32) for c in segs]
        report(donor, box_of(donor), "donor, rejoined (%s)" % name)
        ev = even(segs, target)
        report(ev, box_of(ev), "evened to %.0f (%s)" % (target, name))
