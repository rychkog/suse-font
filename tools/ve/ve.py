"""Which italics draw в as the cursive two-loop form, and in what proportions.

The upright в is a stem with two lobes hung to its right; the cursive в is a
bowl with a leaning loop stacked on it. Both enclose two counters, so the
count says nothing. What tells them apart is the UPPER counter: a lobe is
short and round, a loop is tall, narrow and leans.
"""
import sys, os, glob, math
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from panel import font_dirs

STEPS = 6


class Flat(BasePen):
    def __init__(self, gs):
        BasePen.__init__(self, gs)
        self.polys, self.cur = [], []

    def _moveTo(self, pt):
        self.cur = [pt]

    def _lineTo(self, pt):
        self.cur.append(pt)

    def _curveToOne(self, c1, c2, pt):
        x0, y0 = self.cur[-1]
        for s in range(1, STEPS + 1):
            u = s / float(STEPS); v = 1 - u
            self.cur.append(
                (v**3*x0 + 3*v*v*u*c1[0] + 3*v*u*u*c2[0] + u**3*pt[0],
                 v**3*y0 + 3*v*v*u*c1[1] + 3*v*u*u*c2[1] + u**3*pt[1]))

    def _closePath(self):
        if len(self.cur) > 2:
            self.polys.append(self.cur)
        self.cur = []

    _endPath = _closePath


def draw(gs, name):
    pen = Flat(gs)
    gs[name].draw(pen)
    return pen.polys


def area(poly):
    s = 0.0
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


rows, seen = [], set()
for d in font_dirs():
    for path in sorted(glob.glob(os.path.join(d, "*.ttf"))
                       + glob.glob(os.path.join(d, "*.otf"))):
        if "suse" in os.path.basename(path).lower():
            continue
        try:
            f = TTFont(path, fontNumber=0, lazy=True)
            name = f["name"].getDebugName(4) or ""
            low = name.lower()
            if ("italic" not in low and "oblique" not in low) or name in seen:
                f.close(); continue
            cmap = f.getBestCmap()
            if not {0x0432, ord("n")} <= set(cmap):
                f.close(); continue
            gs = f.getGlyphSet()
            nn = draw(gs, cmap[ord("n")])
            xh = max(p[1] for poly in nn for p in poly)
            polys = draw(gs, cmap[0x0432])
            if len(polys) < 2:
                f.close(); continue
            outer = max(polys, key=lambda p: abs(area(p)))
            holes = [p for p in polys if p is not outer]
            if not holes:
                f.close(); continue
            # the upper counter
            up = max(holes, key=lambda p: sum(y for _, y in p) / len(p))
            xs = [x for x, _ in up]; ys = [y for _, y in up]
            hi, wi = max(ys) - min(ys), max(xs) - min(xs)
            top = [x for x, y in up if y > max(ys) - hi * 0.25]
            bot = [x for x, y in up if y < min(ys) + hi * 0.25]
            lean = ((sum(top) / len(top) - sum(bot) / len(bot)) / hi
                    if top and bot and hi else 0.0)
            rows.append((hi / wi if wi else 0.0, lean, hi / xh, len(holes),
                         name))
            seen.add(name)
            f.close()
        except Exception:
            pass

rows.sort()
print("  %-34s %6s %6s %6s %4s"
      % ("italic face", "tall/wide", "lean", "of xh", "n"))
for asp, lean, h, nh, name in rows:
    print("  %-34s %6.2f %6.2f %6.2f %4d" % (name[:34], asp, lean, h, nh))
print("\n  %d faces" % len(rows))
