"""Compare every drawn glyph against the programming faces on this machine.

    python tools/panel.py            # outliers only
    python tools/panel.py --all      # every letter

The point is NOT to copy any of them. It is that a proportion four or five
independent designers agree on is a fact about the letter, and one they
disagree on is a matter of taste this face gets to settle for itself. Only the
first kind is worth importing; the second must come from SUSE Mono's own Latin.

Everything is measured as ink area normalised by the font's OWN Latin-capital
mean, so a face that is simply bolder does not read as an outlier. What the
comparison catches is a letter that is heavy or light RELATIVE TO ITS OWN
ALPHABET -- which is the only sense in which a Cyrillic glyph can be wrong
about weight while still belonging to its family.
"""

import glob
import os
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen

LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DRAWN = "БГҐДЄЖЗИЛПУФЦЧШЩЪЫЬЭЮЯ"

# The lowercase normaliser is the Latin letters that live inside the x-height
# and nothing else. Twenty-five of the thirty-one Cyrillic lowercase sit in
# that band too, so a mean that included b d f h k l and g j p q y would carry
# each face's ascender proportion into every reading. The six that do reach
# out of the band -- б ґ д ф ц щ -- keep that noise, and their numbers here
# are the softer ones.
LATIN_LC = "acemnorsuvwxz"
DRAWN_LC = "бвгґдєжзиклмнптфцчшщъыьэюя"

SETS = (("capitals", DRAWN, LATIN),
        ("lowercase", DRAWN_LC, LATIN_LC))

NEEDED = [ord(c) for c in "БГДЖЗИЛПФЦШЫЯбгджзилпфцшыя"]

# Skipped, with reasons. Nerd Font and NL builds are the same outlines as the
# family they patch, so counting them would weight that design several times
# over in the median.
SKIP = ("Nerd Font", " NF", "NL", "Term", "Mono Term", "_0")


import os


def font_dirs():
    """Where to look for the comparison faces.

    Override with SUSE_FONT_DIRS (colon separated). The default globs the
    per-user font directory rather than naming an account, so it works on any
    machine and keeps no one's username in a public repo.
    """
    env = os.environ.get("SUSE_FONT_DIRS")
    if env:
        return [d for d in env.split(":") if d]
    import glob as _glob
    out = ["/mnt/c/Windows/Fonts"]
    out += sorted(_glob.glob(
        "/mnt/c/Users/*/AppData/Local/Microsoft/Windows/Fonts"))
    out += [os.path.expanduser("~/.local/share/fonts"),
            "/usr/share/fonts"]
    return [d for d in out if os.path.isdir(d)]


def italics(need=NEEDED):
    """One italic per family, auto-discovered -- the same panel, sloped.

    `families()` throws italics away, which is right for every reading that
    exists to compare an upright letter with an upright letter. The italic asks
    a different question and needs its own list: Cyrillic italic has a set of
    lowercase forms that are not the upright sloped -- и is a u, п an n, т an m
    -- and whether a monospace adopts them is a decision only its italic can
    answer.

    One file per family, the lightest that carries what is asked for, because
    the form question does not change with weight and opening five weights of
    Monaspace would make it Monaspace's answer.
    """
    found = {}
    for d in font_dirs():
        for p in sorted(glob.glob(d + "/*.ttf") + glob.glob(d + "/*.otf")):
            try:
                f = TTFont(p, fontNumber=0, lazy=True)
                try:
                    cm = f.getBestCmap()
                    if not all(c in cm for c in need):
                        continue
                    sub = f["name"].getDebugName(2) or ""
                    fam = f["name"].getDebugName(1) or os.path.basename(p)
                    if "Italic" not in sub and "Oblique" not in sub:
                        continue
                    if any(s in fam for s in SKIP):
                        continue
                    hm = f["hmtx"]
                    if len({hm[cm[c]][0] for c in need}) != 1:
                        continue
                    cap = getattr(f["OS/2"], "sCapHeight", 0) or \
                        0.7 * f["head"].unitsPerEm
                    gs = f.getGlyphSet()
                    pen = AreaPen(gs)
                    gs[cm[ord("H")]].draw(pen)
                    w = abs(pen.value) / (cap * hm[cm[ord("H")]][0])
                    key = fam
                    for suf in (" Extra", " Semi", " Heavy", " Light",
                                " Medium", " Wide", " Thin", " Black",
                                " Bold", " Retina", " Condensed"):
                        key = key.split(suf)[0]
                    found.setdefault(key.strip(), []).append((w, p))
                finally:
                    f.close()
            except Exception:
                continue
    return [(fam, sorted(lst)[0][1]) for fam, lst in sorted(found.items())]


def families():
    """One lightest and one heaviest upright per family, auto-discovered."""
    found = {}
    for d in font_dirs():
        for p in sorted(glob.glob(d + "/*.ttf") + glob.glob(d + "/*.otf")):
            try:
                f = TTFont(p, fontNumber=0, lazy=True)
                cm = f.getBestCmap()
                if not all(c in cm for c in NEEDED):
                    continue
                sub = f["name"].getDebugName(2) or ""
                fam = f["name"].getDebugName(1) or os.path.basename(p)
                if "Italic" in sub or "Oblique" in sub:
                    continue
                if any(s in fam for s in SKIP):
                    continue
                hm = f["hmtx"]
                if len({hm[cm[c]][0] for c in NEEDED}) != 1:
                    continue        # not monospaced
                cap = getattr(f["OS/2"], "sCapHeight", 0) or \
                    0.7 * f["head"].unitsPerEm
                # weight, measured rather than trusted: I's own stroke
                gs = f.getGlyphSet()
                pen = AreaPen(gs)
                gs[cm[ord("H")]].draw(pen)
                w = abs(pen.value) / (cap * hm[cm[ord("H")]][0])
                # One entry per DESIGN, not per shipped file. Monaspace alone
                # ships five variants in three widths; counted separately they
                # would be fifteen of the panel's votes and the median would
                # be Monaspace's opinion wearing a crowd's clothes.
                key = fam
                for suf in (" Extra", " Semi", " Heavy", " Light", " Medium",
                            " Wide", " Thin", " Black", " Bold", " Retina",
                            " Condensed"):
                    key = key.split(suf)[0]
                found.setdefault(key.strip(), []).append((w, p))
            except Exception:
                continue
    out = []
    for fam, lst in sorted(found.items()):
        lst.sort()
        out.append((fam, lst[0][1]))
        if len(lst) > 1:
            out.append((fam + " (heaviest)", lst[-1][1]))
    return out


def profile(path):
    """Each drawn Cyrillic letter's ink, as a multiple of the font's own mean
    for the Latin of the SAME case.

    The cap height and advance in the divisor cancel out of every ratio, so
    the reading is pure proportion and a face that is simply bolder or wider
    does not read as an outlier.
    """
    try:
        f = TTFont(path, fontNumber=0)
    except Exception:
        return None
    cm = f.getBestCmap()
    gs = f.getGlyphSet()
    cap = getattr(f["OS/2"], "sCapHeight", 0) or 0.7 * f["head"].unitsPerEm

    def ink(ch):
        if ord(ch) not in cm:
            return None
        g = cm[ord(ch)]
        pen = AreaPen(gs)
        gs[g].draw(pen)
        return abs(pen.value) / (cap * f["hmtx"][g][0])

    out = {}
    for label, drawn, latin in SETS:
        lat = [v for v in (ink(c) for c in latin) if v]
        if not lat:
            return None
        mean = sum(lat) / len(lat)
        out[label] = {c: (ink(c) / mean if ink(c) else None) for c in drawn}
    return out


def main():
    show_all = "--all" in sys.argv
    refs = []
    for fam, p in families():
        pr = profile(p)
        if pr:
            refs.append((fam, pr))
    print(f"reference panel: {len(refs)} faces")
    for fam, _ in refs:
        print(f"    {fam}")

    worst = 0.0
    for label, drawn, _ in SETS:
        for w in ("Regular", "ExtraBold"):
            mine = profile(f"fonts/ttf/SUSEMono-{w}.ttf")
            if not mine:
                continue
            mine, todo = mine[label], []
            print(f"\n{label} {w}: ink vs the panel's median, per letter")
            rows = []
            for c in drawn:
                vals = sorted(v for _, pr in refs if pr[label].get(c)
                              for v in [pr[label][c]])
                if not vals:
                    continue
                med = vals[len(vals) // 2]
                if not mine.get(c):
                    # not drawn yet: the panel still answers what to aim for
                    todo.append((c, med, vals[0], vals[-1]))
                    continue
                rows.append((mine[c] / med, c, mine[c], med, vals[0], vals[-1]))
            for d, c, mv, med, lo, hi in sorted(rows, reverse=True):
                worst = max(worst, abs(d - 1.0))
                # Outside what ANY of sixty designs does is a real signal.
                # Merely below the median is not -- half of them are.
                outside = mv > hi or mv < lo
                if not show_all and not outside:
                    continue
                tag = "  OUTSIDE PANEL" if outside else ""
                print(f"    {c}  mine {mv:5.2f}   panel median {med:5.2f} "
                      f"(range {lo:4.2f}-{hi:4.2f})   {d:5.2f}x{tag}")
            if rows and not show_all:
                if all(r[4] <= r[2] <= r[5] for r in rows):
                    print("    (every letter inside the panel's range)")
            # the panel's own figures do not depend on which of my weights is
            # being compared, so the targets are worth printing once
            if todo and w == "Regular":
                print(f"    not drawn yet -- what {len(refs)} faces aim at:")
                for c, med, lo, hi in todo:
                    print(f"      {c}  target {med:5.2f} "
                          f"(range {lo:4.2f}-{hi:4.2f})")
    print(f"\nworst deviation across the set: {worst * 100:.0f}%")


if __name__ == "__main__":
    main()
