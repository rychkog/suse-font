"""How much a stroke varies in width, off the rendered ink.

`tools/weights.py` takes the single widest disc in a letter. The question
here is the SPREAD, so the same distance transform is read along the whole
ridge: every pixel whose distance beats its eight neighbours sits on the
stroke's middle, and twice its distance is the stroke there.
"""
import sys
import numpy as np
sys.path.insert(0, "tools")
from weights import render, edt, BIAS
from scipy import ndimage

R = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/MonaspaceRadon-%s_1.otf"
S = "fonts/ttf/SUSEMono-%sItalic.ttf"
XH = 260


def ridge(mask):
    d = edt(mask)
    top = ndimage.maximum_filter(d, size=3)
    keep = (d >= top - 1e-9) & (d > 1.5)
    return np.sort(2.0 * d[keep] - BIAS)


def show(path, ch, label):
    m = render(path, ch, XH)
    if m is None:
        print("  %-30s no render" % label)
        return
    w = ridge(m)
    if not len(w):
        print("  %-30s no ridge" % label)
        return
    q = lambda f: w[int(f * (len(w) - 1))]
    print("  %-30s q1 %5.1f  med %5.1f  q3 %5.1f   q3/q1 %.2f"
          % (label, q(.25), q(.5), q(.75), q(.75) / q(.25) if q(.25) else 0))


if __name__ == "__main__":
    print("stroke width along the ridge, o standing %d px:" % XH)
    for w in ("ExtraLightItalic", "ExtraBoldItalic"):
        show(R % w, "o", "Radon %-16s o" % w[:12])
        show(R % w, "в", "Radon %-16s в" % w[:12])
    for w in ("Thin", "ExtraBold"):
        show(S % w, "o", "SUSE %-18s o" % w)
        show(S % w, "в", "SUSE %-18s в" % w)
