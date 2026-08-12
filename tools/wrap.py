"""How evenly the ink runs where a stroke wraps the end of a bowl.

    ./venv/bin/python tools/wrap.py             # every bowl, both masters
    ./venv/bin/python tools/wrap.py в --draw    # and the even-stroke counter
                                                # drawn over the letter

A counter is not a shape with proportions of its own -- it is the far side of
a stroke, and the outer is the near side. Give the two ends different curves
and the stroke between them stops being a stroke: it swells at the shoulder,
where the eye is at its most sensitive, long before anything the gates take
moves. в's counters were once given b's own share of their own box, landed
every reading `soft.py` takes at 1.000, and were turned down by eye for
exactly this. Nothing else here measures it.

**Read the ink, not either outline.** Both outlines lie about this, in
opposite directions, and both were tried first:

- From the counter's side a square counter has no diagonal to stand on -- its
  outline is two flats and a corner -- so it reads perfectly even however
  round the outer it sits in.
- From the outer's side the nearest point on a square counter slides round
  that corner as the normal turns, so the distance stays flat and the reading
  is blind again.

The disc is neither: the widest circle that fits in the ink at the bowl's end,
which is what the eye reads as mass and does not care which outline put it
there. Reported as MASS -- that disc over the stroke straight out from the
counter's own middle. A single bowl in this face holds 1.00-1.03 at both
masters -- b, o, p, б, ь, ъ, ы all do. A TWO-LOBE letter carries more, because
the junction between the lobes is mass at the end of both: the face's own B
reads 1.22 and 1.20 at Thin, and в 1.09. The в that was shown and rejected
read **1.55**.

`--draw` writes the other half of the answer: the counter an even stroke would
leave, got by taking the whole stroke off the silhouette -- a pen as wide as
the side stroke and as tall as the roof -- and cutting the waist bar out of
what is left. No radius is chosen by anybody in that, so laid over the letter
it says whether a square-looking counter is a construction or the room.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                            # noqa: E402
import glyphsLib                                              # noqa: E402
from PIL import Image, ImageDraw, ImageChops                  # noqa: E402

from params import Params, Lower                              # noqa: E402
import preview as PV                                          # noqa: E402
import recipes as RU                                          # noqa: E402
from weights import edt                                       # noqa: E402

# The bowls this face has, ours first and the donors last. A name that is not
# a recipe is taken as the face's own Latin, which is what the donors are.
# B is the control for в: the face's own two-lobe letter, whose
# junction puts mass at a lobe's end that no single bowl has.
BOWLS = ("в", "ь", "ъ", "ы", "б", "b", "p", "o", "B")
NAMES = {"в": "ve-cy", "ь": "softsign-cy", "ъ": "hardsign-cy",
         "ы": "yeru-cy", "б": "be-cy"}

K = 2.0     # pixels per unit


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
    return outer, sorted([p for p, ins in zip(polys, inside) if ins],
                         key=lambda p: -p[:, 1].mean())


def frame(outer):
    """The raster's size and the mapping into it."""
    x0, y1 = outer[:, 0].min(), outer[:, 1].max()
    w = int((outer[:, 0].max() - x0) * K) + 10
    h = int((y1 - outer[:, 1].min()) * K) + 10
    return w, h, lambda p: (5 + (p[0] - x0) * K, 5 + (y1 - p[1]) * K)


def fill(polys, w, h, T):
    """Even-odd, so counters punch through and the overlaps stay solid."""
    img = Image.new("1", (w, h), 0)
    for p in polys:
        lay = Image.new("1", (w, h), 0)
        ImageDraw.Draw(lay).polygon([T(q) for q in p], fill=1)
        img = ImageChops.logical_xor(img, lay)
    return np.asarray(img)


def strokes(solid, counter, T):
    """(side stroke, roof) of the lobe this counter sits in, off the ink."""
    ymid = (counter[:, 1].min() + counter[:, 1].max()) / 2.0
    row = solid[int(T((0, ymid))[1])]
    x = int(T((counter[:, 0].max(), 0))[0])
    t = (np.nonzero(row)[0].max() - x) / K
    col = solid[:, int(T((counter[:, 0].mean(), 0))[0])]
    th = (int(T((0, counter[:, 1].max()))[1])
          - np.nonzero(col)[0].min()) / K
    return t, th


def mass(ink, D, counter, T):
    """(the stroke at the extreme, the widest disc at the end, their ratio)."""
    top, bot = counter[:, 1].max(), counter[:, 1].min()
    cx = (counter[:, 0].min() + counter[:, 0].max()) / 2.0
    py0, py1 = int(T((0, top))[1]), int(T((0, bot))[1])
    pad = int((py1 - py0) * 0.75)
    sub = np.zeros(D.shape, bool)
    sub[max(0, py0 - pad):py1 + pad, int(T((cx, 0))[0]):] = True
    thick = 2 * D[sub].max() / K
    # straight out from the counter's own middle: cross its edge into the
    # ink, and read the disc halfway across the run
    row = D[int(T((0, (top + bot) / 2.0))[1])]
    a = int(T((cx, 0))[0])
    while a + 1 < len(row) and row[a + 1] == 0:
        a += 1
    b = a + 1
    while b + 1 < len(row) and row[b + 1] > 0:
        b += 1
    at = 2 * row[(a + b) // 2] / K
    return at, thick, thick / max(at, 1e-6)


def ideal(solid, counters, T, w, h):
    """The counter an even stroke would leave: the silhouette with the whole
    stroke taken off it, and the waist bar cut out of what is left."""
    t, th = strokes(solid, counters[0], T)
    small = np.asarray(Image.fromarray((solid * 255).astype("uint8")).resize(
        (w, max(1, int(round(h * t / th)))), Image.NEAREST)) > 127
    d = edt(small)
    out = np.asarray(Image.fromarray(((d >= t * K) * 255).astype("uint8"))
                     .resize((w, h), Image.NEAREST)) > 127
    for a, b in zip(counters, counters[1:]):
        out[int(T((0, a[:, 1].min()))[1]):int(T((0, b[:, 1].max()))[1]) + 1] \
            = False
    return out


def draw(solid, ink, want, path):
    rgb = np.full(solid.shape + (3,), 255, np.uint8)
    rgb[solid] = (218, 218, 218)
    rgb[~ink & solid] = (255, 255, 255)
    edge = (want & ~np.roll(want, 1, 0)) | (want & ~np.roll(want, -1, 0)) \
        | (want & ~np.roll(want, 1, 1)) | (want & ~np.roll(want, -1, 1))
    rgb[edge] = (20, 150, 60)
    Image.fromarray(rgb).save(path)
    print("      wrote", path)


def main():
    font = glyphsLib.load(open("sources/SUSEMono.glyphs"))
    want = [a for a in sys.argv[1:] if not a.startswith("-")] or list(BOWLS)
    for mi, tag in ((0, "Thin"), (1, "ExtraBold")):
        pr = Params(font, mi)
        low = Lower(pr)
        print(tag)
        for ch in want:
            fn = RU.RECIPES.get(NAMES.get(ch, ""))
            paths = fn(pr) if fn else low.paths(ch)
            outer, cs = contours(paths)
            w, h, T = frame(outer)
            solid = fill([outer], w, h, T)
            ink = fill([outer] + cs, w, h, T)
            D = edt(ink)
            for i, c in enumerate(cs):
                at, thick, r = mass(ink, D, c, T)
                print("   %-3s bowl %d   at the extreme %5.1f  thickest %5.1f"
                      "   MASS %.2f" % (ch, i, at, thick, r))
            if "--draw" in sys.argv:
                draw(solid, ink, ideal(solid, cs, T, w, h),
                     "tools/out/wrap_%s_%s.png" % (ch, tag))


if __name__ == "__main__":
    main()
