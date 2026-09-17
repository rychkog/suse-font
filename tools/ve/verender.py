"""Radon's в at both our masters, beside the donor and beside what we ship.

The move `d` is not guessed: it is half the difference between the donor's own
o wall, scaled by the same fit, and this face's o wall at that master. So the
letter arrives weighing what o weighs, which is what г was given too.
"""
import sys
sys.path.insert(0, "tools")
from verode import load, move, rejoin, LIGHT, BOLD
from donor import find
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

O = "fonts/ttf/SUSEMono-%sItalic.ttf"
CELL = 420


def o_wall(path):
    """Half the difference between o's box and o's counter -- its side wall."""
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        gs, cm = f.getGlyphSet(), f.getBestCmap()
        from fontTools.pens.recordingPen import RecordingPen
        rec = RecordingPen()
        gs[cm[ord("o") if ord("o") in cm else ord("о")]].draw(rec)
        cs, cur = [], []
        for op, args in rec.value:
            if op == "moveTo" and cur:
                cs.append(cur); cur = []
            cur.append((op, args))
        if cur:
            cs.append(cur)
        boxes = []
        for c in cs:
            bp = BoundsPen(gs)
            for op, args in c:
                getattr(bp, op)(*args)
            if bp.bounds:
                boxes.append(bp.bounds)
        boxes.sort(key=lambda b: b[2] - b[0])
        xh = getattr(f["OS/2"], "sxHeight", 0) or 0.5 * f["head"].unitsPerEm
        return ((boxes[-1][2] - boxes[-1][0]) - (boxes[0][2] - boxes[0][0])) / 2.0, xh
    finally:
        f.close()


def d_of(segs):
    return "".join(
        ("M%.1f %.1f" % ps[0] if kind == "start" else
         ("L%.1f %.1f" % ps[0] if kind == "line" else
          "C%.1f %.1f %.1f %.1f %.1f %.1f"
          % (ps[0][0], ps[0][1], ps[1][0], ps[1][1], ps[2][0], ps[2][1])))
        for c in segs for kind, ps in c) + "Z"


def main():
    out, x = [], 20
    for label, w, tall in (("ours thin", "Thin", 1.57), ("ours bold", "ExtraBold", 1.50)):
        f = TTFont(O % w, lazy=True)
        gs, cm = f.getGlyphSet(), f.getBestCmap()
        pen = SVGPathPen(gs)
        gs[cm[ord("в")]].draw(pen)
        s = CELL / (tall * f["OS/2"].sxHeight)
        out.append('<text x="%d" y="24" font-family="sans-serif" font-size="13" '
                   'fill="#666">%s</text>' % (x, label))
        out.append('<g transform="translate(%.1f,%.1f) scale(%.4f,%.4f)">'
                   '<path d="%s" fill="#111" fill-rule="evenodd"/></g>'
                   % (x, 40 + CELL * 1.15, s, -s, pen.getCommands()))
        f.close()
        x += CELL * 0.80

    for label, which, ours, tall in (
            ("Radon light, tail off", LIGHT, None, 1.57),
            ("-> our Thin", LIGHT, "Thin", 1.57),
            ("-> our ExtraBold", BOLD, "ExtraBold", 1.50)):
        f = TTFont(O % (ours or "Thin"), lazy=True)
        xh = f["OS/2"].sxHeight
        f.close()
        height = tall * xh
        segs, k = load(height, which)
        d = 0.0
        if ours:
            dw, dxh = o_wall(find(which.replace("%s", "")))
            mine, _ = o_wall(O % ours)
            d = (dw * k - mine) / 2.0
        moved = [move(c, d) for c in segs]
        if ours:
            moved = [rejoin(moved[0])] + moved[1:]
        s = CELL / height
        out.append('<text x="%d" y="24" font-family="sans-serif" font-size="12" '
                   'fill="#666">%s%s</text>'
                   % (x, label, "" if not ours else "  (d=%+.0f)" % d))
        out.append('<g transform="translate(%.1f,%.1f) scale(%.4f,%.4f)">'
                   '<path d="%s" fill="#111" fill-rule="nonzero"/></g>'
                   % (x, 40 + CELL * 1.15, s, -s, d_of(moved)))
        x += CELL * 0.80
    w, h = x + 20, 40 + CELL * 1.25
    print('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="#fff"/>'
          '%s</svg>' % (w, h, w, h, "".join(out)))
    sys.stderr.write("%d %d\n" % (w, h))


if __name__ == "__main__":
    main()
