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


def taper(paths, x_pivot, y0, y1, k0, k1=1.0):
    """`slant`'s sibling: squeeze horizontally by a factor that runs with height.

    `slant` displaces x by height; this scales it. About the vertical line
    `x_pivot`, every point is pulled toward that line by `k0` at `y0` easing
    to `k1` at `y1`, and held at the end values beyond both.

    It exists because an ellipse and a written loop end differently. Refitting
    the round letter to a tall box gives a shape that is rounded at BOTH ends,
    and the italic в's loop is not: it is full width where the pen turns at
    the top and comes to a point where it crosses itself at the bottom. Three
    constructions failed on that one difference -- the loop's wide bottom sat
    on the bowl and read as a figure 8, then dipped inside it and cut its
    counter in two. Tapered, the bottom is narrow enough to run down the
    bowl's own wall, which is where the reference puts it.

    The walls thin with the rest, which is what a pen does and what keeping
    them parallel would not.
    """
    span = (y1 - y0) or 1.0

    def fn(x, y):
        t = (y - y0) / span
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        k = k0 + (k1 - k0) * t
        return x_pivot + (x - x_pivot) * k, y

    return _map_points(paths, fn)


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


def _segments(p):
    """(start node, offcurves, end node) per segment, and each start's index."""
    ns = list(p.nodes)
    on = [i for i, n in enumerate(ns) if str(n.type) != OFFCURVE]
    segs = []
    for k, i in enumerate(on):
        j = on[(k + 1) % len(on)]
        off = ns[i + 1:j] if j > i else ns[i + 1:] + ns[:j]
        segs.append((ns[i], list(off), ns[j]))
    return segs, on


def _meets_y(seg, y, steps=24):
    """Parameters at which this segment crosses height y."""
    p0, off, p1 = seg
    if off:
        a, b = off[0].position.y, off[1].position.y
        y0, y1 = p0.position.y, p1.position.y
        at = lambda t: (y0 * (1 - t) ** 3 + 3 * a * t * (1 - t) ** 2
                        + 3 * b * t * t * (1 - t) + y1 * t ** 3)
    else:
        y0, y1 = p0.position.y, p1.position.y
        at = lambda t: y0 + (y1 - y0) * t
    out = []
    for i in range(steps):
        lo, hi = i / steps, (i + 1) / steps
        if (at(lo) - y) * (at(hi) - y) >= 0:
            continue
        for _ in range(40):
            mid = (lo + hi) / 2.0
            if (at(lo) - y) * (at(mid) - y) <= 0:
                hi = mid
            else:
                lo = mid
        out.append((lo + hi) / 2.0)
    return out


def meets_line(seg, x_at, steps=48):
    """Parameters at which this segment crosses the line x = x_at(y).

    `_meets_y`'s sibling, and the same bisection. What differs is that the
    thing being crossed leans: a flat cut can be found from y alone, a
    stroke's own edge cannot, and a turn grafted onto a stroke has to land on
    one.
    """
    p0, off, p1 = seg
    pts = [(n.position.x, n.position.y) for n in [p0] + off + [p1]]
    if len(pts) == 4:
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
        at = lambda t: (
            (1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * x1
            + 3 * (1 - t) * t * t * x2 + t ** 3 * x3,
            (1 - t) ** 3 * y0 + 3 * (1 - t) ** 2 * t * y1
            + 3 * (1 - t) * t * t * y2 + t ** 3 * y3)
    else:
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        at = lambda t: (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
    f = lambda t: (lambda q: q[0] - x_at(q[1]))(at(t))
    out = []
    for i in range(steps):
        lo, hi = i / steps, (i + 1) / steps
        if (f(lo)) * (f(hi)) >= 0:
            continue
        for _ in range(40):
            mid = (lo + hi) / 2.0
            if f(lo) * f(mid) <= 0:
                hi = mid
            else:
                lo = mid
        out.append((lo + hi) / 2.0)
    return out


def _split_seg(seg, t):
    """de Casteljau: the piece of this segment before t, and the piece after."""
    p0, off, p1 = seg
    if not off:
        x = p0.position.x + (p1.position.x - p0.position.x) * t
        y = p0.position.y + (p1.position.y - p0.position.y) * t
        return (p0, [], node(x, y)), (node(x, y), [], p1)
    pts = [(n.position.x, n.position.y) for n in [p0] + off + [p1]]
    lerp = lambda u, v: (u[0] + (v[0] - u[0]) * t, u[1] + (v[1] - u[1]) * t)
    q = [lerp(pts[i], pts[i + 1]) for i in range(3)]
    r = [lerp(q[0], q[1]), lerp(q[1], q[2])]
    s = lerp(r[0], r[1])
    mid = node(s[0], s[1], CURVE)
    return ((p0, [node(*q[0], OFFCURVE), node(*r[0], OFFCURVE)], mid),
            (node(s[0], s[1], CURVE),
             [node(*r[1], OFFCURVE), node(*q[2], OFFCURVE)], p1))


def cut_at_y(p, y, back, fwd):
    """Cut a contour off flat at height y, dropping the run between two edges.

    `cut_span` cuts at node boundaries, which is only as fine as the donor was
    drawn. This cuts where the ink actually reaches the height: the segment
    leaving node `back` and the segment leaving node `fwd` are split where each
    crosses y, everything between them in contour order goes, and the two ends
    are joined by a straight edge -- the terminal.

    Both edges are named, not searched for. A stroke that doubles back crosses
    the same height several times -- и's foot crosses it going out, coming back
    and going out again -- so "the first crossing" is whichever fold of the
    letter happens to be nearest, which is not a thing a recipe can mean.
    """
    segs, on = _segments(p)
    ib, ia = on.index(back), on.index(fwd)
    n = len(segs)
    tb, ta = _meets_y(segs[ib], y), _meets_y(segs[ia], y)
    if not tb or not ta or ib == ia:
        return clone(p)
    kept = [_split_seg(segs[ia], min(ta))[1]]
    i = (ia + 1) % n
    while i != ib:
        kept.append(segs[i])
        i = (i + 1) % n
    kept.append(_split_seg(segs[ib], max(tb))[0])

    out = []
    for p0, off, _ in kept:
        out.append(node(p0.position.x, p0.position.y, p0.type, p0.smooth))
        out.extend(node(q.position.x, q.position.y, OFFCURVE) for q in off)
    # the last segment has no successor to supply its end node, and that node
    # is one END of the terminal -- left out, the contour closes from a donor
    # node instead and the cut is a slope pinned to the donor rather than the
    # flat edge asked for
    end = kept[-1][2]
    out.append(node(end.position.x, end.position.y, end.type, end.smooth))
    # the edge closing the contour is the terminal, and it is straight
    out[0].type = LINE
    out[0].smooth = False
    return path(out, True)


def cut_along(p, x_at, back, fwd):
    """`cut_at_y`'s sibling, for a terminal that leans.

    Every terminal in this face is cut horizontally, and on an upright stem
    that is the same thing as cutting ACROSS the stroke -- the two readings
    coincide and neither one has to be chosen. On a stroke running any other
    way they come apart, and cutting across the page then leaves a point: the
    cursive г's foot runs out at 28 degrees and its horizontal cut met it at
    34, where this face's own stems meet theirs at 76.

    So the cut is a line rather than a height, and the caller says which line.
    Otherwise this is `cut_at_y` exactly, including naming both edges rather
    than searching for them (F21): the same doubling-back that makes "the
    first crossing" meaningless at a height makes it meaningless at a line.
    """
    segs, on = _segments(p)
    ib, ia = on.index(back), on.index(fwd)
    n = len(segs)
    tb, ta = meets_line(segs[ib], x_at), meets_line(segs[ia], x_at)
    if not tb or not ta or ib == ia:
        # `cut_at_y` hands back the uncut contour here, which is right for a
        # height that a letter simply does not reach. A leaning cut that
        # misses is a construction that did not happen, and shipping the
        # donor's own terminal instead is the silent fallback ґ was nearly
        # caught by. Loud.
        raise ValueError("cut_along: the cut misses an edge it was named")
    kept = [_split_seg(segs[ia], min(ta))[1]]
    i = (ia + 1) % n
    while i != ib:
        kept.append(segs[i])
        i = (i + 1) % n
    kept.append(_split_seg(segs[ib], max(tb))[0])

    out = []
    for p0, off, _ in kept:
        out.append(node(p0.position.x, p0.position.y, p0.type, p0.smooth))
        out.extend(node(q.position.x, q.position.y, OFFCURVE) for q in off)
    end = kept[-1][2]
    out.append(node(end.position.x, end.position.y, end.type, end.smooth))
    out[0].type = LINE
    out[0].smooth = False
    return path(out, True)


def seg_at(seg, t):
    """A point on a segment and the direction the outline runs there."""
    p0, off, p1 = seg
    pts = [(q.position.x, q.position.y) for q in [p0] + off + [p1]]
    if len(pts) == 4:
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
        at = lambda u: (
            (1 - u) ** 3 * x0 + 3 * (1 - u) ** 2 * u * x1
            + 3 * (1 - u) * u * u * x2 + u ** 3 * x3,
            (1 - u) ** 3 * y0 + 3 * (1 - u) ** 2 * u * y1
            + 3 * (1 - u) * u * u * y2 + u ** 3 * y3)
    else:
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        at = lambda u: (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u)
    e = 1e-4
    a, b = at(max(0.0, t - e)), at(min(1.0, t + e))
    return at(t), (b[0] - a[0], b[1] - a[1])


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


def arc_to(x0, y0, x1, y1, cx, cy, k=KAPPA):
    """Quarter-arc from (x0,y0) to (x1,y1) bending around corner (cx,cy)."""
    return [node(x0 + (cx - x0) * k, y0 + (cy - y0) * k, OFFCURVE),
            node(x1 + (cx - x1) * k, y1 + (cy - y1) * k, OFFCURVE),
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
