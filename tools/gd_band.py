"""What a cursive г and д measure, against the face's own o.

    ./venv/bin/python tools/gd_band.py

A donor supplies the SHAPE. The weight and the fitting have to be this face's,
and that means knowing what the relation is before anything is fitted -- б was
fitted to the shape first and guessed at the weight, and the guess put a blob
at its junction for three rounds.

Everything is read off the render rather than the outline, by `weights.py`,
which decides nothing: the largest disc that fits inside the ink at a point is
the stroke's thickness there, whatever direction it runs. Every figure is over
the face's OWN o, because that is the comparison a reader makes -- these
letters sit next to o in every word they appear in.

Only the faces that actually draw the cursive are counted. An italic that
keeps the upright г is not evidence about a letter it does not draw, and one
is here: Roboto Mono slopes its Cyrillic and leaves the construction alone.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import statistics as st                                        # noqa: E402

import numpy as np                                             # noqa: E402
from fontTools.ttLib import TTFont                             # noqa: E402

import weights as W                                            # noqa: E402
from probe import lc_stem_of                                   # noqa: E402

XH = 240                # ratios resolve fine here, and the EDT stays cheap


def box(m):
    ys, xs = np.where(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def is_cursive_ge(m):
    """Ƨ or Г? The bottom of a cursive г runs right; an upright Г's does not.

    Read at a twentieth of the letter's height, where Г has only its stem and
    the cursive has its foot.
    """
    x0, y0, x1, y1 = box(m)
    row = m[int(y1 - 1 - 0.05 * (y1 - y0))]
    xs = np.where(row)[0]
    return len(xs) and (xs.mean() - x0) / float(x1 - x0) > 0.35


def main():
    from panel import italics
    rows = []
    for fam, path in sorted(italics()):
        # this face is not evidence about itself -- see de_arm.py
        if fam.startswith("SUSE Mono"):
            continue
        try:
            o = W.render(path, "o", XH)
            if o is None:
                continue
            wall = W.width(W.edt(o))
            g = W.render(path, "г", XH)
            d = W.render(path, "д", XH)
            if g is None or d is None or not wall:
                continue
            if not is_cursive_ge(g):
                print("   %-22s slopes its upright -- not counted" % fam)
                continue
            f = TTFont(path, fontNumber=0, lazy=True)
            try:
                s = lc_stem_of(f)
                upem = float(f["head"].unitsPerEm)
            finally:
                f.close()
            if not s:
                continue
            ox0, oy0, ox1, oy1 = box(o)
            gx0, gy0, gx1, gy1 = box(g)
            dx0, dy0, dx1, dy1 = box(d)
            hook = W.branch_of(d)
            rows.append((
                s / upem, fam,
                W.width(W.edt(g)) / wall,              # г's stroke
                (gx1 - gx0) / float(ox1 - ox0),        # г's width
                (gy1 - gy0) / float(oy1 - oy0),        # г's height
                (st.median(hook) / wall) if hook else None,   # д's hook
                W.junction(d, wall),                   # д's junction swell
                (dy1 - dy0) / float(oy1 - oy0),        # д's height
                (dx1 - dx0) / float(ox1 - ox0)))       # д's width
        except Exception as e:
            print("   %-22s %s" % (fam, e))

    rows.sort()
    print("\n   %-22s %5s | %-17s | %-23s" % ("", "stem", "г  over o",
                                                "д  over o"))
    print("   %-22s %5s | %5s %5s %5s | %5s %5s %5s %5s"
          % ("", "/em", "ink", "wide", "tall", "hook", "join", "tall", "wide"))
    for s, fam, gs, gw, gh, dh, dj, dt, dw in rows:
        print("   %-22s %.3f | %5.2f %5.2f %5.2f | %5s %5.2f %5.2f %5.2f"
              % (fam, s, gs, gw, gh,
                 "  .  " if dh is None else "%5.2f" % dh, dj, dt, dw))

    def band(i, lo=0.0):
        v = sorted(r[i] for r in rows if r[i] is not None)
        return st.median(v), v[1], v[-2]

    print()
    for i, what in ((2, "г's stroke over o's wall"), (3, "г's width over o's"),
                    (4, "г's height over o's"), (5, "д's hook over o's wall"),
                    (6, "д's junction over o's wall"),
                    (7, "д's height over o's"), (8, "д's width over o's")):
        m, lo, hi = band(i)
        print("   %-26s median %.2f, %.2f..%.2f" % (what, m, lo, hi))

    # and ours, at both masters, for the same quantities
    print("\n   ours, per weight")
    for w in ("Thin", "Regular", "ExtraBold"):
        p = "fonts/ttf/SUSEMono-%sItalic.ttf" % w
        try:
            o = W.render(p, "o", XH)
            g = W.render(p, "г", XH)
            d = W.render(p, "д", XH)
        except Exception:
            continue
        if o is None or g is None or d is None:
            continue
        wall = W.width(W.edt(o))
        ox0, oy0, ox1, oy1 = box(o)
        gx0, gy0, gx1, gy1 = box(g)
        dx0, dy0, dx1, dy1 = box(d)
        hook = W.branch_of(d)
        print("   %-22s      | %5.2f %5.2f %5.2f | %5s %5.2f %5.2f %5.2f"
              % (w, W.width(W.edt(g)) / wall, (gx1 - gx0) / float(ox1 - ox0),
                 (gy1 - gy0) / float(oy1 - oy0),
                 "  .  " if not hook else "%5.2f" % (st.median(hook) / wall),
                 W.junction(d, wall),
                 (dy1 - dy0) / float(oy1 - oy0),
                 (dx1 - dx0) / float(ox1 - ox0)))


if __name__ == "__main__":
    main()
