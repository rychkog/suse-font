"""The ribbon's width all the way along it, not just at the nodes.

Fourteen samples is one per node and it read 56-63, which said monolinear.
The user reads the whole edge, so the whole edge gets measured: the outline
is walked at a fine step, a ray is cast across at each point, and the spread
is what matters -- a stroke that is 40 in one place and 70 in another reads
as two different strokes however tidy the nodes are.
"""
import math
import sys
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
from verode import load, move, rejoin, _flat, across, LIGHT, BOLD


def walk(contour, step=6.0):
    """Points along the contour, evenly spaced, with the direction there."""
    poly = _flat(contour, 24)
    out, carry = [], 0.0
    for i in range(len(poly) - 1):
        ax, ay = poly[i]
        bx, by = poly[i + 1]
        seg = math.hypot(bx - ax, by - ay)
        if seg < 1e-9:
            continue
        t = carry
        while t < seg:
            u = t / seg
            out.append(((ax + (bx - ax) * u, ay + (by - ay) * u),
                        ((bx - ax) / seg, (by - ay) / seg)))
            t += step
        carry = t - seg
    return out


def spread(segs, label):
    polys = [_flat(c, 24) for c in segs]
    from verode import nodes_of, signed_area
    pts, _h = nodes_of(segs[0])
    s = 1.0 if signed_area(pts) > 0 else -1.0
    ws = []
    for p, d in walk(segs[0]):
        n = (-s * d[1], s * d[0])
        w = across(polys, p, n)
        if w < 400.0:
            ws.append(w)
    ws.sort()
    q = lambda f: ws[int(f * (len(ws) - 1))]
    print("  %-26s %d samples   min %3.0f  q1 %3.0f  med %3.0f  q3 %3.0f  "
          "max %3.0f   spread %.2f"
          % (label, len(ws), ws[0], q(.25), q(.5), q(.75), ws[-1],
             ws[-1] / ws[0] if ws[0] else 0))


if __name__ == "__main__":
    print("ribbon width along the whole outline:")
    segs, _k = load(740.0, LIGHT, tail=False)
    spread(segs, "Radon light, as drawn")
    segs, _k = load(740.0, LIGHT)
    spread(segs, "tail off")
    m = [move(c, 16.0) for c in segs]
    spread(m, "eroded to our Thin")
    spread([rejoin(m[0])] + m[1:], "and rejoined")
    segs, _k = load(730.0, BOLD)
    spread(segs, "Radon bold, tail off")
    m = [move(c, -10.0) for c in segs]
    spread([rejoin(m[0])] + m[1:], "grown to our ExtraBold")
