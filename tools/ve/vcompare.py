"""Thin в: the closure three ways, side by side, in company, as outlines."""
import sys
import numpy as np
sys.path.insert(0, "tools")
S = ("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
     "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad")
sys.path.insert(0, S)
from skimage import measure
from svgsheet import Faces, Sheet
from verode import LIGHT
from vpen import ink
import vpen, vpen2, vpen3, vpen4, vform

PX = 1400.0
W = 26.5


def outline(strokes, w=W, place=True, oval=None, light=None):
    xs = [p[0] for s, _c in strokes for p in s]
    ys = [p[1] for s, _c in strokes for p in s]
    x0, y0, y1 = min(xs), min(ys), max(ys)
    if oval:
        w = oval[1]
        if light:
            (pts, _c), = strokes
            i, j, f = light
            box = (x0, y0, max(xs), y1)
            pad = int(max(oval) * PX / (y1 - y0) / 2.0) + 20
            m, k = vpen.ink_oval([(pts[:i + 1], False), (pts[j - 1:], False)], oval[0], oval[1], PX, box, pad)
            m2, _ = vpen.ink_oval([(pts[i:j], False)], oval[0] * f, oval[1] * f, PX, box, pad)
            m = m | m2
        else:
            m, k = vpen.ink_oval(strokes, oval[0], oval[1], px=PX)
            pad = int(max(oval) * k / 2.0) + 20
    else:
        m, k = ink(strokes, w, px=PX)
        pad = int(w * k / 2.0) + 20
    m = vpen2.fill_specks(m, k, w)
    H = m.shape[0]
    rings = []
    for c in measure.find_contours(m.astype(float), 0.5):
        if len(c) < 24:
            continue
        p = measure.approximate_polygon(c, tolerance=0.8)
        rings.append([(x0 + (x - pad) / k, y0 + (H - pad - y) / k) for y, x in p])
    ax = [x for r in rings for x, _y in r]
    ay = [y for r in rings for _x, y in r]
    # a traced letter is centred where the built в is and stood on o's
    # overshoot; one drawn on o's own centreline is already in the cell
    dx = 281.0 - (min(ax) + max(ax)) / 2.0 if place else 0.0
    dy = -10.0 - min(ay) if place else 0.0
    return "".join("M" + "L".join("%.1f,%.1f" % (x + dx, y + dy) for x, y in r) + "Z"
                   for r in rings)


class Swap:
    """The built face with one letter replaced by a candidate outline."""

    def __init__(self, face, key, d):
        self.f, self.key, self.cand = face, key, d
        self.upem = face.upem

    def d(self, ch):
        return self.cand if ch == "в" else self.f.d(ch)

    def advance(self, ch):
        return self.f.advance(ch)


def main():
    faces = Faces()
    thin = faces("ThinItalic")
    label = faces("Regular")
    loop, bowl, _c = vpen2.paths(LIGHT, 740.0, 1.0, 120.0, (0.4, 0.4), 0.0)
    a = outline([(loop, False), (bowl, False)])
    loop, bowl = vpen3.paths(LIGHT, 740.0, 1.0, 280.0, 0.3, (0.3, 0.6))
    b = outline([(loop, False), (bowl, False)])
    ring, lower = vpen4.paths(LIGHT, 740.0, 1.0, 90.0, cut=280.0, at=0.3, pull=(0.3, 0.6))
    b2 = outline([(ring, True), (lower, False)])
    ring, lower = vpen4.paths(LIGHT, 740.0, 1.0, 90.0, straight=True,
                              cut=280.0, at=0.3, pull=(0.3, 0.6))
    b3 = outline([(ring, True), (lower, False)])
    THIN = "fonts/ttf/SUSEMono-ThinItalic.ttf"
    e1 = outline([(vform.strip_spine(THIN, 28.0, None, 10.0, 30.0, 0.24, 1.6, 0.80), True)],
                 28.0, place=False)
    e2 = outline([(vform.strip_spine(THIN, 28.0, None, 10.0, 30.0, 0.28, 1.0, 0.80), True)],
                 28.0, place=False)
    sp = lambda f, w, lean, eye, bow: outline(
        [(vform.strip_spine(f, w, None, 10.0, lean, eye, 1.6, 0.80, bow=bow, stop=True), False)],
        w, place=False)
    nk = lambda f, w, att, neck, lean, eye, close, bow: outline(
        [(vform.strip_spine(f, w, att, neck, lean, eye, close, 0.80, bow=bow, curl=True), False)],
        w, place=False)
    dr = lambda f, w, att, W: outline(
        [(vform.draw_spine(f, w, att, 95.0, 18.0, W, 0.80, 0.55, 0.0, 0.40, soft=31, cap=True), False)],
        w, place=False)
    pn = lambda f, w, r, gap, vee: outline(
        [(vform.pen_spine(f, w, 18.0, r, gap, vee, 0.25), False)], w, place=False)
    st = lambda f, w, r, gap: outline(
        [(vform.stem_spine(f, w, 18.0, r, gap, 35.0, 0.25, 0.80, 0.0, 275.0, 1.0), False)],
        w, place=False)
    sj = lambda f, w, r, split, vee=55.0, bulge=0.60, l2=0.20, merge=0.0: outline(
        [(vform.pen_spine(f, w, 18.0, r, 0.0, vee, bulge, l2=l2, split=split, merge=merge), False)],
        w, place=False)
    rd = lambda f, w, r, full, merge, psi, scale=0.80, wide=1.0: outline(
        [(vform.pen_spine(f, w, 18.0, r, 0.0, 65.0, 0.0, scale=scale, split=0.6, merge=merge,
                          full=full, psi=psi, wide=wide, loopwide=wide), False)], w, place=False)
    rr = lambda f, w, r, merge, wide, lw: outline(
        [(vform.pen_spine(f, w, 18.0, r, 0.0, 65.0, 0.0, scale=0.80, split=0.6, merge=merge,
                          full=0.65, psi=-40.0, wide=wide, loopwide=lw, roundtop=True), False)],
        w, place=False)
    cols = [("L3  as sent", Swap(thin, "l3", rd(THIN, 28.0, 70.0, 0.65, 5.0, -40.0, 0.80, 1.25))),
            ("L3  round top", Swap(thin, "l3r", rr(THIN, 28.0, 70.0, 5.0, 1.25, 1.35)))]
    CW = 520
    sh = Sheet(CW * len(cols) + 40, "Thin italic в, the copybook form", label=label)
    sh.heading("Thin italic в: redrawn to the copybook shape")
    sh.note("the loop's top stays a true circle when it widens; stretched, it squared off at the top left")
    y = sh.y
    for i, (name, _f) in enumerate(cols):
        sh.y = y
        sh._words(label, name, 20 + i * CW, y + 30, 15, "#1a1a1a")
    sh.y = y + 40
    rows = [("Вв", 260, "glyphs"), ("вовк вода", 64, "line"),
            ("право, вовк, звичайно, вгору", 22, "line"),
            ("право, вовк, звичайно, вгору", 14, "line"),
            ("право, вовк, звичайно, вгору", 12, "line")]
    for text, px, kind in rows:
        y = sh.y
        ends = []
        for i, (_n, f) in enumerate(cols):
            sh.y = y
            if kind == "glyphs":
                sh.glyphs(f, text, px, lx=40 + i * CW)
            else:
                sh.line([(f, text, "#000")], px, lx=20 + i * CW)
            ends.append(sh.y)
        sh.y = max(ends)
        sh.rule()
    for i in range(1, len(cols)):
        sh.vrule(i * CW + 5, 90, sh.y)
    # the heavy master, C only: B3's ExtraBold needs Radon's spine stretched
    # by nearly half, which is the thing C was drawn to be rid of
    EB = "fonts/ttf/SUSEMono-ExtraBoldItalic.ttf"
    eb = Swap(faces("ExtraBoldItalic"), "l3reb",
              rr(EB, 132.0, 125.0, 1.2, 1.20, 1.20))
    sh.gap(20)
    sh.heading("ExtraBold, L3 round top")
    sh.glyphs(eb, "Вв", 260, lx=40)
    sh.line([(eb, "вовк вода", "#000")], 64, lx=20)
    sh.line([(eb, "право, вовк, звичайно, вгору", "#000")], 22, lx=20)
    sh.line([(eb, "право, вовк, звичайно, вгору", "#000")], 14, lx=20)
    print(sh.save(sys.argv[1]))
    faces.close()


if __name__ == "__main__":
    main()
