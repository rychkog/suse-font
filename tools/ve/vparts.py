"""в's parts, separated by ink RUN rather than by contour.

Below the crossing a scanline crosses two strokes: the loop's descending
stroke on the left and the bowl's right wall on the right, with the bowl's
own counter between them. So the bowl is the white between run 1 and run 2,
and the loop's stroke is run 1. Above the crossing the same two runs are the
loop's own walls and the white between them is the eye. Reading the bbox
above and below the crossing instead -- which is what the first pass did --
credits the loop's descending stroke to the bowl and gets the letter
backwards."""
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
BANDS = 120


def main():
    for label, path in FACES:
        f = TTFont(path, fontNumber=0, lazy=True)
        gs, cm = f.getGlyphSet(), f.getBestCmap()
        polys = flatten(gs, cm[ord("в")])
        bp = BoundsPen(gs)
        gs[cm[ord("в")]].draw(bp)
        x0, y0, x1, y1 = bp.bounds
        h, wd = y1 - y0, x1 - x0
        rel = lambda v: (v - x0) / wd
        prof = [(y0 + h * (i + 0.5) / BANDS,
                 runs(polys, y0 + h * (i + 0.5) / BANDS))
                for i in range(BANDS)]
        prof = [(y, r) for y, r in prof if r]
        # the crossing: the lowest band, above the letter's own middle, whose
        # white is one piece -- below it the bowl's counter has split off
        two = [(y, r) for y, r in prof if len(r) >= 2]
        cross = None
        for y, r in two:
            if y > y0 + 0.30 * h and len(r) == 1:
                continue
        merged = [y for y, r in prof if len(r) == 1 and y > y0 + 0.25 * h]
        cross = max(merged) if merged else None
        eye = [(y, r) for y, r in two if cross and y > cross]
        blw = [(y, r) for y, r in two if cross and y < cross]
        print("\n%-12s  crossing at %.2f of the height" %
              (label, (cross - y0) / h if cross else -1))
        if eye:
            ys = max(eye, key=lambda t: t[1][1][0] - t[1][0][1])
            print("  eye     widest %.2f of the letter, at %.2f of the height"
                  % (rel(ys[1][1][0]) - rel(ys[1][0][1]), (ys[0] - y0) / h))
            print("  loop    walls span %.2f .. %.2f of the letter"
                  % (rel(min(r[0][0] for _, r in eye)),
                     rel(max(r[-1][1] for _, r in eye))))
        if blw:
            ys = max(blw, key=lambda t: t[1][1][0] - t[1][0][1])
            print("  bowl    counter %.2f wide at %.2f of the height, "
                  "running %.2f .. %.2f of the letter"
                  % (rel(ys[1][1][0]) - rel(ys[1][0][1]), (ys[0] - y0) / h,
                     rel(ys[1][0][1]), rel(ys[1][1][0])))
            print("  bowl    outer edge reaches %.2f of the letter"
                  % rel(max(r[-1][1] for _, r in blw)))
            print("  descend stroke sits at %.2f .. %.2f of the letter"
                  % (rel(min(r[0][0] for _, r in blw)),
                     rel(max(r[0][1] for _, r in blw))))
        f.close()


if __name__ == "__main__":
    main()
