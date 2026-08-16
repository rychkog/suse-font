"""д's junction, drawn as an OUTLINE and magnified -- where the arm lands.

    ./venv/bin/python tools/de_seam.py

Every other probe of this letter reads the ink, and the ink at a seam is a
black shape whose two edges cannot be told apart. What was wrong here could
only be seen as a path: where the arm's underside comes back down onto the
bowl, the two outlines were crossing at a shallow angle and leaving a spur --
a thin wedge of the arm carried on past the crown and cut off flat.

Off the BUILT fonts, so it is the letter as it ships. The x-height is the blue
rule; on-curve nodes are dots, handles are the thin lines.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import math                                                      # noqa: E402

from fontTools.pens.recordingPen import RecordingPen             # noqa: E402
from fontTools.ttLib import TTFont                               # noqa: E402
import numpy as np                                               # noqa: E402
from PIL import Image, ImageDraw, ImageFont                      # noqa: E402

FACE = "fonts/ttf/SUSEMono-Regular.ttf"
WEIGHTS = ("Thin", "Light", "Regular", "Bold", "ExtraBold")
SS = 3
CELL = 380
ZOOM = 5.0              # how much of o's height the window is wide, inverted


def contours(path, ch):
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        gs = f.getGlyphSet()
        cm = f.getBestCmap()
        upem = f["head"].unitsPerEm
        out, cur = [], None
        pen = RecordingPen()
        gs[cm[ord(ch)]].draw(pen)
        for verb, pts in pen.value:
            if verb == "moveTo":
                cur = [pts[0]]
            elif verb == "lineTo":
                cur.append(pts[0])
            elif verb == "qCurveTo":
                cur += list(pts)
            elif verb == "curveTo":
                cur += list(pts)
            elif verb in ("closePath", "endPath") and cur:
                out.append(cur)
                cur = None
        oy = []
        p2 = RecordingPen()
        gs["o"].draw(p2)
        for _v, pts in p2.value:
            oy += [q[1] for q in pts if q]
        return out, upem, (min(oy), max(oy))
    finally:
        f.close()


def _area(c):
    a = 0.0
    for i in range(len(c)):
        x0, y0 = c[i]
        x1, y1 = c[(i + 1) % len(c)]
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def notch(cs, oy1, oh):
    """Where the arm's underside comes back down onto the bowl's crown.

    Found rather than guessed at. Walk the OUTER contour and take the corner
    where it stops descending and starts climbing again -- there is exactly one
    such vertex on the letter's right-hand side within a stroke or two of the
    x-height, and it is the seam. Restricted to that neighbourhood because the
    arm's own terminal is a vertex too, and it is not what this probe is for.
    """
    outer = max(cs, key=lambda c: abs(_area(c)))
    n = len(outer)
    xs = [q[0] for q in outer]
    mid = 0.5 * (min(xs) + max(xs))
    best = None
    for i in range(n):
        q = outer[i]
        if q[0] < mid or abs(q[1] - oy1) > 0.30 * oh:
            continue
        if outer[(i - 1) % n][1] > q[1] < outer[(i + 1) % n][1]:
            if best is None or q[1] < best[1]:
                best = q
    return best or (max(xs) - 0.20 * oh, oy1)


def draw(path, ch, cell, ours=True):
    """The junction window: ink in grey, the path over it, nodes marked."""
    cs, upem, (oy0, oy1) = contours(path, ch)
    oh = oy1 - oy0
    cx, cy = notch(cs, oy1, oh)
    half = oh / ZOOM
    k = cell / (2.0 * half)

    def to(q):
        return ((q[0] - cx) * k + cell / 2.0, cell / 2.0 - (q[1] - cy) * k)

    im = Image.new("RGB", (cell, cell), "white")
    d = ImageDraw.Draw(im)
    # outer filled, counters punched back out -- two overlapping fills would
    # paint the counter in and the seam is read against the white beside it
    order = sorted(cs, key=lambda c: -abs(_area(c)))
    for j, c in enumerate(order):
        d.polygon([to(q) for q in c],
                  fill=(226, 226, 226) if j == 0 else (255, 255, 255))
    y = to((0, oy1))[1]
    d.line([(0, y), (cell, y)], fill=(150, 190, 255), width=2 * SS)
    for c in cs:
        pts = [to(q) for q in c]
        d.line(pts + [pts[0]], fill=(25, 25, 25) if ours else (150, 30, 30),
               width=SS)
        for p in pts:
            r = 3 * SS
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r],
                      fill=(185, 30, 30) if ours else (200, 140, 140))
    return im


def panel():
    """The same seam in the faces that draw this letter. A magnified corner of
    our own is not a judgement of anything -- rule: never show a glyph alone."""
    from panel import italics
    from gd_band import is_cursive_ge
    import weights as W
    out = []
    for fam, path in sorted(italics()):
        if fam.startswith("SUSE Mono"):
            continue
        g = W.render(path, "г", 200)
        if g is None or not is_cursive_ge(g):
            continue
        o = W.render(path, "o", 200)
        de = W.render(path, "д", 200)
        if o is None or de is None:
            continue
        ys = np.where(de.any(axis=1))[0]
        oys = np.where(o.any(axis=1))[0]
        if (ys.max() - oys.max()) / float(oys.max() - oys.min()) > 0.15:
            continue                       # the g-form -- a different letter
        out.append((fam, path))
    return out


def main():
    ch = sys.argv[1] if len(sys.argv) > 1 else "д"
    cell = CELL * SS
    mine = [(w, "fonts/ttf/SUSEMono-%sItalic.ttf" % w)
            for w in ("Thin", "Regular", "ExtraBold")]
    cells = [("ours, " + w, p, True) for w, p in mine] + \
            [(f, p, False) for f, p in panel()]
    COLS = 5
    lab = 40 * SS
    rows = (len(cells) + COLS - 1) // COLS
    im = Image.new("RGB", (24 * SS + COLS * (cell + 20 * SS),
                           70 * SS + rows * (cell + lab + 16 * SS)), "white")
    d = ImageDraw.Draw(im)
    d.text((24 * SS, 18 * SS),
           "%s where the arm lands on the bowl -- the outline, not the ink, at "
           "one magnification. Blue rule is the x-height" % ch,
           font=ImageFont.truetype(FACE, 26 * SS), fill=(170, 30, 30))
    f = ImageFont.truetype(FACE, 20 * SS)
    for i, (name, path, ours) in enumerate(cells):
        x = 24 * SS + (i % COLS) * (cell + 20 * SS)
        y = 70 * SS + (i // COLS) * (cell + lab + 16 * SS)
        try:
            im.paste(draw(path, ch, cell, ours), (x, y))
        except Exception as e:
            d.text((x, y), str(e)[:40], font=f, fill=(200, 0, 0))
        d.text((x, y + cell + 12 * SS), name[:22], font=f,
               fill=(25, 25, 25) if ours else (110, 110, 110))
    im = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    im.save("tools/out/de_seam.png")
    print("   wrote tools/out/de_seam.png", im.size)


if __name__ == "__main__":
    main()
