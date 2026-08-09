"""б's seam at every weight, without a build.

    ./venv/bin/python tools/seam.py            # ours, four weights
    ./venv/bin/python tools/seam.py --panel    # and the panel to compare
    ./venv/bin/python tools/seam.py --check    # blend vs the built fonts

`make mono` is minutes and the edit loop only ever checked the two masters,
which is where a two-master construction hides its errors: this letter reads
2.42 of the bowl's wall at Thin and 1.27 at ExtraBold, and Regular sits outside
the panel while both masters look settled.

The two masters carry identical node lists and the font interpolates them
linearly, so every instance is a blend of the two -- no build needed. `--check`
is what earns that claim: it compares the blended Regular and Bold against the
built ones, and if they disagree the assumption is wrong and that is a finding
rather than a nuisance.

What it reports, per weight:

  mass   the widest disc anywhere in the letter over the bowl's own wall.
         The junction is where every face in the panel puts its widest disc,
         so a mass there is normal; only the size is in question.
  where  that disc's position relative to the counter's box. A right number in
         the wrong place is what this letter has produced four times, so the
         place is reported beside the value and not instead of it.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np
from scipy import ndimage

import weights as W

# Where the four shipped instances sit between the two drawn masters. Read off
# the built fonts rather than assumed -- `--check` re-derives them.
WEIGHTS = (("Thin", 0.0), ("Regular", 0.43), ("Bold", 0.857),
           ("ExtraBold", 1.0))


def blend(a, b, t):
    return [[(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
             for p, q in zip(pa, pb)] for pa, pb in zip(a, b)]


def masters(ch="б"):
    """(letter, o, x-height) flattened, per master, ready to blend."""
    import glyphsLib
    from params import Params, Lower, _flatten
    from classify import TIERS
    import recipes as RU
    font = glyphsLib.load(open("sources/SUSEMono.glyphs"))
    names = {chr(cp): n for cp, n, _t, _n in TIERS if n in RU.RECIPES}
    fn = RU.RECIPES.get(names.get(ch, ""))
    out = []
    for mi in range(len(font.masters)):
        pr = Lower(Params(font, mi))
        out.append(([_flatten(p, 96) for p in (fn(pr._pr) if fn
                                               else pr.paths(ch))],
                    [_flatten(p, 96) for p in pr.paths("o")],
                    float(pr.cap)))
    return out


def read(be, o, cap):
    """(mass, dx, dy) -- the widest disc over the wall, and where it sits."""
    k = W.XH / cap
    om = W.mask_of(o, k)
    wall = W.width(W.edt(om))
    m = W.mask_of(be, k)
    d = W.edt(m)
    y, x = np.unravel_index(int(np.argmax(d)), d.shape)
    h = W.holes(m)
    lab, n = ndimage.label(h)
    if not n or not wall:
        return None
    s = ndimage.sum(h, lab, range(1, n + 1))
    ys, xs = np.where(lab == int(s.argmax()) + 1)
    ch_, cw = max(1, ys.max() - ys.min()), max(1, xs.max() - xs.min())
    return W.width(d) / wall, (x - xs.min()) / cw, (y - ys.min()) / ch_


def ours(ch="б"):
    (a_be, a_o, a_c), (b_be, b_o, b_c) = masters(ch)
    out = []
    for name, t in WEIGHTS:
        r = read(blend(a_be, b_be, t), blend(a_o, b_o, t),
                 a_c + (b_c - a_c) * t)
        if r:
            out.append((name, r))
    return out


def panel(ch="б"):
    from panel import families
    rows = []
    for fam, path in families():
        try:
            wall = W.wall(path, W.XH)
            m = W.render(path, ch, W.XH)
            if not wall or m is None:
                continue
            d = W.edt(m)
            rows.append((W.width(d) / wall, fam))
        except Exception:
            pass
    return sorted(rows)


def main():
    ch = next((a for a in sys.argv[1:] if not a.startswith("-")), "б")

    if "--check" in sys.argv:
        print("blended against built -- the interpolation claim, tested")
        got = dict(ours(ch))
        for name, _t in WEIGHTS:
            p = "fonts/ttf/SUSEMono-%s.ttf" % name
            wall = W.wall(p, W.XH)
            m = W.render(p, ch, W.XH)
            if not wall or m is None or name not in got:
                continue
            built = W.width(W.edt(m)) / wall
            mine = got[name][0]
            off = abs(mine - built) / built
            print("   %-10s blended %.2f   built %.2f   %+.1f%%  %s"
                  % (name, mine, built, 100 * (mine - built) / built,
                     "ok" if off < 0.03 else "DISAGREES"))
        return

    band = None
    if "--panel" in sys.argv:
        v = [r[0] for r in panel(ch)]
        band = (v[len(v) // 10], v[len(v) // 2], v[-1 - len(v) // 10])
        print("panel, %d faces: p10 %.2f  median %.2f  p90 %.2f"
              % (len(v), *band))

    print("%s, ours -- mass over the bowl's wall, and where it sits" % ch)
    for name, (mass, dx, dy) in ours(ch):
        flag = ""
        if band:
            flag = "  " if band[0] <= mass <= band[2] else "  OUTSIDE"
        print("   %-10s mass %.2f   at dx %+.2f dy %+.2f of the counter%s"
              % (name, mass, dx, dy, flag))


if __name__ == "__main__":
    main()
