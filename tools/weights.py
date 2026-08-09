"""Stroke weight measured off the rendered glyph, not off the outline.

    ./venv/bin/python tools/weights.py            # б's branch against o's wall
    ./venv/bin/python tools/weights.py б ю        # named letters

Every other weight probe here reads contours, and reading contours means
deciding which contour is which and which direction is across the stroke.
Both decisions have been wrong: a scanline with a slope correction read a
near-horizontal stroke at four times its weight, and a ray cast between two
contours reported a branch thinned to 0.92 of the bowl's wall that measured
1.77 once built.

This one decides nothing. It renders the glyph, computes the exact Euclidean
distance from every ink pixel to the nearest non-ink pixel, and reads the
stroke's half-width straight off that: the largest disc that fits inside the
ink at a point IS the stroke's thickness there, whatever direction the stroke
runs and whatever contour it came from. The same code renders the panel, so
"ours" and "theirs" are the same quantity by construction.

Reported as a profile rather than a number, because a stroke that is right on
average can be wrong at its elbow -- which is what the eye catches first.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from scipy import ndimage

from panel import families

XH = 420

# A pixel is ink when its centre is inside the outline, so the distance from
# an ink pixel to the nearest non-ink one is measured centre to centre and the
# true edge lies half a pixel further out on each side. Twice the distance is
# therefore about one pixel more than the stroke. Found by the self-test on
# the first run, which is what a self-test is for.
BIAS = 1.0


def width(d):
    """A stroke's width from the distances inside it."""
    return max(0.0, 2.0 * float(np.max(d)) - BIAS)
LETTERS = "б"


def edt(mask):
    """Distance from each True pixel to the nearest False one, in pixels."""
    return ndimage.distance_transform_edt(mask)


def holes(mask):
    """The enclosed background -- counters, and nothing else."""
    return ndimage.binary_fill_holes(mask) & ~mask


def counter_top(mask, h):
    """The highest row of the LARGEST hole, and the bowl's own wall.

    Largest, not any: an even-odd raster of this letter encloses a one-pixel
    pocket at the seam where the branch meets the bowl, and a minimum over
    every hole let that single pixel decide where the branch began. The bowl's
    counter is the only hole worth the name.
    """
    lab, n = ndimage.label(h)
    if not n:
        return None, None
    sizes = ndimage.sum(h, lab, range(1, n + 1))
    big = lab == (int(sizes.argmax()) + 1)
    rows = np.where(big.any(axis=1))[0]
    band = np.zeros_like(mask)
    band[rows.min():rows.max() + 1] = True
    return int(rows.min()), width(edt(mask & band))


def render(path, ch, xh):
    """The glyph as an ink mask, scaled so the face's own o stands `xh` high."""
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        upem = f["head"].unitsPerEm
        gs = f.getGlyphSet()
        cm = f.getBestCmap()
        if ord(ch) not in cm:
            return None
        from probe import contours
        o = contours(f, "o", cm, gs)
        if not o:
            return None
        ys = [q[1] for p in o for q in p]
        own = (max(ys) - min(ys)) / float(upem)
    finally:
        f.close()
    size = int(round(xh / own))
    if size < 40 or size > 4000:
        return None
    fnt = ImageFont.truetype(path, size)
    img = Image.new("L", (int(size * 1.6), int(size * 2.2)), 0)
    ImageDraw.Draw(img).text((int(size * 0.2), int(size * 0.2)), ch,
                             font=fnt, fill=255)
    a = np.asarray(img) > 127
    return a if a.any() else None


def wall(path, xh):
    """The bowl's own wall: the widest disc that fits inside o's ring."""
    m = render(path, "o", xh)
    return None if m is None else width(edt(m))


def junction(mask, wall):
    """The widest disc anywhere in the letter, over the bowl's own wall.

    There is no region decision in this one, which is the point. `branch_of`
    has to say where the branch stops being bowl, and the place a stroke most
    often goes wrong -- where it merges into the bowl -- is exactly the place
    that decision excludes. It did: with the branch reading a flat 0.86 at
    every weight, this read 2.42 at Thin against a panel ninetieth percentile
    of 1.39, and the blob was at the heel, outside the rows `branch_of` keeps.

    `wall` is read off the face's own o and passed in. Measured off the letter
    itself it is contaminated by the very fault being looked for -- the heavier
    the blob, the wider the "wall", and the less of it the reading sees.
    """
    return width(edt(mask)) / wall


def branch_rows(mask):
    """Which rows are branch and which are still bowl.

    The counter's highest row is NOT where the branch starts: the bowl's own
    crown sits above it, one wall thick, and a row through the crown reports
    the wall rather than the branch. Left in it floors every reading near 1.0,
    and a solve against a floored measure runs to the end of its bracket and
    reports success -- which is what happened. At ExtraBold the crown is 28
    per cent of the rows above the counter against a trim of 12.
    """
    h = holes(mask)
    if not h.any():
        return None
    top, w = counter_top(mask, h)
    if top is None or not w:
        return None
    return max(0, int(top - round(w))), w


def branch_of(mask):
    """The stroke's thickness along the branch, terminal first.

    Trimmed by the bowl's own wall at each end rather than by a fixed share:
    the first rows are the terminal's own cut and the last are the junction,
    and both scale with the weight where a percentage does not.
    """
    span = branch_rows(mask)
    if span is None:
        return None
    top, w = span
    d = edt(mask)
    rows = [width(d[y]) for y in range(0, top) if mask[y].any()]
    cut = int(round(w * 0.5))
    return rows[cut:len(rows) - cut] if len(rows) > 4 * cut + 4 else rows


def branch(path, ch, xh):
    m = render(path, ch, xh)
    return None if m is None else branch_of(m)


def mask_of(polys, k):
    """Flattened contours to an ink mask, counters punched out by even-odd."""
    from PIL import ImageChops
    xs = [q[0] for p in polys for q in p]
    ys = [q[1] for p in polys for q in p]
    w = int((max(xs) - min(xs)) * k) + 8
    h = int((max(ys) - min(ys)) * k) + 8
    img = Image.new("1", (w, h), 0)
    for poly in polys:
        lay = Image.new("1", (w, h), 0)
        ImageDraw.Draw(lay).polygon(
            [(4 + (x - min(xs)) * k, h - 4 - (y - min(ys)) * k)
             for x, y in poly], fill=1)
        img = ImageChops.logical_xor(img, lay)
    return np.asarray(img) > 0


def from_recipe(ch, mi, xh=XH):
    """The same mask, straight from the recipes, so the loop is seconds.

    A build takes minutes and this reading has to be taken after every change
    to the outline; the built font is still what the report quotes.
    """
    import glyphsLib
    from params import Params, Lower, _flatten
    from classify import TIERS
    import recipes as RU
    import preview as PV
    font = glyphsLib.load(open("sources/SUSEMono.glyphs"))
    names = {chr(cp): n for cp, n, _t, _n in TIERS if n in RU.RECIPES}
    pr = Lower(Params(font, mi))
    fn = RU.RECIPES.get(names.get(ch, ""))
    out = []
    for paths in (fn(pr._pr) if fn else pr.paths(ch), pr.paths("o")):
        polys = [[(x, y) for x, y in _flatten(p, 96)] for p in paths]
        ys = [q[1] for p in polys for q in p]
        xs = [q[0] for p in polys for q in p]
        k = xh / float(pr.cap)
        w = int((max(xs) - min(xs)) * k) + 8
        h = int((max(ys) - min(ys)) * k) + 8
        img = Image.new("1", (w, h), 0)
        from PIL import ImageChops
        for poly in polys:
            lay = Image.new("1", (w, h), 0)
            ImageDraw.Draw(lay).polygon(
                [(4 + (x - min(xs)) * k, h - 4 - (y - min(ys)) * k)
                 for x, y in poly], fill=1)
            img = ImageChops.logical_xor(img, lay)
        out.append(np.asarray(img) > 0)
    return out


# --- the instrument's own test -------------------------------------------

def _known(coords, w, px=12.0, taper=None):
    """A mask of a stroke of KNOWN width, built by shapely.

    The width is not something this file computed: the shape is a centreline
    buffered by half of it, so the answer is true by construction. That is the
    whole point -- four gauges in a row were wrong and none had ever been shown
    a shape whose answer was known.
    """
    from shapely.geometry import LineString
    from shapely.ops import unary_union
    from PIL import ImageChops
    line = LineString(coords)
    if taper is None:
        geom = line.buffer(w / 2.0, resolution=64)
    else:
        n, parts = 240, []
        for i in range(n):
            a = line.interpolate(i / float(n), normalized=True)
            b = line.interpolate((i + 1.0) / n, normalized=True)
            t = (i + 0.5) / n
            parts.append(LineString([a, b]).buffer(
                (taper[0] + (taper[1] - taper[0]) * t) / 2.0, resolution=16))
        geom = unary_union(parts)
    x0, y0, x1, y1 = geom.bounds
    size = (int((x1 - x0) * px) + 20, int((y1 - y0) * px) + 20)
    img = Image.new("1", size, 0)
    rings = ([geom.exterior] + list(geom.interiors) if geom.geom_type
             == "Polygon" else [g.exterior for g in geom.geoms])
    for ring in rings:
        lay = Image.new("1", size, 0)
        ImageDraw.Draw(lay).polygon(
            [(10 + (x - x0) * px, 10 + (y - y0) * px) for x, y in ring.coords],
            fill=1)
        img = ImageChops.logical_xor(img, lay)
    return np.asarray(img) > 0, px


def selftest():
    """Known widths in, known widths out -- or nothing here is usable."""
    import math
    ok = True

    ring = [(50 + 30 * math.cos(a), 50 + 30 * math.sin(a))
            for a in np.linspace(0, 2 * math.pi, 500)]
    bend = ([(0, 0), (0, 40)]
            + [(20 - 20 * math.cos(a), 40 + 20 * math.sin(a))
               for a in np.linspace(0, math.pi / 2, 80)]
            + [(20, 60), (60, 60)])
    flat = [(0, 0), (100, 17.6)]                    # 10 degrees off horizontal
    steep = [(0, 0), (17.6, 100)]

    for label, coords, w in (
            ("a closed ring", ring, 8.0),
            ("a right-angle bend -- the elbow must not spike", bend, 10.0),
            ("a stroke 10 degrees off horizontal", flat, 9.0),
            ("the same stroke 10 degrees off vertical", steep, 9.0)):
        mask, px = _known(coords, w)
        got = width(edt(mask)) / px
        bad = abs(got - w) / w > 0.03
        ok &= not bad
        print("   %-48s want %5.2f  got %5.2f  %+5.1f%%  %s"
              % (label, w, got, 100 * (got - w) / w, "FAIL" if bad else "ok"))

    mask, px = _known([(0, 0), (140, 0)], 0, taper=(6.0, 14.0))
    d = edt(mask)
    cols = [width(d[:, x]) / px for x in range(mask.shape[1])
            if mask[:, x].any()]
    lo, hi = cols[len(cols) // 8], cols[-1 - len(cols) // 8]
    bad = abs(lo - 6.5) / 6.5 > 0.1 or abs(hi - 13.5) / 13.5 > 0.1
    ok &= not bad
    print("   %-48s want %5.2f %5.2f  got %5.2f %5.2f  %s"
          % ("a taper, read end to end", 6.5, 13.5, lo, hi,
             "FAIL" if bad else "ok"))
    return ok


def report(ch, xh=XH):
    rows = []
    for fam, path in families():
        try:
            w = wall(path, xh)
            b = branch(path, ch, xh) if w else None
            if b:
                s = sorted(v / w for v in b)
                rows.append((s[len(s) // 2], s[-1], fam))
        except Exception:
            pass
    return rows


def main():
    if "--selftest" in sys.argv:
        print("=== weights.py against shapes of known width ===")
        good = selftest()
        print("   %s" % ("instrument usable"
                         if good else "INSTRUMENT FAILED -- do not trust it"))
        sys.exit(0 if good else 1)
    for ch in ("".join(sys.argv[1:]) or LETTERS):
        rows = report(ch)
        if len(rows) < 8:
            print("%s: only %d faces -- not read" % (ch, len(rows)))
            continue
        med = sorted(r[0] for r in rows)
        mx = sorted(r[1] for r in rows)
        print("=" * 70)
        print("%s branch over its own o's wall, measured on the raster,"
              " %d faces" % (ch, len(rows)))
        print("   typical  p10 %.2f  median %.2f  p90 %.2f"
              % (med[len(med) // 10], med[len(med) // 2],
                 med[-1 - len(med) // 10]))
        print("   thickest p10 %.2f  median %.2f  p90 %.2f"
              % (mx[len(mx) // 10], mx[len(mx) // 2], mx[-1 - len(mx) // 10]))
        for w in ("Thin", "Regular", "Bold", "ExtraBold"):
            p = "fonts/ttf/SUSEMono-%s.ttf" % w
            ww = wall(p, XH)
            b = branch(p, ch, XH)
            if not b or not ww:
                continue
            s = sorted(v / ww for v in b)
            print("   SUSE Mono %-10s typical %.2f   thickest %.2f"
                  % (w, s[len(s) // 2], s[-1]))


if __name__ == "__main__":
    main()
