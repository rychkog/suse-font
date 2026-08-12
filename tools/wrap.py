"""How evenly a stroke wraps the end of a bowl.

    ./venv/bin/python tools/wrap.py            # every bowl, both masters
    ./venv/bin/python tools/wrap.py в ь b o    # only these

A counter is not a shape with proportions of its own -- it is the far side of
a stroke, and the outer is the near side. Give the two ends different curves
and the stroke between them stops being a stroke: it swells at the shoulder
where the eye is at its most sensitive, which reads as a lump long before
anything the gates take moves. Nothing else here measures it. в's counters
were given b's own share of their own box, landed every reading `soft.py`
takes at 1.000, and were turned down by eye for exactly this.

The reading: walk the counter's own outline over the end of the bowl -- the
stretch whose outward normal is within 70 degrees of horizontal, which is the
arc and none of the flat -- and take the distance from each step of it to the
outer contour. That distance IS the stroke there.

The number to read is the BULGE: the thickest place over the end, against the
stroke at the extreme. A bowl whose counter is the outer offset inward holds
1.0, and this face holds it dead -- b, o, p and б all read 1.00-1.01 at both
masters, ь ъ ы 1.00, and в 1.00 at Thin as approved. With b's share of the
counter's own box in it в read 1.32 and 1.23, and that was seen and turned
down. Past about 1.15 the eye has something to find.

d and q read 1.36 on the side away from their bowl, which is the stem's own
junction and not a bowl end -- read the side the letter's bowl is on.

The thinnest place is printed beside it but is NOT the headline: on a letter
with a waist the nearest outline to the end of a lobe can be the notch between
the lobes rather than the wall opposite, which shows up as a pinch that is not
in the stroke at all.

Walking the counter's outline, rather than casting rays from its middle, is
what makes the reading independent of how tall the counter is -- a lobe half
the letter high and a bowl the whole of it are read the same way.

Both sides are printed. On b it is the right that is the bowl and the left
that is flat against the stem; on d and q it is the other way about.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                            # noqa: E402
import glyphsLib                                              # noqa: E402

from params import Params, Lower                              # noqa: E402
import preview as PV                                          # noqa: E402
import recipes as RU                                          # noqa: E402

# The bowls this face has, ours first and the donors last. A name that is not
# a recipe is taken as the face's own Latin, which is what the donors are.
BOWLS = ("в", "ь", "ъ", "ы", "б", "b", "d", "p", "q", "o")
NAMES = {"в": "ve-cy", "ь": "softsign-cy", "ъ": "hardsign-cy",
         "ы": "yeru-cy", "б": "be-cy"}

BAND = np.cos(np.deg2rad(70.0))   # how much of the end counts as the end


def contours(paths):
    """(outer, counters) as point arrays, the overlaps already resolved."""
    polys = [np.asarray(p, float)
             for p in PV.flatten_rec(PV.unioned(paths), 64) if len(p) > 3]
    box = [(p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max())
           for p in polys]
    inside = [any(o[0] < b[0] and o[1] < b[1] and o[2] > b[2] and o[3] > b[3]
                  for j, o in enumerate(box) if j != i)
              for i, b in enumerate(box)]
    outer = max((p for p, ins in zip(polys, inside) if not ins),
                key=lambda p: len(p))
    return outer, [p for p, ins in zip(polys, inside) if ins]


def to_outer(pts, outer):
    """Distance from each point to the outer contour, segments not nodes.

    Nodes alone read a chord where the outline holds a curve -- the same trap
    as measuring a bowl off its control points.
    """
    a = outer
    ab = np.roll(outer, -1, axis=0) - a
    den = (ab * ab).sum(1)
    den[den == 0] = 1.0
    out = np.empty(len(pts))
    for i, p in enumerate(pts):
        t = np.clip(((p - a) * ab).sum(1) / den, 0.0, 1.0)
        d = p - (a + t[:, None] * ab)
        out[i] = np.sqrt((d * d).sum(1).min())
    return out


def ends(counter, outer):
    """(left, right) readings of the stroke over each end of the bowl."""
    mid = (counter + np.roll(counter, -1, axis=0)) / 2.0
    edge = np.roll(counter, -1, axis=0) - counter
    n = np.stack([edge[:, 1], -edge[:, 0]], 1)
    ln = np.hypot(n[:, 0], n[:, 1])
    n, mid = n[ln > 1e-9] / ln[ln > 1e-9, None], mid[ln > 1e-9]
    # point the normal away from the counter, whichever way the contour runs
    away = np.sign(((mid - counter.mean(0)) * n).sum(1))
    n = n * np.where(away == 0, 1.0, away)[:, None]
    out = []
    for side in (-1.0, 1.0):
        sel = n[:, 0] * side >= BAND
        if sel.sum() < 4:
            out.append(None)
            continue
        d = to_outer(mid[sel], outer)
        # the extreme is where the normal is most nearly horizontal
        at = d[np.argmax(n[sel][:, 0] * side)]
        out.append((at, d.max(), d.min(), d.max() / max(at, 1e-6)))
    return out


def main():
    font = glyphsLib.load(open("sources/SUSEMono.glyphs"))
    want = [a for a in sys.argv[1:] if not a.startswith("-")] or list(BOWLS)
    for mi, tag in ((0, "Thin"), (1, "ExtraBold")):
        pr = Params(font, mi)
        low = Lower(pr)
        print(tag)
        for ch in want:
            fn = RU.RECIPES.get(NAMES.get(ch, ""))
            outer, cs = contours(fn(pr) if fn else low.paths(ch))
            for i, c in enumerate(sorted(cs, key=lambda p: -p[:, 1].mean())):
                for side, r in zip(("left ", "right"), ends(c, outer)):
                    if r is None:
                        continue
                    print("   %-3s bowl %d %s   at the extreme %5.1f  "
                          "thickest %5.1f  thinnest %5.1f   BULGE %.2f"
                          % (ch, i, side, *r))


if __name__ == "__main__":
    main()
