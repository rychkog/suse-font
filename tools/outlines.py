"""The outlines themselves -- nodes, handles, extrema, kinks.

    ./venv/bin/python tools/outlines.py            # г д, both masters
    ./venv/bin/python tools/outlines.py г о        # named letters

Every other probe in this project reads the INK: how much of it, how wide,
where the widest disc fits. None of them can see a curve that is lumpy, a node
sitting where no extreme is, a handle that kinks a join, or a hundred nodes
doing the work of twelve. A donated outline is exactly where that goes wrong,
because what arrives is whatever the donor's format left behind -- a TrueType
quadratic expanded segment by segment is a node every few units, and dense
nodes ride every wobble in the source.

So this draws the outline rather than the letter, with the on-curve nodes as
squares and the handles as lines to their circles, and reports:

  nodes     how many, against the face's own o -- the comparison that says
            whether the density is this family's or the donor's
  extrema   points where the curve reaches its leftmost, rightmost, top or
            bottom with no node there. Every one is a place the curve cannot
            be edited, hinted or rounded predictably
  kinks     a join marked smooth whose two handles are not in line, in degrees
  short     segments under a hundredth of the em, which are nodes doing
            nothing but holding the count up
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import math                                                    # noqa: E402

import glyphsLib                                               # noqa: E402
from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

from geom import slant                                         # noqa: E402
from params import Params                                      # noqa: E402
import recipes as R                                            # noqa: E402

SRC = "sources/SUSEMono-Italic.glyphs"
FACE = "fonts/ttf/SUSEMono-Regular.ttf"
NAMES = {"г": "ge-cy", "д": "de-cy"}
EM = 1000.0


def built(path, ch, cp=None):
    """The same letter as it SHIPS -- after overlap removal and the quadratic
    conversion. The source is where a letter is drawn and this is what a reader
    gets, and for an assembled glyph they are not the same outline: this
    family builds El, Pe, Sha and д out of overlapping parts, and the overlap
    comes out on the way to the font.
    """
    from fontTools.ttLib import TTFont
    from fontTools.pens.recordingPen import RecordingPen
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        pen = RecordingPen()
        f.getGlyphSet()[f.getBestCmap()[cp or ord(ch)]].draw(pen)
    finally:
        f.close()
    out, cur, at = [], None, None
    for verb, pts in pen.value:
        if verb == "moveTo":
            cur, at = [(pts[0][0], pts[0][1], "line")], pts[0]
        elif verb == "lineTo":
            cur.append((pts[0][0], pts[0][1], "line"))
            at = pts[0]
        elif verb == "qCurveTo":
            offs, end = list(pts[:-1]), pts[-1]
            if end is None:
                end = ((offs[0][0] + offs[-1][0]) / 2.0,
                       (offs[0][1] + offs[-1][1]) / 2.0)
            for i, c in enumerate(offs):
                nxt = end if i == len(offs) - 1 else (
                    (c[0] + offs[i + 1][0]) / 2.0,
                    (c[1] + offs[i + 1][1]) / 2.0)
                cur += [(at[0] + 2.0 / 3.0 * (c[0] - at[0]),
                         at[1] + 2.0 / 3.0 * (c[1] - at[1]), "offcurve"),
                        (nxt[0] + 2.0 / 3.0 * (c[0] - nxt[0]),
                         nxt[1] + 2.0 / 3.0 * (c[1] - nxt[1]), "offcurve"),
                        (nxt[0], nxt[1], "curve")]
                at = nxt
        elif verb in ("closePath", "endPath"):
            out.append(cur)
            cur = None
    return out


def contours(pr, ch):
    """The letter as it is written, leaning, as lists of (x, y, kind)."""
    if ch in NAMES:
        ps = R.ITALIC[NAMES[ch]](pr)
    else:
        ps = pr.paths(ch)
    out = []
    for p in slant(ps, pr.italic, pr.pivot):
        out.append([(n.position.x, n.position.y, n.type, n.smooth)
                    for n in p.nodes])
    return out


def segments(c):
    """(p0, controls, p1) per segment, walking from the first on-curve node."""
    k = next(i for i, n in enumerate(c) if n[2] != "offcurve")
    ns = c[k:] + c[:k]
    out, at, pend = [], ns[0], []
    for n in ns[1:] + [ns[0]]:
        if n[2] == "offcurve":
            pend.append(n)
        else:
            out.append((at, pend, n))
            at, pend = n, []
    return out


def bez(p0, c1, c2, p3, t):
    u = 1.0 - t
    return (u**3 * p0[0] + 3*u*u*t * c1[0] + 3*u*t*t * c2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3*u*u*t * c1[1] + 3*u*t*t * c2[1] + t**3 * p3[1])


def flat(c, steps=32):
    pts = []
    for p0, cs, p1 in segments(c):
        if len(cs) == 2:
            for s in range(steps + 1):
                pts.append(bez(p0, cs[0], cs[1], p1, s / float(steps)))
        else:
            pts += [(p0[0], p0[1]), (p1[0], p1[1])]
    return pts


def extrema(c):
    """Segments whose curve passes an extreme with no node on it.

    Solved on the cubic rather than sampled: the derivative is a quadratic and
    a root strictly inside 0..1 that moves the point more than half a unit off
    the chord IS a missing extreme. Half a unit because the format rounds to
    integers and an extreme that lands within rounding of a node is one.
    """
    bad = []
    for i, (p0, cs, p1) in enumerate(segments(c)):
        if len(cs) != 2:
            continue
        for k in (0, 1):
            a = -p0[k] + 3 * cs[0][k] - 3 * cs[1][k] + p1[k]
            b = 2 * (p0[k] - 2 * cs[0][k] + cs[1][k])
            cc = cs[0][k] - p0[k]
            roots = []
            if abs(a) < 1e-9:
                if abs(b) > 1e-9:
                    roots = [-cc / b]
            else:
                d = b * b - 4 * a * cc
                if d >= 0:
                    r = math.sqrt(d)
                    roots = [(-b + r) / (2 * a), (-b - r) / (2 * a)]
            for t in roots:
                if not (0.02 < t < 0.98):
                    continue
                v = bez(p0, cs[0], cs[1], p1, t)[k]
                if min(p0[k], p1[k]) - 0.5 <= v <= max(p0[k], p1[k]) + 0.5:
                    continue
                bad.append((i, "xy"[k], v - (p1[k] if abs(v - p1[k])
                                             < abs(v - p0[k]) else p0[k])))
    return bad


def kinks(c):
    """Joins DECLARED smooth whose two handles are not in line, in degrees.

    The declaration is the point. A corner is not a kink -- this letter has
    three of them, the terminal and the two cuts where the stroke leaves and
    rejoins the bowl, and a junction that met the oval tangentially would be
    the fault rather than the fix. What is worth finding is a node the drawing
    claims is continuous and is not. Read off the built font, where there are
    no flags, every corner reports and none of it means anything.
    """
    out = []
    segs = segments(c)
    for i, (p0, cs, p1) in enumerate(segs):
        nxt = segs[(i + 1) % len(segs)]
        if p1[2] != "curve" or (len(p1) > 3 and not p1[3]):
            continue
        a = cs[-1] if cs else p0
        b = nxt[1][0] if nxt[1] else nxt[2]
        v1 = (p1[0] - a[0], p1[1] - a[1])
        v2 = (b[0] - p1[0], b[1] - p1[1])
        if math.hypot(*v1) < 1e-6 or math.hypot(*v2) < 1e-6:
            continue
        d = math.degrees(abs(math.atan2(v1[0] * v2[1] - v1[1] * v2[0],
                                        v1[0] * v2[0] + v1[1] * v2[1])))
        if d > 6.0:
            out.append((i, d))
    return out


def shorts(c):
    out = []
    for i, (p0, _cs, p1) in enumerate(segments(c)):
        d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        if d < EM / 100.0:
            out.append((i, d))
    return out


def draw(cells, path):
    pad, cw = 22, 330
    W = pad + len(cells) * (cw + pad)
    im = Image.new("RGB", (W, cw + 118), "white")
    d = ImageDraw.Draw(im)
    hd = ImageFont.truetype(FACE, 21)
    lab = ImageFont.truetype(FACE, 15)
    d.text((pad, 18), "the outlines themselves -- on-curve nodes square, "
           "handles to their circles", font=hd, fill=(170, 30, 30))
    for i, (name, cs) in enumerate(cells):
        xs = [q[0] for c in cs for q in flat(c)]
        ys = [q[1] for c in cs for q in flat(c)]
        k = (cw - 40) / max(max(xs) - min(xs), max(ys) - min(ys))
        ox = pad + i * (cw + pad) + 20
        oy = 56 + cw - 20

        def T(x, y):
            return (ox + (x - min(xs)) * k, oy - (y - min(ys)) * k)

        for c in cs:
            d.line([T(*q) for q in flat(c)] , fill=(30, 30, 30), width=2)
            for p0, hs, p1 in segments(c):
                for h in hs:
                    d.line([T(p0[0], p0[1]) if h is hs[0] else T(p1[0], p1[1]),
                            T(h[0], h[1])], fill=(190, 190, 190), width=1)
                    x, y = T(h[0], h[1])
                    d.ellipse([x - 3, y - 3, x + 3, y + 3], outline=(150, 150,
                                                                     255))
            for n in c:
                if n[2] == "offcurve":
                    continue
                x, y = T(n[0], n[1])
                d.rectangle([x - 4, y - 4, x + 4, y + 4],
                            fill=(200, 40, 40) if n[2] == "line"
                            else (40, 90, 200))
        d.text((pad + i * (cw + pad), 56 + cw + 12), name, font=lab,
               fill=(110, 110, 110))
    im.save(path)


def report(ch, mname, cs, ref, cells, tag=""):
    on = sum(len([n for n in c if n[2] != "offcurve"]) for c in cs)
    ex = [e for c in cs for e in extrema(c)]
    kk = [x for c in cs for x in kinks(c)]
    sh = [x for c in cs for x in shorts(c)]
    print("   %-4s %-10s %-7s %d contour%s, %3d nodes (o has %d)   %d missing "
          "extrema, %d kinks, %d short segments"
          % (ch, mname, tag, len(cs), " " if len(cs) == 1 else "s", on, ref,
             len(ex), len(kk), len(sh)))
    for i, ax, over in ex[:4]:
        print("        segment %-3d passes its %s extreme by %.1f"
              % (i, ax, abs(over)))
    for i, deg in sorted(kk, key=lambda t: -t[1])[:4]:
        print("        segment %-3d joins at %.0f degrees off smooth"
              % (i, deg))
    for i, dd in sorted(sh, key=lambda t: t[1])[:3]:
        print("        segment %-3d is %.1f units long" % (i, dd))
    if cells is not None:
        cells.append(("%s %s%s" % (ch, mname, tag and " " + tag), cs))


def main():
    want = [a for a in sys.argv[1:] if not a.startswith("-")] or ["г", "д"]
    font = glyphsLib.load(open(SRC))
    cells = []
    print()
    if "--built" in sys.argv:
        for w in ("Thin", "Regular", "ExtraBold"):
            p = "fonts/ttf/SUSEMono-%sItalic.ttf" % w
            ref = sum(len([n for n in c if n[2] != "offcurve"])
                      for c in built(p, "o"))
            for ch in want:
                report(ch, w, built(p, ch), ref, cells, "shipped")
        draw(cells, "tools/out/outlines.png")
        print("\n   wrote tools/out/outlines.png")
        return
    for mi, mname in ((0, "Thin"), (1, "ExtraBold")):
        pr = Params(font, mi)
        ref = sum(len([n for n in c if n[2] != "offcurve"])
                  for c in contours(pr, "o"))
        for ch in want:
            cs = contours(pr, ch)
            report(ch, mname, cs, ref, cells)
    draw(cells, "tools/out/outlines.png")
    print("\n   wrote tools/out/outlines.png")


if __name__ == "__main__":
    main()
