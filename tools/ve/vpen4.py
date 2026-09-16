"""B with the stem and the loop's left arm drawn as ONE line through the crossing.

In B the stem belongs to the bowl's path and the left arm to the loop's, each
smooth on its own, meeting at the crossing at an angle -- an elbow on the
left edge. Here they are one closed path, the corner replaced by a cubic
tangent to both, and the loop's lower arm ends ON that cubic: ending at the
old corner would push the elbow back out.
"""
import math
import sys
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
from PIL import Image
from verode import _unit, LIGHT
from vpen import ink
from vpen2 import measure
import vpen3

d = lambda p, q: math.hypot(p[0] - q[0], p[1] - q[1])


def cubic(a, ta, b, tb, n=30):
    s = d(a, b) * 0.4
    p1 = (a[0] + ta[0] * s, a[1] + ta[1] * s)
    p2 = (b[0] - tb[0] * s, b[1] - tb[1] * s)
    out = []
    for i in range(1, n):
        u = i / float(n)
        r = 1 - u
        out.append((r**3 * a[0] + 3*r*r*u * p1[0] + 3*r*u*u * p2[0] + u**3 * b[0],
                    r**3 * a[1] + 3*r*r*u * p1[1] + 3*r*u*u * p2[1] + u**3 * b[1]))
    return out


def hit(ring, p, t, skip=30.0):
    """Where the ray from `p` along `t` first crosses the ring."""
    best = None
    n = len(ring)
    for i in range(n):
        a, c = ring[i], ring[(i + 1) % n]
        sx, sy = c[0] - a[0], c[1] - a[1]
        den = t[0] * sy - t[1] * sx
        if abs(den) < 1e-12:
            continue
        s = ((a[0] - p[0]) * sy - (a[1] - p[1]) * sx) / den
        u = ((a[0] - p[0]) * t[1] - (a[1] - p[1]) * t[0]) / den
        if s > skip and 0.0 <= u <= 1.0 and (best is None or s < best):
            best = s
    return (p[0] + t[0] * best, p[1] + t[1] * best)


def paths(which, height, wide=1.0, radius=80.0, straight=False, **b):
    C, arm, j, bowl = vpen3.paths(which, height, wide, parts=True, **b)
    # C -> up the left arm -> over the top -> down the lower arm to L
    up = arm[::-1][:len(arm) - j]
    # ... then back round the bowl the other way: lid, right side, bottom,
    # and up the stem to C. One closed path with the crossing in its middle.
    ring = up + bowl[::-1][1:]
    head = next(i for i, p in enumerate(ring) if d(p, C) > radius)
    tail = next(i for i in range(len(ring) - 1, -1, -1) if d(ring[i], C) > radius)
    a, b_ = ring[tail], ring[head]
    ta = _unit(a[0] - ring[tail - 3][0], a[1] - ring[tail - 3][1])
    tb = _unit(ring[head + 3][0] - b_[0], ring[head + 3][1] - b_[1])
    bridge = cubic(a, ta, b_, tb)
    ring = ring[head:tail + 1] + bridge
    # the lower arm from L toward C, stopped where it reaches the new line
    lower = arm[j::-1]
    if straight:
        # Radon's own underside bends here; a pen stroke from the join to the
        # left line is straight, leaving along the direction the lid arrives
        L = arm[j]
        t = _unit(arm[j - 2][0] - arm[j + 2][0], arm[j - 2][1] - arm[j + 2][1])
        P = hit(ring, L, t)
        return ring, [(L[0] + (P[0] - L[0]) * i / 20.0, L[1] + (P[1] - L[1]) * i / 20.0)
                      for i in range(21)]
    near = min(bridge, key=lambda p: d(p, C))
    k = next(i for i, p in enumerate(lower) if d(p, C) < radius * 0.8)
    return ring, lower[:k] + cubic(lower[k - 1], _unit(lower[k - 1][0] - lower[k - 4][0],
                                                     lower[k - 1][1] - lower[k - 4][1]),
                                   near, _unit(near[0] - lower[k - 1][0],
                                               near[1] - lower[k - 1][1]), n=10) + [near]


if __name__ == "__main__":
    tiles = []
    for r in [float(x) for x in sys.argv[1:]]:
        ring, lower = paths(LIGHT, 740.0, 1.0, r, cut=280.0, at=0.3, pull=(0.3, 0.6))
        m, k = ink([(ring, True), (lower, False)], 26.5, px=420.0)
        q1, med, q3, holes = measure(m, k)
        print("radius %4.0f  q3/q1 %.2f  counters %d" % (r, q3 / q1, holes))
        tiles.append(Image.fromarray(((~m) * 255).astype("uint8")))
    out = Image.new("L", (sum(t.width + 20 for t in tiles), max(t.height for t in tiles)), 255)
    x = 0
    for t in tiles:
        out.paste(t, (x, 0)); x += t.width + 20
    out.save("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
             "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/vpen4.png")
