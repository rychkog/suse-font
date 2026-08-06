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
                  area, LINE,
                  reverse, arc_to, corner_radius, inner_radius, bbox, squash,
                  fit)
from latin_metrics import Latin
from params import Lower

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
# ф's width at x-height, over the advance: the panel's own median across the
# 51 faces that draw it. The capital takes capWidest instead, being the widest
# letter the face allows.
EF_WIDTH = 0.863
# ...and its total height over the x-height, the panel's median across the same
# 51 faces.
EF_HEIGHT = 1.781
# ю: the clear run between its stem and its bowl, over the advance. The panel's
# lower quartile rather than its median -- at ExtraBold this face's stem is 150
# units of a 600 cell, and every unit given to the gap comes off the bowl.
YU_GAP = 0.129
EF_OVERHANG = 0.10      # Ф: how far the stem projects past the bowl, in cap
                        # heights. Borrowed for the same reason -- see Ef.

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
    m = L(pr)
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
    return body + [rect(px0, 0.0, px1, pr.bar),
                   rect(px0, -foot, px0 + s, pr.bar),
                   rect(px1 - s, -foot, px1, pr.bar)]


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
    widest = m.lcWidest if getattr(pr, "lower", False) else m.capWidest
    edge = (600.0 - widest) / 2.0
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
        ob = bbox(pr.paths(round_of(pr)))
        half = EF_WIDTH * 600.0 / 2.0
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
        st = pr.stem * m.crowd3
        return (bowl(pr, 300.0 - half, 300.0 + half, ob[1], ob[3],
                     crowd=m.crowd3)
                + [rect(300.0 - st / 2.0, foot,
                        300.0 + st / 2.0, foot + EF_HEIGHT * pr.cap)])
    mid = 300.0
    # How far the stem projects past the bowl. Borrowed, and marked as such:
    # no Latin letter here has a stroke crossing a bowl, and this face ships
    # no Greek, so there is no phi to ask. Every drawn face on this machine
    # puts it between 0.065 and 0.170 of cap and clusters hard on 0.10 --
    # JetBrains 0.100, Consolas 0.100, Monotional 0.083, DejaVu 0.083.
    oh = EF_OVERHANG * pr.cap
    return (bowl(pr, edge, 600.0 - edge, oh, pr.cap - oh)
            + [rect(mid - pr.stem / 2.0, 0.0, mid + pr.stem / 2.0, pr.cap)])


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
    tx, _ = bowl_stroke(pr)
    tx *= crowd
    # The clear run between the stem and the bowl. As 0.04 of the span this
    # was 21 units at ExtraBold -- 0.085 of the advance where the panel's
    # median is 0.173 and its lower quartile 0.129 -- and the connecting bar
    # was too short to read as a connection at all.
    # ...and the gap gives way before the bowl does. The bowl must hold two
    # strokes and the counter m already accepts between three stems; whatever
    # is left over is the gap's, up to the panel's figure.
    room = (x1 - x0 - s) - (2.0 * tx + L(pr).counter3)
    bx0 = x0 + s + max(0.0, min(YU_GAP * 600.0, room))
    # the bar sits on the case's own middle: midY is H's and does not travel
    bary = pr.barCentre * pr.cap - pr.bar / 2.0
    return ([rect(x0, 0.0, x0 + s, pr.cap),
             rect(x0, bary, bx0 + tx, bary + pr.bar)]
            + bowl(pr, bx0, x1, min(ys), max(ys), crowd=crowd))


def _mid_arm(pr, y=None):
    """E's middle arm, reused by Є and Э."""
    y = pr.midY if y is None else y
    e = pr.paths("E")[1]
    xs = [n.position.x for n in e.nodes]
    return rect(min(xs), y, max(xs), y + pr.bar)


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
    return clone_all(c) + [rect(x0, mid - pr.bar / 2.0,
                                x0 + (x1 - x0) * 0.73, mid + pr.bar / 2.0)]


def d_shape(left, bot, right, up, r, ry=None):
    """Flat on the left, semicircular on the right, as one contour.

    The straight run between the two arcs is emitted only when it has length.
    Where the radius is exactly half the height it has none, and leaving it in
    puts two coincident nodes at the widest point, which nicks the outline
    where the curve meets the straight.
    """
    ry = r if ry is None else ry
    ns = [node(left, bot), node(right - r, bot)]
    ns += arc_to(right - r, bot, right, bot + ry, right, bot)
    ns += [node(right, up - ry)]
    ns += arc_to(right, up - ry, right - r, up, right, up)
    ns += [node(left, up)]
    return path(ns)


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
    return rx, min((up - bot) / 2.0 * 0.97, rx)


def bowl_pair(left, bot, right, up, t, min_counter=24.0, th=None, rmin=1.0,
              th_bot=None, th_top=None, r=None, ry=None):
    """A d_shape and its counter, one even stroke apart, correctly wound.

    The stroke is clamped so the counter always has positive width AND
    height. Unclamped, Ы's bowl at ExtraBold came out narrower than two
    strokes: the counter inverted, its signed area flipped, and the
    orientation fix below then took the opposite branch in that master only --
    so the contour was wound one way at Thin and the other at ExtraBold, and
    the variable font would not interpolate. It looked fine at both masters.

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
    t = max(1.0, min(t, (right - left - min_counter) / 2.0))
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
    inner = d_shape(left + t, bot + th_bot, right - t, up - th_top,
                    max(r - t, rmin),
                    max(ry - (th_bot + th_top) / 2.0, rmin))
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
    m = L(pr)
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

    rx, ry = bowl_arc(pr, x0, x1, 0.0, top)
    body = bowl_pair(x0, 0.0, x1, top, t, th=pr.bar, r=rx, ry=ry,
                     rmin=inner_radius(pr))

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
    th = t * pr.bar / pr.stem
    waist, step = m.bWaist * top, m.bLobeStep
    upper = x0 + VE_UPPER * (right - x0)
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
    rx, ry1 = bowl_arc(pr, x0, right, 0.0, wl)
    xs = right - rx
    rx2 = max(upper - xs, 4.0)
    ry2 = min((top - wu) / 2.0 * 0.97, rx2)

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
    lo = d_shape(x0 + t, th, right - t, waist - th / 2.0,
                 max(right - xs - t, ri), max(ry1 - th, ri))
    up = d_shape(x0 + t, waist + th / 2.0, upper - t, top - th,
                 max(rx2 - t, ri), max(ry2 - th, ri))
    return [outer] + [reverse(c) if area(c) > 0 else c for c in (lo, up)]


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
    t = bowl_of(pr)[2]
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
    top = pr.cap if top is None else top
    bl, br, _ = bowl_of(pr)
    x0 = bl if x0 is None else x0
    right = br if right is None else right
    s = pr.stem if stem is None else stem
    t0, bt = soft_bowl(pr, top)
    tt = t0 if t is None else t
    rx, ry = bowl_arc(pr, x0, right, 0.0, bt)
    spine = (rect(x0, 0.0, x0 + s, top) if shoulder is None
             else shoulder_spine(pr, shoulder, x0, s, top))
    return ([spine]
            + bowl_pair(x0, 0.0, right, bt, tt,
                        th=tt * pr.bar / pr.stem, r=rx, ry=ry,
                        rmin=inner_radius(pr)))


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
    x0 = 300.0 - 267.0 + HARD_SHOULDER * 600.0
    # the bowl is Ь's, so it ends where Ь's ends -- B's own above and b's own
    # below. Only the stem moves right, to leave the shoulder its room, and
    # the shoulder's own length is a share of the CELL rather than of the
    # letter, so it carries across the case unchanged: the panel puts the
    # lowercase ъ's at 0.203 of the advance against this file's 0.20.
    return Soft(pr, top, x0=x0, right=bowl_of(pr)[1],
                shoulder=300.0 - 267.0)


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
    return (Soft(pr, top, x0=x0, right=x0 + s + YERU_SPLIT * gap + t,
                 stem=s, t=t)
            + [rect(x1 - s, 0.0, x1, top)])


def c_shape(pr, x0, x1, y0, y1, t, open_left):
    """A C, drawn -- not a mirrored Latin C.

    Traced as one closed contour: out along the top, round the closed side,
    back along the bottom, then in along the counter and back. `open_left`
    puts the aperture on the left for Э, on the right for Є's lowercase mate.
    Mirroring the Latin C would reverse its terminal cuts, which a Slavic
    reader sees immediately -- so the shape is built rather than flipped.
    """
    r = min((y1 - y0) / 2.0, (x1 - x0) * 0.5)
    ri = max(r - t, 1.0)
    sgn = 1.0 if open_left else -1.0
    # closed side is the right when the aperture is on the left
    cx0, cx1 = (x0, x1) if open_left else (x1, x0)
    ap = x0 + (x1 - x0) * 0.42 if open_left else x1 - (x1 - x0) * 0.42

    ns = [node(ap, y1), node(cx1 - sgn * r, y1)]
    ns += arc_to(cx1 - sgn * r, y1, cx1, y1 - r, cx1, y1)
    ns += [node(cx1, y0 + r)]
    ns += arc_to(cx1, y0 + r, cx1 - sgn * r, y0, cx1, y0)
    ns += [node(ap, y0), node(ap, y0 + t),
           node(cx1 - sgn * (ri + t), y0 + t)]
    ns += arc_to(cx1 - sgn * (ri + t), y0 + t, cx1 - sgn * t, y0 + t + ri,
                 cx1 - sgn * t, y0 + t)
    ns += [node(cx1 - sgn * t, y1 - t - ri)]
    ns += arc_to(cx1 - sgn * t, y1 - t - ri, cx1 - sgn * (ri + t), y1 - t,
                 cx1 - sgn * t, y1 - t)
    ns += [node(ap, y1 - t)]
    p = path(ns)
    return [p if area(p) > 0 else reverse(p)]


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
    return body + [rect(x1 - (x1 - x0) * 0.73, mid - pr.bar / 2.0,
                        x1, mid + pr.bar / 2.0)]


def Ze(pr, top=None):
    """З -- the digit three, which this typeface has already drawn.

    In a grotesque the two are the same letter shape, and borrowing the real
    outline means З inherits the face's own curve, waist and terminals for
    free. Built from two generated arcs instead it had a visible seam where
    the lobes met, and the waist read as a break rather than a join.
    """
    return clone_all(pr.paths("three"))


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
    m = L(pr)
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
    t = bowl_of(pr)[2]
    mid = (x0 + x1) / 2.0

    # R is the letter this face already built with a leg under a bowl, so R
    # says how one is done, per master: where the bowl stops, how far across
    # the bowl the leg springs from, and at what weight. The leg was carrying
    # a crowded-diagonal reduction and springing from the stem at 0.38 of the
    # cap -- lighter than the bowl above it and starting well below where the
    # bowl ends, so it read as a stroke laid against the letter rather than
    # growing out of it.
    rleg = pr.paths("R")[1]
    ys = [n.position.y for n in rleg.nodes]
    # R's leg springs at an absolute height in CAP space, so it carries across
    # as a FRACTION of the letter and not as raw units. Handed to Lower as it
    # stood it left я's bowl 193 units tall where the capital's is 400, and
    # the leg met it at a 42-degree spike against the face's own sharpest 46.
    # Same trap as Э cloning the Latin C: a number or an outline read off a
    # capital does not re-size just because the recipe is run at x-height.
    # Two heights, and they live in different spaces: r_waist reads R's own
    # outline and must stay in R's units, while waist draws THIS letter and
    # must be in its own. Rescaling the one variable that served both left the
    # node filter below matching nothing at all.
    base = getattr(pr, "_pr", pr)
    r_waist = max(ys)
    waist = r_waist / float(base.cap) * top
    r_top = [n.position.x for n in rleg.nodes if n.position.y == r_waist]
    r_stem = bbox([pr.paths("R")[0]])[0] + pr.stem / 2.0
    reach = ((sum(r_top) / len(r_top)) - r_stem) / (bbox(pr.paths("R"))[2]
                                                    - r_stem)

    # Я's bowl bulges LEFT against the right stem, so the shared d_shape --
    # which is drawn flat-left -- is flipped about this glyph's own centre.
    # That is mirroring my own construction, not deriving Я from a Latin R.
    # Я's bowl is half the letter, so it is short at x-height in exactly the
    # way в's lobes are: without the face's own sweep it flattens, and without
    # a floor its counter's corner collapses onto itself. See bowl_arc.
    rx, ry = bowl_arc(pr, x0, x1, waist, top)
    bowl = mirror_x(bowl_pair(x0, waist, x1, top, t, r=rx, ry=ry,
                              rmin=inner_radius(pr)), mid)

    stem_c = x1 - s / 2.0
    leg_top = stem_c - reach * (stem_c - x0)
    slope = 0.6
    for _ in range(6):
        hw = pr.stem * math.hypot(1.0, slope)
        slope = (leg_top - x0 - hw / 2.0) / (waist - bottom)
    hw = pr.stem * math.hypot(1.0, slope)
    # and the leg runs a little way UP into the bowl rather than stopping on
    # its edge -- an edge two outlines share exactly at both masters is not
    # shared exactly between them, and at ExtraBold that left a splinter
    over = 0.30 * pr.stem
    return ([rect(x1 - s, bottom, x1, top)]
            + bowl
            + [diag(leg_top + slope * over, waist + over,
                    x0 + hw / 2.0, bottom, hw)])


# -- Ж ---------------------------------------------------------------------
# Read off a professionally drawn monospace Ж (JetBrains Mono, Regular and
# ExtraBold), which turns out to be five straight strokes and nothing else:
#
#   * the centre stem is LIGHTER than the arms, 0.844 and 0.880 of them at the
#     two weights -- near enough constant, and the reason the middle does not
#     go black: it is the one stroke pressed on from both sides.
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

ZHE_STEM = 0.86         # centre stem, as a fraction of an arm
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
    "U-cy": U, "Ya-cy": Ya, "Zhe-cy": Zhe,

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
    "pe-cy": lc(Pe), "sha-cy": lc(Sha), "shcha-cy": lc(Shcha),
    "tse-cy": lc(Tse), "ii-cy": lc(Ii, donor="n"),
}
