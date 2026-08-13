"""Take Lilex's hook for the cursive д, and build the bowl from this face's o.

Lilex (https://github.com/mishamyrt/Lilex, Mikhail Myrt) is under the SIL Open
Font License 1.1, which is what lets it be an outline donor; SUSE Mono is under
the same licence. "Lilex" is the donor's trademark and is not a name this font
may use.

Writes `tools/de_donor.py`. Run it from the repository root:

    ./venv/bin/python scripts/de_from_lilex.py

This is б's recipe, part for part, and for the same reason. д is a bowl and one
stroke, and a bowl is where a donor's own design language sits (METHOD F11), so
the bowl is this face's own o and only the hook is donated. Unlike б the hook
is not spliced onto the oval: it is kept as its own closed contour overlapping
o, which is what the letter already did and what the pipeline already accepts,
so there is no landing angle to solve and no seam to assert. Where the hook's
root swells past the plain oval it is meant to -- that swell IS the junction,
and every reference draws it.

Why Lilex and not Sudo, which is this project's donor of record and supplied
г. Sudo draws the OTHER cursive д, the one with a descender, shaped like a g.
Both forms are real and this face has settled on the ∂ form, so Sudo's is the
wrong letter here -- rule 9, METHOD F13. Of the OFL italics on this machine
that draw the ∂ form, Lilex is the one whose weights are structurally
identical: its Thin and Bold italics carry the same segments in the same order,
which is what lets them serve as a weight axis. The static families that do not
(JetBrains Mono, Ioskeley) differ by a node or two per contour, and a font
whose masters disagree on node count does not build.

What comes back to this face, all of it measured by `tools/gd_band.py` over
the eleven monospace italics that actually draw the cursive:

  * the bowl -- this face's own o, untouched, which settles the counter, the
    overshoot, the x-height and the fitting for nothing;
  * the height, 1.38 of o's (panel 1.31..1.50), which is where Lilex already
    draws it;
  * the width, 1.04 of o's (panel 1.00..1.15), fitted LEANING -- see METHOD
    F16, and note the letter this replaces read 1.25;
  * the hook's weight, 0.89 of o's own wall (panel 0.86..0.93), solved on
    Lilex's own two weights read as an axis. Almost exactly what б's branch
    weighs against the same bowl, which is worth noticing: the two letters are
    the same construction in mirror and the panel says so.
"""
import math
import os
import sys

sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")

from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

import glyphsLib
from geom import bbox
from params import Params, Lower, _flatten
from ge_from_sudo import (leaning, mapped, poly, pts_of, stand_up, to_nodes)

FILES = ("Lilex-ThinItalic.otf", "Lilex-BoldItalic.otf")
CP = 0x0434
OUT = "tools/de_donor.py"
SRC = "sources/SUSEMono-Italic.glyphs"

# What the letter should measure, over this face's own o -- `tools/gd_band.py`.
DE_HOOK = 0.89          # the hook's weight over o's wall   panel 0.86..0.93
DE_WIDE = 1.04          # the whole letter's width over o's panel 1.00..1.15

# Lilex draws this letter as one stroke: up the bowl's right side, on over the
# top and back to the left, ending in a cut terminal. These are the segments of
# its outer contour that are HOOK rather than bowl -- from where the bowl's
# right wall carries on upward, round the top, back down the hook's underside,
# and into the two short lines that are the notch where the underside meets the
# bowl's own crown. Counted off by index because the two weights carry the same
# segments in the same order, which `axis` asserts before anything else runs.
HOOK = (3, 4, 5, 6, 7, 8, 9)

# The terminal is the one straight segment inside the hook.
CUT = 5

# What the junction measures, and why it is NOT solved for.
#
# The swell where the hook grows out of the bowl runs 1.13 to 1.41 of o's wall
# across the eleven references, and this letter reads 1.13 at Thin, 1.01 at
# Regular and 1.00 at ExtraBold -- the hook meets the bowl without thickening
# at all at the heavy end, which is under everything measured.
#
# The obvious fix is wrong and was built before it was looked at. Carrying the
# hook's root further down the bowl's right wall means cutting into the
# donor's segment 2, and the chord that then closes the contour runs from the
# crown -- the wall's INNER edge -- down to a point on its OUTER edge, straight
# across the counter. Under non-zero winding that fills part of the counter in;
# it also put a wedge at the junction, and the junction probe was reading the
# wedge. Both masters "improved" and the letter got worse. METHOD F6, again.
#
# Doing it properly means the hook's inner boundary following the COUNTER
# contour rather than the outer one, which is a splice across two contours --
# `scripts/be_from_sudo.py`'s whole machinery, for a swell. Recorded and left.
DE_JOIN = None


def find(name):
    from panel import families
    for r in sorted({os.path.dirname(p) for _f, p in families()}):
        p = os.path.join(r, name)
        if os.path.exists(p):
            return p
    raise SystemExit("%s is not installed -- it is the outline donor" % name)


def segments_of(path, cp):
    """A CFF glyph's contours as (kind, points) segments.

    No quadratic expansion and no curve fitting: CFF is already cubic, so what
    the pen reports is what the designer drew, node for node.
    """
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        pen = RecordingPen()
        f.getGlyphSet()[f.getBestCmap()[cp]].draw(pen)
        deg = float(f["post"].italicAngle)
    finally:
        f.close()
    out, cur = [], None
    for verb, pts in pen.value:
        if verb == "moveTo":
            cur = [("start", [pts[0]])]
        elif verb == "lineTo":
            cur.append(("line", [pts[0]]))
        elif verb == "curveTo":
            cur.append(("curve", list(pts)))
        elif verb in ("closePath", "endPath"):
            out.append(cur)
            cur = None
    return out, deg


def axis():
    """The donor's two weights, checked to be the same drawing."""
    a, deg = segments_of(find(FILES[0]), CP)
    b, _ = segments_of(find(FILES[1]), CP)
    sa = [[k for k, _p in c] for c in a]
    sb = [[k for k, _p in c] for c in b]
    if sa != sb:
        raise SystemExit("Lilex's two italics no longer carry the same "
                         "segments for д -- %s against %s" % (sa, sb))
    return a, b, deg


def blend(a, b, t):
    return [[(k, [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
                  for p, q in zip(ps, qs)])
             for (k, ps), (_k, qs) in zip(ca, cb)]
            for ca, cb in zip(a, b)]


def bowl_top(sg):
    """The top of the donor's own bowl -- where its crown stops rising.

    The letter's own highest point is the hook, so this is read off the segment
    that ends on the crown, which is the one the hook's notch hands over to.
    """
    return sg[HOOK[-1] + 1][1][-1][1]


def fit(sg, pr):
    """The donor's BOWL onto this face's o, and the width onto the panel's.

    The bowl and not the letter: the bowl is what has to end up sitting on this
    face's own o, and everything else -- how far the hook rises, how far left it
    reaches -- follows at the donor's own proportion, which `tools/gd_band.py`
    puts inside the panel already.

    The width is fitted leaning, because that is where it is read (METHOD F16),
    and by bisection because under a shear the extremes change hands as the
    scale changes.
    """
    ox0, oy0, ox1, oy1 = bbox(pr.paths("o"))
    ps = pts_of(sg[0])
    x0 = min(q[0] for q in ps)
    x1 = max(q[0] for q in ps)
    y0 = min(q[1] for q in ps)
    ky = (oy1 - oy0) / (bowl_top(sg[0]) - y0)
    tall = [[(k, [(q[0], oy0 + (q[1] - y0) * ky) for q in qs])
             for k, qs in c] for c in sg]
    want = DE_WIDE * leaning([q for p in pr.paths("o")
                              for q in _flatten(p, 16)], pr.italic, pr.pivot)
    mid = 0.5 * (x0 + x1)

    def at(kx):
        return leaning([(300.0 + (q[0] - mid) * kx, q[1])
                        for q in pts_of(tall[0])], pr.italic, pr.pivot)

    lo, hi = 0.05, 4.0
    for _ in range(30):
        kx = 0.5 * (lo + hi)
        if at(kx) < want:
            lo = kx
        else:
            hi = kx
    kx = 0.5 * (lo + hi)
    out = [mapped(c, lambda q: (300.0 + (q[0] - mid) * kx, q[1])) for c in tall]
    # and the bowl sits where o sits, so the hook lands on o and not beside it
    xs = [q[0] for q in pts_of(out[0])]
    dx = 0.5 * (ox0 + ox1) - 0.5 * (min(xs) + max(xs))
    return [mapped(c, lambda q: (q[0] + dx, q[1])) for c in out]


def square(sg, i, angle):
    """The terminal cut vertical in the italic's own space -- this face cuts
    213 of its 242 terminals at exactly 0 or 90 degrees. Both ends go to the
    one that reaches further left, which is the hook's own extent."""
    t = math.tan(math.radians(angle))
    a, b = sg[i - 1][1][-1], sg[i][1][-1]
    e = min(a[0] - a[1] * t, b[0] - b[1] * t)
    out = list(sg)
    out[i] = (out[i][0], [(e + b[1] * t, b[1])])
    kind, ps = out[i - 1]
    out[i - 1] = (kind, ps[:-1] + [(e + a[1] * t, a[1])])
    return out


def hook(sg):
    """The hook alone, closed off across its own root.

    Kept as its own contour rather than spliced into the oval. It is cut at the
    donor's own handover point, where the bowl's right wall stops being bowl
    and carries on as the hook, and closed with a chord across the stroke
    there -- which lies inside the bowl's ink, so the seam is not on the
    outside of anything. See DE_JOIN for what that costs and why it stands.
    """
    outer = sg[0]
    start = outer[HOOK[0] - 1][1][-1]
    body = [outer[i] for i in HOOK]
    return [("start", [start])] + body + [("line", [start])]


def shape(a, b, t, pr):
    sg = fit(blend(a, b, t), pr)
    return square(hook(sg), HOOK.index(CUT) + 1, pr.italic)


def mask(groups, k):
    """Contours XORed inside a group, groups ORed together.

    `weights.mask_of` XORs everything, which is right for a letter drawn as one
    outline with counters punched out of it and wrong here: the hook OVERLAPS
    the bowl, and XORing the two takes the overlap back out again -- a bite out
    of the junction, in exactly the region the reading is about. The built font
    unions them, because TrueType fills by non-zero winding and both contours
    turn the same way.
    """
    from PIL import Image, ImageDraw, ImageChops
    import numpy as np
    xs = [q[0] for g in groups for p in g for q in p]
    ys = [q[1] for g in groups for p in g for q in p]
    w = int((max(xs) - min(xs)) * k) + 8
    h = int((max(ys) - min(ys)) * k) + 8
    total = Image.new("1", (w, h), 0)
    for g in groups:
        img = Image.new("1", (w, h), 0)
        for pl in g:
            lay = Image.new("1", (w, h), 0)
            ImageDraw.Draw(lay).polygon(
                [(4 + (x - min(xs)) * k, h - 4 - (y - min(ys)) * k)
                 for x, y in pl], fill=1)
            img = ImageChops.logical_xor(img, lay)
        total = ImageChops.logical_or(total, img)
    return np.asarray(total) > 0


def solve(a, b, pr):
    """Where on the donor's two weights the hook weighs what the panel says.

    Read off the render with the bowl in place, because `weights.branch_of`
    finds the hook by where the counter stops -- the stroke above the bowl's
    own crown, trimmed at each end by the bowl's wall so the terminal's cut and
    the junction do not decide the answer. Both leaning, and at twice the
    band's own resolution: METHOD F16.
    """
    import statistics as st
    import weights as W
    from gd_band import XH as BAND_XH
    oy = bbox(pr.paths("o"))
    scale = 2.0 * BAND_XH / float(oy[3] - oy[1])
    lean = math.tan(math.radians(pr.italic))

    def over(pts):
        return [(x + (y - pr.pivot) * lean, y) for x, y in pts]

    bowl = [over(_flatten(q, 96)) for q in pr.paths("o")]
    wall = W.width(W.edt(mask([bowl], scale)))

    def ink(t):
        return mask([bowl, [over(poly(to_nodes(shape(a, b, t, pr)), 40))]],
                    scale)

    def ratio(t):
        rows = W.branch_of(ink(t))
        return (st.median(rows) / wall) if rows else 99.0

    lo, hi = -1.2, 3.0
    for _ in range(16):
        mid = 0.5 * (lo + hi)
        if ratio(mid) < DE_HOOK:
            lo = mid
        else:
            hi = mid
    t = 0.5 * (lo + hi)
    return t, ratio(t), W.width(W.edt(ink(t))) / wall


def build():
    font = glyphsLib.load(open(SRC))
    a, b, deg = axis()
    a = [stand_up(c, deg) for c in a]
    b = [stand_up(c, deg) for c in b]
    out = []
    for mi in range(len(font.masters)):
        pr = Lower(Params(font, mi))
        t, got, jn = solve(a, b, pr)
        print("  master %d  donor axis %+.2f   hook %.2f (wanted %.2f)   "
              "junction %.2f (panel 1.13..1.41 -- see DE_JOIN)"
              % (mi, t, got, DE_HOOK, jn))
        out.append((t, [to_nodes(shape(a, b, t, pr))]))
    n = {tuple(len(p) for p in ps) for _t, ps in out}
    if len(n) != 1:
        raise SystemExit("the masters came out with different nodes, %s -- the "
                         "font will not build" % n)
    return out


def main():
    head = ['"""The cursive д\'s hook, taken from Lilex and fitted to this '
            'face.\n', '\n',
            'Generated by scripts/de_from_lilex.py -- edit that, not this.\n',
            'Lilex is under the SIL Open Font License 1.1, which is what lets\n',
            'it be an outline donor here. Held as data rather than read from\n',
            'the donor at build time so the repository builds without a font\n',
            'that lives outside it.\n', '\n',
            'The BOWL is not here: it is this face\'s own o, added by the\n',
            'recipe. Only the hook is the donor\'s, closed off across its own\n',
            'root and left to overlap the bowl.\n', '\n',
            'UN-SHEARED, like every outline a recipe sees. One entry per\n',
            'master, in source order: contours of (x, y, type, smooth).\n', '"""'
            '\n\nDE = [\n']
    body = []
    made = build()
    for t, paths in made:
        body.append("    # Lilex's Thin to Bold at %+.3f\n    [\n" % t)
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
