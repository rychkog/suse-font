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

**The band is found, not set.** A first version hand-set one per letter and got
the soft-bowl family wrong: `soft_bowl`'s top is not a fixed height, it rises
with the stroke, from 0.51 of the cap at Thin to 0.67 at ExtraBold. A band of
0.02-0.48 therefore read the lower two thirds of those bowls and missed exactly
the part that curves in, reporting Ь at 0.14 when its bowl is very nearly
circular. A hand-set band is a constant measured in one condition and carried
to another -- F1, in the probe rather than in the drawing.

So each bowl locates itself: take the outer edge over the whole letter, and
keep the contiguous run of rows around its widest point where the edge is still
past the halfway mark between its own extremes. That is the bowl and nothing
else, at whatever height the master happens to put it. Only the two lobes of
в and В still need saying, because one letter holds two bowls and the rule
would find only the wider.

**Which side.** For most letters the bowl's outer is the right edge. For the
ones whose stem is on the right -- я Я d, and Э э C c, whose backs face left --
it is the left. Getting this wrong is not a small error: it measures the
opening instead of the back, and C's opening reads 0.00.

**And ы Ы have no outer edge at all.** Their bowl sits BETWEEN the spine and a
detached stem, so on every scanline the rightmost ink is that stem and the
reading comes back 1.00 -- a perfect rectangle, which is a true description of
a stem and says nothing about the bowl. Left as an artefact it would have
quietly exempted the one letter in the family with the narrowest bowl. The fix
is `drop`: discard that many runs from the end of each row before looking, so
the bowl's own wall becomes the last thing left.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from fontTools.ttLib import TTFont

import probe as P

# (label, glyph, band low, band high, read the LEFT edge, runs to drop
#  from the right before looking -- see `drop` in the docstring)
#
# Bands are fractions of the case's own height. They are hand-set and that is
# deliberate: a swept band has to decide where a bowl ends, and every rule for
# that either reads the stem or cuts the arc short in at least one of these
# letters. Written down instead, they can be argued with.
LOWER = (
    ("о", "о", 0.02, 0.98, False, 0),
    ("б", "б", 0.02, 0.98, False, 0),
    ("в upper", "в", 0.52, 0.98, False, 0),
    ("в lower", "в", 0.02, 0.48, False, 0),
    ("ь", "ь", 0.02, 0.98, False, 0),
    ("ъ", "ъ", 0.02, 0.98, False, 0),
    ("ы", "ы", 0.02, 0.98, False, 1),
    ("ю", "ю", 0.02, 0.98, False, 0),
    ("ф", "ф", 0.02, 0.98, False, 0),
    ("я", "я", 0.02, 0.98, True, 0),
    ("э", "э", 0.02, 0.98, False, 0),
    # the host's own, and the bar
    ("b", "b", 0.02, 0.98, False, 0),
    ("p", "p", 0.02, 0.98, False, 0),
    ("d", "d", 0.02, 0.98, True, 0),
    ("c", "c", 0.02, 0.98, True, 0),
    ("o", "o", 0.02, 0.98, False, 0),
)
UPPER = (
    ("О", "О", 0.02, 0.98, False, 0),
    ("Б", "Б", 0.02, 0.98, False, 0),
    ("В upper", "В", 0.52, 0.98, False, 0),
    ("В lower", "В", 0.02, 0.48, False, 0),
    ("Ь", "Ь", 0.02, 0.98, False, 0),
    ("Ъ", "Ъ", 0.02, 0.98, False, 0),
    ("Ы", "Ы", 0.02, 0.98, False, 1),
    ("Ю", "Ю", 0.02, 0.98, False, 0),
    ("Ф", "Ф", 0.02, 0.98, False, 0),
    ("Я", "Я", 0.02, 0.98, True, 0),
    ("Э", "Э", 0.02, 0.98, False, 0),
    ("B upper", "B", 0.52, 0.98, False, 0),
    ("B lower", "B", 0.02, 0.48, False, 0),
    ("D", "D", 0.02, 0.98, False, 0),
    ("P", "P", 0.02, 0.98, False, 0),
    ("C", "C", 0.02, 0.98, True, 0),
    ("O", "O", 0.02, 0.98, False, 0),
)

# The face's own answer, and what everything else is read against. Five
# letters, two cases, one number -- so a letter outside this is outside the
# host and not merely outside a median.
HOST_LC = ("o", "b", "p", "d", "c")
HOST_UC = ("O", "B upper", "B lower", "D", "P", "C")

STEPS = 300
TOL = 0.5


def flat(f, cm, gs, ch, top, y0, y1, left, drop=0):
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
        if drop:
            r = r[:-drop]
        if not r:
            return None
        edge.append(-r[0][0] if left else r[-1][1])
    m, lo = max(edge), min(edge)
    if m <= lo:
        return None
    # the bowl locates itself: the contiguous rows around the widest point
    # that are still past halfway between the edge's own extremes
    half = lo + 0.5 * (m - lo)
    i = edge.index(m)
    a = i
    while a > 0 and edge[a - 1] >= half:
        a -= 1
    b = i
    while b < len(edge) - 1 and edge[b + 1] >= half:
        b += 1
    band = edge[a:b + 1]
    tol = TOL * upem / 1000.0
    return sum(1 for v in band if m - v <= tol) / float(len(band))


def read(f):
    cm, gs = f.getBestCmap(), f.getGlyphSet()
    cap = getattr(f["OS/2"], "sCapHeight", 0)
    xh = getattr(f["OS/2"], "sxHeight", 0)
    if not cap or not xh:
        return None
    out = {}
    for rows, top in ((LOWER, xh), (UPPER, cap)):
        for lab, ch, a, b, left, drop in rows:
            v = flat(f, cm, gs, ch, top, a, b, left, drop)
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
            for lab, _ch, _a, _b, _l, _d in rows:
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
