"""Where д's arm goes and how it ENDS -- the reading every other probe misses.

    ./venv/bin/python tools/de_arm.py

`gd_band.py` reads д's hook, junction, height and width, and our д sat inside
three of those four while the tail was rejected on sight. Every figure there is
a size. None of them says where the arm ends or what it ends WITH, which is the
thing that was wrong. METHOD F13, and rule 9 in CLAUDE.md -- ask whether it is
the right letter before asking whether it is the right size.

Read above the x-height, against the face's own o:

  reach   the arm's leftmost point, as a fraction ACROSS the bowl. 0.0 is
          flush with the bowl's left edge, 1.0 flush with its right, and
          negative means the arm has taken over the letter's left sidebearing.
  rise    how high the arm goes above the x-height, over o's height -- the
          ascender the letter is spending.
  tipwt   the ink at the arm's tip over o's wall. This is the one that caught
          it: a stroke that tapers to a fraction of a wall is a hairline flag
          and not a terminal, and ours read 1.01 at Thin against 0.21 at
          ExtraBold -- not even the same terminal at the two masters.

The bowl is measured from the rows BELOW the x-height, so a long arm cannot
quietly redefine the bowl's own box -- which is how this letter passed `д's
width over o's` at 1.00 while being drawn wrong.

**Only the ∂-form counts.** Inconsolata LGC, Sudo and Victor Mono draw д with a
DESCENDER -- a g-form, a different letter -- and their arms answer a different
question. They were in the band on the first run and dragged the tip figure
down; `gd_band.py` had excluded them only by accident, because the probe that
finds a branch happens to return nothing for them.
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
CELL = 300
DESCEND = 0.15          # below this much of o's height, it is the ∂-form


def box(m):
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def read(path):
    """(reach, rise, tipwt, mask, split, tip-crop) for one face, or a reason."""
    o = W.render(path, "o", XH)
    d = W.render(path, "д", XH)
    if o is None or d is None:
        return "no o or no д"
    wall = W.width(W.edt(o))
    ox0, oy0, ox1, oy1 = box(o)
    oh, ow = oy1 - oy0, ox1 - ox0
    _dx0, dy0, _dx1, dy1 = box(d)
    if (dy1 - oy1) / float(oh) > DESCEND:
        return "draws the g-form, with a descender -- a different letter"
    split = dy1 - oh
    if split <= dy0 + 2:
        return "no arm above the x-height"
    above, below = d[:split], d[split:]
    if not above.any() or not below.any():
        return "no arm above the x-height"
    bx0, _, bx1, _ = box(below)
    ax0, ay0, _, _ = box(above)
    bw = float(bx1 - bx0)
    # the ink AT the tip: the widest disc that fits, in the few columns at the
    # arm's leftmost end -- the terminal, and none of the run behind it.
    #
    # Read just BEHIND the terminal, not at it. The widest disc within `w` of
    # a cut end cannot be wider than `w` whatever the stroke does, and near the
    # corner itself it is smaller still, so a band that starts at the very tip
    # reads the band and the corner rather than the stroke: ours at ExtraBold
    # read 0.21 with its terminal drawn at 0.77 of the wall and cut square.
    # An eighth to a fifth of the arm's own run back from the end is clear of
    # the corner, is still the terminal's own stroke and not the arm behind it,
    # and asks a light weight and a heavy one the same question.
    e = W.edt(d)
    ax1 = np.where(above.any(axis=0))[0].max() + 1
    run = ax1 - ax0
    tip = e[:split, ax0 + max(2, int(0.08 * run)):
            ax0 + max(4, int(0.20 * run))]
    tipwt = (2.0 * tip.max() / wall) if tip.any() and wall else None
    # the arm's own weight, along the arm. `weights.branch_of` reads by ROWS
    # and trims the last of them by the bowl's wall, which is two wrong things
    # for this letter: the arm curves over the top, so a row cuts across it
    # only where it happens to be upright, and a trim that depends on the
    # junction means changing the junction moves this reading and moves the
    # solve that targets it. CLAUDE.md rule 5, two constants justifying each
    # other. Read down the arm's own columns instead, dropping a sixth at each
    # end -- the terminal's cut at one end, the bowl at the other.
    cols = np.where(above.any(axis=0))[0]
    drop = max(1, len(cols) // 6)
    ridge = [2.0 * e[:split, c].max() / wall for c in cols[drop:-drop]]
    armwt = st.median(ridge) if ridge and wall else None
    # FLAT: how much of the arm's top edge is level. A written stroke has one
    # highest point and falls away from it both ways; a flat run across the top
    # is an awning, and it is what makes ours read as a bar laid over the bowl
    # rather than a stroke leaving it. Counted as the share of the arm's
    # columns whose top edge sits within a fiftieth of o's height of the very
    # highest -- a share, so a long arm and a short one are asked the same
    # question.
    tops = np.array([np.argmax(above[:, c]) for c in cols])
    flat = float((tops <= tops.min() + 0.02 * oh).sum()) / len(cols)
    # TAPER: the free end's thickness over the junction end's. Below 1 the
    # stroke thins as it leaves, which is what a pen does.
    k = max(1, len(cols) // 6)
    head = [2.0 * e[:split, c].max() for c in cols[:k]]
    foot = [2.0 * e[:split, c].max() for c in cols[-k:]]
    taper = st.median(head) / st.median(foot) if foot and st.median(foot) else None
    pad = int(0.10 * ow)
    crop = d[max(0, ay0 - pad):split,
             max(0, ax0 - pad):ax0 + int(0.45 * bw)].copy()
    return ((ax0 - bx0) / bw, (split - ay0) / float(oh), tipwt, armwt,
            flat, taper, d, split, crop)


def tile(m, ink, cell=CELL * SS, rule=None):
    """A mask blown up to fill its cell, nearest so the edge stays honest."""
    h, w = m.shape
    rgb = np.full((h, w, 3), 255, np.uint8)
    rgb[m] = ink
    if rule is not None and 0 < rule < h:
        rgb[max(0, rule - 1):rule + 1] = (150, 190, 255)
    s = min(cell / float(w), cell / float(h))
    im = Image.fromarray(rgb)
    return im.resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)


def main():
    from panel import italics
    from gd_band import is_cursive_ge

    OURS = "fonts/ttf/SUSEMono-%sItalic.ttf"
    rows, cells = [], []
    # all three of ours, because the fault is that the terminal is not the
    # same terminal at the two masters and one weight cannot show that
    for w in ("Thin", "Regular", "ExtraBold"):
        got = read(OURS % w)
        if not isinstance(got, str):
            rows.append(("ours, " + w,) + got[:6])
            cells.append(("ours, " + w, (25, 25, 25), got[6], got[7], got[8]))

    for fam, path in sorted(italics()):
        try:
            g = W.render(path, "г", XH)
            if g is None or not is_cursive_ge(g):
                continue
            got = read(path)
            if isinstance(got, str):
                print("   %-22s %s" % (fam, got))
                continue
            rows.append((fam,) + got[:6])
            cells.append((fam, (185, 30, 30), got[6], got[7], got[8]))
        except Exception as e:
            print("   %-22s %s" % (fam, e))

    print("\n   %-22s %6s %6s %6s %6s %6s %6s"
          % ("", "reach", "rise", "tipwt", "armwt", "flat", "taper"))
    for r in rows:
        print("   %-22s %s"
              % (r[0], " ".join("%6s" % ("  .  " if v is None else "%6.2f" % v)
                                for v in r[1:])))

    ref = [r for r in rows if not r[0].startswith("ours")]
    print()
    for i, what in ((1, "arm's reach across the bowl"),
                    (2, "arm's rise over o's height"),
                    (3, "ink at the tip over o's wall"),
                    (4, "the arm's own weight over o's wall"),
                    (5, "share of the top edge that is flat"),
                    (6, "free end's thickness over the root's")):
        v = sorted(r[i] for r in ref if r[i] is not None)
        print("   %-30s median %5.2f, %5.2f..%5.2f  (%d faces)"
              % (what, st.median(v), v[1], v[-2], len(v)))

    # a GRID and not one long strip. Anything wider than about two thousand
    # pixels is looked at scaled down, so a strip of eleven cells arrives at a
    # sixth of the size it was drawn -- which is the pixelation this project
    # has been caught by twice. Four across keeps every cell big enough to
    # judge a terminal by.
    COLS = 4
    zoom = CELL * 3 // 5
    cw, ch = CELL + 30, CELL + zoom + 78
    rowsn = (len(cells) + COLS - 1) // COLS
    W_, H_ = 24 + COLS * cw, 70 + rowsn * ch
    im = Image.new("RGB", (W_ * SS, H_ * SS), "white")
    d = ImageDraw.Draw(im)
    d.text((24 * SS, 16 * SS), "д's arm above the x-height (blue rule), and "
           "under each one the terminal it ends with, magnified",
           font=ImageFont.truetype(FACE, 26 * SS), fill=(170, 30, 30))
    lab = ImageFont.truetype(FACE, 18 * SS)
    for i, (fam, ink, m, split, crop) in enumerate(cells):
        x = (24 + (i % COLS) * cw) * SS
        y = (70 + (i // COLS) * ch) * SS
        c = tile(m, ink, rule=split)
        im.paste(c, (x + (CELL * SS - c.width) // 2, y))
        z = tile(crop, ink, cell=zoom * SS)
        im.paste(z, (x + (CELL * SS - z.width) // 2, y + (CELL + 16) * SS))
        d.text((x, y + (CELL + zoom + 32) * SS), fam[:20], font=lab,
               fill=(110, 110, 110))
    im.save("tools/out/de_arm.png")
    print("\n   wrote tools/out/de_arm.png", im.size)


if __name__ == "__main__":
    main()
