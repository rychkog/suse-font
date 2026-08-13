"""К and к among the Cyrillic they share a page with, not beside the Latin.

    ./venv/bin/python tools/ka_company.py

К was judged against the Latin K it replaced and against Roboto Mono's К, and
neither of those is the company it keeps. The letters a reader meets it with
are the face's own other diagonals -- Ж Х У И Л Д and their lowercase -- and
the only question that matters is whether one of them looks like it was drawn
by somebody else.

Measured, К is the shallowest diagonal in the Cyrillic: 55-60 degrees at
ExtraBold where Х holds 63-66, И 63, У 69 and Ж 81. That is not a defect and
it is worth knowing why before looking -- the face's own LATIN K is the
shallowest thing it draws too, 55-63 against X's 63-66, N's 64 and V's 74-76.
К is shallow here because K is shallow here, and it is inside K's own range at
both masters.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

F = "fonts/ttf/SUSEMono-%s.ttf"
SS = 4

# the diagonal family, К first so the eye lands on it, then the rest
CAPS = "КЖХУИЛДАМЯ"
LOWER = "кжхуилдамя"
WORDS = ("Харків жінка художник", "книжка лікар яскравий",
         "ЖУРНАЛ ХАРКІВ ДЯКУЮ")
MIXED = "git commit -m 'книжка' build/художник-Київ.log"


def text(path, s, px):
    f = ImageFont.truetype(path, px * SS)
    box = f.getbbox(s)
    w, h = box[2] + px * SS // 2, int(px * SS * 1.55)
    im = Image.new("RGB", (w, h), "white")
    ImageDraw.Draw(im).text((0, 0), s, font=f, fill=(20, 20, 20))
    out = im.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    im.close()
    return out


def main():
    lab = ImageFont.truetype(F % "Regular", 17)
    head = ImageFont.truetype(F % "Regular", 27)
    sub = ImageFont.truetype(F % "Regular", 19)

    rows = []
    for w in ("Thin", "Regular", "Bold", "ExtraBold"):
        rows.append(("%s -- К к against every other diagonal this face draws"
                     % w, [text(F % w, CAPS, 62), text(F % w, LOWER, 62)]))
    # the place the doubt is: heaviest, beside the two letters whose diagonals
    # are steepest, where К's lean is furthest from its neighbours'
    for w in ("Thin", "ExtraBold"):
        rows.append(("%s magnified -- К beside the steepest two, Ж and Х" % w,
                     [text(F % w, "КЖХ", 132), text(F % w, "кжх", 132)]))
    for w in ("Regular", "Bold"):
        rows.append(("%s -- in words that put them together" % w,
                     [text(F % w, s, 38) for s in WORDS]))
    for px in (12, 14):
        rows.append(("Regular and Bold at %dpx" % px,
                     [text(F % "Regular", MIXED, px),
                      text(F % "Bold", MIXED, px),
                      text(F % "Regular", WORDS[1], px)]))

    pad, left = 20, 26
    W = max(max(left + sum(i.width + pad for i in r[1]) + pad
                for r in rows), 900)
    H = 96 + sum(max(i.height for i in r[1]) + 44 for r in rows)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((left, 20), "К к in company -- the face's own Cyrillic diagonals",
           font=head, fill=(170, 30, 30))
    d.text((left, 54), "К is the shallowest of them, because the Latin K it is "
           "built from is the shallowest thing this face draws",
           font=sub, fill=(140, 140, 140))
    y = 100
    for title, imgs in rows:
        d.text((left, y), title, font=lab, fill=(150, 150, 150))
        y += 22
        x = left
        for i in imgs:
            im.paste(i, (x, y))
            x += i.width + pad
        y += max(i.height for i in imgs) + 22
    im.save("tools/out/ka_company.png")
    print("wrote tools/out/ka_company.png", im.size)


if __name__ == "__main__":
    main()
