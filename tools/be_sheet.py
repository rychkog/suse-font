"""б's review sheet: in company, in words, and at reading size.

    ./venv/bin/python tools/be_sheet.py

Rendered from the BUILT fonts rather than from the recipes, because what is
being judged here is the artefact that ships. Three bands, each answering a
question the others cannot:

  company   б beside its own capital, beside the о it is built from, beside
            the 6 it is nearly, and beside the Latin b and o it shares a line
            with. A letter alone is always plausible.
  words     Ukrainian and Russian, plus the mixed line, because the letter has
            to hold a word and not only a cell.
  reading   12px and 14px, at size and magnified. Everything above is a
            display size, and this face is a terminal face.
"""

import glob
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from PIL import Image, ImageDraw, ImageFont

from panel import font_dirs

F = "fonts/ttf/SUSEMono-%s.ttf"
WEIGHTS = ("Thin", "Regular", "Bold", "ExtraBold")

COMPANY = "Бб об 6 бо bo"
WORDS = ("бублик", "обід", "робота", "будь")
LINE = "git commit -m 'бібліотека'"

SMALL = (12, 14)
# What a 12px row is magnified by so the shape can be seen at all. Nearest,
# not smooth: the point of this band is the pixels the rasteriser actually
# produced, and any resampling other than nearest invents new ones.
MAG = 4


def label(sz):
    for d in font_dirs():
        for n in ("DejaVuSans.ttf", "segoeui.ttf",
                  "LiberationSans-Regular.ttf"):
            hit = glob.glob(d + "/" + n)
            if hit:
                return ImageFont.truetype(hit[0], sz)
    return ImageFont.load_default()


LAB = label(20)
LAB_S = label(15)


def band(title, rows, gap=14):
    """One titled block of already-rendered rows, stacked."""
    w = max([r.width for r in rows] + [400]) + 200
    h = 46 + sum(r.height + gap for r in rows)
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 12), title, font=LAB, fill=(150, 40, 40))
    y = 46
    for r in rows:
        im.paste(r, (200, y))
        y += r.height + gap
    return im


def row(name, draw_into, w, h):
    """A row with the weight's name in the left margin."""
    im = Image.new("RGB", (w, h), "white")
    ImageDraw.Draw(im).text((0, h // 2 - 12), name, font=LAB,
                            fill=(130, 130, 130))
    draw_into(im)
    return im


def text_row(name, text, size, pad=200):
    f = ImageFont.truetype(F % name, size)
    w = pad + int(size * 0.62 * len(text)) + 60
    h = int(size * 1.5)

    def go(im):
        ImageDraw.Draw(im).text((pad, h * 0.5), text, font=f, fill=(0, 0, 0),
                                anchor="lm")

    return row(name, go, w, h)


def small_row(name, size):
    """The reading band: every word at `size`, at size and magnified."""
    f = ImageFont.truetype(F % name, size)
    text = "  ".join(WORDS) + "   " + LINE
    w = int(size * 0.62 * len(text)) + 40
    tile = Image.new("RGB", (w, int(size * 1.6)), "white")
    ImageDraw.Draw(tile).text((10, tile.height * 0.5), text, font=f,
                              fill=(0, 0, 0), anchor="lm")
    big = tile.resize((tile.width * MAG, tile.height * MAG), Image.NEAREST)
    im = Image.new("RGB", (200 + max(tile.width, big.width) + 20,
                           tile.height + big.height + 16), "white")
    ImageDraw.Draw(im).text((0, 8), "%s %dpx" % (name, size), font=LAB_S,
                            fill=(130, 130, 130))
    im.paste(tile, (200, 4))
    im.paste(big, (200, tile.height + 12))
    return im


def stack(bands, gap=26):
    w = max(b.width for b in bands)
    im = Image.new("RGB", (w, sum(b.height + gap for b in bands) + 20),
                   "white")
    y = 10
    for b in bands:
        im.paste(b, (0, y))
        ImageDraw.Draw(im).line([(0, y + b.height + gap // 2),
                                 (w, y + b.height + gap // 2)],
                                fill=(228, 228, 228))
        y += b.height + gap
    return im


def main():
    company = band("in company -- б, its capital, the о it is built from, "
                   "the 6 it is nearly, and the Latin it shares a line with",
                   [text_row(n, COMPANY, 130) for n in WEIGHTS])
    words = band("in words",
                 [text_row(n, "  ".join(WORDS), 90) for n in WEIGHTS])
    small = band("at reading size -- as delivered, and magnified %d times"
                 % MAG,
                 [small_row(n, s) for n in WEIGHTS for s in SMALL])
    out = stack([company, words, small])
    out.save("tools/out/be_sheet.png")
    print("wrote tools/out/be_sheet.png  %dx%d" % out.size)


if __name__ == "__main__":
    main()
