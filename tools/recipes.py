import math
"""How each derived Cyrillic glyph is put together, per master.

A recipe is a function of the master's measured Params and returns contours.
Nothing here chooses a number by eye: proportions come from latin_metrics,
which reads them off the Latin that already solves the same problem (m for a
crowded third stem, W for crowded diagonals, A for how far a leg may splay,
p and y for descender depth, B for where a two-lobe letter waists).

Design rules this file obeys, from the brief:

  * Never mirror a Latin glyph to make a Cyrillic one. Internal symmetry
    within a single letter is fine; deriving И from Н or Я from R is not.
  * The heaviest master is the constraint. Where a letter cannot hold Latin
    stem weight in 600 units, counters give way first and stem weight last.
  * Corners follow the face: where one stroke TURNS it rounds, where two
    cross it stays square. E, F, L, C, G, S, U, B, D, P, R all turn and are
    rounded; H, T, X cross and are square.
"""

from glyphsLib.types import Point
from geom import (node, path, rect, clone_all, translate, mirror_x, mirror_y,
                  area, LINE, OFFCURVE, KAPPA,
                  reverse, arc_to, corner_radius, inner_radius, bbox, squash,
                  squash_x, piecewise_y, scale_x, fit, slant, taper,
                  cut_at_y, cut_along, meets_line, seg_at,
                  _segments, _split_seg, _map_points)
from latin_metrics import Latin
from params import Lower, _flatten
from probe import runs, vruns
from be_donor import BE as BE_DONOR, BE_IT as BE_DONOR_IT
from ge_donor import GE as GE_DONOR
from de_donor import DE as DE_DONOR

# Multiple of the face's own corner radius, for the letters whose arm is too
# short to carry the whole thing.
#
# E, F and L are the only Latin glyphs here with a vertical swept into a
# horizontal, and all three draw that corner at 103 outer / 78 inner at Thin
# and 122 / 20 at ExtraBold. But all three also turn it into an arm of much
# the same length -- 355 to 400 units at Thin, around 460 at ExtraBold -- so
# the corner takes 0.26 to 0.29 of the arm in every case. With one arm length
# in evidence there is no way to tell a constant radius from a constant share,
# and the face never poses the short-arm case at all.
#
# A bend is bounded by the SHORTER of the two strokes it joins, and where that
# stroke is short the full corner swallows it. Ъ's shoulder reaches only 0.20
# of the cell, so the face's radius ate 0.69 of it at Thin. Ґ's tick stands
# 175 units against an arm of 398, and took 0.59. П and Ш put two corners on
# one bar, which is the same problem from the other side. Reduced, all of them
# take 0.24 to 0.38 -- bracketing what the face does rather than overshooting.
#
# Ч and Г keep the full radius: Ч's cup turns into a 386-unit underside, which
# is E's own arm length, and Г's corner IS E's nodes.
# This factor is the one figure not read off a glyph.
RADIUS = 0.55
def diag(xa, ya, xb, yb, h):
    """Stroke between two CENTRELINE points, ends cut horizontally, width h.

    Matches how K and Y are drawn: the horizontal cut is what keeps a diagonal
    the same visual weight as a vertical stem. Forced counter-clockwise -- the
    orientation flips with the direction of travel, and a clockwise contour is
    a hole under nonzero fill rather than ink.
    """
    p = path([node(xa - h / 2.0, ya), node(xb - h / 2.0, yb),
              node(xb + h / 2.0, yb), node(xa + h / 2.0, ya)])
    return p if area(p) > 0 else reverse(p)


def diag_unit(pr):
    """K's diagonal thickness, rescaled to the stem this pass is using, so a
    lowercase pass does not inherit the capital's diagonal weight."""
    base = getattr(pr, "_pr", pr)
    k = base.paths("K")[0]
    top = max(n.position.y for n in k.nodes)
    xs = [n.position.x for n in k.nodes if n.position.y == top]
    return (max(xs) - min(xs)) * (pr.stem / float(base.stem))


MIN_SB = 0.055          # tightest sidebearing a widened letter may take
YERU_SPLIT = 2.2        # Ы: bowl counter, as a multiple of the gap to its stem
YERU_INK = 0.72         # Ы: share of its own width that may be ink
BOWL_COUNTER_TOP = 0.47 # Ь Ъ Б Ы: height of the bowl COUNTER, in cap heights
# Ь Ъ Б all hang the same bowl off a stem, and so does the face's own B, which
# is what В is -- В is the Latin B, unchanged. So the bowl is not a fraction of
# the advance to pick: it reaches exactly as far as B's does, and starts where
# B's stem starts. Both are read per master from L(pr).bowlLeft/.bowlRight.
#
# As a fixed 0.93 of the advance the bowl matched В at ExtraBold and missed it
# everywhere else: B's own bowl narrows to 0.863 of the cell at Thin while a
# constant stays at 0.930, so Ь came out 4.3% wider than В at Regular where
# every drawn face measured holds the two within 2.6%, at a median of 1.000.
# Ь's stem sat 19 units left of В's for the same reason -- it was taking the
# face's general capital extent rather than B's own.
HARD_SHOULDER = 0.20    # Ъ: shoulder length, as a fraction of the advance

# Ъ's LEFT edge, as a share of the advance, and it falls with the weight.
# The shoulder's length is a share of the cell and does not move, so wherever
# this edge sits is where the stem sits, and whatever is left over is the
# bowl's. Held flat at 0.055 the bowl lost width as the wall grew, and by
# ExtraBold Ъ's counter was HALF Ь's -- 0.50 against a panel that holds
# 0.78 to 0.79 at every weight, and outside the panel at Bold and ExtraBold
# in both cases. The panel moves the edge instead: 0.035 of the advance at
# Thin down to 0.013 at ExtraBold for the capital.
#
# Going that far left is this face's own habit, not the panel's alone -- Y
# already starts at 18 units at Thin and at -1 at ExtraBold, and the
# lowercase w at 32 and 20, which is where these lines put ъ.
HARD_LEFT = {"cap": (0.0398, -0.167), "lc": (0.0603, -0.182)}
# Д Ц Щ Џ all hang below the baseline, and every drawn face gives them ONE
# depth -- JetBrains, DejaVu, Consolas, Fira and Segoe each use a single figure
# for all three of Д Ц Щ. Measured against each face's OWN p, it lands
# between 0.69 and 0.82 of the descender. This file had two separate guesses,
# 0.55 of the descender for Д and 0.19 of the cap for the rest, so Д hung
# shallower than Ц beside it.
CAP_DESCENT = 0.75      # of the face's own descender depth
# Ч: the least white the cup may keep, in cap heights. Borrowed, and marked as
# such -- no Latin capital has a cup, so the face genuinely cannot answer it.
# Across sixty drawn designs the cup's counter runs 0.42 to 0.755 of cap, and
# the two tightest, Consolas at 0.455 and JetBrains at 0.470, sit just under
# this. Everything else about Ч comes from SUSE's own Y and L.
CHE_COUNTER = 0.48
# ф's width at x-height, over the advance -- and it is NOT a constant.
#
# It was one: the panel's median, 0.863, taken across all 51 faces at once.
# That median hid a relation. Bucketed by the face's own stroke weight the
# panel reads 0.832 at light, 0.842 at medium, 0.871 at bold and 0.938 at
# extra bold: as the strokes thicken, faces WIDEN the bowl so the counters
# survive. Held flat at 0.863 this face was too wide at Thin and below the
# entire panel range at ExtraBold, where the ink had nowhere to go but into
# the counters -- which is exactly how it read, a fat bar between two slits.
#
# A least-squares fit over the 60 panel faces, ф's width against the face's
# own stem, both over the em, with a residual sd of 0.045. Linear in the
# stem, so interpolation between the two masters reproduces it exactly at
# Regular and Bold instead of drifting off it.
#
# Everything else about ф was already right: its walls and middle stem
# thin from 0.97 to 0.78 of the stem across the axis where the panel does
# 0.99 to 0.85, and weight-matched its counters sit inside the panel. Only
# the width was frozen.
# Three of them, per case, and every one is a straight line in the face's own
# stem rather than a number. The panel thins a Ф or ф from the inside as the
# strokes grow: over the em-normalised stem its bowl wall runs 1.03 down to
# 0.86 and its middle stem 1.00 down to 0.78, while its width goes the other
# way, 0.87 up to 0.95, so the counters have somewhere to be. Fitted by least
# squares over the 60 panel faces; linear in the stem, so interpolation
# between the two masters reproduces them at Regular and Bold rather than
# drifting off them.
#
# The capital was exempt from all three, on the reasoning that it is the
# widest letter the face allows and so has room to spare. It has not: at
# ExtraBold it stood at 1.005 of its own advance with negative sidebearings,
# wall and stem still at full weight, and its counters down to 0.35 of the
# stem against a panel 0.42-0.61 -- the stem nearly three times the counter it
# sat between. There is no room left to buy once the letter is past the cell
# edge; the ink goes into the counters instead.
# ф's bowl, over the height the face's own о is drawn at -- see Ef.
EF_BOWL_TALLER = 1.05

# Ф's wall: the line's heavy end is the panel's ratio among faces whose stem is
# as heavy as this one's -- 0.83 of the stem across the twelve drawing it at a
# quarter of the advance or more. Fitted across all weights the line asked
# 0.87 there, and at this face's heavy stem those units came out of the
# counter: Ф's stood at 0.128 of the advance against their 0.143. The light
# end is unchanged, capped at the stem.
EF_FIT = {
    "cap": {"width": (0.8444, 0.6314),
            "wall": (1.1431, -1.9323),
            "mid": (1.1072, -1.7645)},
    "lc": {"width": (0.7892, 0.7754),
           "wall": (1.1279, -1.7705),
           "mid": (1.0777, -1.7156)},
}


def ef_fit(pr, key):
    a, b = EF_FIT["lc" if getattr(pr, "lower", False) else "cap"][key]
    v = a + b * (pr.stem / 1000.0)
    # The panel's lightest face draws its stem at about 0.05 of the em; this
    # one draws Thin at 0.029, off the bottom of the data the lines were
    # fitted to. Extrapolated down there they ask for a bowl wall heavier than
    # the stem it crosses -- 1.03 against a panel maximum of 1.02, which the
    # stroke gate refused, and rightly. An interior stroke is never heavier
    # than the stem; at the light end the two are simply equal.
    return min(v, 1.0) if key in ("wall", "mid") else v


def ef_edge(pr, draw):
    """The sidebearing to DRAW so Ф stands at its target width once sheared.

    Upright the two are the same number and this returns it unchanged. Under
    the italic they are not, and not in the direction the shear suggests: a
    box drawn upright and leaned over comes out WIDER, but this bowl is not
    drawn upright. It is this face's own italic O un-sheared -- which leans
    the other way -- fitted to the box and leaned back, so the fit is paid for
    twice and the letter arrives narrow. Ф is meant to be the widest letter in
    the set and the panel draws it at 0.99 to 1.36 of its own O; ours stood at
    0.920 of it at Thin Italic and 0.889 at ExtraBold Italic, under the floor,
    where the upright holds 1.131 and 1.050. ф was the same, 1.005 and 0.996
    against its own o where the upright holds 1.205 and 1.040.

    `draw` is the letter itself as a function of the sidebearing, because the
    two cases build different letters and it is the finished INK that has to
    measure right -- the stem crosses the bowl and can reach past it.

    Bisected rather than solved, which is F17's own instruction: under a shear
    the extremes change hands as the box scales, so a closed form would have
    to know which points win at which width.
    """
    want = ef_fit(pr, "width") * 600.0
    edge = (600.0 - want) / 2.0
    if not pr.italic:
        return edge

    def ink(e):
        xs = [x for q in slant(draw(e), pr.italic, pr.pivot)
              for x, _ in _flatten(q, 24)]
        return max(xs) - min(xs)

    lo, hi = edge - 260.0, edge
    for _ in range(22):
        mid = (lo + hi) / 2.0
        if ink(mid) < want:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def ef_crowd(pr, ink):
    """The bowl's wall as a share of what the round letter draws it at.

    Derived from the stem in both styles, over the round letter's INK side.
    The italic once took a separate share (`EF_BOWL_SHARE`), because its O
    read twelve per cent heavier than the upright's for the same stem -- 184
    against 164 at ExtraBold. That was the un-sheared O's handles, not its
    ink (F17): read off the ink the two sides are the same 164.
    """
    return ef_fit(pr, "wall") * pr.stem / ink["tx"]
# ...and its total height over the x-height, the panel's median across the same
# 51 faces.
EF_HEIGHT = 1.781
# ю: the clear run between its stem and its bowl, over the advance. The panel's
# lower quartile rather than its median -- at ExtraBold this face's stem is 150
# units of a 600 cell, and every unit given to the gap comes off the bowl.
YU_GAP = 0.129
# ...and the least it gives way to at the heavy end: the lower quartile of the
# heavy faces whose stem is as heavy as this one's (a fifth of the advance).
# Read, like theirs, a quarter up the letter, where the bowl has already
# curved away from the stem -- set at the bowl's extreme instead, it left Ю's
# gap reading 0.106 and took the counter's room out of the walls.
YU_GAP_MIN = 0.078
YU_GAP_ROW = 0.25
# The bowl's counter, as a share of the face's own o / O counter width: the
# median of those same faces, ю 0.476 and Ю 0.448. With m's three-stem gap as
# the only floor, ю closed to 0.35 of o and Ю to 0.32 of O at ExtraBold -- the
# narrowest of every heavy face measured. Their walls match ours; they spend
# the gap on the counter instead.
YU_COUNTER = {"lc": 0.476, "cap": 0.448}
# The least the bowl's roof and floor weigh, over the case's bar: the lightest
# horizontal the face draws in that case -- t's bar itself, and B's 0.90-0.96
# of H's. Floored at H's full bar, Ю's roof matched its walls at ExtraBold and
# the italic's shear knotted the turn (1.09 against O's 1.01). Ф's capital
# takes it too: with its heavy wall thinned, its roof read 0.90 at Regular.
BOWL_ROOF = {"lc": 1.00, "cap": 0.90}
# Ф: how far the stem projects past the bowl, in cap heights. Borrowed for the
# same reason -- see Ef.
#
# It was 0.10, which is where every drawn face on this machine clusters when
# you ask the question that way round. But this figure also sets the bowl's
# HEIGHT, which is cap minus twice the overhang, and read from that side 0.10
# was too generous: the bowl came out at the very bottom of the panel's height
# range at all four weights while the projection sat at the top, and the bowl
# ended up wider than it was tall -- 1.07 against a panel that stops at 1.00.
# Too much stem showing and not enough bowl. At 0.07 the bowl grows 7.5%, the
# aspect lands at 0.995 and the projection still measures inside the panel.
EF_OVERHANG = 0.07

_METRICS = {}


def L(pr):
    base = getattr(pr, "_pr", pr)
    k = (id(base.font), base.mi)
    if k not in _METRICS:
        _METRICS[k] = Latin(base)
    return _METRICS[k]


def fit_stems(pr, count, advance=600.0):
    """Place `count` stems in the cell: returns (left, right, stem).

    Widen into the sidebearings first, and only shave stem weight with
    whatever is still missing -- the order m uses against n.
    """
    # The counter is the face's own, measured off m -- the letter that already
    # answers "how much air do three stems in a row need". A flat 0.32 of the
    # stem, which is what this used, is far tighter than anything the face or
    # any reference does at the heavy end: it left Ш's counters at 0.29 of a
    # stem where four drawn faces run 0.47 to 0.73, and made Ш the one letter
    # in the set carrying more ink than the consensus.
    c = L(pr).counter3 / float(pr.stem)
    nominal = pr.capR - pr.capL
    widest = advance - 2 * round(MIN_SB * advance)
    required = count * pr.stem + (count - 1) * c * pr.stem
    span = min(widest, max(nominal, required))
    stem = pr.stem
    if required > span:
        stem = span / (count + (count - 1) * c)
    mid = (pr.capL + pr.capR) / 2.0
    return mid - span / 2.0, mid + span / 2.0, stem


# ---------------------------------------------------------------------------
# shared shapes
# ---------------------------------------------------------------------------

def comb(pr, x0, x1, n, s, top, bar, r, tail_w=0.0, tail_d=0.0,
         tail_right=None):
    """`n` stems standing on a bar, as ONE contour, with an optional tail.

    Ш Щ Ц П are all this shape. The tail is traced into the same outline
    rather than laid over it as a second rectangle: two overlapping shapes
    meet at little re-entrant corners along the seam, visible at every weight.

    The inner radius is clamped to the bar, or the corner arc cuts through the
    bar it is meant to turn into and thins it under the middle stem.
    """
    # Never zero: at ExtraBold the stem is wider than the corner radius, so
    # r - s goes negative and the arc branch would vanish, leaving 14 nodes
    # against Thin's 20 and an outline that tears apart between the masters.
    # The floor is 4 units, not 1 -- at 1 the arc's control point lands on top
    # of its own node and nicks the outline. 4 still reads as a square corner.
    ri = max(min(r - s, bar), 4.0)
    xs = ([x0] if n == 1 else
          [x0 + i * (x1 - x0 - s) / (n - 1.0) for i in range(n)])

    ns = [node(x0, top), node(x0, r)]
    ns += arc_to(x0, r, x0 + r, 0.0, x0, 0.0)
    if tail_w:
        # the tail juts PAST the right stem rather than continuing it; the
        # overhang is what stops it reading as the stem failing to stop
        # The bar runs out to the tail's right edge and the tail hangs off
        # that overhang. Stopping the bar at the last stem left the tail
        # jutting past the letter as a detached block -- JetBrains runs its Ц
        # bar 94-565 with the tail at 485-565, flush.
        xt = tail_right - tail_w
        # The leg is the bar TURNING DOWN, and this face turns corners the way
        # L does: a generous radius on the outside, a tighter one on the
        # inside. Left square on the outside it reads as a rectangle stuck to
        # the bar -- which is fine in a squared face like JetBrains, and wrong
        # in this one.
        # ...and no wider than the overhang it turns inside. The bar's top
        # edge runs back from this corner to x1, so a radius past that reverses
        # the outline and leaves a zero-degree spike. At the reduced radius the
        # bound is never reached, which is why it was missing; at the face's
        # full corner Ц and Щ both spiked at ExtraBold.
        ro = min(r, tail_w * 0.85, (bar + tail_d) * 0.45,
                 tail_right - x1 - 4.0)
        ns += [node(xt - ri, 0.0)]
        ns += arc_to(xt - ri, 0.0, xt, -ri, xt, 0.0)
        ns += [node(xt, -tail_d), node(tail_right, -tail_d),
               node(tail_right, bar - ro)]
        ns += arc_to(tail_right, bar - ro, tail_right - ro, bar,
                     tail_right, bar)
        ns += [node(x1, bar)]
    else:
        ns += [node(x1 - r, 0.0)]
        ns += arc_to(x1 - r, 0.0, x1, r, x1, 0.0)
    ns += [node(x1, top)]

    for i in range(n - 1, 0, -1):
        li, prev = xs[i], xs[i - 1] + s
        ns += [node(li, top), node(li, bar + ri)]
        ns += arc_to(li, bar + ri, li - ri, bar, li, bar)
        ns += [node(prev + ri, bar)]
        ns += arc_to(prev + ri, bar, prev, bar + ri, prev, bar)
        # the next iteration opens on xs[i-1] at the top, so emitting it here
        # too leaves two nodes on the same point -- a nick between the notch
        # and the stem beside it
        ns += [node(prev, top)]

    p = path(ns)
    return [p if area(p) > 0 else reverse(p)]


def _tailed_body(pr, n, over):
    """Body extents and stem for a tailed letter with `n` stems."""
    x0, x1, s = fit_stems(pr, n)
    x1 = min(x1, 592.0 - over)
    span = x1 - x0
    # The face's own counter, off m -- the same figure fit_stems uses. This
    # line carried the flat 0.32 that fit_stems was fixed for and kept, which
    # is the Ь-and-Ъ pattern again: a constant discredited in one place and
    # left running in another. It bit only Щ at ExtraBold and only by a third
    # of a unit, so nothing would ever have shown it.
    c = L(pr).counter3 / float(pr.stem)
    if span / (n + (n - 1) * c) < s:
        s = max(0.80 * pr.stem, min(pr.stem, span / (n + (n - 1) * c)))
    return x0, x1, s


def tailed_layout(pr, n):
    """Body extents and leg for Ц Щ Џ.

    Ц and Щ get ONE leg -- same width, same depth, same overhang, same
    position -- because they are the same letter with an extra stem. That
    means sizing it off the NARROWER of the two: Щ's stems shrink to fit three
    of them, so a leg cut to Ц's stem would outweigh Щ's, and a leg cut to
    each letter's own stem comes out visibly wider on Ц. Wider at the same
    depth reads as shorter, which is why the two legs looked mismatched.

    The overhang is JetBrains' measured 75 units, which also leaves Щ enough
    width to hold its stems at the same -17% this face applies to its own m
    against n.
    """
    # Constant across the weight axis, but scaled to THIS face's cap height.
    # Every reference overhangs the last stem by about this much and holds it
    # from Thin to ExtraBold: JetBrains 77/76/76/75/75/75, Consolas 58,
    # Iosevka 56, Fira 63. Capping it against the stem so the leg would always
    # overlap dragged it to 46 at Regular -- the smallest of any of them --
    # which is why the leg sat against the body instead of standing clear.
    #
    # JetBrains' 75 is measured on a 730-unit cap; this face's is 700, so the
    # figure is carried across as a proportion rather than as raw units.
    # Mixing absolute and relative transplants was the inconsistency.
    over = 75.0 * pr.cap / 730.0

    # At the light weights this leaves the leg hanging free of the stem, on
    # the bar alone -- deliberate, and what JetBrains does too: at Thin its
    # leg starts 27 units PAST the stem's right edge.
    x0, x1, s = _tailed_body(pr, n, over)
    _, _, s3 = _tailed_body(pr, 3, over)
    return (x0, x1, s, 0.92 * min(s, s3), descent(pr), x1 + over)


def descent(pr):
    """How far below the baseline a tailed letter reaches -- Д Ц Щ Џ and
    their lowercase alike.

    ONE depth for both cases, and it is the capitals' 0.75 of the face's own
    descender. The lowercase does NOT go deeper, though its body is a third
    shorter.

    This started out case-split, on the reasoning that p q y g j all reach
    -200 so ц щ д should stand with them. That is a bad inference: p's
    descender is the stem carrying on down, a different feature from a tail
    hung off the baseline, and the Latin has no lowercase tail to read at all.
    So the panel has to answer, and across 60 faces it is emphatic -- ц's tail
    runs 0.94 of its own Ц's, ranging 0.69 to 1.16, and the single commonest
    value is exactly 1.000, drawn by 26 of them. A full descender put ц at
    1.333 of Ц, outside what any of the sixty does, and the tails read far too
    long against the capitals.

    Measured against each face's own p, the two cases land in the same place
    -- 0.756 for the capital and 0.737 for the lowercase -- which is what one
    depth for both means, and which is why CAP_DESCENT needs no lowercase
    twin.
    """
    return L(pr).descDepth * CAP_DESCENT


def round_of(pr, upper="O"):
    """The face's own round letter for the case in hand: O and C above, o and
    c below.

    Same rule as bowl_of, and for the reason Э proved: a cloned or refitted
    outline does not re-size through Lower. Run at x-height with the capital
    still named, Э came out a full cap-height letter standing in a lowercase
    word, and nothing but the height rule noticed.
    """
    return upper.lower() if getattr(pr, "lower", False) else upper


def bowl_stroke(pr, donor=None):
    """O's own side stroke, per master.

    O is monolinear at Thin (29 all round) but modulated at ExtraBold -- 164
    at the sides against 136 top and bottom. Insetting its counter uniformly
    throws that away and leaves Ф and Ю visibly lighter than O beside them.
    """
    donor = round_of(pr) if donor is None else donor
    o, c = pr.paths(donor)[0], pr.paths(donor)[1]
    ox = min(n.position.x for n in o.nodes)
    cx = min(n.position.x for n in c.nodes)
    oy = min(n.position.y for n in o.nodes)
    cy = min(n.position.y for n in c.nodes)
    return cx - ox, cy - oy


def bowl(pr, x0, x1, y0, y1, donor=None, crowd=1.0):
    """O's curve refitted to a box, at O's stroke weight times `crowd`.

    Ф and Ю carry a stem through the bowl, so a scanline crosses three
    strokes where O has two. At O's full weight their counters close to slits
    at ExtraBold. `crowd` is the face's own answer to a third stroke, read off
    m against n -- x0.97 at Thin, x0.83 at ExtraBold -- so the letters give up
    exactly as much stroke as the typeface itself gives up, and no more.
    """
    donor = round_of(pr) if donor is None else donor
    outer, counter = pr.paths(donor)[0], pr.paths(donor)[1]
    tx, ty = bowl_stroke(pr, donor)
    tx, ty = tx * crowd, ty * crowd
    return (fit([outer], x0, y0, x1, y1)
            + fit([counter], x0 + tx, y0 + ty, x1 - tx, y1 - ty))


# ---------------------------------------------------------------------------
# T2 capitals
# ---------------------------------------------------------------------------

def Ghe(pr, top=None, bottom=0.0):
    """Г -- E's spine and upper arm, cut flat at the baseline.

    E's contour runs inner-spine up, round the inner corner, out under the
    arm, up its end, back along the top, round the outer corner, down the
    outer spine. Nodes 6..15 are exactly that, so Г reuses the face's own
    corner instead of reproducing it.
    """
    top = pr.cap if top is None else top
    e = pr.paths("E")[0]
    ns = list(e.nodes)
    inner, outer = ns[6].position.x, ns[15].position.x
    seg = [node(n.position.x, n.position.y, n.type, n.smooth) for n in ns[6:16]]
    seg[0].type, seg[0].smooth = "line", False
    return [path([node(inner, bottom)] + seg + [node(outer, bottom)])]


# Ґ's tick, reviewed and accepted long before this session. Both its rise and
# its inner radius were changed here without being asked -- the radius to
# inner_radius, the rise to a stem-derived formula -- and both are reverted.
# ґ takes the same two figures so the cases agree.
#
# The panel would put the rise higher and the radius rounder, and that is not
# a reason: an approved letter is evidence about this face, and a median
# across sixty others is not evidence against it.
TICK_RISE = 0.21


def Ghe_upturn(pr):
    """Ґ -- Г with a tick turning up at the end of the arm.

    Both Consolas and Iosevka rise about 0.21 of cap height above the arm and
    overshoot the ascender doing it; that is the convention, not a liberty.

    ONE contour, spliced into Г's own. As a separate tick laid over the arm it
    could not be made to work, because the arm ends square at exactly the
    tick's right edge: below the cap line the arm filled the rounded outer
    corner straight back in, and above the cap line that same corner bit a
    notch out of the tick, which is the wedge of white this letter showed. The
    turn has to REPLACE the arm's terminal rather than sit on top of it.

    The tick TURNS up off the arm, so both sides of the bend are rounded --
    outside and inside, which is L's foot stood on end. Only the tick's top
    stays flat: that is a terminal, and terminals here are cut square.

    A bend is bounded by the SHORTER of the two strokes it joins, and here
    that is the tick, not the arm: it stands 175 units tall at Thin against an
    arm of 398. At the face's own radius the corner took 0.59 of it, where E
    and F give theirs 0.26. So the tick takes the reduced corner, for the same
    reason Ъ's short shoulder does -- see RADIUS.
    """
    top, bottom = pr.cap, 0.0
    e = pr.paths("E")[0]
    ns = list(e.nodes)
    inner, outer = ns[6].position.x, ns[15].position.x
    seg = [node(n.position.x, n.position.y, n.type, n.smooth) for n in ns[6:16]]
    seg[0].type, seg[0].smooth = "line", False

    # seg[4] and seg[5] are the arm's flat right end -- the two nodes the turn
    # stands in for. Everything on either side of them is the face's own E.
    arm_end, y = seg[4].position.x, seg[4].position.y
    rise = round(TICK_RISE * top)
    x0 = arm_end - pr.stem
    ro = corner_radius(pr) * RADIUS
    ri = max(min(ro - pr.stem, pr.bar), 4.0)

    turn = [node(arm_end - ro, y)]
    turn += arc_to(arm_end - ro, y, arm_end, y + ro, arm_end, y)
    turn += [node(arm_end, top + rise), node(x0, top + rise),
             node(x0, top + ri)]
    turn += arc_to(x0, top + ri, x0 - ri, top, x0, top)

    p_ = path([node(inner, bottom)] + seg[:4] + turn + seg[6:]
              + [node(outer, bottom)])
    return [p_ if area(p_) > 0 else reverse(p_)]


def Pe(pr, top=None, bottom=0.0):
    """П -- two stems under a bar."""
    top = pr.cap if top is None else top
    x0, x1, s = fit_stems(pr, 2)
    return mirror_y(comb(pr, x0, x1, 2, s, top, pr.bar,
                         corner_radius(pr) * RADIUS), top / 2.0)


# г's bar is shorter than Г's, and by a share that has to hold across the
# axis. The panel puts (г arm / Г arm), normalised by each face's own
# lowercase-to-capital width, at a median 0.895 across 60 faces and keeps it
# roughly flat with weight. This face's climbed instead -- 0.872 at Thin,
# 0.933 at Regular, 0.995 at Bold, 1.017 at ExtraBold -- because г took the
# lowercase sidebearings whole while Г took E's own, and the two converge as
# the strokes thicken. At ExtraBold both arms measured 461 and г's left
# sidebearing was actually TIGHTER than Г's, so the lowercase bar had stopped
# being the shorter of the two altogether.
#
# A ceiling, not an assignment: where the face already draws the arm shorter
# than the panel's share it keeps its own value, which leaves Thin and
# Regular untouched at 367 and 384 and pulls only Bold and ExtraBold back.
# The face is the authority on what it already does well; the panel is only
# the authority on the relation.
ARM_SHARE = 0.895


def lc_arm_end(pr, x0, x1):
    if not getattr(pr, "lower", False):
        return x1
    xs = [n.position.x for p in pr.paths("E") for n in p.nodes]
    cap_arm = max(xs) - min(xs)
    return x0 + min(x1 - x0, ARM_SHARE * cap_arm * L(pr).lcCapWidth)


def Ghe_lc(pr, top=None):
    """г -- one stem under a bar, with the face's own corner.

    The capital splices E's actual nodes, which is the better answer whenever
    there is an E to splice. There is no lowercase e with an arm, so this
    rebuilds the same corner out of the radii the face uses.

    Both radii are the FULL ones, and both were wrong first time round.

    The outer took П's reduction, which halved it -- г's corner measured 0.49
    of Г's own at every master, so the same letter turned twice as tightly at
    x-height as at cap height. The reduction is for a bend whose shorter
    stroke cannot carry the whole corner: П and Ш put two corners on one bar,
    Ъ's shoulder reaches a fifth of the cell, Ґ's tick stands 175 units. г's
    arm is the full width of the letter and carries one corner, which is why
    Г keeps the full radius -- and г is the same letter. At 122 into a 461
    arm it takes 0.26 of it, exactly what E and F give theirs.

    The inner came from `ro - s`, which goes to -28 at ExtraBold and floored
    at 4, squaring off a corner the face holds at 20. That is the whole
    reason inner_radius exists; see its docstring.

    Nothing here needs scaling for the case. This face's turn is the same 103
    and 78 at Thin whether it is drawing E, F, L, t or f, and at ExtraBold the
    lowercase turns WIDER than the capital, not tighter -- 168 in t and f
    against 122 in E, F and L. So the capital's own radius is the floor for a
    lowercase corner, never the ceiling, and half of it is nowhere.
    """
    top = pr.cap if top is None else top
    x0, x1, s, b = pr.capL, pr.capR, pr.stem, pr.bar
    x1 = lc_arm_end(pr, x0, x1)
    ro = corner_radius(pr)
    ri = inner_radius(pr)
    ns = [node(x0, 0.0), node(x0, top - ro)]
    ns += arc_to(x0, top - ro, x0 + ro, top, x0, top)
    ns += [node(x1, top), node(x1, top - b), node(x0 + s + ri, top - b)]
    ns += arc_to(x0 + s + ri, top - b, x0 + s, top - b - ri, x0 + s, top - b)
    ns += [node(x0 + s, 0.0)]
    p = path(ns)
    return [p if area(p) > 0 else reverse(p)]


def Ghe_upturn_lc(pr, top=None):
    """ґ -- г with a tick turning up at the end of its arm.

    Ґ splices E's own nodes; there is no lowercase e with an arm, so this
    rebuilds the same shape from the radii the face uses, exactly as Ghe_lc
    does for г. The tick's proportions are Ґ's: it rises 0.21 of the letter
    above the arm, which is the convention Consolas and Iosevka both hold and
    which the panel puts at a median 0.213 across the 37 faces that draw the
    letter.

    Both bends take the reduced corner, as Ґ's does: a bend is bounded by the
    SHORTER of the strokes it joins, and here that is the tick.
    """
    top = pr.cap if top is None else top
    x0, x1, s, b = pr.capL, pr.capR, pr.stem, pr.bar
    # the tick rides the arm's right end, so it moves with it
    x1 = lc_arm_end(pr, x0, x1)
    ro = corner_radius(pr)
    # Two different inner radii, as Ґ has. The stem-into-arm corner is the
    # face's own, which the capital gets from E's spliced nodes -- 78 and 20.
    # The tick's own bend is the shorter, derived figure the capital uses
    # there, 28 and 4.
    ri = inner_radius(pr)
    rk = max(min(corner_radius(pr) * RADIUS - s, b), 4.0)
    # The face's own inner radius, read off L. Derived as `ro - s` it goes
    # negative once the stroke outgrows the corner and floors at 4, squaring
    # off the tick's bend at ExtraBold where this face turns at 20 -- the
    # rounded turn IS the signature, and this is the third time that same
    # subtraction has thrown it away, after г's corner and в's counter.
    # The tick rises further at x-height than at cap height, and the panel is
    # clear about both: 0.213 of the cap above Г across the 37 faces that draw
    # Ґ, but 0.280 of the x-height above г across 51 that draw ґ. A shorter
    # letter needs proportionally more tick to stay legible. Carrying the
    # capital's 0.21 down left ґ at 0.66 of the panel's ink median against a
    # range that bottoms out at 0.65.
    # ґ's own rise, not the capital's. The panel is clear about both: 0.213 of
    # the cap above Г across the 37 faces that draw Ґ, but 0.280 of the
    # x-height above г across the 51 that draw ґ -- a shorter letter needs
    # proportionally more tick to stay legible. Carrying the capital's 0.21
    # down here is what made the notch read thick, because the tick's width is
    # the stem either way.
    rise = round(0.28 * top)
    # The tick's RIGHT edge is the arm's own right end, carried on upward; its
    # LEFT edge comes down only as far as the arm's top surface. Run the left
    # edge down to the arm's UNDERSIDE instead and the outline crosses itself
    # where it meets the arm's top -- at (381, 493) at ExtraBold -- and the
    # tip comes away from the letter. Same topology the capital splices out
    # of E.
    # FOUR turns, the same four Ґ has, and it had three. The arm ran straight
    # up into the tick with no rounding at all, leaving a square notch at the
    # one junction the eye goes to. And the top-left took the reduced corner
    # where Г and г both take the full one.
    rt = corner_radius(pr) * RADIUS
    ns = [node(x0 + s, 0.0), node(x0 + s, top - b - ri)]
    ns += arc_to(x0 + s, top - b - ri, x0 + s + ri, top - b, x0 + s, top - b)
    ns += [node(x1 - rt, top - b)]
    ns += arc_to(x1 - rt, top - b, x1, top - b + rt, x1, top - b)
    ns += [node(x1, top + rise),
           node(x1 - s, top + rise), node(x1 - s, top + rk)]
    ns += arc_to(x1 - s, top + rk, x1 - s - rk, top, x1 - s, top)
    ns += [node(x0 + ro, top)]
    ns += arc_to(x0 + ro, top, x0, top - ro, x0, top)
    ns += [node(x0, 0.0)]
    p_ = path(ns)
    return [p_ if area(p_) > 0 else reverse(p_)]
def En_lc(pr, top=None):
    """н -- two stems joined at the waist.

    Н above is the Latin H unchanged, so H is what this follows: three
    rectangles, the bar inset into both stems by 0.41 of a stem at Thin and
    0.49 at ExtraBold rather than butted against their edges, and its centre
    on 0.515 of the height. Both are read off H and carried as ratios; e's
    own middle bar puts itself at the same height at x-height.
    """
    top = pr.cap if top is None else top
    x0, x1, s = fit_stems(pr, 2)
    y = pr.barCentre * top - pr.bar / 2.0
    return [rect(x0, 0.0, x0 + s, top), rect(x1 - s, 0.0, x1, top),
            rect(x0 + s - pr.barOverlap, y,
                 x1 - s + pr.barOverlap, y + pr.bar)]


def Te_lc(pr, top=None):
    """т -- a bar with a stem hung from its middle.

    Two rectangles, as T is drawn here, and the stem runs up INTO the bar
    rather than stopping under it -- T's own stem overlaps by the same inset
    H's crossbar takes. The bar reaches wider than the stems' sidebearings,
    which is the face's habit too: T's runs 57..543 where H stands 93..508,
    and t's crossbar runs 46..514 where n stands 117..484. That crossbar is
    this bar, measured rather than proportioned across from the capital.
    """
    top = pr.cap if top is None else top
    s = pr.stem
    # Only the crossbar's WIDTH transfers, never its position: t is not a
    # symmetric letter, and its crossbar sits at 46..514 -- centred on 280,
    # not 300. Taken as-is that put т's stem twenty units left of the middle
    # of a monospaced cell, which is visible at any size. T's own bar centres
    # on exactly 300 at both masters, and т is that same symmetric letter.
    w = (pr.lcBarR - pr.lcBarL) / 2.0
    return [rect(300.0 - s / 2.0, 0.0,
                 300.0 + s / 2.0, top - pr.bar + pr.barOverlap),
            rect(300.0 - w, top - pr.bar, 300.0 + w, top)]


def Sha(pr, top=None, tail=False):
    """Ш / Щ -- three stems on a bar."""
    top = pr.cap if top is None else top
    if tail:
        x0, x1, s, tw, td, tr = tailed_layout(pr, 3)
    else:
        x0, x1, s = fit_stems(pr, 3)
        tw = td = 0.0
        tr = None
    return comb(pr, x0, x1, 3, s, top, pr.bar,
                corner_radius(pr) * RADIUS, tw, td, tr)


def Shcha(pr, **kw):
    return Sha(pr, tail=True, **kw)


def Tse(pr, top=None, centre_tail=False):
    """Ц -- two stems on a bar with a tail; Џ is the same with the tail
    brought to the middle."""
    top = pr.cap if top is None else top
    x0, x1, s, tw, td, tr = tailed_layout(pr, 2)
    if centre_tail:
        mid = (x0 + x1) / 2.0
        body = comb(pr, x0, x1, 2, s, top, pr.bar,
                    corner_radius(pr) * RADIUS)
        return body + [rect(mid - tw / 2.0, -td, mid + tw / 2.0, pr.bar)]
    return comb(pr, x0, x1, 2, s, top, pr.bar,
                corner_radius(pr) * RADIUS, tw, td, tr)


def Dzhe(pr):
    return Tse(pr, centre_tail=True)


# How far Л's leg is pushed out of П's span, and how far Д narrows its body.
#
# Л stays at 0: the splay is spent INSIDE П's span and the letter is exactly
# its neighbours' width. That was tried before and rejected as "a leaning П",
# but the flatness was the lean, not the width -- see LEG_LEAN, which was
# discarding nearly half the face's own splay. With the diagonal restored the
# letter reads as an Л at П's width, and any outward slide is width on top of
# a slant that already fills the cell.
#
# Which matters because a sloped leg is optically wider than a vertical stem:
# the bbox says 1.000 while the eye sees more of the cell filled than п or н
# fill. Every width figure sat on the panel's median while the letter still
# looked too wide beside its neighbours, because bbox width is not what the
# reader is comparing. Both cases stay inside the panel's range for Л/П and
# л/п -- 0.993 to 1.254 and 0.881 to 1.230 -- at its narrow end, deliberately.
#
# Д cannot follow it. Its body is already 0.80 of the advance against a panel
# median of 0.614, and every step outward pushes the body further over the
# plinth until the legs disappear beneath it -- which is the fault this was
# opened to fix. Д keeps the slant inside its span and narrows the body
# instead, which is what gives the plinth something to jut past.
EL_OUTWARD = 0.0
DE_BODY = 0.86

# What Д's legs weigh, over the face's own stem, linear in the stem and
# clamped to the two masters it was fitted over.
#
# They were the stem, flat, at every weight -- 1.009, 0.999, 1.008, 1.001
# measured on the built font, where the panel goes 0.974, 0.918, 0.864, 0.932.
# A leg hanging under a plinth is an interior stroke and §2 says interior
# strokes thicken at about three quarters the rate the stem does; this one
# took no reduction at all.
#
# It shows twice. The legs read fat and therefore short -- the eye's verdict
# was "stubs" -- and the white BETWEEN them is what pays: 1.32 stems at
# ExtraBold against a panel 1.82, because the plinth is against the
# sidebearing and cannot grow, so the gap is whatever the legs leave. Once the
# plinth cannot move, the legs' own weight is the only lever on the gap.
#
# Not to be confused with the body's walls, which were the first suspect and
# are fine: measured perpendicular rather than as a horizontal footprint they
# read 1.009, 0.985, 1.000, 0.993 against a panel 1.031, 1.029, 0.997, 0.986.
# The horizontal footprint of a slanted leg is not its weight, and reading it
# that way said 1.76 against 1.55 and sent a whole round at the wrong term.
DE_LEG = (0.9832, -0.3182, 0.932, 0.974)


def de_leg(pr):
    a, b, lo, hi = DE_LEG
    return max(lo, min(hi, a + b * (pr.stem / 1000.0)))

# What share of the face's own leg lean Л takes. A and v measure a LATIN leg,
# which spans a triangle rather than the full height, so some factor is needed
# -- but 0.55 was never derived from anything. It threw away nearly half the
# measured lean and left Л at 0.155-0.182 of travel per unit height against a
# panel median of 0.211, and л at 0.206-0.230 against 0.251. The letter went
# nearly rectangular, and a rectangle reads WIDE however narrow it measures:
# every width figure for л sat on the panel median while the letter still
# looked too wide, because width was never the thing that was wrong.
#
# 0.65 is what puts both cases on the panel: Л lands at 0.215 and 0.182, л at
# 0.271 and 0.243, bracketing the medians of 0.211 and 0.251.
LEG_LEAN = 0.65


def El(pr, top=None, bottom=0.0, outward=0.0, span=1.0):
    """Л -- right stem, arm across the top, leg splaying left as it descends.

    The top left is ROUNDED. It is a place where one stroke turns into
    another, and this face rounds every one of those -- E, F, L, C, G, S, U,
    B, D, P, R. Left square it is an acute wedge; given a vertical run first
    it just moves the kink down to where the vertical meets the slant. Both
    show as a nick. Rounding it is what the typeface itself would do.

    The splay is A's, measured: this face lets a leg travel 0.28-0.33 of its
    own height sideways.

    Л measures 1% narrower, against its own alphabet, than any of the sixty
    panel designs, and Л/П here is 1.000 where their median is 1.137. Widening
    it was tried and reverted, because the width and the slant are not
    independent: this construction spends the splay INSIDE П's span, and
    deriving the splay from a wider target instead straightens the leg -- 127
    units of travel at Thin fell to 79. That buys width by giving up the one
    thing that makes Л a Л, and the letter reads as a leaning П. If it is ever
    widened it has to be by pushing this same splay outward, keeping the
    slant; at Regular that lands at Л/П 1.27, marginally over the panel's
    1.254, so it is not free either.
    """
    top = pr.cap if top is None else top
    m = L(pr)
    r = corner_radius(pr) * RADIUS
    x0, x1, s_ = fit_stems(pr, 2)
    # Д's body is Л, and the two want opposite things: Л is 1.000 of П's width
    # where the panel's median is 1.137, while Д's body is 0.80 of the advance
    # where the panel's is 0.614. Widening Л therefore made Д worse, its body
    # overflowing the plinth until the legs vanished under it. So the body
    # narrows independently of the slant, and Д is the only caller that uses it.
    if span != 1.0:
        mid = (x0 + x1) / 2.0
        half = (x1 - x0) * span / 2.0
        x0, x1 = mid - half, mid + half
    # The face's own leg lean, per case: A's above, v's below. They are not the
    # same -- 0.330 and 0.280 against 0.417 and 0.373 -- and using A's for both
    # left л's leg travelling 0.115 to 0.158 of its own width where the panel's
    # median is 0.204. Too little slant reads as too much width: the letter
    # goes nearly rectangular and stops looking like an л at all.
    lean = m.lcLegSplay if getattr(pr, "lower", False) else m.legSplay
    splay = (top - bottom) * lean * LEG_LEAN
    # `outward` slides the SAME slant leftward out of П's span: at 0 the leg
    # ends where П's stem stands and the letter is П's width, at 1 it starts
    # there and the letter is wider by a whole splay. The slant is identical
    # either way, which is the point -- the earlier attempt derived the splay
    # from a width target instead and straightened the leg to buy the width.
    lgx = x0 + splay * (1.0 - outward)
    foot = lgx - splay
    # unit vector down the leg's left edge, to set the arc's start back from
    # the corner by the same radius as the horizontal side
    dx, dy = foot - lgx, bottom - top
    ln = math.hypot(dx, dy) or 1.0
    ax, ay = lgx + r * dx / ln, top + r * dy / ln

    # opens on the arm, NOT on (lgx + r, top): the closing arc already ends
    # there, and starting on it too leaves two nodes on the same point
    ns = [node(x1 - r, top)]
    ns += arc_to(x1 - r, top, x1, top - r, x1, top)
    # The leg's right edge stops at the arm's underside, so it must be given
    # the x it reaches at THAT height, not the x it would reach at the cap
    # line. Using the latter made it steeper than the left edge, and the leg
    # tapered -- 95 units wide at the top against 89 at the foot.
    inner = foot + s_ + splay * (top - pr.bar - bottom) / float(top - bottom)
    ns += [node(x1, bottom), node(x1 - s_, bottom),
           node(x1 - s_, top - pr.bar), node(inner, top - pr.bar),
           node(foot + s_, bottom), node(foot, bottom), node(ax, ay)]
    ns += arc_to(ax, ay, lgx + r, top, lgx, top)
    p_ = path(ns)
    return [p_ if area(p_) > 0 else reverse(p_)]


def De(pr, top=None):
    """Д -- Л standing on a plinth, with a leg dropping at each end.

    Д measures 0.87 of Ф's width where the panel runs 0.90 to 1.11 at a median
    of 1.015, so it is a little narrow. Widening the plinth to the face's own
    widest capital fixes the number and was reverted with Л: Д's body IS Л, so
    the body straightened along with it and the plinth then had to grow to
    cover a letter that had lost its slant. The two have to move together, and
    Л cannot move without giving up its leg.
    """
    top = pr.cap if top is None else top
    foot = descent(pr)
    x0, x1, s = fit_stems(pr, 2)
    # How far the plinth juts past the body, which is what makes the legs read
    # as legs. As a flat 0.045 of the cap this was 32 units at every weight
    # while the stem grew from 29 to 161, so the overhang fell from 2.24 stems
    # at Thin to 0.27 at ExtraBold -- below the whole panel, whose median is
    # 1.01 -- and the legs disappeared under the strokes above them.
    #
    # It now scales with the stem and stops at the tightest sidebearing the
    # face allows, which is what actually binds here: at ExtraBold 0.6 of a
    # stem is 90 units and there is room for 37.
    inset = min(max(round(0.045 * pr.cap), round(0.60 * pr.stem)),
                x0 - round(MIN_SB * 600.0))
    px0, px1 = x0 - inset, x1 + inset
    body = El(pr, top=top, bottom=pr.bar, span=DE_BODY)
    # The legs keep the plinth's own ends and take their weight inward, so
    # the letter's width does not move and the white between them is what
    # grows -- which is the reading that was wrong.
    lw = round(s * de_leg(pr))
    return body + [rect(px0, 0.0, px1, pr.bar),
                   rect(px0, -foot, px0 + lw, pr.bar),
                   rect(px1 - lw, -foot, px1, pr.bar)]


def Ef(pr):
    """Ф -- a bowl crossed by a full-height stem.

    Ф is the widest letter in the set, and it takes the widest the face itself
    lets a capital be: Y's width, 565 units at Thin and 603 at ExtraBold,
    where Y overhangs the cell by a unit or two. Set against a fixed 548 the
    letter was barely wider than this face's own О at the heavy end -- a ratio
    of 1.013, where every drawn face runs 0.99 to 1.36 and clusters on 1.118.
    At Y's width the ratio comes out 1.115.

    That width is what pays for the strokes. Both the bowl and the stem used
    to take the face's three-stem crowding reduction, which left the bowl at
    0.835 of this face's own О where six of the eight faces measured hold Ф's
    bowl at exactly their О's weight. With the extra room neither needs
    thinning: the bowl is О's, the stem is the Latin stem, and the counter
    absorbs the difference -- 0.095 of the advance at ExtraBold, against a
    panel that runs 0.088 to 0.258. Counters first, stems last, as the brief
    has it.

    The bowl stops short of the lines so the stem can show past it. That is
    the whole letter: without it Ф is an oval with a line buried inside, which
    is what this was -- the bowl took O's full extent, overshoot and all, so
    it stood 20 units TALLER than the stem it was meant to be crossed by and
    the stem never appeared. Nothing projected, and the letter read as a
    barrel. The stem itself stays flat on cap and baseline, the way every
    flat-ended vertical in this face does.
    """
    m = L(pr)
    # Both cases take the panel's width relation now. capWidest is what let
    # the capital grow past its own cell.
    # The lowercase ф is a TALL letter: its stem runs from the descender to
    # the ascender with the bowl at x-height, which is what classify has said
    # all along -- "bowl + ascender-to-descender stem". Drawn to the x-height
    # like its neighbours it measured 1.000 of the x-height where the panel
    # runs 1.589 to 1.975, and its ink came out at 0.69 of the panel's median,
    # outside every one of the 51 faces that draw it.
    if getattr(pr, "lower", False):
        # The bowl is simply o, centred, at o's own size. EF_OVERHANG says how
        # far the STEM projects past the bowl, and it was borrowed for the
        # capital, where the stem stops at the cap line and has to be seen
        # doing it. Down here the stem already runs to the ascender and the
        # descender, so nothing is gained by holding the bowl short of the
        # x-height -- and holding it short is what flattened the bowl: 0.10 of
        # the height off the top and the bottom left it 1.44 wide for its
        # height at Thin and 1.77 at ExtraBold, where the panel's ф sits at
        # 1.04 and this face's own o at 0.86 and 1.31. A flat ellipse where
        # the face draws round.
        # o's own height, and the panel's own width for ф -- 0.863 of the
        # advance, which with that height gives the bowl an aspect of 1.02
        # against the panel's median of 1.04. o's width alone is too narrow:
        # at ExtraBold its counter left only 22 units either side of the stem
        # crossing it, and the four junctions came to 37 degrees where this
        # face's own sharpest is 46.
        #
        # And unlike Ю, ф DOES take the crowding reduction. A scanline across
        # its bowl crosses three strokes -- wall, stem, wall -- which is what
        # m's figure is for. The capital escapes it by being the widest letter
        # the face allows; at x-height there is no such room to buy.
        ink = _ink_round(pr, round_of(pr))
        ob = ink["box"]
        # ф's bowl is NOT о. Drawn at о's exact height it measured 0.97 of the
        # x-height where the panel runs 0.99 to 1.03, and 1.13 wide for its
        # height where the panel stops at 1.08 -- a squashed oval. The panel
        # draws this bowl at 1.04 to 1.10 of the face's own о and is quite
        # clear that it is a bigger letter, so it is given its own height
        # about о's centre rather than о's outline.
        oc = (ob[1] + ob[3]) / 2.0
        orad = (ob[3] - ob[1]) / 2.0 * EF_BOWL_TALLER
        ob = (ob[0], oc - orad, ob[2], oc + orad)
        # The stem runs the panel's own height for ф, centred on the bowl,
        # rather than all the way from the descender to the ascender. Taken
        # to both extremes it stood 1.89 of the x-height at ExtraBold and
        # 1.97 at Thin, against a panel median of 1.781 and a maximum of
        # 1.975 -- a bar longer than any of the 51 faces that draw it.
        # The foot sits on the face's own descender -- p q y g j all reach
        # exactly -200 and ф stands in that same line -- and the panel's
        # height is taken upward from there, which stops short of the
        # ascender. Centring the stem on the bowl instead left it descending
        # 184 where every other descender in the face reaches 200.
        foot = -m.descDepth
        # The stem takes the SAME reduction as the bowl. Left at full weight
        # against a crowd-reduced bowl it ran 1.14 and 1.20 of its own bowl's
        # wall at Regular and ExtraBold, where the panel holds the two equal --
        # median 1.000 across 60 faces, quartiles 0.950 and 1.031. A letter
        # this crowded gives way in both strokes at once or in neither.
        # crowd3 is m's three-stem figure and it over-thins here: it left the
        # wall at 0.78 of the stem where the panel wants 0.82-0.93, which is
        # what made the counters read airy once the bowl had been widened.
        st = ef_fit(pr, "mid") * pr.stem
        crowd = ef_crowd(pr, ink)

        def draw(e):
            # `half` and the sidebearing are the same number read from the two
            # ends of the cell, so the bisection has one thing to solve for in
            # both cases.
            return (_ink_bowl(pr, ink, e, 600.0 - e, ob[1], ob[3], crowd)
                    + [rect(300.0 - st / 2.0, foot,
                            300.0 + st / 2.0, foot + EF_HEIGHT * pr.cap)])
        return draw(ef_edge(pr, draw))
    mid = 300.0
    # How far the stem projects past the bowl. Borrowed, and marked as such:
    # no Latin letter here has a stroke crossing a bowl, and this face ships
    # no Greek, so there is no phi to ask. Every drawn face on this machine
    # puts it between 0.065 and 0.170 of cap and clusters hard on 0.10 --
    # JetBrains 0.100, Consolas 0.100, Monotional 0.083, DejaVu 0.083.
    oh = EF_OVERHANG * pr.cap
    st = ef_fit(pr, "mid") * pr.stem
    ink = _ink_round(pr, round_of(pr))
    crowd = ef_crowd(pr, ink)

    def draw(e):
        return (_ink_bowl(pr, ink, e, 600.0 - e, oh, pr.cap - oh, crowd,
                          BOWL_ROOF["cap"] * pr.bar)
                + [rect(mid - st / 2.0, 0.0, mid + st / 2.0, pr.cap)])
    return draw(ef_edge(pr, draw))


def Yu(pr):
    """Ю -- stem, joining bar, bowl."""
    o = pr.paths(round_of(pr))[0]
    ys = [n.position.y for n in o.nodes]
    x0, x1, s = fit_stems(pr, 3)
    # The bowl keeps O's weight. m's three-stem reduction is for three STEMS,
    # and Ю's bowl is a bowl -- the same argument Ф was fixed on, and the same
    # order the brief sets: counters give way first, stroke weight last. With
    # the reduction ю's lightest stroke read 0.750 of the stem at ExtraBold,
    # under the panel's tenth percentile of 0.769 and well under its median of
    # 0.910, while its counters sat at a roomy 125. Without it the counter
    # takes the strain and closes to 81, which is still wider than the 79 this
    # face's own m accepts between three stems.
    # The bowl takes m's reduction after all. Removing it to lift ю's lightest
    # stroke off the panel's tenth percentile looked right in isolation, and
    # combined with a wider gap it drove the bowl's counter NEGATIVE at
    # ExtraBold: the bowl needed 407 units and had 322, Ю's stroke measured
    # 320 against O's 164, and the variable font stopped interpolating. A
    # scanline across this letter crosses a stem and both bowl walls, which is
    # what the figure is for.
    crowd = L(pr).crowd3
    ink = _ink_round(pr, round_of(pr))
    tx = ink["tx"] * crowd
    case = "lc" if getattr(pr, "lower", False) else "cap"
    # The right side is a bowl, not a stem, and this face sets a round side
    # nearer the edge: b keeps 0.56-0.65 of its stem side's margin there, D
    # 0.50-0.58. Fitted as three stems, ю kept 0.94 and Ю 1.00, and the
    # panel's ю runs 3% wider than its m where ours ran exactly as wide.
    # The italic takes the roman's gain: its un-sheared margins are not margins.
    ro = sloped(pr, caps=True)
    r0, r1, _ = fit_stems(ro, 3)
    x1 += (600.0 - r1) - r0 * _round_share(ro, "b" if case == "lc" else "D")
    # The clear run between the stem and the bowl. As 0.04 of the span this
    # was 21 units at ExtraBold -- 0.085 of the advance where the panel's
    # median is 0.173 and its lower quartile 0.129 -- and the connecting bar
    # was too short to read as a connection at all.
    # ...and the GAP gives way before the counter does, down to YU_GAP_MIN.
    # With the counter the one giving way, down to m's gap between three
    # stems, ю read 0.35 of o at ExtraBold, a slit. Only below YU_GAP_MIN
    # does the gap go further, and then only to keep the counter off m's floor.
    # The walls never give: the heavy faces' walls are this face's O.
    room = x1 - x0 - s
    avail = room - 2.0 * tx
    # Both panel figures are read on that low row, so both are carried to it
    # through the bowl's own curve: `curl` for the gap, `narrow` for the counter.
    bx, by0, bx1, by1 = ink["box"]
    y = by0 + (YU_GAP_ROW * pr.cap - min(ys)) / (max(ys) - min(ys)) * (by1 - by0)
    r = runs([_flatten(ink["o"], 48), _flatten(ink["c"], 48)], y)
    curl = (r[0][0] - bx) / (bx1 - bx)
    narrow = (r[1][0] - r[0][1]) / ink["cw"]
    want = max(L(pr).counter3, YU_COUNTER[case] * ink["cw"] / narrow)
    floor = (YU_GAP_MIN * 600.0 - curl * room) / (1.0 - curl)
    gap = max(0.0, min(YU_GAP * 600.0, max(floor, avail - want),
                       avail - L(pr).counter3))
    bx0 = x0 + s + gap
    # the bar sits on the case's own middle: midY is H's and does not travel
    bary = pr.barCentre * pr.cap - pr.bar / 2.0
    return ([rect(x0, 0.0, x0 + s, pr.cap),
             # into the middle of the wall: ending on the counter's edge, the
            # bar grazed the sheared counter and left a step at ExtraBold
            rect(x0, bary, bx0 + tx / 2.0, bary + pr.bar)]
            + _ink_bowl(pr, ink, bx0, x1, min(ys), max(ys), crowd,
                        BOWL_ROOF[case] * pr.bar))


def _round_share(pr, donor):
    """`donor`'s margin on its round side over its margin on its stem side."""
    xs = [q[0] for p in pr.paths(donor) for q in _flatten(p, 24)]
    return (600.0 - max(xs)) / min(xs)


def _ink_round(pr, donor):
    """A round letter's outer, counter and their INK figures.

    `bowl` reads nodes, and under the italic `paths` un-shears a drawn italic,
    which swings its handles out past the curve (F17): the node box read o 62
    units wider than its ink and its side 16 heavier at ExtraBold, so ю's
    italic bowl came out narrower and heavier than its own numbers. Upright
    the two readings agree to the unit. Ф ф took it on 2026-09-17.
    """
    o, c = pr.paths(donor)[0], pr.paths(donor)[1]
    fo, fc = _flatten(o, 48), _flatten(c, 48)
    xs, ys = [q[0] for q in fo], [q[1] for q in fo]
    mid = (min(ys) + max(ys)) / 2.0
    r = runs([fo, fc], mid)
    return {"o": o, "c": c, "box": (min(xs), min(ys), max(xs), max(ys)),
            "cbox": (min(q[0] for q in fc), min(q[1] for q in fc),
                     max(q[0] for q in fc), max(q[1] for q in fc)),
            "tx": r[0][1] - r[0][0], "ty": min(q[1] for q in fc) - min(ys),
            "cw": r[1][0] - r[0][1]}


def _ink_fit(p, box, x0, y0, x1, y1):
    bx0, by0, bx1, by1 = box
    sx, sy = (x1 - x0) / (bx1 - bx0), (y1 - y0) / (by1 - by0)
    return _map_points([p], lambda x, y: (x0 + (x - bx0) * sx,
                                          y0 + (y - by0) * sy))


def _ink_bowl(pr, ink, x0, x1, y0, y1, crowd, ty_min=0.0):
    """`bowl`, fitted to the ink rather than the nodes.

    `ty_min` floors the roof and floor. `crowd` is a squeeze ACROSS the
    letter, and this face draws no lowercase horizontal lighter than t's bar,
    nor a round capital's roof lighter than H's: crowded, ю's read 0.95 of it
    at Regular once its bowl was wide enough for the signature gate to count
    them.
    """
    tx, ty = ink["tx"] * crowd, max(ink["ty"] * crowd, ty_min)
    return (_ink_fit(ink["o"], ink["box"], x0, y0, x1, y1)
            + _ink_fit(ink["c"], ink["cbox"], x0 + tx, y0 + ty,
                       x1 - tx, y1 - ty))

def _arm_end(body, lo, hi, left):
    """Where a middle arm should die into a curved back.

    Both letters that have one used to run the arm to the bowl's own extreme
    -- x0 for Є, x1 for Э -- which is the single point where the back is
    tangent to vertical. A flat arm end sitting exactly there squares the back
    at the one height it should be roundest, and it does it over the arm's
    whole thickness, so the fault grows with the weight while looking innocent
    at Thin: the back stood still over 0.13 of its edge at Thin and 0.25 at
    ExtraBold, against the C it is drawn from holding 0.12 at every weight.

    The arm has to reach far enough that no white is left between it and the
    back at any height it spans, and not so far that it shows past the arc at
    any of them. The back's own wall is that window, and neither of its edges
    is a safe place to stop: ending on the inner one leaves the arm tangent to
    the counter at the arm's own middle, ending on the outer one runs its two
    corners exactly along the arc, and a boundary that touches another without
    crossing it is F9. So the arm runs to the MIDDLE of the wall, which both
    corners cross square -- read at the arm's top and bottom, taking whichever
    is shallower, since the donor is a drawn C and not assumed symmetric.
    """
    def wall(y):
        a, b = runs(body, y)[0] if left else runs(body, y)[-1]
        return (a + b) / 2.0
    return max(wall(lo), wall(hi)) if left else min(wall(lo), wall(hi))


def E_ukr(pr):
    """Є -- C with a middle arm that stops short of the aperture.

    Reusing E's arm ran it almost the full width and made the letter look
    lopsided. JetBrains' Є ends its arm at 405 against a bowl spanning 92-522
    -- 0.73 of the way across -- so the aperture stays open.
    """
    c = pr.paths(round_of(pr, "C"))
    xs = [n.position.x for p in c for n in p.nodes]
    ys = [n.position.y for p in c for n in p.nodes]
    x0, x1 = min(xs), max(xs)
    mid = (min(ys) + max(ys)) / 2.0
    lo, hi = mid - pr.bar / 2.0, mid + pr.bar / 2.0
    # Є's back is the left one, so that is the edge the arm must not square
    end = _arm_end([_flatten(p) for p in c], lo, hi, True)
    return clone_all(c) + [rect(end, lo, x0 + (x1 - x0) * 0.73, hi)]


def d_shape(left, bot, right, up, r, ry=None, k=KAPPA):
    """Flat on the left, semicircular on the right, as one contour.

    The straight run between the two arcs is emitted only when it has length.
    Where the radius is exactly half the height it has none, and leaving it in
    puts two coincident nodes at the widest point, which nicks the outline
    where the curve meets the straight.
    """
    ry = r if ry is None else ry
    ns = [node(left, bot), node(right - r, bot)]
    ns += arc_to(right - r, bot, right, bot + ry, right, bot, k)
    ns += [node(right, up - ry)]
    ns += arc_to(right, up - ry, right - r, up, right, up, k)
    ns += [node(left, up)]
    return path(ns)


def _spine_walk(spine, y_end):
    """A spine's own boundary, from its bottom-RIGHT corner -- lifted to
    `y_end` -- round the top and down to just short of its bottom-LEFT.

    Read off the spine's finished path rather than rewritten, so Ъ's elbow
    keeps having exactly one description in this file and the capital keeps
    the contour it was approved with. The direction is decided by the path
    itself: whichever way makes the step off the bottom-right corner go UP.
    """
    def ends(ns):
        y0 = min(n.position.y for n in ns)
        flat = [k for k, n in enumerate(ns) if abs(n.position.y - y0) < 1e-6]
        return (min(flat, key=lambda k: ns[k].position.x),
                max(flat, key=lambda k: ns[k].position.x))

    ns = list(spine.nodes)
    bl, br = ends(ns)
    if (br + 1) % len(ns) == bl:
        ns = list(reverse(spine).nodes)
        bl, br = ends(ns)
    out = [node(ns[br].position.x, y_end, ns[br].type, ns[br].smooth)]
    k = br
    while (k + 1) % len(ns) != bl:
        k = (k + 1) % len(ns)
        n = ns[k]
        out.append(node(n.position.x, n.position.y, n.type, n.smooth))
    return out


def _spine_bowl(outer, spine, left, s, up):
    """The spine and the bowl as ONE contour, so the counter can cut into the
    spine instead of being filled back in by it.

    Three contours -- spine, bowl, counter -- cannot express this at all. The
    spine and the bowl both wind positive and the counter negative, so where
    the counter reaches back over the spine the winding still comes to one and
    the ink returns. The silhouette does not change by an outline unit: this
    is the same union, said in one path instead of two.
    """
    if area(outer) < 0:
        outer = reverse(outer)
    ns = [node(n.position.x, n.position.y, n.type, n.smooth)
          for n in outer.nodes]
    # the bowl's top-left corner, which is where the spine takes over
    j = min(range(len(ns)), key=lambda k: abs(ns[k].position.x - left)
            + abs(ns[k].position.y - up))
    p = path(ns[j + 1:] + ns[:j] + _spine_walk(spine, up))
    return p if area(p) > 0 else reverse(p)

def bowl_arc(pr, left, right, bot, up):
    """How far a bowl's outer arc reaches, horizontally and vertically.

    The horizontal comes from how far this face sweeps a bowl -- 0.49 of its
    width at Thin and 0.41 at ExtraBold, the same figure in B as in b -- and
    the vertical from the bowl's own half-height. Deriving both from a single
    radius makes the arc a quarter-circle, which is only right while the bowl
    is about as tall as it is wide. Ь Ъ Б Ы hang one tall bowl at cap height
    and very nearly get away with it; at x-height the same bowl is 250 units
    tall against 413 wide, the height binds, and the sweep collapses to 0.29.
    That is what made в read as a rectangle with rounded corners next to В.
    """
    m = L(pr)
    sweep = m.lcBowlSweep if getattr(pr, "lower", False) else m.bowlSweep
    rx = min(sweep * (right - left), (right - left) * 0.5)
    # The vertical is the bowl's own half-height and nothing else bounds it.
    # It used to be `min(half, rx)`, which is the same tie that made в square,
    # and it bites on exactly one letter: a bowl narrow enough that its sweep
    # comes out under its own half-height drags the vertical down with it and
    # runs its sides flat. **Ы is that letter** -- 360 wide against 468 tall at
    # ExtraBold, where Ь's 477 and Б's are wide enough that the half-height was
    # already binding and this changes nothing for them. Ы's edge stood still
    # over 0.31 of its bowl against a host holding 0.12, the worst in the
    # extension, and it was outside at every weight. See `tools/round.py`, and
    # note the tie is exactly what в had in its own copy of this arithmetic.
    return rx, (up - bot) / 2.0 * 0.97


def bowl_pair(left, bot, right, up, t, min_counter=24.0, th=None, rmin=1.0,
              th_bot=None, th_top=None, r=None, ry=None, tl=None,
              csweep=None, cut=None, lean=0.0, tall=None):
    """A d_shape and its counter, one even stroke apart, correctly wound.

    The stroke is clamped so the counter always has positive width AND
    height. Unclamped, Ы's bowl at ExtraBold came out narrower than two
    strokes: the counter inverted, its signed area flipped, and the
    orientation fix below then took the opposite branch in that master only --
    so the contour was wound one way at Thin and the other at ExtraBold, and
    the variable font would not interpolate. It looked fine at both masters.

    `tl` is the inset on the LEFT, where the bowl meets the spine, and it is a
    different quantity from `t`. `t` is the bowl's own wall and this face draws
    it heavier than a stem -- 166 against 161 at ExtraBold, which is B's own
    figure and the reason `bowl_of` reports it. But B spends that 166 only on
    the wall it curves; on the left its counter sits against the STEM's edge,
    157, because there is no second wall there -- the spine is the wall. Insetting
    both sides by `t` draws a left wall the donor does not have, and the counter
    pays for it: at ExtraBold Ь's counter came out 145 against В's 154, and 166
    minus 157 is the whole of that nine units.

    So `tl` defaults to `t`, which is what a bowl with two walls of its own
    wants, and a caller whose bowl grows off a spine passes the spine's width.
    See METHOD F5 -- one number was doing two jobs, and it was right for one of
    them.

    `rmin` is the floor on the COUNTER's own corner radius. Deriving it as
    `r - t` is fine while the lobe is tall enough to outrun its stroke, which
    is true of Ь Ъ Б Ы, and false of в: its lobes are half the letter, so at
    ExtraBold a 149 radius meets a 150 stroke and the corner floors at a
    single unit, putting two nodes on top of each other. That is the same
    subtraction that squared off г's inner corner -- see Ghe_lc. Callers whose
    lobes can be short pass the face's own inner radius instead.
    """
    # The counter is inset by the stroke on the sides and by the BAR weight
    # top and bottom. This face draws its horizontals lighter than its
    # verticals -- 135 against 161 at ExtraBold -- and a bowl inset evenly
    # ignores that: Б's bowl came out as thick across its top and bottom as
    # down its side, which is heavier than the arm sitting directly above it,
    # and read as the letter changing width from one part to the next.
    th = t if th is None else th
    # The two ends may be inset by different amounts. в needs it: its lobes
    # meet at the waist and share ONE bar between their counters, so each
    # gives half a bar to the join and a whole one to the outside. Insetting
    # both ends equally instead forced the lobes to overlap by a full bar,
    # and the waist barely pinched at all -- 8.5% against B's own 26.8%.
    th_bot = th if th_bot is None else th_bot
    th_top = th if th_top is None else th_top
    # Both insets are clamped TOGETHER, against the room the two of them share.
    # Clamping each to half the width separately is what the single-stroke
    # version did, and with two different insets that lets their sum exceed the
    # letter and invert the counter again -- the winding fault this docstring
    # opens with, which passed both masters and failed in between.
    tl = t if tl is None else tl
    room_w = right - left - min_counter
    if t + tl > room_w and t + tl > 0:
        k = max(0.0, room_w) / (t + tl)
        t, tl = t * k, tl * k
    t, tl = max(1.0, t), max(1.0, tl)
    room, tot = up - bot - min_counter, th_bot + th_top
    if tot > room and tot > 0:
        k = max(0.0, room) / tot
        th_bot, th_top = th_bot * k, th_top * k
    th_bot, th_top = max(1.0, th_bot), max(1.0, th_top)
    # Held just under a true semicircle so the straight run between the two
    # arcs ALWAYS has length. At exactly half the height it has none, and
    # whether that mattered depended on whether the shape was taller or wider
    # -- which differed between the masters for Я, so the two layers ended up
    # with different node counts and the font would not build at all.
    r = (min((up - bot) / 2.0 * 0.97, (right - left) * 0.5) if r is None
         else min(r, (right - left) * 0.5))
    ry = min((up - bot) / 2.0 * 0.97, r) if ry is None else ry
    outer = d_shape(left, bot, right, up, r, ry)
    # The counter's own corner. `r - t` is F2 -- the outer sweep less the
    # stroke -- and it holds up only while the stroke is small against the
    # sweep. It is not: the stroke grows five times across this axis and the
    # sweep does not, so the counter's corner falls from 0.45 of its own width
    # at Thin to 0.24 at ExtraBold where the face's own b holds 0.45 and 0.44
    # and its o holds 0.45 at both. A caller with a lowercase donor to read
    # passes the share instead; `csweep` is that share.
    #
    # `cut` moves the counter's left edge INTO the spine and leaves it a
    # straight line. b lets its counter run past its stem's right edge -- 140
    # units of stroke beside it against a stem of 150 at ExtraBold, 28 against
    # 29 at Thin -- and B does not, 157 against 157. The edge stays flat
    # because this bowl is half b's height and has to run straight somewhere:
    # rounding it as well, which was tried on 2026-08-12 and rejected, leaves
    # the counter straight nowhere and it reads as an ellipse. Only a caller
    # that draws its spine and bowl as ONE contour may pass it -- a separate
    # spine rectangle fills the cut straight back in.
    cl = left + tl - (cut or 0.0)
    inner_w = (right - t) - cl
    ri = (max(min(csweep * inner_w, inner_w * 0.5), rmin) if csweep
          else max(r - t, rmin))
    iry = max(ry - (th_bot + th_top) / 2.0, rmin)
    # `tall` marks a counter end standing more than `tall` times its reach.
    # Inset from a tall outer, a narrow counter turns one tall curve from top
    # to bottom -- Ы's ends run 42 by 111 at ExtraBold -- and sheared plain it
    # tapers to a point. The face's own D has the same curve at twice the
    # width. The side stays curved, as D's does, and is drawn fuller instead.
    # A straight-sided slot, as the panel draws it, was rejected on sight.
    full = bool(tall) and iry > tall * ri
    inner = d_shape(cl, bot + th_bot, right - t, up - th_top, ri, iry,
                    YERU_FULL if full else KAPPA)
    # `lean` takes back part of the italic's shear on the ROUND end, about the
    # bowl's own middle, so the turns come out even once sheared. Left alone,
    # the shear tightens the top-right turn into a knuckle and slackens the
    # bottom-right one: ь's top-right stroke stood 0.09-0.20 of a stem heavier
    # than its bottom-right, where the face's own italic P R D hold 0.04-0.06
    # -- they start the top turn earlier than their upright does. The flat side
    # stays where the spine is. A mirrored caller passes it negated.
    # A full counter is left as sheared: turned about the bowl's middle, its
    # long side leant back into a wedge. Only its outer takes the lean, less.
    if lean:
        yc = (bot + up) / 2.0
        if full:
            lean *= TALL_LEAN
        for p, flat in ((outer, left),) if full else ((outer, left), (inner, cl)):
            for n in p.nodes:
                if abs(n.position.x - flat) > 1e-6:
                    n.position = Point(n.position.x - lean * (n.position.y - yc),
                                       n.position.y)
    if area(outer) < 0:
        outer = reverse(outer)
    if area(inner) > 0:
        inner = reverse(inner)
    return [outer, inner]


def Be(pr):
    """Б -- Г's arm and spine over a bowl.

    The bowl is drawn, not borrowed. B's lower lobe is half of a two-lobe
    letter, so pressing it into service as a single bowl means stretching its
    outer and squeezing its counter by different amounts, and a counter
    squashed on its own comes out twisted at the heavy weights. D is the right
    SHAPE but its counter curves on the left, so used here it swells the
    bowl's left stroke to 40 units against a 29-unit spine and bulges inside
    the letter.

    So: flat on the left, flush with the spine, and a semicircular right end,
    with outer and counter offset by one even stroke. Corners come from the
    face's own arc.

    Height and arm length are measured: the bowl reaches 59% of cap
    (JetBrains 59%), and the arm stops at 92% of the bowl's width (JetBrains
    94%, Consolas 91%, Iosevka 90%; Г's full arm reaches 98% and reads
    top-heavy).
    """
    arm = Ghe(pr)
    x0 = min(n.position.x for n in arm[0].nodes)
    # The bowl reaches where B's does -- Б, Ь and Ъ all hang the same bowl,
    # and the face already draws it.
    x1 = bowl_of(pr)[1]
    top = 0.59 * pr.cap
    # B's own bowl stroke, not the stem and not the three-stem reduction. Б is
    # a spine and a bowl -- two strokes -- and the face draws that bowl
    # slightly heavier than its stem, 166 against 161 at ExtraBold. Carrying
    # m's crowding reduction here made Б lighter than all sixty panel faces.
    t = bowl_of(pr)[2]

    # ...on the wall it curves, and only there. On the left the counter sits
    # against the spine, exactly as B's does, and the spine here is Г's own --
    # read off the arm's contour rather than taken as `pr.stem`, so it cannot
    # drift from the letter it is spliced to. See bowl_pair's `tl`.
    spine = arm[0].nodes[0].position.x - x0

    rx, ry = bowl_arc(pr, x0, x1, 0.0, top)
    body = bowl_pair(x0, 0.0, x1, top, t, th=pr.bar, r=rx, ry=ry,
                     rmin=inner_radius(pr), tl=spine)

    arm_right = max(n.position.x for n in arm[0].nodes)
    for n in arm[0].nodes:
        if abs(n.position.x - arm_right) < 1.0:
            n.position = Point(x1 * 0.92, n.position.y)
    return arm + body



# ---------------------------------------------------------------------------
# T3 capitals -- drawn, never mirrored from a Latin letter
# ---------------------------------------------------------------------------

def bowl_of(pr):
    """The bowl this case hangs: B's for the capitals, b's for the lowercase.

    Both are read off the face, and they genuinely differ -- b's reaches 526
    where B's reaches 518 at Thin, and it is drawn at exactly the lowercase
    stem where B's is a unit heavier than its own. Two answers from the host,
    not one answer carried across a case boundary.
    """
    m = L(pr)
    if getattr(pr, "lower", False):
        return m.lcBowlLeft, m.lcBowlRight, m.lcBowlStroke
    return m.bowlLeft, m.bowlRight, m.bowlStroke


def shear_fit(pr, right, rows):
    """Pull a drawn right edge in until the ITALIC's shear lands it on b's.

    Every recipe here is written upright and the italic shears the result, so
    a letter's rightmost ink ends up wherever its own widest ROW sits, plus
    the slant that row has climbed. `bowl_of` hands back b's box UN-SHEARED --
    which is not a footprint -- and the heights do not match: b is widest two
    thirds of the way up its bowl, ь three tenths of the way up its own, в at
    its upper lobe and б at its arm, right up at the ascender. The upright
    cannot see any of this, and there ь, ъ and в land on b's right edge to the
    unit. In the italic they stood 22, 23 and 41 units past it and б 119.

    `rows` maps a candidate edge to the (x, y) of every row that could be the
    widest -- в has two lobes and only the shear decides which of them is in
    front. Twice round, because a row need not move with the edge unit for
    unit: в draws its upper lobe at 0.945 of it, and once round leaves that
    fraction of the error behind.

    Only ever narrows, and only in the italic lowercase. The capitals are
    sloped uprights in this face -- H's extremes are its baseline and its cap,
    the same two rows B is widest between -- so the shear costs them nothing
    and they are left alone.
    """
    if not pr.italic or not getattr(pr, "lower", False):
        return right
    k = math.tan(math.radians(pr.italic))
    goal = max(pr.ink("b"))
    for _ in range(2):
        out = max(x + (y - pr.pivot) * k for x, y in rows(right))
        right -= max(out - goal, 0.0)
    return right


def _rows(paths):
    """Every point of a drawn shape, for shear_fit to pick the widest from."""
    return [q for p in paths for q in _flatten(p, 24)]


# в's upper lobe, as a fraction of the lower's width. The face's own B puts it
# at 0.949 at Thin and 0.941 at ExtraBold; the panel's median for в is 0.946
# across 51 faces. Host and panel agreeing to three decimals is as settled as
# a proportion gets here.
VE_UPPER = 0.945


def Ve(pr, top=None):
    """в -- two lobes on a stem, the upper a little narrower.

    В is the Latin B unchanged, so B is the construction: a stem the full
    height carrying a D-shaped lobe above and below a waist. Everything with a
    size in it comes from the lowercase instead -- b's bowl rather than B's,
    per bowl_of.

    The waist sits at 0.51, which is B's own at all three weights and inside
    the panel's 0.496-0.592 for в.

    The two lobes share ONE bar at the waist rather than stacking a bar each,
    which is the difference between working and not at x-height: the strokes
    here are 93% of the capital's while the letter is 70% as tall, so two bars
    would leave the ExtraBold counters at less than nothing. Each lobe's outer
    therefore runs half a bar PAST the waist and its counter stops half a bar
    short of it.
    """
    top = pr.cap if top is None else top
    x0, right, t = bowl_of(pr)
    m = L(pr)
    base = getattr(pr, "_pr", pr)
    # B's own three horizontals, per master. A two-lobe letter does not draw
    # them at the bar: B runs its lobe's roof and floor at 0.96 of the bar at
    # Thin and 0.90 at ExtraBold, and its waist lighter still at 0.96 and
    # 0.85. Drawn at a flat bar each, в spent 318 of its 493 units of
    # x-height on three horizontals and left 175 for two counters, where the
    # panel leaves 204 -- and the counters came out 2.09 times as wide as
    # they were tall against a panel 1.17 to 1.83.
    #
    # Read from B's INNER contour, and from its on-curve nodes only. Its node
    # box is 45 units taller than the curve it describes, because the control
    # points of a bowl's corner sit outside the bowl -- the same trap as
    # taking control points for polygon vertices, which mis-measured every
    # round letter until check.py's flat() was fixed. Nodes 1 and 18 are the
    # counters' outer ends, 9 and 10 the two sides of the waist.
    bi = pr.paths("B")[1].nodes
    th = (base.cap - bi[1].position.y) / float(base.bar) * pr.bar
    wb = ((bi[9].position.y - bi[10].position.y) / float(base.bar)) * pr.bar
    waist, step = m.bWaist * top, m.bLobeStep
    ri = inner_radius(pr)

    # The outer is ONE contour, and the join is B's own: the lower arc arrives
    # horizontal, the outline steps straight down, and the upper arc leaves
    # horizontal again. Two right angles.
    #
    # Two separate d_shapes cannot do this and both ways of trying failed the
    # sweep. Left to their own radii the arcs end at different x, so the union
    # steps sideways between two curves each tangent to the horizontal there:
    # a 6-degree needle at every master. Forced to end at the same x they meet
    # tangentially instead, which is a cusp -- 12 degrees. The face's own
    # sharpest notch is 19 at Thin and 15 at ExtraBold, so neither will do.
    # What makes B's join square is the short vertical BETWEEN the two arcs,
    # 12 units at Thin and 5 at ExtraBold, which is why bLobeStep is measured.
    wl, wu = waist + step / 2.0, waist - step / 2.0

    # The arcs are ELLIPSES, not quarter-circles: the horizontal reach comes
    # from how far this face sweeps a bowl and the vertical from the lobe's
    # own half-height. One radius for both axes is what made в look nothing
    # like В -- a lobe is half the letter tall, so the height bound the radius
    # and the arc swept only 0.24 of the width where b and B both sweep about
    # 0.5. The lobes came out as rectangles with rounded corners.
    # ...and the sweep is a fraction of the LOBE'S HEIGHT, not of the letter's
    # WIDTH. The fraction itself is right and comes from the face; what it
    # multiplied was wrong. A lobe is half the letter tall and the whole of it
    # wide, so a reach taken across the width asked for a corner 202 units
    # across on a lobe 193 tall at ExtraBold -- a radius wider than the lobe
    # was high. The letter read wide and flat, which is what was reported.
    #
    # Measured in the built font as the outer edge's setback at the waist over
    # the lobe's height, this face's В runs 0.42 at Thin falling to 0.36 at
    # ExtraBold and the panel's в 0.39 falling to 0.32. Against the width, в
    # ran 0.57 RISING to 0.65: outside at every weight and moving the wrong
    # way, because a bowl's sweep narrows as the face gets heavier while the
    # letter it is measured across widens.
    # ...and BOTH of those readings were of the horizontal radius, because
    # there was only ever one lever: the vertical was derived from it,
    # `ry = min(half the lobe, rx)`. That is why neither attempt could be
    # right. A reach taken across the width drove the vertical to a full
    # semicircle and the lobe read wide and flat; taken across the lobe's
    # height it left the vertical tiny and the lobe read square -- 0.59 of its
    # height standing still at ExtraBold against a panel 0.19-0.23, and
    # getting worse with weight while the face's own b held 0.22. Reported by
    # eye; no gate here measures roundness.
    #
    # So the two radii are read separately and neither bounds the other. The
    # horizontal is the face's sweep across the lobe's WIDTH, which is the
    # rule `bowl_arc` already follows and what `_sweep` actually measures --
    # multiplying it by a height was a dimensional error of the same class as
    # the bowl's inset. The vertical is b's own: it turns its bowl in over
    # 0.400 of the height at each end at both masters, and B agrees at 0.454.
    # ...and both of those readings were of the SAME radius, because there was
    # only one lever: the vertical was derived from the horizontal, so no value
    # of the horizontal could land both. A sweep across the width dragged the
    # vertical to a semicircle and the lobe read wide and flat; a sweep across
    # the lobe's height left the vertical tiny and the lobe read square -- 0.54
    # of its own edge standing still at ExtraBold against 0.17-0.26 for every
    # other bowl in the face, and getting worse with weight. Reported by eye;
    # no gate here measures roundness.
    #
    # The answer is that в had no business rolling its own radii. `bowl_arc` is
    # the rule the whole family already follows -- the horizontal from how far
    # this face sweeps a bowl ACROSS ITS WIDTH, which is what `_sweep` actually
    # measures, and the vertical from the lobe's own half-height, which binds
    # whenever the lobe is short. It binds here, and that is correct rather
    # than a fallback: a lobe half the letter tall is very nearly semicircular
    # in this face, which is what ь's own bowl does at 0.25.
    # The horizontal is B's own WAIST -- how far a two-lobe letter comes back
    # in between its lobes, 0.353 of its bowl width at Thin and 0.288 at
    # ExtraBold -- and NOT the bowl's sweep. The sweep says how far an arc
    # reaches; on a letter with a waist the same number then also decides how
    # deep the pinch is, and one number cannot answer both. Taking the sweep
    # dug the waist to 144 units against B's 137 at ExtraBold and brought the
    # junction to a point where B steps square. Reported by eye, on a version
    # whose every other reading had just landed; the profile through the waist
    # is what confirmed it.
    #
    # The vertical is the lobe's own half-height, and nothing else bounds it.
    # A lobe half the letter tall is very nearly semicircular in this face --
    # ь's own bowl is -- and the flat run that leaves, 0.11 of the edge, is
    # exactly what b and о hold.
    ry1 = wl / 2.0 * 0.97
    ry2 = (top - wu) / 2.0 * 0.97
    # WHICH LOBE STANDS FURTHEST RIGHT is not the same question upright and
    # sheared. The upper is drawn five per cent narrower, so upright the lower
    # wins; sheared, the upper sits a quarter of the x-height higher and the
    # slant is worth more than the five per cent. Both rows are the top of a
    # lobe's straight run, and shear_fit takes whichever is in front.
    right = shear_fit(pr, right, lambda r: [
        (r, wl - ry1), (x0 + VE_UPPER * (r - x0), top - ry2)])
    upper = x0 + VE_UPPER * (right - x0)
    rx = min(m.bowlWaist * (right - x0), (right - x0) * 0.5)
    xs = right - rx
    # The upper lobe's arc starts at the same x as the lower's, which is what
    # keeps B's square join.
    rx2 = max(upper - xs, 4.0)

    ns = [node(x0, 0.0), node(xs, 0.0)]
    ns += arc_to(xs, 0.0, right, ry1, right, 0.0)
    ns += [node(right, wl - ry1)]
    ns += arc_to(right, wl - ry1, xs, wl, right, wl)
    ns += [node(xs, wu)]
    ns += arc_to(xs, wu, upper, wu + ry2, upper, wu)
    ns += [node(upper, top - ry2)]
    ns += arc_to(upper, top - ry2, xs, top, upper, top)
    ns += [node(x0, top)]
    outer = path(ns)
    if area(outer) < 0:
        outer = reverse(outer)

    # and the two counters, one bar apart across the waist
    lo = d_shape(x0 + t, th, right - t, waist - wb / 2.0,
                 max(right - xs - t, ri), max(ry1 - th, ri))
    up = d_shape(x0 + t, waist + wb / 2.0, upper - t, top - th,
                 max(rx2 - t, ri), max(ry2 - th, ri))
    return [outer] + [reverse(c) if area(c) > 0 else c for c in (lo, up)]


# ь ы ъ я: how the lowercase bowl is PROPORTIONED. Built from the capital's
# construction at x-height across a full lowercase cell, ь's bowl stood 0.60
# to 0.68 as tall as it was wide and я's 0.71, where every bowl this face
# draws stands at 0.87 or more -- and the user saw it before any reading did:
# "their bowls don't fit the fontface aesthetic". Two moves, in this order:
#
# SOFT_RAISE lifts the bowl at the light end only -- 18 % at the Thin stem,
# nothing at the ExtraBold one, as `a + b * stem / 1000`. At ExtraBold the
# bowl already stands higher, because it grows with its stroke, and lifting
# it too left a stub of stem above it (the user: "a short leg at the top").
# The stem left above it then shortens 0.42 -> 0.34 of the x-height across
# the axis, which is P's own 0.47 -> 0.38 at the same rate.
#
# SOFT_SHAPE then narrows the bowl until it stands at this share of b's own
# proportion: 0.88 at Thin, 0.77 at ExtraBold. One share, because the face's
# bowls widen for their height as they get bolder, and a single target for
# every weight made ExtraBold ь "just prominently narrower". A bowl already
# at the target -- ы and ъ at ExtraBold -- is left alone, and a narrowed
# letter is recentred in its cell.
SOFT_RAISE = (1.2231, -1.4876)
SOFT_SHAPE = 0.74
# How much of the shear a sloped bowl's round end takes back -- see bowl_pair.
# The face's own italic P R D leave their top turn 0.00-0.10 of a stem heavier
# than upright, P and R 0.03-0.04. All of it back balances the turns exactly,
# more evenly than the face does; three quarters leaves ь Ь Ъ я Я 0.01-0.06.
BOWL_LEAN = 0.75


# How tall for its reach a sloped Ы/ы counter end stands before it is drawn
# full. The light master's stand 0.99-1.09 and are left alone; ExtraBold's
# stand 1.5 and 2.6.
YERU_TALL = 1.3
# The share of the lean a full counter's OUTER takes. With none, heavy Ы ы
# read +0.11-0.13 against P's +0.04, and every weight between inherited it.
TALL_LEAN = 0.25
# How full a tall Ы/ы counter end is drawn, as its curve's handle share
# (a circle is 0.5523). Plain, sheared, it tapers to a point at ExtraBold.
YERU_FULL = 0.7


def bowl_lean(pr):
    return BOWL_LEAN * math.tan(math.radians(pr.italic))


def sloped(pr, caps=False):
    """What a sloped-roman letter reads its donor figures from.

    Under the italic the roman master -- see `Params.roman`. ь ы ъ я are drawn
    upright and sheared, so the letter they slope is the ROMAN b and R; this
    face's italic b is a true italic whose figures overweighted their bowls
    and cut the Thin counter into the stem. Everywhere else, `pr` itself.

    `caps` lets a capital in as well, for Я Ь Ъ Ы: read off the italic B,
    their stroke came out 185 against the roman's 166 at ExtraBold and their
    sweep 0.455 against 0.501, and the counter's corner fell to 0.20-0.28 of
    its width against the upright letters' 0.44-0.46 -- the box the user
    marked in Я. Б reads B its own way and is not asked.
    """
    lower = getattr(pr, "lower", False)
    if not pr.italic or not (lower or caps):
        return pr
    return Lower(pr.roman()) if lower else pr.roman()


def soft_raise(pr):
    """SOFT_RAISE at this master's stem; never below no lift at all."""
    a, b = SOFT_RAISE
    return max(a + b * pr.stem / 1000.0, 1.0)


def soft_bowl(pr, top=None):
    """The lower bowl shared by Ь Ъ Ы Б, and its stem left edge.

    One shape for all four, so they stay a family. Its top sits at half the
    cap: JetBrains puts Ь's bowl top at 0.50 cap and Ъ's at the same height.
    """
    top = pr.cap if top is None else top
    # Full stem weight, not the three-stem reduction. Ь and Ъ are a spine and
    # a bowl -- two strokes across any scanline, exactly what B's lower bowl
    # is -- so nothing is crowding them. Carrying m's reduction here made
    # their bowls 0.79 of В's own at ExtraBold, where every face measured
    # holds the two equal, at a median of 1.004. This is the same fault Б was
    # already fixed for; Ь and Ъ never got the fix.
    #
    # Ы does have three strokes and does shave, but it shaves its own stem
    # first and then scaled THIS by the result, so its bowl was reduced twice
    # over. With the double reduction gone it lands on the panel's median.
    t = bowl_of(sloped(pr, caps=True))[2]
    # The bowl's TOP is not a fixed height -- its COUNTER's top is. Every face
    # measured holds Ь's and Ы's counter top between 0.45 and 0.53 of the cap
    # and barely moves it across the weight axis; the bowl's outer top then
    # rises with the stroke to keep it there. Pinned at a fixed 0.52 of the
    # cap, as this was, the counter is squeezed from above as the stroke
    # thickens -- by ExtraBold its top had fallen to 0.34 cap and the hole in
    # the bowl had shut to a third of its height. The bowl grows instead.
    return t, BOWL_COUNTER_TOP * top + t * pr.bar / pr.stem


def shoulder_spine(pr, sx, xs, s, top):
    """A stem with a shoulder reaching left from its top, as ONE contour.

    Г's elbow, the other way round, and rounded the way this face rounds every
    turn: the generous radius on the outside of the bend, the tighter one on
    the inside. Laid on as a plain rectangle instead -- which is what Ъ did --
    both corners come out square, and a square elbow is the one thing Г, L, E
    and J never show. Drawn as a single contour rather than a bar over a stem
    so the two do not share an edge exactly at each master and drift apart
    between them.

    At the face's own radius, though, the corner swallowed the shoulder: the
    shoulder reaches 0.20 of the cell and the corner took 0.69 of it at Thin,
    where E and F give theirs 0.26 to 0.29 of the arm. So it takes the reduced
    corner, and the same inner radius comb derives from it -- see RADIUS.
    """
    ro = corner_radius(pr) * RADIUS
    ri = max(min(ro - pr.stem, pr.bar), 4.0)
    b = pr.bar
    ns = [node(sx, top), node(xs + s - ro, top)]
    ns += arc_to(xs + s - ro, top, xs + s, top - ro, xs + s, top)
    ns += [node(xs + s, 0.0), node(xs, 0.0), node(xs, top - b - ri)]
    ns += arc_to(xs, top - b - ri, xs - ri, top - b, xs, top - b)
    ns += [node(sx, top - b)]
    p = path(ns)
    return p if area(p) > 0 else reverse(p)


def Soft(pr, top=None, x0=None, right=None, stem=None, t=None, shoulder=None):
    """Ь -- stem the full height, bowl on the lower half."""
    out, lost = _soft(pr, top, x0, right, stem, t, shoulder)
    return translate(out, lost / 2.0) if lost else out


def _soft(pr, top=None, x0=None, right=None, stem=None, t=None, shoulder=None,
          tall=None):
    """Soft's drawing, and how much narrower SOFT_SHAPE made it -- which the
    caller recentres by half, and Ы also takes off its detached stem."""
    top = pr.cap if top is None else top
    bl, br, _ = bowl_of(pr)
    x0 = bl if x0 is None else x0
    # Ы hands its own edge in, worked out from where its detached stem starts,
    # and Ъ lets this find Ь's. Only an edge taken from b needs the shear
    # correction -- see shear_fit.
    fit = right is None
    right = br if right is None else right
    s = pr.stem if stem is None else stem
    t0, bt = soft_bowl(pr, top)
    tt = t0 if t is None else t
    lower = getattr(pr, "lower", False)
    if lower:
        bt *= soft_raise(pr)
    spine = (rect(x0, 0.0, x0 + s, top) if shoulder is None
             else shoulder_spine(pr, shoulder, x0, s, top))
    # The counter's corner is read off b for the LOWERCASE only. `r - t`, which
    # is what the capitals keep, happens to land on the face's own answer at
    # cap height -- Ь's counter turns over 0.46 of its width at Thin and 0.44
    # at ExtraBold against B's 0.50 and 0.61 -- because a cap-height bowl is
    # wide enough that its sweep still outruns the stroke. The lowercase bowl
    # is half that height and it does not: ь's fell to 0.24 at ExtraBold, ъ's
    # to 0.17 and ы's to 0.19, against b's own 0.44. See bowl_pair, and F2.
    csweep = L(sloped(pr)).lcCounterSweep if lower else None
    # ...and how far the counter runs past the spine's edge, also b's and also
    # the lowercase only. Taken as a SHARE of the spine rather than in units,
    # because Ы's spine is its own shaved stem and not the face's -- the same
    # reason `tl` is passed the spine below. `lcBowlInsetStem` is read per
    # master, so the cut widens with the weight the way b's does: ten units at
    # ExtraBold, one at Thin.
    cut = s * (1.0 - L(sloped(pr)).lcBowlInsetStem) if lower else 0.0
    # `tl=s` -- the counter's left edge is the spine's own, not the bowl's
    # wall. Ь Ъ Ы all come through here, so all three take it, and Ы passes its
    # own shaved stem rather than the face's because that IS its spine. See
    # bowl_pair's `tl`.
    # The capitals take B's sweep off the roman too; the lowercase keeps the
    # sweep it was approved on.
    arc_pr = pr if lower else sloped(pr, caps=True)

    def bowl_at(r):
        rx, ry = bowl_arc(arc_pr, x0, r, 0.0, bt)
        return bowl_pair(x0, 0.0, r, bt, tt,
                         th=tt * pr.bar / pr.stem, r=rx, ry=ry,
                         rmin=inner_radius(pr), tl=s, csweep=csweep, cut=cut,
                         lean=bowl_lean(pr), tall=tall)

    if fit:
        right = shear_fit(pr, right, lambda r: _rows(bowl_at(r)))
    lost = 0.0
    if lower:
        lost = max(right - (x0 + bt / (SOFT_SHAPE * L(sloped(pr)).lcBowlShape)), 0.0)
        right -= lost
    bowl = bowl_at(right)
    if not cut:
        return [spine] + bowl, lost
    return [_spine_bowl(bowl[0], spine, x0, s, bt), bowl[1]], lost


def Hard(pr, top=None):
    """Ъ -- Ь with a shoulder reaching left from the top of the stem.

    The shoulder's length is the one thing every drawn Ъ agrees on, and it is
    not a multiple of the stem -- against the stem it runs anywhere from 1.56
    down to 0.57 across the weights. Against the ADVANCE it barely moves:
    0.233, 0.208 and 0.192 through JetBrains' three weights, 0.212 and 0.203
    through DejaVu's two, 0.191 and 0.189 through Consolas'. A fifth of the
    cell, near enough, at any weight.

    And Ъ is a WIDE letter because of it -- 0.90 to 0.96 of the advance in
    every face measured. This was shifting Ь's stem right by a token amount
    and keeping Ь's own width, so the shoulder came out at 0.085 of the
    advance, less than half of anyone's, and the letter stayed as narrow as Ь.
    The shoulder now reaches out to the sidebearing instead, and the bowl
    keeps its own width by running the other way.

    The shoulder is part of the stem's own contour, not a bar laid across it,
    so the elbow can carry the face's corners -- see shoulder_spine.
    """
    top = pr.cap if top is None else top
    # the bowl is Ь's, so it ends where Ь's ends -- B's own above and b's own
    # below. Only the stem moves right, to leave the shoulder its room, and
    # the shoulder's own length is a share of the CELL rather than of the
    # letter, so it carries across the case unchanged: the panel puts the
    # lowercase ъ's at 0.203 of the advance against this file's 0.20.
    #
    # What the stem's position then costs is the bowl's width, and the bowl
    # pays for the wall twice. That is why the left edge has to travel -- see
    # HARD_LEFT.
    a, b = HARD_LEFT["lc" if getattr(pr, "lower", False) else "cap"]
    left = max(a + b * (pr.stem / 1000.0), 0.0) * 600.0
    # The edge is left to Soft rather than passed in, which finds the same
    # `bowl_of` number -- and in the italic fits it to ъ's own bowl, which
    # stands further right than Ь's because the shoulder has pushed the stem
    # across. See shear_fit.
    return Soft(pr, top, x0=left + HARD_SHOULDER * 600.0, shoulder=left)


def Yeru(pr, top=None):
    """Ы -- Ь with a detached stem at the right."""
    top = pr.cap if top is None else top
    s = pr.stem
    # The bowl's right edge was a fixed fraction of the advance, and by
    # ExtraBold the detached stem had already begun before it: the two
    # overlapped by a few units and left a splinter of ink above and below the
    # join. The edge is not a fraction to pick -- it is wherever the stem
    # starts, less the gap this face leaves between two strokes.
    # Across the cell Ы has to find, in order: a stem, the bowl's counter, the
    # bowl's own stroke, a gap, and a second stem. That is three strokes and
    # two counters -- the same problem Ш solves -- so it takes the width and
    # the stem Ш gets, widening into the sidebearings first and giving up
    # stroke weight only after that.
    x0, x1, s = fit_stems(pr, 3)
    # Three strokes in a row is how much ROOM Ы needs, but not how heavy it may
    # be. Measured across four faces at their bold weights, Ы is between 68 and
    # 75 per cent ink across its own width, and to hold that every one of them
    # shaves its stems below the face's own -- JetBrains takes 7 per cent off
    # at Regular and 14 at ExtraBold. Ш's shave alone is not enough here,
    # because the bowl's stroke has to fit between the stems rather than
    # standing clear of them: at ExtraBold this came out 79 per cent ink,
    # heavier than any reference and visibly heavier than the rest of the face.
    s = min(s, YERU_INK * (x1 - x0) / (2.0 + L(pr).crowd3))
    t = soft_bowl(pr, top)[0] * (s / pr.stem)

    # The two counters are NOT equal, and neither is a fraction of the stem.
    # The reference runs the bowl's counter at 2.26 and 2.17 times the gap to
    # the detached stem -- near enough the same split at both weights. Giving
    # the gap a fixed slice of the stem and handing the bowl whatever was left
    # unbalanced it completely: at Thin the gap came to nine units and the bowl
    # all but touched the stem, and at ExtraBold the bowl swallowed the width
    # and its own counter closed to a slit.
    gap = (x1 - x0 - 2.0 * s - t) / (1.0 + YERU_SPLIT)
    # Ы's bowl is barely wider than its stroke, so in the italic its tall
    # counter is drawn full -- see bowl_pair's `tall`. Upright, the narrow D
    # reads as a bowl and was approved as one.
    out, lost = _soft(pr, top, x0=x0, right=x0 + s + YERU_SPLIT * gap + t,
                      stem=s, t=t, tall=YERU_TALL if pr.italic else None)
    # a narrowed bowl takes its detached stem in with it, so the gap between
    # them stays the one the reference splits by
    out = out + [rect(x1 - s - lost, 0.0, x1 - lost, top)]
    return translate(out, lost / 2.0) if lost else out

def E_rev(pr, top=None):
    """Э -- C reflected, plus a middle arm.

    Reflection is the right construction here and building it from generated
    arcs was not: Э IS a reversed С, and every well-drawn Cyrillic makes it
    one. Eight of the eight faces measured set Э to within a few thousandths
    of their own С's width; the median ratio across the whole panel is 1.000.

    The terminals are C's, untouched. They used to be squared off afterwards,
    on the theory that C's slanted cut leans the wrong way once mirrored --
    but that reading was wrong. C's cut is a straight run the length of the
    stroke, laid PERPENDICULAR to it, and a perpendicular cut stays
    perpendicular through a reflection. Worse, the squaring only ever fired at
    Thin: it grouped the four terminal nodes by height, and at ExtraBold the
    upper pair straddles the bucket boundary, so that master kept the chisel
    while Thin got a flat cut. The two masters described different terminals
    and every weight between them interpolated one into the other.
    """
    # Э reverses the face's own C, so the donor follows the case: C above and
    # c below. Cloned outlines do not re-size through Lower the way measured
    # geometry does -- run at x-height with C still named, э came out at the
    # CAP height, 710 units tall, and matching node counts across the masters
    # said nothing about it.
    body = mirror_x(clone_all(pr.paths(
        "c" if getattr(pr, "lower", False) else "C")), 300.0)
    ns = list(body[0].nodes)
    xs = [n.position.x for n in ns]
    ys = [n.position.y for n in ns]
    mid = (min(ys) + max(ys)) / 2.0
    x0, x1 = min(xs), max(xs)
    lo, hi = mid - pr.bar / 2.0, mid + pr.bar / 2.0
    # reflected, so Э's back is the right one -- see `_arm_end`
    end = _arm_end([_flatten(p) for p in body], lo, hi, False)
    return body + [rect(x1 - (x1 - x0) * 0.73, lo, end, hi)]


# З against this face's own O, and з against its own o -- the width each takes,
# whatever the digit it is drawn from happens to be. Both are the panel's own
# figure over the 50 faces that answer, and both are genuinely flat: fitted as
# a line in the stem the slope is nothing, and the fit's residual matches the
# flat constant's to four decimals. See METHOD, "Not every constant hides a
# relation" -- and the two agreeing to two parts in a thousand across the case
# is the panel saying this is one figure, not two.
ZE_ROUND = {"cap": 0.9814, "lc": 0.9829}


def round_w(pr, name):
    """How wide O/o's INK is -- which `bbox` does not say in the italic.

    `bbox` reads nodes, and a drawn italic un-sheared has its extremes BETWEEN
    them: un-shearing swings the control points out past the curve, and the box
    then overstates o by 62 units at Thin. Upright the extremes are nodes and
    the two readings agree exactly, which is why the upright has always been
    right here and cannot move.

    З and з take their width from a round letter and their own box from the
    flattened three, so the two sides of that comparison were being read in
    different units -- and only in the italic. It put З 148 units past О and з
    103 past о where the upright sits just inside both. The other face of the
    fault `shear_fit` answers: a reading that is not ink is not a width.
    """
    xs = [x for p in pr.paths(name) for x, _ in _flatten(p, 24)]
    return max(xs) - min(xs)


def _ze_wall(polys, x0, x1, y0, y1):
    """The three's wall at the lobes' widest, where a horizontal cut crosses it
    square. This is the one stroke a horizontal squash would thin, so it is the
    one that gets pinned."""
    k = max(range(5, 96),
            key=lambda j: runs(polys, y0 + (y1 - y0) * j / 100.0)[-1][1])
    return [b - a for a, b in runs(polys, y0 + (y1 - y0) * k / 100.0)][-1]


def Ze(pr, top=None):
    """З -- the digit three, which this typeface has already drawn, widened.

    In a grotesque the two are the same letter shape, and borrowing the real
    outline means З inherits the face's own curve, waist and terminals for
    free. Built from two generated arcs instead it had a visible seam where
    the lobes met, and the waist read as a break rather than a join.

    The panel says the borrowing is right and says so specifically. Structure:
    over the 51 faces that draw both, the two letters put their lobes in the
    same proportion -- 0.928 upper to lower for З against 0.926 for the three,
    middle halves overlapping -- and end their strokes at the same angles. The
    one construction that would disqualify a three is the flat-topped one, the
    three drawn with a straight diagonal shoulder: 13 of the 51 faces draw
    that, and no Cyrillic З in the panel does. This face's three is not one of
    them. Its upper terminal leans 1.97 at Thin and 2.21 at ExtraBold, inside
    a З population holding 1.61 to 2.02 and nowhere near the flat-topped
    three's 0.00.

    What does NOT come across is the width, and cloning the outline whole was
    taking it. Half the panel draws З wider than its own three, but that is
    not about З: the same faces draw O wider than their own 0 by the same
    amount, and З/3 measured against O/0 has a median of exactly 1.000. It is
    the digit set being drawn narrow, and this face does it too -- its digits
    widen 13% from Thin to ExtraBold where its capitals widen 18%. Cloned flat
    at the digit's width, З came out at 0.937 of O at ExtraBold against a
    panel bucket holding 0.974 to 1.007, and its own lowercase at 0.925 of o
    against 0.933 to 1.022. Both cases, one cause, the heavy end only.

    So the outline is the three's and the width is O's. `squash_x` puts the
    difference into the whites and leaves the wall alone -- the same instrument
    з uses, for the same reason: scaling the letter horizontally would thin the
    walls exactly the way scaling it vertically thins the bars.
    """
    src = [_flatten(p) for p in pr.paths("three")]
    xs = [q[0] for p in src for q in p]
    ys = [q[1] for p in src for q in p]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    want = round_w(pr, "O") * ZE_ROUND["cap"]
    wall = _ze_wall(src, x0, x1, y0, y1)
    out = squash_x(clone_all(pr.paths("three")), [(x1 - wall, x1)],
                   x1, x0 + want, x0)
    return translate(out, dx=300.0 - (x0 + want / 2.0))


def Ze_lc(pr):
    """з -- the same digit three, brought down to the lowercase.

    З is the face's own three and this is that same outline, because the
    alternative is the one thing already known not to work here: built from
    generated arcs the capital had a visible seam where the lobes met and the
    waist read as a break. There is no lowercase three to take instead, and no
    Latin lowercase of this shape at all, so the letter has to be *derived* --
    and derived is not scaled. A capital scaled down is the fault this project
    names first; what follows is a reweighting that happens to change the size.

    The face makes it awkward in a specific way. At Thin the two cases share
    their strokes exactly -- 29 and 29, 28 and 28 -- and differ most in the
    box, the lowercase being 0.884 of the capital's. At ExtraBold the box has
    nearly closed, 0.956, and it is the strokes that differ: 150 against 161
    and 106 against 135. So no single scale can serve, and neither can one
    scale per axis: on each axis the stroke and the size want different
    factors. Each axis therefore takes two stages -- the weight first, at the
    face's own ratio, then the size, with the stroke already correct and
    pinned so the second stage cannot touch it.

    Vertically that is `squash`, which was written for exactly this and has
    waited for its letter. Horizontally it is `squash_x`, the same trick
    turned on its side, which this is the first use of: a plain horizontal
    scale thins the walls the way a plain vertical scale thins the bars.
    """
    base = getattr(pr, "_pr", pr)
    src = [_flatten(p) for p in base.paths("three")]
    xs = [q[0] for p in src for q in p]
    ys = [q[1] for p in src for q in p]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)

    # The three horizontal strokes -- the crown of each lobe and the waist --
    # found rather than named, by cutting down the letter where it is flattest.
    # Anywhere in the middle third gives three clean runs; the flattest of them
    # is the one clear of every curve's turn.
    flat = min(((sum(b - a for a, b in v), v) for v in
                (vruns(src, x0 + (x1 - x0) * k / 100.0) for k in range(35, 56))
                if len(v) == 3), key=lambda t: t[0])[1]

    # ...and the one stroke whose thickness is measured across: the wall at
    # the lobes' widest, where a horizontal cut crosses it square.
    ymax = max(range(5, 96),
               key=lambda k: runs(src, y0 + (y1 - y0) * k / 100.0)[-1][1])
    wall = [b - a for a, b in
            runs(src, y0 + (y1 - y0) * ymax / 100.0)][-1]

    # The lowercase's own overshoot, off o -- not the three's, scaled by
    # accident. A round letter sits below the line and above it by a figure
    # this face holds across the case, and audit reads exactly that.
    ob = bbox(base.paths("o"))
    over = (-ob[1] + (ob[3] - base.xh)) / 2.0

    # y: the bars to lowercase weight, then the rest of the way to x-height.
    k = pr.bar / float(base.bar)
    out = piecewise_y(clone_all(base.paths("three")),
                      [(y0, -over), (y1, -over + (y1 - y0) * k)])
    bands = [(-over + (a - y0) * k, -over + (b - y0) * k) for a, b in flat]
    out = squash(out, bands, -over + (y1 - y0) * k, pr.cap + over, -over)

    # x: the walls to lowercase weight about the cell's centre, then the width
    # to the one the face's own o asks for. Not the box ratio, which is what
    # this took first and which carries the digit set's own narrowness: this
    # face widens its digits 13% from Thin to ExtraBold where its round letters
    # widen 18%, so the box ratio left з at 0.925 of o at the heavy end against
    # a panel holding 0.933 to 1.022. `ZE_ROUND` is the panel's own figure and
    # the capital takes the same reading against O -- see `Ze`. At ExtraBold
    # the first stage overshoots the width this asks for and the second widens
    # the letter back out, which is the same arithmetic run the other way and
    # needs no special case.
    ax0 = 300.0 + (x0 - 300.0) * pr.stem / float(base.stem)
    ax1 = 300.0 + (x1 - 300.0) * pr.stem / float(base.stem)
    out = scale_x(out, pr.stem / float(base.stem))
    want = round_w(base, "o") * ZE_ROUND["lc"]
    aw = wall * pr.stem / float(base.stem)
    out = squash_x(out, [(ax1 - aw, ax1)], ax1, ax0 + want, ax0)
    return translate(out, dx=300.0 - (ax0 + want / 2.0))


def Be_lc(pr):
    """б -- this face's own o for the bowl, Sudo's branch spliced onto it.

    Nine constructions were drawn for this letter and none of them was
    accepted, so the branch is no longer being drawn: it is taken from a face
    that already has it. Sudo is under the SIL Open Font License, which is
    what makes that legitimate, and it builds б the way this face's own six is
    built -- one stroke out of the bowl's left wall rather than a bowl hung on
    a stem.

    The BOWL is not the donor's, and taking it was the fault this letter cost
    a round to find. A donor's outline carries the donor's own design language
    and most of that language sits in the round parts: Sudo draws rounded
    rectangles, so its б counter fills 0.854 of its box exactly as its o does,
    and dropped into a face whose o fills 0.810 the same outline read 0.845.
    Sixty panel faces hold б's counter within 0.014 of their OWN o's, median
    0.001, at a counter width median of exactly 1.00 -- which makes the bowl
    the one thing about this letter that is settled before it is drawn. So the
    bowl is o, squashed to the height the donor gave it and spliced onto the
    branch where the donor's outline leaves the oval. See METHOD F11.

    Sudo's axis does not reach either end of this one -- its wall runs from a
    tenth of the x-height to just under a quarter, where this face needs a
    sixteenth and three tenths -- so its own axis is extrapolated point for
    point past both ends, and the branch's weight is solved against the
    donor's own bowl wall so it keeps the donor's proportion to a bowl of this
    weight. The letter is anchored on o, so the x-height, the overshoot and
    the baseline are this face's; stretched above the x-height on its own,
    because Sudo's б stands 1.34 x-heights and this face's lowercase stands
    1.50 to 1.57; and fitted to o's width, because the cell is not optional.

    `tools/be_donor.py` holds the result as frozen data -- its generator is
    retired -- and `tools/bowls.py` is the reading that judges it.
    """
    # The italic takes the ITALIC o's bowl, as д does. The roman б sheared
    # leant its counter 38-41 degrees against o's 17-26. At the donor's bowl
    # height Thin still read 37, because a shorter oval tips further under
    # the same slant (METHOD F29); `RISE_IT` in the retired generator raised
    # the bowl.
    base = getattr(pr, "_pr", pr)
    donor = BE_DONOR_IT if base.italic else BE_DONOR
    ps = [path([node(x, y, ty, sm) for x, y, ty, sm in c])
          for c in donor[base.mi]]
    ps.sort(key=lambda q: -abs(area(q)))
    return ([ps[0] if area(ps[0]) > 0 else reverse(ps[0])]
            + [q if area(q) < 0 else reverse(q) for q in ps[1:]])

def Ii(pr, top=None, bottom=0.0, donor="N"):
    """И -- two stems with a diagonal rising from the left foot to the right
    shoulder. Drawn, not N flipped: mirroring reverses the terminal cuts.

    `donor` is the face's own letter of the same construction, two stems with
    a diagonal between them, which settles the width and the stem weight as
    well as the junction. n takes over at x-height -- its arch is not И's
    diagonal, but its two stems stand exactly where и's must.
    """
    top = pr.cap if top is None else top
    m = L(pr)
    # N is not merely the model for the junction -- it is the same
    # construction, two stems with a diagonal between them, so it settles the
    # width and the stem weight as well. Sized as three stems in a row instead,
    # И came out lighter in the stem and wider in the cell than any of the
    # sixty faces on the panel, and fell below every one of them for weight.
    # WHERE THE STEMS STAND is the stance, not the donor's box, and in the
    # italic those are different numbers. `bbox` reads nodes, and un-shearing a
    # drawn italic swings its control points out past the curve; worse, an
    # un-sheared box is not a footprint, so drawing to it and then shearing
    # pays the slant twice. и came out 107 units wider than н at Regular from
    # exactly that, and overran its cell at ExtraBold, while the upright had
    # all three letters identical to the unit.
    #
    # `Lower` already answers this -- capL/capR is where a lowercase stem has
    # to be DRAWN so the shear lands it on n's own footprint, and н п ш ц all
    # take it. In the upright the stance is n's box to the unit, so this
    # changes nothing there. The capital keeps the donor's box: И is a sloped
    # upright in this face, as H and N are, and pays no slant to correct.
    if getattr(pr, "lower", False):
        x0, x1 = pr.capL, pr.capR
    else:
        nb = bbox(pr.paths(donor))
        x0, x1 = nb[0], nb[2]
    s = pr.stem_of(donor, (top - bottom) * 0.25)
    # The diagonal still takes the crowding reduction: three strokes cross the
    # cell at mid height, and at full weight it closes the counters.
    # N shows how this face lands a diagonal on a stem: the diagonal merges
    # into the stem so the two share one flat cut at the cap and one at the
    # baseline, and its inner edge stops a few units INSIDE the stem's inner
    # edge -- three of them at Thin, against a stem of twenty-nine. Aimed at
    # the stems' inner edges instead, which is what this did, the diagonal
    # hangs off the side of each stem; aimed at their centres it lands right on
    # the edge. Either way it leaves a hairline wedge of ink running up the
    # stem, which is the spike the sweep kept reporting at the light weights.
    d = s * m.crowd3
    w = d
    for _ in range(6):
        w = d * math.hypot(1.0, ((x1 - x0) - w) / (top - bottom))
    slope = ((x1 - x0) - w) / (top - bottom)

    # Where the diagonal leaves the stem it opens a wedge of white barely
    # wider than the diagonal's own slant -- the sharpest thing in the letter.
    # N does not leave it: it steps about a third of a stem across before the
    # diagonal starts, blunting the point. Same step here, at both junctions.
    def step(x_stem, y):
        t = 0.30 * s
        q = path([node(x_stem, y), node(x_stem, y + t),
                  node(x_stem + slope * t, y + t)])
        return q if area(q) > 0 else reverse(q)

    # Started exactly where the stem edge and the diagonal edge cross, the
    # step's apex is a point two outlines share -- exact at both masters and
    # not between them. Dropped a fifth of a stem lower it starts inside the
    # ink, where the drift cannot show.
    yc = s / slope - 0.2 * s
    return [rect(x0, bottom, x0 + s, top),
            rect(x1 - s, bottom, x1, top),
            diag(x0 + w / 2.0, bottom, x1 - w / 2.0, top, w),
            step(x0 + s, yc),
            mirror_x(mirror_y([step(x0 + s, yc)], (top + bottom) / 2.0),
                     (x0 + x1) / 2.0)[0]]


def Che(pr, top=None, bottom=0.0):
    """Ч -- a cup handing off to a full-height stem.

    This was three rectangles: a flat bar meeting a dead-vertical arm at a
    right angle. Every one of the sixty drawn faces on this machine TURNS
    there instead, carrying the arm's edge 0.09 to 0.26 of the advance round
    the corner -- and so does this face, whose L, J and U all sweep a vertical
    into a horizontal rather than butting the two together. With no turn at
    all the letter read as a bracket rather than a letter.

    Where the cup sits comes from SUSE's own Y, the one capital here whose
    upper structure hands off to a full-height stem: Y forks at 0.436 of cap
    light and 0.406 bold, which is also where the drawn Cyrillic puts Ч's bar
    (the panel's median is 0.390). The single thing Y cannot answer is how
    much white the cup has to keep, and at the heavy end that is what binds --
    Ч's bar is a full horizontal, half again the thickness of Y's junction
    band, so holding Y's height alone shut the counter to 0.355 of cap, under
    every face measured.
    """
    top = pr.cap if top is None else top
    x0, x1, s = fit_stems(pr, 2)
    h = top - bottom

    # the cup's floor: Y's own handoff, dropped only when the counter would
    # otherwise close under the thickening bar
    j = min(bottom + L(pr).yFork * h, top - CHE_COUNTER * h - pr.bar)
    floor = j + pr.bar

    # One corner on a long arm is exactly L's problem -- the same vertical
    # swept into the same horizontal -- so Ч takes L's corner outright, both
    # radii, rather than the reduced sweep П and Ш share for having two
    # corners close together. Deriving the inner one instead, as the outer
    # minus the stroke, gets it wrong at the heavy end: that subtraction goes
    # negative and squares the corner off, which is not what L does.
    ro = corner_radius(pr)
    ri = inner_radius(pr)

    # One contour, not a cup laid over a stem. The cup's floor and its
    # underside both end ON the stem's left edge, and as separate shapes those
    # two nodes would be exact at each master and adrift between them -- the
    # splinter of ink that has cost this file four other letters.
    ns = [node(x0, top), node(x0 + s, top), node(x0 + s, floor + ri)]
    ns += arc_to(x0 + s, floor + ri, x0 + s + ri, floor, x0 + s, floor)
    ns += [node(x1 - s, floor), node(x1 - s, top), node(x1, top),
           node(x1, bottom), node(x1 - s, bottom), node(x1 - s, j),
           node(x0 + ro, j)]
    ns += arc_to(x0 + ro, j, x0, j + ro, x0, j)
    p = path(ns)
    return [p if area(p) > 0 else reverse(p)]


def U(pr, top=None, bottom=0.0):
    """У -- two arms meeting a stem that stops ON the baseline.

    Every reference keeps У out of the descender: JetBrains 0..730, Iosevka
    0..690. Consolas and Fira dip 18 and 23 units, which is overshoot, not a
    descender -- their Д and Ц drop 283 and 294 for comparison.
    """
    top = pr.cap if top is None else top
    h = top - bottom

    # This was a Latin Y with a Cyrillic name: two arms meeting a VERTICAL
    # stem. In У the right arm does not stop at a fork -- it runs unbroken
    # from the top right down to the foot, and the foot therefore sits left of
    # centre. That single difference is what tells У from Y, and it was
    # missing. The foot's offset is a fifth of the advance, which is where
    # both weights of the reference put it.
    # The fork is not a thing to choose. Measured off a drawn У at two weights,
    # the two strokes carry the SAME slope -- the left arm is 1.10 times the
    # right one at Regular and at ExtraBold alike -- and everything else falls
    # out of that: where they merge, how deep the trough runs, where the fork
    # lands. Choosing a fork height instead is what went wrong twice. Aimed at
    # Y's fork the arm came in far shallower than the stroke it met and read as
    # splayed; aimed low enough to fix that it came in STEEPER than the stroke,
    # which is the opposite error and reads as a slanted V.
    arm = pr.stem * 0.95            # what Y gives an arm, measured
    wb = bbox(pr.paths(U_WIDTH))
    xa, xb = 300.0 - (wb[2] - wb[0]) / 2.0, 300.0 + (wb[2] - wb[0]) / 2.0
    foot = 300.0 - U_FOOT * 600.0

    # the right stroke: one straight run, top right corner to the foot
    sr = 0.45
    for _ in range(8):
        wr = arm * math.hypot(1.0, sr)
        sr = (xb - wr / 2.0 - foot) / (top - bottom)
    wr = arm * math.hypot(1.0, sr)
    wl = arm * math.hypot(1.0, U_LEAN * sr)

    def cr(y):
        return foot + sr * (y - bottom)

    def cl(y):
        return xa + wl / 2.0 + U_LEAN * sr * (top - y)

    def lin(f, want):
        """Height at which a linear quantity reaches `want`."""
        a, b = f(bottom), f(top)
        return bottom + h * (want - a) / (b - a)

    # Y closes the trough between its arms with a short horizontal flat rather
    # than a point, so the arm's inner edge stops there and steps across to the
    # right stroke, and only its outer edge carries on down to where the two
    # silhouettes become one. A tenth of a stem, not Y's near-half: Y can
    # afford a wide flat because its trough is deep, and У's is shallower. Cut
    # to Y's width the flat grew with the weight faster than the trough did,
    # until by Bold it read as a horizontal line across the middle of the
    # letter rather than as the bottom of a V.
    yf = lin(lambda y: (cr(y) - wr / 2.0) - (cl(y) + wl / 2.0), 0.10 * pr.stem)
    # Where the arm's outer edge crosses the right stroke's, the two outlines
    # coincide exactly -- and an exact coincidence at both masters is not an
    # exact coincidence between them, which left a one-degree splinter of ink
    # at Regular. Carrying the arm a quarter of a stroke further down buries
    # the meeting inside the right stroke, where drift cannot show.
    ym = lin(lambda y: (cl(y) - wl / 2.0) - (cr(y) - wr / 2.0), 0.0) - 0.25 * arm
    # Both of these have to land INSIDE the right stroke, not on its edge. The
    # trough's real bottom is then wherever the arm's inner edge actually meets
    # that edge, which stays true at every weight; put them on the edge exactly
    # and the drift between masters leaves a splinter of ink at Regular.
    bury = 0.35 * arm
    q = path([node(xa, top), node(xa + wl, top),
              node(cl(yf) + wl / 2.0, yf), node(cr(yf) - wr / 2.0 + bury, yf),
              node(cl(ym) - wl / 2.0, ym)])
    return [diag(cr(top), top, foot, bottom, wr),
            q if area(q) > 0 else reverse(q)]


def Ya(pr, top=None, bottom=0.0):
    """Я -- bowl at the top left, leg falling to the right.

    Drawn rather than R flipped, for the same reason as И.
    """
    top = pr.cap if top is None else top
    m = L(pr)
    x0, x1, s = fit_stems(pr, 2)
    # The face's own bowl, not m's three-stem reduction. A scanline across Я
    # crosses its bowl wall, the counter and the stem -- two strokes, exactly
    # what В's own bowl is -- so nothing crowds it. Carrying the reduction put
    # Я's bowl at 0.82 of В's at ExtraBold, below every one of the 51 panel
    # faces that draw both, whose median is 1.000. This is the same fault Ь and
    # Ъ were fixed for; Я was never in the family check to catch it, and the
    # check could not have seen it anyway -- it reads the rightmost run, and
    # Я's bowl bulges LEFT.
    sp = sloped(pr, caps=True)
    t = bowl_of(sp)[2]

    # R is the letter this face already built with a leg under a bowl, so R
    # says how one is done, per master: where the bowl stops, how far across
    # the bowl the leg springs from, and at what weight. The leg was carrying
    # a crowded-diagonal reduction and springing from the stem at 0.38 of the
    # cap -- lighter than the bowl above it and starting well below where the
    # bowl ends, so it read as a stroke laid against the letter rather than
    # growing out of it.
    rout = sp.paths("R")[0]
    rleg = sp.paths("R")[1]
    # R's bowl stops in one place and R's leg springs in another, and this
    # recipe took the second for the first. The leg's top edge is BURIED
    # inside the bowl's floor -- 13 units above it at Thin, 69 at ExtraBold --
    # so the two heights very nearly coincide at the light master and are a
    # tenth of the cap apart at the heavy one. Read as the bowl's floor, the
    # leg's height held Я's bowl at a flat 0.44 of cap while the stroke
    # crossing it grew five and a half times, and the counter closed from
    # 0.445 of cap to 0.085 -- against 0.28 in the panel and 0.305 in this
    # face's own R. F1: two figures that agree in one condition and not in
    # another.
    #
    # Node 11 is where R's bowl meets the stem on its outer underside, which
    # is what `waist` means here -- bowl_pair takes the bowl's OUTER bottom.
    # It falls with the weight, 0.449 of cap to 0.339, exactly as the panel's
    # own Я does and for the same reason: a bowl whose floor stays put has
    # nowhere to put a stroke that keeps growing.
    #
    # Both heights are absolute in CAP space, so they carry across as a
    # FRACTION of the letter and not as raw units. Handed to Lower as raw
    # units they left я's bowl 193 tall where the capital's is 400, and the
    # leg met it at a 42-degree spike against the face's own sharpest 46.
    # Same trap as Э cloning the Latin C: a number read off a capital does not
    # re-size because the recipe is run at x-height. And they live in two
    # spaces at once -- r_floor and r_legtop read R's own outline and stay in
    # R's units, while waist draws THIS letter and must be in its own.
    base = getattr(sp, "_pr", sp)
    r_floor = rout.nodes[11].position.y
    waist = r_floor / float(base.cap) * top
    r_legtop = max(n.position.y for n in rleg.nodes)
    # ...and R's leg again, this time the whole of it. What fixes where a leg
    # lands is how far its top edge stands off the STEM'S OWN EDGE, as a share
    # of the letter's width. The figure this replaces measured from the stem's
    # centre across a run that is a different length in the two letters --
    # R's leg reaches out to the letter's right edge, Я's to its left -- and
    # left Я's leg 29 units nearer its own stem than R's is to its. The white
    # wedge under the bowl closed to 0.26 of a stem at ExtraBold where this
    # face's own R holds 0.63 and the panel's Я 0.61.
    r_bbox = bbox(sp.paths("R"))
    r_inner = min(n.position.x for n in rleg.nodes
                  if n.position.y == r_legtop)
    standoff = ((r_inner - (r_bbox[0] + base.stem))
                / (r_bbox[2] - r_bbox[0]))

    # Я's bowl bulges LEFT against the right stem, so the shared d_shape --
    # which is drawn flat-left -- is flipped about this glyph's own centre.
    # That is mirroring my own construction, not deriving Я from a Latin R.
    # Я's bowl is half the letter, so it is short at x-height in exactly the
    # way в's lobes are: without the face's own sweep it flattens, and without
    # a floor its counter's corner collapses onto itself. See bowl_arc.
    # ...and the bowl's roof and floor are drawn at the BAR, not at the side
    # stroke. This face writes its horizontals lighter than its verticals --
    # 135 against 161 at ExtraBold -- and Б's bowl already says so. Insetting
    # this one evenly took another 62 units out of the same counter, on top of
    # the 69 the waist had cost it, and made Я's roof read heavier than the
    # arm of the Г beside it.
    leg_top = r_legtop / float(base.cap) * top
    # The lowercase bowl takes the soft sign's proportion -- see SOFT_RAISE.
    # The leg is R's, so it keeps springing from the same depth inside the
    # bowl's floor and simply starts lower with it.
    if getattr(pr, "lower", False):
        bh = min((top - waist) * soft_raise(pr),
                 SOFT_SHAPE * L(sp).lcBowlShape * (x1 - x0))
        leg_top -= waist - (top - bh)
        waist = top - bh
        c = (x0 + x1) / 2.0
        w = min(x1 - x0, bh / (SOFT_SHAPE * L(sp).lcBowlShape))
        x0, x1 = c - w / 2.0, c + w / 2.0
    mid = (x0 + x1) / 2.0
    rx, ry = bowl_arc(sp, x0, x1, waist, top)
    # ...and the lowercase counter turns over b's own share of its width, as
    # ь's does. Left to `r - t` it fell to 0.18 at ExtraBold against b's 0.43
    # -- F2 -- and the user marked the counter as a box.
    csweep = L(sp).lcCounterSweep if getattr(pr, "lower", False) else None
    bowl = mirror_x(bowl_pair(x0, waist, x1, top, t, th=pr.bar, r=rx, ry=ry,
                              rmin=inner_radius(pr), csweep=csweep,
                              lean=-bowl_lean(pr)), mid)

    # The leg spans from its top INNER edge, standing off the stem by R's own
    # figure, to its foot's OUTER edge on the letter's left -- R's leg lands
    # on its letter's edge and this one lands on the mirror of it. Both edges
    # are edges and not centres, so the solve carries half the leg's own
    # horizontal width at each end.
    # The leg is solved over the height R's own leg has, not over the height
    # of the bowl it hangs from. Those are two different runs -- R's leg top
    # sits 69 units up inside the bowl's floor at ExtraBold -- and solving the
    # slope over the shorter one made the leg meet the baseline in the same
    # place while leaning through a third less height, so it stood closer to
    # the stem all the way down. The wedge of white under the bowl read 0.38
    # of a stem against 0.63 in this face's own R.
    #
    # It also settles the splinter that a hand-set overshoot used to: the leg
    # ends where R's ends, which is inside the bowl at both masters -- 13
    # units at Thin, 69 at ExtraBold -- so the two outlines never share an
    # edge exactly, and cannot drift into one between the masters.
    #
    # Sheared, a stroke leaning down to the left comes out thinner than the
    # stem does -- 0.92 of it at Thin, 0.94 at ExtraBold, where the upright
    # leg is the stem to the unit. The shear keeps area, so a stroke along
    # (m, 1) keeps hypot(1, m) / hypot(1, m + k) of its width and the stem
    # keeps 1 / hypot(1, k); the leg is drawn wider by the ratio -- in Я too,
    # whose italic leg stood at 0.89-0.93 of the stem.
    leg_in = (x1 - s) - standoff * (x1 - x0)
    k = math.tan(math.radians(pr.italic))

    def leg_w(m):
        return pr.stem * math.hypot(1.0, m + k) / math.hypot(1.0, k)

    slope = 0.6
    for _ in range(8):
        hw = leg_w(slope)
        slope = ((leg_in - hw / 2.0) - (x0 + hw / 2.0)) / (leg_top - bottom)
    hw = leg_w(slope)
    return ([rect(x1 - s, bottom, x1, top)]
            + bowl
            + [diag(leg_in - hw / 2.0, leg_top, x0 + hw / 2.0, bottom, hw)])


# -- Ж ---------------------------------------------------------------------
# The construction was read off a professionally drawn monospace Ж (JetBrains
# Mono, Regular and ExtraBold), which turns out to be five straight strokes
# and nothing else:
#
#   * the centre stem is NOT lighter than the arms. JetBrains draws it at
#     0.87-0.95 of them and falling with weight, and that was taken as the
#     figure -- but across the 49 panel faces that draw Ж the ratio fits
#     1.033 + 0.011 * stem/em, which is flat at 1.03 over the whole axis.
#     JetBrains sits near the bottom of that population, so 0.86 generalised
#     one face's habit into a constant, which is the fault ф was found by.
#     The face agrees with the panel rather than with JetBrains: it does not
#     lighten a diagonal at all -- X runs 0.97 to 1.02 of H's stem at every
#     weight -- so there is no reason here for the one vertical stroke in the
#     letter to be the lightest thing in it. See ZHE_STEM.
#   * the upper pair of arms land on the stem ABOVE the middle and the lower
#     pair BELOW it, never at one point. The band between the two landings is
#     solid, and its height is 0.756 and 0.713 of a stem -- again near enough
#     constant at three quarters of a stem.
#   * that band sits at 0.519 and 0.516 of cap height, a touch above the
#     optical middle, exactly where this face puts X's waist.
# -- У ---------------------------------------------------------------------
# Both read off a drawn У at Regular and ExtraBold, and near enough identical
# at the two: the left arm leans 1.103 and 1.100 times as far as the right
# stroke, and the foot's centre sits 0.378 and 0.390 of the way across the
# letter. Everything else about the fork follows from those two.
# Only ONE number here comes from outside this typeface, and it is the one
# nothing inside it can answer: how far left of the middle У plants its foot.
# No Latin letter stands off-centre, so there is nothing to measure it against;
# a drawn У puts it a flat 61 units left at both weights, and that is taken.
#
# The other two are the face's own. It gives the two arms of Y exactly the same
# slope -- 0.678 against 0.681 at Thin, 0.510 against 0.531 at ExtraBold -- so
# У's arms get the same slope as each other too, rather than the tenth of a
# degree of asymmetry the reference happens to carry.
U_LEAN = 1.00
# And У takes V's width, not Y's. V is this face's own two-diagonal letter and
# the nearest thing it has to У, and it already draws narrower than Y at both
# weights. The width matters more here than anywhere: У's right stroke crosses
# from the top right corner down to that off-centre foot, so every unit of
# extra width is a unit of extra lean, and at Y's full span the whole letter
# tipped over into a slanted V.
U_WIDTH = "V"
U_FOOT = 0.102

# Centre stem, as a fraction of an arm. The panel's own figure, fitted over 49
# faces: 1.033 + 0.011 * stem/em, which is flat to a hundredth across the whole
# range, so a constant is the right shape here and not a relation waiting to be
# found. Taken at the fitted value rather than at a round 1.0 because the
# measurement carries a one to three per cent offset against the source ratio
# -- the panel's brackets are built with the same instrument, so the target has
# to be measured-inside-measured, and 1.0 re-measures at 0.97 against a Regular
# bracket that starts at 0.999.
ZHE_STEM = 1.033
ZHE_BAND = 0.73         # solid middle band height, as a fraction of an arm
ZHE_WAIST = 0.517       # its centre, as a fraction of cap height
ZHE_SHELF = 0.33        # arm-to-stem step, as a fraction of an arm


def Zhe(pr, top=None, bottom=0.0, stem=None, sb=None, shelf=None):
    """Ж -- a centre stem with four straight arms, symmetric about its middle.

    Not two К's. К's arm meets its stem low, at 0.29 of cap height, and its
    leg springs off the arm rather than off the stem, so К has no horizontal
    axis to be mirrored about; every version built from it crossed its arms
    below the middle and only held together at the heavy end, where the
    strokes were fat enough to hide it. Ж is symmetric top to bottom and the
    only way to get that is to draw it that way.

    The forms are all this face's own. Diagonals are cut flat at cap and
    baseline, the way X, V, W and K are cut. Nothing is rounded, because
    nothing here turns -- every meeting is two strokes crossing, which this
    face keeps square. Outside, each pair of arms crosses and the silhouette
    notches to a sharp point, which is what X does at its waist.
    """
    top = pr.cap if top is None else top
    h = top - bottom
    stem = pr.stem if stem is None else stem

    # three strokes cross the cell at the cap line, so the arms carry the same
    # reduction the face gives m's third stem against n -- and so Ж and Ш,
    # which sit side by side, come out the same colour
    arm = stem * L(pr).crowd3
    stem_c = arm * ZHE_STEM
    xL, xR = 300.0 - stem_c / 2.0, 300.0 + stem_c / 2.0

    # X says how far a diagonal letter may reach into the sidebearings here
    sb = bbox(pr.paths("X"))[0] if sb is None else sb

    waist = bottom + h * ZHE_WAIST
    band = arm * ZHE_BAND / 2.0
    up, lo = waist + band, waist - band

    # The arm's slope is not chosen: it is whatever gets the inner edge from
    # its flat top cut down to one short step short of the stem. Solved by
    # iteration because widening the arm for its own slant moves the top cut.
    shelf = max(6.0, ZHE_SHELF * arm if shelf is None else shelf * arm)
    reach = xL - shelf - sb
    s = 0.3
    for _ in range(8):
        s = (reach - arm * math.sqrt(1.0 + s * s)) / (top - up)
    width = arm * math.sqrt(1.0 + s * s)

    # The two arms on a side are reflections of each other in the waist, but
    # each is cut flat at the line it actually meets -- cap or baseline. Taking
    # the lower one as a straight mirror of the upper stops it 24 units short
    # of the baseline, because the waist is above the middle.
    def edge_up(y):
        return sb + s * (top - y)

    def edge_lo(y):
        return edge_up(2.0 * waist - y)

    def arm_at(flat, near, far, edge):
        # Each arm runs past its own landing on to the OPPOSITE one, so the
        # outer edges of the pair cross inside the shape and the notch between
        # them falls out of the overlap instead of having to be cut.
        q = path([node(edge(flat), flat),
                  node(edge(flat) + width, flat),
                  node(edge(near) + width, near),
                  node(xL, near),
                  node(xL, far),
                  node(edge(far), far)])
        return q if area(q) > 0 else reverse(q)

    left = [arm_at(top, up, lo, edge_up), arm_at(bottom, lo, up, edge_lo)]
    return ([rect(xL, bottom, xR, top)] + left
            + mirror_x(clone_all(left), 300.0))


# м's vertex, as a fraction of М's own -- each measured against its own line,
# so this is the shift the landmark takes across the case and nothing else.
# The panel's median over the 51 faces that draw both; its middle half is
# wide, 0.308 to 0.889, so the panel rules out the two extremes rather than
# fixing a value, and the median is the only figure inside that band it
# actually supports. Applied to this face's own М it puts the vertex at 0.206
# of the x-height at Thin and 0.182 at ExtraBold, against a panel median for
# м's vertex read directly -- a separate reading -- of 0.180.
EM_VERTEX = 0.639


def Em(pr, top=None, bottom=0.0):
    """м -- М's construction at x-height, rebuilt from M's own figures.

    М here IS the Latin M, a tier-1 donor, and Latin m is three arches, so
    unlike к there is no lowercase counterpart to take and the letter has to be
    built. What can still be inherited is every proportion: nothing below is
    chosen, all of it is read off M at this master.

    Four strokes -- two upright, two diagonal down to a vertex that stops well
    above the baseline. The vertex is cut FLAT rather than brought to a point,
    because that is what M does: its two diagonals stop level with the height
    at which their centrelines cross, which is this face's rule that two
    strokes crossing stay square.

    Across the 51 panel faces that draw both, м is 1.000 of М's width with the
    middle half inside seven thousandths, and М's uprights and м's carry the
    same reduction against their own case's stem -- 0.925 and 0.922. So the
    box and the weights come straight across; only the height changes.
    """
    top = pr.cap if top is None else top
    base = getattr(pr, "_pr", pr)
    h = top - bottom
    polys = [_flatten(p) for p in base.paths("M")]

    def cross(y):
        xs = []
        for pts in polys:
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 - y) * (y1 - y) < 0:
                    xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
        xs.sort()
        return [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]

    def line(ya, yb, idx):
        """Centreline and perpendicular width of one stroke between two cuts."""
        ra, rb = cross(ya), cross(yb)
        a, b = ra[idx], rb[idx]
        ca, cb = (a[0] + a[1]) / 2.0, (b[0] + b[1]) / 2.0
        s = (cb - ca) / (yb - ya)
        return ca, s, (a[1] - a[0]) / math.hypot(1.0, s)

    # The uprights, read low down where the diagonals have gone.
    low = cross(base.cap * 0.15)
    left, right = low[0][0], low[-1][1]
    upright = (low[0][1] - low[0][0]) / base.stem

    # The diagonals, read a quarter of the way into the band where all four
    # strokes stand apart. That band is 0.36..0.95 of cap at Thin and
    # 0.53..0.89 at ExtraBold, so any fixed height reads a merged run at one
    # of the two masters and gives the diagonal a slope it does not have.
    four = [j for j in range(5, 99) if len(cross(base.cap * j / 100.0)) == 4]
    ya = base.cap * (four[0] + (four[-1] - four[0]) * 0.25) / 100.0
    yb = ya + base.cap * 0.10
    la, ra_ = line(ya, yb, 1), line(ya, yb, 2)
    diag = (la[2] + ra_[2]) / 2.0 / base.stem
    mvert = (ya + (ra_[0] - la[0]) / (la[1] - ra_[1])) / base.cap

    # ...and how far into its upright the diagonal's outer top corner sits,
    # read off М by running its own centreline up to the cap line. It cannot
    # be read with a scanline: at the top the two shapes are one run, and the
    # corner in question is buried inside the upright.
    _cx = la[0] + la[1] * (base.cap - ya)
    inset = (_cx - la[2] * math.hypot(1.0, la[1]) / 2.0 - left) \
        / (upright * base.stem)

    # ...and rebuilt in this case's box, at this case's stroke.
    #
    # The uprights are М's own figure and nothing else. `crowd3` was applied
    # here as well and it is the wrong stroke to apply it to: М's 0.845 of the
    # stem IS this face's reduction for four strokes across a cell, so taking
    # m's three-stem reduction on top counted the same crowding twice and left
    # the uprights at 0.704 of n's stem at ExtraBold. The panel is tight on
    # exactly this figure -- over the 51 faces that draw both, м's upright
    # against n is 1.000 of М's against H, middle half inside 0.979 to 1.035 --
    # and the letter read visibly leaner than п and и beside it, which is what
    # 0.704 against their 1.000 looks like. See F3.
    us = upright * pr.stem

    # The diagonals do not take it either, and this was the second half of the
    # same fault. The argument for applying it here -- the box is М's, so the
    # same width is crossed over two thirds of the height and each diagonal
    # leans half again as hard -- describes something real, and `diag` has
    # already paid for it: it is read off М at this master, and М's diagonal is
    # ALREADY reduced to 0.62 of its own stem where the upright sits at 0.85.
    # That reduction is this face's answer for a stroke crossing a crowded
    # cell. Taking m's three-upright figure on top counted it twice, exactly as
    # it did for the uprights, and left the one stroke the first fix did not
    # reach at 0.495 of n at ExtraBold.
    #
    # The panel settles it in the same form the uprights were settled in --
    # the shift the figure takes across the case, since a lowercase diagonal is
    # lighter than its capital's in every face at once. Over the faces nearest
    # this weight, м's diagonal against n is 1.02 to 1.06 of М's against H,
    # middle half inside 0.97 to 1.07 at three of the four weights; not one
    # face in the bracket draws it LIGHTER than its own capital's. Ours was
    # 0.80. See `tools/diagonals.py` and METHOD F3.
    ds = diag * pr.stem

    # The vertex is М's own height, moved by the shift the panel gives that
    # landmark across the case: over the 51 faces that draw both, м's vertex
    # against its own x-height is EM_VERTEX of М's against its own cap. Both
    # diagonals run to (300, yv), so the flat cut sits exactly where their
    # centrelines meet -- М's own rule that two strokes crossing stay square,
    # and the reason the vertex is cut rather than pointed.
    yv = bottom + h * mvert * EM_VERTEX
    out = [rect(left, bottom, left + us, top),
           rect(right - us, bottom, right, top)]
    for sign, edge in ((1.0, left), (-1.0, right)):
        # Where the diagonal meets the top of its upright is М's figure too,
        # and it is not the upright's centre. Centring it there is what put a
        # step on BOTH sides of every upright at the x-height -- the diagonal
        # poking a unit past the outer edge at the light end and sinking
        # inside it at the heavy end, which reads as a nick in the corner
        # rather than as a stroke leaving a stem. М sets its diagonal's outer
        # top corner INSIDE the upright, so the outer edge runs clean to the
        # top and the whole junction opens inward: one step, on the side the
        # stroke is going.
        #
        # The top span's centre fixes the lean and the lean fixes the span's
        # width, so the two are solved together; three passes settle it to
        # well under a unit.
        x0 = edge + sign * inset * us
        hw = ds
        for _ in range(4):
            s = (300.0 - (x0 + sign * hw / 2.0)) / (yv - top)
            hw = ds * math.hypot(1.0, s)
        out.append(path([node(x0, top), node(x0 + sign * hw, top),
                         node(300.0 + sign * hw / 2.0, yv),
                         node(300.0 - sign * hw / 2.0, yv)]))
    return [p if area(p) > 0 else reverse(p) for p in out]


# К's junction, as a fraction of the letter's own height.
#
# This is ZHE_WAIST, written out rather than shared. Ж and К are the only two
# letters in this alphabet that hang an arm and a leg off one upright, they sit
# in the same words, and Ж is approved with its waist at 0.517 -- so К takes
# the same figure. It is copied and not referenced because a later change to Ж
# must not silently move an approved К; that is the rule Ґ cost.
#
# The panel arrives at the same number from outside. Of the faces whose Latin K
# branches and which redrew the Cyrillic rather than donating it, thirteen
# replaced the branch with a single vertex, and every one of them put that
# vertex between 0.503 and 0.534 of the cap -- Geist Mono 0.503, Lilex and
# Roboto Mono 0.509, Myna 0.519, Maple Mono 0.522, Hasklig 0.528. The nine that
# kept a branch are AverageMono, Courier New, Monaspace Xenon and Old Timey
# Code, at two weights each: serif and display faces. `tools/ka.py`.
KA_WAIST = 0.517

# How far out from the stem the arm and the leg part company, over the
# letter's own height. This is the figure that says a К is not a K.
#
# The arm and the leg do not meet the stem separately and they do not meet it
# at a point: they run together as ONE stroke for a short way, and that merged
# neck is what touches the stem. Read off the ink of every panel face that
# un-branches its К -- the leftmost point of the white wedge between the two
# strokes, out from the stem's right edge -- the neck is 0.181 to 0.272 of the
# cap for К and 0.260 to 0.398 of the x-height for к, and it barely moves with
# weight within a family: Lilex 0.262 to 0.250, Myna 0.237 to 0.238, Hasklig
# 0.267 to 0.270. The medians are taken. `tools/ka.py`.
#
# Two figures rather than one because the letter's height changes across the
# case and its width does not: к is wider for its height than К is, so the
# same fraction of the height would leave its diagonals flatter. Expressed
# against the WIDTH instead the panel is half as tight (0.28-0.49 against
# 0.18-0.27), so the height is the relation and this is the case's own value.
#
# The neck is also what sets the two leans, and therefore the sharpness of the
# corner where each stroke's flat cut meets it. Built without one -- with both
# strokes springing from a point on the stem -- every corner came out 33 to 44
# degrees against the face's own floor of 42, because the strokes had to cover
# the whole width from the stem in half the height. With it they land at 50 to
# 59, which is Roboto Mono's own К to the degree at both ends of its axis.
KA_NECK = 0.245         # К, over the cap height
KA_NECK_LC = 0.339      # к, over the x-height


def Ka(pr, donor="K", top=None, neck=KA_NECK):
    """К -- the arm and the leg meeting the stem at one point, at Ж's waist.

    This letter used to BE the Latin K, donated as a component, and the thing
    that made that wrong is not a proportion. K here branches: its leg leaves
    the arm out in the counter and the arm carries on underneath it down to the
    stem, so there are two strokes running beside the stem for a quarter of the
    cap height and the arm lands low -- 0.32 of the cap at Thin, sliding to
    0.43 at ExtraBold. Cyrillic К is one vertex, and it sits at the middle.
    That is a different letter, not a differently fitted one, which is why the
    ink-area reading could not see it and the overlay could.

    Everything except where the vertex goes is still the host's K, and that is
    the point of building it this way rather than drawing a К:

      * the arm and the leg keep their own PERPENDICULAR weight, taken off K's
        own flat end cuts and divided by the lean there -- so the strokes weigh
        what this face's diagonals weigh, at both masters, without a constant;
      * each keeps the extreme it reaches, so the letter fills the cell exactly
        as K does and needs no sidebearing of its own;
      * each is cut flat at the line it lands on, cap or baseline, the way X, V,
        W and K are cut, and buried in the stem with a vertical cut the way K
        buries its own arm.

    The slopes are what changes, and they are not chosen either: they are
    whatever gets a stroke of that weight from that extreme to the vertex.
    Solved by iteration because widening a stroke for its own lean moves the
    end it is being aimed from.

    What the two strokes do where they meet is the letter, and it is neither
    of the two obvious things. They do not each land on the stem separately --
    that crosses their outer edges inside it. They do not meet at a point on
    the stem either: that was built, and it forced both strokes to cover the
    whole width in half the height, which left every flat cut at a 33-to-44
    degree spike against the face's own floor of 42. They run together as one
    stroke for KA_NECK of the height and that merged neck meets the stem, over
    a band one horizontal bar tall -- so the two outer edges are cut flat and
    stepped in to the stem, exactly as Ж's four arms are.

    к is this construction against k and the x-height, not К squashed: k's own
    arm and leg carry the lowercase's diagonal weight already. The three
    contours are told apart by what they do -- the stem is the tall one, the
    arm is the one that reaches the top line -- never by their order, which is
    the sort of thing that means something different at the other master.
    """
    top = pr.cap if top is None else top
    ps = pr.paths(donor)
    stem = max(ps, key=lambda p: bbox([p])[3] - bbox([p])[1])
    sb = bbox([stem])
    rest = [p for p in ps if p is not stem]
    arm = max(rest, key=lambda p: bbox([p])[3])
    leg = [p for p in rest if p is not arm][0]

    def borrow(p, line):
        """(perpendicular weight, the extreme it reaches) where its own two
        edges arrive at the line.

        Read off the STROKE, never off whatever the donor put at the end of it.
        The upright's k ends both diagonals in a flat cut and the two readings
        are the same one; the italic's k ends its leg in the face's own foot --
        a slab 27 units tall and twice the stroke wide -- and taking the width
        across the nodes at the baseline returned a leg of 59.8 units against a
        stem of 30. The letter was built with it: к's italic leg came out at
        twice the weight of its own stem at Thin, and the user saw it on a
        screen before any reading here did, because nothing measures a
        diagonal ACROSS itself. METHOD F22.
        """
        ns = [n.position for n in p.nodes]
        if len(ns) > 4:
            # not a plain diagonal any more: the donor has drawn something onto
            # the end of it, and the stroke's own end is where its two long
            # edges arrive at the line
            sides = sorted((e for e in ((ns[i - 1], ns[i])
                                        for i in range(len(ns)))
                            if abs(e[1].y - e[0].y) > 1.0),
                           key=lambda e: math.hypot(e[1].x - e[0].x,
                                                    e[1].y - e[0].y))[-2:]
            edge = [((b.x - a.x) / (b.y - a.y), a.x, a.y) for a, b in sides]
            at = lambda e, y: e[1] + (y - e[2]) * e[0]
            other = max((q.y for e in sides for q in e),
                        key=lambda y: abs(y - line))
            ns = [Point(at(e, line), line) for e in edge] \
                + [Point(at(e, other), other) for e in edge]
        far = [n for n in ns if abs(n.y - line) < 1.0]
        near = [n for n in ns if abs(n.y - line) >= 1.0]
        fc = sum(n.x for n in far) / len(far)
        nc = sum(n.x for n in near) / len(near)
        ny = sum(n.y for n in near) / len(near)
        s = (fc - nc) / (line - ny)
        w = max(n.x for n in far) - min(n.x for n in far)
        return w / math.hypot(1.0, s), max(n.x for n in far)

    xv, yv = sb[2], top * KA_WAIST
    xa = xv + neck * top

    def stroke(p, line):
        """A stroke from the apex out to the extreme its donor reaches.

        Returns its lean, its horizontal width, and where its OUTER edge sits
        at the height the neck is cut at. Solved by iteration because widening
        a stroke for its own lean moves the end it is aimed from.
        """
        wp, R = borrow(p, line)
        s = 1.0 if line > yv else -1.0
        for _ in range(6):
            h = wp * math.hypot(1.0, s)
            s = (R - h - xa) / (line - yv)
        return s, wp * math.hypot(1.0, s)

    s_a, h_a = stroke(arm, top)
    s_l, h_l = stroke(leg, 0.0)
    # the band the merged neck meets the stem over: one horizontal, centred on
    # the junction. Below one bar the neck reads as a hairline joint at Thin;
    # above it the two shelves cross and the letter fills in.
    yT, yB = yv + pr.bar / 2.0, yv - pr.bar / 2.0
    # each outer edge is the inner one a stroke to its left, cut where the band
    # is. Clamped to the stem: at the heaviest master the shelf runs out.
    La = max(xv, xa - h_a + s_a * (yT - yv))
    Lb = max(xv, xa - h_l + s_l * (yB - yv))

    return [rect(sb[0], 0.0, sb[2], top),
            _ka_body(xv, yT, yB, La, Lb, xa, yv,
                     R_a=bbox([arm])[2], R_l=bbox([leg])[2],
                     h_a=h_a, h_l=h_l, top=top)]


def _ka_body(xv, yT, yB, La, Lb, xa, yv, R_a, R_l, h_a, h_l, top):
    """К's arm, leg and neck as one contour -- the shape Roboto Mono draws.

    Nine nodes, the same nine at every master, which is what a font that
    interpolates needs: up the stem's right edge, out along the top shelf, up
    the arm's outer edge to its flat cut, back down its inner edge to the
    apex, out along the leg's inner edge to ITS flat cut, and back along the
    leg's outer edge to the bottom shelf.
    """
    q = path([node(xv, yT), node(La, yT),
              node(R_a - h_a, top), node(R_a, top),
              node(xa, yv),
              node(R_l, 0.0), node(R_l - h_l, 0.0),
              node(Lb, yB), node(xv, yB)])
    return q if area(q) > 0 else reverse(q)



def lc(fn, **kw):
    """Run a recipe against the lowercase's own stem, bar and sidebearings.

    Cyrillic lowercase is largely small-capital in shape, so for these letters
    the CONSTRUCTION carries over unchanged -- and only the construction.
    Everything with a size or a weight in it comes from Lower instead: the
    x-height for the cap, 150 against 161 for the stem, 106 against 135 for
    the bar at ExtraBold. The same recipe run through Lower is a redrawing at
    lowercase weight, which is what the brief asks for; a vertical squash of
    the built capital is the scaled capital it rules out.
    """
    def run(pr):
        return fn(Lower(pr), **kw)
    return run


RECIPES = {
    "Ge-cy": Ghe, "Gheupturn-cy": Ghe_upturn, "Pe-cy": Pe, "Sha-cy": Sha,
    "Shcha-cy": Shcha, "Tse-cy": Tse, "Dzhe-cy": Dzhe, "El-cy": lambda pr: El(pr, outward=EL_OUTWARD),
    "De-cy": De, "Ef-cy": Ef, "Yu-cy": Yu, "E-cy": E_ukr, "Be-cy": Be,
    "Softsign-cy": Soft, "Hardsign-cy": Hard, "Yeru-cy": Yeru,
    "Ereversed-cy": E_rev, "Ze-cy": Ze, "Ii-cy": Ii, "Che-cy": Che,
    "U-cy": U, "Ya-cy": Ya, "Zhe-cy": Zhe, "Ka-cy": Ka,

    # ---- lowercase: the stem-and-bar block ----------------------------
    # г н т have no capital recipe to reuse -- Г splices E's nodes, Н and Т
    # are the Latin H and T unchanged, and none of the three has a lowercase
    # Latin counterpart to donate. The other five are their capital's own
    # construction driven through Lower.
    "ge-cy": lc(Ghe_lc), "en-cy": lc(En_lc), "te-cy": lc(Te_lc),
    "ve-cy": lc(Ve),
    "ef-cy": lc(Ef), "yu-cy": lc(Yu), "e-cy": lc(E_ukr),
    "gheupturn-cy": lc(Ghe_upturn_lc), "softsign-cy": lc(Soft), "hardsign-cy": lc(Hard),
    # the capital's own construction at x-height. These six need no donor
    # swap: they are built from measured parameters and geometry rather than
    # from spliced Latin outlines, so Lower alone re-sizes them.
    "de-cy": lc(De), "zhe-cy": lc(Zhe), "el-cy": lc(El, outward=EL_OUTWARD),
    "che-cy": lc(Che), "ereversed-cy": lc(E_rev), "ya-cy": lc(Ya),
    "yeru-cy": lc(Yeru),
    # Lower, not pr: the neck is a HORIZONTAL, and this face draws 61 there at
    # Regular where the capital draws 74. Run against the capital's bar the
    # signature gate reads к's neck at 1.21 of the face's own lowercase
    # horizontal -- the one number in the letter that has a weight in it, and
    # so the one that had to come from the lowercase's own view.
    "ka-cy": lambda pr: Ka(Lower(pr), "k", pr.xh, KA_NECK_LC),
    "em-cy": lc(Em),
    "ze-cy": lc(Ze_lc), "be-cy": lc(Be_lc),
    "pe-cy": lc(Pe), "sha-cy": lc(Sha), "shcha-cy": lc(Shcha),
    "tse-cy": lc(Tse), "ii-cy": lc(Ii, donor="n"),
}


# Recipes that differ under an ITALIC master, name -> fn. Anything absent
# falls back to RECIPES, which is right for all but a handful: run against the
# italic source, the same construction reads the italic's own donors and comes
# out a true italic on its own.
#
# Only the letters Cyrillic CURSIVE restructures belong here, and и п т are
# not among them -- they ARE the italic's own u n m, handled as tier 1 in
# `classify.ITALIC` rather than as a drawing.
ITALIC = {}


def Ge_cursive(pr):
    """г, taken whole from Lilex and fitted here -- `tools/ge_donor.py`.

    This letter was drawn twice from a SPINE read off the references and
    stroked at a constant width, and rejected twice. The second rejection is
    the one worth keeping: the spine was not what was wrong. Ink laid along a
    centreline has no modulation and no terminals, so it reads as bent wire
    whatever path it follows, and a perfect spine would have failed the same
    way. That is б's fault class exactly -- nine drawings refused, and what
    passed was not a better drawing but a donated outline. METHOD F15.

    So the outline is Lilex's -- the same donor as д's hook, which is one
    design language for the pair rather than two, and CFF, which matters: the
    first donation came off Sudo's variable TrueType and arrived as 34 nodes
    against this face's own o at 8. It measured right on every reading this
    project takes, because all of them read the ink, and as an outline it was
    machine spaghetti. Lilex draws the same letter in 16.

    There is nothing of this face to build it from:
    the cursive г is a top bar, a curve descending left and a foot running
    right, it has no bowl and no counter, and no Latin or Cyrillic letter in
    this family draws any part of it. c bulges the wrong way and mirroring is
    banned; з's lower terminal exits left where this one has to run right.
    What IS this face's is the height, the width, the cell, the terminal cut
    and the weight -- the retired `ge_from_lilex.py`, in git history, has each
    of them and where it was measured.
    """
    base = getattr(pr, "_pr", pr)
    out = []
    for c in GE_DONOR[base.mi]:
        q = path([node(x, y, ty, sm) for x, y, ty, sm in c])
        out.append(q if area(q) > 0 else reverse(q))

    # BOTH of Lilex's terminals are cut level, and neither of this letter's
    # strokes is upright, so neither cut is across the stroke it ends. The
    # foot runs out at 28 degrees and met its own cut at 34; the mouth climbs
    # away at 40 and met its own at 40. This face's own stems meet theirs at
    # 76 and its curved terminals at 77 to 87. `square_off` turns each cut
    # square to the stroke it ends and leaves it where it was.
    #
    # They are taken one at a time, and each is found again after the one
    # before it: a cut re-splices the contour, so an index read off the
    # donor is stale the moment the first terminal is replaced.
    for lo, hi, far in ((0.0, 0.35, max), (0.60, 1.00, min)):
        p0 = out[0]
        segs, on = _segments(p0)
        ends = lambda k: (segs[k][0].position, segs[k][2].position)
        want = [k for k in range(len(segs))
                if str(segs[k][2].type) == LINE
                and lo * pr.xh <= min(q.y for q in ends(k))
                and max(q.y for q in ends(k)) <= hi * pr.xh]
        if not want:
            raise ValueError("ge: a terminal is not where the donor left it")
        # the foot's is the rightmost of the low cuts, the mouth's the
        # leftmost of the high ones -- named by the letter, not by an index
        k = far(want, key=lambda k: sum(q.x for q in ends(k)))
        a, b = ends(k)
        out[0] = square_off(p0, on[(k - 1) % len(on)], on[(k + 1) % len(on)],
                            ((a.x, a.y), (b.x, b.y)),
                            math.tan(math.radians(pr.italic)))
    return out


GHE_TICK = 0.28         # ґ in the italic: the forelock's rise, in x-heights
GHE_LEAN = (0.25, 0.25)  # and how far it leans past upright, per master
GHE_WIDE = 0.95         # and how wide, in stems: 319 italics say 0.85-1.00


def Ghe_upturn_cursive(pr):
    """ґ in the italic -- the cursive г whose opening stroke turns up.

    Asked for on 2026-08-27: *"ґ italic should be the same as г but with
    forelock"*. Until then it was the upright ґ sheared, a corner with a tick,
    standing next to a г that is the cursive form -- one letter and its mark
    drawn in two hands.

    **The forelock goes where the stroke BEGINS.** Built first at the bar's
    right shoulder, which is where the upright's tick sits, and rejected: the
    cursive г's bar does not END there, it turns down into the body, so a tick
    standing on it reads as an ascender and the letter comes out a d. The
    user's sketch puts it on the left, which is how the letter is written by
    hand -- the tick is the first stroke, before the г.

    **And it is ONE stroke.** Built next as its own contour standing on the bar
    and overlapping it, which is this face's vocabulary for H and T, and
    rejected too: where the bar's terminal is cut at an angle, a straight-sided
    tick laid over it leaves its own corner sticking out past the ink. The
    user circled it. A turn has to REPLACE the terminal rather than sit on it,
    which is what the capital Ґ does with E's nodes and for the same reason.

    **And the terminal is not its base either.** Built next as a tick standing
    on that terminal -- its two edges rising from the cut's two ends -- and
    rejected by the heavy master: *"It becomes completely broken on extra
    bold, but overall shape looks right"*. The cut runs at about 63 degrees
    from horizontal and every forelock worth drawing runs between 55 and 76,
    so it is nearly parallel to the stroke standing on it and the span between
    its ends, taken across the tick, is three units at Thin and twelve at
    ExtraBold. A tick of any usable width has to reach far past that cut to
    find its second edge, and the ink between fills in as a wedge across the
    whole top left. At Thin every figure involved is under 24 units, which is
    why three rounds of correction went past it. METHOD F23.

    **And then the terminal became its base after all.** Squaring г's own
    two cuts -- *"Made square cut for lower leg but not the upper part"* --
    took the mouth from 63 degrees to 116, and F23's obstruction went with
    it: the cut now meets the tick at 52 to 57 degrees rather than lying
    along it, and the span between its ends, taken across the tick, is 10
    units at Thin and 58 at ExtraBold where it was 3 and 12. A base.

    That matters because the construction it forced was eating the letter.
    Drawn as a turn, the tick's inner edge crossed the bar's own top edge and
    everything past the crossing was dropped, so **ґ's bar was cut back by up
    to 68 units through its whole upper left at ExtraBold** -- nearly half a
    stem -- against г's. Read height by height, г's ink starts at 205, 172
    and 155 where ґ's starts at 249, 236 and 223. At Thin the two are within
    a few units, which is why it only reads wrong at weight: *"the upper
    elbow for ґ is shorter than г and it doesn't seem right, seems ґ is
    essentially г just with forelock"*.

    So it is now exactly that. г is taken whole, nothing of it is dropped or
    re-fitted, and the mouth's cut -- one straight segment, and the contour's
    closing one after squaring -- grows two edges and a cap. Two nodes are
    added at each master and nothing else moves.

    **The tick is therefore as wide as the mouth, and that is the price.**
    Both edges stand on the cut, so the width is the cut's own span across
    the tick: 0.36 of a stem at Thin and 0.39 at ExtraBold, against the 0.62
    and 0.50 it was drawn at while the bar was paying for it. It is the same
    width as the stroke it grows out of, which is what was asked for two
    rounds ago and could not be built then. What makes it thin at Thin is the
    donor's own taper, not this construction.

    It rises 0.28 of the x-height, the upright ґ's own figure and the panel's
    median for the letter, and leans `GHE_LEAN` past the face's own slant --
    *"forelock inclination should be bigger"* -- one number for both masters
    on the user's call, over a per-master pair the notch depth asked for.
    The cap is square to the tick, as the upright ґ's is at both masters.

    **The panel does not do any of this and was asked.** Of the ten italic
    monos here whose г is the cursive form -- Consolas, Inconsolata, Ioskeley,
    JetBrains, Lilex, Lyth, Monaspace Radon and Xenon, Sudo, Victor -- every
    one keeps ґ as the sheared upright corner. The user's call outranks it; the
    reading is recorded so the next round knows it was taken.
    """
    ps = Ge_cursive(pr)
    p = ps[0]
    ns = list(p.nodes)
    # Squaring the mouth left it as the contour's CLOSING segment, so the two
    # ends of the cut are the last node and the first, and the tick is two
    # nodes on the end of the list. Nothing is searched for and nothing is
    # dropped: this is г, with a detour inserted into one straight edge.
    if str(ns[0].type) != LINE:
        raise ValueError("ghe-upturn: г's mouth is not where it closes")
    a = ns[-1].position

    lean = GHE_LEAN[getattr(pr, "_pr", pr).mi]
    t = math.tan(math.radians(pr.italic))
    hyp = math.hypot(1.0, lean + t)

    # **The tick is a stem wide, and that is the panel's number, not a taste.**
    # Of the 319 italics on this machine that draw ґ, the upturn's width over
    # the face's own stem runs 0.85 to 1.00 between the quartiles with a
    # median of 0.96, and the thinnest reading in the whole set is 0.27.
    # Standing it on the mouth's cut made it 0.36 of a stem at Thin and 0.39
    # at ExtraBold -- outside the panel at the thin end, and the user saw it:
    # *"the forelock now is too thin"*. The rise is not in question: the
    # panel's median is 0.27 of the x-height against GHE_TICK's 0.28. Nor is
    # the lean: the italics that draw a cursive г rather than a sloped
    # upright -- Georgia, Cambria, Times, Monaspace Radon -- lean their tick
    # at 0.58 to 0.61 where ours leans at 0.50.
    w = GHE_WIDE * pr.stem

    # A tick wider than the mouth cannot stand ON the mouth: the cut IS the
    # bar's whole cross-section there, so a base longer than the cut runs out
    # past the bar's underside and hangs there as a spur. Where the ink
    # actually is, above the cut, is the bar's TOP edge -- so the tick's inner
    # edge comes down to meet that edge, and the meeting point is the elbow's
    # notch. That was always the right shape. What was wrong was splicing it
    # into г's outline, which deleted the bar's top edge beyond the notch and
    # took up to 68 units out of the letter's upper left. As its own contour
    # the same geometry only ADDS: the notch is where the tick stops, not
    # where the bar does.
    segs, _ = _segments(p)
    x_in = lambda y: a.x + w * hyp / (1.0 + t * (lean + t)) + (y - a.y) * lean
    k, ts = len(segs) - 2, []
    for back in range(3):
        k = (len(segs) - 2 - back) % len(segs)
        ts = meets_line(segs[k], x_in)
        if ts:
            break
    if not ts:
        raise ValueError("ghe-upturn: the tick's inner edge misses the bar")
    notch = _split_seg(segs[k], max(ts))[0][2].position

    # the cap is square to the tick -- the upright ґ caps this same tick at 90
    # degrees at both masters -- and its MIDDLE keeps the rise GHE_TICK asks
    # for, so squaring it does not make the letter taller on one side
    ytip = pr.xh * (1.0 + GHE_TICK)
    dy = w * (lean + t) / hyp
    ya = ytip + dy / 2.0
    xa = a.x + (ya - a.y) * lean
    xb = xa + w * (1.0 + t * (lean + t)) / hyp
    # The tick is its OWN contour, overlapping the letter, which is how this
    # family already builds El, Pe, Sha and д. Let into г's contour instead it
    # SUBTRACTS: its inner edge re-crosses the outline it was let into -- the
    # two strokes leave the mouth together, one at 40 degrees and one at 63 --
    # and the bump then runs against the letter's own winding there. It came
    # out as a bite taken from the upper left.
    #
    # It closes from the notch straight back to the cut's outer end rather
    # than following the bar's top edge, which is a chord under a rising
    # convex edge and so lies inside the ink: the union does not care, and
    # four nodes interpolate where a traced edge would not.
    tick = path([node(a.x, a.y, LINE), node(xa, ya, LINE),
                 node(xb, ya - dy, LINE), node(notch.x, notch.y, LINE)], True)
    return ps + [tick if area(tick) > 0 else reverse(tick)]


VE_WIDE = (1.33, 1.17)   # в in the italic: the letter's width, in o's widths
VE_BOWL = 0.74           # how much of that the bowl takes, measured from the left
VE_LOOP = 1.00           # and the loop -- the whole of it, corner to corner
VE_CROSS = (0.50, 0.55)  # where the loop's stroke meets the bowl, up the letter
VE_DIP = 0.10            # how far BELOW the crossing the loop's point is buried
VE_PINCH = 0.18          # and how narrow it is down there, in its own width
VE_LEAN = 0.45           # how far it leans past the face's own slant
VE_EYE = (0.46, 0.24)    # the eye, as a share of the loop's own box, per master


def Ve_cursive(pr):
    """в in the italic -- the bowl with a leaning loop stacked on it.

    Asked for on 2026-09-03 with a drawing: *"One of the canonical one looks
    like this"*. Until now the italic в was the upright в sheared -- a stem
    with two lobes hung off it -- standing in a set where г, д, і, ї, т and п
    are all the cursive forms. This is the letter as it is written by hand: a
    closed bowl, and above it a loop that leaves the bowl's left shoulder,
    rises to the right and comes back to the same place.

    **Two faces on this machine draw it and one of them is the sketch.**
    Monaspace Radon puts the join at 0.45 of the letter's height and takes the
    letter to 1.42 of its own x-height; Victor Mono draws the other reading, a
    small eye at 0.77 over a large oval. The user's drawing splits bowl from
    loop at 0.45, which is Radon's to a hundredth. Of the 321 italics here
    that carry в, those two are the only ones that leave the upright behind.

    **The height is this face's own, not Radon's.** b, l and б all top out at
    1.51 of the x-height at Thin and 1.45 at ExtraBold, and б is the sibling
    that matters -- a Cyrillic lowercase with a bowl and something rising off
    it. So в tops out on б's line. It makes в an ASCENDING letter, which is a
    change to the texture of every line rather than to one glyph, в being what
    it is in both languages; both reference faces do it and the sketch does
    it.

    **Both parts are `bowl`, which refits o's curve to a box at o's own
    stroke weight.** Scaling o down instead would thin its wall, and this face
    redraws stems at the target weight rather than shrinking a donor. They
    overlap and the union comes out on the way to the font, which is how El,
    Pe, Sha, д and ґ are already built.

    **Corrected 2026-09-11 -- the placement, not a dial.** *"current в looks
    like a 6-year old would write it... compare with Radon"*. It did, and the
    reason was that both boxes started at o's left edge with the loop the
    narrower of the two, so the letter was a small ring balanced on a large
    one. Radon does not nest them, it OFFSETS them: measured on the real
    outline, its bowl runs from the letter's left edge to 0.73 of its width
    and its loop from 0.20 across to the right edge, each about as wide as the
    other. What reads as one swept ribbon is two o-sized parts displaced along
    the diagonal, and what reads as a child's в is two parts sharing a left
    edge. `VE_BOWL` and `VE_LOOP` are that displacement; they sum past 1.0
    because the parts overlap in the middle, which is where the letter crosses
    itself.

    **The earlier figures in this recipe were read off the wrong file.**
    Windows splits Monaspace into subsets and the plain `MonaspaceRadon-*.otf`
    installed here carries no Cyrillic at all -- its в lives in the `_1`
    files. Read properly, Radon takes the letter to 1.48-1.58 of its own
    x-height, not the 1.42 recorded here, and puts the crossing at 0.54 of the
    letter's height at its light master rising to 0.61 at its heavy one, not a
    flat 0.45. The height was right anyway, being this face's own; the
    crossing was not, and `VE_CROSS` now carries the pair.

    **The letter is centred in its cell and allowed to spill.** At 1.33 of o
    it no longer fits between o's sidebearings. This face's italic already
    lets a lowercase out of its cell where the letter needs it -- f by 178
    units at ExtraBold, ж by 115, б by 66 -- so the idiom is there; centring
    rather than left-aligning splits the overhang between the two sides.
    """
    base = getattr(pr, "_pr", pr)
    ow = bbox(pr.paths("o"))
    top = bbox(pr.paths("b"))[3]
    w = VE_WIDE[base.mi] * (ow[2] - ow[0])
    x0 = (ow[0] + ow[2]) / 2.0 - w / 2.0
    cross = ow[1] + VE_CROSS[base.mi] * (top - ow[1])
    cup = bowl(pr, x0, x0 + VE_BOWL * w, ow[1], cross)

    # The loop runs DOWN INTO the bowl rather than sitting on it. Built to
    # start at the crossing it kept its own rounded bottom and the letter read
    # as a figure 8 -- two ovals stacked, which is what б already is. Dipped
    # below, the union swallows that bottom and what shows above the bowl is
    # the eye the reference draws.
    #
    # **The loop is anchored at BOTH corners, and that is the whole letter.**
    # Anchored only at its top right it came out a narrow leaf leaning off a
    # circle, because its descending stroke then landed in the MIDDLE of the
    # bowl's counter and cut it in two -- the letter had three whites, and the
    # third was the tell. Radon lands that stroke ON the bowl's left wall:
    # read band by band, at the bowl's widest the letter has one stroke there
    # doing both jobs, at 0.10 to 0.21 of the letter. So the loop runs corner
    # to corner, bottom left to top right, and its lean is what carries it
    # there; the box it is drawn in is narrower than the letter by exactly
    # what the lean adds back.
    # The point is buried just BELOW the crossing, not down at the baseline.
    # Taken as a share of the letter's height it reached the bowl's floor, and
    # the loop's whole lower half then lay across the bowl's counter -- the
    # taper made the crossing stroke a hairline instead of removing it. Where
    # the reference buries it is a tenth of the letter under the crossing, and
    # the two whites meet at that point rather than overlapping.
    dip = cross - VE_DIP * (top - ow[1])
    lw = VE_LOOP * w - (top - dip) * VE_LEAN

    # **The eye governs the wall, not the other way round.** Two walls at o's
    # own weight fit inside this box at Thin and eat all of it at ExtraBold,
    # where o draws its wall five times heavier for a letter barely wider --
    # the loop went solid black. `crowd` is the parameter `bowl` already has
    # for a letter carrying one stroke more than the round letter does, which
    # is what this loop does to the bowl it crosses. Capped at 1.0, so the
    # light master keeps o's wall untouched and only the heavy one gives way.
    tx = bowl_stroke(pr)[0]
    crowd = min(1.0, (1.0 - VE_EYE[base.mi]) * lw / (2.0 * tx))
    if crowd < 0.5:
        raise ValueError("ve: the loop's wall is thinner than half the bowl's")
    # **And it is pinched at the bottom, because an ellipse is not.** Refitted
    # to a tall box the round letter is rounded at BOTH ends, so the loop's
    # bottom arrived at the bowl a full box wide and cut the bowl's counter in
    # two -- three whites where the letter has two, at both masters. The pen
    # does not do that: it turns at the top, full width, and comes to a point
    # where it crosses itself. `taper` about the loop's own left edge, so the
    # descending stroke stays where the lean put it and only the right edge
    # closes on it.
    lx0 = x0 + (cross - dip) * VE_LEAN
    loop = bowl(pr, lx0, lx0 + lw, dip, top, crowd=crowd)
    loop = taper(loop, lx0, dip, top, VE_PINCH)
    loop = slant(loop, math.degrees(math.atan(VE_LEAN)), cross)
    return cup + loop


# в in the italic as ONE pen stroke -- `tools/ve/README.md`. Thin is L3 with
# the round top; ExtraBold is H, kept for now. Per master: the pen (wide,
# tall), the width the construction measures in, the loop's radius, how far
# along the bowl's top the loop lands (in those widths), the bowl's width and
# height against o's, and how much the loop's circle grows.
VP_PEN = ((28.0, 28.0), (148.0, 112.0))
VP_W = (28.0, 130.0)
VP_R = (70.0, 100.0)
VP_MERGE = (5.0, 1.8)
VP_WIDE = (1.25, 1.15)
VP_SCALE = (0.80, 0.92)
VP_LOOP = (1.35, 1.10)
VP_LEAN = 18.0      # the loop's axis, off the vertical
VP_TURN = 0.65      # the descending curve's handles, toward where its ends' directions cross
VP_STOP = 40.0      # degrees short of half-way round that the top circle ends


def Ve_pen(pr):
    """в in the italic, written as the copybook writes it -- one stroke.

    Rejected as two parts (`Ve_cursive`, two bowls; a leaf on an oval) and
    accepted as a pen path, 2026-09-16: *"this is a single stroke"*. Up the
    bowl's own left side and on as a straight line, round a circle at the
    top, down in one curve onto the bowl's top, and the bowl round once.

    * The bowl is this face's italic o's centreline, shrunk about its foot.
    * The line leaves the bowl at K, where the bowl already travels at the
      loop's lean, so the loop's left side IS the bowl's left side run on.
    * The loop lands on the bowl's top `VP_MERGE` widths past K and shares the
      bowl's stroke from there. Landing in solid ink at ExtraBold left the
      loop's white a point; landing late filled the waist Thin has.
    * ExtraBold's pen is oval, as its o is: 148 across, 112 up and down.

    Worked in italic space -- the top is a circle THERE -- and un-sheared on
    the way out, since the build shears every drawn glyph.
    """
    import pen as P
    mi = pr.mi
    stroke, w = VP_PEN[mi], VP_W[mi]
    o = slant(pr.paths("o"), pr.italic, pr.pivot)
    polys = sorted((P.flatten(p) for p in o), key=lambda q: -abs(sum(
        a[0] * b[1] - b[0] * a[1] for a, b in zip(q, q[1:] + q[:1]))))
    cl = P.centreline(polys[0], polys[1])
    ring_pts = [cl[0](2.0 * math.pi * i / 720) for i in range(720)]
    xs = [p[0] for p in ring_pts]
    foot = ((min(xs) + max(xs)) / 2.0, min(p[1] for p in ring_pts))
    bowl_c = P.scaled(cl, foot, VP_SCALE[mi] * VP_WIDE[mi], VP_SCALE[mi])
    at, vel = bowl_c

    th = math.radians(VP_LEAN)
    ax = (math.sin(th), math.cos(th))
    nm = (ax[1], -ax[0])

    def up_axis(t):
        dx, dy = vel(t)
        m = math.hypot(dx, dy)
        return -(dx * ax[0] + dy * ax[1]) / m
    tK = max((math.pi / 2 + (math.pi / 2) * i / 3600.0 for i in range(3601)), key=up_axis)
    K = at(tK)

    top = bbox(pr.paths("b"))[3] - w / 2.0
    r = VP_R[mi] * VP_LOOP[mi]
    s = (top - r - nm[1] * r - K[1]) / ax[1]
    PL = (K[0] + ax[0] * s, K[1] + ax[1] * s)
    Cc = (PL[0] + nm[0] * r, PL[1] + nm[1] * r)

    tQ, acc = tK, 0.0
    while acc < VP_MERGE[mi] * w:
        a, b = at(tQ), at(tQ - 1e-3)
        acc += math.hypot(b[0] - a[0], b[1] - a[1])
        tQ -= 1e-3
    Q = at(tQ)
    tq = P._unit(*vel(tQ))

    fE = math.radians(VP_STOP)
    E = (Cc[0] + r * (math.cos(fE) * nm[0] + math.sin(fE) * ax[0]),
         Cc[1] + r * (math.cos(fE) * nm[1] + math.sin(fE) * ax[1]))
    tE = (math.sin(fE) * nm[0] - math.cos(fE) * ax[0],
          math.sin(fE) * nm[1] - math.cos(fE) * ax[1])
    den = tE[0] * -tq[1] - tE[1] * -tq[0]
    u = ((Q[0] - E[0]) * -tq[1] - (Q[1] - E[1]) * -tq[0]) / den
    X = (E[0] + tE[0] * u, E[1] + tE[1] * u)
    h1 = (E[0] + (X[0] - E[0]) * VP_TURN, E[1] + (X[1] - E[1]) * VP_TURN)
    h2 = (Q[0] + (X[0] - Q[0]) * VP_TURN, Q[1] + (X[1] - Q[1]) * VP_TURN)

    down = P.bezier(E, h1, h2, Q)
    cuts = [0.0] + P.x_turns(down) + [1.0]
    fTop = math.pi / 2 + th
    loop = ([P.straight(P.line(K, PL)),
             P.arc(Cc, r, nm, ax, math.pi, fTop),
             P.arc(Cc, r, nm, ax, fTop, fE)]
            + [P.part(down, a, b) for a, b in zip(cuts, cuts[1:])])
    # the ring carries a node where the loop leaves it and where it lands, so
    # both parts pass through those points in the same direction
    ts = sorted(t % (2.0 * math.pi) for t in P.turns(bowl_c) + [tK, tQ])
    ts = ts + [ts[0] + 2.0 * math.pi]
    ring = [P.along(bowl_c, a, b) for a, b in zip(ts, ts[1:])]

    out, e1 = P.ring(ring, stroke)
    rib, e2 = P.ribbon(loop, stroke)
    out.append(rib)
    worst = max(e1, e2)
    Ve_pen.fit_error = worst
    return slant(out, -pr.italic, pr.pivot)


def De_cursive(pr):
    """д -- this face's own o for the bowl, Lilex's hook laid over it.

    б's recipe, part for part. A bowl is where a donor's design language sits
    (METHOD F11) and this letter is a bowl and one stroke, so the bowl is o
    itself -- which settles the counter, the overshoot, the x-height and the
    fitting for nothing -- and only the hook is donated.

    The hook is SPLICED, not laid over. It was laid over first, as its own
    contour overlapping the oval, and that reads as a stroke grazing a bowl
    rather than growing out of one: the junction measured 1.00 of the bowl's
    own wall at the heavy master against a panel running 1.13 to 1.41. What is
    missing in an overlap is the swell, and the swell is the piece of the
    donor's outline between where its stroke leaves the bowl and where it comes
    back -- which is exactly the piece an overlap throws away. So the outer
    contour here is one outline: this face's o everywhere except the arc the
    stroke covers, and the donor's there. `donor.splice`.

    Only the counter is still taken live off o. The outer is per-master data
    because the splice is solved against o at that master; if o is ever
    redrawn, the frozen outer no longer fits it (METHOD §9).

    What was here before all of that was a centreline stroked at a constant
    width, and it was rejected: ink laid along a spine has no modulation and no
    terminals. METHOD F15.
    """
    base = getattr(pr, "_pr", pr)
    counter = min(clone_all(pr.paths("o")), key=lambda q: abs(area(q)))
    out = []
    for c in DE_DONOR[base.mi]:
        h = path([node(x, y, ty, sm) for x, y, ty, sm in c])
        out.append(h if area(h) > 0 else reverse(h))
    return out + [counter if area(counter) < 0 else reverse(counter)]


def square_off(p, back, fwd, ends, t=0.0, turns=4, pull=0.15):
    """Recut a free terminal ACROSS the stroke instead of across the page.

    Every terminal this face draws is a horizontal cut, and on the upright
    stems it is drawn on that is the same cut as one taken square across the
    stroke -- the two readings coincide and neither has to be chosen. They
    come apart on a stroke running any other way, and cutting level then
    leaves a point. Measured in the shipped italic, н, п, т, ц, ш and щ meet
    their cuts at 76 degrees and the face's own curved terminals -- с, e --
    at 77 to 87, while the cursive г's foot met its own at 34 and і's at 40.
    That is the whole of what reads as a sharp leg.

    **Square is taken in the SHIPPED drawing, not in the upright one.** The
    shear is not a rotation and does not preserve angles: a cut drawn square
    to a slanted stroke before the shear is not square after it, and after is
    where the reader is. So the stroke's direction is sheared by `t`, squared
    there, and the perpendicular brought back -- which for an upright stem
    reduces to the level cut this face already draws, and to the 76 degrees
    that go with it.

    **The cut is anchored at the REAR end of the terminal it replaces**, not
    at its middle. A very oblique terminal is longer than the stroke is wide,
    so a square cut through its middle runs out past the tip on one side and
    crosses nothing there -- which is what the cursive г does, its foot cut
    lying at 45 degrees to its own stroke. Anchored at the rear end and
    pulled a little further back, the cut always fits inside the ink, and the
    letter can only get shorter. It gets shorter by a fraction of a terminal.

    It iterates because turning the cut moves where it crosses the two edges,
    which moves the direction it should be turned to -- but it is seeded from
    the edges' own ends, so the first guess needs no crossing to exist and is
    already close. Two passes settle it.

    Both edges are named, never searched, for the reason `cut_at_y` gives.
    """
    segs, on = _segments(p)
    ib, ia = on.index(back), on.index(fwd)

    def axis(ub, ua):
        """The stroke's own direction, pointing at the tip."""
        n1 = math.hypot(*ub) or 1.0
        n2 = math.hypot(*ua) or 1.0
        # the edges run opposite ways round the contour, so the stroke's own
        # axis is their difference and not their sum
        return ub[0] / n1 - ua[0] / n2, ub[1] / n1 - ua[1] / n2

    def square(u):
        sx, sy = u[0] + t * u[1], u[1]            # as the reader sees it
        cx, cy = -sy, sx                          # square, there
        cx -= t * cy                              # and back to the drawing
        if abs(cy) < 1e-9:
            raise ValueError("square_off: the cut comes out level")
        return cx / cy

    _, ub = seg_at(segs[ib], 1.0)
    _, ua = seg_at(segs[ia], 0.0)
    u = axis(ub, ua)
    n = math.hypot(*u) or 1.0
    rear = min(ends, key=lambda q: q[0] * u[0] + q[1] * u[1])
    step = pull * math.dist(ends[0], ends[1])
    at = (rear[0] - step * u[0] / n, rear[1] - step * u[1] / n)

    k = square(u)
    for _ in range(turns):
        x_at = lambda y, k=k: at[0] + (y - at[1]) * k
        tb, ta = meets_line(segs[ib], x_at), meets_line(segs[ia], x_at)
        if not tb or not ta:
            break
        _, ub = seg_at(segs[ib], max(tb))
        _, ua = seg_at(segs[ia], min(ta))
        kn = square(axis(ub, ua))
        if abs(kn - k) < 1e-4:
            k = kn
            break
        k = kn
    return cut_along(p, lambda y: at[0] + (y - at[1]) * k, back, fwd)


def flat_foot(pr, donor):
    """The face's own italic letter with its EXIT TAIL replaced by a flat foot.

    т and п are the italic's own m and n -- the cursive forms, which 10 of the
    29 monospace italics on this machine take and every one of them takes by
    mapping the codepoint straight to the Latin glyph. The forms are right and
    the panel backs them. What was wrong is the company: this face tails every
    italic lowercase stem, and our Cyrillic is built upright and sheared, so it
    is cut flat throughout. Three letters wearing the Latin's exit among a set
    that has none is two hands on one line, and it reads in a word before it
    reads on a sheet.

    Nothing here is drawn. In both letters only the LAST stem tails; every
    earlier one already ends flat -- n's left stem holds one stem's width at
    every height down to the baseline while its right swells by half as much
    again. So the foot being grafted on is the letter's own, at its own weight
    and its own slant, and the graft is mechanical: the last stem's two edges
    are long straight runs that stop early to make room for the tail, so each
    is continued down its own slope to the baseline and closed flat.

    и is NOT here. Its bowl arrives at the right stem exactly where the tail
    begins, so removing the tail leaves the bowl nothing to land on and the
    junction has to be re-fitted -- д's fault class, rejected five times over a
    concavity at that same handover. It stays the borrowed u, tail and all.
    """
    src = clone_all(pr.paths(donor))
    xh = pr.xh
    out = []
    for p in src:
        ns = list(p.nodes)
        low = [i for i, n in enumerate(ns) if n.position.y < 0.30 * xh]
        if not low:
            out.append(p)
            continue
        tip = max(low, key=lambda i: ns[i].position.x)

        xy = lambda i: (ns[i].position.x, ns[i].position.y)

        def edge(step):
            """Back out of the tail to the stem edge that runs into it.

            Found by the segment's RISE, not by a height: at ExtraBold the
            terminal's flat cut sits at the same height as the tail's tip, so
            anything keyed on height grabs the cut and reads a slope of zero.
            A stem edge climbs most of the x-height; a terminal cut climbs
            nothing.
            """
            i = tip
            for _ in range(len(ns)):
                i = (i + step) % len(ns)
                if str(ns[i].type) != "line":
                    continue
                _, y1 = xy((i - 1) % len(ns))
                _, y2 = xy(i)
                if abs(y2 - y1) > 0.20 * xh:
                    return i
            return None

        a, b = edge(-1), edge(1)
        if a is None or b is None:
            out.append(p)
            continue

        def to_base(i):
            """Where the edge arriving at node `i` reaches the baseline."""
            x1, y1 = xy((i - 1) % len(ns))
            x2, y2 = xy(i)
            return x2 + (0.0 - y2) * (x1 - x2) / (y1 - y2)

        x_in, x_out = to_base(a), to_base(b)
        keep = ns[:a + 1] + [node(x_in, 0.0), node(x_out, 0.0)] + ns[b:]
        out.append(path([node(n.position.x, n.position.y, n.type, n.smooth)
                         for n in keep]))
    return out


def Te_comb(pr, top=None):
    """т in the italic -- П's own construction with three stems.

    "ш turned over" is what it looks like, but nothing is turned over: `comb`
    draws n stems standing on a bar and П is already that comb flipped about
    its mid-height, so this is П's recipe with three stems instead of two. The
    face's own corner radius, bar weight and stem fit come with it, and every
    terminal is cut the way `comb` cuts one -- which is why this is not the
    mirroring CLAUDE.md forbids. И from a flipped N reverses cuts that were
    drawn to face one way; a comb is symmetric about the axis it is flipped
    on, and П has been approved built exactly like this.

    Chosen over the cursive form on 2026-08-25. The graft that preceded it --
    the italic m with its exit tail replaced, `flat_foot` below -- fixed the
    foot and left the shoulder: т and п closed over into an arch at the
    x-height where н, ш and ц are cut flat, most visibly at ExtraBold, where
    п's shoulder had closed by four fifths of the way up. The arch IS the
    cursive form, so there was nothing to repair without leaving it.
    """
    top = pr.cap if top is None else top
    x0, x1, s = fit_stems(pr, 3)
    return mirror_y(comb(pr, x0, x1, 3, s, top, pr.bar,
                         corner_radius(pr) * RADIUS), top / 2.0)


I_CUT = 0.30            # і: where the stroke stops, across the bowl's upswing
I_TILT = 2.0            # і: degrees of slant this letter carries over the face's


def I_cursive(pr, mark="dotaccentcomb"):
    """і -- one stroke: и's own, stopped where и turns up into its second stem.

    The Latin і was donated whole and it is the Latin's own italic i: an entry
    flag at the top left and a long flat foot, which is how this face ends
    every straight-stemmed lowercase it draws -- i, l, t, d, a all carry it.
    That is right for the Latin and wrong here. Our Cyrillic is built upright
    and sheared, so it is cut flat throughout with no entry and no exit, and
    one letter wearing the Latin's foot among a set that has none reads in a
    word before it reads on a sheet -- `flat_foot`'s argument, which took т
    and п off the cursive forms for the same reason.

    и went the other way, on the user's call: it stays the italic's own u,
    tail and all. і is cut from that same stroke, so the two letters are the
    same ink, but і does NOT keep the tail -- the user cut it twice, first the
    stub of the second stem and then the foot's flick: *"that little tale
    shouldn't be there"*. What is left is the stroke down, round the bowl, and
    up again far enough to read as a turn.

    The cut runs from the bottom of the bowl's outer edge to where the bowl
    leaves the stem -- both named, because the foot crosses any height three
    times and "the first crossing" is not a thing this recipe can mean (F21).
    Its height sits between the bowl's counter floor and where the bowl stops
    rising, two heights и carries at each master, so the same two segments are
    split at both and the node count matches by construction.

    **The terminal is out of band at the heavy end and that is known**: it
    measures about one and a half stems at Thin and about half a stem at
    ExtraBold, because и's bowl closes up as it gets heavy and there is no
    height where a cut across it is a stem wide at both masters. The letter
    was chosen over the reading; the ledger says so.

    The dot is the face's own combining mark, laid over the middle of the
    stroke's top cut, which is where the face puts it on its own i. ї is this
    letter under `dieresiscomb`; its base was `idotless` while і was the Latin
    and has to follow і now, or the pair reads as two hands.
    """
    src = clone_all(pr.paths("u"))[0]
    y = lambda i: src.nodes[i].position.y
    on = [i for i, n in enumerate(src.nodes) if str(n.type) != OFFCURVE]
    xh = max(y(i) for i in on)
    # the right stem's top cut: the contour walks left along it, so the run to
    # be dropped -- stem, foot and all -- starts here
    stem = on.index(max((i for i in on if abs(y(i) - xh) < 1.0),
                        key=lambda i: src.nodes[i].position.x))
    fwd = on[(stem + 2) % len(on)]              # the bowl leaves the stem
    floor = y(on[(stem + 3) % len(on)])         # the bowl's counter floor
    back = min(on, key=y)                       # the bottom of the bowl
    rise = y(on[(on.index(back) + 1) % len(on)])  # where the bowl stops rising
    # where the terminal sits is `I_CUT`'s question and is unchanged; HOW it
    # is cut is not. Cut level, on a stroke leaving at 40 degrees, it met its
    # own edge at 40 where this face's own terminals meet theirs at 76 -- a
    # point, and the same fault as the cursive г's foot. So the level cut is
    # taken only to find the place, and the cut that ships is square to the
    # stroke through that same middle.
    level = cut_at_y(src, floor + I_CUT * (rise - floor), back, fwd)
    ends = (level.nodes[-1].position, level.nodes[0].position)
    # і is slanted a further `I_TILT` below, so the drawing the reader sees
    # is sheared by both and squaring against the face's own angle alone
    # would leave the cut two degrees off
    body = square_off(src, back, fwd,
                      [(q.x, q.y) for q in ends],
                      math.tan(math.radians(pr.italic + I_TILT)))

    # Two degrees more slant than the rest of the face, on this letter alone,
    # chosen off a sheet of five (-4/-2/0/+2/+4) on 2026-08-27. It is a
    # departure and it is deliberate: the stroke already leans at the face's
    # own 14.0 degrees at every band -- the identical reading н, м and l give
    # -- so nothing was wrong with the angle as measured. What is short is the
    # STRAIGHT run. The face's own i holds its stem straight for 79% of the
    # x-height before it turns; this letter, cut out of и, turns at 57%,
    # because и's bowl has to start reaching for a second stem. A letter with
    # a short straight and a long curve does not declare an angle, and reads
    # as leaning less than its neighbours whatever it measures. Two degrees is
    # what it took to look level with them.
    t = math.tan(math.radians(pr.italic))
    if pr.italic:
        body = slant([body], math.degrees(math.atan(
            math.tan(math.radians(pr.italic + I_TILT)) - t)), pr.pivot)[0]

    # и's left sidebearing is и's, and и keeps a second stem to the right of
    # it. Cut that away and the letter hangs off the left of the cell: it
    # measured 203 against 298 for the face's own i at Regular Italic, and 187
    # against 295 at ExtraBold -- two thirds of a stem out of place, which is
    # what "the inclination looks off" turns out to be. A slanted stroke sitting
    # left of where its neighbours sit reads as tipped, not as displaced.
    # So it takes the host's own fitting: the same ink centre as `idotless`,
    # read at this master, in the space the letter is finally drawn in.
    xs = [x + (y - pr.pivot) * t for x, y in _flatten(body)]
    host = pr.ink("idotless")
    body = translate([body], (min(host) + max(host)) / 2.0
                     - (min(xs) + max(xs)) / 2.0)[0]

    top = sorted(n.position.x for n in body.nodes
                 if abs(n.position.y - xh) < 1.0)
    an = [a for a in pr.layer(mark).anchors if a.name == "_top"][0]
    ps = clone_all(pr.paths(mark))
    up_x = an.position.x - (an.position.y - pr.pivot) * t
    if pr.italic:
        e = math.degrees(math.atan(
            math.tan(math.radians(pr.italic + I_TILT)) - t))
        ps = slant(ps, e, pr.pivot)
        up_x += (an.position.y - pr.pivot) * math.tan(math.radians(e))
    return [body] + translate(ps, (top[0] + top[-1]) / 2.0 - up_x)


def Yi_cursive(pr):
    """ї -- і under the face's own dieresis."""
    return I_cursive(pr, "dieresiscomb")


ITALIC["ge-cy"] = Ge_cursive
ITALIC["de-cy"] = De_cursive
ITALIC["ve-cy"] = Ve_pen
ITALIC["gheupturn-cy"] = lc(Ghe_upturn_cursive)
ITALIC["te-cy"] = lc(Te_comb)
ITALIC["i-cy"] = I_cursive
ITALIC["yi-cy"] = Yi_cursive
# п is left OUT: with no italic override it falls through to the upright
# recipe, which is П's two-stem comb, and the shear does the rest.
#
# `flat_foot` above is kept and wired to nothing. It is the cursive graft this
# replaced, and putting either letter back is one line here.
