"""How round is a bowl? The one thing no gate here measured.

    ./venv/bin/python tools/round.py            # ours, four weights
    ./venv/bin/python tools/round.py --panel    # and the panel, bucketed by stem

Every gate in `verify.sh` reads weight, area, position or the way a stroke
ends. None of them reads curvature, so в passed all seven while standing still
over half its own edge at ExtraBold, twice, on two different constructions. It
was caught by eye both times. This is that reading, so it stops depending on
someone looking.

**What it measures.** The share of a bowl's outer edge that stands STILL --
within half a unit of the letter's widest point -- over the bowl's own extent.
A rectangle reads 1.00, a circle reads 0.00, and this face's own o, b, B, D and
P all sit at 0.09-0.11, which is close enough across five letters and two cases
to be a bar rather than a median.

**Half a unit, not one per cent.** A tolerance proportional to the edge's own
travel inflates the reading, and by different amounts for different letters,
because near a vertical tangent an arc leaves its maximum very slowly. An early
version of this probe used one per cent and reported в matching the family it
was visibly outside.

**Each bowl gets its own band**, listed below, because a bowl occupies a
different part of every letter -- ь's is the lower half, в's is two lobes, я's
is the upper half and opens the other way. A single band across the x-height
reads the stem in half of them and reports 1.00.

**Which side.** For most letters the bowl's outer is the right edge. For the
ones whose stem is on the right -- я Я d, and Э э C c, whose backs face left --
it is the left. Getting this wrong is not a small error: it measures the
opening instead of the back, and C's opening reads 0.00.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from fontTools.ttLib import TTFont

import probe as P

# (label, glyph, band low, band high, read the LEFT edge)
#
# Bands are fractions of the case's own height. They are hand-set and that is
# deliberate: a swept band has to decide where a bowl ends, and every rule for
# that either reads the stem or cuts the arc short in at least one of these
# letters. Written down instead, they can be argued with.
LOWER = (
    ("о", "о", 0.02, 0.98, False),
    ("б", "б", 0.02, 0.66, False),
    ("в upper", "в", 0.52, 0.98, False),
    ("в lower", "в", 0.02, 0.48, False),
    ("ь", "ь", 0.02, 0.48, False),
    ("ъ", "ъ", 0.02, 0.48, False),
    ("ю", "ю", 0.02, 0.98, False),
    ("ф", "ф", 0.02, 0.98, False),
    ("я", "я", 0.45, 0.98, True),
    ("э", "э", 0.02, 0.98, False),
    # the host's own, and the bar
    ("b", "b", 0.02, 0.98, False),
    ("p", "p", 0.02, 0.98, False),
    ("d", "d", 0.02, 0.98, True),
    ("c", "c", 0.02, 0.98, True),
    ("o", "o", 0.02, 0.98, False),
)
UPPER = (
    ("О", "О", 0.02, 0.98, False),
    ("Б", "Б", 0.02, 0.60, False),
    ("В upper", "В", 0.52, 0.98, False),
    ("В lower", "В", 0.02, 0.48, False),
    ("Ь", "Ь", 0.02, 0.48, False),
    ("Ъ", "Ъ", 0.02, 0.48, False),
    ("Ю", "Ю", 0.02, 0.98, False),
    ("Ф", "Ф", 0.02, 0.98, False),
    ("Я", "Я", 0.45, 0.98, True),
    ("Э", "Э", 0.02, 0.98, False),
    ("B upper", "B", 0.52, 0.98, False),
    ("B lower", "B", 0.02, 0.48, False),
    ("D", "D", 0.02, 0.98, False),
    ("P", "P", 0.52, 0.98, False),
    ("C", "C", 0.02, 0.98, True),
    ("O", "O", 0.02, 0.98, False),
)

# The face's own answer, and what everything else is read against. Five
# letters, two cases, one number -- so a letter outside this is outside the
# host and not merely outside a median.
HOST_LC = ("o", "b", "p", "d", "c")
HOST_UC = ("O", "B upper", "B lower", "D", "P", "C")

STEPS = 300
TOL = 0.5


def flat(f, cm, gs, ch, top, y0, y1, left):
    """Share of the bowl's outer edge standing still, over its own band."""
    name = cm.get(ord(ch))
    if name is None:
        return None
    ps = P.contours(f, name, cm, gs)
    if not ps:
        return None
    upem = f["head"].unitsPerEm
    edge = []
    for k in range(STEPS):
        r = P.runs(ps, top * (y0 + (y1 - y0) * k / (STEPS - 1.0)))
        if not r:
            return None
        edge.append(-r[0][0] if left else r[-1][1])
    m = max(edge)
    tol = TOL * upem / 1000.0
    return sum(1 for v in edge if m - v <= tol) / float(len(edge))


def read(f):
    cm, gs = f.getBestCmap(), f.getGlyphSet()
    cap = getattr(f["OS/2"], "sCapHeight", 0)
    xh = getattr(f["OS/2"], "sxHeight", 0)
    if not cap or not xh:
        return None
    out = {}
    for rows, top in ((LOWER, xh), (UPPER, cap)):
        for lab, ch, a, b, left in rows:
            v = flat(f, cm, gs, ch, top, a, b, left)
            if v is not None:
                out[lab] = v
    return out


OURS = [("Thin", "fonts/ttf/SUSEMono-Thin.ttf"),
        ("Regular", "fonts/ttf/SUSEMono-Regular.ttf"),
        ("Bold", "fonts/ttf/SUSEMono-Bold.ttf"),
        ("ExtraBold", "fonts/ttf/SUSEMono-ExtraBold.ttf")]


def main():
    want = "--panel" in sys.argv
    ref = {}
    if want:
        from panel import families
        for _fam, path in families():
            f = TTFont(path, fontNumber=0, lazy=True)
            try:
                s = P.stem_of(f)
                r = read(f)
                if s and r:
                    for k, v in r.items():
                        ref.setdefault(k, []).append(
                            (s / f["head"].unitsPerEm, v))
            except Exception:
                pass
            finally:
                f.close()
        print("panel faces answering: %d\n"
              % max((len(v) for v in ref.values()), default=0))

    print("share of each bowl's outer edge standing still, over its own band")
    print("  1.00 is a rectangle, 0.00 a circle\n")
    for name, path in OURS:
        f = TTFont(path, lazy=True)
        se = (P.stem_of(f) or 0) / float(f["head"].unitsPerEm)
        r = read(f) or {}
        f.close()
        print(name)
        for rows, host in ((LOWER, HOST_LC), (UPPER, HOST_UC)):
            hv = [r[k] for k in host if k in r]
            if not hv:
                continue
            bar = max(hv)
            cells = []
            for lab, _ch, _a, _b, _l in rows:
                if lab not in r:
                    continue
                mark = ""
                if lab not in host and r[lab] > bar * 1.35:
                    mark = "!"
                if want:
                    c = P.compare(ref.get(lab, []), se, r[lab])
                    if c and not c[3]:
                        mark += "P"
                cells.append("%s %.2f%s" % (lab, r[lab], mark))
            print("   the host holds %.2f  --  " % bar + "  ".join(cells))
    print("\n  ! = more than a third above the host's own worst"
          "      P = outside the panel")


if __name__ == "__main__":
    main()
