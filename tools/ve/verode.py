"""Radon's в brought to THIS face's weight by moving its own nodes.

Radon cannot be blended to our masters: its в is 18 curve segments at
ExtraLight and 17 at ExtraBold, so it is not an axis, and its lightest wall
comes out about twice our Thin's after fitting. So a drawing is taken whole
and every node is moved along the outline's own normal there, its handles
travelling with it. The outer moves toward its interior and the counters
toward theirs, which for opposite windings is opposite directions, so one
rule thins or thickens the whole ribbon at once.

This is NOT the offset-curve trap of METHOD F25. No edge is created, nothing
is rejoined, and the topology is the donor's throughout.

**The direction comes from the HANDLES, not from the neighbouring nodes.**
Taken as the chord between the two neighbouring on-curve points it is wrong
wherever the outline turns hard -- and this letter turns hardest exactly
where it crosses itself. That put a white notch at the crossing and a nick in
the terminal: *"it looks ugly and fractured"*. Each node has an incoming
direction and an outgoing one, given by the control points either side of it;
the node moves along the MITRE of the two normals, which is the offset a
corner actually needs, capped so a near-cusp cannot throw it to infinity.
"""
import math
import sys
sys.path.insert(0, "tools")
from donor import segments_of, find

LIGHT = "MonaspaceRadon-ExtraLightItalic_1.otf"
BOLD = "MonaspaceRadon-ExtraBoldItalic_1.otf"

# Radon's в reaches a little tail out to the left at mid height -- the entry
# stroke a connecting script draws, which this face does not. Node 11 is where
# it leaves the descending edge and node 16 where it rejoins; the span between
# is the tail. Named, not searched: the reason `cut_at_y` gives.
# The bold draws one node fewer -- 17 against 18 -- and the odd one out is
# node 12, INSIDE the tail. So dropping the tail is also what repairs parity:
# both weights come back with 14 nodes and the same segments in the same
# order, which is the hard constraint two masters have to meet.
TAIL = {LIGHT: (11, 16), BOLD: (11, 15)}
MITRE = 2.5


def nodes_of(contour):
    """On-curve points, and the two handles of the segment reaching each."""
    pts = [contour[0][1][0]]
    hands = [None]
    for kind, ps in contour[1:]:
        if kind == "curve":
            hands.append([ps[0], ps[1]])
            pts.append(ps[2])
        else:
            hands.append(None)
            pts.append(ps[0])
    return pts, hands


def rebuild(pts, hands):
    out = [("start", [pts[0]])]
    for i in range(1, len(pts)):
        h = hands[i]
        out.append(("line", [pts[i]]) if h is None
                   else ("curve", [h[0], h[1], pts[i]]))
    return out


def drop_tail(contour, span):
    """Take the entry tail out, and let the descending edge run straight on."""
    pts, hands = nodes_of(contour)
    a, b = span
    keep_pts = pts[:a + 1] + pts[b:]
    keep_h = hands[:a + 1] + hands[b:]
    # the segment that now reaches node b leaves node a, so it keeps b's own
    # arrival handle and takes a's departure from the first dropped segment
    keep_h[a + 1] = [hands[a + 1][0], hands[b][1]] if hands[b] else None
    return rebuild(keep_pts, keep_h)


def signed_area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1]
                     - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def _unit(dx, dy):
    m = math.hypot(dx, dy)
    return (dx / m, dy / m) if m > 1e-9 else None


def move(contour, d):
    """Move every node `d` toward the contour's own interior."""
    pts, hands = nodes_of(contour)
    n = len(pts)
    s = 1.0 if signed_area(pts) > 0 else -1.0
    shift = []
    for i in range(n):
        hi, ho = hands[i], hands[(i + 1) % n]
        back = hi[1] if hi else pts[(i - 1) % n]
        fwd = ho[0] if ho else pts[(i + 1) % n]
        u = _unit(pts[i][0] - back[0], pts[i][1] - back[1]) \
            or _unit(pts[i][0] - pts[(i - 1) % n][0], pts[i][1] - pts[(i - 1) % n][1])
        v = _unit(fwd[0] - pts[i][0], fwd[1] - pts[i][1]) \
            or _unit(pts[(i + 1) % n][0] - pts[i][0], pts[(i + 1) % n][1] - pts[i][1])
        if u is None or v is None:
            shift.append((0.0, 0.0))
            continue
        n1 = (-s * u[1], s * u[0])
        n2 = (-s * v[1], s * v[0])
        dot = n1[0] * n2[0] + n1[1] * n2[1]
        k = 1.0 + dot
        # a near-cusp sends the mitre to infinity; this face would round it
        k = max(k, 2.0 / MITRE)
        shift.append((d * (n1[0] + n2[0]) / k, d * (n1[1] + n2[1]) / k))
    out = [("start", [(pts[0][0] + shift[0][0], pts[0][1] + shift[0][1])])]
    for i in range(1, n):
        h = hands[i]
        p = (pts[i][0] + shift[i][0], pts[i][1] + shift[i][1])
        if h is None:
            out.append(("line", [p]))
        else:
            a = (h[0][0] + shift[i - 1][0], h[0][1] + shift[i - 1][1])
            b = (h[1][0] + shift[i][0], h[1][1] + shift[i][1])
            out.append(("curve", [a, b, p]))
    return out


def fit(segs, height):
    ys = [p[1] for c in segs for _k, ps in c for p in ps]
    xs = [p[0] for c in segs for _k, ps in c for p in ps]
    k = height / (max(ys) - min(ys))
    x0, y0 = min(xs), min(ys)
    return [[(kind, [((p[0] - x0) * k, (p[1] - y0) * k) for p in ps])
             for kind, ps in c] for c in segs], k


def load(height, which=LIGHT, tail=True):
    segs, _deg = segments_of(find(which), ord("в"))
    if tail:
        segs = [drop_tail(segs[0], TAIL[which])] + segs[1:]
    return fit(segs, height)


if __name__ == "__main__":
    segs, k = load(740.0)
    print("fitted by %.4f; contours %s" % (k, [len(c) for c in segs]))
# Where the bowl's mouth is. Node 3 is the curl's tip and nodes 2 and 4 the
# cap either side of it; nodes 8 and 7 are the descending stroke's inner edge,
# which is what the curl has to reach to close the bowl. Radon leaves it open
# -- that is the script idiom, and this face has no open spiral anywhere.
MOUTH = (2, 4, 8, 7)


def close_bowl(contour, over=0.25):
    """A bridge from the curl's cap across to the descending stroke.

    Its own contour, overlapping both, which is how El, Pe, Sha, д and ґ are
    already built in this family -- the union comes out on the way to the
    font. Drawn as a bar the width of the cap it grows from, so the join has
    no step in it, and run `over` of its own length past the stroke so the
    union has something to bite on rather than a tangency.
    """
    pts, _hands = nodes_of(contour)
    a, b, c, d = (pts[i] for i in MOUTH)
    # the stroke's inner edge, as the line through nodes 8 and 7
    ex, ey = d[0] - c[0], d[1] - c[1]
    m = math.hypot(ex, ey) or 1.0
    ex, ey = ex / m, ey / m
    # how far each cap end has to travel to reach that line, along the cap's
    # own normal -- the direction the curl was already heading
    nx, ny = -ey, ex
    reach = lambda p: ((c[0] - p[0]) * nx + (c[1] - p[1]) * ny)
    far = max(reach(a), reach(b))
    far += over * math.hypot(b[0] - a[0], b[1] - a[1])
    quad = [a, (a[0] + far * nx, a[1] + far * ny),
            (b[0] + far * nx, b[1] + far * ny), b]
    # The bridge must wind the way the letter does. Let into a contour against
    # its winding a bump SUBTRACTS -- that is what took 68 units out of ґ's
    # bar before the tick was made its own contour.
    if (signed_area(quad) > 0) != (signed_area(pts) > 0):
        quad.reverse()
    return [("start", [quad[0]])] + [("line", [q]) for q in quad[1:]]
def _flat(contour, steps=16):
    """The contour as a polyline, for casting rays across the ribbon."""
    pts, hands = nodes_of(contour)
    out = []
    n = len(pts)
    for i in range(1, n):
        p0, p1, h = pts[i - 1], pts[i], hands[i]
        out.append(p0)
        if h:
            for j in range(1, steps):
                t = j / steps
                u = 1 - t
                out.append((u**3 * p0[0] + 3*u*u*t*h[0][0] + 3*u*t*t*h[1][0] + t**3*p1[0],
                            u**3 * p0[1] + 3*u*u*t*h[0][1] + 3*u*t*t*h[1][1] + t**3*p1[1]))
    out.append(pts[-1])
    return out


def across(polys, p, d, skip=6.0, far=4000.0):
    """How thick the ribbon is at `p`, measured along `d`.

    The nearest point on another edge is NOT the width -- a ray cast along the
    normal is (METHOD F25). Crossings closer than `skip` are the node's own
    neighbourhood and are ignored.
    """
    best = far
    qx, qy = p[0] + d[0] * far, p[1] + d[1] * far
    for poly in polys:
        n = len(poly)
        for i in range(n):
            ax, ay = poly[i]
            bx, by = poly[(i + 1) % n]
            r1x, r1y = qx - p[0], qy - p[1]
            s1x, s1y = bx - ax, by - ay
            den = r1x * s1y - r1y * s1x
            if abs(den) < 1e-12:
                continue
            t = ((ax - p[0]) * s1y - (ay - p[1]) * s1x) / den
            u = ((ax - p[0]) * r1y - (ay - p[1]) * r1x) / den
            if 0.0 <= u <= 1.0 and t > 0.0:
                dist = t * far
                if skip < dist < best:
                    best = dist
    return best


def normals(pts, hands, s):
    """Each node's inward normal, taken from its HANDLES.

    The chord between the two neighbouring on-curve points is not the tangent
    at a sharp turn, and this letter's sharpest turns are the loop's tip and
    its crossing. Taken that way the ray at the loop's tip pointed across the
    whole letter and read 181 units where the ribbon is 60.
    """
    n = len(pts)
    out = []
    for i in range(n):
        hi, ho = hands[i], hands[(i + 1) % n]
        back = hi[1] if hi else pts[(i - 1) % n]
        fwd = ho[0] if ho else pts[(i + 1) % n]
        u = _unit(pts[i][0] - back[0], pts[i][1] - back[1])
        v = _unit(fwd[0] - pts[i][0], fwd[1] - pts[i][1])
        if u is None and v is None:
            out.append(None)
            continue
        u = u or v
        v = v or u
        t = _unit(u[0] + v[0], u[1] + v[1]) or u
        out.append((-s * t[1], s * t[0]))
    return out


def shrink(segs, ratio):
    """Thin the whole ribbon to `ratio` of its thickness, modulation intact.

    A flat move takes the same units off a thick stroke and a thin one, so at
    the ratio our Thin needs -- 0.46 of what Radon draws -- the thin parts of
    a modulated donor go to nothing and the letter breaks into pieces:
    *"doesn't look like a single stroke"*. Measured instead, each node moves a
    share of the ribbon's OWN thickness there, so a stroke twice as thick
    gives up twice as much and the drawing keeps its own thicks and thins.
    """
    polys = [_flat(c) for c in segs]
    out = []
    for c in segs:
        pts, hands = nodes_of(c)
        n = len(pts)
        s = 1.0 if signed_area(pts) > 0 else -1.0
        ns = normals(pts, hands, s)
        shift = []
        for i in range(n):
            if ns[i] is None:
                shift.append((0.0, 0.0))
                continue
            nx, ny = ns[i]
            d = across(polys, pts[i], (nx, ny)) * (1.0 - ratio) / 2.0
            shift.append((nx * d, ny * d))
        moved = [("start", [(pts[0][0] + shift[0][0], pts[0][1] + shift[0][1])])]
        for i in range(1, n):
            h = hands[i]
            p = (pts[i][0] + shift[i][0], pts[i][1] + shift[i][1])
            if h is None:
                moved.append(("line", [p]))
            else:
                moved.append(("curve", [
                    (h[0][0] + shift[i - 1][0], h[0][1] + shift[i - 1][1]),
                    (h[1][0] + shift[i][0], h[1][1] + shift[i][1]), p]))
        out.append(moved)
    return out
# The curl, and the stem it has to reach. Nodes 2, 3 and 4 are Radon's inward
# hook -- the open finish a script draws. Nodes 8 and 7 are the stem's inner
# edge, which is what a CLOSED bowl rejoins.
# Only node 3, the hook's TIP, is Radon's open finish. Nodes 2 and 4 are the
# bowl's own shoulders and they stay: taken out with it, the outer edge ran
# from the bowl's right side straight to the stem and the bowl came out a
# wedge rather than a bowl.
CURL = (3,)
STEM = (8, 7)
INTO = 18.0             # how far past the stem's edge the rejoin buries itself


def rejoin(contour, high=0.06, low=0.62):
    """Close the bowl by running its stroke INTO the stem, not across to it.

    Bridged with a straight bar from the curl's cap it read as a second stroke
    laid over the letter -- *"doesn't look like a single stroke"* -- because a
    chord between two curves is the one line in the drawing that continues
    nothing. What a closed cursive в actually does is drop the inward hook:
    the bowl comes round, rises, and merges into the stem it started from.

    So the hook's three nodes go, and the two edges either side of it are
    carried on to the stem's own inner edge, each keeping the handle it
    already had at the bowl end so it leaves exactly as it did before. The
    cut between them lands inside the stem's ink, where the union hides it.
    """
    pts, hands = nodes_of(contour)
    a, b = pts[STEM[0]], pts[STEM[1]]
    e = _unit(b[0] - a[0], b[1] - a[1])
    s = 1.0 if signed_area(pts) > 0 else -1.0
    into = (-s * e[1] * INTO, s * e[0] * INTO)
    span = math.hypot(b[0] - a[0], b[1] - a[1])
    at = lambda t: (a[0] + e[0] * span * t - into[0],
                    a[1] + e[1] * span * t - into[1])
    A, B = at(high), at(low)

    # Each new node's own handle points BACK along the stroke that reaches
    # it. Aimed along the stem instead, it sat past the node it belonged to
    # and folded the curve over itself, which filled the bowl solid.
    def toward(p, q, k=0.35):
        u = _unit(q[0] - p[0], q[1] - p[1]) or (0.0, 0.0)
        L = k * math.hypot(q[0] - p[0], q[1] - p[1])
        return (p[0] + u[0] * L, p[1] + u[1] * L)

    i = CURL[0]
    prev, nxt = pts[i - 1], pts[i + 1]
    keep_p = pts[:i] + [A, B] + pts[i + 1:]
    keep_h = (hands[:i]
              + [[hands[i][0], toward(A, prev)],
                 None,
                 [toward(B, nxt), hands[i + 1][1]]]
              + hands[i + 2:])
    return rebuild(keep_p, keep_h)
def _split(p0, c1, c2, p3, t):
    """de Casteljau: one cubic into two, the curve unchanged."""
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, c = lerp(p0, c1), lerp(c1, c2), lerp(c2, p3)
    d, e = lerp(a, b), lerp(b, c)
    f = lerp(d, e)
    return (a, d, f), (e, c, p3)


def subdivide(contour, n):
    """Every segment into `n` pieces, the drawing bit-identical.

    The node move is exact only AT the nodes; between them a rigidly
    translated handle is not a parallel curve, and Radon draws this letter in
    14 nodes. Measured along the whole edge the ribbon came out 32 to 46 units
    where the donor holds 52 to 64 -- *"why does the stroke have different
    width at different parts"*. Splitting first puts the move's exact points
    close enough together that the drift between them is small.
    """
    if n <= 1:
        return contour
    pts, hands = nodes_of(contour)
    out_p, out_h = [pts[0]], [None]
    for i in range(1, len(pts)):
        p0, p3, h = pts[i - 1], pts[i], hands[i]
        if h is None:
            for j in range(1, n + 1):
                u = j / n
                out_p.append((p0[0] + (p3[0] - p0[0]) * u,
                              p0[1] + (p3[1] - p0[1]) * u))
                out_h.append(None)
            continue
        c1, c2 = h
        a, b = p0, (c1, c2, p3)
        for j in range(n - 1, 0, -1):
            left, right = _split(a, b[0], b[1], b[2], 1.0 / (j + 1))
            out_p.append(left[2])
            out_h.append([left[0], left[1]])
            a, b = left[2], right
        out_p.append(b[2])
        out_h.append([b[0], b[1]])
    return rebuild(out_p, out_h)
def _cut(p0, c1, c2, p3, t):
    """de Casteljau: one cubic into two, exactly."""
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, c = lerp(p0, c1), lerp(c1, c2), lerp(c2, p3)
    d, e = lerp(a, b), lerp(b, c)
    f = lerp(d, e)
    return (c1 and a, d, f), (e, c, p3)


def split(contour, n):
    """Every segment into `n`, on the curve it already is.

    The move is only right AT the nodes: a handle translated rigidly does not
    trace a parallel curve, and the error grows with the square of the
    segment's length. Radon draws this letter in fourteen nodes, so between
    them the drift was most of the stroke -- the ribbon came out 32 to 46
    units where the donor holds 52 to 64. Splitting changes nothing about the
    shape, and it is the only thing that makes the move mean what it says.
    """
    pts, hands = nodes_of(contour)
    out_p, out_h = [pts[0]], [None]
    for i in range(1, len(pts)):
        p0, p3, h = pts[i - 1], pts[i], hands[i]
        if h is None:
            for j in range(1, n + 1):
                t = j / n
                out_p.append((p0[0] + (p3[0] - p0[0]) * t,
                              p0[1] + (p3[1] - p0[1]) * t))
                out_h.append(None)
            continue
        a, b, cur = h[0], h[1], p0
        for j in range(n, 0, -1):
            if j == 1:
                out_p.append(p3)
                out_h.append([a, b])
                break
            (_x, d, f), (e, c, _y) = _cut(cur, a, b, p3, 1.0 / j)
            out_p.append(f)
            out_h.append([_x, d])
            cur, a, b = f, e, c
    return rebuild(out_p, out_h)
