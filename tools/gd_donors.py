"""Which face can donate the cursive г and д, and can г stay in the family?

    ./venv/bin/python tools/gd_donors.py

Three rows, and each answers one question.

  donors   the OFL italics' г and д. A donor has to be OFL before its shape is
           worth looking at, so Consolas is not here however clean it reads.
           Sudo is first because it is already this project's donor -- б's
           branch is Sudo's, the fitting machinery in `scripts/be_from_sudo.py`
           is already tuned to its coordinate space, and one donor for two
           letters is one design language instead of two.
  д        each candidate's д over this face's own italic o. If the bowl sits
           on o, д is `o + one stroke`, which is б's recipe part for part.
  ours     this face's own italic з, c, o, and the г and д as they stand.
           Option C: г is a top bar, a curve descending left and a foot, and
           if any of that is already drawn in this family it should not be
           borrowed. No mirroring -- it has to work the way it is drawn.
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
CAND = ("Sudo", "Lyth Mono", "JetBrains Mono", "Roboto Mono", "Lilex",
        "Ioskeley Tuned", "Monaspace Xenon")
CW = 132


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

    rows = [("the OFL candidates' г", [(f, unsheared(paths[f], "г", ang[f]))
                                       for f in names]),
            ("their д, over our own italic o",
             [(f, unsheared(paths[f], "д", ang[f])) for f in names]),
            ("ours already: з c o, and г д as they stand",
             [(c, unsheared(OURS, c, oa)) for c in "зcoгд"])]

    pad = 14
    W = pad + max(len(r[1]) for r in rows) * (CW + pad)
    im = Image.new("RGB", (W, len(rows) * (CW + 62) + 70), "white")
    d = ImageDraw.Draw(im)
    hd = ImageFont.truetype(FACE, 19)
    lab = ImageFont.truetype(FACE, 14)

    for r, (title, cells) in enumerate(rows):
        y = 40 + r * (CW + 62)
        d.text((pad, y - 26), title, font=hd, fill=(170, 30, 30))
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
            c.thumbnail((CW, CW), Image.LANCZOS)
            x = pad + i * (CW + pad)
            im.paste(c, (x + (CW - c.width) // 2, y + (CW - c.height) // 2))
            d.text((x, y + CW + 10), fam, font=lab, fill=(110, 110, 110))

    im.save("tools/out/gd_donors.png")
    print("   wrote tools/out/gd_donors.png")


if __name__ == "__main__":
    main()
