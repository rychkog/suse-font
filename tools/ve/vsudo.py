"""Sudo's cursive в beside Radon's and ours. Sudo is variable, so it is drawn
at the two ends of its own weight axis."""
import sys
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.recordingPen import RecordingPen

SUDO = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/Sudo-Italic[YTDE,wght].ttf"
R = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/MonaspaceRadon-%s_1.otf"
O = "fonts/ttf/SUSEMono-%sItalic.ttf"
ROWS = [("Radon light", R % "ExtraLightItalic", None),
        ("Radon bold", R % "ExtraBoldItalic", None),
        ("Sudo 200", SUDO, {"wght": 200}),
        ("Sudo 700", SUDO, {"wght": 700}),
        ("ours thin", O % "Thin", None),
        ("ours bold", O % "ExtraBold", None)]
CELL = 400


def main():
    out, x = [], 20
    for label, path, loc in ROWS:
        f = TTFont(path, fontNumber=0, lazy=True)
        gs = f.getGlyphSet(location=loc) if loc else f.getGlyphSet()
        cm = f.getBestCmap()
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
                           'stroke-width="%.1f"/></g>' % (p.getCommands(), 5 / s))
                cur = []
            cur.append((op, args))
        f.close()
        out.append('<text x="%d" y="24" font-family="sans-serif" font-size="13" '
                   'fill="#666">%s</text>' % (x, label))
        x += CELL * 0.92
    w, h = x + 20, 40 + CELL * 1.7
    print('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="#fff"/>'
          '%s</svg>' % (w, h, w, h, "".join(out)))
    sys.stderr.write("%d %d\n" % (w, h))


if __name__ == "__main__":
    main()
