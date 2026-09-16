"""в traced out of the swept ink, beside the donor, as an SVG."""
import sys
import numpy as np
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
from skimage import measure
from vpen import paths, ink
from verode import load, _flat, LIGHT, BOLD

CELL = 430


def trace(mask, tol=1.2):
    out = []
    for c in measure.find_contours(mask.astype(float), 0.5):
        if len(c) < 24:
            continue
        p = measure.approximate_polygon(c, tolerance=tol)
        if len(p) > 6:
            out.append([(float(x), float(y)) for y, x in p])
    return out


def d_of(rings, box, flip_h):
    x0, y0, x1, y1 = box
    parts = []
    for r in rings:
        parts.append("M%.1f %.1f" % (r[0][0], flip_h - r[0][1]))
        parts += ["L%.1f %.1f" % (x, flip_h - y) for x, y in r[1:]]
        parts.append("Z")
    return "".join(parts)


def main():
    cols = []
    segs, _k = load(740.0, LIGHT)
    polys = [_flat(c, 40) for c in segs]
    xs = [x for p in polys for x, _y in p]
    ys = [y for p in polys for _x, y in p]
    cols.append(("Radon, tail off", polys, (min(xs), min(ys), max(xs), max(ys)), None))

    for name, which, h, w, wide in (("ours Thin", LIGHT, 740.0, 26.5, 1.0),
                                    ("ours ExtraBold", BOLD, 730.0, 132.0, 1.45)):
        loop, bowl, stub = paths(which, h, wide)
        m, k = ink([(loop, True), (bowl, True), (stub, False)], w)
        cols.append((name, trace(m), None, m.shape))

    out, x = [], 20
    for name, rings, box, shape in cols:
        if box is not None:
            k = CELL / (box[3] - box[1])
            rings = [[((px - box[0]) * k, (py - box[1]) * k) for px, py in r]
                     for r in rings]
            hh = CELL
        else:
            # scale on whichever of height or width binds, or the widened
            # ExtraBold runs off the sheet
            wx = max(px for r in rings for px, _p in r)
            k = min(CELL / (shape[0] * 0.86), CELL * 0.78 / wx)
            rings = [[(px * k, (shape[0] - py) * k) for px, py in r]
                     for r in rings]
            hh = shape[0] * k
        out.append('<text x="%d" y="24" font-family="sans-serif" '
                   'font-size="13" fill="#666">%s</text>' % (x, name))
        out.append('<g transform="translate(%.1f,%.1f)">'
                   '<path d="%s" fill="#111" fill-rule="evenodd"/></g>'
                   % (x, 40 + hh, d_of(rings, None, 0.0) if False else ""))
        # emit with y already flipped above
        parts = []
        for r in rings:
            parts.append("M%.1f %.1f" % (r[0][0], -r[0][1]))
            parts += ["L%.1f %.1f" % (px, -py) for px, py in r[1:]]
            parts.append("Z")
        out[-1] = ('<g transform="translate(%.1f,%.1f)">'
                   '<path d="%s" fill="#111" fill-rule="evenodd"/></g>'
                   % (x, 40 + hh, "".join(parts)))
        x += CELL * 0.9
    w2, h2 = x + 20, 40 + CELL * 1.25
    print('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="#fff"/>'
          '%s</svg>' % (w2, h2, w2, h2, "".join(out)))
    sys.stderr.write("%d %d\n" % (w2, h2))


if __name__ == "__main__":
    main()
