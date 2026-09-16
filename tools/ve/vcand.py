"""The candidate donors for в, on the four things that decide one.

Format, because a TrueType donor arrives as quadratics and expands to a node
every few units (METHOD F15). Node count, for the same reason. Whether the
bowl closes, because the user asked for closed. And the weight range, because
a donor whose lightest is heavier than our Thin cannot be blended, only
extrapolated.
"""
import glob, sys
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from panel import font_dirs


def look(path, label):
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        cm = f.getBestCmap()
        if ord("в") not in cm:
            return
        upem = f["head"].unitsPerEm
        xh = getattr(f["OS/2"], "sxHeight", 0) or 0.5 * upem
        gs = f.getGlyphSet()
        rec = RecordingPen()
        gs[cm[ord("в")]].draw(rec)
        ncontour = sum(1 for op, _ in rec.value if op == "moveTo")
        nnode = sum(1 for op, _ in rec.value if op in ("lineTo", "curveTo", "qCurveTo"))
        kind = "CFF " if "CFF " in f else "glyf"
        var = "variable" if "fvar" in f else "static  "
        b = {}
        for c in "во":
            bp = BoundsPen(gs)
            gs[cm[ord(c)]].draw(bp)
            b[c] = bp.bounds
        wall = (b["о"][2] - b["о"][0]) / xh
        print("  %-30s %s %s  contours %d  nodes %3d   "
              "в %.2f xh   o box %.2f xh"
              % (label[:30], kind, var, ncontour, nnode,
                 (b["в"][3] - b["в"][1]) / xh, wall))
    finally:
        f.close()


def main():
    want = ("MonaspaceRadon-ExtraLightItalic_1", "MonaspaceRadon-ExtraBoldItalic_1",
            "SudoVar-Italic", "Sudo-Italic", "consolai", "consolaz")
    print("candidate donors for the cursive в:")
    for d in font_dirs():
        for p in sorted(glob.glob(d + "/*.ttf") + glob.glob(d + "/*.otf")):
            base = p.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if any(w.lower() == base.lower() for w in want):
                look(p, base)
    print("\nand this face's own o wall, for the light end:")
    for w in ("Thin", "ExtraBold"):
        f = TTFont("fonts/ttf/SUSEMono-%sItalic.ttf" % w, lazy=True)
        cm, gs = f.getBestCmap(), f.getGlyphSet()
        xh = f["OS/2"].sxHeight
        bo = BoundsPen(gs); gs[cm[ord("o")]].draw(bo)
        print("  SUSE Mono %-10s o box %.2f xh" % (w, (bo.bounds[2] - bo.bounds[0]) / xh))
        f.close()


if __name__ == "__main__":
    main()
