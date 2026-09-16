"""What Radon's в is made of, against ours. Structure first, size second."""
import sys
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen

R = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/MonaspaceRadon-%s.otf"
O = "fonts/ttf/SUSEMono-%sItalic.ttf"

FACES = [("Radon light", R % "ExtraLightItalic"),
         ("Radon bold", R % "ExtraBoldItalic"),
         ("ours thin", O % "Thin"),
         ("ours bold", O % "ExtraBold")]


def contours(gs, name):
    """Each closed contour as its own bounds and area, in em units."""
    rec = RecordingPen()
    gs[name].draw(rec)
    out, cur = [], []
    for op, args in rec.value:
        if op == "moveTo" and cur:
            out.append(cur)
            cur = []
        cur.append((op, args))
    if cur:
        out.append(cur)
    res = []
    for c in out:
        bp, ap = BoundsPen(gs), AreaPen(gs)
        for op, args in c:
            getattr(bp, op)(*args)
            getattr(ap, op)(*args)
        if bp.bounds:
            res.append((bp.bounds, ap.value))
    return res


def main():
    for label, path in FACES:
        f = TTFont(path, fontNumber=0, lazy=True)
        cm, gs = f.getBestCmap(), f.getGlyphSet()
        upem = f["head"].unitsPerEm
        xh = getattr(f["OS/2"], "sxHeight", 0) or 0.5 * upem
        asc = getattr(f["OS/2"], "sCapHeight", 0) or 0.7 * upem
        have = "".join(c for c in "вbоаь" if ord(c) in cm)
        print("\n%-12s upem %d  xh %d  cap %d  has: %s"
              % (label, upem, xh, asc, have))
        for ch in "вo":
            if ord(ch) not in cm:
                continue
            cs = contours(gs, cm[ord(ch)])
            gb = (min(b[0] for b, _ in cs), min(b[1] for b, _ in cs),
                  max(b[2] for b, _ in cs), max(b[3] for b, _ in cs))
            print("  %s  contours %d   box w %.2f xh  h %.2f xh  top %.2f xh"
                  % (ch, len(cs), (gb[2] - gb[0]) / xh,
                     (gb[3] - gb[1]) / xh, gb[3] / xh))
            for b, a in sorted(cs, key=lambda t: -abs(t[1])):
                print("     part w %.2f xh  h %.2f xh  y %.2f..%.2f  %s"
                      % ((b[2] - b[0]) / xh, (b[3] - b[1]) / xh,
                         b[1] / xh, b[3] / xh,
                         "outer" if a < 0 else "counter"))
        f.close()


if __name__ == "__main__":
    main()
