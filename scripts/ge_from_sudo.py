"""Take Sudo's cursive г whole, and fit it to this face's italic.

Sudo (https://github.com/jenskutilek/sudo-font, Jens Kutilek) is under the SIL
Open Font License 1.1, which is what lets it be an outline donor; SUSE Mono is
under the same licence. "Sudo" is the donor's trademark and is not a name this
font may use. It is already this project's donor of record -- б's branch is
Sudo's -- and one donor for two letters is one design language rather than two.

Writes `tools/ge_donor.py`. Run it from the repository root:

    ./venv/bin/python scripts/ge_from_sudo.py

Why the whole outline this time, when б takes only a stroke. б has a bowl, and
a bowl is where a donor's own language sits (METHOD F11), so its round part had
to be this face's own o. The cursive г has no bowl and no counter and no
counterpart anywhere in this family: it is a top bar, a curve descending to the
left, and a foot running right, and this face draws no stroke that does any of
that. Two rounds were spent reading a SPINE off the references and stroking it
at a constant width instead, and the result was rejected -- ink laid along a
centreline has no modulation and no terminals, so it reads as bent wire
whatever path it follows. A donated outline has both because a designer drew
them.

So the borrow is bigger than б's and is called one. What comes back to this
face is everything that can:

  * the height. `tools/gd_band.py` reads г at exactly 1.00 of its own face's o
    in every one of the eleven italics that draw the cursive -- not 0.99 and
    not 1.01 -- so г's own extent is mapped onto this face's o, overshoot and
    all, rather than carried across at Sudo's proportion of 0.98;
  * the width, 0.97 of o's (the panel's median, 0.92 to 1.04), centred in the
    cell, because the cell is not optional;
  * the terminals, cut vertical in the italic's own sheared space. This face
    cuts 213 of its 242 terminals at exactly 0 or 90 degrees and Sudo cuts
    both of these oblique;
  * and the weight, 0.98 of this face's own o wall (the panel's median, 0.96
    to 1.05) -- which is the whole point of reading the band before fitting
    anything. г weighs what o weighs, and the reader sees the two together in
    every word the letter appears in.

The weight comes off Sudo's own axis, extrapolated below its light end -- see
`solve` for why that is right here and was wrong for б's branch.

Everything here is UN-SHEARED, because that is the space every recipe in this
project works in -- `params.Params.paths` hands a recipe a donor standing up
and `build_cyrillic` leans the result back over on write.
"""
import math
import sys

sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

import glyphsLib
from geom import bbox
from params import Params, Lower, _flatten

SUDO = ("/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/"
        "Sudo-Italic[YTDE,wght].ttf")
CP = 0x0433
OUT = "tools/ge_donor.py"
SRC = "sources/SUSEMono-Italic.glyphs"

# The two ends of Sudo's own weight axis. The letter is taken at a point on
# the line between them, solved per master by `solve`, and that point is below
# 0 at this face's Thin -- Sudo does not draw anything as light as this face's
# lightest.
T = (200.0, 700.0)

# What the letter should measure, over this face's own o. `tools/gd_band.py`,
# over the eleven monospace italics on this machine that actually draw the
# cursive -- an italic that slopes its upright г is not evidence about a letter
# it does not draw, and eighteen of the twenty-nine do exactly that.
GE_INK = 0.98           # its stroke over o's wall     panel 0.96..1.05
GE_WIDE = 0.97          # its width over o's           panel 0.92..1.04
                        # its height is 1.00 of o's in every face measured


def load(w):
    return instantiateVariableFont(TTFont(SUDO), {"wght": w}, inplace=False,
                                   updateFontNames=False)


def segments_of(f, cp):
    """The glyph's contours as (kind, points) segments, quadratics expanded.

    Not qu2cu: a fitted conversion splits where the curvature asks it to, the
    two ends of an axis ask differently, and a glyph that comes out 28 nodes at
    one weight and 25 at the other is a font that will not build. A quadratic
    converts to a cubic exactly, and TrueType's implied on-curve points are
    midpoints, so expanding those gives the same node for the same node at
    every weight. (Lifted from `be_from_sudo.segments`, which is the same
    problem; kept here rather than shared because that one reads б by name.)
    """
    pen = RecordingPen()
    f["glyf"][f.getBestCmap()[cp]].draw(pen, f["glyf"])
    out, cur, at = [], None, (0.0, 0.0)
    for verb, pts in pen.value:
        if verb == "moveTo":
            cur, at = [("start", [pts[0]])], pts[0]
        elif verb == "lineTo":
            cur.append(("line", [pts[0]]))
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
                cur.append(("curve", [
                    (at[0] + 2.0 / 3.0 * (c[0] - at[0]),
                     at[1] + 2.0 / 3.0 * (c[1] - at[1])),
                    (nxt[0] + 2.0 / 3.0 * (c[0] - nxt[0]),
                     nxt[1] + 2.0 / 3.0 * (c[1] - nxt[1])),
                    nxt]))
                at = nxt
        elif verb in ("closePath", "endPath"):
            out.append(cur)
            cur = None
    return out


def mapped(sg, f):
    return [(kind, [f(q) for q in pts]) for kind, pts in sg]


def pts_of(sg):
    return [q for _kind, ps in sg for q in ps]


def stand_up(sg, deg):
    """The donor's own slope taken out. `deg` is its `italicAngle`, which is
    negative for a face leaning right, so the shear is applied as it stands."""
    t = math.tan(math.radians(deg))
    return mapped(sg, lambda q: (q[0] + q[1] * t, q[1]))


def terminals(sg):
    """The two straight segments are the two terminal cuts.

    Sudo draws this letter as one open stroke, so its outline is one loop with
    exactly two straight ends in it and everything else a curve. Found rather
    than counted off by index, because the index moves with the weight and the
    property does not.
    """
    ix = [i for i, (kind, _p) in enumerate(sg) if kind == "line"]
    if len(ix) != 2:
        raise SystemExit("Sudo's г has %d straight segments, expected the two "
                         "terminals -- the outline has changed" % len(ix))
    return ix


def fit(sg, pr):
    """Sudo's г into this face's cell: o's height, 0.97 of o's width, centred.

    The height is the letter's OWN extent onto o's own extent rather than
    Sudo's o onto this one. The panel is unanimous that г stands exactly as
    tall as the face's o -- eleven faces, all 1.00 -- and Sudo draws it at
    0.98, so carrying its proportion across would import the one figure the
    references agree on being different.
    """
    ox0, oy0, ox1, oy1 = bbox(pr.paths("o"))
    ps = pts_of(sg)
    x0 = min(q[0] for q in ps)
    x1 = max(q[0] for q in ps)
    y0 = min(q[1] for q in ps)
    y1 = max(q[1] for q in ps)
    ky = (oy1 - oy0) / (y1 - y0)
    want = (ox1 - ox0) * GE_WIDE
    kx = want / (x1 - x0)
    left = 300.0 - want / 2.0
    return mapped(sg, lambda q: (left + (q[0] - x0) * kx,
                                 oy0 + (q[1] - y0) * ky))


def square(sg, ix, angle):
    """Both terminals cut vertical -- in the italic's own space, not this one.

    Everything here stands up and the letter is leaned back over on write, so
    a cut that should be vertical in the font has to lean by the italic's own
    angle here. Each cut moves to the end that reaches furthest, which keeps
    the letter's extent rather than shortening it: the top bar reaches left and
    the foot reaches right.
    """
    t = math.tan(math.radians(angle))
    out = list(sg)
    for i in ix:
        a = out[i - 1][1][-1] if i else out[-1][1][-1]
        b = out[i][1][-1]
        # x at a common height, so the comparison is of reach and not of slope
        ea, eb = a[0] - a[1] * t, b[0] - b[1] * t
        e = min(ea, eb) if ea + eb < 600.0 else max(ea, eb)
        na = (e + a[1] * t, a[1])
        nb = (e + b[1] * t, b[1])
        out[i] = (out[i][0], [nb])
        j = i - 1 if i else len(out) - 1
        kind, ps = out[j]
        out[j] = (kind, ps[:-1] + [na])
    return out


def bez(p0, p1, p2, p3, t):
    u = 1.0 - t
    return (u**3 * p0[0] + 3*u*u*t * p1[0] + 3*u*t*t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3*u*u*t * p1[1] + 3*u*t*t * p2[1] + t**3 * p3[1])


def walk(sg, steps=10):
    """A run of segments as a polyline, its start included."""
    at = sg[0][1][-1]
    pts = [at]
    for kind, p in sg[1:]:
        if kind == "curve":
            for s in range(1, steps + 1):
                pts.append(bez(at, p[0], p[1], p[2], s / float(steps)))
            at = p[2]
        else:
            pts.append(p[0])
            at = p[0]
    return pts


def ray(o, d, poly):
    """How far from o, along d, the polyline is. None if it is not ahead."""
    best = None
    for i in range(len(poly) - 1):
        ax, ay = poly[i]
        ex, ey = poly[i + 1][0] - ax, poly[i + 1][1] - ay
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-9:
            continue
        fx, fy = ax - o[0], ay - o[1]
        s = (fx * ey - fy * ex) / den
        u = (fx * d[1] - fy * d[0]) / den
        if s > 1e-6 and -1e-9 <= u <= 1.0 + 1e-9 and (best is None or s < best):
            best = s
    return best


def to_nodes(sg):
    out = []
    for kind, pts in sg[1:]:
        if kind == "curve":
            out += [(pts[0][0], pts[0][1], "offcurve", False),
                    (pts[1][0], pts[1][1], "offcurve", False),
                    (pts[2][0], pts[2][1], "curve", True)]
        else:
            out.append((pts[0][0], pts[0][1], "line", False))
    return out


def poly(nodes, steps=24):
    ns = nodes[:]
    start = next(i for i, n in enumerate(ns) if n[2] != "offcurve")
    ns = ns[start:] + ns[:start]
    pts, cur, i = [(ns[0][0], ns[0][1])], (ns[0][0], ns[0][1]), 1
    ring = ns[1:] + [ns[0]]
    while i <= len(ring):
        n = ring[i - 1]
        if n[2] == "offcurve":
            c1, c2, e = n, ring[i], ring[i + 1]
            for s in range(1, steps + 1):
                u = s / float(steps)
                m = 1 - u
                pts.append((m ** 3 * cur[0] + 3 * m * m * u * c1[0]
                            + 3 * m * u * u * c2[0] + u ** 3 * e[0],
                            m ** 3 * cur[1] + 3 * m * m * u * c1[1]
                            + 3 * m * u * u * c2[1] + u ** 3 * e[1]))
            cur = (e[0], e[1])
            i += 3
        else:
            cur = (n[0], n[1])
            pts.append(cur)
            i += 1
    return pts


def blend(a, b, t, into):
    for i in range(len(a)):
        into.coordinates[i] = (a[i][0] + (b[i][0] - a[i][0]) * t,
                               a[i][1] + (b[i][1] - a[i][1]) * t)


def shape(a, b, t, work, deg, pr):
    """The finished letter at one point on the donor's axis: its own weight,
    then this face's box, then this face's terminal cut."""
    blend(a, b, t, work["glyf"][work.getBestCmap()[CP]])
    sg = fit(stand_up(segments_of(work, CP)[0], deg), pr)
    return square(sg, terminals(sg), pr.italic)


def solve(a, b, work, deg, pr):
    """Where on the donor's axis this letter weighs what o's wall weighs.

    The axis, and not an offset of the outline. Thinning by moving the edges
    inward folds: an offset curve crosses itself wherever the radius of
    curvature falls below half the stroke, this letter turns twice, and the
    fault shows up as a lump exactly where the turns are -- the light master's
    stroke measured 2.49 of o's wall unthinned and 2.86 after being offset to a
    third of its weight, because the reading was picking up the fold. A weight
    axis is the one way to change a drawing's weight that a designer already
    solved: the modulation, the terminals and the turns all come with it.

    Extrapolated below the donor's own light end, which METHOD §1 warns against
    and `be_from_sudo` was corrected for. The distinction is what the donor is
    supplying. There it supplies ONE STROKE spliced onto this face's bowl, and
    extrapolating drove that stroke's root and terminal apart until it fell
    off the letter. Here it supplies the whole letter, every part scaling
    together, and it stays a letter until the stroke passes through zero -- at
    t -0.9 it is a coherent hairline and at -1.2 it has turned inside out. The
    solve is bracketed above that and `build` refuses anything below it.

    Read off the render, by `weights.py`, which decides nothing: the largest
    disc that fits inside the ink is the stroke's thickness there whatever
    direction the stroke runs. The same measure is taken of o, so the two are
    the same quantity by construction.
    """
    import weights as W
    scale = W.XH / float(pr.cap)
    wall = W.width(W.edt(W.mask_of([_flatten(q, 96) for q in pr.paths("o")],
                                   scale)))

    def ratio(t):
        ps = [poly(to_nodes(shape(a, b, t, work, deg, pr)), 40)]
        return W.width(W.edt(W.mask_of(ps, scale))) / wall

    lo, hi = FLOOR, 1.6
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        if ratio(mid) < GE_INK:
            lo = mid
        else:
            hi = mid
    t = 0.5 * (lo + hi)
    return t, ratio(t)


# How far below the donor's own light end the axis may be carried. The stroke
# passes through zero at about -1.0 and the outline turns inside out below it;
# -0.85 is a coherent hairline and the last point worth calling a drawing.
FLOOR = -0.85


def build():
    font = glyphsLib.load(open(SRC))
    lo, hi = load(T[0]), load(T[1])
    gn = lo.getBestCmap()[CP]
    a = list(lo["glyf"][gn].coordinates)
    b = list(hi["glyf"][gn].coordinates)
    lo.close()
    hi.close()
    work = load(T[0])
    deg = float(work["post"].italicAngle)
    out = []
    for mi in range(len(font.masters)):
        pr = Lower(Params(font, mi))
        t, got = solve(a, b, work, deg, pr)
        if t <= FLOOR + 0.02:
            raise SystemExit("master %d ran to the floor of the donor's axis "
                             "at %.2f -- past there the stroke passes through "
                             "zero and the outline turns inside out" % (mi, t))
        print("  master %d  donor axis %+.2f (wght %.0f)   г measures %.2f of "
              "o's wall, wanted %.2f"
              % (mi, t, T[0] + (T[1] - T[0]) * t, got, GE_INK))
        out.append((t, [to_nodes(shape(a, b, t, work, deg, pr))]))
    work.close()
    n = {tuple(len(p) for p in ps) for _t, ps in out}
    if len(n) != 1:
        raise SystemExit("the masters came out with different nodes, %s -- the "
                         "font will not build" % n)
    return out


def main():
    head = ['"""The cursive г, taken whole from Sudo and fitted to this '
            'face.\n', '\n',
            'Generated by scripts/ge_from_sudo.py -- edit that, not this.\n',
            'Sudo is under the SIL Open Font License 1.1, which is what lets\n',
            'it be an outline donor here. Held as data rather than read from\n',
            'the donor at build time so the repository builds without a font\n',
            'that lives outside it.\n', '\n',
            'UN-SHEARED, like every other outline a recipe sees: the italic\n',
            'goes back on in build_cyrillic. Its height is this face\'s o, its\n',
            'width 0.97 of o\'s, its terminals cut vertical and its stroke\n',
            'thinned to 0.98 of o\'s own wall.\n', '\n',
            'One entry per master, in source order: contours of\n',
            '(x, y, type, smooth). Both masters carry the same nodes in the\n',
            'same order.\n', '"""\n\nGE = [\n']
    body = []
    made = build()
    for t, paths in made:
        body.append("    # Sudo's own weight axis at %.0f\n    [\n" % t)
        for p in paths:
            body.append("        [\n")
            for x, y, ty, sm in p:
                body.append("            (%.1f, %.1f, %r, %r),\n"
                            % (x, y, ty, sm))
            body.append("        ],\n")
        body.append("    ],\n")
    open(OUT, "w").write("".join(head) + "".join(body) + "]\n")
    print("%s  %s" % (OUT, [[len(p) for p in ps] for _, ps in made]))


if __name__ == "__main__":
    main()
