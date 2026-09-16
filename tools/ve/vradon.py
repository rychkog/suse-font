"""Radon's italic в beside ours. A probe: labels are live text, not outlines."""
import sys
sys.path.insert(0, "tools")
from svgsheet import Face

R = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/MonaspaceRadon-%s.otf"
O = "fonts/ttf/SUSEMono-%sItalic.ttf"

ROWS = [("Radon light", R % "ExtraLightItalic"),
        ("Radon reg", R % "Italic"),
        ("Radon bold", R % "ExtraBoldItalic"),
        ("ours thin", O % "Thin"),
        ("ours reg", O % "Regular"),
        ("ours bold", O % "ExtraBold")]

CH = "вbоаь"
CELL, GAP, LAB = 150, 16, 90


def main():
    out, y = [], GAP
    for name, path in ROWS:
        f = Face(path)
        s = CELL / f.upem
        out.append('<text x="4" y="%.1f" font-family="sans-serif" '
                   'font-size="13" fill="#666">%s</text>' % (y + CELL * 0.8, name))
        x = LAB
        for ch in CH:
            if f.has(ch):
                out.append(
                    '<g transform="translate(%.1f,%.1f) scale(%.4f,%.4f)">'
                    '<path d="%s" fill="#111" fill-rule="evenodd"/></g>'
                    % (x, y + CELL, s, -s, f.d(ch)))
            x += CELL * 0.72
        f.close()
        y += CELL * 1.22
    w, h = LAB + CELL * 0.72 * len(CH) + GAP, y + GAP
    print('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="#fff"/>'
          '%s</svg>' % (w, h, w, h, "".join(out)))
    sys.stderr.write("%d %d\n" % (w, h))


if __name__ == "__main__":
    main()
