"""The cursive г and д, in the company they actually keep.

    ./venv/bin/python tools/cursive_sheet.py

Never alone and never against the reference only: beside this face's own o,
which is the letter both of them are measured against, in words, at every
weight, and at the sizes the font is read at. A cursive letter that survives
at display size and falls apart at 12px has not survived.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

I = "fonts/ttf/SUSEMono-%sItalic.ttf"
LAB = "fonts/ttf/SUSEMono-Regular.ttf"
SS = 4

WEIGHTS = ("Thin", "Light", "Regular", "Bold", "ExtraBold")
LETTERS = "го до гдо"
WORDS = ("дорога, година", "ґудзик, погляд")
MIXED = "git log --graph 'дорога' build/погода.log"


def text(path, s, px, fill=(20, 20, 20)):
    """One line, supersampled and resolved down -- a 1-bit fill is unreadable."""
    f = ImageFont.truetype(path, px * SS)
    box = f.getbbox(s)
    w = box[2] + px * SS
    h = int(px * SS * 1.55)
    im = Image.new("RGB", (w, h), "white")
    ImageDraw.Draw(im).text((px * SS // 4, 0), s, font=f, fill=fill)
    out = im.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    im.close()
    return out


def main():
    pad = 22
    rows = []
    for w in WEIGHTS:
        rows.append((w, text(I % w, LETTERS + "   " + WORDS[0], 56)))
    rows.append(("Regular, in a line", text(I % "Regular", MIXED, 30)))
    for px in (14, 12):
        rows.append(("Regular at %dpx" % px,
                     text(I % "Regular", MIXED + "  " + WORDS[1], px)))

    W = pad * 2 + max(r[1].width for r in rows) + 210
    H = pad * 2 + sum(r[1].height + 16 for r in rows) + 40
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    hd = ImageFont.truetype(LAB, 22)
    lab = ImageFont.truetype(LAB, 15)
    d.text((pad, pad), "the cursive г and д, beside the o they are measured "
           "against", font=hd, fill=(170, 30, 30))
    y = pad + 40
    for name, img in rows:
        im.paste(img, (pad + 200, y))
        d.text((pad, y + img.height // 2 - 8), name, font=lab,
               fill=(120, 120, 120))
        y += img.height + 16
    im.save("tools/out/cursive_sheet.png")
    print("   wrote tools/out/cursive_sheet.png")


if __name__ == "__main__":
    main()
