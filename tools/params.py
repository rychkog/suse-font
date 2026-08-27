"""Per-master design parameters, measured from the Latin rather than declared.

Thin and ExtraBold differ in far more than stroke weight: the x-height moves
(472 -> 493), the sidebearings tighten (cap left 93 -> 59) and the corner radii
change independently of the stem. Hardcoding any of it would produce glyphs
that look right at one end of the axis and wrong at the other.
"""


import math                                                  # noqa: E402

from geom import slant                                       # noqa: E402


class Params:
    def __init__(self, font, mi):
        self.font = font
        self.mi = mi
        self.master = font.masters[mi]
        self.G = {g.name: g for g in font.glyphs}

        m = {mm.type: mv.position for mm, mv in zip(font.metrics, self.master.metrics)}
        self.cap = m["cap height"]
        self.xh = m["x-height"]
        self.asc = m["ascender"]
        self.desc = m["descender"]
        self.over = next(mv.overshoot for mm, mv in
                         zip(font.metrics, self.master.metrics)
                         if mm.type == "x-height")

        # The italic is a second source file with its own two masters and a 14
        # degree slope, and every recipe in this project is written in UPRIGHT
        # space: a stem is a `rect`, a bar is horizontal, `mirror_x` reflects
        # about 300. So the italic is built by un-shearing its Latin, running
        # the same construction, and shearing the result back. That reuses
        # every approved drawing rather than re-deriving it -- rule 1 -- and it
        # picks up the italic's OWN redrawn round capitals and its true-italic
        # lowercase for nothing, because a recipe reads `pr.paths(donor)` and
        # never the upright file.
        #
        # The pivot is the face's own and it is NOT the baseline: solved
        # against the eleven capitals that are a pure slant, it comes out at
        # y = 235 at Thin where the x-height is 472 and y = 245 at ExtraBold
        # where it is 493 -- xh/2 to within a unit at both masters. Shear about
        # the baseline instead and 300 stops being the middle of the cell in
        # the space the recipes are written in, which moves every anchor, every
        # mirror axis and every sidebearing this file reports.
        self.italic = getattr(self.master, "italicAngle", 0) or 0.0
        self.pivot = self.xh / 2.0

        # H is three rectangles: right stem, left stem, crossbar. That gives
        # the vertical stem, the horizontal bar and the cap sidebearings in
        # one glyph, all mutually consistent.
        h = self.paths("H")
        rstem, lstem, xbar = (self.box(p) for p in h)
        self.stem = lstem[2] - lstem[0]
        self.bar = xbar[3] - xbar[1]
        self.capL = lstem[0]
        self.capR = rstem[2]
        self.midY = xbar[1]
        self.barOverlap = lstem[2] - xbar[0]
        # H's bar does not run stem edge to stem edge -- it starts inside the
        # left stem and stops inside the right one, by 0.41 of a stem at Thin
        # and 0.49 at ExtraBold. Held as a fraction so н can take the same
        # inset against a lowercase stem.
        self.barInset = self.barOverlap / float(self.stem)
        # and its centre sits at 0.515 of the cap at both masters, which e's
        # own middle bar agrees with at x-height. A ratio, so it carries.
        self.barCentre = (xbar[1] + self.bar / 2.0) / float(self.cap)

        # E carries the rounded corner treatment that defines the face; Г, Ь,
        # Б and the rest reuse those exact nodes, so only the extents are
        # needed numerically.
        e = self.paths("E")
        self.eSpineOut = min(n.position.x for n in e[0].nodes)
        self.eArmEnd = max(n.position.x for n in e[0].nodes)

        # lowercase stem and sidebearings come from n, whose left stem is a
        # straight vertical run
        n = self.box(self.paths("n")[0])
        self.lcL = n[0]
        self.lcR = n[2]
        # measured halfway up the x-height, clear of l's bottom serif
        # and of n's arch
        self.lcStem = self.stem_of("l", self.xh * 0.5)

        # The lowercase horizontal, from t's crossbar -- f's agrees exactly at
        # both masters, and both sit with their top edge on the x-height. It
        # is NOT the capital bar: at ExtraBold this face draws 106 here
        # against the capitals' 135, so a Cyrillic lowercase squashed down
        # from its capital would carry a bar a fifth too heavy. That is the
        # single most common way a bolted-on Cyrillic gives itself away, and
        # no amount of holding bar height through the squash prevents it.
        self.lcBar = self.xh - self._bar_bottom("t")
        # and it reaches past the stems' sidebearings, the way T's bar reaches
        # past H's: 46..514 against n's 117..484 at Thin. т takes this extent.
        self.lcBarL, self.lcBarR = self._bar_span("t", self.xh - self.lcBar / 2.0)

    def paths(self, name):
        """The donor's outlines, STANDING UP.

        Under an italic master this hands back un-sheared clones, so that every
        reading in this file and every recipe that reads a donor works in one
        space. Clones and not the live paths: `slant` copies, but a caller that
        got the originals could mutate the source font.
        """
        ps = list(self.G[name].layers[self.mi].paths)
        return slant(ps, -self.italic, self.pivot) if self.italic else ps

    def layer(self, name):
        return self.G[name].layers[self.mi]

    @staticmethod
    def box(p):
        xs = [n.position.x for n in p.nodes]
        ys = [n.position.y for n in p.nodes]
        return (min(xs), min(ys), max(xs), max(ys))

    def stem_of(self, name, at):
        """Ink width of the first stroke crossed by a horizontal line at `at`.

        Reading stems off the sorted node x-values does not work: l's serifs
        and n's arch contribute nodes between the stem edges, and picking the
        smallest gap between them returns a 13-unit detail rather than the
        29-unit stem -- which then propagates into every rebuilt lowercase as
        a hairline. A scanline crossing measures the stroke that is actually
        there.
        """
        xs = []
        for p in self.paths(name):
            pts = _flatten(p)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 - at) * (y1 - at) < 0:
                    xs.append(x0 + (x1 - x0) * (at - y0) / (y1 - y0))
        xs.sort()
        return (xs[1] - xs[0]) if len(xs) >= 2 else self.stem

    def _vscan(self, name, x):
        ys = []
        for p in self.paths(name):
            pts = _flatten(p)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (x0 - x) * (x1 - x) < 0:
                    ys.append(y0 + (y1 - y0) * (x - x0) / (x1 - x0))
        return sorted(ys)

    def _bar_bottom(self, name):
        """Underside of the horizontal stroke whose top edge is the x-height,
        read clear of the stem so nothing else is in the way."""
        xs = [n.position.x for p in self.paths(name) for n in p.nodes]
        ys = self._vscan(name, min(xs) + 15.0)
        for lo, hi in zip(ys[0::2], ys[1::2]):
            if abs(hi - self.xh) < 2.0:
                return lo
        return self.xh - self.bar

    def ink(self, name):
        """A Latin letter's box AS DRAWN, which under an italic master is not
        the box `paths` hands back.

        `paths` un-shears, so every recipe can be written in upright space.
        That is right for a stem's weight and for a corner's radius, and wrong
        for a SIDEBEARING, because a sidebearing is a property of the letter
        the reader sees. This shears the un-sheared box back and reports where
        the ink really stands in the cell.
        """
        t = math.tan(math.radians(self.italic))
        xs = [x + (y - self.pivot) * t
              for p in self.paths(name) for x, y in _flatten(p, 24)]
        return min(xs), max(xs)

    def ink_right(self, name, y):
        """Where an edge must be DRAWN so the shear lands it on `name`'s own.

        `ink` says where a Latin letter's right edge stands. This says where to
        put a mark that will be sheared: ink drawn at height `y` travels
        `(y - pivot) * tan` to the right on its way back, so it has to start
        that much short of the target.

        The height is the whole of it. A recipe is written upright and its
        widest row is wherever its own construction puts it -- ь's is the
        straight run up its bowl, в's is its upper lobe, б's is its arm at the
        ascender -- and b's is b's. Two heights, one slant, and the difference
        comes out as a sidebearing that nothing in the upright can see.
        """
        return max(self.ink(name)) - (y - self.pivot) * math.tan(
            math.radians(self.italic))

    def _bar_span(self, name, at):
        """How far that same stroke reaches left and right."""
        xs = []
        for p in self.paths(name):
            pts = _flatten(p)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
                if (y0 - at) * (y1 - at) < 0:
                    xs.append(x0 + (x1 - x0) * (at - y0) / (y1 - y0))
        return (min(xs), max(xs)) if xs else (self.lcL, self.lcR)

    def __repr__(self):
        return (f"<{self.master.name}: cap={self.cap} xh={self.xh} "
                f"stem={self.stem} bar={self.bar} lcStem={self.lcStem:.0f} "
                f"capL={self.capL} capR={self.capR} lc=[{self.lcL},{self.lcR}]>")


class Lower:
    """A Params that answers with the lowercase's own figures.

    Same master, same outlines: `paths` still hands back the real Latin, so a
    recipe that reads L's corner or O's bowl gets exactly what it got before.
    What changes is every number saying how big and how heavy -- the cap
    becomes the x-height, the stem and bar become the lowercase's, and the
    sidebearings come from n rather than from H.

    Cyrillic lowercase is largely small-capital in SHAPE, which is what makes
    a vertical squash so tempting and so wrong. At ExtraBold this face draws a
    lowercase bar of 106 against the capitals' 135 and a stem of 150 against
    161. A compressed capital carries both of the heavier figures into a
    shorter letter and reads as a weight error rather than a size change --
    and holding bar height through the squash, which is what geom.squash is
    for, does not help, because the bar was the wrong weight to begin with.

    What is NOT rescaled is as deliberate. The corner radius stays exactly the
    capitals': this face's corner tracks stroke weight, not letter height --
    L's grows 103 to 122 as the stem goes 29 to 161 while the cap never moves
    at all -- and t and f put the same radius at x-height as at the ascender.
    The crowding, counter, span and descender readings in latin_metrics were
    already lowercase measurements, off n, m, p and y, so they need no view.

    `_pr` is the way back to the true master, for the two places that must
    read the Latin at its own size: L(), and diag_unit() reading K.
    """

    def __init__(self, pr):
        self._pr = pr
        self.lower = True
        self.cap = pr.xh
        self.stem = pr.lcStem
        self.bar = pr.lcBar
        # THE LOWERCASE STANCE IS NOT n's BOX.
        #
        # Every recipe here draws upright and the italic shears the result, so
        # a letter whose widest ink is at the x-height pays the whole slant in
        # its footprint -- about a fifth of the cell. **This face's own italic
        # lowercase does not pay it**, because it is a true italic and not a
        # sloped upright: n's widest ink is at the baseline, o's at a fifth of
        # the x-height, b's at a quarter. Its capitals ARE sloped uprights --
        # H stands 34..623 with its extremes at the baseline and the cap -- so
        # the capitals were never wrong and are not touched here.
        #
        # Handed n's own box and then sheared, н came out 0.98 of the cell
        # against the face's own italic n at 0.80, where the UPRIGHT н is n to
        # the unit. It showed as л н я reading wide beside и and п, which are
        # the italic u and n as components and so could not be wrong. Every
        # reference monospace holds н and и at one width; ours ran a quarter
        # apart.
        #
        # So the stance is derived from the FOOTPRINT n really occupies, less
        # the slant an upright-built letter will pick up over the x-height.
        # Under an upright master the slant is nothing and this is n's box
        # again, which is why there is one path and not two.
        l, r = pr.ink("n")
        half = 0.5 * (r - l - pr.xh * math.tan(math.radians(pr.italic)))
        self.capL = 0.5 * (l + r) - half
        self.capR = 0.5 * (l + r) + half
        self.barOverlap = pr.barInset * pr.lcStem

    def __getattr__(self, k):
        return getattr(self._pr, k)

    def __repr__(self):
        return (f"<{self._pr.master.name} lowercase: xh={self.cap} "
                f"stem={self.stem:.0f} bar={self.bar:.0f} "
                f"[{self.capL},{self.capR}]>")


def _flatten(p, steps=12):
    """Contour as a polygon, for scanline measurement."""
    ns = list(p.nodes)
    if not ns:
        return []
    start = next((i for i, n in enumerate(ns) if n.type != "offcurve"), 0)
    ns = ns[start:] + ns[:start]
    pts = [(ns[0].position.x, ns[0].position.y)]
    pend = []
    for n in ns[1:] + [ns[0]]:
        pt = (n.position.x, n.position.y)
        if n.type == "offcurve":
            pend.append(pt)
        elif n.type == "curve" and len(pend) == 2:
            p0 = pts[-1]
            c1, c2 = pend
            for s in range(1, steps + 1):
                t = s / steps
                mt = 1 - t
                pts.append((
                    mt**3 * p0[0] + 3 * mt * mt * t * c1[0]
                    + 3 * mt * t * t * c2[0] + t**3 * pt[0],
                    mt**3 * p0[1] + 3 * mt * mt * t * c1[1]
                    + 3 * mt * t * t * c2[1] + t**3 * pt[1]))
            pend = []
        else:
            pts.append(pt)
            pend = []
    return pts
