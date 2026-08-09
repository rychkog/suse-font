"""§2 step 0 for Д and д: what is the counter cut out of, and does it grow?

    ./venv/bin/python tools/de.py            # ours, four weights
    ./venv/bin/python tools/de.py --panel    # and the panel, bucketed by stem

`relations.py` found Д and д's counter closing monotonically with weight --
nothing at Thin, 39 per cent under the panel by ExtraBold. §2 says the counter
is the symptom and going straight at it treats the symptom, and gives the
order: find the SPAN the counter is cut out of first, because no reading of
the counter itself says which of the three terms is wrong.

For this letter the span is the body: the Л that stands on the plinth. Its
counter is bounded above by the arm, below by the plinth's top, on the left by
the slanted leg and on the right by the stem. So

    span_h = the body's width where the counter is
    span_v = the body's height, arm included
    counter = span minus the strokes that bound it

and the question is whether the span moves with the weight or stands still
while the strokes grow. Measured generically off the raster, so it means the
same thing on a face that draws Д some other way:

  * the body's edges are the leftmost and rightmost ink on the row through
    the counter's middle -- which is inside the body and above the plinth, so
    the plinth's jut cannot contaminate it;
  * the arm is the ink above the counter's top;
  * the plinth is the ink below the counter's bottom, down to the baseline,
    and the legs below that are not part of the span.

One lens for ours and theirs, the same one `weights.py` and `relations.py`
read through, and one render per letter per face.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np
from scipy import ndimage

import probe as P
import weights as W
from relations import Face, OURS


def read(fc, ch, lower):
    """The span, the strokes that bound it, and what is left as counter."""
    m = fc.mask(ch)
    if m is None:
        return None
    return read_mask(m, fc.f["hmtx"][fc.cm[ord(ch)]][0] * fc.k,
                     fc.stem[lower])


def read_mask(m, adv_px, stem):
    """The same off a bare mask, so the solve can drive it from the recipes
    without a build."""
    holes = W.holes(m)
    lab, n = ndimage.label(holes)
    if not n:
        return None
    big = int(np.argmax(ndimage.sum(holes, lab, range(1, n + 1)))) + 1
    ys, xs = np.where(lab == big)
    ct, cb = ys.min(), ys.max()
    cl, cr = xs.min(), xs.max()

    rows = np.where(m.any(axis=1))[0]
    mid = (ct + cb) // 2
    on = np.where(m[mid])[0]
    if not len(on):
        return None

    span_h = float(on.max() - on.min() + 1)
    counter_w = float(cr - cl + 1)
    # the body's top is the letter's top; its floor is the counter's floor,
    # because below that is plinth and legs, which are not what the counter
    # is cut out of
    span_v = float(cb - rows.min() + 1)
    counter_h = float(cb - ct + 1)
    # The plinth is the widest ink below the counter -- wider than the body,
    # which is what makes the legs read as legs, and narrower than nothing
    # else down there, since the legs themselves are two stems apart. Measured
    # rather than assumed, because whether the body CAN be widened is exactly
    # the question the recipe says blocks it.
    below = m[cb + 1:]
    plinth = 0.0
    if below.size and below.any():
        widths = [np.where(r)[0] for r in below if r.any()]
        plinth = float(max(w.max() - w.min() + 1 for w in widths))

    return {"plinth/span_h": plinth / span_h if span_h else 0.0,
            "jut/stem": (plinth - span_h) / 2.0 / stem if stem else 0.0,
            "span_h/adv": span_h / adv_px,
            "span_v/xh": span_v / float(W.XH),
            "counter_w/span_h": counter_w / span_h,
            "counter_h/span_v": counter_h / span_v,
            "walls/stem": (span_h - counter_w) / stem,
            "arm/stem": (span_v - counter_h) / stem}


KEYS = ("span_h/adv", "plinth/span_h", "jut/stem",
        "counter_w/span_h", "walls/stem")


def ours():
    out = []
    for name, path in OURS:
        fc = Face(path)
        for ch, lower in (("Д", False), ("д", True)):
            v = read(fc, ch, lower)
            if v:
                out.append((name, ch, fc.stem_em(), v))
        fc.close()
    return out


def panel():
    from panel import families
    out = {}
    for _name, path in families():
        try:
            fc = Face(path)
        except Exception:
            continue
        try:
            for ch, lower in (("Д", False), ("д", True)):
                if ord(ch) not in fc.cm:
                    continue
                v = read(fc, ch, lower)
                if v:
                    out.setdefault(ch, []).append((fc.stem_em(), v))
        except Exception:
            pass
        finally:
            fc.close()
    return out


def solve():
    """DE_BODY per master, bisected against the panel's own span.

    The constant is a flat 0.86 and CLAUDE.md's rule is that a flat proportion
    is suspect until the panel has been bucketed by weight. Bucketed, the
    panel wants the body to be a growing share of the cell, and 0.86 is under
    it at every weight -- so the letter has been solving the wrong problem:
    the recipe holds the body narrow to protect the plinth's jut, and the jut
    is already LARGER than the panel's at every weight while the body is
    smaller. Both move the same way.

    Solved on the rendered glyph, from the recipes, so it is the artefact and
    not a model of it -- and per master, because the target is not flat.
    """
    import glyphsLib
    from params import Params, Lower, _flatten
    import recipes as RU
    from PIL import Image, ImageChops, ImageDraw

    ref = panel()
    font = glyphsLib.load(open("sources/SUSEMono.glyphs"))

    def span_of(pr, name, body=None):
        # None means "whatever the recipe's own fit says", so the before and
        # after in the report are both read off the artefact rather than one
        # of them being remembered.
        RU.DE_FIT = (keep if body is None else
                     {k: (body, 0.0, body, body) for k in keep})
        paths = RU.RECIPES[name](pr._pr if name == "De-cy" else pr)
        polys = [[(x, y) for x, y in _flatten(p, 96)] for p in paths]
        xs = [q[0] for p in polys for q in p]
        ys = [q[1] for p in polys for q in p]
        k = W.XH / float(pr.cap)
        w = int((max(xs) - min(xs)) * k) + 8
        h = int((max(ys) - min(ys)) * k) + 8
        img = Image.new("1", (w, h), 0)
        for poly in polys:
            lay = Image.new("1", (w, h), 0)
            ImageDraw.Draw(lay).polygon(
                [(4 + (x - min(xs)) * k, h - 4 - (y - min(ys)) * k)
                 for x, y in poly], fill=1)
            img = ImageChops.logical_xor(img, lay)
        m = np.asarray(img) > 0
        return read_mask(m, 600.0 * k, pr.stem)

    keep = RU.DE_FIT
    print("Д's body solved against the panel's own span, per case per master")
    print("the two cases do not share a target and so cannot share a fit\n")
    solved = {}
    for case, ch, name in (("cap", "Д", "De-cy"), ("lc", "д", "de-cy")):
        pts = [(s, r["span_h/adv"]) for s, r in ref[ch]]
        for mi, wname in ((0, "Thin"), (1, "ExtraBold")):
            pr = Lower(Params(font, mi))
            here = pr._pr if case == "cap" else pr
            want = P.compare(pts, here.stem / 600.0, 0.0)[0]
            # A body narrow enough closes the counter altogether and the
            # reading has nothing to return. That is "too narrow", not a
            # failure -- but it has to be said, because a bisection that
            # treats None as either bound silently runs to that bound, which
            # this solve has already done once.
            lo, hi = 0.80, 1.20
            for _ in range(22):
                mid = 0.5 * (lo + hi)
                r = span_of(pr, name, mid)
                if r is None or r["span_h/adv"] < want:
                    lo = mid
                else:
                    hi = mid
            b = 0.5 * (lo + hi)
            got = span_of(pr, name, b)
            RU.DE_FIT = keep
            now = span_of(pr, name)
            solved[(case, mi)] = (here.stem, b)
            print("  %s %-10s want %.3f   body %.3f -> %.3f   span %.3f "
                  "-> %.3f   plinth/body %.3f   jut/stem %.2f"
                  % (ch, wname, want, RU.de_body(here), b,
                     now["span_h/adv"], got["span_h/adv"],
                     got["plinth/span_h"], got["jut/stem"]))
    RU.DE_FIT = keep
    print("\nDE_FIT = {")
    for case in ("cap", "lc"):
        (s0, v0), (s1, v1) = solved[(case, 0)], solved[(case, 1)]
        b = (v1 - v0) / ((s1 - s0) / 1000.0)
        a = v0 - b * (s0 / 1000.0)
        print('    "%s": (%.4f, %.4f, %.3f, %.3f),'
              % (case, a, b, min(v0, v1), max(v0, v1)))
    print("}")


def main():
    if "--solve" in sys.argv:
        return solve()
    ref = panel() if "--panel" in sys.argv else {}
    print("Д д -- the span the counter is cut out of, and the strokes "
          "that bound it\n")
    hdr = "%-10s %s " % ("", "")
    for k in KEYS:
        hdr += "%18s" % k
    print(hdr)
    for name, ch, se, v in ours():
        line = "%-10s %s " % (name, ch)
        for k in KEYS:
            pts = [(s, r[k]) for s, r in ref.get(ch, []) if k in r]
            mark = ""
            if len(pts) > 5:
                c = P.compare(pts, se, v[k])
                if c:
                    mark = " " if c[3] else "!"
            line += "%17.3f%s" % (v[k], mark)
        print(line)
    if ref:
        print("\npanel medians, nearest-neighbour by stem at each of our "
              "weights\n")
        for name, ch, se, _v in ours():
            line = "%-10s %s " % (name, ch)
            for k in KEYS:
                pts = [(s, r[k]) for s, r in ref.get(ch, []) if k in r]
                c = P.compare(pts, se, 0.0) if len(pts) > 5 else None
                line += "%17.3f " % (c[0] if c else 0.0)
            print(line)
        print("\n  (%d faces draw Д, %d draw д)"
              % (len(ref.get("Д", [])), len(ref.get("д", []))))


if __name__ == "__main__":
    main()
