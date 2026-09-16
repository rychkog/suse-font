"""Where в's two parts sit, left to right, above and below the crossing.
Everything is in x-heights, measured from the letter's own left edge, so the
faces can be compared without their cell widths getting in the way."""
import sys
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from vprofile import flatten, runs

R = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/MonaspaceRadon-%s_1.otf"
O = "fonts/ttf/SUSEMono-%sItalic.ttf"
FACES = [("Radon light", R % "ExtraLightItalic"),
         ("Radon bold", R % "ExtraBoldItalic"),
         ("ours thin", O % "Thin"),
         ("ours bold", O % "ExtraBold")]
BANDS = 80


def main():
    for label, path in FACES:
        f = TTFont(path, fontNumber=0, lazy=True)
        gs, cm = f.getGlyphSet(), f.getBestCmap()
        upem = f["head"].unitsPerEm
        xh = getattr(f["OS/2"], "sxHeight", 0) or 0.5 * upem
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
        one = [p for p in prof
               if p[1] == 1 and y0 + 0.15 * h < p[0] < y0 + 0.85 * h]
        cross = max(one, key=lambda p: p[0])[0]
        up = [p for p in prof if p[0] > cross]
        dn = [p for p in prof if p[0] < cross]
        u = (min(p[2] for p in up), max(p[3] for p in up))
        d = (min(p[2] for p in dn), max(p[3] for p in dn))
        # where the crossing sits across the letter, and the bowl's own
        # widest band -- the one that says how low and how right it sits
        cb = [p for p in prof if abs(p[0] - cross) < h / BANDS][0]
        fat = max(dn, key=lambda p: p[3] - p[2])
        print("\n%-12s  letter %.2f xh wide, %.2f tall" % (label, (x1 - x0) / xh, h / xh))
        print("  crossing at %.2f of the height, %.2f xh across from the left"
              % ((cross - y0) / h, (cb[2] - x0) / xh))
        print("  loop  x %.2f .. %.2f xh   (%.2f wide)"
              % ((u[0] - x0) / xh, (u[1] - x0) / xh, (u[1] - u[0]) / xh))
        print("  bowl  x %.2f .. %.2f xh   (%.2f wide)"
              % ((d[0] - x0) / xh, (d[1] - x0) / xh, (d[1] - d[0]) / xh))
        print("  bowl widest at %.2f of the height, x %.2f .. %.2f xh"
              % ((fat[0] - y0) / h, (fat[2] - x0) / xh, (fat[3] - x0) / xh))
        f.close()


if __name__ == "__main__":
    main()
