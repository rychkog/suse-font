"""Outline algebra over Glyphs paths.

Everything here exists to serve one constraint: the two masters (Thin 100 and
ExtraBold 800) must stay interpolation-compatible. A glyph built by applying
the SAME sequence of operations to the SAME donor contours in both masters is
compatible by construction -- the donors already are, since the upstream font
interpolates. That is why recipes are written as operations on real outlines
rather than as coordinates: hand-typed coordinates would have to be kept in
sync across masters by hand, and would drift.
"""

from glyphsLib.classes import GSPath, GSNode
from glyphsLib.types import Point

LINE = "line"
CURVE = "curve"
OFFCURVE = "offcurve"


def node(x, y, typ=LINE, smooth=False):
    n = GSNode()
    n.position = Point(x, y)
    n.type = typ
    n.smooth = smooth
    return n


def path(nodes, closed=True):
    p = GSPath()
    p.closed = closed
    for n in nodes:
        p.nodes.append(n)
    return p


def rect(x0, y0, x1, y1):
    """An axis-aligned rectangle, wound the same way the source winds its stems.

    SUSE Mono builds H, T and friends as overlapping rectangles rather than as
    merged outlines, so this is the native vocabulary of the typeface, not a
    shortcut around it.
    """
    return path([node(x1, y0), node(x1, y1), node(x0, y1), node(x0, y0)])


def clone(p):
    return path([node(n.position.x, n.position.y, n.type, n.smooth)
                 for n in p.nodes], p.closed)


def clone_all(paths):
    return [clone(p) for p in paths]


def reverse(p):
    """Reverse contour direction, keeping the on-curve/off-curve pattern valid.

    An on-curve node carries the type of the segment ARRIVING at it from the
    previous on-curve node. Reversing the point list flips which segment
    arrives where, so a node's new type is the type its SUCCESSOR used to
    carry: with A-line B-curve C-line, the reversed path runs C B A and needs
    C=line, B=line, A=curve.

    Mirroring without this leaves the winding inverted, which turns the shape
    into a hole once overlaps are removed.
    """
    ns = list(p.nodes)
    if not ns:
        return clone(p)
    oncurve = [i for i, n in enumerate(ns) if n.type != OFFCURVE]
    new_type = {}
    for k, i in enumerate(oncurve):
        new_type[i] = ns[oncurve[(k + 1) % len(oncurve)]].type
    out = []
    for i in reversed(range(len(ns))):
        n = ns[i]
        out.append(node(n.position.x, n.position.y,
                        new_type.get(i, OFFCURVE), n.smooth))
    return path(out, p.closed)


def _map_points(paths, fn):
    out = []
    for p in paths:
        q = clone(p)
        for n in q.nodes:
            x, y = fn(n.position.x, n.position.y)
            n.position = Point(x, y)
        out.append(q)
    return out


def translate(paths, dx=0, dy=0):
    return _map_points(paths, lambda x, y: (x + dx, y + dy))


def mirror_x(paths, axis=300.0):
    """Mirror horizontally. Direction is reversed to keep the winding correct --
    a mirrored contour that keeps its original order becomes a counter."""
    flipped = _map_points(paths, lambda x, y: (2 * axis - x, y))
    return [reverse(p) for p in flipped]


def mirror_y(paths, axis):
    flipped = _map_points(paths, lambda x, y: (x, 2 * axis - y))
    return [reverse(p) for p in flipped]


def piecewise_y(paths, knots):
    """Rescale vertically through a piecewise-linear map given as (from, to) pairs.

    Used for the cap-height to x-height derivations (П from H, Ш, Ц, Я from R
    and so on). A plain uniform scale would thin every horizontal bar by the
    scale factor while leaving vertical stems untouched, which reads as a
    weight error rather than a size change. Pinning the bar edges as knots
    keeps bar thickness exact and absorbs the difference in the open field
    between them.
    """
    # collapse knots that share a source value -- a band starting exactly on
    # the baseline produces one, and a zero-width source span has no slope
    ks = []
    for a, b in sorted(knots):
        if ks and abs(a - ks[-1][0]) < 1e-9:
            ks[-1] = (a, b)
        else:
            ks.append((a, b))
    if len(ks) < 2:
        return clone_all(paths)

    def f(y):
        if y <= ks[0][0]:
            (a0, b0), (a1, b1) = ks[0], ks[1]
            return b0 + (y - a0) * (b1 - b0) / (a1 - a0)
        for (a0, b0), (a1, b1) in zip(ks, ks[1:]):
            if a0 <= y <= a1:
                return b0 + (y - a0) * (b1 - b0) / (a1 - a0)
        (a0, b0), (a1, b1) = ks[-2], ks[-1]
        return b0 + (y - a0) * (b1 - b0) / (a1 - a0)

    return _map_points(paths, lambda x, y: (x, f(y)))


def scale_x(paths, factor, center=300.0):
    return _map_points(paths, lambda x, y: (center + (x - center) * factor, y))


def bbox(paths):
    xs = [n.position.x for p in paths for n in p.nodes]
    ys = [n.position.y for p in paths for n in p.nodes]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def slant(paths, angle_deg, pivot_y=0.0):
    """Shear for the sloped-roman italic. x shifts by (y - pivot) * tan(angle)."""
    import math
    t = math.tan(math.radians(angle_deg))
    return _map_points(paths, lambda x, y: (x + (y - pivot_y) * t, y))


def cut_span(p, start, end):
    """Keep nodes [start:end] of a contour and close the gap with a straight edge.

    This is how Г comes out of E: E's left spine carries the rounded corner
    treatment that defines the typeface, so Г reuses those exact nodes instead
    of trying to reproduce the corner from measurements.
    """
    kept = [node(n.position.x, n.position.y, n.type, n.smooth)
            for n in list(p.nodes)[start:end]]
    if kept:
        # the reconnecting edge must be a straight line, whatever the donor
        # segment arriving at this node used to be
        kept[0].type = LINE
        kept[0].smooth = False
    return path(kept, True)


def fit(paths, x0, y0, x1, y1):
    """Map a group of contours so their common bounding box becomes the target.

    Used for the bowls of Ф and Ю: reusing O's curve character while setting
    width and stroke thickness independently is the only way those letters
    keep a counter at ExtraBold inside a 600-unit cell.
    """
    bx0, by0, bx1, by1 = bbox(paths)
    sx = (x1 - x0) / (bx1 - bx0) if bx1 > bx0 else 1.0
    sy = (y1 - y0) / (by1 - by0) if by1 > by0 else 1.0
    return _map_points(paths, lambda x, y: (x0 + (x - bx0) * sx,
                                            y0 + (y - by0) * sy))


def squash(paths, bands, y_from, y_to, y_base=0.0):
    """Compress cap-height artwork to x-height without thinning horizontal bars.

    `bands` are source y-ranges -- the bars, and the rounded corners -- whose
    height must survive unchanged; everything between them absorbs the
    difference. A plain vertical scale would take a 28-unit bar down to 19 and
    read as a weight error rather than a size change, which is the single most
    common way a bolted-on Cyrillic gives itself away.
    """
    bands = sorted(bands)
    fixed = sum(hi - lo for lo, hi in bands)
    span_src = y_from - y_base
    span_dst = y_to - y_base
    if span_src - fixed <= 0:
        factor = 1.0
    else:
        factor = (span_dst - fixed) / float(span_src - fixed)
    knots = [(y_base, y_base)]
    cur_s, cur_d = y_base, y_base
    for lo, hi in bands:
        cur_d += (lo - cur_s) * factor
        knots.append((lo, cur_d))
        cur_d += hi - lo
        knots.append((hi, cur_d))
        cur_s = hi
    knots.append((y_from, y_to))
    return piecewise_y(paths, knots)


def piecewise_x(paths, knots):
    """`piecewise_y` across the other axis. Same map, same collapsing rule."""
    ks = []
    for a, b in sorted(knots):
        if ks and abs(a - ks[-1][0]) < 1e-9:
            ks[-1] = (a, b)
        else:
            ks.append((a, b))
    if len(ks) < 2:
        return clone_all(paths)

    def f(x):
        if x <= ks[0][0]:
            (a0, b0), (a1, b1) = ks[0], ks[1]
            return b0 + (x - a0) * (b1 - b0) / (a1 - a0)
        for (a0, b0), (a1, b1) in zip(ks, ks[1:]):
            if a0 <= x <= a1:
                return b0 + (x - a0) * (b1 - b0) / (a1 - a0)
        (a0, b0), (a1, b1) = ks[-2], ks[-1]
        return b0 + (x - a0) * (b1 - b0) / (a1 - a0)

    return _map_points(paths, lambda x, y: (f(x), y))


def squash_x(paths, bands, x_from, x_to, x_base):
    """`squash` across the other axis: narrow artwork without thinning walls.

    The vertical counterpart exists because a plain vertical scale thins the
    horizontal bars. A plain horizontal scale has the same fault the other way
    round -- it thins the vertical walls -- and a letter derived from a wider
    donor needs both halves of the trick, one per axis.

    `bands` are source x-ranges to carry across unchanged; the field between
    them absorbs the difference. Unlike `squash` the base is not the origin,
    so it is passed rather than defaulted: a letter is narrowed about its own
    left edge, not about zero.
    """
    bands = sorted(bands)
    fixed = sum(hi - lo for lo, hi in bands)
    span_src = x_from - x_base
    span_dst = x_to - x_base
    if span_src - fixed <= 0:
        factor = 1.0
    else:
        factor = (span_dst - fixed) / float(span_src - fixed)
    knots = [(x_base, x_base)]
    cur_s, cur_d = x_base, x_base
    for lo, hi in bands:
        cur_d += (lo - cur_s) * factor
        knots.append((lo, cur_d))
        cur_d += hi - lo
        knots.append((hi, cur_d))
        cur_s = hi
    knots.append((x_from, x_to))
    return piecewise_x(paths, knots)


def area(p):
    """Signed area; positive is counter-clockwise, the outer-contour direction
    this source uses. Negative means the contour subtracts."""
    pts = [(n.position.x, n.position.y) for n in p.nodes]
    return 0.5 * sum(x0 * y1 - x1 * y0
                     for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))


def stretch_right(paths, x):
    """Move the rightmost vertical edge out to x, lengthening an arm.

    L's arm is drawn for L's own width; reused as the foot of Ш or the bar of
    Ч it has to reach the letter's own right edge. Moving the end nodes keeps
    the rounded corner at the other end untouched.
    """
    b = bbox(paths)
    out = clone_all(paths)
    for p in out:
        for n in p.nodes:
            if abs(n.position.x - b[2]) < 1.0:
                n.position = Point(x, n.position.y)
    return out


# L's corner is a circular quarter-arc: its control points sit at 0.43 of the
# radius from the corner, against 0.448 for a true circle. So the face's
# corner can be regenerated at any radius without inventing its curvature.
KAPPA = 0.5523


def arc_to(x0, y0, x1, y1, cx, cy):
    """Quarter-arc from (x0,y0) to (x1,y1) bending around corner (cx,cy)."""
    return [node(x0 + (cx - x0) * KAPPA, y0 + (cy - y0) * KAPPA, OFFCURVE),
            node(x1 + (cx - x1) * KAPPA, y1 + (cy - y1) * KAPPA, OFFCURVE),
            node(x1, y1, CURVE, True)]


def corner_radius(pr):
    """The face's own outer corner radius, read off L."""
    ns = list(pr.paths("L")[0].nodes)
    ys = [n.position.y for n in ns]
    xs = [n.position.x for n in ns]
    # L's outer corner runs from its lowest-left node up the spine
    return max(ys[8] - min(ys), 1.0) if len(ns) > 8 else 0.15 * pr.cap


def inner_radius(pr):
    """The face's own INNER corner radius at the same turn, read off L.

    Not the outer radius minus the stroke. At ExtraBold that subtraction goes
    negative -- L's outer sweep is 122 against a 161 stem -- and the face does
    not answer by squaring the corner off: it holds 20 units of turn. Reading
    the value rather than deriving it gets both masters right, 78 and 20.
    """
    ns = list(pr.paths("L")[0].nodes)
    if len(ns) <= 5:
        return 4.0
    return max(abs(ns[2].position.x - ns[5].position.x), 1.0)
