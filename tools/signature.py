"""Does a drawn glyph carry the face's signature, or only its metrics?

Every gate in `verify.sh` asks whether a glyph is *correct*. None of them asks
the question a reader asks, which is whether it *belongs* -- and the two come
apart. A letter can hold the advance, the stem, the counter and the overshoot,
pass every check, and still read as having been added later.

`docs/METHOD.md` says the signature is concrete and readable off the Latin.
This file is that claim taken literally: measure the Latin, let its answer BE
the reference, then read the drawn glyphs against it. Two of the enumerated
items turn out to survive being measured this way.

**How a stroke ends.** The face cuts terminals square and flat. Measured over
its own alphabet and digits at both masters, 213 of its 242 terminals are cut
at exactly 0 or 90 degrees, no chamfer anywhere exceeds 45 degrees, and every
exception is a diagonal's end -- the letters that have no square way to stop.
So an oblique cut is not forbidden, it is *earned by a diagonal*, and a glyph
that cuts obliquely without one is doing something the face does not do.

**How heavy a horizontal is.** This is the tell `params.py` calls the most
common way a bolted-on Cyrillic gives itself away: the lowercase horizontal is
NOT the capital's. At ExtraBold the face draws 106 here against the capitals'
135, so a lowercase squashed down from its capital carries a bar a fifth too
heavy, and no amount of holding the height through the squash prevents it.

Both are read at both masters, because the face's answers move between them
and a census at one end misses half of what it does.

A third reading was tried and is deliberately absent. "A lowercase turn is
never tighter than its capital's" is the most characteristic item on the list,
and asking it of every case pair rather than the six in `audit.py` looked like
free coverage. It is not: `corner_set` cannot tell a corner from a bowl, and a
bowl is genuinely a different size in the two cases -- O sweeps 361 where o
sweeps 140 and 261 -- so the check reported ten of the face's own pairs.
Separating the two needs a cutoff between "corner" and "bowl" that the face
does not state anywhere, and a threshold that has to be picked is the thing
this project has been burned by most. The six pairs in `audit.py` are the six
whose letters are made of corners, which is why they are the six.

Not a gate. It reports, the way `harmony.py` does -- a finding here is a
candidate for the user's eye, and several of the letters it names are frozen.
Run `--selftest` first: it puts the Latin through the identical readings, and
anything it flags is this file being wrong rather than the face.
"""

import math
import sys
from collections import Counter

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import glyphsLib  # noqa: E402
import probe as P  # noqa: E402
import recipes  # noqa: E402
from audit import CAPS, LOWER  # noqa: E402
from classify import TIERS  # noqa: E402
from params import Params  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402

WEIGHTS = ("Thin", "Regular", "Bold", "ExtraBold")

# The digits are part of the capitals' reference and not an afterthought. They
# stand on the cap line, they are drawn with the capitals' stroke, and this
# project takes glyphs straight off them -- З IS the figure three, unchanged.
# Left out, the reference says the face never cuts at 128 degrees and the
# probe reports the face's own three as a foreign terminal.
DIGITS = ("zero", "one", "two", "three", "four",
          "five", "six", "seven", "eight", "nine")

# How far off square a cut may be read and still count as square. The face
# draws its flat terminals at exactly 0 and 90; this only absorbs the outline
# arithmetic, and at 2 degrees a 29-unit terminal has moved by a single unit.
SQUARE_TOL = 2.0

# What counts as a terminal: a straight segment about as long as the stroke is
# wide, with the outline turning away from it at both ends. Below 0.55 of the
# stroke it is a chamfer or the flat of a corner rather than an end, and above
# 1.9 it is a side. The turn has to be a real one -- 69 degrees, not 90 --
# because a terminal on a diagonal meets its own arm obliquely by construction.
CUT_LO, CUT_HI, CUT_SQUARE = 0.55, 1.9, 0.36

# ...and a cut is SHORTER than what it cuts across. This is what separates an
# end from a side, and the length window alone does not: at ExtraBold the
# stroke is 161 units wide, so Ж's upper arms -- 295 units of straight side --
# land inside the window and were reported as two oblique terminals in a
# letter whose every real terminal is cut flat. A terminal's neighbours are
# the stroke's two long sides; a side's neighbours are its own two terminals.
CUT_ARM = 0.9

# A horizontal stroke is an ink run up a vertical line that is short compared
# with the letter. Three tenths of the height clears the face's heaviest bar
# -- 135 against a 700 cap -- with room to spare, and stays under the shortest
# thing that is NOT a horizontal: B's lobe stands 272 units tall at ExtraBold
# and a looser limit reads it as a bar four times too heavy, in the Latin.
BAR_MAX = 0.30


def onpts(path):
    """On-curve points in order, flagged for whether they arrive by a line.

    A cut is straight by definition, so a point reached by a curve cannot end
    one, and asking the control points would put the terminal where the ink is
    not.
    """
    out, pend = [], 0
    for n in path.nodes:
        if n.type == "offcurve":
            pend += 1
            continue
        out.append((n.position.x, n.position.y, pend == 0))
        pend = 0
    if out:
        out[0] = (out[0][0], out[0][1], pend == 0)
    return out


def cuts(paths, stem):
    """Every stroke end in the glyph, as the angle it is cut at."""
    out = []
    for p in paths:
        pts = onpts(p)
        n = len(pts)
        if n < 4:
            continue
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            if not b[2]:
                continue
            seg = (b[0] - a[0], b[1] - a[1])
            ln = math.hypot(*seg)
            if not (CUT_LO * stem <= ln <= CUT_HI * stem):
                continue
            arms = ((a[0] - pts[i - 1][0], a[1] - pts[i - 1][1]),
                    (pts[(i + 2) % n][0] - b[0], pts[(i + 2) % n][1] - b[1]))
            if all(math.hypot(*v) >= max(4.0, ln * CUT_ARM)
                   and abs((v[0] * seg[0] + v[1] * seg[1])
                           / (math.hypot(*v) * ln)) <= CUT_SQUARE
                   for v in arms):
                out.append(math.degrees(math.atan2(seg[1], seg[0])) % 180.0)
    return out


def off_square(a):
    """How far a cut is from flat or upright, which is the only part that
    carries a decision.

    Not the angle itself. A terminal's absolute angle also records which side
    of the stroke it is on, and the face has no left-opening round lowercase
    for э to be compared against -- so э's chamfer came out at 135 where c's
    is at 45, and reading the angles reported the face's own treatment as
    foreign. The two are the same cut seen from the two sides.
    """
    a %= 90.0
    return min(a, 90.0 - a)


def oblique(paths, stem):
    """The cuts that are neither flat nor upright, by how far off square."""
    return sorted(round(off_square(a)) for a in cuts(paths, stem)
                  if off_square(a) > SQUARE_TOL)


def bars(polys, samples=40):
    """The horizontal strokes' weights, thinnest first.

    Read up vertical lines rather than off the nodes, because a horizontal is
    a run of ink and not a rectangle: Г's arm is one contour with its stem, and
    e's bar runs between two curves that never meet a node at the same height.

    A stroke is what PERSISTS. Taking the shortest run any single line happens
    to give reads the tip of a diagonal or the sliver above a corner instead --
    which is not a subtle failure, it flagged forty-three of the face's own
    letters. So the runs are grouped by the height they sit at and a group is a
    horizontal only once it has survived a fifth of the width.

    On the BUILT font, and not on the source, because a scanline pairs its
    crossings alternately and the source's contours overlap: H there is three
    rectangles, so a line through the crossbar's overlap with a stem crosses
    four edges and pairs them into two runs of nothing. The build unions them,
    and the same reading that gave H a phantom 271 gives it 135.
    """
    if not polys:
        return []
    xs = [q[0] for po in polys for q in po]
    ys = [q[1] for po in polys for q in po]
    lo, hi, height = min(xs), max(xs), max(ys) - min(ys)
    if hi - lo < 1 or height < 1:
        return []
    seen = {}
    for k in range(1, samples):
        x = lo + (hi - lo) * k / float(samples)
        for a, b in P.vruns(polys, x):
            if 0 < b - a < height * BAR_MAX:
                seen.setdefault(round((a + b) / 24.0), []).append((a, b))
    keep = []
    for v in seen.values():
        if len(v) < samples * 0.2:
            continue
        mids = [(a + b) / 2.0 for a, b in v]
        hs = sorted(b - a for a, b in v)
        # A horizontal holds its height AND stays at one height. Without the
        # second half, Ж's arms qualify: near the stem the upper pair and the
        # lower pair each cut a short run out of a vertical line, and they
        # persist across enough of the width to look like a bar. They are the
        # only thing in the set that does, and they gave Ж a phantom
        # horizontal that swung from 1.61 of the face's own at Regular to 0.72
        # at Bold -- a jump no drawn stroke makes, which is how it was caught.
        if max(mids) - min(mids) > height * 0.06:
            continue
        if hs[-1] - hs[0] > hs[len(hs) // 2] * 0.2:
            continue
        keep.append(hs[len(hs) // 2])
    return sorted(keep)


def subjects():
    """The Cyrillic this project draws, per case, as (letter, recipe name).

    Only outlines written here. A donor IS the Latin and a composite inherits
    it, so reading either would be reading the face back to itself.
    """
    out = {CAPS.label: [], LOWER.label: []}
    for cp, name, _tier, _note in TIERS:
        if name not in recipes.RECIPES:
            continue
        case = LOWER if LOWER.holds(cp) else CAPS
        out[case.label].append((chr(cp), name))
    return out


def cut_pass(selftest, subj):
    """How every drawn stroke ends, against how the Latin ends its own.

    On the SOURCE, where a terminal is a real straight segment between two
    real nodes. The build turns the cubics into quadratics and resamples them,
    so the same question asked there is asked of a different drawing.
    """
    src = glyphsLib.load("sources/SUSEMono.glyphs")
    findings = []
    for mi in range(len(src.masters)):
        pr = Params(src, mi)
        for case in (CAPS, LOWER):
            stem = pr.stem if case is CAPS else pr.lcStem
            ref = Counter()
            for ch in (list(case.alphabet)
                       + (list(DIGITS) if case is CAPS else [])):
                ref.update(oblique(pr.paths(ch), stem))
            rows = ([(ch, None) for ch in case.alphabet] if selftest
                    else subj[case.label])
            print("=" * 72)
            print(f"{pr.master.name} {case.label} terminals -- the face cuts "
                  f"oblique only at {sorted(ref) or 'nothing'}")
            for ch, gname in rows:
                paths = (pr.paths(ch) if gname is None
                         else list(recipes.RECIPES[gname](pr)))
                ob = [a for a in oblique(paths, stem)
                      if not any(abs(a - r) <= 4 for r in ref)]
                if ob:
                    print(f"    {ch}  cuts at {ob} where the face cuts square")
                    findings.append(f"{pr.master.name:9} {ch} cuts at {ob}")
            print(f"    ({len(rows)} read)")
    return findings


def _median(v):
    return sorted(v)[len(v) // 2]


def bar_pass(selftest, subj):
    """How heavy every horizontal is, against the Latin's own for that case.

    The reference is H's crossbar for the capitals and t's for the lowercase,
    which is where `params.py` reads them, and the tolerance is not chosen: it
    is the range the face's own letters already occupy. Over four weights and
    both cases every Latin letter that carries a horizontal sits between 0.89
    and 1.12 of its case's bar, so a drawn letter outside that is outside what
    the face does rather than outside a number picked here.

    On the BUILT fonts, which is also the only way to see Regular and Bold:
    the two masters interpolate, and a horizontal that is right at both ends
    can still be wrong in between if it was pinned rather than derived.
    """
    findings = []
    for weight in WEIGHTS:
        f = TTFont(f"fonts/ttf/SUSEMono-{weight}.ttf", lazy=True)
        try:
            cm, gs = f.getBestCmap(), f.getGlyphSet()
            for case in (CAPS, LOWER):
                own = bars(P.contours(f, case.stem if case is CAPS else "t",
                                      cm, gs) or [])
                if not own:
                    continue
                ref = _median(own)
                seen = []
                for ch in case.alphabet:
                    b = bars(P.contours(f, ch, cm, gs) or [])
                    if b:
                        seen.append(_median(b) / ref)
                lo, hi = min(seen), max(seen)
                rows = ([(ch, None) for ch in case.alphabet] if selftest
                        else subj[case.label])
                print("=" * 72)
                print(f"{weight} {case.label} horizontals -- the face's own "
                      f"is {ref:.0f}, and its own letters hold "
                      f"{lo:.2f}-{hi:.2f} of it")
                for ch, _g in rows:
                    b = bars(P.contours(f, ch, cm, gs) or [])
                    if not b:
                        continue
                    d = _median(b) / ref
                    if not lo <= d <= hi:
                        print(f"    {ch}  horizontal {_median(b):.0f}, "
                              f"{d:.2f} of the face's own {ref:.0f}")
                        findings.append(f"{weight:9} {ch} horizontal "
                                        f"{d:.2f} of the face's own")
                print(f"    ({len(rows)} read)")
        finally:
            f.close()
    return findings


def report(selftest=False):
    subj = subjects()
    return cut_pass(selftest, subj) + bar_pass(selftest, subj)


if __name__ == "__main__":
    out = report("--selftest" in sys.argv)
    print("=" * 72)
    print(f"{len(out)} findings")
