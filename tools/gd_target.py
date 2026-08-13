"""What the cursive г and д actually are, and whether д's bowl is our o.

    ./venv/bin/python tools/gd_target.py

Two rounds were spent reading a SPINE off these letters and stroking it at
constant width, and the result was rejected as terrible. The diagnosis is not
the spine: ink laid along a centreline has no modulation and no terminals, so
it reads as bent wire whatever path it follows. That is the same fault class
that cost б nine drawings, and б's answer is the one to copy -- the host's own
round parts, with only the genuinely new terminal donated.

So this sheet asks the two questions that decide whether that answer applies:

  top     what the reference cursive г and д ARE, alone and un-overlaid.
          г is a top bar, a curve descending to the left, and a foot -- no
          bowl anywhere. д is a bowl with a stroke off its top right rising to
          ascender height.
  bottom  this face's own italic o, un-sheared, under each reference д,
          un-sheared, scaled to the same bowl height. If the bowls sit on it,
          д is `o + one stroke`, which is б's recipe exactly and the smallest
          borrow available. г has no bowl and no host counterpart, so it is
          the case METHOD keeps for a whole-outline donation.

Nothing here is a donor decision -- a donor has to be OFL before it can be one
and Consolas is on this sheet only as a reference.

The row that is NOT here was the first thing tried and it was worse than
useless: our o and each reference г drawn into the same raster, one grey and
one red, to test whether г's curve was o's curve. The composite read as a
double-bowled S and the hypothesis looked confirmed. It was the two letters
being seen as one shape. **Overlay to compare two drawings of the SAME letter;
to find out what a letter is, draw it alone.** г has no bowl at all.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                             # noqa: E402
from PIL import Image, ImageDraw, ImageFont                    # noqa: E402
from fontTools.ttLib import TTFont                             # noqa: E402

from cursive import unsheared, REFS                            # noqa: E402

OURS = "fonts/ttf/SUSEMono-RegularItalic.ttf"
FACE = "fonts/ttf/SUSEMono-Regular.ttf"
CW = 150
# Drawn at SS times the delivered size and resolved down with Lanczos -- see
# the note in tools/gd_donors.py.
SS = 3
SCALE = 2


def angle(path):
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        return abs(getattr(f["post"], "italicAngle", 0.0)) or 12.0
    finally:
        f.close()


def tile(rgb, cw=CW * SS):
    c = Image.fromarray(rgb)
    c.thumbnail((cw, cw), Image.LANCZOS)
    return c


def main():
    from panel import italics
    paths = dict(italics())
    names = [f for f in REFS if f in paths]

    o = unsheared(OURS, "o", angle(OURS))
    ours = {ch: unsheared(OURS, ch, angle(OURS)) for ch in "гд"}

    pad = 16
    W = pad + (len(names) + 1) * (CW + pad)
    H = 2 * (CW + 56) + 96
    im = Image.new("RGB", (W * SS, H * SS), "white")
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(FACE, 23 * SS)
    lab = ImageFont.truetype(FACE, 16 * SS)

    d.text((pad * SS, 16 * SS), "the cursive г and д as the references draw "
           "them, and our own italic o (grey) under each д", font=big,
           fill=(170, 30, 30))

    for r, ch in enumerate("гд"):
        y = 60 + r * (CW + 56)
        cells = [("ours, now", ours[ch])] + \
                [(f, unsheared(paths[f], ch, angle(paths[f]))) for f in names]
        for i, (fam, a) in enumerate(cells):
            if a is None:
                continue
            hh, ww = a.shape
            rgb = np.full((hh, ww, 3), 255, np.uint8)
            if ch == "д" and i:
                # o behind, same height, bowls' left edges together
                oh, ow = o.shape
                sc = hh / float(oh) * 0.62
                ob = np.asarray(
                    Image.fromarray((o * 255).astype(np.uint8))
                    .resize((max(1, int(ow * sc)), max(1, int(oh * sc))),
                            Image.LANCZOS)) > 127
                bh, bw = ob.shape
                if bh <= hh and bw <= ww:
                    reg = rgb[hh - bh:, :bw]
                    reg[ob] = (205, 205, 205)
            rgb[a] = (30, 30, 30) if not i else (185, 30, 30)
            c = tile(rgb)
            x = (pad + i * (CW + pad)) * SS
            im.paste(c, (x + (CW * SS - c.width) // 2,
                         y * SS + (CW * SS - c.height) // 2))
            d.text((x, (y + CW + 12) * SS), "%s %s" % (ch, fam), font=lab,
                   fill=(110, 110, 110))

    im = im.resize((W * SCALE, H * SCALE), Image.LANCZOS)
    im.save("tools/out/gd_target.png")
    print("   wrote tools/out/gd_target.png")


if __name__ == "__main__":
    main()
