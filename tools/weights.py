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

from panel import families

XH = 220
LETTERS = "б"


def _dt1(f):
    """Felzenszwalb's 1-D squared distance transform."""
    n = len(f)
    d = np.empty(n)
    v = np.zeros(n, dtype=np.int64)
    z = np.empty(n + 1)
    k = 0
    z[0], z[1] = -1e20, 1e20
    for q in range(1, n):
        while True:
            s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2.0 * q
                                                             - 2.0 * v[k])
            if s > z[k]:
                break
            k -= 1
        k += 1
        v[k], z[k], z[k + 1] = q, s, 1e20
    k = 0
    for q in range(n):
        while z[k + 1] < q:
            k += 1
        d[q] = (q - v[k]) ** 2 + f[v[k]]
    return d


def edt(mask):
    """Distance from each True pixel to the nearest False one, in pixels."""
    f = np.where(mask, 1e20, 0.0)
    for axis in (0, 1):
        f = np.apply_along_axis(_dt1, axis, f)
    return np.sqrt(f)


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
    if not a.any():
        return None
    return a, size / float(upem)


def holes(mask):
    """The enclosed background -- counters, and nothing else."""
    bg = ~mask
    out = np.zeros_like(bg)
    out[0, :] = bg[0, :]
    out[-1, :] = bg[-1, :]
    out[:, 0] = bg[:, 0]
    out[:, -1] = bg[:, -1]
    while True:
        grown = out.copy()
        grown[1:, :] |= out[:-1, :]
        grown[:-1, :] |= out[1:, :]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        grown &= bg
        if (grown == out).all():
            break
        out = grown
    return bg & ~out


def wall(path, xh):
    """The bowl's own wall: the widest disc that fits inside o's ring."""
    r = render(path, "o", xh)
    if r is None:
        return None
    return 2.0 * edt(r[0]).max()


def branch(path, ch, xh):
    """The stroke's thickness along the part that clears the bowl.

    Rows above the counter's top are branch and nothing else, and the widest
    disc fitting in each of those rows is the stroke's thickness where it
    crosses that row -- including at the elbow, where a disc is exactly what
    the eye is reading.
    """
    r = render(path, ch, xh)
    if r is None:
        return None
    mask = r[0]
    h = holes(mask)
    if not h.any():
        return None
    top = np.where(h.any(axis=1))[0].min()          # counter's highest row
    d = edt(mask)
    rows = []
    for y in range(0, top):
        if mask[y].any():
            rows.append(2.0 * d[y].max())
    # the first rows are the terminal's own cut and the last touch the bowl;
    # both are junctions rather than stroke, so the middle is the stroke
    n = len(rows)
    return rows[int(n * 0.12):int(n * 0.88)] if n > 12 else rows


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


def branch_of(mask):
    h = holes(mask)
    if not h.any():
        return None
    top = np.where(h.any(axis=1))[0].min()
    d = edt(mask)
    rows = [2.0 * d[y].max() for y in range(0, top) if mask[y].any()]
    n = len(rows)
    return rows[int(n * 0.12):int(n * 0.88)] if n > 12 else rows


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
