"""Scanline measurement of built fonts, and the panel comparison that goes with it.

Everything in tools/ above this measures the SOURCE, one master at a time.
This measures BUILT fonts -- ours and the panel's -- through the same lens, so
a reading of ours and a reading of theirs are the same quantity.

A horizontal cut through a glyph gives alternating ink and white runs, and for
most letters that is the whole measurement. ф and Ф at the bowl's middle give
wall / counter / stem / counter / wall in one go; Ж gives arm / stem / arm; Ы
gives bowl and stem. `vruns` does the same vertically, which is how a counter's
height (and so its roundness) is read.

Two rules this file exists to make cheap, both learned the hard way -- see
docs/METHOD.md:

  * Bucket the panel by WEIGHT before believing a median. A median taken over
    every face at once averages light and heavy cuts together and hides any
    relation that moves with weight. `compare` brackets against the faces
    nearest in stem weight instead, which has no bands to fall between.

  * Check the probe before believing the finding. `runs` flattens curves
    properly; taking control points as vertices (which check.py did until it
    was fixed) puts the polygon outside the true outline and can miss a
    counter crossing the scanline entirely.
"""

import statistics as st
import sys

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])

STEPS = 24


def contours(f, ch, cm=None, gs=None):
    """Flattened closed contours for a character, in font units."""
    cm = cm if cm is not None else f.getBestCmap()
    gs = gs if gs is not None else f.getGlyphSet()
    name = cm.get(ord(ch)) if len(ch) == 1 else ch
    if name is None or name not in gs:
        return None
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    out, cur = [], []
    for op, a in pen.value:
        if op == "moveTo":
            cur = [a[0]]
        elif op == "lineTo":
            cur.append(a[0])
        elif op == "curveTo":
            p0 = cur[-1]
            c1, c2, p3 = a
            for k in range(1, STEPS + 1):
                t = k / float(STEPS)
                u = 1.0 - t
                cur.append((u**3 * p0[0] + 3*u*u*t * c1[0]
                            + 3*u*t*t * c2[0] + t**3 * p3[0],
                            u**3 * p0[1] + 3*u*u*t * c1[1]
                            + 3*u*t*t * c2[1] + t**3 * p3[1]))
        elif op == "qCurveTo":
            p0 = cur[-1]
            pts = list(a)
            on = pts[-1]
            offs = pts[:-1]
            if on is None:
                on = offs[0]
            for i, c in enumerate(offs):
                end = on if i == len(offs) - 1 else (
                    (c[0] + offs[i + 1][0]) / 2.0,
                    (c[1] + offs[i + 1][1]) / 2.0)
                for k in range(1, STEPS + 1):
                    t = k / float(STEPS)
                    u = 1.0 - t
                    cur.append((u*u * p0[0] + 2*u*t * c[0] + t*t * end[0],
                                u*u * p0[1] + 2*u*t * c[1] + t*t * end[1]))
                p0 = end
        elif op == "closePath" and cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def runs(ps, y):
    """Ink runs [(x0, x1), ...] where a horizontal line at y is inside."""
    if not ps:
        return []
    xs = []
    for poly in ps:
        for i in range(len(poly)):
            (x1, y1) = poly[i]
            (x2, y2) = poly[(i + 1) % len(poly)]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def gaps(r):
    """The white runs between ink runs -- counters, joins, clear space."""
    return [(r[i][1], r[i + 1][0]) for i in range(len(r) - 1)]


def vruns(ps, x):
    """Ink runs along a VERTICAL line at x -> [(y0, y1), ...]."""
    if not ps:
        return []
    return runs([[(y, xx) for xx, y in poly] for poly in ps], x)


def stem_of(f, cm=None, gs=None):
    """The face's own stem, read off H clear of its crossbar.

    Scanning at mid cap height cuts the bar and reads ONE run instead of two,
    which silently drops the face from a panel sweep. Take it well clear.
    """
    cm = cm if cm is not None else f.getBestCmap()
    gs = gs if gs is not None else f.getGlyphSet()
    cap = getattr(f["OS/2"], "sCapHeight", 0) or 0.7 * f["head"].unitsPerEm
    ps = contours(f, "H", cm, gs)
    for frac in (0.82, 0.18, 0.88):
        r = runs(ps, cap * frac)
        if len(r) == 2:
            return r[0][1] - r[0][0]
    return None


def lc_stem_of(f, cm=None, gs=None):
    """The face's own LOWERCASE stem, read off n.

    Measure a lowercase against this and never against `stem_of`. This face
    draws n at 0.93 of H where the panel's median is 0.98, so a lowercase
    relation divided by the capital stem reads about six per cent low in every
    face -- which is the whole of a "the bowl is lighter than the stem"
    finding that turned out to be the probe talking. o's wall is exactly this
    figure at all four weights.
    """
    cm = cm if cm is not None else f.getBestCmap()
    gs = gs if gs is not None else f.getGlyphSet()
    xh = getattr(f["OS/2"], "sxHeight", 0)
    if not xh:
        return None
    ps = contours(f, "n", cm, gs)
    if not ps:
        return None
    for frac in (0.35, 0.25, 0.45):
        r = runs(ps, xh * frac)
        if len(r) == 2:
            return r[0][1] - r[0][0]
    return None


def widest_run_set(f, ch, ref, n, cm=None, gs=None):
    """The scanline through `ch` giving exactly n ink runs at its widest.

    Sweeping the height rather than fixing it is what makes one probe work
    across sixty designs: the bowl's middle is not at the same fraction of the
    x-height in every face.
    """
    ps = contours(f, ch, cm, gs)
    if not ps:
        return None
    best = None
    for k in range(25, 76):
        r = runs(ps, ref * k / 100.0)
        if len(r) == n:
            w = r[-1][1] - r[0][0]
            if best is None or w > best[1]:
                best = (r, w, ref * k / 100.0)
    return best


def panel(measure):
    """Run `measure(TTFont) -> value|None` over every panel face.

    Returns [(stem_over_em, value), ...]. Opens one font at a time and closes
    it: this machine is memory-constrained and sixty open TTFonts will not fit.
    """
    from panel import families
    out = []
    for _fam, path in families():
        f = TTFont(path, fontNumber=0, lazy=True)
        try:
            s = stem_of(f)
            if s is None:
                continue
            v = measure(f)
            if v is not None:
                out.append((s / f["head"].unitsPerEm, v))
        except Exception:
            pass
        finally:
            f.close()
    return out


def compare(pts, stem, value, k=11):
    """Bracket `value` against the k panel faces nearest in stem weight.

    Nearest-neighbour rather than weight BANDS: a band puts a face at its own
    edge next to faces two steps away, and this face's Regular reads as
    'light' against cuts far lighter than it. Returns (median, lo, hi, inside).
    """
    nb = sorted(pts, key=lambda p: abs(p[0] - stem))[:k]
    v = sorted(x[1] for x in nb)
    if len(v) < 4:
        return None
    lo, hi = v[1], v[-2]
    return st.median(v), lo, hi, lo <= value <= hi


def fit(pts):
    """Least squares of value against stem/em -> (base, slope).

    Prefer a relation LINEAR in the stem. The two masters interpolate
    linearly, so a straight line is reproduced exactly at Regular and Bold
    while a curve is not. And clamp the result: this face draws Thin at 0.029
    of the em, off the bottom of the panel data every such line is fitted to.
    """
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    den = sum((p[0] - mx) ** 2 for p in pts)
    b = sum((p[0] - mx) * (p[1] - my) for p in pts) / den
    return my - b * mx, b
