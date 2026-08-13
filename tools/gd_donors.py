"""Which face can donate the cursive г and д, and can г stay in the family?

    ./venv/bin/python tools/gd_donors.py

This is the sheet the donor decision was made on, kept because the decision has
to stay checkable against its own evidence. Three rows, each answering one
question, and all three are answered now:

  donors   the OFL italics' г and д. A donor has to be OFL before its shape is
           worth looking at, so Consolas is not here however clean it reads.
           **Lilex leads because it is the donor**, of both letters -- and it
           is CFF, which is why: its г is 16 nodes where Sudo's variable
           TrueType expands to 34. See METHOD F15.
  д        each candidate's д over this face's own italic o. Two forms are
           drawn here and they are different letters, not different fits:
           Sudo's has a DESCENDER, like a g, and the rest are ∂. This face
           draws ∂, which is what rules Sudo out for д however good its г was.
           Roboto Mono keeps the upright and is here to show what that is.
  ours     this face's own italic з and c -- why г could not stay in the
           family, since c bulges the wrong way and mirroring is banned and
           з's lower terminal exits left where г's foot runs right -- then o,
           and г and д as they now stand.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                             # noqa: E402
from PIL import Image, ImageDraw, ImageFont                    # noqa: E402
from fontTools.ttLib import TTFont                             # noqa: E402

from cursive import unsheared                                  # noqa: E402

OURS = "fonts/ttf/SUSEMono-RegularItalic.ttf"
FACE = "fonts/ttf/SUSEMono-Regular.ttf"

# OFL, and drawn in a monospace of comparable colour. Sudo leads because it is
# already the donor of record.
CAND = ("Lilex", "Lyth Mono", "JetBrains Mono", "Ioskeley Tuned",
        "Monaspace Xenon", "Sudo", "Roboto Mono")
CW = 132
# Drawn at SS times the delivered size and resolved down with Lanczos. Pasting
# a glyph raster straight into a cell leaves the raster's own staircase in the
# picture; at three times over it is gone.
SS = 3


def angle(path):
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        return abs(getattr(f["post"], "italicAngle", 0.0)) or 12.0
    finally:
        f.close()


def main():
    from panel import italics
    paths = dict(italics())
    names = [f for f in CAND if f in paths]
    ang = {f: angle(paths[f]) for f in names}
    oa = angle(OURS)
    o = unsheared(OURS, "o", oa)

    rows = [("the OFL candidates' г -- Lilex is the donor of both letters",
             [(f, unsheared(paths[f], "г", ang[f])) for f in names]),
            ("their д, over our own italic o -- Sudo's is the g-form, the "
             "wrong letter here",
             [(f, unsheared(paths[f], "д", ang[f])) for f in names]),
            ("ours: з and c, which could not supply г, then o and the two "
             "letters as they stand",
             [(c, unsheared(OURS, c, oa)) for c in "зcoгд"])]

    pad = 14
    W = pad + max(len(r[1]) for r in rows) * (CW + pad)
    H = len(rows) * (CW + 62) + 70
    im = Image.new("RGB", (W * SS, H * SS), "white")
    d = ImageDraw.Draw(im)
    hd = ImageFont.truetype(FACE, 19 * SS)
    lab = ImageFont.truetype(FACE, 14 * SS)

    for r, (title, cells) in enumerate(rows):
        y = 40 + r * (CW + 62)
        d.text((pad * SS, (y - 26) * SS), title, font=hd, fill=(170, 30, 30))
        for i, (fam, a) in enumerate(cells):
            if a is None:
                continue
            hh, ww = a.shape
            rgb = np.full((hh, ww, 3), 255, np.uint8)
            if r == 1:
                oh, ow = o.shape
                # o at the bowl's own height, sitting on the baseline, left
                # edges together -- the bowl is the letter's left-hand part
                sc = hh / float(oh) * 0.66
                ob = np.asarray(
                    Image.fromarray((o * 255).astype(np.uint8))
                    .resize((max(1, int(ow * sc)), max(1, int(oh * sc))),
                            Image.LANCZOS)) > 127
                bh, bw = ob.shape
                if bh <= hh and bw <= ww:
                    rgb[hh - bh:, :bw][ob] = (200, 200, 200)
            rgb[a] = (30, 30, 30) if r == 2 else (185, 30, 30)
            c = Image.fromarray(rgb)
            c.thumbnail((CW * SS, CW * SS), Image.LANCZOS)
            x = (pad + i * (CW + pad)) * SS
            im.paste(c, (x + (CW * SS - c.width) // 2,
                         y * SS + (CW * SS - c.height) // 2))
            d.text((x, (y + CW + 10) * SS), fam, font=lab, fill=(110, 110, 110))

    im = im.resize((W, H), Image.LANCZOS)
    im.save("tools/out/gd_donors.png")
    print("   wrote tools/out/gd_donors.png")


if __name__ == "__main__":
    main()
