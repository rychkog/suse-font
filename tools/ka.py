"""Where does К's leg start -- on the stem, or on the arm?

    ./venv/bin/python tools/ka.py            # ours, then the panel
    ./venv/bin/python tools/ka.py --draw     # the reading, drawn over the ink

К is the one letter of the twenty-five the Latin donates where the panel does
not simply agree: 31 of 65 faces draw it apart from K. This reads WHAT they do
differently, because "drawn apart" was as far as the ink-area and overlay
readings got and a letter is not redrawn from a percentage.

There are only two structures a K-shaped letter can have, and they are told
apart by one number. Put a scanline through the letter and count the runs of
ink to the RIGHT of the stem:

  * **vertex on the stem** -- the arm comes down to the stem and the leg
    leaves from the same place. Above that point there is only the arm, below
    it only the leg: one run at every height, and the fork band is zero.
  * **the leg springs off the arm** -- the leg leaves the arm at a point out
    in the counter, and the arm carries on down to the stem underneath it.
    Between the two landings there are TWO runs beside the stem, and the
    height of that band is how far up the arm the leg starts.

So `fork` below is the height of the two-run band over the cap height. Zero is
a vertex; anything else is a branch, and the number IS the branch.

The other two figures answer the questions the band cannot. `arm` is where the
arm's own landing sits on the stem, over the cap -- Cyrillic К is commonly
described as meeting its stem higher than the Latin does. `neck` is the gap
between the stem and the nearest diagonal ink, in units of the em: a few faces
hold the whole junction clear of the stem, which is a third thing again and
would read as a broken letter if it were done by accident.

Read from the raster and not from the outline on purpose: a junction is a
question about where the ink is, and every one of these faces reaches it with
a different number of contours in a different order.
"""

import math                                                    # noqa: E402
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                             # noqa: E402
from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

# the sixteen families donated.py --panel names, plus the four the overlay
# showed the difference to be structural in
APART = ("AverageMono", "Courier New", "Fira Code", "Geist Mono", "Hasklig",
         "Ioskeley Mono", "Ioskeley Tuned", "Liberation Mono", "Lilex",
         "Lucida Console", "Maple Mono", "Monaspace Xenon", "Myna",
         "Old Timey Code", "Roboto Mono", "Victor Mono")
# 160 and not 240: every figure here is a ratio, and a letter 160 pixels tall
# already resolves a junction to better than a thousandth of the cap. The
# canvas is quadratic in this, and this probe walks 65 faces.
SZ = 160
OURS = "fonts/ttf/SUSEMono-%s.ttf"


def raster(font, ch):
    """The glyph's ink, cropped to itself, as a boolean array.

    The crop is COPIED. A numpy slice is a view that pins the whole canvas
    alive, so a caller holding a dozen crops was holding a dozen full-size
    rasters, and this machine has been brought down by less.
    """
    im = Image.new("L", (SZ * 2, int(SZ * 2.2)), 0)
    ImageDraw.Draw(im).text((SZ // 3, SZ // 3), ch, font=font, fill=255)
    a = np.asarray(im) > 127
    if not a.any():
        return None
    ys, xs = np.where(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def runs(row, x0):
    """(start, end) of every run of ink at or beyond x0."""
    out, s = [], None
    for x in range(x0, len(row)):
        if row[x] and s is None:
            s = x
        elif not row[x] and s is not None:
            out.append((s, x - 1))
            s = None
    if s is not None:
        out.append((s, len(row) - 1))
    return out


def read(a):
    """fork, arm, neck -- see the module docstring. None if there is no stem."""
    h, w = a.shape
    # the stem is the first column run that is ink nearly all the way down.
    # Read at 0.9 so a flat-cut diagonal's own column cannot qualify.
    tall = a.sum(0) > 0.9 * h
    if not tall.any():
        return None
    stem_r = np.flatnonzero(tall)[0]
    while stem_r + 1 < w and tall[stem_r + 1]:
        stem_r += 1

    # everything beyond the stem, one scanline at a time
    gap = max(1, w // 120)
    band, near, land = 0, w, []
    for y in range(h):
        r = runs(a[y], stem_r + 1)
        if not r:
            continue
        near = min(near, r[0][0] - stem_r)
        if r[0][0] - stem_r <= gap:
            land.append(y)
        if len(r) > 1:
            band += 1
    if not land:
        # nothing reaches the stem at all: the junction is held clear of it
        return band / float(h), None, (near - 1) / float(h)
    # the arm's landing is the contact furthest from the letter's own ends;
    # a K lands on the stem in one place and a fork lands in one place too
    mid = sum(land) / float(len(land))
    return band / float(h), 1.0 - mid / float(h), 0.0


def apex(a):
    """Where the white wedge between the arm and the leg comes to a point.

    The one figure that says how a К is built. Read off the ink: walk every
    scanline, find the first run of white AFTER the ink that touches the stem,
    and take the leftmost such start over the whole letter. That point is the
    apex, and the distance from the stem's right edge out to it is the NECK --
    the length of merged stroke the arm and the leg share before they part.

    A neck of zero is arm and leg meeting the stem at a point, which is what
    this project built first. Roboto Mono's К has a neck of 126 units per
    thousand at its light weight and 166 at its heaviest, drawn as a short
    horizontal shelf off the stem, and its Ж-like consequence is the whole
    reason its diagonals are steeper than ours were.

    Returns (neck, apex height), both over the letter's own height.
    """
    h, w = a.shape
    tall = a.sum(0) > 0.9 * h
    if not tall.any():
        return None
    s = np.flatnonzero(tall)[0]
    while s + 1 < w and tall[s + 1]:
        s += 1
    best = None
    for y in range(h):
        r = runs(a[y], s + 1)
        if not r or r[0][0] > s + max(1, w // 120):
            continue
        # the white that starts where the stem-borne ink ends
        gap = r[0][1] + 1
        if gap >= w:
            continue
        if best is None or gap < best[0]:
            best = (gap, y)
    if best is None:
        return None
    return (best[0] - s) / float(h), 1.0 - best[1] / float(h)


def spike(a):
    """The angle the arm's flat top cut makes with the arm itself, degrees.

    The sharp corner at the far end of the arm. It is not free: a stroke that
    lands at the middle of the cap instead of a third of the way up covers the
    same horizontal run in two thirds of the height, so it leans further and
    the corner where the flat cut meets it closes. The audit compares this
    against the face's own Latin, which has no letter with a diagonal this
    flat -- so the only fair comparison is other faces' Cyrillic К.

    Read off the outer edge over the top eighth of the letter, which is well
    clear of the junction and long enough not to be a rounding.
    """
    h, w = a.shape
    n = max(3, h // 8)
    xs = [max(np.flatnonzero(a[y])) for y in range(n) if a[y].any()]
    if len(xs) < 3:
        return None
    return math.degrees(math.atan2(len(xs) - 1.0, max(xs) - min(xs) + 1e-9))


def show(name, a):
    r = read(a)
    if r is None:
        return None
    fork, arm, neck = r
    sp = spike(a)
    print("   %-26s fork %5.3f   arm %s   neck %s   spike %s"
          % (name, fork,
             "  --  " if arm is None else "%5.3f" % arm,
             "  --  " if not neck else "%5.3f" % neck,
             " -- " if sp is None else "%3.0f" % sp))
    return r


def _draw(cells):
    """The two-run band drawn on the letters it was read from."""
    pad, cw = 18, SZ + 90
    W, H = pad + len(cells) * (cw + pad), 150 + int(SZ * 1.4)
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    lab = ImageFont.truetype(OURS % "Regular", 19)
    d.text((pad, 22), "the leg leaves the arm here -- red is the band where "
           "two strokes run beside the stem",
           font=ImageFont.truetype(OURS % "Regular", 26), fill=(170, 30, 30))
    for i, (name, a) in enumerate(cells):
        x0, y0 = pad + i * (cw + pad), 80
        h, w = a.shape
        rgb = np.full((h, w, 3), 255, np.uint8)
        rgb[a] = (25, 25, 25)
        tall = a.sum(0) > 0.9 * h
        if tall.any():
            s = np.flatnonzero(tall)[0]
            while s + 1 < w and tall[s + 1]:
                s += 1
            for y in range(h):
                if len(runs(a[y], s + 1)) > 1:
                    rgb[y, s + 1:] = np.where(a[y, s + 1:, None],
                                              (215, 40, 40), rgb[y, s + 1:])
        c = Image.fromarray(rgb)
        c.thumbnail((cw, int(SZ * 1.25)), Image.LANCZOS)
        im.paste(c, (x0 + (cw - c.width) // 2, y0))
        d.text((x0, y0 + int(SZ * 1.3)), name, font=lab, fill=(110, 110, 110))
    im.save("tools/out/ka_fork.png")
    print("\n   wrote tools/out/ka_fork.png")


BRANCH = 0.05           # a fork band under this is a vertex, not a branch


def main():
    """Ours at three weights, then the question the panel can answer.

    Ж is deliberately not read here. The probe assumes a stem with the whole
    letter to the right of it, and Ж has its stem in the MIDDLE with two arms
    on each side -- at ExtraBold the left arms are wide enough to be the first
    column that is ink nearly all the way down, so "beside the stem" starts in
    the wrong place and the band reads 0.857 for a letter that has no fork at
    all. Ж's waist is an exact figure in the recipe anyway (ZHE_WAIST) and
    needs no raster to read.
    """
    from panel import families
    cells, draw_it = [], "--draw" in sys.argv
    draw = draw_it
    print("\n   ours -- the Latin the Cyrillic is taken from\n")
    for w in ("Thin", "Regular", "ExtraBold"):
        f = ImageFont.truetype(OURS % w, SZ)
        for ch in "Kk":
            a = raster(f, ch)
            if (a is not None and show("%s %s" % (ch, w), a)
                    and draw_it and w == "Regular"):
                cells.append(("%s ours" % ch, a))
    print("\n   and the junction our own approved Ж already puts on its stem:"
          "\n   %-26s          arm %5.3f  (ZHE_WAIST, both masters)"
          % ("Ж ж ours", 0.517))

    print("\n   the panel: what does a face do with a BRANCHED Latin K?\n")
    from fontTools.ttLib import TTFont
    from probe import contours
    keep, flat, given, n, novote = [], [], 0, 0, 0
    for fam, path in families():
        try:
            f = ImageFont.truetype(path, SZ)
        except Exception:
            continue
        la, cy = raster(f, "K"), raster(f, "К")
        if la is None or cy is None:
            continue
        rl, rc = read(la), read(cy)
        if rl is None or rc is None:
            continue
        n += 1
        if rl[0] < BRANCH:
            # its Latin K has no branch to keep or lose: not a vote
            novote += 1
            continue
        # a face that hands К the same outline never asked the question. It is
        # not evidence for the branch, and this lineage is repeated -- DejaVu,
        # Menlo, Meslo, Hack, Monotional and Inconsolata LGC are one drawing.
        try:
            t = TTFont(path, fontNumber=0, lazy=True)
            cm, gs = t.getBestCmap(), t.getGlyphSet()
            same = (contours(t, cm[0x41A], cm, gs)
                    == contours(t, cm[0x4B], cm, gs))
            t.close()
        except Exception:
            same = False
        if same:
            given += 1
            continue
        (keep if rc[0] >= BRANCH else flat).append(
            "%s (%.2f -> %.2f)" % (fam, rl[0], rc[0]))
        # only keep a raster if it is going to be drawn
        if draw and fam in ("Geist Mono", "Roboto Mono", "Lilex"):
            cells += [("K %s" % fam, la), ("Cyrillic %s" % fam, cy)]
    print("   %d faces carry both letters; %d draw K with a vertex already,"
          "\n   so they have no branch to keep and are not a vote.\n"
          % (n, novote))
    print("   %d of the remaining %d hand К the same outline -- they never"
          "\n   asked the question either.\n" % (given, given + len(keep)
                                                 + len(flat)))
    print("   so %d faces have a branched Latin K and REDREW the Cyrillic:"
          % (len(keep) + len(flat)))
    print("     %2d replaced the branch with a single vertex" % len(flat))
    for s in sorted(flat):
        print("        %s" % s)
    print("     %2d kept a branch" % len(keep))
    for s in sorted(keep):
        print("        %s" % s)
    if draw_it:
        _draw(cells)


if __name__ == "__main__":
    main()
