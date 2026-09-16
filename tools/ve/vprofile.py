"""в read as an ink profile: where the loop is, where the bowl is, and the
height where the two meet. Radon draws it as ONE contour, so parts cannot be
separated by contour -- they are separated by how many runs of ink a scanline
crosses."""
import sys
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen

R = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/MonaspaceRadon-%s_1.otf"
O = "fonts/ttf/SUSEMono-%sItalic.ttf"
FACES = [("Radon light", R % "ExtraLightItalic"),
         ("Radon reg", R % "Italic"),
         ("Radon bold", R % "ExtraBoldItalic"),
         ("ours thin", O % "Thin"),
         ("ours reg", O % "RegularItalic".replace("Italic", "")),
         ("ours bold", O % "ExtraBold")]
BANDS = 60


def flatten(gs, name, steps=24):
    """Every contour as a closed polyline. Cheap and good enough for runs."""
    rec = RecordingPen()
    gs[name].draw(rec)
    polys, cur, start = [], [], None
    for op, args in rec.value:
        if op == "moveTo":
            if cur:
                polys.append(cur)
            start = args[0]
            cur = [start]
        elif op == "lineTo":
            cur.append(args[0])
        elif op in ("curveTo", "qCurveTo"):
            p0 = cur[-1]
            pts = [p for p in args if p is not None]
            for i in range(1, steps + 1):
                t = i / steps
                if op == "curveTo" and len(pts) == 3:
                    a, b, c = pts
                    u = 1 - t
                    cur.append((u**3 * p0[0] + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*c[0],
                                u**3 * p0[1] + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*c[1]))
                else:
                    a = pts[0]
                    c = pts[-1]
                    u = 1 - t
                    cur.append((u*u*p0[0] + 2*u*t*a[0] + t*t*c[0],
                                u*u*p0[1] + 2*u*t*a[1] + t*t*c[1]))
        elif op == "closePath" and cur:
            polys.append(cur)
            cur = []
    if cur:
        polys.append(cur)
    return polys


def runs(polys, y):
    """The x spans of ink on the scanline y, by even-odd crossings."""
    xs = []
    for p in polys:
        n = len(p)
        for i in range(n):
            (x0, y0), (x1, y1) = p[i], p[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    xs.sort()
    return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]


def main():
    for label, path in FACES:
        f = TTFont(path, fontNumber=0, lazy=True)
        gs, cm = f.getGlyphSet(), f.getBestCmap()
        upem = f["head"].unitsPerEm
        xh = getattr(f["OS/2"], "sxHeight", 0) or 0.5 * upem
        adv = f["hmtx"][cm[ord("в")]][0]
        polys = flatten(gs, cm[ord("в")])
        bp = BoundsPen(gs)
        gs[cm[ord("в")]].draw(bp)
        x0, y0, x1, y1 = bp.bounds
        h = y1 - y0
        prof = []
        for i in range(BANDS):
            y = y0 + h * (i + 0.5) / BANDS
            rs = runs(polys, y)
            if rs:
                prof.append((y, len(rs), min(r[0] for r in rs),
                             max(r[1] for r in rs)))
        # the crossing: the highest band below the top third that is one run
        one = [p for p in prof if p[1] == 1]
        mid = [p for p in one if y0 + 0.15 * h < p[0] < y0 + 0.85 * h]
        cross = max(mid, key=lambda p: p[0])[0] if mid else None
        wide_up = max((p[3] - p[2] for p in prof if cross and p[0] > cross),
                      default=0)
        wide_dn = max((p[3] - p[2] for p in prof if cross and p[0] < cross),
                      default=0)
        two = [p for p in prof if p[1] >= 2]
        two_below = [p for p in two if cross and p[0] < cross]
        print("\n%-12s adv %d (%.2f em)  box w %.2f xh  h %.2f xh  "
              "overhang %+d" % (label, adv, adv / upem, (x1 - x0) / xh,
                                h / xh, int(max(0, x1 - adv) + max(0, -x0))))
        if cross:
            print("  crossing at %.2f of the letter's height" % ((cross - y0) / h))
            print("  loop above %.2f xh wide   bowl below %.2f xh wide   "
                  "ratio %.2f" % (wide_up / xh, wide_dn / xh,
                                  wide_up / wide_dn if wide_dn else 0))
        print("  bands with 2+ ink runs: %d of %d, %d of them below the "
              "crossing" % (len(two), len(prof), len(two_below)))
        f.close()


if __name__ == "__main__":
    main()
