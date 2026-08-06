"""Sweep every new glyph for the defect classes found by review.

Each check here exists because a specific defect got past me and had to be
pointed out. They are cheap to run and they do not depend on my judgement,
which is the point.

  acute corners   a slanted stroke meeting a horizontal one at a sharp angle
                  reads as a nick or a spike. This was Л's top left, twice.
  square turns    where ONE stroke turns into another this face rounds it --
                  E, F, L, C, G, S, U, B, D, P, R all do. A hard 90 degree
                  outer corner at a turn is what made Ц's leg look stuck on.
  heavy appendage a leg, tick or foot must never outweigh the stems it hangs
                  from. Ц's leg was 65% over at Thin.
  pinched counter a counter squeezed to a slit, which is what Ф and Ю did
                  before the crowding model was applied.
  swallowed curve a rounded corner on one contour that a second contour of
                  the same glyph fills straight back in. Ґ's tick sat on Г's
                  arm and the arm ended square at exactly the tick's edge, so
                  the rounding never appeared and a notch opened where the two
                  stopped overlapping. Every contour was correct on its own,
                  which is why nothing else caught it.

    python tools/audit.py
"""

import math
import sys
from collections import Counter

from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from classify import TIERS          # noqa: E402
from params import Params, _flatten  # noqa: E402
import recipes                     # noqa: E402

# How tight a counter may get, and how sharp a corner, are the face's
# decisions and not mine. A flat 0.28 of the stem flagged И and Щ for counters
# that N's own diagonal already closes to the same width at ExtraBold; the
# face's own diagonals answer instead, measured per weight at the same scan
# line, because the angle opens as the strokes thicken.
#
# Both of these used to carry a backstop underneath the measurement -- no
# counter under 0.10 of the stem, no corner under 30 degrees -- and --selftest
# showed both sitting ABOVE what the Latin already does: Y's own fork closes
# to 7 units where 0.10 of the stem is 9, and M's own terminal comes to 22
# degrees where the floor said 30. A threshold that flags the letters it was
# measured from is not a measurement, so the backstops are gone and the
# defaults below apply only if the reference set is missing altogether.
NO_REFERENCE_COUNTER = 0.0
NO_REFERENCE_ANGLE = 62.0

# Recipes that reproduce a glyph this face already draws, unchanged. Their
# corners are the face's corners, so measuring them against the capitals says
# nothing -- З was being reported for a 25-degree waist that belongs to the
# figure three, which is the whole glyph. What IS worth checking is that they
# still match what they claim to reproduce.
CLONES = {"Ze-cy": "three"}

# Backstops for the bowl family, in the same spirit as ACUTE_FLOOR: the
# comparison is against the face's own В, so these only say how far apart the
# two may drift before it is worth reporting. The probe below reads Ь, Ъ and Б
# at exactly В's own figures at all three weights, so the tolerance is here to
# absorb outline rounding -- a unit or so -- rather than the measurement's own
# noise. The two faults that prompted the check were 4.3% and 21% out.
BOWL_END = 0.02
BOWL_WEIGHT = 0.02
# ...and never tighter than this many units, whatever the percentage works out
# to. The comment above says the tolerance is here to absorb outline rounding,
# "a unit or so", and 2 per cent of a 29-unit stroke is 0.58 -- too tight to
# do what it claims. в reads 0.7 light against ь and ъ at every master purely
# because its elliptical arcs reach their widest by a different route, so the
# probe lands on a sample where the counter's bezier has already begun to
# turn. All four are drawn with the identical stroke. The faults this check
# exists for were 22 and 35 units out at ExtraBold.
BOWL_UNIT = 1.5
# The band the lower bowl lives in, and how finely to walk it. Wide enough to
# contain the widest point at every master and to stay clear of both the
# baseline corner and the waist.
BOWL_BAND = (0.12, 0.42)
BOWL_STEPS = 60


class Case:
    """Which Latin glyphs answer each of the questions below, for one case.

    Every threshold here is read off the face rather than picked, so each one
    needs a Latin glyph to read it off -- and the Latin answers differently
    for capitals and for lowercase. H's stem is not n's; O overshoots the cap
    line where o overshoots the x-height; no capital in this face descends at
    all while five lowercase drop to -200.

    `alphabet` is what --selftest sweeps: the face's own letters, put through
    the same checks as the Cyrillic. If a threshold flags the Latin that grew
    it, the threshold is wrong, and that is worth knowing before drawing
    thirty-one glyphs against it.
    """

    def __init__(self, label, metric, stem, acute, counter, round_, flat,
                 asc, desc, bowls, alphabet, holds):
        self.label = label
        self.metric = metric        # OS/2 field giving this case's top line
        self.stem = stem            # the face's own plain two-stem letter
        self.acute = acute          # every corner construction it already makes
        self.counter = counter      # and every counter it already closes
        self.round_ = round_        # letters that turn at the line: they overshoot
        self.flat = flat            # letters that end flat: they sit on it
        self.asc = asc              # how far above the line the face reaches
        self.desc = desc            # and how far below
        self.bowls = bowls          # (drawn glyph, the Latin it hangs off)
        self.alphabet = alphabet
        self.holds = holds


def _is_lower(cp):
    return 0x0430 <= cp <= 0x045F or cp == 0x0491


CAPS = Case(
    label="capital",
    metric="sCapHeight",
    stem="H",
    acute="AKMNVWXYZ",
    counter="ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    round_=("O", "C", "S", "G", "zero", "three", "six", "eight", "nine"),
    flat=("H", "E", "T", "B", "D", "P"),
    # No capital gets a ceiling check: the cap line IS the ceiling, and Ґ's
    # upturn is meant to clear it. That is measured, not assumed -- Ґ rises
    # 0.210 of the cap above Г here, against a panel median of 0.213 across
    # the 37 reference faces that carry the letter, well inside their
    # 0.130-0.274. So there is no single ceiling to check a capital against.
    asc=(),
    # and none descends, so the rule for Д Ц Щ can only be that they agree
    # with each other
    desc=(),
    bowls=(("Ь", "В"), ("Ъ", "В"), ("Б", "В")),
    # Q is left out of the self-test for the same reason f g i j t are below:
    # its descending part is a broad flag merged into the bowl rather than a
    # distinct stroke, so "an appendage must not outweigh the stem it hangs
    # from" has no stem to read and measures 265 against 165. Every Cyrillic
    # capital that descends -- Д Ц Щ -- hangs a separate upright instead.
    alphabet="ABCDEFGHIJKLMNOPRSTUVWXYZ",
    holds=lambda cp: not _is_lower(cp),
)

LOWER = Case(
    label="lowercase",
    metric="sxHeight",
    stem="n",
    # k v w x y z are the diagonal terminals, as above. b d h m n p q r u are
    # here because the lowercase has a construction the capitals do not: a
    # stroke springing off a stem tangentially, which opens a far sharper
    # wedge than any diagonal -- r's is 19 degrees at Thin against the
    # diagonals' 29. Leaving them out set the limit above what the face does
    # to nine of its own letters. Every Cyrillic bowl-on-a-stem -- в б ь ъ я
    # ю -- is that same spring, so this is the construction they answer to.
    acute="bdhkmnpqruvwxyz",
    counter="abcdefghijklmnopqrstuvwxyz",
    round_=("a", "c", "e", "o", "s", "u"),
    flat=("n", "m", "r", "v", "w", "x", "z"),
    asc=("b", "d", "h", "k", "l"),
    desc=("g", "j", "p", "q", "y"),
    bowls=(("ь", "в"), ("ъ", "в"), ("б", "в")),
    # f g i j t are left out of the self-test on purpose: each ends at a
    # height that is its own business -- f's hook, g's ear, i and j's dot, t's
    # short ascender -- and no Cyrillic letter reproduces any of them, so the
    # ceiling rule that б and ф must meet was never meant to cover them.
    alphabet="abcdehklmnopqrsuvwxyz",
    holds=_is_lower,
)

CASES = (CAPS, LOWER)


STEPS = 16      # samples per curve segment
REACH = 25.0    # how far along the outline a corner's arms are measured


class _FlatPen(BasePen):
    """Outlines as polygons that follow the ink, with the real corners marked.

    The recording pen hands back control points, and taking those as polygon
    vertices puts a hard corner wherever the outline is in fact smooth -- B's
    waist read as a 17-degree spike that way, and every scanline in this file
    crossed the control polygon rather than the curve. BasePen decomposes
    components and turns the TrueType quadratics into cubics, so the only
    thing left to do is sample them.

    `ends` records which points are segment endpoints. A corner can only exist
    at one of those; the rest are samples along a curve, and asking them about
    angles is what made a curve look like a run of corners.
    """

    def __init__(self, glyphSet):
        BasePen.__init__(self, glyphSet)
        self.polys = []
        self.cur = []
        self.ends = []

    def _moveTo(self, pt):
        self.cur, self.marks = [pt], [True]

    def _lineTo(self, pt):
        self.cur.append(pt)
        self.marks.append(True)

    def _curveToOne(self, c1, c2, pt):
        p0 = self.cur[-1]
        for s in range(1, STEPS + 1):
            self.cur.append(_bez(p0, c1, c2, pt, s / float(STEPS)))
            self.marks.append(s == STEPS)

    def _closePath(self):
        if self.cur:
            # a contour that closes back onto its start point carries it twice
            if (len(self.cur) > 1
                    and math.dist(self.cur[0], self.cur[-1]) < 1e-6):
                self.cur.pop()
                self.marks.pop()
            self.polys.append(self.cur)
            self.ends.append([i for i, m in enumerate(self.marks) if m])
            self.cur = []

    def _endPath(self):
        self._closePath()


def flatten(gs, name):
    """(polygon, indices of its real corners) for each contour."""
    pen = _FlatPen(gs)
    gs[name].draw(pen)
    return list(zip(pen.polys, pen.ends))


def contours(gs, name):
    return [p for p, _ in flatten(gs, name)]


# A lowercase letter turns at the same radius as its own capital. The face
# says so twice over: its INNER corner is one number everywhere -- 78 at Thin
# and 20 at ExtraBold, identical in E, F, L, t and f, across both cases -- and
# its OUTER is the same at Thin and WIDER in the lowercase at ExtraBold, 168
# in t and f against 122 in E, F and L. So a lowercase corner is never
# tighter than its capital's.
#
# г was drawn at half. It took П's reduction, which is only for a bend whose
# shorter stroke cannot carry the whole corner, and its inner radius came from
# `ro - s`, which goes negative at ExtraBold and floored at 4 where the face
# holds 20. Both lines were copied from П without checking them against the
# rule, and nothing here compared a letter to its own capital, so the sweep
# stayed clean while the same letter turned twice as tightly at x-height.
CORNER_PAIRS = [
    ("Ge-cy", "ge-cy"), ("Pe-cy", "pe-cy"), ("Sha-cy", "sha-cy"),
    ("Shcha-cy", "shcha-cy"), ("Tse-cy", "tse-cy"), ("Ii-cy", "ii-cy"),
]

# Ц and Щ hang their tail off an overhang, and a corner cannot be wider than
# the overhang it turns inside without reversing the outline into a spike --
# which is a fault this file has already had once. The lowercase overhang is
# 50.7 against the capital's 71.9, so its tail corner is bound to 47 where the
# capital reaches the full 67. Forced by the geometry, and by the face's own
# rule that a bend is bounded by the shorter of the strokes it joins. One
# radius may therefore differ, and only by coming out TIGHTER; anything else
# still reports.
CORNER_EXEMPT = {"tse-cy", "shcha-cy"}

# Д Ц Щ Џ and their lowercase hang a TAIL off the baseline, and a tail is not
# a descender. p's stroke carries on down past the baseline; ц's turns and
# stops. They are different features and they do not reach the same depth --
# across 60 faces ц's tail runs 0.94 of its own Ц's, while p's descender is a
# third deeper again. Seeding these from the Latin's p q y g j made the sweep
# insist they match it, which is precisely the bad inference that had ц
# descending a full 200 and reading far too long against Ц. So the tails are
# one group, agreeing with each other, and true descenders are another.
TAILED = set("ДЦЩЏдцщџ")

# ...and a lowercase tail hangs as deep as its own capital's, in absolute
# units, though its body is a third shorter. Checking the tails only against
# each other would not have caught this: ц and щ were both a full descender
# deep and agreed perfectly. It is the relation to the CAPITAL that broke.
#
# Equality is stricter than the panel's median of 0.94, and deliberately so:
# it is the commonest value there by a wide margin, drawn by 26 of the 60
# faces against 14 for the next, and it is the rule this file has chosen --
# one depth for both cases, see recipes.descent. The fault it replaces sat at
# 1.333, outside all sixty.
TAIL_PAIRS = (("ц", "Ц"), ("щ", "Щ"), ("д", "Д"), ("џ", "Џ"))

# A lowercase must be its capital's SHAPE, size aside. Sampling each letter's
# right edge up its own height and dividing by its own width strips out the
# size, the weight and the sidebearings and leaves the silhouette, so the two
# cases become directly comparable. Every pair here agrees to within 0.053.
#
# Only the MEAN difference is checked, never the worst. A bar or a tail is a
# fixed number of units in both cases -- rightly so, the panel says the same
# -- and therefore occupies a bigger fraction of a shorter letter, so a single
# sample can land above the arm in Г and inside it in г and jump by 0.8 on its
# own. That is physical, not a defect.
PROFILE_PAIRS = "ВвГгНнТтПпШшЩщЦцИиЬьЪъЫы"
PROFILE_TOL = 0.08


def profile(gs, gname):
    """The letter's right edge up its own height, over its own width."""
    polys = contours(gs, gname)
    if not polys:
        return None
    ys = [q[1] for po in polys for q in po]
    xs = [q[0] for po in polys for q in po]
    top, bot, left, right = max(ys), min(ys), min(xs), max(xs)
    if right <= left or top <= bot:
        return None
    out = []
    for j in range(5, 100, 5):
        cr = runs(polys, bot + (top - bot) * j / 100.0 + 0.13)
        out.append((max(cr) - left) / (right - left) if len(cr) >= 2 else None)
    return out


def corner_set(paths):
    """Every near-circular turn in a glyph, by radius.

    Circular is what separates a corner from a bowl: the face's corners run
    103x103 and 78x78 at Thin, while b's bowl sweeps 204x238 and 187x145. So
    a chord whose two extents are within a quarter of each other is a corner
    and the rest of the drawing is left alone.
    """
    out = []
    for p in paths:
        ns = list(p.nodes)
        st = next((i for i, n in enumerate(ns) if n.type != "offcurve"), 0)
        ns = ns[st:] + ns[:st]
        prev, pend = ns[0], []
        for n in ns[1:] + [ns[0]]:
            if n.type == "offcurve":
                pend.append(n)
                continue
            if n.type == "curve" and len(pend) == 2:
                dx = abs(n.position.x - prev.position.x)
                dy = abs(n.position.y - prev.position.y)
                if min(dx, dy) > 2 and min(dx, dy) / max(dx, dy) > 0.75:
                    out.append(round(max(dx, dy)))
            pend = []
            prev = n
    return sorted(out)


def corner_drift(low, cap, exempt):
    """What differs between a lowercase letter's corners and its capital's."""
    if low == cap:
        return None
    only_low = Counter(low) - Counter(cap)
    only_cap = Counter(cap) - Counter(low)
    if (exempt and sum(only_low.values()) == 1
            and sum(only_cap.values()) == 1
            and min(only_low) < min(only_cap)):
        return None
    return f"{low} against its capital's {cap}"


def _walk(poly, ends, i, step):
    """Where a corner's arm points: up to REACH units along the outline, but
    never past the next corner.

    Both halves of that matter. Following arc length rather than the
    neighbouring sample lets one threshold serve a straight arm and a curved
    one alike. Stopping at the next corner keeps a short feature from being
    walked straight over -- at Thin the strokes are 29 units wide, so a
    25-unit reach ran around r's whole terminal and came back down the other
    side, reporting the arm's own width as a 19-degree spike.
    """
    n = len(poly)
    left, at = REACH, poly[i]
    for k in range(1, n):
        j = (i + step * k) % n
        nxt = poly[j]
        d = math.dist(at, nxt)
        if d >= left:
            t = left / d if d else 0.0
            return (at[0] + (nxt[0] - at[0]) * t,
                    at[1] + (nxt[1] - at[1]) * t)
        left -= d
        at = nxt
        if j in ends:
            return at
    return at


def corner_angles(poly, ends):
    """Interior angle at each real corner, plus whether it is a point of INK
    or a notch of white.

    The arms are taken REACH units back and on along the outline, not to the
    neighbouring vertex. On a curve that reads as the turn accumulated over 25
    units -- a dozen degrees at any radius this face uses -- so a smooth join
    stays near 180 and only a genuine corner comes down.

    Ink and white fail at completely different angles and have to be judged
    apart. A sharp ink point is a spike -- it prints weak, and it is what Л's
    top left was doing. A sharp white notch is a wedge cut into the shape,
    which this face uses freely: at Thin, M and W close their inner vertices
    to under 20 degrees. Measuring both together collapses the limit onto the
    notches and the check stops catching spikes at all.
    """
    n = len(poly)
    if n < 3:
        return
    seen = set(ends)
    ccw = sum((poly[i][0] - poly[i - 1][0]) * (poly[i][1] + poly[i - 1][1])
              for i in range(n)) < 0
    for i in ends:
        b = poly[i]
        a, c = _walk(poly, seen, i, -1), _walk(poly, seen, i, 1)
        v1 = (a[0] - b[0], a[1] - b[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        # too short an arm to have a direction worth reading
        if l1 < 2.0 or l2 < 2.0:
            continue
        cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)
        # v1 points BACK along travel, so the turn is cross(-v1, v2); ink sits
        # on the inside of that turn. Reading it the other way round swapped
        # the two classes wholesale -- both the reference and the subject, so
        # no verdict was ever wrong, but every "spike" in a finding was a
        # notch and the limits were each measured off the other's letters.
        cross = -(v1[0] * v2[1] - v1[1] * v2[0])
        yield (b, math.degrees(math.acos(max(-1.0, min(1.0, cosang)))),
               (cross > 0) == ccw)


def _bez(p0, c1, c2, p3, t):
    mt = 1.0 - t
    return (mt**3 * p0[0] + 3 * mt * mt * t * c1[0]
            + 3 * mt * t * t * c2[0] + t**3 * p3[0],
            mt**3 * p0[1] + 3 * mt * mt * t * c1[1]
            + 3 * mt * t * t * c2[1] + t**3 * p3[1])


def _meet(a, b, c, d):
    """Where line a->b crosses line c->d, or None if they are parallel."""
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-9:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    return (a[0] + t * r[0], a[1] + t * r[1])


def _wraps(poly, pt):
    """Winding number of a polygon about a point -- nonzero means filled."""
    x, y = pt
    w = 0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if y0 <= y < y1 and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) > 0:
            w += 1
        elif y1 <= y < y0 and (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0) < 0:
            w -= 1
    return w


def swallowed_curves(paths, polys):
    """Curves whose bend is filled in by another contour of the same glyph.

    A rounded corner only exists because the ink stops short of the corner
    point. Lay a second contour over that gap -- Ґ's tick sat on Г's arm, and
    the arm ended square at exactly the tick's edge -- and the corner is
    filled straight back in: the rounding is invisible where the two overlap
    and bites a notch out of the shape where they stop overlapping. It looks
    like a drawing mistake because it is one, and neither the interpolation
    check nor the corner check can see it, because each contour is correct on
    its own.

    So: for every curve on an ink contour, take the corner it is cutting off
    and ask whether anything ELSE in the glyph fills that gap.
    """
    out = []
    for i, (path_, poly) in enumerate(zip(paths, polys)):
        # Counters are MEANT to sit inside ink, so only ink contours are asked.
        # This source's convention: positive signed area is the outer
        # direction, negative subtracts.
        if _signed(poly) <= 0:
            continue
        others = [q for j, q in enumerate(polys) if j != i]
        if not others:
            continue
        ns = list(path_.nodes)
        start = next((k for k, n in enumerate(ns) if n.type != "offcurve"), 0)
        ns = ns[start:] + ns[:start]
        prev = ns[0]
        pend = []
        for n in ns[1:] + [ns[0]]:
            if n.type == "offcurve":
                pend.append(n)
                continue
            if n.type == "curve" and len(pend) == 2:
                p0 = (prev.position.x, prev.position.y)
                c1 = (pend[0].position.x, pend[0].position.y)
                c2 = (pend[1].position.x, pend[1].position.y)
                p3 = (n.position.x, n.position.y)
                corner = _meet(p0, c1, p3, c2)
                span = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
                if corner and span > 8:
                    mid = _bez(p0, c1, c2, p3, 0.5)
                    reach = math.hypot(corner[0] - mid[0], corner[1] - mid[1])
                    if reach < 3 * span:
                        # just inside the gap the curve opens up
                        probe = (corner[0] + 0.35 * (mid[0] - corner[0]),
                                 corner[1] + 0.35 * (mid[1] - corner[1]))
                        if any(_wraps(q, probe) != 0 for q in others):
                            out.append(corner)
            pend = []
            prev = n
    return out


def _bowl(gs, name, top):
    """Where the lower bowl ends, and the weight of its own right-hand stroke.

    The rightmost ink run IS that stroke, in В as in Ь: the scanline crosses
    the spine, the counter, then the bowl's wall. But only where the bowl is
    at its WIDEST, and that height has to be found rather than named. A fixed
    fraction of the cap lands in a different part of the curve at each master:
    at 0.22 the ExtraBold counter has only just opened, so the scanline cut
    the wall obliquely and read it 9 per cent heavy -- which is why Б could
    never be checked here numerically and had to be passed by eye. Where the
    bowl is widest the wall is vertical, so the run across it is its true
    thickness, and В's comes out at 166 at ExtraBold: the same figure
    latin_metrics reads straight off B's nodes.
    """
    polys = contours(gs, name)
    rows = []
    lo, hi = BOWL_BAND
    for i in range(BOWL_STEPS + 1):
        xs = runs(polys, top * (lo + (hi - lo) * i / float(BOWL_STEPS)))
        # under four crossings means the counter has not opened at this height
        if len(xs) >= 4:
            rows.append((xs[-1], xs[-1] - xs[-2]))
    if not rows:
        return None
    end = max(r[0] for r in rows)
    return end, min(r[1] for r in rows if r[0] > end - 1.0)


def _signed(poly):
    """Signed area, same convention as geom.area: positive is the outer
    direction this source draws ink in."""
    return 0.5 * sum(x0 * y1 - x1 * y0
                     for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))


def _thickness(polys, y, d=12.0):
    """How thick the leftmost stroke is at height y -- across the stroke,
    not across the page.

    Two corrections, and Q needs both. A scanline reports a stroke leaning at
    angle t as 1/cos wider than it is, so where the stroke's centre travels
    between two heights gives the lean and the lean gives the correction. And
    a bar lying on its side is only as thick as it is TALL, however far it
    reaches: Q's tail is a 269-unit slab against a 165 stem read horizontally,
    and 140 units deep read the way it is actually drawn.
    """
    a, b = runs(polys, y - d), runs(polys, y + d)
    if len(a) < 2 or len(b) < 2:
        return None
    w = (a[1] - a[0] + b[1] - b[0]) / 2.0
    slope = ((b[0] + b[1]) - (a[0] + a[1])) / 2.0 / (2.0 * d)
    across = w / math.hypot(1.0, slope)
    cx = (a[0] + a[1] + b[0] + b[1]) / 4.0
    tall = min((hi - lo for lo, hi in zip(vruns(polys, cx)[0::2],
                                          vruns(polys, cx)[1::2])
                if lo <= y <= hi), default=None)
    return across if tall is None else min(across, tall)


def vruns(polys, x):
    ys = []
    for poly in polys:
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            if (x0 - x) * (x1 - x) < 0:
                ys.append(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    ys.sort()
    return ys


def runs(polys, y):
    xs = []
    for poly in polys:
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            if (y0 - y) * (y1 - y) < 0:
                xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    xs.sort()
    return xs


def reference(gs, case, top):
    """Read this case's thresholds off the Latin, at this weight.

    Nothing here is a number I chose. The stem comes from the face's own
    two-stem letter, the counter floor from the tightest gap its own diagonals
    already close to, and the corner limits from the sharpest terminal it
    already cuts -- separately for ink and for white, because the two fail at
    completely different angles.
    """
    if case.stem not in gs:
        return None
    sx = runs(contours(gs, case.stem), top * 0.25)
    stem = (sx[1] - sx[0]) if len(sx) >= 2 else None

    gaps = []
    for n in case.counter:
        if n in gs:
            rx = runs(contours(gs, n), top * 0.55)
            gaps += [b - a for a, b in zip(rx[1::2], rx[2::2]) if b > a]

    acute = {}
    for ink in (True, False):
        acute[ink] = min(
            (ang for n in case.acute if n in gs
             for poly, ends in flatten(gs, n)
             for _, ang, k in corner_angles(poly, ends) if k is ink),
            default=NO_REFERENCE_ANGLE)

    # where the face lets ink sit relative to this case's own top and bottom
    def edges(names):
        out = {}
        for n in names:
            if n in gs:
                ys = [p[1] for poly in contours(gs, n) for p in poly]
                out[n] = (-min(ys), max(ys))
        return out

    rounds = sorted({round(v[0]) for v in edges(case.round_).values()})
    flats = sorted({round(v[0]) for v in edges(case.flat).values()})
    return {
        "top": top,
        "stem": stem,
        "counter": min(gaps) if gaps else NO_REFERENCE_COUNTER,
        "acute": acute,
        "rounds": rounds,
        "flats": flats,
        "asc": sorted({round(v[1]) for v in edges(case.asc).values()}),
        "desc": {n: round(v[0]) for n, v in edges(case.desc).items()},
    }


def sweep(gs, subjects, ref, weight):
    """Put one case's drawn glyphs through the per-glyph checks.

    Returns the findings, and how far each glyph reached past the case's top
    and bottom lines, which only mean anything once the whole set is in.
    """
    out, depths, tails = [], dict(ref["desc"]), {}
    top, stem, floor = ref["top"], ref["stem"], ref["counter"]
    for ch, gname in subjects:
        shapes = flatten(gs, gname)
        polys = [p for p, _ in shapes]
        if not polys:
            continue

        for poly, ends in shapes:
            for pt, ang, ink in corner_angles(poly, ends):
                if ang < ref["acute"][ink]:
                    out.append(
                        f"{weight:9} {ch} {'spike' if ink else 'notch'} "
                        f"{ang:.0f}deg < Latin's own {ref['acute'][ink]:.0f} "
                        f"at ({pt[0]:.0f},{pt[1]:.0f})")

        # anything hanging below the baseline must not outweigh the stems
        ymin = min(p[1] for poly in polys for p in poly)
        if ymin < -20 and stem:
            lw = _thickness(polys, ymin * 0.5)
            body = runs(polys, top * 0.25)
            if lw and len(body) >= 2:
                sw = body[1] - body[0]
                if lw > sw * 1.05:
                    out.append(f"{weight:9} {ch} appendage {lw:.0f} heavier "
                               f"than stem {sw:.0f}")

        # counters that have closed to slits
        if stem:
            xs = runs(polys, top * 0.55)
            for g in (b - a for a, b in zip(xs[1::2], xs[2::2])):
                if 0 < g < floor:
                    out.append(f"{weight:9} {ch} counter {g:.0f} < Latin's "
                               f"own {floor:.0f} (stem {stem:.0f})")

        # Round-ended letters overshoot the line and flat-ended ones sit on
        # it. A glyph a few units off either, for no reason, belongs to
        # neither habit. The face is not down to a single figure -- O
        # overshoots 10 at Thin and 15 at ExtraBold -- so the rule is not one
        # value but a value the face actually uses, which is why the digits
        # are in the capitals' reference set and why З, being the figure
        # three, is not adrift for overshooting 10 where О overshoots 15.
        ymax = max(p[1] for poly in polys for p in poly)
        pad = max(ref["rounds"] + [0]) + 5
        if ymin < -pad:
            (tails if ch in TAILED else depths)[ch] = round(-ymin)
        elif round(-ymin) not in ref["rounds"] + ref["flats"]:
            out.append(f"{weight:9} {ch} sits {-ymin:.0f} below the baseline "
                       f"-- the face uses {ref['flats']} or {ref['rounds']}")
        # and a glyph that reaches above the line must reach the height the
        # face reaches, not one of its own
        if ref["asc"] and ymax > top + pad and round(ymax) not in ref["asc"]:
            out.append(f"{weight:9} {ch} rises to {ymax:.0f} -- the face's "
                       f"own ascenders reach {ref['asc']}")
    return out, depths, tails


def main():
    import glyphsLib
    present = {g.name for g in glyphsLib.load("sources/SUSEMono.glyphs").glyphs}
    selftest = "--selftest" in sys.argv
    findings = []

    for weight in ("Thin", "Regular", "ExtraBold"):
        f = TTFont(f"fonts/ttf/SUSEMono-{weight}.ttf")
        cmap = f.getBestCmap()
        gs = f.getGlyphSet()

        for case in CASES:
            ref = reference(gs, case, getattr(f["OS/2"], case.metric))
            if ref is None:
                continue

            subjects = []
            for cp, name, _, _ in TIERS:
                # only outlines I drew. Donors and base+mark composites
                # inherit their corners from the Latin -- the accents are
                # pointed by design and y's tail comes to a vertex, and
                # neither is mine.
                if not case.holds(cp) or cp not in cmap:
                    continue
                if name not in present or name not in recipes.RECIPES:
                    continue
                if name in CLONES:
                    mine = contours(gs, cmap[cp])
                    theirs = contours(gs, CLONES[name])
                    if [len(p) for p in mine] != [len(p) for p in theirs]:
                        findings.append(
                            f"{weight:9} {chr(cp)} no longer matches the "
                            f"{CLONES[name]} it reproduces")
                    continue
                subjects.append((chr(cp), cmap[cp]))
            if selftest:
                subjects = [(n, n) for n in case.alphabet if n in gs]

            got, depths, tails = sweep(gs, subjects, ref, weight)
            findings += got
            # Every glyph that descends does so to the SAME depth -- true of
            # Д Ц Щ in each of the five drawn faces measured, and true of the
            # Latin's own p q y g j here. Where the Latin answers, `depths`
            # starts seeded with its answer, so a drawn glyph is compared
            # against the face rather than only against its own siblings.
            for group, what in ((depths, "descending"), (tails, "tailed")):
                if len(set(group.values())) > 1:
                    findings.append(
                        f"{weight:9} {what} {case.label}s disagree on depth: "
                        + ", ".join(f"{c} {d}"
                                    for c, d in sorted(group.items())))

    # Coincident nodes are checked in the SOURCE, on real nodes. Measured on
    # the built outline they cannot be told apart from a curve's control
    # points, which sit close together by design -- that gave five glyphs of
    # false positives. Two points on top of each other leave a nick where a
    # curve meets a straight, which is invisible in the filled shape.
    import glyphsLib as _gl
    src = _gl.load("sources/SUSEMono.glyphs")
    prs = [Params(src, mi) for mi in range(len(src.masters))]
    for cp, name, _, _ in TIERS:
        fn = recipes.RECIPES.get(name)
        if not fn:
            continue
        for pr in prs:
            paths = list(fn(pr))
            for path_ in paths:
                ns = list(path_.nodes)
                for a, b in zip(ns, ns[1:] + ns[:1]):
                    if (abs(a.position.x - b.position.x) < 0.6
                            and abs(a.position.y - b.position.y) < 0.6):
                        findings.append(
                            f"{pr.master.name:9} {chr(cp)} coincident nodes "
                            f"at ({a.position.x:.0f},{a.position.y:.0f})")
                        break

            # a curve whose bend another contour fills straight back in
            polys = [_flatten(p) for p in paths]
            for x, y in swallowed_curves(paths, polys):
                findings.append(
                    f"{pr.master.name:9} {chr(cp)} rounded corner at "
                    f"({x:.0f},{y:.0f}) is filled in by another contour")

    # a lowercase letter turns the way its own capital does -- see CORNER_PAIRS
    for upper, lower in CORNER_PAIRS:
        fu, fl = recipes.RECIPES.get(upper), recipes.RECIPES.get(lower)
        if not fu or not fl:
            continue
        ch = next((chr(cp) for cp, n, _, _ in TIERS if n == lower), lower)
        for pr in prs:
            drift = corner_drift(corner_set(list(fl(pr))),
                                 corner_set(list(fu(pr))),
                                 lower in CORNER_EXEMPT)
            if drift:
                findings.append(
                    f"{pr.master.name:9} {ch} turns {drift}")

    # ---- the rest of the set: donors and base+mark composites -------------
    # Their outlines come from the Latin, so corner and stroke checks would
    # only re-report the face's own drawing. What CAN go wrong is the join:
    # a mark sitting on top of its base, off-centre, or pushed outside the
    # cell. And a donor pointing at the wrong Latin letter renders perfectly
    # and is still wrong.
    import glyphsLib as _gl2
    from classify import TIERS as _T
    src2 = _gl2.load("sources/SUSEMono.glyphs")
    byname = {g.name: g for g in src2.glyphs}
    donors = {n: note for cp, n, t, note in _T if t == 1}

    for weight in ("Thin", "Regular", "ExtraBold"):
        f = TTFont(f"fonts/ttf/SUSEMono-{weight}.ttf")
        cmap = f.getBestCmap()
        gs = f.getGlyphSet()
        asc = f["OS/2"].sTypoAscender
        desc = f["OS/2"].sTypoDescender

        for cp, name, tier, note in _T:
            if name not in byname or cp not in cmap:
                continue
            g = byname[name]
            comps = [c.name for c in g.layers[0].components]
            polys = contours(gs, cmap[cp])
            if not polys:
                continue
            ch = chr(cp)
            xs = [p[0] for poly in polys for p in poly]
            ys = [p[1] for poly in polys for p in poly]

            # a donor must be the SAME drawing as the Latin it names
            if tier == 1 and note in gs:
                ref = contours(gs, note)
                if len(ref) != len(polys):
                    findings.append(
                        f"{weight:9} {ch} donor differs from Latin {note}")

            # composites: the mark must clear the base and sit centred
            if len(comps) == 2 and comps[1] in gs:
                base = contours(gs, comps[0]) if comps[0] in gs else []
                mark = contours(gs, comps[1])
                if base and mark:
                    btop = max(p[1] for poly in base for p in poly)
                    mbot = min(p[1] for poly in mark for p in poly)
                    if mbot < btop - 2:
                        findings.append(
                            f"{weight:9} {ch} mark overlaps base by "
                            f"{btop - mbot:.0f}")
                    mxs = [p[0] for poly in mark for p in poly]
                    off = (min(mxs) + max(mxs)) / 2 - 300
                    if abs(off) > 12:
                        findings.append(
                            f"{weight:9} {ch} mark off-centre by {off:+.0f}")

            # nothing may sit outside the vertical band the font declares
            if max(ys) > asc + 5 or min(ys) < desc - 5:
                findings.append(
                    f"{weight:9} {ch} outside typo metrics: "
                    f"{min(ys):.0f}..{max(ys):.0f} vs {desc}..{asc}")

    # ---- house style ------------------------------------------------------
    # Things that are not defects in any one glyph but break the face's own
    # habits when the set is read together. Each is a rule the FACE states,
    # measured off it, not a preference of mine.
    #
    # Ь Ъ Б hang the same bowl, and it is a bowl this face already draws: В
    # here IS the Latin B, a donor, unchanged. So the three are checked
    # against В rather than against a number -- where the bowl ends, and how
    # heavy its own stroke is. Both had drifted: the bowl was pinned to a
    # fraction of the advance while B's narrows at the light end, and it
    # carried m's three-stem reduction although nothing crowds it, so at
    # ExtraBold its stroke was 0.79 of В's. The lowercase repeats the whole
    # arrangement at x-height, so it gets the same check against в.
    #
    # Left out on purpose: Ы, which carries a third stroke and shaves for it,
    # as every drawn face does; and Ф and Ю, which hang O's bowl rather than
    # B's and take the same shave.
    for weight in ("Thin", "Regular", "ExtraBold"):
        f = TTFont(f"fonts/ttf/SUSEMono-{weight}.ttf")
        cmap = f.getBestCmap()
        gs = f.getGlyphSet()

        for i in range(0, len(PROFILE_PAIRS), 2):
            up, low = PROFILE_PAIRS[i], PROFILE_PAIRS[i + 1]
            if ord(up) not in cmap or ord(low) not in cmap:
                continue
            pu, pl = profile(gs, cmap[ord(up)]), profile(gs, cmap[ord(low)])
            if not pu or not pl:
                continue
            d = [abs(a - b) for a, b in zip(pu, pl) if a and b]
            if d and sum(d) / len(d) > PROFILE_TOL:
                findings.append(
                    f"{weight:9} {low} is not {up}'s shape: silhouettes "
                    f"differ by {sum(d) / len(d):.3f} on average")

        for low, up in TAIL_PAIRS:
            if ord(low) not in cmap or ord(up) not in cmap:
                continue
            def _floor(ch):
                polys = contours(gs, cmap[ord(ch)])
                return min(p[1] for poly in polys for p in poly) if polys else 0
            a, b = _floor(low), _floor(up)
            if abs(a - b) > 2:
                findings.append(
                    f"{weight:9} {low} tail reaches {-a:.0f} where its "
                    f"capital {up} reaches {-b:.0f}")

        for case in CASES:
            top = getattr(f["OS/2"], case.metric)
            for ch, host in case.bowls:
                if ord(ch) not in cmap or ord(host) not in cmap:
                    continue
                ref = _bowl(gs, cmap[ord(host)], top)
                got = _bowl(gs, cmap[ord(ch)], top)
                if not ref or not got:
                    continue
                if abs(got[0] - ref[0]) > max(BOWL_END * ref[0], BOWL_UNIT):
                    findings.append(
                        f"{weight:9} {ch} bowl ends at {got[0]:.0f} where "
                        f"{host} ends at {ref[0]:.0f}")
                if abs(got[1] - ref[1]) > max(BOWL_WEIGHT * ref[1],
                                              BOWL_UNIT):
                    findings.append(
                        f"{weight:9} {ch} bowl stroke {got[1]:.0f} against "
                        f"{host}'s own {ref[1]:.0f}")

    if not findings:
        print("audit clean")
        return
    seen = {}
    for x in findings:
        seen.setdefault(x.split()[1], []).append(x)
    print(f"{len(findings)} findings across {len(seen)} glyphs\n")
    for ch in sorted(seen):
        print(f"  {ch}")
        for x in seen[ch][:4]:
            print(f"      {x}")


main()
