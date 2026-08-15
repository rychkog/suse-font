"""Is the cursive д a `d` with a different ascender, or an `o` with a hook?

    ./venv/bin/python tools/de_vs_d.py

Both descriptions fit the picture; they are different letters to build. Ours
takes this face's own **o** for the whole bowl and grafts a donated hook onto
its crown, and every round since has been spent on that graft -- a blob at the
departure, a pinch at the landing, a junction 1.64 against a ceiling of 1.34.

The panel can settle it, because a face's own `d` is right there beside its д
in the same file at the same weight. Read below the x-height, where д has only
its bowl and whatever runs down its right side:

  right   how straight that right side is: the rightmost ink in each row, a
          line fitted to it, and the worst departure over the run's length.
          A stem reads near 0. A round wall reads at the bulge. **A ratio, so
          it does not care how big the letter is, and taken on the leaning
          outline so it does not care about the slope either** (a line fitted
          to a sheared straight edge is still a straight edge).
  cover   how much of `d`'s ink below the x-height д also covers, over their
          union. 1.0 is the same drawing.
  bowlw   д's bowl width over d's bowl width, and `bowlx` where its left edge
          sits relative to d's, in units of that width.

Only the ∂-form counts -- `de_arm.py` says why -- and only faces that draw the
cursive г, which is what says the italic is a true italic and not a slope.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import statistics as st                                          # noqa: E402

import numpy as np                                               # noqa: E402
from PIL import Image, ImageDraw, ImageFont                      # noqa: E402

import weights as W                                              # noqa: E402

XH = 240
FACE = "fonts/ttf/SUSEMono-Regular.ttf"
SS = 2
CELL = 320
DESCEND = 0.15


def box(m):
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def straight(m, top, bot):
    """Worst departure of the right edge from a straight line, over its run.

    Rows `top`..`bot` only, and the two rows at each end dropped: a bowl's
    right edge turns at both, and the question is about the run between them.
    """
    rows, xs = [], []
    for y in range(top, bot):
        r = np.where(m[y])[0]
        if len(r):
            rows.append(y)
            xs.append(r.max())
    k = max(1, len(rows) // 12)
    rows, xs = rows[k:-k], xs[k:-k]
    if len(rows) < 8:
        return None
    a, b = np.polyfit(rows, xs, 1)
    dev = max(abs(np.polyval((a, b), rows) - np.array(xs)))
    return dev / float(rows[-1] - rows[0])


def read(path):
    """(right for д/d/o, cover, bowlw, bowlx, masks) for one face, or why not."""
    o = W.render(path, "o", XH)
    d = W.render(path, "d", XH)
    de = W.render(path, "д", XH)
    if o is None or d is None or de is None:
        return "no o, d or д"
    ox0, oy0, ox1, oy1 = box(o)
    oh = oy1 - oy0
    _, _, _, dey1 = box(de)
    if (dey1 - oy1) / float(oh) > DESCEND:
        return "draws the g-form, with a descender -- a different letter"
    # the x-height line, measured off the letter's OWN bottom so an overshoot
    # at the baseline does not shift it
    top, bot = dey1 - oh, dey1
    lo = de[top:bot]
    ld = d[top:bot]
    if not lo.any() or not ld.any():
        return "nothing below the x-height"
    inter = float((lo & ld).sum())
    union = float((lo | ld).sum())
    bx0, _, bx1, _ = box(lo)
    dx0, _, dx1, _ = box(ld)
    bw, dw = float(bx1 - bx0), float(dx1 - dx0)
    return (straight(de, top, bot), straight(d, top, bot),
            straight(o, oy0, oy1), inter / union, bw / dw,
            (bx0 - dx0) / dw, de, d, top)


def tile(de, d, top, cell):
    """д in red over `d` in grey, both as drawn, in the one frame they share."""
    y0 = min(box(de)[1], box(d)[1])
    x0 = min(box(de)[0], box(d)[0])
    x1 = max(box(de)[2], box(d)[2])
    y1 = max(box(de)[3], box(d)[3])
    a = de[y0:y1, x0:x1].copy()
    b = d[y0:y1, x0:x1].copy()
    h, w = a.shape
    rgb = np.full((h, w, 3), 255, np.uint8)
    rgb[b] = (203, 203, 203)
    rgb[a] = (185, 30, 30)
    rgb[a & b] = (70, 20, 20)
    r = top - y0
    if 0 < r < h:
        rgb[max(0, r - 1):r + 1] = (150, 190, 255)
    s = min(cell / float(w), cell / float(h))
    return Image.fromarray(rgb).resize(
        (max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)


def main():
    from panel import italics
    from gd_band import is_cursive_ge

    rows, cells = [], []
    for w in ("Thin", "Regular", "ExtraBold"):
        got = read("fonts/ttf/SUSEMono-%sItalic.ttf" % w)
        if not isinstance(got, str):
            rows.append(("ours, " + w,) + got[:6])
            cells.append(("ours, " + w, got[6], got[7], got[8]))

    for fam, path in sorted(italics()):
        # THIS FACE IS NOT EVIDENCE ABOUT ITSELF. `italics()` reads the fonts
        # installed on the machine, and SUSE Mono is one of them -- so a band
        # built here quietly contained the very letter it was being used to
        # judge, twice over, at whatever build happened to be installed. The
        # taper floor came out 0.64 with them in and 0.79 with them out, and
        # 0.64 was our own rejected д voting for itself. CLAUDE.md rule 5 with
        # nobody noticing there were two of them.
        if fam.startswith("SUSE Mono"):
            continue
        try:
            g = W.render(path, "г", XH)
            if g is None or not is_cursive_ge(g):
                continue
            got = read(path)
            if isinstance(got, str):
                print("   %-22s %s" % (fam, got))
                continue
            rows.append((fam,) + got[:6])
            cells.append((fam, got[6], got[7], got[8]))
        except Exception as e:
            print("   %-22s %s" % (fam, e))

    print("\n   %-22s %7s %7s %7s %7s %7s %7s"
          % ("", "д", "d", "o", "cover", "bowlw", "bowlx"))
    print("   %-22s %-23s %s"
          % ("", "  right edge, dev/run", "д against its own d"))
    for r in rows:
        print("   %-22s %s"
              % (r[0], " ".join("%7s" % ("  .  " if v is None else "%.3f" % v)
                                for v in r[1:])))

    ref = [r for r in rows if not r[0].startswith("ours")]
    print()
    for i, what in ((1, "д's right edge, dev/run"),
                    (2, "d's right edge, dev/run"),
                    (3, "o's right edge, dev/run"),
                    (4, "д over d below the x-height"),
                    (5, "д's bowl width over d's"),
                    (6, "д's bowl left, in d's widths")):
        v = sorted(r[i] for r in ref if r[i] is not None)
        print("   %-30s median %6.3f, %6.3f..%6.3f  (%d)"
              % (what, st.median(v), v[1], v[-2], len(v)))

    COLS = 4
    cw, ch = CELL + 30, CELL + 46
    n = (len(cells) + COLS - 1) // COLS
    im = Image.new("RGB", ((24 + COLS * cw) * SS, (66 + n * ch) * SS), "white")
    dr = ImageDraw.Draw(im)
    dr.text((24 * SS, 16 * SS), "д (red) over the same face's own d (grey), "
            "in the frame they share -- blue rule is the x-height",
            font=ImageFont.truetype(FACE, 24 * SS), fill=(170, 30, 30))
    lab = ImageFont.truetype(FACE, 18 * SS)
    for i, (fam, de, d, top) in enumerate(cells):
        x = (24 + (i % COLS) * cw) * SS
        y = (66 + (i // COLS) * ch) * SS
        c = tile(de, d, top, CELL * SS)
        im.paste(c, (x + (CELL * SS - c.width) // 2, y))
        dr.text((x, y + (CELL + 12) * SS), fam[:20], font=lab,
                fill=(110, 110, 110))
    im.save("tools/out/de_vs_d.png")
    print("\n   wrote tools/out/de_vs_d.png", im.size)


if __name__ == "__main__":
    main()
