"""The evened letter, drawn from the moved samples."""
import sys
sys.path.insert(0, "tools")
from verode import load, rejoin, _flat, LIGHT, BOLD
from veven import even

CELL = 420


def poly_d(polys):
    out = []
    for p in polys:
        out.append("M%.1f %.1f" % p[0])
        out += ["L%.1f %.1f" % q for q in p[1:]]
        out.append("Z")
    return "".join(out)


def main():
    out, x = [], 20
    cols = [("donor, rejoined", LIGHT, 740.0, None),
            ("evened to 26", LIGHT, 740.0, 26.0),
            ("bold donor", BOLD, 730.0, None),
            ("evened to 132", BOLD, 730.0, 132.0)]
    for label, which, h, t in cols:
        segs, _k = load(h, which)
        segs = [rejoin(segs[0])] + segs[1:]
        polys = [_flat(c, 32) for c in segs] if t is None else even(segs, t)
        s = CELL / h
        out.append('<text x="%d" y="24" font-family="sans-serif" font-size="13" '
                   'fill="#666">%s</text>' % (x, label))
        out.append('<g transform="translate(%.1f,%.1f) scale(%.4f,%.4f)">'
                   '<path d="%s" fill="#111" fill-rule="evenodd"/></g>'
                   % (x, 40 + CELL * 1.10, s, -s, poly_d(polys)))
        x += CELL * 0.82
    w, hh = x + 20, 40 + CELL * 1.2
    print('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="#fff"/>'
          '%s</svg>' % (w, hh, w, hh, "".join(out)))
    sys.stderr.write("%d %d\n" % (w, hh))


if __name__ == "__main__":
    main()
