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


def main():
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
