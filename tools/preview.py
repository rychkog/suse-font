"""Rasterise constructed glyphs straight from the recipes, without a font build.

A full gftools build takes minutes; drawing the paths directly makes the
edit-look-fix loop a couple of seconds, which is the only way this many glyphs
gets reviewed by eye at all.
"""

import sys
import glyphsLib
from PIL import Image, ImageDraw

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from params import Params            # noqa: E402
import recipes as RU

ALL = dict(RU.RECIPES)

# The cell as delivered. The polygons are filled into a 1-bit mask so the XOR
# below gives even-odd fill, and a 1-bit fill has no antialiasing at all -- so
# the mask is built at SS times this and the sheet is downsampled once at the
# end, which is where the grey edges come from. Drawn at the delivered size it
# was a hard aliased staircase.
CELL_OUT = int(__import__("os").environ.get("CELL", 300))
SS = 4
CELL = CELL_OUT * SS
PAD = 8 * SS


def flatten(p, steps=16):
    """Bezier -> polygon. Winding is resolved by even-odd fill below, so the
    only thing that matters here is that the outline is closed."""
    pts = []
    ns = list(p.nodes)
    if not ns:
        return pts
    # rotate so the contour starts on an on-curve node
    start = next((i for i, n in enumerate(ns) if n.type != "offcurve"), 0)
    ns = ns[start:] + ns[:start]
    cur = (ns[0].position.x, ns[0].position.y)
    pts.append(cur)
    i = 1
    ring = ns[1:] + [ns[0]]
    while i <= len(ring):
        n = ring[i - 1]
        if n.type == "offcurve":
            c1 = (n.position.x, n.position.y)
            c2n = ring[i]
            c2 = (c2n.position.x, c2n.position.y)
            endn = ring[i + 1]
            end = (endn.position.x, endn.position.y)
            for s in range(1, steps + 1):
                t = s / steps
                mt = 1 - t
                x = (mt ** 3 * cur[0] + 3 * mt * mt * t * c1[0]
                     + 3 * mt * t * t * c2[0] + t ** 3 * end[0])
                y = (mt ** 3 * cur[1] + 3 * mt * mt * t * c1[1]
                     + 3 * mt * t * t * c2[1] + t ** 3 * end[1])
                pts.append((x, y))
            cur = end
            i += 3
        else:
            cur = (n.position.x, n.position.y)
            pts.append(cur)
            i += 1
    return pts


def to_pen(paths, pen):
    """Replay Glyphs contours into a segment pen.

    In this format an on-curve node carries the type of the segment arriving
    at it, and a 'curve' node is preceded by its two off-curve controls.
    """
    for p in paths:
        ns = list(p.nodes)
        if not ns:
            continue
        start = next((i for i, n in enumerate(ns)
                      if n.type != "offcurve"), None)
        if start is None:
            continue
        ns = ns[start:] + ns[:start]
        pen.moveTo((ns[0].position.x, ns[0].position.y))
        pend = []
        for n in ns[1:] + [ns[0]]:
            pt = (n.position.x, n.position.y)
            if n.type == "offcurve":
                pend.append(pt)
            elif n.type == "curve":
                pen.curveTo(*pend, pt)
                pend = []
            else:
                pen.lineTo(pt)
                pend = []
        pen.closePath()


def unioned(paths):
    """Resolve the overlapping pieces into clean contours, exactly as the font
    build does. Without this the deliberate stem-over-bar overlaps read as
    holes and every heavy weight looks shattered."""
    import pathops
    sk = pathops.Path()
    to_pen(paths, sk.getPen())
    out = pathops.Path()
    pathops.union([sk], out.getPen())
    from fontTools.pens.recordingPen import RecordingPen
    rec = RecordingPen()
    out.draw(rec)
    return rec.value


def flatten_rec(rec, steps=16):
    """Flatten recorded segments into closed polygons."""
    polys, cur, start = [], [], None
    for op, args in rec:
        if op == "moveTo":
            if cur:
                polys.append(cur)
            start = args[0]
            cur = [start]
        elif op == "lineTo":
            cur.append(args[0])
        elif op == "curveTo":
            p0 = cur[-1]
            c1, c2, p3 = args
            for s in range(1, steps + 1):
                t = s / steps
                mt = 1 - t
                cur.append((
                    mt**3 * p0[0] + 3 * mt * mt * t * c1[0]
                    + 3 * mt * t * t * c2[0] + t**3 * p3[0],
                    mt**3 * p0[1] + 3 * mt * mt * t * c1[1]
                    + 3 * mt * t * t * c2[1] + t**3 * p3[1]))
        elif op == "qCurveTo":
            # pathops answers in quadratics wherever the input segment was
            # one, which happens as soon as an outline comes from a TrueType
            # donor rather than from a recipe. Dropped instead of flattened,
            # the polygon loses whole stretches of the outline and the letter
            # renders as a bowtie -- which read as a broken donor for an
            # afternoon.
            offs, end = list(args[:-1]), args[-1]
            p0 = cur[-1]
            for i, c in enumerate(offs):
                nxt = end if i == len(offs) - 1 else (
                    (c[0] + offs[i + 1][0]) / 2.0,
                    (c[1] + offs[i + 1][1]) / 2.0)
                for s in range(1, steps + 1):
                    t = s / steps
                    mt = 1 - t
                    cur.append((mt * mt * p0[0] + 2 * mt * t * c[0]
                                + t * t * nxt[0],
                                mt * mt * p0[1] + 2 * mt * t * c[1]
                                + t * t * nxt[1]))
                p0 = nxt
        elif op in ("closePath", "endPath"):
            if cur:
                polys.append(cur)
            cur = []
    if cur:
        polys.append(cur)
    return polys


def draw_cell(img, ox, oy, paths, upem, cap, xh):
    d = ImageDraw.Draw(img, "RGBA")
    s = (CELL - 2 * PAD) / float(upem)

    def T(pt):
        return (ox + PAD + pt[0] * s, oy + CELL - PAD - (pt[1] + 260) * s)

    for y, col in ((0, (200, 200, 255, 255)), (cap, (255, 210, 210, 255)),
                   (xh, (210, 255, 210, 255))):
        yy = T((0, y))[1]
        d.line([(ox, yy), (ox + CELL, yy)], fill=col, width=SS)
    # XOR each contour in turn, which gives even-odd fill: counters punch
    # through, and the deliberate stem/bar overlaps stay solid rather than
    # cancelling the way a naive nonzero fill of separate rects would.
    from PIL import ImageChops
    mask = Image.new("1", (CELL, CELL), 0)
    for raw in flatten_rec(unioned(paths)):
        poly = [T(pt) for pt in raw]
        if len(poly) < 3:
            continue
        layer = Image.new("1", (CELL, CELL), 0)
        ImageDraw.Draw(layer).polygon(
            [(x - ox, y - oy) for x, y in poly], fill=1)
        mask = ImageChops.logical_xor(mask, layer)
    img.paste((0, 0, 0), (ox, oy), mask)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "sources/SUSEMono.glyphs"
    font = glyphsLib.load(src)
    names = sys.argv[2:] or list(ALL)
    # a name that is not a recipe is taken as a Latin glyph in the source, so
    # the same harness can show what the typeface already does
    fns = []
    for n in names:
        if ALL.get(n):
            fns.append((n, ALL[n]))
        else:
            fns.append((n, (lambda nm: lambda pr: pr.paths(nm))(n)))

    cols = len(fns)
    img = Image.new("RGB", (cols * CELL, 2 * CELL), "white")
    for mi in (0, 1):
        pr = Params(font, mi)
        print(pr)
        for i, (name, fn) in enumerate(fns):
            try:
                paths = fn(pr)
            except Exception as exc:
                print(f"   !! {name}: {type(exc).__name__}: {exc}")
                continue
            draw_cell(img, i * CELL, mi * CELL, paths, font.upm, pr.cap, pr.xh)
    out = "tools/out/preview.png"
    img = img.resize((cols * CELL_OUT, 2 * CELL_OUT), Image.LANCZOS)
    img.save(out)
    print("wrote", out, img.size)


if __name__ == "__main__":
    main()
