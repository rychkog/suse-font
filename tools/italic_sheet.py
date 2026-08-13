"""The italic Cyrillic, against the upright and against the italic Latin.

    ./venv/bin/python tools/italic_sheet.py

First look at a thing that did not exist an hour ago: `build_cyrillic.py` had
only ever written into the upright source. Every letter here is the SAME
construction as its upright, run against the italic's own Latin in un-sheared
space and sheared back about the middle of the x-height -- so a letter built
from a straight-sided donor comes out as the upright sloped, which is what this
face does to its own straight capitals, and a letter built from a round one or
from the lowercase comes out different, because the italic redraws those.

Seven letters answer differently, because Cyrillic cursive restructures them
and no shear can do that. `tools/italic_forms.py --changed` asked all 29
monospace italics on this machine which ones they redraw, comparing each
italic Cyrillic with its OWN upright sheared and no Latin in the test:

  и й п т   are the italic's own u n m -- honest tier 1 here while they are
            drawn in the upright, which is what a per-source table is for
  г д       have no counterpart in either script and are donated outlines,
            Lilex's, fitted to this face. `scripts/ge_from_lilex.py` and
            `scripts/de_from_lilex.py`
  м         is deliberately NOT changed: only 8 of the 29 redraw it and what
            moves is an entry stroke, not the construction

The round letters -- а б в е з о р с у ф ъ ы ь э ю -- come out redrawn for
free, because a recipe reads `pr.paths(donor)` and the italic's own bowls are
already the italic's.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

R = "fonts/ttf/SUSEMono-%s.ttf"
I = "fonts/ttf/SUSEMono-%sItalic.ttf"
SS = 4

CAPS = "АБВГҐДЕЄЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
LOWER = "абвгґдеєжзийклмнопрстуфхцчшщьюя"
WORDS = ("ґрунт боротьба єднати", "юність, тёщи, книжка")
MIXED = "git commit -m 'юність' build/ґрунт-єднати.log"


def text(path, s, px, fill=(20, 20, 20)):
    f = ImageFont.truetype(path, px * SS)
    box = f.getbbox(s)
    w, h = box[2] + px * SS, int(px * SS * 1.6)
    im = Image.new("RGB", (w, h), "white")
    ImageDraw.Draw(im).text((px * SS // 4, 0), s, font=f, fill=fill)
    out = im.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    im.close()
    return out


def main():
    lab = ImageFont.truetype(R % "Regular", 17)
    head = ImageFont.truetype(R % "Regular", 27)
    sub = ImageFont.truetype(R % "Regular", 19)

    rows = []
    for w in ("Regular", "Bold"):
        rows.append(("%s italic -- the capitals" % w,
                     [text(I % w, CAPS, 40)]))
        rows.append(("%s upright, the same line" % w,
                     [text(R % w, CAPS, 40)]))
    for w in ("Regular", "Bold"):
        rows.append(("%s italic -- the lowercase" % w,
                     [text(I % w, LOWER, 40)]))
        rows.append(("%s upright, the same line" % w,
                     [text(R % w, LOWER, 40)]))
    rows.append(("Regular italic -- in words, then upright below",
                 [text(I % "Regular", s, 34) for s in WORDS]))
    rows.append(("", [text(R % "Regular", s, 34) for s in WORDS]))
    for px in (12, 14):
        rows.append(("italic and upright at %dpx" % px,
                     [text(I % "Regular", MIXED, px),
                      text(R % "Regular", MIXED, px)]))

    title = "the italic Cyrillic"
    caption = ("the same constructions, run against the italic's own Latin "
               "and sheared back about xh/2 -- except the seven that Cyrillic "
               "cursive restructures")

    pad, left = 20, 26
    # the caption counts toward the width. It did not, and it has been cut off
    # mid-word in every sheet this tool has ever produced -- the width came
    # from the specimen rows alone, and the one line that says what the reader
    # is looking at ran off the edge.
    W = max(max(left + sum(i.width + pad for i in r[1]) + pad for r in rows),
            left + int(sub.getlength(caption)) + pad, 900)
    H = 96 + sum(max(i.height for i in r[1]) + 40 for r in rows)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((left, 20), title, font=head, fill=(170, 30, 30))
    d.text((left, 54), caption, font=sub, fill=(140, 140, 140))
    y = 100
    for title, imgs in rows:
        if title:
            d.text((left, y), title, font=lab, fill=(150, 150, 150))
        y += 20
        x = left
        for i in imgs:
            im.paste(i, (x, y))
            x += i.width + pad
        y += max(i.height for i in imgs) + 20
    im.save("tools/out/italic_sheet.png")
    print("wrote tools/out/italic_sheet.png", im.size)


if __name__ == "__main__":
    main()
