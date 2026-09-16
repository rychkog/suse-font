"""The cursive в, measured on the two faces that draw it."""
import sys, os, glob, math
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from panel import font_dirs

WANT = ["Monaspace Radon Italic", "Monaspace Radon Bold Italic",
        "Victor Mono Italic", "Victor Mono Bold Italic"]
STEPS = 8


class Flat(BasePen):
    def __init__(self, gs):
        BasePen.__init__(self, gs); self.polys, self.cur = [], []
    def _moveTo(self, pt): self.cur = [pt]
    def _lineTo(self, pt): self.cur.append(pt)
    def _curveToOne(self, c1, c2, pt):
        x0, y0 = self.cur[-1]
        for s in range(1, STEPS + 1):
            u = s / float(STEPS); v = 1 - u
            self.cur.append(
                (v**3*x0 + 3*v*v*u*c1[0] + 3*v*u*u*c2[0] + u**3*pt[0],
                 v**3*y0 + 3*v*v*u*c1[1] + 3*v*u*u*c2[1] + u**3*pt[1]))
    def _closePath(self):
        if len(self.cur) > 2: self.polys.append(self.cur)
        self.cur = []
    _endPath = _closePath


def draw(gs, n):
    pen = Flat(gs); gs[n].draw(pen); return pen.polys


def spans(polys, y):
    xs = []
    for poly in polys:
        m = len(poly)
        for i in range(m):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % m]
            if (y1 - y) * (y2 - y) < 0:
                xs.append((x1 + (x2 - x1) * (y - y1) / (y2 - y1),
                           1 if y2 > y1 else -1))
    xs.sort()
    out, wind, st = [], 0, None
    for x, d in xs:
        if wind == 0:
            st = x
        wind += d
        if wind == 0 and st is not None:
            out.append((st, x))
    return out


found = {}
for d in font_dirs():
    for p in sorted(glob.glob(os.path.join(d, "*.ttf"))
                    + glob.glob(os.path.join(d, "*.otf"))):
        try:
            f = TTFont(p, fontNumber=0, lazy=True)
            n = f["name"].getDebugName(4) or ""
            if n in WANT and n not in found and 0x0432 in f.getBestCmap():
                found[n] = p
            f.close()
        except Exception:
            pass

for n in WANT:
    if n not in found:
        continue
    f = TTFont(found[n], fontNumber=0, lazy=True)
    cmap, gs, upm = f.getBestCmap(), f.getGlyphSet(), f["head"].unitsPerEm
    k = 1000.0 / upm
    nn, ve, oo = draw(gs, cmap[ord("n")]), draw(gs, cmap[0x0432]), \
        draw(gs, cmap[ord("o")])
    xh = max(p[1] for poly in nn for p in poly)
    top = max(p[1] for poly in ve for p in poly)
    xs = [x for poly in ve for x, _ in poly]
    ow = max(x for poly in oo for x, _ in poly) - \
        min(x for poly in oo for x, _ in poly)
    print("== %s ==" % n)
    print("   в reaches %.2f of the x-height, %.2f of o's width wide"
          % (top / xh, (max(xs) - min(xs)) / ow))
    # where the two shapes meet: the height at which the ink is one run and
    # narrowest, between the loop above and the bowl below
    best = None
    for i in range(20, 85):
        y = top * i / 100.0
        iv = spans(ve, y)
        if len(iv) == 1:
            w = iv[0][1] - iv[0][0]
            if best is None or w < best[1]:
                best = (y, w)
    if best:
        print("   they meet at %.2f of the letter's height, %.2f of o's width"
              % (best[0] / top, best[1] / ow))
    for frac in (0.95, 0.80, 0.65, 0.50, 0.35, 0.20, 0.08):
        iv = spans(ve, top * frac)
        print("      %.2f up: %s" % (frac, "  ".join(
            "%.0f-%.0f" % (a * k, b * k) for a, b in iv)))
    f.close()
