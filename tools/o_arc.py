"""Is the cursive г's arc this face's own o?

    ./venv/bin/python tools/o_arc.py

The hypothesis, and the reason for asking. б was drawn nine times and rejected
nine times, and what finally passed was not a better drawing: it was the
host's own o for the round part with only the new terminal donated. METHOD F11
-- a face's design language lives in its round parts, so the round parts have
to be the host's.

Read that back onto the cursive г and д and they stop being new letters:

    д = o + a hook
    г = the RIGHT SIDE of o, opened, + an entry stroke at the top left

This asks whether the second line is true, because it is a claim about a
shape and not a feeling. Every reference г is rasterised un-sheared, and so is
this face's own italic o; then the outer right edge of each is read at twenty
heights and put in x-heights, so the numbers compare. If the г arcs sit on
o's arc the letter is an assembly and not a drawing. If they do not, г needs a
whole outline donated, which is a much bigger borrow and should be called one.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                             # noqa: E402
from PIL import Image, ImageDraw, ImageFont                    # noqa: E402
from fontTools.ttLib import TTFont                             # noqa: E402

from cursive import unsheared, REFS                            # noqa: E402

OURS = "fonts/ttf/SUSEMono-RegularItalic.ttf"
ROWS = 21


def metrics(path):
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        upm = f["head"].unitsPerEm / 1000.0
        return (abs(getattr(f["post"], "italicAngle", 0.0)) or 12.0,
                f["OS/2"].sxHeight / upm)
    finally:
        f.close()


def edge(a):
    """The outer right edge and the ink's thickness there, at ROWS heights.

    Returned in units of the CROP's own height, which is the x-height plus
    whatever overshoot the letter takes -- the same measure for both letters,
    which is what makes them comparable.
    """
    h, w = a.shape
    out = []
    for i in range(ROWS):
        f = 0.98 - i * (0.96 / (ROWS - 1))
        row = a[int(round((1.0 - f) * (h - 1)))]
        xs = np.where(row)[0]
        if not len(xs):
            out.append((f, None, None))
            continue
        # the RIGHTMOST run, which is the arc even when a stem is present
        r = xs.max()
        lo = r
        while lo - 1 >= 0 and row[lo - 1]:
            lo -= 1
        out.append((f, r / float(h), (r - lo + 1) / float(h)))
    return out


def main():
    from panel import italics
    paths = dict(italics())

    ang, _ = metrics(OURS)
    o = unsheared(OURS, "o", ang)
    eo = edge(o)

    print("\n   the outer right edge, in crop heights (x-height + overshoot)\n")
    print("   %-16s %s" % ("up the letter",
                           " ".join("%.2f" % f for f, _, _ in eo)))
    print("   %-16s %s" % ("our italic o",
                           " ".join("  . " if x is None else "%.2f" % x
                                    for _, x, _ in eo)))

    rows = [("our o", o)]
    for fam in REFS:
        if fam not in paths:
            continue
        ang2, _ = metrics(paths[fam])
        a = unsheared(paths[fam], "г", ang2)
        if a is None:
            continue
        e = edge(a)
        # how far each г's arc sits from o's, over the span they share
        d = [abs(x - y) for (_, x, _), (_, y, _) in zip(e, eo)
             if x is not None and y is not None]
        print("   %-16s %s   | off o by %.3f med, %.3f worst"
              % (fam, " ".join("  . " if x is None else "%.2f" % x
                               for _, x, _ in e),
                 float(np.median(d)) if d else -1,
                 max(d) if d else -1))
        rows.append((fam, a))

    # and the picture: o in grey, each г in red over it, baselines together
    pad, cw = 16, 200
    W = pad + len(rows) * (cw + pad)
    im = Image.new("RGB", (W, 150 + cw), "white")
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype("fonts/ttf/SUSEMono-Regular.ttf", 24)
    lab = ImageFont.truetype("fonts/ttf/SUSEMono-Regular.ttf", 16)
    d.text((pad, 22), "our italic o (grey) under each reference cursive г "
           "(red) -- is the arc the same arc?", font=big, fill=(170, 30, 30))
    for i, (fam, a) in enumerate(rows):
        hh, ww = a.shape
        # put o behind at the same height, right edges together
        oh, ow = o.shape
        sc = hh / float(oh)
        ob = np.asarray(Image.fromarray((o * 255).astype(np.uint8))
                        .resize((max(1, int(ow * sc)), hh),
                                Image.LANCZOS)) > 127
        W2 = max(ww, ob.shape[1])
        rgb = np.full((hh, W2, 3), 255, np.uint8)
        rgb[:, W2 - ob.shape[1]:][ob] = (205, 205, 205)
        sub = rgb[:, W2 - ww:]
        sub[a] = (200, 30, 30)
        c = Image.fromarray(rgb)
        c.thumbnail((cw, cw), Image.LANCZOS)
        im.paste(c, (pad + i * (cw + pad) + (cw - c.width) // 2, 70))
        d.text((pad + i * (cw + pad), 70 + cw + 12), fam, font=lab,
               fill=(110, 110, 110))
    im.save("tools/out/o_arc.png")
    print("\n   wrote tools/out/o_arc.png")


if __name__ == "__main__":
    main()
