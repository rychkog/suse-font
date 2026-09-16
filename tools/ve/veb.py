"""ExtraBold в with an oval pen. Tile: `r,merge,wide,loopwide,sx,sy`."""
import sys
from PIL import Image
from vform import pen_spine
from vpen import ink_oval
from vpen2 import fill_specks
from scipy import ndimage
import numpy as np
import os
EB = os.environ.get("FONT", "fonts/ttf/SUSEMono-ExtraBoldItalic.ttf")
S = ("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
     "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/")
tiles = []
for spec in sys.argv[1:]:
    r, merge, wide, lw, sx, sy, scale, lean = (float(x) for x in spec.split(","))
    p = pen_spine(EB, (sx + sy) / 2.0, lean, r, 0.0, 65.0, 0.0, scale=scale, split=0.6,
                  merge=merge, full=0.65, psi=-40.0, wide=wide, loopwide=lw, roundtop=True)
    import os, math
    cut = float(os.environ.get("TRIM", "0"))
    while cut > 0 and len(p) > 2:
        cut -= math.hypot(p[-1][0] - p[-2][0], p[-1][1] - p[-2][1]); p = p[:-1]
    lf = float(os.environ.get("LOOPPEN", "1"))
    m, k = ink_oval([(p, False)], sx, sy, px=420.0)
    if lf != 1.0:
        i, j = pen_spine.loop
        xs_, ys_ = [q[0] for q in p], [q[1] for q in p]
        box = (min(xs_), min(ys_), max(xs_), max(ys_))
        pad = int(sx * 420.0 / (box[3] - box[1]) / 2.0) + 20
        m1, k = ink_oval([(p[:i + 1], False), (p[j - 1:], False)], sx, sy, 420.0, box, pad)
        m2, _ = ink_oval([(p[i:j], False)], sx * lf, sy * lf, 420.0, box, pad)
        m = m1 | m2
    m = fill_specks(m, k, sy)
    lbl, n = ndimage.label(ndimage.binary_fill_holes(m) & ~m, structure=np.ones((3, 3)))
    areas = sorted(ndimage.sum(np.ones_like(lbl), lbl, range(1, n + 1)) / k / k, reverse=True)
    xs = [q[0] for q in p]
    rows = np.nonzero(m.any(axis=1))[0]; top, bot = rows[0], rows[-1]; h = bot - top
    span = lambda r: (np.nonzero(r)[0][-1] - np.nonzero(r)[0][0]) if r.any() else 0
    lw_ = max(span(m[r]) for r in range(top, top + int(h * 0.30)))
    bw_ = max(span(m[r]) for r in range(bot - int(h * 0.40), bot))
    print("loop/bowl outer %.2f" % (lw_ / bw_), end="  ")
    print("%-32s counters %d  areas %s  ink width %3.0f" % (
        spec, n, " ".join("%5.0f" % a for a in areas), max(xs) - min(xs) + sx))
    tiles.append(Image.fromarray(((~m) * 255).astype("uint8")))
out = Image.new("L", (sum(t.width + 30 for t in tiles), max(t.height for t in tiles)), 255)
x = 0
for t in tiles:
    out.paste(t, (x, 0)); x += t.width + 30
out.save(S + "veb.png")
