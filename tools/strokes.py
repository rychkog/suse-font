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

import statistics
import sys

from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from panel import families              # noqa: E402
from audit import contours, runs        # noqa: E402

CAPS = "БВГҐДЕЄЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
LOWS = "бвгґдеєжзийклмнопрстуфхцчшщъыьэюя"


def stem_of(gs, name, top):
    """The face's own stem, from its plain two-stem letter."""
    xs = runs(contours(gs, name), top * 0.25)
    return (xs[1] - xs[0]) if len(xs) >= 2 else None


def weight(gs, gname, stem):
    """The LIGHTEST stroke in the glyph, over the face's own stem.

    Not the median, and the difference decides whether this check works. The
    fault it exists for is always ONE stroke carrying a reduction nothing
    justifies, and a glyph's other strokes are full weight, so a median moves
    only half as far as the fault does. Tested against the five glyphs that
    actually had it, a median caught two: Я's bowl at 0.82 of В's read 1.003
    against a panel floor of 0.994 and sailed through. The lightest run reads
    the bowl itself.

    Runs under a third of the stem are dropped -- those are the sliver where a
    scanline grazes a corner or a diagonal's tip, not a stroke anyone drew.

    KNOWN LIMIT, and it is why this tool reports rather than gates. The run is
    measured horizontally, so a stroke that curves reads light wherever the
    scanline crosses it obliquely. в's stem measures exactly 150.0 at every
    height while its bowl wall reads 150 where it is vertical and 136 as the
    arc turns towards the waist, which drops the letter to 0.886 and under the
    panel's p10 with nothing wrong with it. Correcting that needs the run
    measured perpendicular to its own stroke, the way latin_metrics._lean_width
    does for y's tail. Until then, a flag on a letter with curved strokes is a
    prompt to go and look, not a verdict.
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
        xs = runs(polys, bot + (top - bot) * i / 100.0 + 0.13)
        got += [b - a for a, b in zip(xs[0::2], xs[1::2]) if b > a]
    got = [g for g in got if g > stem / 3.0]
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
            outside = v < p10 or v > vals[-1]
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


main()
