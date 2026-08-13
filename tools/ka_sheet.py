"""К and к as they are now, against the Latin K and k they used to be.

    ./venv/bin/python tools/ka_sheet.py

The old К was the Latin K itself, donated as a component, so the Latin column
IS the previous drawing -- this is a before-and-after, not a family portrait.
Adjacent and per weight, because that is the only way the junction's height
shows: one block above another hides exactly the difference being judged.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

F = "fonts/ttf/SUSEMono-%s.ttf"
WEIGHTS = ("Thin", "Regular", "Bold", "ExtraBold")
SS = 4                  # supersample; a 1-bit fill is unreadable at these sizes

PAIRS = (("КK", "кk"), ("КKКK", "кkкk"))
WORDS = ("Київська книжка", "як крок у рік", "КРОК КИЇВ ЛЬВІВ")
MIXED = "git commit -m 'кирилиця' build/книга.log"


def text(path, s, px, fill=(20, 20, 20)):
    """One run of text, drawn big and brought down with Lanczos."""
    f = ImageFont.truetype(path, px * SS)
    box = f.getbbox(s)
    w, h = box[2] + px * SS // 2, int(px * SS * 1.6)
    im = Image.new("RGB", (w, h), "white")
    ImageDraw.Draw(im).text((0, 0), s, font=f, fill=fill)
    return im.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)


def main():
    lab = ImageFont.truetype(F % "Regular", 17)
    head = ImageFont.truetype(F % "Regular", 27)
    sub = ImageFont.truetype(F % "Regular", 20)

    rows = []
    # the letters, adjacent, per weight
    for w in WEIGHTS:
        rows.append(("%s -- Cyrillic then Latin, adjacent" % w,
                     [text(F % w, PAIRS[0][0], 96),
                      text(F % w, PAIRS[0][1], 96),
                      text(F % w, PAIRS[1][0], 44),
                      text(F % w, PAIRS[1][1], 44)]))
    # in company
    for w in ("Regular", "Bold"):
        rows.append(("%s -- in words" % w,
                     [text(F % w, s, 42) for s in WORDS]))
    # at the sizes it is actually read at
    for px in (12, 14):
        rows.append(("Regular and Bold at %dpx" % px,
                     [text(F % "Regular", MIXED, px),
                      text(F % "Bold", MIXED, px),
                      text(F % "Regular", " ".join(WORDS), px)]))

    pad, left = 20, 26
    W = max(left + sum(i.width + pad for i in r[1]) + pad for r in rows)
    W = max(W, 900)
    H = 84 + sum(max(i.height for i in r[1]) + 44 for r in rows)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((left, 20), "К к drawn -- arm and leg merged into a neck off the "
           "stem, at Ж's waist", font=head, fill=(170, 30, 30))
    d.text((left, 52), "beside the Latin K k, which is what К к used to be -- "
           "K branches, К does not", font=sub, fill=(140, 140, 140))
    y = 96
    for title, imgs in rows:
        d.text((left, y), title, font=lab, fill=(150, 150, 150))
        y += 22
        x = left
        for i in imgs:
            im.paste(i, (x, y))
            x += i.width + pad
        y += max(i.height for i in imgs) + 22
    im.save("tools/out/ka_sheet.png")
    print("wrote tools/out/ka_sheet.png", im.size)


if __name__ == "__main__":
    main()
