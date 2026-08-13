"""Ours against Roboto Mono's К and к, the letter the design is taken from.

    ./venv/bin/python tools/ka_roboto.py

Roboto Mono is one of the thirteen faces whose Latin K branches and whose
Cyrillic К does not, and it is the one this К is drawn after. Its light and
heaviest weights stand against our Thin and ExtraBold; ours is red where it
differs, so the junction's height and the two leans are the only things left
to look at.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                             # noqa: E402
from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

from panel import families                                     # noqa: E402

SZ = 260
OURS = "fonts/ttf/SUSEMono-%s.ttf"
# our weight against the nearest Roboto Mono has
PAIRS = (("Thin", "Roboto Mono"), ("Regular", "Roboto Mono"),
         ("ExtraBold", "Roboto Mono (heaviest)"))


def ink(path, ch, px):
    f = ImageFont.truetype(path, px)
    im = Image.new("L", (px * 2, int(px * 2.2)), 0)
    ImageDraw.Draw(im).text((px // 3, px // 3), ch, font=f, fill=255)
    a = np.asarray(im) > 127
    if not a.any():
        return None
    ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def over(mine, theirs):
    """Theirs in grey, ours in red on top, both scaled to one height."""
    h = max(mine.shape[0], theirs.shape[0])

    def up(a):
        im = Image.fromarray((a * 255).astype(np.uint8))
        im = im.resize((int(a.shape[1] * h / a.shape[0]), h), Image.LANCZOS)
        return np.asarray(im) > 127
    A, B = up(mine), up(theirs)
    w = max(A.shape[1], B.shape[1])

    def pad(a):
        out = np.zeros((h, w), bool)
        out[:, :a.shape[1]] = a
        return out
    A, B = pad(A), pad(B)
    rgb = np.full((h, w, 3), 255, np.uint8)
    rgb[B] = (185, 185, 185)
    rgb[A] = (200, 40, 40)
    rgb[A & B] = (35, 35, 35)
    return Image.fromarray(rgb)


def main():
    paths = dict(families())
    lab = ImageFont.truetype(OURS % "Regular", 18)
    head = ImageFont.truetype(OURS % "Regular", 27)
    sub = ImageFont.truetype(OURS % "Regular", 19)

    cells, labels = [], []
    for w, fam in PAIRS:
        if fam not in paths:
            continue
        for ch in "Кк":
            a, b = ink(OURS % w, ch, SZ), ink(paths[fam], ch, SZ)
            if a is None or b is None:
                continue
            cells.append(over(a, b))
            labels.append("%s %s, over theirs" % (ch, w))
        # side by side as well, because an overlay hides the letter
        for ch in "Кк":
            a, b = ink(OURS % w, ch, SZ), ink(paths[fam], ch, SZ)
            if a is None or b is None:
                continue
            for src, tint in ((a, (35, 35, 35)), (b, (35, 35, 35))):
                rgb = np.full(src.shape + (3,), 255, np.uint8)
                rgb[src] = tint
                cells.append(Image.fromarray(rgb))
            labels.append("%s ours" % ch)
            labels.append("%s Roboto" % ch)

    # six cells is exactly one weight, so a row is a weight and the long
    # labels never land beside each other
    pad, left, top = 22, 26, 96
    per = 6
    W = left + per * (SZ + pad)
    rows = (len(cells) + per - 1) // per
    H = top + rows * (int(SZ * 1.35) + 44)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    d.text((left, 22), "К к against Roboto Mono", font=head, fill=(170, 30, 30))
    d.text((left, 56), "ours red, theirs grey, both where they agree -- then "
           "each on its own", font=sub, fill=(140, 140, 140))
    for i, (c, t) in enumerate(zip(cells, labels)):
        c = c.copy()
        c.thumbnail((SZ, int(SZ * 1.3)), Image.LANCZOS)
        x = left + (i % per) * (SZ + pad)
        y = top + (i // per) * (int(SZ * 1.35) + 44)
        im.paste(c, (x, y))
        d.text((x, y + int(SZ * 1.3) + 6), t, font=lab, fill=(120, 120, 120))
    im.save("tools/out/ka_roboto.png")
    print("wrote tools/out/ka_roboto.png", im.size)


if __name__ == "__main__":
    main()
