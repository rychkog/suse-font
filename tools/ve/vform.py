"""в drawn as the copybook draws it, on this face's own o.

The pen's order, read off the reference's arrows: up the loop's right arm,
over the top, DOWN its left arm -- and that same line keeps going as the stem
and as the bowl's left side, one pass -- round the bottom, up the right, and
the lid closes back at the crossing.

So the spine is ONE closed path that crosses itself at the crossing, not a
leaf and an oval sharing a point. Radon's skeleton is gone: the bowl is our
own o's centreline, the stem is the face's own slant, and the only figures
with no Latin source are the loop's lean and the width of its eye.
"""
import math
import sys
sys.path.insert(0, "tools")
from fontTools.pens.recordingPen import RecordingPen
from fontTools.ttLib import TTFont

SLANT = 14.0            # the face's own italic angle
ASC = 730.0             # b and l reach this


from fontTools.pens.basePen import BasePen


class _Flat(BasePen):
    """Contours as polylines. BasePen splits a TrueType chain of quadratics
    at its implied on-curve points; reading the chain as ONE curve of higher
    degree, as `_flatten` did, bent o out of shape."""

    def __init__(self, gs=None, steps=16):
        BasePen.__init__(self, gs)
        self.out, self.steps = [], steps

    def _moveTo(self, p):
        self.out.append([p])

    def _lineTo(self, p):
        self.out[-1].append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._getCurrentPoint()
        for i in range(1, self.steps + 1):
            t = i / float(self.steps)
            r = 1 - t
            self.out[-1].append((r**3 * p0[0] + 3*r*r*t * p1[0] + 3*r*t*t * p2[0] + t**3 * p3[0],
                                 r**3 * p0[1] + 3*r*r*t * p1[1] + 3*r*t*t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self._getCurrentPoint()
        for i in range(1, self.steps + 1):
            t = i / float(self.steps)
            r = 1 - t
            self.out[-1].append((r*r * p0[0] + 2*r*t * p1[0] + t*t * p2[0],
                                 r*r * p0[1] + 2*r*t * p1[1] + t*t * p2[1]))


def _flatten(rp, steps=24):
    """The recorded pen's contours as polylines."""
    out, cur, last = [], [], (0.0, 0.0)
    for op, args in rp.value:
        if op == "moveTo":
            cur, last = [args[0]], args[0]
        elif op == "lineTo":
            cur.append(args[0]); last = args[0]
        elif op in ("curveTo", "qCurveTo"):
            pts = [last] + list(args)
            for i in range(1, steps + 1):
                t = i / float(steps)
                p = pts
                while len(p) > 1:
                    p = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                         for a, b in zip(p, p[1:])]
                cur.append(p[0])
            last = pts[-1]
        elif op == "closePath" and cur:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def _cross(poly, c, ang):
    """How far the ray from `c` at `ang` travels to reach `poly`."""
    dx, dy = math.cos(ang), math.sin(ang)
    best = None
    for a, b in zip(poly, poly[1:] + poly[:1]):
        sx, sy = b[0] - a[0], b[1] - a[1]
        den = dx * sy - dy * sx
        if abs(den) < 1e-12:
            continue
        s = ((a[0] - c[0]) * sy - (a[1] - c[1]) * sx) / den
        u = ((a[0] - c[0]) * dy - (a[1] - c[1]) * dx) / den
        if s > 0 and 0.0 <= u <= 1.0 and (best is None or s < best):
            best = s
    return best


def centreline(path, ch="o", n=360):
    """o's own centreline: half way between its outer edge and its counter.

    Read as a ray cast from the middle rather than as an ellipse fitted to it,
    because the italic o is a sheared round letter and its extremes do not sit
    where an upright's do.
    """
    ft = TTFont(path, lazy=True)
    pen = _Flat(ft.getGlyphSet())
    ft.getGlyphSet()[ft.getBestCmap()[ord(ch)]].draw(pen)
    cs = sorted(pen.out, key=lambda c: -abs(_area(c)))
    outer, counter = cs[0], cs[1]
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    c = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
    out = []
    for i in range(n):
        a = 2.0 * math.pi * i / n
        ro, ri = _cross(outer, c, a), _cross(counter, c, a)
        if ro is None or ri is None:
            continue
        r = (ro + ri) / 2.0
        out.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    ft.close()
    return out


def _area(c):
    return 0.5 * sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(c, c[1:] + c[:1]))


def _cubic(a, ta, la, b, tb, lb, n=26):
    p1 = (a[0] + ta[0] * la, a[1] + ta[1] * la)
    p2 = (b[0] - tb[0] * lb, b[1] - tb[1] * lb)
    out = []
    for i in range(1, n + 1):
        t = i / float(n)
        r = 1 - t
        out.append((r**3 * a[0] + 3*r*r*t * p1[0] + 3*r*t*t * p2[0] + t**3 * b[0],
                    r**3 * a[1] + 3*r*r*t * p1[1] + 3*r*t*t * p2[1] + t**3 * b[1]))
    return out


def _bez(a, p1, p2, b, n=30):
    out = []
    for i in range(1, n + 1):
        t = i / float(n)
        r = 1 - t
        out.append((r**3 * a[0] + 3*r*r*t * p1[0] + 3*r*t*t * p2[0] + t**3 * b[0],
                    r**3 * a[1] + 3*r*r*t * p1[1] + 3*r*t*t * p2[1] + t**3 * b[1]))
    return out


def ring_spine(path, w, att=152.0, lean=24.0, eye=0.42, open_=0.6):
    """The bowl is o entire; the loop stands on it at `att`.

    A straight stem cut across o's own left side and left the bowl reading as
    an egg. Here the crossing sits ON o's centreline and the loop's left arm
    leaves along o's own direction there, so the line runs from the loop's
    top, down, and round the bowl without a seam.
    """
    cl = centreline(path)
    n = len(cl)
    i = int(att / 360.0 * n) % n
    C = cl[i]
    # the way o's own line runs downward past the crossing
    d = _unit(cl[(i + 1) % n][0] - cl[i - 1][0], cl[(i + 1) % n][1] - cl[i - 1][1])
    th = math.radians(lean)
    A = (C[0] + (ASC - w / 2.0 - C[1]) * math.tan(th), ASC - w / 2.0)
    L = math.hypot(A[0] - C[0], A[1] - C[1])
    a = _unit(A[0] - C[0], A[1] - C[1])
    nrm = (a[1], -a[0])                      # the loop's right-hand side
    # Given as control points rather than as a direction and a length: a
    # direction at the crossing wide enough to make the eye opened the loop
    # into a triangle, where the bulge belongs half way up.
    e = eye * L
    P = lambda f, g: (C[0] + a[0] * f * L + nrm[0] * g, C[1] + a[1] * f * L + nrm[1] * g)
    # The apex is a turn, so the two arms meet it with their control points on
    # opposite sides of the axis: both tangents come out across the loop and
    # the top rounds instead of coming to a spike.
    turn = 0.62 * e
    right = _bez(C, P(0.42, e * open_), (A[0] + nrm[0] * turn, A[1] + nrm[1] * turn), A)
    back = _bez(A, (A[0] - nrm[0] * turn, A[1] - nrm[1] * turn),
                (C[0] - d[0] * L * 0.42, C[1] - d[1] * L * 0.42), C)
    bowl = [cl[(i + j) % n] for j in range(n + 1)]
    return [C] + right + back + bowl


def leaf_spine(path, w, att=128.0, neck=40.0, lean=(24.0, 34.0), eye=0.20):
    """The loop as the reference draws it, read row by row off the image.

    Two nearly straight sides, both leaning right, the right one more -- so
    the loop is widest near its top and narrows all the way down. A small
    round turn at the top. The sides merge into a short neck, and below the
    neck the bowl splits off: its left side down, its lid to the right.
    `eye` is the counter at the top as a share of the loop's height; the
    reference holds about a fifth.
    """
    cl = centreline(path)
    n = len(cl)
    i = int(att / 360.0 * n) % n
    K = cl[i]
    d = _unit(cl[(i + 1) % n][0] - cl[i - 1][0], cl[(i + 1) % n][1] - cl[i - 1][1])
    u = (-d[0], -d[1])
    N = (K[0] + u[0] * neck, K[1] + u[1] * neck)
    top = ASC - w / 2.0
    h = top - N[1]
    rt = (w + eye * h) / 2.0                     # the round turn's radius
    # The loop's axis leans at the mean of the two sides; its top is `eye`
    # wide and the sides run from the neck to either end of that. Set from
    # the two side angles alone, the top width ignored `eye` and the loop
    # stayed a sliver.
    ta = math.tan(math.radians((lean[0] + lean[1]) / 2.0))
    ys = top - rt
    X = N[0] + ta * (ys - N[1])
    PL = (X - rt, ys)
    PR = (X + rt, ys)
    half = rt
    A = (X + ta * rt, top)
    kk = 0.5523
    aR = _unit(PR[0] - N[0], PR[1] - N[1])
    aL = _unit(PL[0] - N[0], PL[1] - N[1])
    right = _bez(N, (N[0] + (u[0] + aR[0]) / 2.0 * h * 0.3, N[1] + (u[1] + aR[1]) / 2.0 * h * 0.3),
                 (PR[0] - aR[0] * h * 0.3, PR[1] - aR[1] * h * 0.3), PR)
    over = (_bez(PR, (PR[0] + aR[0] * rt * kk, PR[1] + aR[1] * rt * kk),
                 (A[0] + half * kk, A[1]), A)
            + _bez(A, (A[0] - half * kk, A[1]),
                   (PL[0] + aL[0] * rt * kk, PL[1] + aL[1] * rt * kk), PL))
    left = _bez(PL, (PL[0] - aL[0] * h * 0.3, PL[1] - aL[1] * h * 0.3),
                (N[0] + (u[0] + aL[0]) / 2.0 * h * 0.3, N[1] + (u[1] + aL[1]) / 2.0 * h * 0.3), N)
    down = [(N[0] + (K[0] - N[0]) * j / 8.0, N[1] + (K[1] - N[1]) * j / 8.0) for j in range(1, 9)]
    up = down[::-1][1:] + [N]
    bowl = [cl[(i + j) % n] for j in range(n + 1)]
    return [K] + up + right + over + left + down + bowl


def strip_spine(path, w, att=None, neck=25.0, lean=32.0, eye=0.30, close=0.40, scale=1.0, soft=9, bow=0.0, stop=False, curl=False):
    """The loop as a leaning strip: sides parallel, round at the top.

    Read off the reference, the loop's two sides lean TOGETHER and only close
    toward each other in the lower part; set as two lines fanning from the
    neck they made a triangle with one side upright. So the loop is laid out
    along its own leaning axis, with a half-width that is full for most of
    the length and runs to nothing over the lowest `close` of it.
    `eye` is the counter's width as a share of the axis length.
    """
    cl = centreline(path)
    n = len(cl)
    # `scale` shrinks o about its foot: the same shape, standing on the
    # baseline, leaving the loop more of the height -- the reference's bowl
    # is two fifths of the letter, and Radon's crossing sits well under its
    # x-height too
    xs = [p[0] for p in cl]
    foot = ((min(xs) + max(xs)) / 2.0, min(p[1] for p in cl))
    cl = [(foot[0] + (p[0] - foot[0]) * scale, foot[1] + (p[1] - foot[1]) * scale) for p in cl]
    th = math.radians(lean)
    a = (math.sin(th), math.cos(th))
    tang = lambda j: _unit(cl[(j + 1) % n][0] - cl[j - 1][0], cl[(j + 1) % n][1] - cl[j - 1][1])
    if att is None:
        # where the bowl's own line, run upward, already points along the
        # loop's axis -- so the loop's left side continues it without a kink
        upper_left = range(int(0.25 * n), int(0.5 * n))
        i = min(upper_left, key=lambda j: -(-tang(j)[0] * a[0] - tang(j)[1] * a[1]))
    else:
        i = int(att / 360.0 * n) % n
    K = cl[i]
    d = tang(i)
    N = (K[0] - d[0] * neck, K[1] - d[1] * neck)
    necked = None
    if att is not None and curl:
        # The loop closes on its own ABOVE the bowl: the crossing stays high
        # on the bowl's top-left and a short neck climbs from it, leaving
        # along the bowl's own line and bending into the loop's slant. With
        # the crossing slid down the bowl's side, the loop had to close
        # through the bowl, and the bowl's top stood in for its bottom.
        N = (K[0] + a[0] * neck, K[1] + a[1] * neck)
        necked = _bez(K, (K[0] - d[0] * neck * 0.45, K[1] - d[1] * neck * 0.45),
                      (N[0] - a[0] * neck * 0.45, N[1] - a[1] * neck * 0.45), N, n=12)
    nrm = (a[1], -a[0])
    top = ASC - w / 2.0
    # the axis length L and the width W depend on each other through the
    # round end; two passes settle it
    L = (top - N[1]) / a[1]
    for _ in range(3):
        W = w + eye * L
        L = (top - N[1] - (W / 2.0) * a[1]) / a[1]
    hw = W / 2.0

    # The left side is ONE straight line, from the top down through the
    # crossing into the bowl; only the right side swings in to meet it.
    # Narrowing both sides bent the left one upright near the bottom.
    # The right side closes in STEADILY: the reference's gap shrinks in equal
    # steps all the way down. A flat run then an S-shaped swing near the
    # bottom left an elbow. `close` < 0 keeps the old swing for comparison.
    def right_off(t):
        if close < 0:
            f = min(1.0, t / (-close * L))
            return -hw + 2.0 * hw * (f * f * (3 - 2 * f))
        # `close` >= 1 is the bulge: 1 a straight side, more a convex one --
        # open fast below the top, closing gradually toward the crossing
        u = min(1.0, t / L)
        # `bow` pushes the side outward in its middle only, rounding it
        # without the lower loop crowding the left side as a bigger `close` does
        return -hw + 2.0 * hw * (1.0 - (1.0 - u) ** close) + bow * hw * math.sin(math.pi * u)

    pt = lambda t, o: (N[0] + a[0] * t + nrm[0] * (o + hw), N[1] + a[1] * t + nrm[1] * (o + hw))
    steps = 40
    right = [pt(L * j / steps, right_off(L * j / steps)) for j in range(1, steps + 1)]
    cap = [pt(L + hw * math.sin(math.pi * j / 24), hw * math.cos(math.pi * j / 24))
           for j in range(1, 24)]
    left = [pt(L * j / steps, -hw) for j in range(steps, 0, -1)] + [N]
    down = [(N[0] + (K[0] - N[0]) * j / 6.0, N[1] + (K[1] - N[1]) * j / 6.0) for j in range(1, 7)]
    up = down[::-1][1:] + [N]
    if necked is not None:
        up = necked
        down = necked[::-1][1:] + [K]
    bowl = [cl[(i + j) % n] for j in range(n + 1)]
    # the straight right side meets the round top at a slight angle; soften
    # that one join, holding both ends of the loop where they are
    loop = right + cap + left
    if close >= 0 and soft:
        from vstroke import smooth
        loop = [loop[0]] + smooth(loop, win=soft, step=1, closed=False)[1:-1] + [loop[-1]]
    if not stop:
        return [K] + up + loop + down + bowl
    # With a steeper loop the crossing sits lower on the bowl, and a right
    # side carried on to it cut across the bowl's top and trapped a sliver.
    # So the pen writes the bowl, climbs the left side, turns over the top,
    # and STOPS where the right side reaches the bowl. An open path.
    def inside(q):
        c = False
        for a1, b1 in zip(cl, cl[1:] + cl[:1]):
            if (a1[1] > q[1]) != (b1[1] > q[1]):
                x = a1[0] + (q[1] - a1[1]) * (b1[0] - a1[0]) / (b1[1] - a1[1])
                if x > q[0]:
                    c = not c
        return c
    back = loop[::-1]                    # N, up the left, over, down the right
    mid = len(left) + len(cap)
    end = len(back)
    for j in range(mid, len(back)):
        if inside(back[j]):
            end = j
            break
    tail = []
    if end < len(back):
        a1, b1 = back[end - 1], back[end]
        tail = [((a1[0] + b1[0]) / 2.0, (a1[1] + b1[1]) / 2.0)]
    return bowl + up + back[:end] + tail


def draw_spine(path, w, att=140.0, q=95.0, lean=20.0, W=130.0, scale=0.80,
               drop=0.40, rlean=0.0, pull=0.55, round_=0.32, apex=0.45, soft=0, cap=False):
    """в as the user drew it, measured row by row.

    The bowl is o at `scale`, standing on the baseline. The loop's left side
    is ONE straight line at `lean` from the crossing to the top. Its round
    top turns into a right side that drops near-vertically (`rlean` from
    upright) to its widest point, `drop` of the way down the loop and `W`
    right of the left line, then curves hard left and lands tangent on the
    bowl's top at angle `q`, sharing the bowl's stroke back to the crossing.
    """
    cl = centreline(path)
    n = len(cl)
    xs = [p[0] for p in cl]
    foot = ((min(xs) + max(xs)) / 2.0, min(p[1] for p in cl))
    cl = [(foot[0] + (p[0] - foot[0]) * scale, foot[1] + (p[1] - foot[1]) * scale) for p in cl]
    tang = lambda j: _unit(cl[(j + 1) % n][0] - cl[j - 1][0], cl[(j + 1) % n][1] - cl[j - 1][1])
    i = int(att / 360.0 * n) % n
    iq = int(q / 360.0 * n) % n
    K, Q = cl[i], cl[iq]
    tq = tang(iq)                                # along the bowl toward K
    top = ASC - w / 2.0
    s = math.tan(math.radians(lean))
    X = lambda y: K[0] + s * (y - K[1])
    a = _unit(s, 1.0)
    rt = round_ * W                              # the round top's reach
    PL = (X(top - rt), top - rt)
    A = (PL[0] + apex * W, top)
    yR = top - drop * (top - K[1])
    R = (X(yR) + W, yR)
    rl = math.radians(rlean)
    tR = (-math.sin(rl), -math.cos(rl))          # heading down the right side
    line = [(K[0] + (PL[0] - K[0]) * j / 20.0, K[1] + (PL[1] - K[1]) * j / 20.0)
            for j in range(1, 21)]
    arc1 = _bez(PL, (PL[0] + a[0] * rt * 0.55, PL[1] + a[1] * rt * 0.55),
                (A[0] - (A[0] - PL[0]) * 0.55, A[1]), A, n=16)
    k2 = 0.55 * max(R[0] - A[0], A[1] - R[1])
    arc2 = _bez(A, (A[0] + (R[0] - A[0]) * 0.55, A[1]),
                (R[0] - tR[0] * k2, R[1] - tR[1] * k2), R, n=24)
    if cap:
        # A half-circle top, W across, and the right side dropping straight
        # from its end to the widest point: a long single curve from the apex
        # left the top pointed on its left.
        r0 = W / 2.0
        PL = (X(top - r0), top - r0)
        A = (PL[0] + r0, top)
        RT = (PL[0] + W, top - r0)
        R = (RT[0] + (top - r0 - yR) * math.tan(rl), yR)
        arc1 = _bez(PL, (PL[0], PL[1] + r0 * 0.5523), (A[0] - r0 * 0.5523, A[1]), A, n=16)
        arc2 = (_bez(A, (A[0] + r0 * 0.5523, A[1]), (RT[0], RT[1] + r0 * 0.5523), RT, n=16)
                + [(RT[0] + (R[0] - RT[0]) * j / 10.0, RT[1] + (R[1] - RT[1]) * j / 10.0)
                   for j in range(1, 11)])
        line = [(K[0] + (PL[0] - K[0]) * j / 20.0, K[1] + (PL[1] - K[1]) * j / 20.0)
                for j in range(1, 21)]
    k3 = math.hypot(Q[0] - R[0], Q[1] - R[1]) * pull
    arc3 = _bez(R, (R[0] + tR[0] * k3, R[1] + tR[1] * k3),
                (Q[0] - tq[0] * k3, Q[1] - tq[1] * k3), Q, n=30)
    shared = [cl[j % n] for j in range(iq + 1, i + 1)]
    bowl = [cl[(i + j) % n] for j in range(1, n + 1)]
    # three curves joined at the apex and the widest point bent at their
    # joins; smoothed as one run -- ends held -- the right side is one curve
    run = [PL] + arc1[1:] + arc2 + arc3
    if soft:
        from vstroke import smooth
        run = [run[0]] + smooth(run, win=soft, step=1, closed=False)[1:-1] + [run[-1]]
    return [K] + line + run[1:] + shared + bowl


def pen_spine(path, w, lean=18.0, r=60.0, gap=1.6, vee=35.0, bulge=0.25,
              scale=0.80, l1=0.55, l2=0.40, split=0.0, merge=0.0, full=0.0, psi=0.0, wide=1.0, loopwide=1.0, roundtop=False):
    """в as ONE pen movement, the way the copybook teaches it.

    Start where the loop closes (J). Up the loop's right side, round the top,
    down its left side -- and that line keeps going as the bowl's own left
    side -- round the bowl, over its top, and back into the line at K.

    * The loop's left side IS the bowl's left side run on upward: K is where
      the bowl already travels at `lean`, and the line leaves along it.
    * The bowl's top peels off that line at K, BELOW J; J sits `gap` strokes
      above the bowl's top, so loop and bowl never share a stroke.
    * The top is an exact half-circle of radius `r` in the loop's own
      leaning frame; nothing is smoothed.
    * The right side drops from the circle in one convex curve (`bulge`
      outward) and meets the line at J at `vee` degrees.
    """
    cl = centreline(path)
    n = len(cl)
    xs = [p[0] for p in cl]
    foot = ((min(xs) + max(xs)) / 2.0, min(p[1] for p in cl))
    # `wide` scales the bowl's width on its own: shrunk to `scale` both
    # ways, the bowl lost width the letter needs beside о and а
    cl = [(foot[0] + (p[0] - foot[0]) * scale * wide, foot[1] + (p[1] - foot[1]) * scale)
          for p in cl]
    th = math.radians(lean)
    ax = (math.sin(th), math.cos(th))            # up the loop
    nm = (ax[1], -ax[0])                         # the loop's right-hand side
    tang = lambda j: _unit(cl[(j + 1) % n][0] - cl[j - 1][0], cl[(j + 1) % n][1] - cl[j - 1][1])
    # where the bowl, run upward (against its own direction), points along ax
    i = min(range(int(0.25 * n), int(0.5 * n)),
            key=lambda j: -(-tang(j)[0] * ax[0] - tang(j)[1] * ax[1]))
    K = cl[i]
    btop = max(p[1] for p in cl)
    top = ASC - w / 2.0
    # J: on the line, `gap` strokes above the bowl's top
    tJ = (btop + gap * w - K[1]) / ax[1]
    if split:
        # Close the loop exactly where the bowl's top visibly leaves the
        # line: the first point up the bowl from K that stands `split`
        # strokes off the line. Closing higher left a bare stretch of line
        # between loop and bowl.
        for k in range(1, n // 2):
            p = cl[(i - k) % n]
            off = (p[0] - K[0]) * nm[0] + (p[1] - K[1]) * nm[1]
            if off > split * w:
                tJ = (p[0] - K[0]) * ax[0] + (p[1] - K[1]) * ax[1]
                break
    J = (K[0] + ax[0] * tJ, K[1] + ax[1] * tJ)
    # the half-circle's highest point sits on `top`
    if roundtop and loopwide != 1.0:
        # widen the top as a CIRCLE: stretched across only, it became a
        # half-oval whose flat turn met the left line in a square shoulder
        r = r * loopwide
    tL = (top - r - J[1] - nm[1] * r) / ax[1]
    PL = (J[0] + ax[0] * tL, J[1] + ax[1] * tL)
    Cc = (PL[0] + nm[0] * r, PL[1] + nm[1] * r)
    RT = (PL[0] + 2 * nm[0] * r, PL[1] + 2 * nm[1] * r)
    cap = [(Cc[0] + r * (-math.cos(f) * nm[0] + math.sin(f) * ax[0]),
            Cc[1] + r * (-math.cos(f) * nm[1] + math.sin(f) * ax[1]))
           for f in [math.pi * k / 32.0 for k in range(32, -1, -1)]]   # RT -> PL
    D = math.hypot(RT[0] - J[0], RT[1] - J[1])
    vr = math.radians(vee)
    v = (math.cos(vr) * ax[0] + math.sin(vr) * nm[0], math.cos(vr) * ax[1] + math.sin(vr) * nm[1])
    # J -> RT, leaving J along v, arriving at RT heading up the axis
    right = _bez(J, (J[0] + v[0] * D * l2, J[1] + v[1] * D * l2),
                 (RT[0] - ax[0] * D * l1 + nm[0] * bulge * r, RT[1] - ax[1] * D * l1 + nm[1] * bulge * r),
                 RT, n=40)
    line = [(PL[0] + (K[0] - PL[0]) * k / 40.0, PL[1] + (K[1] - PL[1]) * k / 40.0)
            for k in range(1, 41)]
    bowl = [cl[(i + k) % n] for k in range(1, n + 1)]
    if merge:
        # Landed at an angle, the loop's lower curve ran alongside the bowl's
        # top for a stretch less than a stroke apart and the ink swelled. So
        # it lands ON the bowl's top, `merge` strokes along from the join,
        # travelling the bowl's way, and from there to the join the two are
        # the same points -- the ink is laid once.
        acc, k = 0.0, 0
        while acc < merge * w and k < n // 3:
            a1_, b1_ = cl[(i - k) % n], cl[(i - k - 1) % n]
            acc += math.hypot(b1_[0] - a1_[0], b1_[1] - a1_[1])
            k += 1
        iq = (i - k) % n
        Q = cl[iq]
        tq = tang(iq)                            # along the bowl, toward K
        DQ = math.hypot(RT[0] - Q[0], RT[1] - Q[1])
        if full:
            # A round turn: both handles point at where the two end
            # directions cross, and reach `full` of the way there. The
            # outward push bent the start away from the half-circle and
            # left a notch. Straight down from the circle's half-way point
            # the two directions crossed on the WRONG side and the side went
            # hollow, so the circle carries on `psi` degrees further first.
            ps = math.radians(psi)
            E = (Cc[0] + r * (math.cos(ps) * nm[0] - math.sin(ps) * ax[0]),
                 Cc[1] + r * (math.cos(ps) * nm[1] - math.sin(ps) * ax[1]))
            tE = (-math.sin(ps) * nm[0] - math.cos(ps) * ax[0],
                  -math.sin(ps) * nm[1] - math.cos(ps) * ax[1])
            more = [(Cc[0] + r * (math.cos(g) * nm[0] - math.sin(g) * ax[0]),
                     Cc[1] + r * (math.cos(g) * nm[1] - math.sin(g) * ax[1]))
                    for g in [ps * q / 12.0 for q in range(1, 13)]] if ps > 0 else []
            if ps < 0:
                # stopping SHORT of half-way: drop the cap's last stretch so
                # the side leaves heading down and outward, then swings in
                cut = int(round(-ps / math.pi * 32))
                cap = cap[cut:]
            den = tE[0] * (-tq[1]) - tE[1] * (-tq[0])
            u = ((Q[0] - E[0]) * (-tq[1]) - (Q[1] - E[1]) * (-tq[0])) / den
            P = (E[0] + tE[0] * u, E[1] + tE[1] * u)
            down = more + _bez(E, (E[0] + (P[0] - E[0]) * full, E[1] + (P[1] - E[1]) * full),
                               (Q[0] + (P[0] - Q[0]) * full, Q[1] + (P[1] - Q[1]) * full), Q, n=40)
        else:
            down = _bez(RT, (RT[0] - ax[0] * DQ * l1 + nm[0] * bulge * r,
                             RT[1] - ax[1] * DQ * l1 + nm[1] * bulge * r),
                        (Q[0] - tq[0] * DQ * l2, Q[1] - tq[1] * DQ * l2), Q, n=40)
        shared = [cl[(iq + j) % n] for j in range(1, k + 1)]
        up = line[::-1][1:] + [PL]
        loop = cap[::-1][1:] + down
        if loopwide != 1.0:
            # Widen the WHOLE loop from its left line outward, as the bowl was
            # widened. Raising `r` alone only grew the top circle -- the lower
            # curve lands at a fixed spot on the bowl -- and the loop barely
            # changed. The factor fades to 1 at the landing, so the join holds.
            def grow(q, g):
                o = (q[0] - K[0]) * nm[0] + (q[1] - K[1]) * nm[1]
                return (q[0] + nm[0] * o * (g - 1.0), q[1] + nm[1] * o * (g - 1.0))
            if roundtop:
                # the circle is already wide and the lower curve follows it;
                # swelling that curve as well put a bump under the circle
                pass
            else:
                def ramp(q):
                    f = min(1.0, max(0.0, (q[1] - Q[1]) / max(1.0, top - Q[1])))
                    return 1.0 + (loopwide - 1.0) * (f * f * (3 - 2 * f))
                loop = [grow(q, ramp(q)) for q in loop]
        pen_spine.loop = (1 + len(up), 1 + len(up) + len(loop))
        return [K] + up + loop + shared + bowl
    return [J] + right + cap[1:] + line + bowl


def stem_spine(path, w, lean=18.0, r=60.0, gap=1.6, vee=35.0, bulge=0.25,
               scale=0.80, shift=0.0, bang=250.0, fh=0.9, l1=0.55, l2=0.40):
    """G with the line carried down to the bowl's BOTTOM.

    In G the bowl left the line half way down its own left side. Here the
    line IS the bowl's left side: it runs at `lean`, `shift` left of o's
    leftmost point, and turns into o's own bottom at `bang` degrees through
    a short curve that starts `fh` of that height-gap above it. From there
    o's arc goes round the right side and over the top until it meets the
    line again, and stops. The loop closes on the line `gap` strokes above
    the bowl's top, as in G.
    """
    cl = centreline(path)
    n = len(cl)
    xs = [p[0] for p in cl]
    foot = ((min(xs) + max(xs)) / 2.0, min(p[1] for p in cl))
    cl = [(foot[0] + (p[0] - foot[0]) * scale, foot[1] + (p[1] - foot[1]) * scale) for p in cl]
    th = math.radians(lean)
    ax = (math.sin(th), math.cos(th))
    nm = (ax[1], -ax[0])
    s = math.tan(th)
    lx = min(range(n), key=lambda j: cl[j][0])
    M = (cl[lx][0] - shift, cl[lx][1])
    X = lambda y: M[0] + s * (y - M[1])          # the line's x at height y
    left_of = lambda p: p[0] < X(p[1])
    tang = lambda j: _unit(cl[(j + 1) % n][0] - cl[j - 1][0], cl[(j + 1) % n][1] - cl[j - 1][1])
    ib = int(bang / 360.0 * n) % n
    B = cl[ib]
    F = (X(B[1] + fh * (M[1] - B[1])), B[1] + fh * (M[1] - B[1]))
    dF = math.hypot(B[0] - F[0], B[1] - F[1])
    tb = tang(ib)
    fillet = _bez(F, (F[0] - ax[0] * dF * 0.5, F[1] - ax[1] * dF * 0.5),
                  (B[0] - tb[0] * dF * 0.5, B[1] - tb[1] * dF * 0.5), B, n=20)
    # o's arc from B, round the bottom, up the right, over the top, until it
    # comes back across the line
    arc = []
    k = ib
    for _ in range(n):
        k = (k + 1) % n
        p = cl[k]
        if len(arc) > n // 3 and left_of(p):
            break
        arc.append(p)
    E = arc[-1]
    Xp = (X(E[1]), E[1])                         # onto the line
    btop = max(p[1] for p in cl)
    top = ASC - w / 2.0
    yJ = btop + gap * w
    J = (X(yJ), yJ)
    tL = (top - r - J[1] - nm[1] * r) / ax[1]
    PL = (J[0] + ax[0] * tL, J[1] + ax[1] * tL)
    Cc = (PL[0] + nm[0] * r, PL[1] + nm[1] * r)
    RT = (PL[0] + 2 * nm[0] * r, PL[1] + 2 * nm[1] * r)
    cap = [(Cc[0] + r * (-math.cos(f) * nm[0] + math.sin(f) * ax[0]),
            Cc[1] + r * (-math.cos(f) * nm[1] + math.sin(f) * ax[1]))
           for f in [math.pi * q / 32.0 for q in range(32, -1, -1)]]
    D = math.hypot(RT[0] - J[0], RT[1] - J[1])
    vr = math.radians(vee)
    v = (math.cos(vr) * ax[0] + math.sin(vr) * nm[0], math.cos(vr) * ax[1] + math.sin(vr) * nm[1])
    right = _bez(J, (J[0] + v[0] * D * l2, J[1] + v[1] * D * l2),
                 (RT[0] - ax[0] * D * l1 + nm[0] * bulge * r, RT[1] - ax[1] * D * l1 + nm[1] * bulge * r),
                 RT, n=40)
    line = [(PL[0] + (F[0] - PL[0]) * q / 60.0, PL[1] + (F[1] - PL[1]) * q / 60.0)
            for q in range(1, 61)]
    return [J] + right + cap[1:] + line + fillet + arc + [Xp]


def head_spine(path, w, att=150.0, r=0.70, reach=0.45, q=None):
    """The loop's top is o itself, scaled; only below its middle does it narrow.

    Two free curves gave a teardrop that answered to nothing in the face. The
    face's own stacked letters, 8 and В, carry an upper bowl the same SHAPE as
    the lower at about nine tenths of its size. в has only the ascender's room
    above the bowl, so the head keeps o's shape at `r` of its width and lets
    its lower half run down into the crossing instead.
    `reach` is how far the right side's pull toward the crossing extends.
    """
    cl = centreline(path)
    n = len(cl)
    xs = [p[0] for p in cl]
    ys = [p[1] for p in cl]
    ocx, ocy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    ohh = (max(ys) - min(ys)) / 2.0
    i = int(att / 360.0 * n) % n
    C = cl[i]
    d = _unit(cl[(i + 1) % n][0] - cl[i - 1][0], cl[(i + 1) % n][1] - cl[i - 1][1])
    s = math.tan(math.radians(SLANT))
    top = ASC - w / 2.0
    cy = top - r * ohh                           # the head's own middle
    # the head's left extreme stands on the slant line up from the crossing
    lx = min(range(n), key=lambda j: cl[j][0])
    off = C[0] + s * (cy - C[1]) - (ocx + r * (cl[lx][0] - ocx))
    H = [(ocx + r * (p[0] - ocx) + off, cy + r * (p[1] - ocy)) for p in cl]
    # its upper half, from the right-hand extreme round over the top to the left
    rx = max(range(n), key=lambda j: H[j][0])
    arc = [H[(rx + j) % n] for j in range(((lx - rx) % n) + 1)]
    R, Lp = arc[0], arc[-1]
    tR = _unit(arc[1][0] - arc[0][0], arc[1][1] - arc[0][1])
    tL = _unit(arc[-1][0] - arc[-2][0], arc[-1][1] - arc[-2][1])
    k1 = math.hypot(R[0] - C[0], R[1] - C[1])
    k2 = math.hypot(Lp[0] - C[0], Lp[1] - C[1])
    if q is None:
        right = _bez(C, (C[0] + (R[0] - C[0]) * reach, C[1] + (R[1] - C[1]) * 0.15),
                     (R[0] - tR[0] * k1 * 0.40, R[1] - tR[1] * k1 * 0.40), R)
    else:
        # Crossed, the right side cut down through the bowl's top and left a
        # third counter. So it runs along the bowl's own top from the
        # crossing -- the same points, so no ink is doubled -- and leaves it
        # at `q` to climb to the head, as B3's lid did.
        iq = int(q / 360.0 * n) % n
        shared = [cl[(i - j) % n] for j in range(((i - iq) % n) + 1)]
        Q = shared[-1]
        tq = _unit(shared[-1][0] - shared[-3][0], shared[-1][1] - shared[-3][1])
        kq = math.hypot(R[0] - Q[0], R[1] - Q[1])
        right = shared[1:] + _bez(Q, (Q[0] + tq[0] * kq * reach, Q[1] + tq[1] * kq * reach),
                                  (R[0] - tR[0] * kq * 0.45, R[1] - tR[1] * kq * 0.45), R)
    left = _bez(Lp, (Lp[0] + tL[0] * k2 * 0.40, Lp[1] + tL[1] * k2 * 0.40),
                (C[0] - d[0] * k2 * 0.40, C[1] - d[1] * k2 * 0.40), C)
    bowl = [cl[(i + j) % n] for j in range(n + 1)]
    return [C] + right + arc[1:] + left + bowl


def spine(path, w, lean=24.0, eye=0.42, lid=150.0, bulge=(0.55, 0.20)):
    """One closed path: loop up and over and down, stem, bowl, lid.

    `lean` is how far the loop's axis leans from upright, `eye` its width as a
    share of its own length, `lid` the angle round o at which the lid leaves
    the bowl's arc for the crossing.
    """
    cl = centreline(path)
    top = max(p[1] for p in cl)
    # the point where a line at the face's own slant runs alongside the bowl:
    # from there down, the bowl IS o; above it, the stem replaces o's left side
    s = math.tan(math.radians(SLANT))
    left = [i for i, p in enumerate(cl)
            if cl[(i + 1) % len(cl)][1] < p[1] and p[0] < cl[0][0]]
    i_m = min(left, key=lambda i: abs((cl[(i + 1) % len(cl)][0] - cl[i][0])
                                      - s * (cl[(i + 1) % len(cl)][1] - cl[i][1])))
    M = cl[i_m]
    yC = top
    C = (M[0] + s * (yC - M[1]), yC)
    # the loop
    th = math.radians(lean)
    a = (math.sin(th), math.cos(th))
    nrm = (math.cos(th), -math.sin(th))
    L = (ASC - w / 2.0 - yC) / math.cos(th)
    A = (C[0] + a[0] * L, C[1] + a[1] * L)
    u = (s / math.hypot(s, 1.0), 1.0 / math.hypot(s, 1.0))   # up the stem
    e = eye * L
    right = _cubic(C, (a[0] * 0.5 + nrm[0] * 0.87, a[1] * 0.5 + nrm[1] * 0.87),
                   L * bulge[0], A, (-nrm[0], -nrm[1]), e * 0.9)
    back = _cubic(A, (-nrm[0], -nrm[1]), e * 0.9,
                  C, (-u[0], -u[1]), L * bulge[1])
    # the stem, straight, from the crossing to where the bowl takes over
    stem = [(C[0] + (M[0] - C[0]) * i / 12.0, C[1] + (M[1] - C[1]) * i / 12.0)
            for i in range(1, 13)]
    # o's own arc from there, round the bottom and up the right side
    k = len(cl)
    arc = []
    i = i_m
    while True:
        i = (i + 1) % k
        arc.append(cl[i])
        if i == i_m:
            break
    # the lid leaves o's arc once it has come back up the right side to
    # within `lid` of the bowl's own top; from there it runs to the crossing
    span = top - min(p[1] for p in cl)
    for j, p in enumerate(arc):
        if j > len(arc) // 2 and p[1] > top - lid * span and p[0] > C[0]:
            arc = arc[:j + 1]
            break
    E = arc[-1]
    tE = _unit(E[0] - arc[-4][0], E[1] - arc[-4][1])
    close = _cubic(E, tE, math.hypot(C[0] - E[0], C[1] - E[1]) * 0.45,
                   C, (-u[0], -u[1]), math.hypot(C[0] - E[0], C[1] - E[1]) * 0.35)
    return [C] + right + back + stem + arc + close


def _unit(x, y):
    m = math.hypot(x, y) or 1.0
    return (x / m, y / m)


if __name__ == "__main__":
    from PIL import Image
    from vpen import ink
    from vpen2 import measure
    THIN = "fonts/ttf/SUSEMono-ThinItalic.ttf"
    tiles = []
    for spec in sys.argv[1:]:
        att, lean, eye, op = (float(x) for x in spec.split(","))
        p = ring_spine(THIN, 28.0, att, lean, eye, op)
        m, k = ink([(p, True)], 28.0, px=420.0)
        q1, med, q3, holes = measure(m, k)
        print("%-16s q3/q1 %.2f  counters %d" % (spec, q3 / q1, holes))
        tiles.append(Image.fromarray(((~m) * 255).astype("uint8")))
    out = Image.new("L", (sum(t.width + 20 for t in tiles),
                          max(t.height for t in tiles)), 255)
    x = 0
    for t in tiles:
        out.paste(t, (x, 0)); x += t.width + 20
    out.save("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
             "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/vform.png")
