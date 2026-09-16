"""ExtraBold italic в, three candidates side by side, Thin as approved above."""
import sys
from vcompare import outline, Swap, S
from svgsheet import Faces, Sheet
import vform

THIN = "fonts/ttf/SUSEMono-ThinItalic.ttf"
EB = "fonts/ttf/SUSEMono-ExtraBoldItalic.ttf"
PEN = (148.0, 112.0)


def cand(f, w, r, merge, wide, lw, scale, oval=None, lean=18.0, lf=None):
    p = vform.pen_spine(f, w, lean, r, 0.0, 65.0, 0.0, scale=scale, split=0.6,
                                     merge=merge, full=0.65, psi=-40.0, wide=wide,
                                     loopwide=lw, roundtop=True)
    light = vform.pen_spine.loop + (lf,) if lf else None
    return outline([(p, False)], w, place=False, oval=oval, light=light)


def main():
    faces = Faces()
    label = faces("Regular")
    thin = Swap(faces("ThinItalic"), "t", cand(THIN, 28.0, 70.0, 5.0, 1.25, 1.35, 0.80))
    ebf = faces("ExtraBoldItalic")
    ow = sum(PEN) / 2.0
    from svgsheet import Face
    radon = Face("/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/"
                 "MonaspaceRadon-ExtraBoldItalic_1.otf", key="radon")
    cols = [("H: the better one", Swap(ebf, "h1", cand(EB, ow, 100.0, 1.8, 1.15, 1.10, 0.92, PEN))),
            ("K: H with Thin's waist", Swap(ebf, "k1", cand(EB, ow, 130.0, 1.3, 1.15, 1.10, 0.90, PEN))),
            ("L: K, a little narrower", Swap(ebf, "l1", cand(EB, ow, 130.0, 1.4, 1.05, 1.05, 0.90, PEN)))]
    CW = 620
    sh = Sheet(CW * len(cols) + 40, "Italic в, ExtraBold", label=label)
    sh.heading("Italic в at ExtraBold: the waist on the right")
    sh.note("at Thin the loop lands early, so the bowl's top right stays free; H lands late and fills it")
    sh.note("Thin, as you approved it:")
    sh.glyphs(thin, "бВвьы", 150, lx=40)
    sh.line([(thin, "право, вовк, звичайно, вгору, бувало, вибір", "#000")], 22, lx=20)
    sh.rule()
    y = sh.y
    for i, (name, _f) in enumerate(cols):
        sh._words(label, name, 20 + i * CW, y + 30, 15, "#1a1a1a")
    sh.y = y + 40
    top = sh.y
    rows = [("бВвьы", 120, "glyphs"), ("вовк вода", 56, "line"),
            ("право, вовк, вибір", 22, "line"),
            ("право, вовк, звичайно, вгору", 14, "line"),
            ("право, вовк, звичайно, вгору", 12, "line"),
            ("бувало ввів вибив", 14, "line"),
            ("бувало ввів вибив", 12, "line")]
    for text, px, kind in rows:
        y = sh.y
        ends = []
        for i, (_n, f) in enumerate(cols):
            sh.y = y
            if kind == "glyphs":
                sh.glyphs(f, text, px, lx=30 + i * CW)
            else:
                sh.line([(f, text, "#000")], px, lx=20 + i * CW)
            ends.append(sh.y)
        sh.y = max(ends)
        sh.rule()
    for i in range(1, len(cols)):
        sh.vrule(i * CW + 5, top - 40, sh.y)
    sh.note("spacing is the built в's, not the candidate's")
    print(sh.save(sys.argv[1]))
    faces.close()


if __name__ == "__main__":
    main()
