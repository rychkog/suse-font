"""Does a face draw д's bowl the same size as its own o? And б's?

The question came from the eye: д's ellipse "much bigger than o". Ours cannot
be bigger in the COUNTER -- д's counter is o's own inner contour, the same
points -- so if it reads bigger, either the bowl around it is bigger or the
letter is being compensated somewhere every reference compensates it.

A letter that hangs a stroke off a round has a reason to shrink that round: the
arm adds ink on one side, and o's width was fitted to o alone. Whether the
panel actually does that is a question about a RELATION, which is what a panel
can answer. It cannot say what size SUSE Mono's bowl should be -- only whether
the relation exists and how tight it is.

Read below the x-height only, so the arm never enters the width, and against
each face's OWN o so the comparison survives faces of different width.

    ./venv/bin/python tools/de_bowl.py
"""
import sys

sys.path.insert(0, "tools")

import numpy as np

import weights as W
from panel import italics

XH = 200
DESCEND = 0.15          # below this much of o's height, it is the ∂-form


def box(m):
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def counter(m):
    """The area and bbox of the letter's enclosed white, or None.

    The white that is NOT reachable from the border. A bowl's counter is the
    biggest such region; anything smaller is a nick between strokes.
    """
    from scipy.ndimage import label
    pad = np.zeros((m.shape[0] + 2, m.shape[1] + 2), bool)
    pad[1:-1, 1:-1] = m
    lab, n = label(~pad)
    if n < 2:
        return None
    out = lab[0, 0]
    best, area = None, 0
    for i in range(1, n + 1):
        if i == out:
            continue
        a = int((lab == i).sum())
        if a > area:
            best, area = i, a
    if best is None:
        return None
    return area, box(lab == best)


def read(path):
    """(o, д, б) readings for one face, or a reason it is not evidence."""
    o = W.render(path, "o", XH)
    d = W.render(path, "д", XH)
    b = W.render(path, "б", XH)
    if o is None or d is None:
        return "no o or no д"
    ox0, oy0, ox1, oy1 = box(o)
    oh, ow = float(oy1 - oy0), float(ox1 - ox0)
    _x0, _y0, _x1, dy1 = box(d)
    if (dy1 - oy1) / oh > DESCEND:
        return "draws the g-form, with a descender -- a different letter"

    oc = counter(o)
    if oc is None:
        return "o has no counter to read"

    # д's BOWL: the ink from the x-height down. The arm lives above it, so it
    # cannot widen this reading; a bowl is what is left when the arm is gone.
    split = dy1 - int(round(oh))
    bowl = d[max(0, split):]
    if not bowl.any():
        return "nothing below the x-height"
    bx0, _by0, bx1, _by1 = box(bowl)
    dc = counter(d)

    row = {"д bowl w / o w": (bx1 - bx0) / ow}
    if dc is not None:
        row["д counter area / o's"] = dc[0] / float(oc[0])
        cx0, _cy0, cx1, _cy1 = dc[1]
        ocx0, _o0, ocx1, _o1 = oc[1]
        row["д counter w / o's"] = (cx1 - cx0) / float(ocx1 - ocx0)
    if b is not None:
        bc = counter(b)
        if bc is not None:
            row["б counter area / o's"] = bc[0] / float(oc[0])
    return row


KEYS = ("д bowl w / o w", "д counter w / o's", "д counter area / o's",
        "б counter area / o's")


def main():
    rows, skipped = [], []
    for fam, path in sorted(italics()):
        # THIS FACE IS NOT EVIDENCE ABOUT ITSELF -- `italics()` reads the fonts
        # installed on this machine and SUSE Mono is one of them.
        if fam.startswith("SUSE Mono"):
            continue
        got = read(path)
        if isinstance(got, str):
            skipped.append((fam, got))
            continue
        rows.append((fam, got))

    print("Does д's bowl match the face's own o? %d italics that draw the "
          "∂ form\n" % len(rows))
    for key in KEYS:
        vals = sorted((r[key], fam) for fam, r in rows if key in r)
        if not vals:
            continue
        lo, hi = vals[0], vals[-1]
        med = vals[len(vals) // 2][0]
        print("  %-24s %.3f .. %.3f   median %.3f"
              % (key, lo[0], hi[0], med))
        print("  %-24s narrowest %s, widest %s"
              % ("", lo[1], hi[1]))
    print()
    for fam, r in rows:
        print("  %-34s %s" % (fam, "  ".join(
            "%s %.3f" % (k.split(" / ")[0], r[k]) for k in KEYS if k in r)))
    if skipped:
        print("\n  not evidence:")
        for fam, why in skipped:
            print("    %-32s %s" % (fam, why))


if __name__ == "__main__":
    main()
