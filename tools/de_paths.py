"""Which face's д is drawn for a bowl like OURS -- the donor question.

    ./venv/bin/python tools/de_paths.py

The arm is donated as a PATH now (`scripts/de_from_lilex.py`), so what has to
suit this face is not the donor's colour or its terminals -- none of that comes
across -- but where its stroke RUNS, and that depends entirely on the bowl it
was drawn to leave. Lilex's д stands on a bowl with a nearly straight
right-hand side and its stroke goes straight up that side for a third of the
letter before it turns. Ours stands on a round o. Fitted here, the straight run
landed against a wall curving away underneath it and the seam came out as a
long dead straight edge ending in a point below the x-height -- rejected on
sight, and correctly.

So read the thing that matters: the **right-hand stroke's centreline**, row by
row, from the bottom of the bowl up into the arm. Taken off the ink, so no
per-font segment indices are needed and every candidate is read the same way.
Against the face's own o, so it is a shape and not a size.

  fitted  how far the donor's own centreline strays from THIS face's own o
          wall, below the x-height, in units of o's wall. 0 is a stroke that
          would run exactly where ours runs; anything much over 1 is a stroke
          drawn for a different bowl.
  turn    where it leaves that wall, over o's height, measured from the
          x-height. Negative is below.

Drawn as well as counted: each candidate's centreline over this face's own o,
at one scale.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                               # noqa: E402
from PIL import Image, ImageDraw, ImageFont                      # noqa: E402

import weights as W                                              # noqa: E402

XH = 260
FACE = "fonts/ttf/SUSEMono-Regular.ttf"
OURS = "fonts/ttf/SUSEMono-RegularItalic.ttf"
SS = 2
CELL = 330
DESCEND = 0.15

# Consolas is on this machine and is drawn for a bowl very like ours, and it is
# Microsoft's. It is here to be looked at and can never be a donor.
PROPRIETARY = ("Consolas", "Courier New", "Menlo", "Lucida Console",
               "Liberation Mono")


def box(m):
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def spine(m, y0, y1):
    """The centreline of the RIGHTMOST run of ink, row by row."""
    out = []
    for y in range(y0, y1):
        xs = np.where(m[y])[0]
        if not len(xs):
            continue
        brk = np.where(np.diff(xs) > 1)[0]
        run = xs[brk[-1] + 1:] if len(brk) else xs
        out.append((0.5 * (run[0] + run[-1]), y))
    return out


def read(path):
    """(spine of д, o's own wall spine, o's box, wall) for one face."""
    o = W.render(path, "o", XH)
    d = W.render(path, "д", XH)
    if o is None or d is None:
        return "no o or no д"
    ox0, oy0, ox1, oy1 = box(o)
    oh = oy1 - oy0
    _x0, _y0, _x1, dy1 = box(d)
    if (dy1 - oy1) / float(oh) > DESCEND:
        return "draws the g-form, with a descender -- a different letter"
    wall = W.width(W.edt(o))
    # the bowl's own band: from its floor to its crown, and no arm in it
    ow = spine(o, oy0 + int(0.12 * oh), oy1 - int(0.12 * oh))
    dw = spine(d, dy1 - oh + int(0.12 * oh), dy1 - int(0.12 * oh))
    if not ow or not dw or not wall:
        return "no wall"
    return dw, ow, (ox0, oy0, ox1, oy1), wall


def main():
    from panel import italics
    from gd_band import is_cursive_ge

    mine = read(OURS)
    if isinstance(mine, str):
        raise SystemExit("our own italic: %s" % mine)
    _md, mo, mbox, mwall = mine
    mine_by_y = {int(round(y)): x for x, y in mo}
    mx1, my0, my1 = mbox[2], mbox[1], mbox[3]
    moh = my1 - my0

    rows, cells = [], []
    for fam, path in sorted(italics()):
        if fam.startswith("SUSE Mono"):
            continue
        g = W.render(path, "г", XH)
        if g is None or not is_cursive_ge(g):
            continue
        got = read(path)
        if isinstance(got, str):
            print("   %-22s %s" % (fam, got))
            continue
        dw, _ow, dbox, _wall = got
        # put the donor's letter in our frame: its own o's box onto ours
        k = moh / float(dbox[3] - dbox[1])
        put = [(mx1 + (x - dbox[2]) * k, my1 + (y - dbox[3]) * k)
               for x, y in dw]
        off, turn = [], None
        for x, y in put:
            r = int(round(y))
            if r not in mine_by_y:
                continue
            e = abs(x - mine_by_y[r]) / mwall
            off.append(e)
            if e < 0.55:
                turn = y
        fitted = float(np.median(off)) if off else None
        rows.append((fam, fitted,
                     None if turn is None else (my1 - turn) / float(moh),
                     fam in PROPRIETARY))
        cells.append((fam, put, fam in PROPRIETARY))

    print("\n   %-22s %7s %7s" % ("", "fitted", "turn"))
    for fam, fitted, turn, prop in sorted(rows, key=lambda r: r[1] or 99):
        print("   %-22s %7s %7s   %s"
              % (fam,
                 "  .  " if fitted is None else "%.2f" % fitted,
                 "  .  " if turn is None else "%+.2f" % turn,
                 "PROPRIETARY -- reference only" if prop else ""))

    COLS = 4
    cw, ch = CELL + 26, CELL + 44
    n = (len(cells) + COLS - 1) // COLS
    im = Image.new("RGB", ((24 + COLS * cw) * SS, (66 + n * ch) * SS), "white")
    dr = ImageDraw.Draw(im)
    dr.text((24 * SS, 16 * SS), "each face's д drawn as its right-hand "
            "stroke's centreline, laid over THIS face's own italic o",
            font=ImageFont.truetype(FACE, 24 * SS), fill=(170, 30, 30))
    lab = ImageFont.truetype(FACE, 18 * SS)
    om = W.render(OURS, "o", XH)
    for i, (fam, put, prop) in enumerate(cells):
        x = (24 + (i % COLS) * cw) * SS
        y = (66 + (i // COLS) * ch) * SS
        h, w = om.shape
        rgb = np.full((h, w, 3), 255, np.uint8)
        rgb[om] = (214, 214, 214)
        tile = Image.fromarray(rgb)
        t = ImageDraw.Draw(tile)
        t.line([(a, b) for a, b in put],
               fill=(150, 150, 150) if prop else (185, 30, 30), width=3)
        s = min(CELL * SS / float(w), CELL * SS / float(h))
        tile = tile.resize((int(w * s), int(h * s)), Image.LANCZOS)
        im.paste(tile, (x + (CELL * SS - tile.width) // 2, y))
        dr.text((x, y + (CELL + 12) * SS), fam[:22], font=lab,
                fill=(110, 110, 110))
    im.save("tools/out/de_paths.png")
    print("\n   wrote tools/out/de_paths.png", im.size)


if __name__ == "__main__":
    main()
