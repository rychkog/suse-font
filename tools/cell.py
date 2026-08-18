"""How much of its cell does each letter's ink take, at reading height?

    ./venv/bin/python tools/cell.py

A monospace gives every letter the same advance, so the only thing that can
make one letter read wider than its neighbour is how much of that cell its INK
takes. Written after the user reported that "lots of letters in italic are much
wider than the others", which is a question about a DISTRIBUTION and not about
any one letter -- nothing here had ever read one.

Read inside the x-height band only. An ascender or a descender on a slanted
letter drags the outline's box sideways without the eye seeing a wider letter,
and a band keeps the comparison to the rows that carry the rhythm.

Three readings, because one of them alone says nothing:

  ours against the panel      is our spread unusual for a monospace italic?
  ours at the HEAVY end       `panel.italics` keeps each family's lightest, and
                              what a face does when its italic gets bold and
                              the cell does not is a different question
  upright against italic      does a face let its italic take more of the cell
                              than its own upright does, and by how much

The answer, over 31 monospace italics: the unevenness is the genre. ж is over
the cell in almost every face at every weight, and at the heavy end five to
twelve letters are, ours included. See METHOD §8.
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                               # noqa: E402
from PIL import Image, ImageDraw, ImageFont                      # noqa: E402
from fontTools.ttLib import TTFont                               # noqa: E402

from probe import contours                                       # noqa: E402

CYR = "абвгдежзийклмнопрстуфхцчшщъыьэюя"
LAT = "abcdefghijklmnopqrstuvwxyz"
SIZE = 200


def read(path, chars):
    """{letter: its ink width over the advance}, read in the x-height band."""
    f = TTFont(path, fontNumber=0, lazy=True)
    try:
        upem = f["head"].unitsPerEm
        gs, cm = f.getGlyphSet(), f.getBestCmap()
        o = contours(f, "o", cm, gs)
        if not o:
            return None
        ys = [q[1] for p in o for q in p]
        oy0, oy1 = min(ys), max(ys)
        adv = f["hmtx"][cm[ord("o")]][0]
    finally:
        f.close()
    k = SIZE / float(upem)
    fnt = ImageFont.truetype(path, SIZE)
    pad = int(SIZE * 0.6)
    out = {}
    for ch in chars:
        img = Image.new("L", (SIZE * 3, SIZE * 3), 0)
        ImageDraw.Draw(img).text((pad, pad), ch, font=fnt, fill=255,
                                 anchor="ls")
        a = np.asarray(img) > 127
        if not a.any():
            continue
        band = a[max(0, pad - int(round(oy1 * k))):pad - int(round(oy0 * k))]
        if not band.any():
            continue
        xs = np.where(band.any(axis=0))[0]
        out[ch] = (xs[-1] + 1 - xs[0]) / (adv * k)
    return out


def spread(d):
    v = sorted(d.values())
    return v[0], v[len(v) // 2], v[-1]


def over(d):
    return "".join(ch for ch, v in sorted(d.items(), key=lambda kv: -kv[1])
                   if v > 1.0) or "none"


def line(label, d, extra=""):
    lo, md, hi = spread(d)
    print("   %-26s %.2f..%.2f med %.2f  %s%s"
          % (label, lo, hi, md, extra, over(d)))


def main():
    from panel import italics, families
    print("\n=== ours, upright against italic ===")
    for a in ("Thin", "Regular", "ExtraBold"):
        line("ours, %s upright" % a, read("fonts/ttf/SUSEMono-%s.ttf" % a, CYR))
        line("ours, %s italic" % a,
             read("fonts/ttf/SUSEMono-%sItalic.ttf" % a, CYR))

    print("\n=== the panel, lightest italic of each family ===")
    for fam, path in italics():
        if fam.startswith("SUSE Mono"):
            continue
        c = read(path, CYR)
        if c and len(c) >= 20:
            line(fam, c)

    print("\n=== the italic's growth over the same family's upright ===")
    up = {f: p for f, p in families() if not f.endswith("(heaviest)")}
    ds = []
    for fam, ip in italics():
        if fam.startswith("SUSE Mono"):
            continue
        key = next((k for k in up if k.startswith(fam) or fam.startswith(k)),
                   None)
        if key is None:
            continue
        u, i = read(up[key], CYR), read(ip, CYR)
        if not u or not i or len(u) < 20 or len(i) < 20:
            continue
        ds.append(spread(i)[1] - spread(u)[1])
        print("   %-26s %.2f -> %.2f   %+.2f"
              % (fam, spread(u)[1], spread(i)[1], ds[-1]))
    ds.sort()
    print("   panel  %+.2f .. %+.2f   median %+.2f  (%d families)"
          % (ds[0], ds[-1], ds[len(ds) // 2], len(ds)))


if __name__ == "__main__":
    main()
