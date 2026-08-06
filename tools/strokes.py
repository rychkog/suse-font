"""Every drawn glyph's STROKE WEIGHT against the same 60 monospace faces.

panel.py compares ink AREA, and area is a poor witness for the fault this
project keeps hitting: a stroke carrying a weight reduction nothing justifies.
A bowl 18 per cent light inside a letter a little wider than average comes out
at the median and passes. Я did exactly that -- 1.10 against a median of 1.11
on area, while its bowl measured 0.82 of В's.

So this measures the strokes themselves. For each glyph it takes the median
ink run across the letter and divides by that font's OWN stem, which makes the
reading a pure proportion: how heavy this glyph's strokes are relative to the
face they belong to. A face that is simply bolder does not move.

The gate is NOT panel.py's "outside what any face does". That rule suits ink
area, whose range is tight, and fails here: the median lightest stroke is
1.000 across the whole bowl family -- most faces draw every stroke in those
letters at full stem weight -- while one to three faces of a genuinely
different construction drag the minimum down to 0.39, 0.55, 0.67. A gate at
the minimum passes a stroke a fifth too light.

So the gate is the panel's tenth percentile: lighter than nine faces in ten.
Against the five glyphs that actually carried the fault it catches four -- Я,
Ь, Б and я -- and misses Ъ at 0.790 against a p10 of 0.785, which is honestly
ambiguous, since five panel faces do draw Ъ that light.

    python tools/strokes.py
"""

import math
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from panel import families              # noqa: E402
from audit import contours, runs        # noqa: E402

# Only what this project DREW. А В Е І О Р С Т Х and their lowercase are
# donors -- the Latin letter unchanged -- so a flag on one is a fault in this
# tool and never in the glyph, which is precisely how the round-letter
# misreading was found: at ExtraBold е measured 0.431 of the stem against a
# panel median of 0.908, and е is the Latin e.
#
# Э and є go too, for the reason audit.CLONES exists: Э reverses the face's own
# C and є reuses it, so their thinnest section is the face's own drawing and
# measuring it against the panel says nothing about this project.
CLONES = "ЭэЄє"

# Below p10 AND meaningfully below the median. Some letters have no spread at
# all in the panel -- Џ's p10 IS its median, 1.000, so a reading of 0.988 sits
# below the tenth percentile while being a rounding away from what every face
# does. Two conditions instead of one keeps that from reporting.
BELOW_MEDIAN = 0.97

# в is excluded, and the reason is the project's own rule that the host settles
# what the panel only frames. Its bowl wall thins to 0.793 of its stem towards
# the waist; SUSE Mono's own B thins to 0.795. в is doing exactly what this
# face's two-lobe letter does, while the panel's median в, at 0.940, mostly
# does not. Measured, not waved through -- see the wall profiles in the commit
# that added this tool.
EXEMPT = "вВ"


def drawn_set():
    import recipes
    from classify import TIERS
    out = []
    for cp, name, _, _ in TIERS:
        if name in recipes.RECIPES and chr(cp) not in CLONES:
            out.append(chr(cp))
    return ("".join(c for c in out if c.isupper()),
            "".join(c for c in out if c.islower()))


CAPS, LOWS = drawn_set()


def stem_of(gs, name, top):
    """The face's own stem, from its plain two-stem letter."""
    xs = runs(contours(gs, name), top * 0.25)
    return (xs[1] - xs[0]) if len(xs) >= 2 else None


def across(polys, y, d=6.0):
    """Every stroke's thickness at height y, measured across ITSELF.

    A run taken horizontally reports a leaning stroke 1/cos too wide, so the
    two scanlines either side give the stroke's own lean and the lean gives the
    correction. Runs are paired by position between the two lines; where their
    counts differ a stroke has appeared or vanished between them and the sample
    is dropped rather than guessed at.
    """
    def rr(v):
        xs = runs(polys, v)
        return list(zip(xs[0::2], xs[1::2]))

    a, b = rr(y - d), rr(y + d)
    if len(a) != len(b) or not a:
        return []
    out = []
    for (a0, a1), (b0, b1) in zip(a, b):
        w = ((a1 - a0) + (b1 - b0)) / 2.0
        slope = ((b0 + b1) - (a0 + a1)) / 2.0 / (2.0 * d)
        # Pairing runs by position is only safe while both scanlines cross the
        # same strokes. Past about 27 degrees of lean the pair is as likely to
        # be two different strokes, or one caught mid-merge, and the
        # correction then divides by a large factor and invents a hairline --
        # Ъ read 0.339 of its own stem that way, and the Latin o, a donor that
        # cannot be wrong, read 0.799. Steep samples are dropped, not guessed.
        if abs(slope) > 0.5:
            continue
        out.append(w / math.hypot(1.0, slope))
    return out


def weight(gs, gname, stem):
    """The LIGHTEST stroke in the glyph, over the face's own stem.

    Not the median, and the difference decides whether this check works. The
    fault it exists for is always ONE stroke carrying a reduction nothing
    justifies, and a glyph's other strokes are full weight, so a median moves
    only half as far as the fault does. Tested against the five glyphs that
    actually had it, a median caught two: Я's bowl at 0.82 of В's read 1.003
    against a panel floor of 0.994 and sailed through. The lightest run reads
    the bowl itself.

    Two kinds of run are not strokes and are dropped. Under a third of the stem
    is the sliver where a scanline grazes a corner or a diagonal's tip. Over
    twice the stem is merged ink -- at в's waist the scanline crosses the whole
    letter and reports a 367-unit "stroke".
    """
    polys = contours(gs, gname)
    if not polys:
        return None
    ys = [q[1] for po in polys for q in po]
    top, bot = max(ys), min(ys)
    got = []
    # The middle of the letter only. Sampled to the very top and bottom this
    # picks up the sliver where a scanline grazes the tangent of a round
    # letter -- э read 0.376 of the stem that way, measuring the top of its
    # own curve rather than any stroke.
    for i in range(25, 76, 2):
        got += across(polys, bot + (top - bot) * i / 100.0 + 0.13)
    got = [g for g in got if stem / 3.0 < g < 2.0 * stem]
    return min(got) / stem if got else None


def profile(path):
    try:
        f = TTFont(path, fontNumber=0)
        cm, gs = f.getBestCmap(), f.getGlyphSet()
        cap = getattr(f["OS/2"], "sCapHeight", 0)
        xh = getattr(f["OS/2"], "sxHeight", 0)
        if not cap or not xh or "H" not in gs or "n" not in gs:
            return None
        sc, sl = stem_of(gs, "H", cap), stem_of(gs, "n", xh)
        if not sc or not sl:
            return None
    except Exception:
        return None
    out = {}
    for chars, stem in ((CAPS, sc), (LOWS, sl)):
        for ch in chars:
            if ord(ch) in cm:
                try:
                    out[ch] = weight(gs, cm[ord(ch)], stem)
                except Exception:
                    pass
    return {k: v for k, v in out.items() if v}


def main():
    refs = [p for p in (profile(q) for _, q in families()) if p]
    mine = {w: profile(f"fonts/ttf/SUSEMono-{w}.ttf")
            for w in ("Thin", "Regular", "ExtraBold")}
    print(f"stroke weight over the face's own stem -- {len(refs)} faces\n")
    bad = 0
    for w, prof in mine.items():
        if not prof:
            continue
        rows = []
        for ch, v in sorted(prof.items()):
            vals = sorted(r[ch] for r in refs if ch in r)
            if len(vals) < 20:
                continue
            n = len(vals)
            med, p10 = vals[n // 2], vals[int(0.10 * (n - 1))]
            _ = med
            outside = ((v < p10 and v < med * BELOW_MEDIAN)
                       or v > vals[-1]) and ch not in EXEMPT
            rows.append((outside, abs(v / med - 1.0), ch, v, med,
                         p10, vals[-1]))
        rows.sort(reverse=True)
        flagged = [r for r in rows if r[0]]
        bad += len(flagged)
        print(f"  {w}: {len(rows)} glyphs measured, {len(flagged)} below the "
              f"panel's tenth percentile")
        for _, _, ch, v, med, lo, hi in flagged:
            print(f"      {ch}  mine {v:5.3f}   median {med:5.3f} "
                  f"(p10 {lo:5.3f}, max {hi:5.3f})")
        for _, d, ch, v, med, lo, hi in rows[:3]:
            if not any(r[2] == ch for r in flagged):
                print(f"      {ch}  mine {v:5.3f}   median {med:5.3f} "
                      f"(p10 {lo:5.3f}, max {hi:5.3f})   furthest inside")
    print(f"\n{bad} readings below the panel's tenth percentile")
    # non-zero so verify.sh gates on it, the way check.py already does
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
