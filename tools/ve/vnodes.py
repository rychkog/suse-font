"""Radon's в with its on-curve nodes numbered, so the bowl's mouth can be
NAMED rather than searched for -- the reason `cut_at_y` gives."""
import sys
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
from donor import segments_of, find
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

F = "MonaspaceRadon-ExtraLightItalic_1.otf"
CELL = 620


def main():
    path = find(F)
    segs, deg = segments_of(path, ord("в"))
    f = TTFont(path, fontNumber=0, lazy=True)
    gs, cm = f.getGlyphSet(), f.getBestCmap()
    upem = f["head"].unitsPerEm
    pen = SVGPathPen(gs)
    gs[cm[ord("в")]].draw(pen)
    d = pen.getCommands()
    f.close()

    xs = [p[0] for c in segs for _k, ps in c for p in ps]
    ys = [p[1] for c in segs for _k, ps in c for p in ps]
    s = CELL / (max(ys) - min(ys))
    ox, oy = 60 - min(xs) * s, 40 + (max(ys)) * s

    out = ['<g transform="translate(%.1f,%.1f) scale(%.4f,%.4f)">'
           '<path d="%s" fill="#ddd" stroke="#999" stroke-width="%.1f"/></g>'
           % (ox, oy, s, -s, d, 2 / s)]
    for ci, c in enumerate(segs):
        for i, (kind, ps) in enumerate(c):
            x, y = ps[-1]
            px, py = ox + x * s, oy - y * s
            out.append('<circle cx="%.1f" cy="%.1f" r="4" fill="%s"/>'
                       % (px, py, "#e00" if ci == 0 else "#06c"))
            out.append('<text x="%.1f" y="%.1f" font-family="sans-serif" '
                       'font-size="13" fill="%s">%d</text>'
                       % (px + 6, py - 5, "#e00" if ci == 0 else "#06c", i))
    w = 60 + (max(xs) - min(xs)) * s + 120
    h = 40 + (max(ys) - min(ys)) * s + 60
    print('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="#fff"/>'
          '%s</svg>' % (w, h, w, h, "".join(out)))
    sys.stderr.write("%d %d  contours %s\n"
                     % (w, h, [len(c) for c in segs]))


if __name__ == "__main__":
    main()
