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

# The em. The advance is 600 and the two are not the same number; using the
# advance to index the panel by stem is a bug this file has already made.
UPM = 1000.0


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

    # The walls' PERPENDICULAR weight, not their horizontal footprint. Across
    # the counter's own rows the only ink is the two walls, so the largest
    # disc that fits there is the thicker one's true thickness -- whatever
    # angle it leans at, which a scanline cannot say. Same quantity and same
    # instrument weights.py reads a stroke with.
    band = m[ct:cb + 1]
    wall = W.width(ndimage.distance_transform_edt(band)) if band.any() else 0.0

    # The legs: how far they drop below the plinth, and how much white they
    # keep between them. Below the counter the plinth reads as ONE run and the
    # legs as two, which tells them apart without knowing where the baseline
    # is on a raster.
    leg_rows = [np.where(r)[0] for r in m[cb + 1:] if r.any()]
    legs = [r for r in leg_rows
            if len(np.where(np.diff(r) > 1)[0]) == 1]
    gap = leg_w = 0.0
    if legs:
        mid_r = legs[len(legs) // 2]
        cut = int(np.argmax(np.diff(mid_r)))
        gap = float(mid_r[cut + 1] - mid_r[cut] - 1)
        # each leg's own width, which is what decides the gap once the plinth
        # is against the sidebearing and cannot grow
        leg_w = float(cut + 1)

    # How far the body's left edge travels across the counter's own height,
    # as a share of that height. Д's counter is bounded on the left by a
    # slanted leg, so the slant is a second lever on the counter's width --
    # and one that does not touch the letter's width at all, which the first
    # attempt did and was rejected for.
    top_on = np.where(m[ct])[0]
    bot_on = np.where(m[cb])[0]
    lean = 0.0
    if len(top_on) and len(bot_on) and cb > ct:
        lean = float(top_on.min() - bot_on.min()) / float(cb - ct)

    return {"lean": lean,
            "wall/stem": wall / stem if stem else 0.0,
            "leg w/stem": leg_w / stem if stem else 0.0,
            "leg drop/xh": len(legs) / float(W.XH),
            "leg gap/stem": gap / stem if stem else 0.0,
            "plinth/span_h": plinth / span_h if span_h else 0.0,
            "jut/stem": (plinth - span_h) / 2.0 / stem if stem else 0.0,
            "span_h/adv": span_h / adv_px,
            "span_v/xh": span_v / float(W.XH),
            "counter_w/span_h": counter_w / span_h,
            "counter_h/span_v": counter_h / span_v,
            "walls/stem": (span_h - counter_w) / stem,
            "arm/stem": (span_v - counter_h) / stem}


KEYS = ("lean", "counter_w/span_h", "span_h/adv",
        "leg w/stem", "leg gap/stem")


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
    """Д's lean, bisected against the panel's own, per case per master.

    Measured on the rendered glyph from the recipes, so it is the artefact and
    not a model of it, and per master because the target is not flat -- the
    panel straightens its Д as the face gets bolder.
    """
    import glyphsLib
    from params import Params, Lower, _flatten
    import recipes as RU
    from PIL import Image, ImageChops, ImageDraw

    ref = panel()
    font = glyphsLib.load(open("sources/SUSEMono.glyphs"))
    keep = RU.DE_LEAN

    def read_at(pr, name, k=None):
        RU.DE_LEAN = (keep if k is None else
                      {c: (k, 0.0, k, k) for c in keep})
        paths = RU.RECIPES[name](pr._pr if name == "De-cy" else pr)
        polys = [[(x, y) for x, y in _flatten(p, 96)] for p in paths]
        xs = [q[0] for p in polys for q in p]
        ys = [q[1] for p in polys for q in p]
        sc = W.XH / float(pr.cap)
        w = int((max(xs) - min(xs)) * sc) + 8
        h = int((max(ys) - min(ys)) * sc) + 8
        img = Image.new("1", (w, h), 0)
        for poly in polys:
            lay = Image.new("1", (w, h), 0)
            ImageDraw.Draw(lay).polygon(
                [(4 + (x - min(xs)) * sc, h - 4 - (y - min(ys)) * sc)
                 for x, y in poly], fill=1)
            img = ImageChops.logical_xor(img, lay)
        return read_mask(np.asarray(img) > 0, 600.0 * sc, pr.stem)

    print("Д's lean solved against the panel's own, per case per master\n")
    solved = {}
    for case, ch, name in (("cap", "Д", "De-cy"), ("lc", "д", "de-cy")):
        pts = [(s, r["lean"]) for s, r in ref[ch]]
        for mi, wname in ((0, "Thin"), (1, "ExtraBold")):
            pr = Lower(Params(font, mi))
            here = pr._pr if case == "cap" else pr
            # stem over the EM, which is 1000. The advance is 600 and dividing
            # by that instead put this face's Thin at 0.048 and its ExtraBold
            # at 0.268, where `Face.stem_em` -- the same quantity the panel is
            # indexed by -- reads 0.029 and 0.161. Nearly 1.67 times too
            # heavy, so `compare` handed back the median of faces far bolder
            # than this one and every target solved against it was the wrong
            # bucket's. The width solve that was rejected by eye used it too.
            want = P.compare(pts, here.stem / float(UPM), 0.0)[0]
            # a leg straight enough merges into the stem and the counter
            # stops being a separate region: that is "too straight", and it
            # has to be said or the bisection walks to that bound
            lo, hi = 0.30, 1.10
            for _ in range(20):
                mid = 0.5 * (lo + hi)
                r = read_at(pr, name, mid)
                if r is None or r["lean"] > want:
                    hi = mid
                else:
                    lo = mid
            k = 0.5 * (lo + hi)
            got = read_at(pr, name, k)
            RU.DE_LEAN = keep
            now = read_at(pr, name)
            solved[(case, mi)] = (here.stem, k)
            print("  %s %-10s want %.3f   now %.3f -> %.3f   k %.3f   "
                  "counter_w/span %.3f -> %.3f"
                  % (ch, wname, want, now["lean"], got["lean"], k,
                     now["counter_w/span_h"], got["counter_w/span_h"]))
    RU.DE_LEAN = keep
    print("\nDE_LEAN = {")
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
