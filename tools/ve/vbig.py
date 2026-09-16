"""Radon's в and ours, large, with each closed contour outlined in red."""
import sys
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.recordingPen import RecordingPen

R = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/MonaspaceRadon-%s_1.otf"
O = "fonts/ttf/SUSEMono-%sItalic.ttf"
FACES = [("Radon light", R % "ExtraLightItalic"),
         ("Radon bold", R % "ExtraBoldItalic"),
         ("ours thin", O % "Thin"),
         ("ours bold", O % "ExtraBold")]
CELL = 420


def main():
    out, x = [], 20
    for label, path in FACES:
        f = TTFont(path, fontNumber=0, lazy=True)
        gs, cm = f.getGlyphSet(), f.getBestCmap()
        s = CELL / f["head"].unitsPerEm
        pen = SVGPathPen(gs)
        gs[cm[ord("в")]].draw(pen)
        g = '<g transform="translate(%.1f,%.1f) scale(%.4f,%.4f)">' % (
            x, 40 + CELL * 1.6, s, -s)
        out.append(g + '<path d="%s" fill="#111" fill-rule="evenodd"/></g>'
                   % pen.getCommands())
        rec = RecordingPen()
        gs[cm[ord("в")]].draw(rec)
        cur = []
        for op, args in rec.value:
            if op == "moveTo" and cur:
                p = SVGPathPen(gs)
                for o2, a2 in cur:
                    getattr(p, o2)(*a2)
                out.append(g + '<path d="%s" fill="none" stroke="#e00" '
                           'stroke-width="%.1f"/></g>'
                           % (p.getCommands(), 6 / s))
                cur = []
            cur.append((op, args))
        f.close()
        out.append('<text x="%d" y="24" font-family="sans-serif" '
                   'font-size="14" fill="#666">%s</text>' % (x, label))
        x += CELL * 0.95
    w, h = x + 20, 40 + CELL * 1.7
    print('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="#fff"/>'
          '%s</svg>' % (w, h, w, h, "".join(out)))
    sys.stderr.write("%d %d\n" % (w, h))


if __name__ == "__main__":
    main()
