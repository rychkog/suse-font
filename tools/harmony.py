"""Do the bowl letters agree with each other?

Every letter here hangs a bowl off a stem, and three things have to agree
across the whole family or the row comes apart: where the bowl REACHES, how
heavy its WALL is, and how much WHITE is left inside it. All three are read
at one place -- the height where the bowl is at its widest.

Each reading is then asked twice. Once against the rest of OUR family, which
says whether the letter sits in the row, and once against the panel's own
letter, which says whether the row is in the right place. A letter can be an
outlier in the family and still be right, because that is what the letter is;
and every letter can sit comfortably in a family that is wrong. Only the two
answers together say which:

    -  or  +     outside +/-6% of our own family's median
    !            outside the panel's bracket at this weight

Read on the bowl's own side: right for most, LEFT for С, Я, я, d, whose bowl
closes on the left. An open letter is read on the side it is closed on -- a
scanline through C's middle gives one run, not two.

Nothing here comes from a bounding box. A bbox answers for the letter, not
for the bowl, and Ъ's answer would be its shoulder.
"""

import statistics as st
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import probe as P  # noqa: E402

# +1 closed on the right, -1 closed on the left.
CAPS = [("О", 1), ("В", 1), ("Б", 1), ("Ь", 1), ("Ъ", 1), ("Р", 1),
        ("Ю", 1), ("Ф", 1), ("Э", 1), ("С", -1), ("Я", -1),
        ("B", 1), ("P", 1), ("D", 1), ("O", 1), ("C", -1)]
LC = [("о", 1), ("в", 1), ("ь", 1), ("ъ", 1), ("ю", 1), ("ф", 1),
      ("э", 1), ("с", -1), ("я", -1),
      ("b", 1), ("p", 1), ("o", 1), ("d", -1), ("q", 1), ("c", -1)]

OURS = [("Thin", "fonts/ttf/SUSEMono-Thin.ttf"),
        ("Regular", "fonts/ttf/SUSEMono-Regular.ttf"),
        ("Bold", "fonts/ttf/SUSEMono-Bold.ttf"),
        ("ExtraBold", "fonts/ttf/SUSEMono-ExtraBold.ttf")]

KEYS = ["reach/adv", "wall/stem", "white/stem"]

# Coarse pass then a fine one around the winner. A flat sweep fine enough to
# be accurate is fine everywhere, and every scanline walks the whole outline:
# at 240 steps over 60 faces and 31 letters this file took minutes.
COARSE, FINE = 48, 12


def _widest(ps, lo, hi, side):
    """The cut where the bowl reaches furthest, and the runs across it."""
    def scan(a, b, n):
        best = None
        for k in range(n + 1):
            y = a + (b - a) * k / float(n)
            r = P.runs(ps, y)
            if len(r) < 2:
                continue
            edge = r[-1][1] if side > 0 else r[0][0]
            if best is None or (edge > best[0] if side > 0 else edge < best[0]):
                best = (edge, r, y)
        return best

    span = (hi - lo) / float(COARSE)
    best = scan(lo + span, hi - span, COARSE)
    if best is None:
        return None
    return scan(max(lo, best[2] - span), min(hi, best[2] + span), FINE) or best


def read(f, ch, side, ref, cm=None, gs=None, stem=None):
    """One letter's three readings, or None if this face does not draw it."""
    cm = cm if cm is not None else f.getBestCmap()
    gs = gs if gs is not None else f.getGlyphSet()
    if stem is None:
        stem = (P.lc_stem_of(f, cm, gs) if ref == "lc"
                else P.stem_of(f, cm, gs))
    if not stem:
        return None
    ps = P.contours(f, ch, cm, gs)
    if not ps:
        return None
    ys = [q[1] for p in ps for q in p]
    best = _widest(ps, min(ys), max(ys), side)
    if best is None:
        return None
    edge, r, _y = best
    if side > 0:
        wall, white = r[-1][1] - r[-1][0], r[-1][0] - r[-2][1]
    else:
        wall, white = r[0][1] - r[0][0], r[1][0] - r[0][1]
    adv = f["hmtx"][cm[ord(ch)]][0]
    return {"stem/em": stem / float(f["head"].unitsPerEm),
            "reach/adv": (edge if side > 0 else adv - edge) / adv,
            "wall/stem": wall / stem,
            "white/stem": white / stem}


def read_all(f):
    """Every letter in one pass over one open font.

    The font, its cmap, its glyph set and its two stems are built once. Read
    per letter instead -- opening the face again for each -- and the panel
    sweep costs thirty-one times what it needs to.
    """
    cm, gs = f.getBestCmap(), f.getGlyphSet()
    stems = {"cap": P.stem_of(f, cm, gs), "lc": P.lc_stem_of(f, cm, gs)}
    out = {}
    for table, ref in ((CAPS, "cap"), (LC, "lc")):
        for ch, side in table:
            v = read(f, ch, side, ref, cm, gs, stems[ref])
            if v:
                out[ch] = v
    return out


def panel():
    """Every panel face, opened once each."""
    from panel import families
    out = {}
    for _name, path in families():
        f = TTFont(path, fontNumber=0, lazy=True)
        try:
            for ch, v in read_all(f).items():
                out.setdefault(ch, []).append(v)
        except Exception:
            pass
        finally:
            f.close()
    return out


def report():
    ref = panel()
    for name, path in OURS:
        f = TTFont(path, lazy=True)
        mine = read_all(f)
        f.close()
        print("=" * 72)
        print(name)
        for label, table in (("capitals", CAPS), ("lowercase", LC)):
            rows = [(ch, mine[ch]) for ch, _s in table if ch in mine]
            if not rows:
                continue
            med = {k: st.median([v[k] for _c, v in rows]) for k in KEYS}
            print("  %-10s %13s %16s %16s"
                  % (label, "reach/adv", "wall/stem", "white/stem"))
            for ch, v in rows:
                line = "    %s  " % ch
                for k in KEYS:
                    d = v[k] / med[k] if med[k] else 0.0
                    fam = "" if 0.94 <= d <= 1.06 else ("-" if d < 1 else "+")
                    pts = [(p["stem/em"], p[k]) for p in ref.get(ch, [])]
                    c = (P.compare(pts, v["stem/em"], v[k])
                         if len(pts) > 5 else None)
                    line += "%10.3f%1s%2s" % (v[k], fam,
                                              "" if c is None else
                                              ("" if c[3] else "!"))
                print(line)
            print("    med %9.3f %13.3f %15.3f"
                  % (med["reach/adv"], med["wall/stem"], med["white/stem"]))


if __name__ == "__main__":
    report()
