"""Everything the Latin can tell us about how this typeface behaves.

The first version of the Cyrillic composed rectangles using constants chosen
by eye -- a 0.16 leg splay, a 0.5 junction, a 0.32 counter. Those constants
were the defects. Ж, Ы, Л, Д and Ш were each wrong in the specific way a
made-up number is wrong.

Every question they answer badly is a question some Latin glyph in this same
font already answers well:

    how much does a crowded glyph narrow its stems?   m against n
    ... and four crowded diagonals?                   W against V
    at what height does a diagonal meet a stem?       K, Y
    how far does a leg splay?                         A, V
    how deep is a descender, and how does it end?     p, y, Q
    how does a bowl divide a cell against a stem?     B, R, D

So this module measures rather than decides. Nothing here is a design choice;
they are all readings off the existing outlines, per master, because Thin and
ExtraBold answer these questions differently.
"""

import math
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from params import _flatten                          # noqa: E402


def scan(pr, name, y):
    """x positions where a horizontal line at `y` crosses the outline."""
    xs = []
    for p in pr.paths(name):
        pts = _flatten(p)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            if (y0 - y) * (y1 - y) < 0:
                xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    return sorted(xs)


def strokes(pr, name, y):
    """(ink runs, gaps) along that scanline."""
    xs = scan(pr, name, y)
    ink = [b - a for a, b in zip(xs[0::2], xs[1::2])]
    gaps = [b - a for a, b in zip(xs[1::2], xs[2::2])]
    return ink, gaps


def vscan(pr, name, x):
    """y positions where a vertical line at `x` crosses the outline."""
    ys = []
    for p in pr.paths(name):
        pts = _flatten(p)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            if (x0 - x) * (x1 - x) < 0:
                ys.append(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
    return sorted(ys)


class Latin:
    """Measured behaviour of the typeface, per master."""

    def __init__(self, pr):
        self.pr = pr
        cap, xh = pr.cap, pr.xh

        # -- crowding -------------------------------------------------------
        # m is this face's own three-stem glyph and W its own four-diagonal
        # one. Whatever they do about a full cell is the answer for Ш and Ж.
        n_ink, _ = strokes(pr, "n", xh * 0.30)
        m_ink, m_gap = strokes(pr, "m", xh * 0.30)
        v_ink, _ = strokes(pr, "V", cap * 0.60)
        w_ink, w_gap = strokes(pr, "W", cap * 0.60)

        self.lcStem2 = n_ink[0]
        self.lcStem3 = m_ink[0]
        # how much a third stem costs, as a ratio -- 0.83 at ExtraBold, ~1.0
        # at Thin, where the cell never binds
        self.crowd3 = m_ink[0] / n_ink[0]
        self.counter3 = min(m_gap) if m_gap else None
        self.crowd4diag = (min(w_ink) / min(v_ink)) if v_ink else 1.0

        # the widest the face lets a capital be -- Y at both masters here, 565
        # units at Thin and 603 at ExtraBold, where it overhangs the cell. This
        # is the ceiling for Ф, the widest letter in the Cyrillic set.
        # Q is drawn from components in this source and reports no nodes of
        # its own, so the widths are collected from whatever actually has
        # outlines rather than assuming all 26 do.
        drawn = [self._bbox(pr, g)
                 for g in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if pr.paths(g)]
        self.capWidest = max(b[2] - b[0] for b in drawn)

        self.span2 = self._span(pr, "n")
        self.span3 = self._span(pr, "m")
        self.span4 = self._span(pr, "W")

        # -- junction heights ----------------------------------------------
        # where K's diagonals meet its stem, as a fraction of cap height
        self.kJoint = self._k_joint(pr)
        # where Y's arms fork
        self.yFork = self._y_fork(pr)
        # B's waist -- the height at which a two-lobe letter divides
        self.bWaist, self.bLobeStep = self._b_lobes(pr)

        # -- proportion of a stem-plus-bowl letter --------------------------
        # B: how much of the cell the stem takes and how much the bowl gets.
        # This is what Ы, Ь, Ъ and Б need and what they were guessing at.
        bx = self._bbox(pr, "B")
        self.bowlLeft = bx[0]
        self.bowlRight = bx[2]
        self.bowlWidth = bx[2] - bx[0]
        # B's bowl is drawn slightly HEAVIER than its own stem -- 30 against
        # 29 at Thin, 166 against 161 at ExtraBold. Ь Ъ Б hang that same bowl,
        # so this is their stroke. Taking the stem instead left them a few per
        # cent lighter than В standing next to them.
        _o, _c = pr.paths("B")[0], pr.paths("B")[1]
        self.bowlStroke = (max(n.position.x for n in _o.nodes)
                           - max(n.position.x for n in _c.nodes))
        # ...and the wall on the OTHER side is a different number, which is the
        # whole of this reading's reason. B spends `bowlStroke` on the side it
        # curves; on the left its counter sits against the stem, because there
        # is no second wall there. Insetting a bowl by `bowlStroke` on both
        # sides therefore draws a left wall B does not have, and Ь Ъ Б Ы each
        # lost the difference out of their counters -- nine units at ExtraBold,
        # which was exactly Ь's deficit against В.
        #
        # Measured on a SCANLINE rather than off the node box: a bowl's corner
        # puts its control points outside the counter, so `min(node.x)` reports
        # a counter wider than the curve by 14 units at ExtraBold. The same
        # trap `Ve` documents for the vertical, and it flatters this reading in
        # the direction that would hide the fault.
        self.bowlInset = self._inset(pr, "B", cap)
        self.bowlInsetStem = self.bowlInset / float(pr.stem)

        # -- the same questions again, at x-height ---------------------------
        # Cyrillic lowercase is largely small-capital in shape, which is
        # exactly why every one of these has to be asked again rather than
        # scaled: b's bowl is not B's, k's diagonals meet its stem at 0.31 of
        # the x-height at Thin and 0.10 at ExtraBold where K's barely move,
        # and the lowercase sidebearings are tighter. The crowding, counter,
        # span and descender figures above are already lowercase readings --
        # they come from n, m, p and y -- so they are not repeated here.
        bl = self._bbox(pr, "b")
        self.lcBowlLeft = bl[0]
        self.lcBowlRight = bl[2]
        self.lcBowlWidth = bl[2] - bl[0]
        # b's bowl comes out at exactly the lowercase stem at both masters,
        # where B's is a unit heavier than its own. Measured, not assumed.
        _lo, _lc = pr.paths("b")[0], pr.paths("b")[1]
        self.lcBowlStroke = (max(n.position.x for n in _lo.nodes)
                             - max(n.position.x for n in _lc.nodes))
        # b's left inset is NOT b's stem, and this is the half of the fault the
        # capitals do not have. b lets its counter cut ten units INTO the stem
        # -- 140 against a stem of 150 at ExtraBold, 28 against 29 at Thin --
        # so the bowl's inner curve runs on into the stem instead of stopping
        # against its edge. B does not: its counter sits exactly on the stem,
        # 157 against 157. Two donors, two answers, and taking the capital's
        # for both is the same fault in the other direction.
        self.lcBowlInset = self._inset(pr, "b", xh)
        self.lcBowlInsetStem = self.lcBowlInset / float(pr.lcStem)

        # How far the bowl SWEEPS: the horizontal reach of its outer arcs, as
        # a share of its own width. This is the face's roundness, and it is the
        # one thing B and b agree on across the case boundary -- 0.47-0.55 in B
        # against 0.45-0.49 in b at Thin, 0.33-0.51 against 0.31-0.41 at
        # ExtraBold. So the Latin reconciles a capital with its lowercase by
        # holding the sweep, and в has to as well: built from arcs that were
        # circular rather than elliptical it swept only 0.24, and its lobes
        # read as rectangles with rounded corners rather than as D-shapes.
        self.bowlSweep = self._sweep(pr, "B")
        self.lcBowlSweep = self._sweep(pr, "b")

        self.lcWidest = max(b[2] - b[0] for b in
                            (self._bbox(pr, g)
                             for g in "abcdefghijklmnopqrstuvwxyz"
                             if pr.paths(g)))

        # k's upper diagonal lands on its stem here, as K's does above
        self.lcKJoint = min(n.position.y
                            for n in pr.paths("k")[0].nodes) / float(xh)
        # and v is the lowercase's own two-diagonal letter, so it says how far
        # this face lets a leg travel sideways per unit of x-height
        self.lcLegSplay = abs(self._a_splay(pr, "v"))

        # -- descenders ------------------------------------------------------
        # depth and terminal width of the face's own descenders
        self.descDepth = -self._bbox(pr, "p")[1]
        yb = self._bbox(pr, "y")
        self.yTailDepth = -yb[1]
        self.yTailLeft = yb[0]
        # Width of y's tail where it ends -- across the stroke, not across the
        # page. The tail is a diagonal, and a horizontal scanline reports a
        # stroke leaning at angle t as 1/cos wider than it is: 266 units at
        # ExtraBold against a true 134. Nothing reads this yet, which is
        # exactly why it was worth correcting before something does.
        self.tailWidth = self._lean_width(pr, "y", -self.yTailDepth * 0.55)

        # -- diagonal splay --------------------------------------------------
        # A's left leg: how far this face lets a leg travel sideways over the
        # cap height. Л's splay was invented; this measures it.
        self.legSplay = self._a_splay(pr, "A")

        # How wide this face sets a lowercase letter against a capital, over
        # letters of the same construction -- straight-sided, flat-topped,
        # one or two stems. NOT lcWidest/capWidest: those are maxima over the
        # whole alphabet, so the capital side is Y at 565 and the ratio ends
        # up measuring how splayed the widest capital is rather than how the
        # two cases are spaced. The panel's reading of г's arm is normalised
        # by exactly this, and it has to be the same measurement here or the
        # comparison is meaningless.
        #
        # This face runs 1.06 at Thin down to 0.98 at ExtraBold -- the
        # lowercase starts wider than the capitals and ends narrower. Any
        # lowercase width derived from a capital's has to carry that, or it
        # drifts across the axis; see how г's arm did.
        self.lcCapWidth = (
            max(self._bbox(pr, g)[2] - self._bbox(pr, g)[0]
                for g in "nudbhkpqm" if pr.paths(g)) /
            max(self._bbox(pr, g)[2] - self._bbox(pr, g)[0]
                for g in "HNUDBEFKLPR" if pr.paths(g)))

    @staticmethod
    def _bbox(pr, name):
        xs = [n.position.x for p in pr.paths(name) for n in p.nodes]
        ys = [n.position.y for p in pr.paths(name) for n in p.nodes]
        return min(xs), min(ys), max(xs), max(ys)

    @staticmethod
    def _inset(pr, name, top):
        """How far the bowl's counter sits from the letter's own left edge.

        Swept rather than read at a fixed height, for the reason every probe
        here sweeps: the row where a bowl's counter is widest is not the same
        fraction of the height in B as in b, and a fixed line reads the corner
        in one of them. The widest row is taken because that is where the
        counter's left edge is furthest from the curve's influence -- above and
        below it the corner is closing and the reading is about the radius.
        """
        best = None
        for k in range(12, 89):
            xs = scan(pr, name, top * k / 100.0)
            if len(xs) < 4:
                continue
            w = xs[2] - xs[1]
            if best is None or w > best[0]:
                best = (w, xs[1] - xs[0])
        return best[1] if best else None

    @staticmethod
    def _lean_width(pr, name, at, d=12.0):
        """Thickness of the leftmost stroke at height `at`, across the stroke
        rather than across the page.

        Two corrections, and y's tail needs both. Where the stroke's centre
        travels between two heights gives its lean, and the lean gives a
        1/cos correction -- but that only helps a stroke that is more upright
        than not. Where the tail has flattened out, a horizontal scanline
        reports its LENGTH, and the honest thickness is how tall it is at that
        point: 266 units read flat, 257 after the lean, 134 read the way it is
        actually drawn.
        """
        xa, xb = scan(pr, name, at - d), scan(pr, name, at + d)
        if len(xa) < 2 or len(xb) < 2:
            return pr.stem
        w = ((xa[1] - xa[0]) + (xb[1] - xb[0])) / 2.0
        slope = ((xb[0] + xb[1]) - (xa[0] + xa[1])) / 2.0 / (2.0 * d)
        across = w / math.hypot(1.0, slope)
        ys = vscan(pr, name, (xa[0] + xa[1] + xb[0] + xb[1]) / 4.0)
        tall = min((hi - lo for lo, hi in zip(ys[0::2], ys[1::2])
                    if lo <= at <= hi), default=None)
        return across if tall is None else min(across, tall)

    @staticmethod
    def _sweep(pr, name):
        """Mean horizontal reach of the bowl's two widest outer arcs, over the
        bowl's width. Taking the two widest picks out the arcs that make the
        bowl's right-hand sweep and leaves the smaller ones where it meets the
        stem."""
        p = pr.paths(name)[0]
        ns = list(p.nodes)
        st = next((i for i, n in enumerate(ns) if n.type != "offcurve"), 0)
        ns = ns[st:] + ns[:st]
        prev, pend, dx = ns[0], [], []
        for n in ns[1:] + [ns[0]]:
            if n.type == "offcurve":
                pend.append(n)
                continue
            if n.type == "curve" and len(pend) == 2:
                dx.append(abs(n.position.x - prev.position.x))
            pend = []
            prev = n
        xs = [n.position.x for q in pr.paths(name) for n in q.nodes]
        dx.sort(reverse=True)
        return (sum(dx[:2]) / 2.0) / (max(xs) - min(xs)) if dx else 0.47

    @staticmethod
    def _span(pr, name):
        b = Latin._bbox(pr, name)
        return b[2] - b[0]

    def _k_joint(self, pr):
        """Height where K's diagonals meet the stem, over cap height."""
        k = pr.paths("K")
        # the upper diagonal's lowest node sits on the stem
        low = min(n.position.y for n in k[0].nodes)
        return low / float(pr.cap)

    def _y_fork(self, pr):
        y = pr.paths("Y")[0]
        ys = sorted({round(n.position.y) for n in y.nodes})
        # the fork is the lowest y shared by the two arms, above the stem foot
        return ys[1] / float(pr.cap) if len(ys) > 1 else 0.45

    def _b_lobes(self, pr):
        """Where B's two lobes meet, and by how much the join steps.

        Both come off the same feature.

        B is one outer contour that traces the lower lobe, steps back across
        the stem, and traces the upper: (307,367) to (307,355) at Thin,
        (374,363) to (371,358) at ExtraBold. That step IS the waist, and its
        midpoint lands on 0.516 and 0.515 -- the same figure at both masters,
        and the same one the panel's own в reports at a median 0.520.

        Two earlier readings were wrong, both by measuring something adjacent
        to the waist rather than the waist. A node index gave 0.429 at
        ExtraBold: that is the lower counter's top edge, which moves with the
        stroke. A scanline hunting for where the counter shuts gave 0.416,
        because B's counter is a single contour joined by a slit across the
        stem, so the crossing count never drops at the waist at all.

        The step's DEPTH matters as much as its height. It is what keeps the
        join square: the lower arc arrives horizontal, the outline drops 12
        units at Thin or 5 at ExtraBold, and the upper arc leaves horizontal
        again -- two right angles. Without it the two arcs meet tangentially
        and the join is a needle. See Ve.
        """
        ns = list(pr.paths("B")[0].nodes)
        for a, b in zip(ns, ns[1:]):
            if a.type == "offcurve" or b.type == "offcurve":
                continue
            y = (a.position.y + b.position.y) / 2.0
            dy = abs(a.position.y - b.position.y)
            if (abs(a.position.x - b.position.x) < 8
                    and 0 < dy < 0.1 * pr.cap
                    and 0.25 * pr.cap < y < 0.75 * pr.cap):
                return y / float(pr.cap), dy
        return 0.515, 0.017 * pr.cap

    def _a_splay(self, pr, name):
        """Horizontal travel of a diagonal letter's left leg over its full
        height, per unit height -- the face's own idea of how far a leg leans.

        Signed: A's leg leans out going down and v's leans in, so v comes back
        negative. Only the magnitude is the answer to how far, which is why
        the lowercase reading takes the absolute value.
        """
        a = pr.paths(name)[0]
        pts = [(n.position.x, n.position.y) for n in a.nodes]
        top = max(p[1] for p in pts)
        bot = min(p[1] for p in pts)
        xtop = min(p[0] for p in pts if p[1] > top - 0.12 * (top - bot))
        xbot = min(p[0] for p in pts if p[1] < bot + 0.12 * (top - bot))
        return (xtop - xbot) / float(top - bot)

    def report(self):
        p = self.pr
        return "\n".join([
            f"--- {p.master.name} ---",
            f"  stem cap/lc          {p.stem} / {p.lcStem:.0f}   bar {p.bar}",
            f"  crowding: 3 stems    stroke x{self.crowd3:.3f}  "
            f"counter {self.counter3:.0f}  span {self.span3:.0f} "
            f"(2 stems: {self.span2:.0f})",
            f"  crowding: 4 diagonals stroke x{self.crowd4diag:.3f}  "
            f"span {self.span4:.0f}",
            f"  K joint  {self.kJoint:.3f} cap     "
            f"Y fork {self.yFork:.3f} cap     B waist {self.bWaist:.3f} cap",
            f"  B bowl   x[{self.bowlLeft:.0f},{self.bowlRight:.0f}] "
            f"width {self.bowlWidth:.0f}",
            f"           wall {self.bowlStroke:.0f} on the side it curves, "
            f"inset {self.bowlInset:.0f} ({self.bowlInsetStem:.3f} stem) on "
            f"the side the spine is  --  b: {self.lcBowlStroke:.0f} and "
            f"{self.lcBowlInset:.0f} ({self.lcBowlInsetStem:.3f} lc stem)",
            f"  descender depth {self.descDepth:.0f}   y tail depth "
            f"{self.yTailDepth:.0f} left {self.yTailLeft:.0f} "
            f"width {self.tailWidth:.0f}",
            f"  leg splay {self.legSplay:.3f} per unit height",
            f"  lowercase: bowl x[{self.lcBowlLeft:.0f},"
            f"{self.lcBowlRight:.0f}] stroke {self.lcBowlStroke:.0f}   "
            f"widest {self.lcWidest:.0f}",
            f"             k joint {self.lcKJoint:.3f} xh   "
            f"leg splay {self.lcLegSplay:.3f} per unit height",
        ])


if __name__ == "__main__":
    import glyphsLib
    from params import Params
    f = glyphsLib.load(sys.argv[1] if len(sys.argv) > 1
                       else "sources/SUSEMono.glyphs")
    for mi in range(len(f.masters)):
        print(Latin(Params(f, mi)).report())
