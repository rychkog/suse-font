"""What does a Ж weigh, and what does this face do with a diagonal?

Three questions, one pass over each face:

  * Ж and ж -- the centre stem against an arm, and the arm against the face's
    own stem for that case. ZHE_STEM is a flat 0.86 read off ONE face.
  * the face's own diagonals -- X V W K Y measured PERPENDICULAR to the
    stroke, against H. Ж's arms take m's three-upright crowding reduction, and
    whether a diagonal letter in this face is reduced at all is a question the
    face can answer for itself.
  * М and м -- both uprights and both diagonals, each over its own case's
    stem, and the ratio the pair of them takes across the case. м is built as
    М at x-height, so every one of those four figures is inherited, and the
    question this answers is whether a face reduces its lowercase diagonal
    BEYOND whatever its capital already does. The upright half of the same
    reading is the check on the probe: м's approval records the panel's
    upright ratio as 1.000 with the middle half inside 0.979-1.035, read a
    different way, so this one has to land there too.

A diagonal's horizontal run is wider than the stroke by 1/cos of its lean, so
every thickness here is divided by that -- the slope comes from tracking the
same edge at two heights. Comparing horizontal runs would make every diagonal
look heavy and is the whole reason "Ф against H" once reported a 28% error.

The lowercase divides by n's stem, never H's: this face draws n at 0.93 of H,
so a lowercase relation taken against the capital stem reads six per cent low
in every face at once.

This file exists because ZHE_STEM did not. The constant was read off one face
by hand, written down as 0.86, and then could not be re-checked by anyone --
so it survived until a gate that measures something else entirely noticed Ж
was the furthest thing here from the panel's median. An approval's readings
have to be reproducible or the next round is starting from prose.

Not a gate. Run it when a diagonal's weight is in question:

    ./venv/bin/python tools/diagonals.py
"""
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from fontTools.ttLib import TTFont

import probe as P


def slope_and_width(ps, y1, y2, idx):
    """(perpendicular thickness, dx/dy) of run `idx` between two cuts."""
    r1, r2 = P.runs(ps, y1), P.runs(ps, y2)
    if len(r1) <= idx or len(r2) <= idx or len(r1) != len(r2):
        return None
    a1, b1 = r1[idx]
    a2, b2 = r2[idx]
    s = ((a2 + b2) / 2.0 - (a1 + b1) / 2.0) / (y2 - y1)
    return (b1 - a1) / (1.0 + s * s) ** 0.5, s


def zhe(ps, ref):
    """Ж's centre stem and one arm, perpendicular, as a median over the band.

    The median over every clean cut, not the first one found. The arm's
    measured thickness drifts with the height it is read at -- it is cut flat
    against the cap line at the top and runs into the stem at the bottom, so
    the two-cut slope is not the same estimate at both ends. Reading our own
    Regular at the lowest clean cut gave 0.983 and at the highest 1.035 for a
    ratio the source holds at exactly 1.033 at both masters, which is a value
    interpolation cannot change. First-clean-cut was therefore reporting where
    the sweep happened to start.
    """
    if not ps:
        return None
    mids, arms = [], []
    for k in range(60, 90, 4):
        y1, y2 = ref * k / 100.0, ref * (k + 6) / 100.0
        if len(P.runs(ps, y1)) != 3 or len(P.runs(ps, y2)) != 3:
            continue
        arm = slope_and_width(ps, y1, y2, 0)
        mid = slope_and_width(ps, y1, y2, 1)
        if arm and mid and abs(mid[1]) < 0.05 and arm[0] > 1 and mid[0] > 1:
            mids.append(mid[0])
            arms.append(arm[0])
    if not mids:
        return None
    mids.sort()
    arms.sort()
    return mids[len(mids) // 2], arms[len(arms) // 2]


def em_four(ps, ref):
    """(upright, diagonal) of an М-shaped letter, perpendicular, as medians.

    Four strokes: the outer pair stand up, the inner pair lean to the vertex.
    Both are read at every cut in the band where all four stand apart, and the
    median is taken, for the reason `zhe` takes one -- a two-cut estimate of a
    leaning stroke drifts with the height it is read at, so the first clean cut
    reports where the sweep started and not what the letter does. The band
    itself cannot be fixed either: for this face's own М all four are apart
    over 0.36..0.95 of the cap at Thin and only 0.53..0.89 at ExtraBold, so a
    single height reads merged ink at one master or the other.

    The shape is checked rather than assumed. A face whose м is not М's
    construction -- and some draw it with a rounded vertex or as a three-arch
    letter -- gives four runs that do not answer this description, so the outer
    pair must be within a twentieth of vertical and the inner pair must
    actually lean. Otherwise the reading is dropped, not guessed at.
    """
    if not ps:
        return None
    ups, dis = [], []
    for k in range(30, 90, 2):
        y1, y2 = ref * k / 100.0, ref * (k + 6) / 100.0
        if len(P.runs(ps, y1)) != 4 or len(P.runs(ps, y2)) != 4:
            continue
        v = [slope_and_width(ps, y1, y2, i) for i in range(4)]
        if any(x is None or x[0] <= 1 for x in v):
            continue
        if max(abs(v[0][1]), abs(v[3][1])) > 0.05:
            continue
        if min(abs(v[1][1]), abs(v[2][1])) < 0.15:
            continue
        ups.append((v[0][0] + v[3][0]) / 2.0)
        dis.append((v[1][0] + v[2][0]) / 2.0)
    if not ups:
        return None
    ups.sort()
    dis.sort()
    return ups[len(ups) // 2], dis[len(dis) // 2]


def diagonals(f, cm, gs, cap):
    """Each of X V W K Y's diagonal strokes, perpendicular, over H's stem."""
    out = {}
    for ch, idx in (("X", 0), ("V", 0), ("W", 0), ("K", 1), ("Y", 0)):
        ps = P.contours(f, ch, cm, gs)
        if not ps:
            continue
        for k in (72, 66, 78, 60):
            y1, y2 = cap * k / 100.0, cap * (k + 8) / 100.0
            r1 = P.runs(ps, y1)
            if len(r1) <= idx or len(r1) != len(P.runs(ps, y2)):
                continue
            v = slope_and_width(ps, y1, y2, idx)
            if v and v[0] > 1 and abs(v[1]) > 0.15:
                out[ch] = v[0]
                break
    return out


def read(f):
    cm, gs = f.getBestCmap(), f.getGlyphSet()
    stem = P.stem_of(f, cm, gs)
    cap = getattr(f["OS/2"], "sCapHeight", 0)
    if not stem or not cap:
        return None
    row = {"stem/em": stem / float(f["head"].unitsPerEm)}

    z = zhe(P.contours(f, "Ж", cm, gs), cap)
    if z:
        row["mid/arm"], row["arm/stem"] = z[0] / z[1], z[1] / stem

    lcs = P.lc_stem_of(f, cm, gs)
    xh = getattr(f["OS/2"], "sxHeight", 0)
    if lcs and xh:
        z = zhe(P.contours(f, "ж", cm, gs), xh)
        if z:
            row["lc mid/arm"], row["lc arm/stem"] = z[0] / z[1], z[1] / lcs

    cap4 = em_four(P.contours(f, "М", cm, gs), cap)
    lc4 = em_four(P.contours(f, "м", cm, gs), xh) if lcs and xh else None
    if cap4:
        row["М up/H"], row["М diag/H"] = cap4[0] / stem, cap4[1] / stem
    if lc4:
        row["м up/n"], row["м diag/n"] = lc4[0] / lcs, lc4[1] / lcs
    if cap4 and lc4:
        # The two figures the recipe inherits, as the shift each takes across
        # the case and nothing else. This is the form m's uprights were settled
        # in and the only form that can answer the question: an absolute
        # lowercase diagonal is lighter than its capital's in every face at
        # once, because the capital's is heavier to begin with.
        row["м/М up"] = (lc4[0] / lcs) / (cap4[0] / stem)
        row["м/М diag"] = (lc4[1] / lcs) / (cap4[1] / stem)

    for ch, v in diagonals(f, cm, gs, cap).items():
        row[ch] = v / stem
    return row


OURS = [("Thin", "fonts/ttf/SUSEMono-Thin.ttf"),
        ("Regular", "fonts/ttf/SUSEMono-Regular.ttf"),
        ("Bold", "fonts/ttf/SUSEMono-Bold.ttf"),
        ("ExtraBold", "fonts/ttf/SUSEMono-ExtraBold.ttf")]
KEYS = ["mid/arm", "arm/stem", "lc mid/arm", "lc arm/stem",
        "М up/H", "М diag/H", "м up/n", "м diag/n", "м/М up", "м/М diag",
        "X", "V", "W", "K", "Y"]


def main():
    from panel import families
    ref = {}
    for _fam, path in families():
        f = TTFont(path, fontNumber=0, lazy=True)
        try:
            r = read(f)
            if r:
                for k in KEYS:
                    if k in r:
                        ref.setdefault(k, []).append((r["stem/em"], r[k]))
        except Exception:
            pass
        finally:
            f.close()

    print("panel faces answering: "
          + "  ".join(f"{k} {len(ref.get(k, []))}" for k in KEYS))
    print()
    for name, path in OURS:
        f = TTFont(path, lazy=True)
        r = read(f) or {}
        f.close()
        print(name)
        for k in KEYS:
            if k not in r:
                continue
            pts = ref.get(k, [])
            c = P.compare(pts, r["stem/em"], r[k]) if len(pts) > 5 else None
            if c:
                print("   %-12s mine %6.3f   panel %6.3f  (%.3f..%.3f)%s"
                      % (k, r[k], c[0], c[1], c[2],
                         "" if c[3] else "   OUTSIDE"))
            else:
                print("   %-12s mine %6.3f" % (k, r[k]))


if __name__ == "__main__":
    main()
