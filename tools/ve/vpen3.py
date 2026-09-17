"""в with the bowl's lid run INTO the loop's underside: the waist is one stroke.

vpen2 aimed the closure at the crossing and left a wedge of white between
lid and loop. Here the closure meets the loop's lower arm part way along,
arriving along it, so from there to the crossing the two share one stroke.
"""
import math
import sys
sys.path.insert(0, "tools")
from PIL import Image
from vspine import raster, spine, branches, to_units
from vstroke import smooth
from verode import load, _unit, LIGHT, BOLD
from vpen import ink
from vpen2 import arclen_cut, measure


def paths(which, height, wide=1.0, cut=200.0, at=0.3, pull=(0.4, 0.4), parts=False):
    segs, _k = load(height, which)
    m, k, org = raster(segs)
    brs, junc = branches(spine(m))
    brs.sort(key=len, reverse=True)
    stretch = lambda ps: [(p[0] * wide, p[1]) for p in ps]
    jr = sum(p[0] for p in junc) / len(junc)
    jc = sum(p[1] for p in junc) / len(junc)
    C = stretch(to_units([(jr, jc)], k, org))[0]
    d = lambda p: math.hypot(p[0] - C[0], p[1] - C[1])
    loop = [C] + smooth(stretch(to_units(brs[0], k, org)), step=6, closed=False) + [C]
    sweep = stretch(to_units(brs[1], k, org))
    if d(sweep[0]) > d(sweep[-1]):
        sweep = sweep[::-1]
    sweep = arclen_cut([C] + smooth(sweep, step=6, closed=False), cut)
    # the lower arm: the loop walked from C along whichever end climbs less
    arm = loop if loop[3][1] < loop[-4][1] else loop[::-1]
    # the loop's far tip is its point furthest from C; `at` is a share of that
    far = max(range(len(arm)), key=lambda i: d(arm[i]))
    j = max(2, int(at * far))
    L = arm[j]
    back = _unit(arm[j - 2][0] - arm[j + 2][0], arm[j - 2][1] - arm[j + 2][1])
    e = sweep[-1]
    t = _unit(e[0] - sweep[-3][0], e[1] - sweep[-3][1])
    span = math.hypot(L[0] - e[0], L[1] - e[1])
    p1 = (e[0] + t[0] * span * pull[0], e[1] + t[1] * span * pull[0])
    p2 = (L[0] - back[0] * span * pull[1], L[1] - back[1] * span * pull[1])
    arc = []
    for i in range(1, 41):
        s = i / 40.0
        r = 1 - s
        arc.append((r**3 * e[0] + 3*r*r*s * p1[0] + 3*r*s*s * p2[0] + s**3 * L[0],
                    r**3 * e[1] + 3*r*r*s * p1[1] + 3*r*s*s * p2[1] + s**3 * L[1]))
    if parts:
        return C, arm, j, sweep + arc
    # from L to the crossing the lid IS the loop's arm, point for point
    return loop, sweep + arc + arm[j - 1::-1]


if __name__ == "__main__":
    tiles = []
    for spec in sys.argv[1:]:
        cut, at, pa, pb = (float(x) for x in spec.split(","))
        loop, bowl = paths(LIGHT, 740.0, 1.0, cut, at, (pa, pb))
        m, k = ink([(loop, False), (bowl, False)], 26.5, px=420.0)
        q1, med, q3, holes = measure(m, k)
        print("%-18s q3/q1 %.2f  counters %d" % (spec, q3 / q1, holes))
        tiles.append(Image.fromarray(((~m) * 255).astype("uint8")))
    W = sum(t.width for t in tiles) + 20 * len(tiles)
    out = Image.new("L", (W, max(t.height for t in tiles)), 255)
    x = 0
    for t in tiles:
        out.paste(t, (x, 0)); x += t.width + 20
    out.save("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
             "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/vpen3.png")
