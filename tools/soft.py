"""§2 step 0 for Б, Ь and Ы: what is the bowl's counter cut out of?

    ./venv/bin/python tools/soft.py            # ours, four weights
    ./venv/bin/python tools/soft.py --panel    # and the panel, bucketed by stem

Two independent readings arrived at these three letters. METHOD's standing
thread had Ь and Б's counters just outside the panel at the heavy end where В,
which shares the same `soft_bowl`, is inside; `relations.py` came at it from a
different reading, agreed, and added Ы. Neither said why.

§2 says the counter is the symptom and gives the order: find the SPAN it is cut
out of first. Here the span is the bowl — from the spine's left edge to the
bowl's outer right edge, across the counter's own rows — so

    span     = spine + counter + bowl wall
    counter  = span minus the two strokes that bound it

and the question is which of the three terms is wrong. Д taught the rest of it
twice over: a counter narrow inside a span that is ALSO narrow is a fact about
a narrow face, not a fault, and the panel's median width is not this face's
target unless the letter it should be measured against is inside it.

**В and в are the control and cannot be wrong.** В is the Latin B unchanged, a
tier-1 donor, and its lower lobe IS the shape `soft_bowl` reproduces. So its
readings say what this face does with this bowl, and any reading where В sits
outside the panel alongside Б Ь Ы is a reading about SUSE Mono rather than
about the three drawn letters. That is the whole reason it is measured here.

One lens for ours and theirs -- `weights.py`'s render, each face scaled so its
own o stands XH high -- and one render per letter per face.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np
from scipy import ndimage

import probe as P
import weights as W
from relations import Face, OURS

# The em. The advance is 600 and the two are not the same number; indexing the
# panel by stem/advance is a bug this tree has already made once -- see F6.
UPM = 1000.0

# The drawn three, then the two the thread already settled, then the control.
# Order matters only for reading the output.
GLYPHS = (("Б", False), ("Ь", False), ("Ы", False),
          ("Ъ", False), ("В", False), ("B", False),
          ("ь", True), ("ы", True), ("ъ", True), ("в", True), ("b", True))

LIVE = ("Б", "Ь", "Ы", "ь", "ы")

KEYS = ("span/adv", "counter w/span", "counter w/stem",
        "spine/stem", "wall/stem", "counter h/xh", "reach/adv")

# Each drawn letter against the face's own LATIN, per face -- the form that
# settled м's diagonals. Every reading above is absolute, and this face's B is
# itself outside the panel on most of them, so an absolute reading cannot say
# whether Б Ь Ы are wrong or whether SUSE Mono's B is simply narrow. The ratio
# can: it asks what each face does with the SAME bowl in the two letters, and
# is blind to how wide that face draws it.
#
# **B and b, not В and в.** В is the Latin B unchanged, so either name gives
# the same outline -- but в is DRAWN here, from the same `bowl_of` and the
# same `bowl_pair` as the letters under test. Divide by в and any fault the
# construction shares cancels exactly, and the reading reports zero. That is
# how the lowercase first came back clean. A control has to be a letter this
# project did not draw.
PAIRS = (("Б", "B"), ("Ь", "B"), ("Ы", "B"), ("Ъ", "B"), ("В", "B"),
         ("ь", "b"), ("ы", "b"), ("ъ", "b"), ("в", "b"))
PAIR_KEYS = ("counter w/span", "counter w/stem", "span/adv", "spine/stem")


def read_mask(m, adv_px, stem):
    """The bowl's span, the two strokes that bound it, and what is left.

    The bowl taken is the LOWEST counter in the letter, which is what
    `soft_bowl` draws and what В's lower lobe is. Picking the largest instead
    reads В's upper lobe on some faces and its lower on others, and then the
    control is not one measurement.

    The two bounding strokes are found by ADJACENCY to the counter rather than
    by position in the row: Ы puts a detached stem to the right of its bowl, so
    "the last run on the row" is a different stroke in that letter than in the
    other four, and a reading that means two things is worth nothing.
    """
    holes = W.holes(m)
    lab, n = ndimage.label(holes)
    if not n:
        return None
    area = ndimage.sum(holes, lab, range(1, n + 1))
    # A speck at a junction is not a counter. Anything under a twentieth of the
    # biggest hole is one, and this face draws several.
    keep = [i + 1 for i in range(n) if area[i] > 0.05 * area.max()]
    if not keep:
        return None
    bottom = {i: np.where(lab == i)[0].max() for i in keep}
    big = max(keep, key=lambda i: bottom[i])

    ys, xs = np.where(lab == big)
    ct, cb = int(ys.min()), int(ys.max())

    # The counter at its WIDEST row, not at its middle: a bowl's counter is a
    # rounded shape and its middle row is not reliably its widest, so a span
    # read at the middle carries a different slice of the curve on every face.
    rows = [(int((xs[ys == y]).max() - (xs[ys == y]).min() + 1), int(y))
            for y in range(ct, cb + 1) if (ys == y).any()]
    if not rows:
        return None
    counter_w, wy = max(rows)
    cl = int(xs[ys == wy].min())
    cr = int(xs[ys == wy].max())

    on = np.where(m[wy])[0]
    if not len(on):
        return None
    # runs on the counter's widest row, as (start, end) inclusive
    cuts = np.where(np.diff(on) > 1)[0]
    starts = np.concatenate(([on[0]], on[cuts + 1]))
    ends = np.concatenate((on[cuts], [on[-1]]))
    left = [(s, e) for s, e in zip(starts, ends) if e < cl]
    right = [(s, e) for s, e in zip(starts, ends) if s > cr]
    if not left or not right:
        return None
    spine = left[-1]
    wall = right[0]

    span = float(wall[1] - spine[0] + 1)
    return {"span/adv": span / adv_px,
            "counter w/span": counter_w / span,
            "counter w/stem": counter_w / stem if stem else 0.0,
            "spine/stem": (spine[1] - spine[0] + 1) / stem if stem else 0.0,
            "wall/stem": (wall[1] - wall[0] + 1) / stem if stem else 0.0,
            "counter h/xh": (cb - ct + 1) / float(W.XH),
            "reach/adv": float(on.max() - on.min() + 1) / adv_px}


def read(fc, ch, lower):
    if ord(ch) not in fc.cm:
        return None
    m = fc.mask(ch)
    if m is None:
        return None
    return read_mask(m, fc.f["hmtx"][fc.cm[ord(ch)]][0] * fc.k,
                     fc.stem[lower])


def sweep():
    from panel import families
    out = {}
    for _name, path in families():
        try:
            fc = Face(path)
        except Exception:
            continue
        try:
            se = P.stem_of(fc.f, fc.cm, fc.gs)
            if not se:
                continue
            se /= float(fc.upem)
            got = {}
            for ch, lower in GLYPHS:
                v = read(fc, ch, lower)
                if v:
                    got[ch] = v
                    for k in KEYS:
                        out.setdefault((ch, k), []).append((se, v[k]))
            for a, b in PAIRS:
                if a in got and b in got:
                    for k in PAIR_KEYS:
                        if got[b][k]:
                            out.setdefault((a + "/" + b, k), []).append(
                                (se, got[a][k] / got[b][k]))
        except Exception:
            pass
        finally:
            fc.close()
    return out


def main():
    want_panel = "--panel" in sys.argv
    ref = sweep() if want_panel else {}
    if want_panel:
        print("panel faces answering: "
              + "  ".join("%s %d" % (ch, len(ref.get((ch, KEYS[0]), [])))
                          for ch, _ in GLYPHS))
        print()
    for name, path in OURS:
        fc = Face(path)
        se = (P.stem_of(fc.f, fc.cm, fc.gs) or 0) / float(fc.upem)
        print(name)
        for ch, lower in GLYPHS:
            v = read(fc, ch, lower)
            if not v:
                continue
            tag = "   " if ch in LIVE else " . "
            cells = []
            for k in KEYS:
                pts = ref.get((ch, k), [])
                c = P.compare(pts, se, v[k]) if len(pts) > 5 else None
                if c:
                    cells.append("%s %.3f%s" % (k, v[k],
                                                "" if c[3] else "!"))
                else:
                    cells.append("%s %.3f" % (k, v[k]))
            print("  %s%s  %s" % (tag, ch, "  ".join(cells)))
            if want_panel:
                out = []
                for k in KEYS:
                    pts = ref.get((ch, k), [])
                    c = P.compare(pts, se, v[k]) if len(pts) > 5 else None
                    if c and not c[3]:
                        out.append("%s %.3f vs %.3f..%.3f"
                                   % (k, v[k], c[1], c[2]))
                if out:
                    print("        outside: " + "; ".join(out))
        if want_panel:
            print("    -- each letter over the face's OWN В, per face --")
            mine = {ch: read(fc, ch, lo) for ch, lo in GLYPHS}
            for a, b in PAIRS:
                if not mine.get(a) or not mine.get(b):
                    continue
                cells = []
                for k in PAIR_KEYS:
                    if not mine[b][k]:
                        continue
                    r = mine[a][k] / mine[b][k]
                    pts = ref.get((a + "/" + b, k), [])
                    c = P.compare(pts, se, r) if len(pts) > 5 else None
                    if c:
                        cells.append("%s %.3f vs %.3f (%.3f..%.3f)%s"
                                     % (k, r, c[0], c[1], c[2],
                                        "" if c[3] else " !"))
                    else:
                        cells.append("%s %.3f" % (k, r))
                print("      %s/%s  %s" % (a, b, "   ".join(cells)))
        fc.close()


if __name__ == "__main__":
    main()
