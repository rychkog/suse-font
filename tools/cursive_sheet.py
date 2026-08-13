"""The cursive г and д, in the company they actually keep.

    ./venv/bin/python tools/cursive_sheet.py

Never alone and never against the reference only: beside this face's own o,
which is the letter both of them are measured against, in words, at every
weight, and at the sizes the font is read at. A cursive letter that survives
at display size and falls apart at 12px has not survived.

The display rows are drawn large on purpose and the 12px and 14px rows are
NOT -- their whole point is being the size the font is read at, and a reading
row scaled up is a lie about the one thing it is there to show. Everything is
supersampled four times and resolved down with Lanczos, so a large row is
large because it was rendered large.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

I = "fonts/ttf/SUSEMono-%sItalic.ttf"
LAB = "fonts/ttf/SUSEMono-Regular.ttf"
SS = 4
# SS is the supersample used to get a clean edge; SCALE is how much bigger than
# its nominal size the whole sheet is DELIVERED. They are not the same thing.
# Supersampling alone gives a properly antialiased 14-pixel line -- which is
# then fourteen actual pixels tall in the PNG, and anything showing the PNG
# above 1:1 is enlarging fourteen pixels. Sharp and tiny reads as low quality
# and is. Rows that exist to show a READING size are drawn at that size and
# enlarged by whole pixels with NEAREST, so what is magnified is the real
# rasterisation rather than a smoother invention of it.
SCALE = 3

WEIGHTS = ("Thin", "Light", "Regular", "Bold", "ExtraBold")
LETTERS = "го до гдо"
WORDS = ("дорога, година", "ґудзик, погляд")
MIXED = "git log --graph 'дорога' build/погода.log"


def text(path, s, px, fill=(20, 20, 20), real=False):
    """One line at SCALE times `px`, or at `px` magnified if `real`."""
    at = px if real else px * SCALE
    f = ImageFont.truetype(path, at * SS)
    box = f.getbbox(s)
    w = box[2] + at * SS
    h = int(at * SS * 1.55)
    im = Image.new("RGB", (w, h), "white")
    ImageDraw.Draw(im).text((at * SS // 4, 0), s, font=f, fill=fill)
    out = im.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    im.close()
    if real:
        out = out.resize((out.width * SCALE, out.height * SCALE),
                         Image.NEAREST)
    return out


def main():
    pad = 22
    rows = []
    for w in WEIGHTS:
        rows.append((w, text(I % w, LETTERS + "   " + WORDS[0], 46)))
    rows.append(("Regular, in a line", text(I % "Regular", MIXED, 26)))
    for px in (14, 12):
        rows.append(("Regular at %dpx, magnified %dx" % (px, SCALE),
                     text(I % "Regular", MIXED + "  " + WORDS[1], px,
                          real=True)))

    pad, lead = pad * SCALE, 210 * SCALE
    W = pad * 2 + max(r[1].width for r in rows) + lead
    H = pad * 2 + sum(r[1].height + 16 * SCALE for r in rows) + 40 * SCALE
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    hd = ImageFont.truetype(LAB, 22 * SCALE)
    lab = ImageFont.truetype(LAB, 15 * SCALE)
    d.text((pad, pad), "the cursive г and д, beside the o they are measured "
           "against", font=hd, fill=(170, 30, 30))
    y = pad + 40 * SCALE
    for name, img in rows:
        im.paste(img, (pad + 200 * SCALE, y))
        d.text((pad, y + img.height // 2 - 8 * SCALE), name, font=lab,
               fill=(120, 120, 120))
        y += img.height + 16 * SCALE
    im.save("tools/out/cursive_sheet.png")
    print("   wrote tools/out/cursive_sheet.png")


if __name__ == "__main__":
    main()
