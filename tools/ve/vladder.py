"""One change at a time, so the step that breaks the letter is visible."""
import sys
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
from verode import load, move, close_bowl, rejoin, LIGHT
from verender import d_of

CELL = 400


def main():
    out, x = [], 20
    steps = [("Radon, as drawn", False, 0.0, False),
             ("tail off", True, 0.0, False),
             ("tail off, eroded", True, 16.0, False),
             ("and rejoined", True, 16.0, True)]
    for label, tail, d, bridge in steps:
        segs, k = load(740.0, LIGHT, tail)
        segs = [move(c, d) for c in segs]
        if bridge:
            segs = [rejoin(segs[0])] + segs[1:]
        s = CELL / 740.0
        out.append('<text x="%d" y="24" font-family="sans-serif" font-size="13" '
                   'fill="#666">%s</text>' % (x, label))
        out.append('<g transform="translate(%.1f,%.1f) scale(%.4f,%.4f)">'
                   '<path d="%s" fill="#111" fill-rule="nonzero"/></g>'
                   % (x, 40 + CELL * 1.10, s, -s, d_of(segs)))
        x += CELL * 0.82
    w, h = x + 20, 40 + CELL * 1.2
    print('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
          'viewBox="0 0 %d %d"><rect width="100%%" height="100%%" fill="#fff"/>'
          '%s</svg>' % (w, h, w, h, "".join(out)))
    sys.stderr.write("%d %d\n" % (w, h))


if __name__ == "__main__":
    main()
