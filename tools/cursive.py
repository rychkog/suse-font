"""What is the cursive г and д actually made of?

    ./venv/bin/python tools/cursive.py

Two letters in the Cyrillic italic have no counterpart in either script, and
the temptation is to name a Latin glyph they resemble and splice it. That has
now been tried twice and been wrong twice -- `2` for г, `g` for д -- which is
METHOD F13 arriving from the side it is easiest to miss: a shape that LOOKS
like a letter is not that letter, and a donor named by resemblance carries
none of the reasons the donor has its shape.

So this reads the reference instead of naming one. Each face's г and д is
rasterised UN-SHEARED, the distance transform is taken, and the ridge of that
transform -- every pixel as far from the edge as anything near it -- is the
letter's skeleton: the path a broad-nib pen walked, with the stroke thickness
divided out. What the skeleton shows is the construction, and it is the only
thing worth carrying across from another face, because the weight, the
terminals and the fitting all have to be this face's own.

Everything is normalised to the reference's own x-height, so the numbers
transfer: x and y are in x-heights, with the baseline at 0.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import math                                                    # noqa: E402

import numpy as np                                             # noqa: E402
from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

from weights import edt                                        # noqa: E402

REFS = ("JetBrains Mono", "Consolas", "Lyth Mono", "Ioskeley Tuned", "Lilex")
PX = 220                # tall enough to resolve a skeleton, small enough to be free


def unsheared(path, ch, angle):
    """The glyph's ink, standing up, cropped to itself."""
    f = ImageFont.truetype(path, PX)
    im = Image.new("L", (PX * 3, PX * 3), 0)
    ImageDraw.Draw(im).text((PX, PX // 2), ch, font=f, fill=255)
    a = np.asarray(im) > 127
    im.close()
    if not a.any():
        return None
    # shear back about the raster's own baseline row: the pivot only shifts
    # the drawing sideways and every figure below is taken from the ink's box
    t = math.tan(math.radians(angle))
    h, w = a.shape
    out = np.zeros_like(a)
    ys, xs = np.where(a)
    nx = np.round(xs - t * (h - ys)).astype(int)
    ok = (nx >= 0) & (nx < w)
    out[ys[ok], nx[ok]] = True
    ys, xs = np.where(out)
    return out[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def skeleton(a):
    """The ridge of the distance transform -- the letter with its weight
    divided out. Kept broad on purpose: a one-pixel thinning invents junctions
    that the drawing does not have, and what is wanted here is the shape of
    the path, not a graph of it."""
    d = edt(a)
    m = d.max()
    return d >= 0.72 * m, m


def main():
    from panel import italics
    paths = dict(italics())
    rows = []
    for fam in REFS:
        if fam not in paths:
            continue
        from fontTools.ttLib import TTFont
        f = TTFont(paths[fam], fontNumber=0, lazy=True)
        try:
            ang = abs(getattr(f["post"], "italicAngle", 0.0)) or 12.0
            xh = f["OS/2"].sxHeight / (f["head"].unitsPerEm / 1000.0)
        finally:
            f.close()
        for ch in "гд":
            a = unsheared(paths[fam], ch, ang)
            if a is None:
                continue
            sk, m = skeleton(a)
            rows.append((fam, ch, a, sk, m))
    if not rows:
        print("   no reference italics found")
        return

    print("\n   the skeleton, in x-heights -- where the path starts, turns "
          "and ends\n")
    for fam, ch, a, sk, m in rows:
        h, w = a.shape
        ys, xs = np.where(sk)
        # the path's extremes, and where it is at five heights up the letter
        print("   %-16s %s  stroke %.2f of its height, box %.2f wide"
              % (fam, ch, 2.0 * m / h, w / float(h)))
        for f in (0.95, 0.75, 0.5, 0.25, 0.05):
            row = int((1.0 - f) * (h - 1))
            band = xs[(ys >= row - 2) & (ys <= row + 2)]
            if len(band):
                print("       at %.2f up: x %.2f..%.2f"
                      % (f, band.min() / float(h), band.max() / float(h)))
        print()

    # and the picture, because a list of crossings is not a shape
    pad, cw = 18, 220
    W = pad + len(rows) * (cw + pad)
    H = 150 + cw
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    lab = ImageFont.truetype("fonts/ttf/SUSEMono-Regular.ttf", 17)
    d.text((pad, 24), "the cursive г and д with their stroke weight divided "
           "out -- red is the path the pen walked",
           font=ImageFont.truetype("fonts/ttf/SUSEMono-Regular.ttf", 26),
           fill=(170, 30, 30))
    for i, (fam, ch, a, sk, m) in enumerate(rows):
        hh, ww = a.shape
        rgb = np.full((hh, ww, 3), 255, np.uint8)
        rgb[a] = (215, 215, 215)
        rgb[sk] = (200, 30, 30)
        c = Image.fromarray(rgb)
        c.thumbnail((cw, cw), Image.LANCZOS)
        x = pad + i * (cw + pad)
        im.paste(c, (x + (cw - c.width) // 2, 80))
        d.text((x, 80 + cw + 10), "%s %s" % (ch, fam), font=lab,
               fill=(110, 110, 110))
    im.save("tools/out/cursive_skeleton.png")
    print("   wrote tools/out/cursive_skeleton.png")


if __name__ == "__main__":
    main()
