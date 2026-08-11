"""м's two diagonals, at the weight they were and the weight М gives them.

    ./venv/bin/python tools/em_sheet.py OLD_DIR [NEW_DIR]

OLD_DIR is any stashed build -- copy the four static ttfs aside before
rebuilding -- and NEW_DIR defaults to the live `fonts/ttf`, so re-running this
after a further change needs only the one argument.

Two builds, each a directory of SUSEMono-<weight>.ttf, drawn ADJACENT on one
line per weight rather than as two blocks -- a difference of a tenth of a stem
is invisible between two pictures a screen apart and obvious between two
letters that touch.

The bands ask different questions. `company` puts м next to the М it is built
from and next to и п л ж, the letters it shares a stroke or a vertex with,
because a diagonal reads light only against the uprights beside it. `words`
and the reading band ask whether any of it survives at the size this face is
actually used at.
"""

import glob
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from PIL import Image, ImageDraw, ImageFont

from panel import font_dirs

WEIGHTS = ("Thin", "Regular", "Bold", "ExtraBold")

# М is the donor; и п л are the uprights м is judged beside; ж is the face's
# other diagonal Cyrillic; m w n are the Latin it shares a line with.
COMPANY = "Мм ими мпм мжм mwn"
WORDS = ("мама", "миша", "дім", "команда")
LINE = "git commit -m 'момент'"
ALPHABET = "абвгдежзийклмнопрстуфхцчшщьюяєіїґ"

SMALL = (12, 14)
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
OLD = sys.argv[1]
NEW = sys.argv[2] if len(sys.argv) > 2 else "fonts/ttf"
PAD = 200


def band(title, rows, gap=14):
    w = max([r.width for r in rows] + [400])
    h = 46 + sum(r.height + gap for r in rows)
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    d.text((16, 12), title, font=LAB, fill=(150, 40, 40))
    y = 46
    for r in rows:
        im.paste(r, (0, y))
        y += r.height + gap
    return im


def pair(name, text, size, tag=True):
    """One weight: the same text in both builds, side by side and adjacent."""
    fo = ImageFont.truetype("%s/SUSEMono-%s.ttf" % (OLD, name), size)
    fn = ImageFont.truetype("%s/SUSEMono-%s.ttf" % (NEW, name), size)
    tw = int(size * 0.62 * len(text))
    h = int(size * 1.5)
    im = Image.new("RGB", (PAD + 2 * tw + 90, h), "white")
    d = ImageDraw.Draw(im)
    d.text((0, h // 2 - 12), name, font=LAB, fill=(130, 130, 130))
    d.text((PAD, h * 0.5), text, font=fo, fill=(0, 0, 0), anchor="lm")
    d.text((PAD + tw + 60, h * 0.5), text, font=fn, fill=(0, 0, 0),
           anchor="lm")
    d.line([(PAD + tw + 30, 4), (PAD + tw + 30, h - 4)], fill=(210, 210, 210))
    if tag:
        d.text((PAD, 2), "approved", font=LAB_S, fill=(150, 150, 150))
        d.text((PAD + tw + 60, 2), "М's own diagonal", font=LAB_S,
               fill=(150, 40, 40))
    return im


def small_pair(name, size):
    """The reading band: at size, and magnified so the pixels can be seen."""
    text = "  ".join(WORDS) + "   " + LINE
    tiles = []
    for d_ in (OLD, NEW):
        f = ImageFont.truetype("%s/SUSEMono-%s.ttf" % (d_, name), size)
        w = int(size * 0.62 * len(text)) + 20
        t = Image.new("RGB", (w, int(size * 1.6)), "white")
        ImageDraw.Draw(t).text((10, t.height * 0.5), text, font=f,
                               fill=(0, 0, 0), anchor="lm")
        tiles.append(t)
    big = [t.resize((t.width * MAG, t.height * MAG), Image.NEAREST)
           for t in tiles]
    h = sum(t.height for t in tiles) + sum(b.height for b in big) + 24
    im = Image.new("RGB", (PAD + max(b.width for b in big) + 20, h), "white")
    d = ImageDraw.Draw(im)
    d.text((0, 8), "%s %dpx" % (name, size), font=LAB_S, fill=(130, 130, 130))
    y = 4
    for i, (t, b) in enumerate(zip(tiles, big)):
        d.text((0, y + 26), ("approved", "М's own")[i], font=LAB_S,
               fill=((150, 150, 150), (150, 40, 40))[i])
        im.paste(t, (PAD, y))
        im.paste(b, (PAD, y + t.height + 4))
        y += t.height + b.height + 12
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
    out = stack([
        band("in company -- м beside the М it is built from, and beside the "
             "uprights and the other diagonal it is read against",
             [pair(n, COMPANY, 120) for n in WEIGHTS]),
        band("among the whole drawn lowercase",
             [pair(n, ALPHABET, 56, tag=False) for n in WEIGHTS]),
        band("in words",
             [pair(n, "  ".join(WORDS), 82, tag=False) for n in WEIGHTS]),
        band("at reading size -- as delivered, and magnified %d times" % MAG,
             [small_pair(n, s) for n in WEIGHTS for s in SMALL]),
    ])
    out.save("tools/out/em_sheet.png")
    print("wrote tools/out/em_sheet.png  %dx%d" % out.size)


if __name__ == "__main__":
    main()
