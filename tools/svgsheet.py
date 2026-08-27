"""Review sheets as SVG, carrying the font's own outlines.

A raster sheet is drawn at one size and resolved down, so a curve can only be
judged at the size that was picked -- and every join question ends in "render
it bigger". An SVG carries the path data itself: the same file answers whether
a join kinks at 12px and at 1200, and the reader does the zooming.

Three consequences for the rules in CLAUDE.md. Supersampling and Lanczos stop
applying, there being nothing to resolve. XOR-ing each contour so counters
punch through becomes `fill-rule="evenodd"` -- the same instruction given to
the renderer instead of carried out by hand, and exact where the XOR was exact
only to the pixel. And the reading-size rows need no trick at all: the PNG
sheet drew 12px and magnified it with NEAREST so that what grew was the pixel
grid rather than the outline, where here the line simply says 12px and the
viewer rasterises it the way a screen will.

EVERYTHING goes in as outlines, labels included. The file is opened on a
machine where this font is not installed, and a live text node there silently
falls back to something else -- a sheet showing the wrong typeface is the stale
picture fault in a new costume. Labels were exempted once, on the reasoning
that they are the sheet talking about itself rather than the specimen, and the
user caught it immediately: the fallback drew a tailed `l` and a two-storey `g`
across every heading, and on a specimen every Latin letter on the page reads
as the face. There is no cost to being strict -- a label letter is one more
`<use>` of a glyph the sheet already defines.

Every glyph is defined once and placed with `<use>`. One sheet sets the same
letter hundreds of times across weights and sizes, and inlining the path each
time is what makes a single-file specimen impossible.
"""
import glyphsLib
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

# The italic reaches past its cell on both sides, so a row needs air around it
# rather than the advance alone.
PAD = 60.0


class Face:
    """One built font, opened once -- outlines and advances come from here."""

    def __init__(self, path, key=None):
        self.path = path
        self.key = key or path.rsplit("/", 1)[-1].split(".")[0]
        self.font = TTFont(path, fontNumber=0, lazy=True)
        self.upem = self.font["head"].unitsPerEm
        self._gs = self.font.getGlyphSet()
        self._cmap = self.font.getBestCmap()
        self._hmtx = self.font["hmtx"]
        self._d = {}

    def has(self, ch):
        return ord(ch) in self._cmap

    def d(self, ch):
        """SVG path data for a character, in font units, y up."""
        if ch not in self._d:
            n = self._cmap.get(ord(ch))
            if n is None:
                self._d[ch] = ""
            else:
                pen = SVGPathPen(self._gs)
                self._gs[n].draw(pen)
                self._d[ch] = pen.getCommands()
        return self._d[ch]

    def advance(self, ch):
        n = self._cmap.get(ord(ch))
        return self._hmtx[n][0] if n else self.upem // 2

    def close(self):
        self.font.close()


class Faces:
    """Every weight and style, opened on first use and kept open once."""

    def __init__(self, pattern="fonts/ttf/SUSEMono-%s.ttf"):
        self.pattern = pattern
        self._open = {}

    def __call__(self, style):
        if style not in self._open:
            # The key has to name the FILE, not the weight. Keyed on the weight
            # alone, upright Regular and italic Regular are one entry in the
            # sheet's glyph table and the italic silently renders upright.
            path = self.pattern % style
            self._open[style] = Face(path, key=path)
        return self._open[style]

    def get(self, style):
        """The face, or None if that build does not have it.

        A build compared against is whatever was stashed, and an older one can
        predate a whole style. The caller skips the row; a comparison sheet
        that dies because half of it is missing shows nothing at all.
        """
        try:
            return self(style)
        except (IOError, OSError):
            self._open[style] = None
            return None

    def close(self):
        for f in self._open.values():
            if f is not None:
                f.close()
        self._open.clear()


def source_d(path, glyph, master):
    """Path data for a glyph as it stands in a .glyphs source.

    For the before half of a comparison, where the only copy of the old letter
    is the source `git show` hands back and there is no font to open.
    """
    font = glyphsLib.load(open(path))
    g = {x.name: x for x in font.glyphs}[glyph]
    out = []
    for p in g.layers[master].paths:
        nodes = list(p.nodes)
        starts = [i for i, n in enumerate(nodes) if str(n.type) != "offcurve"]
        if not nodes or not starts:
            continue
        # Glyphs stores a closed contour with no explicit start, so the run has
        # to begin at the last on-curve node and wrap.
        s = starts[-1]
        nodes = nodes[s + 1:] + nodes[:s + 1]
        d = ["M%.1f,%.1f" % (nodes[-1].position.x, nodes[-1].position.y)]
        off = []
        for n in nodes:
            if str(n.type) == "offcurve":
                off.append(n)
            elif off:
                pts = off + [n]
                d.append(("C" if len(pts) == 3 else "Q") + " ".join(
                    "%.1f,%.1f" % (q.position.x, q.position.y) for q in pts))
                off = []
            else:
                d.append("L%.1f,%.1f" % (n.position.x, n.position.y))
        out.append(" ".join(d) + "Z")
    return " ".join(out)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Sheet:
    """Sections stacked down the page, each drawn in font units and scaled."""

    def __init__(self, width, title="", label=None, label_bold=None):
        # The face the sheet's own words are set in. Its own, so that nothing
        # on the page is a substitute -- see the module docstring.
        self.label = label
        self.label_bold = label_bold or label
        self.width = width
        self.title = title
        self.body = []
        self.defs = {}
        self.y = 20.0

    # ---- glyph placement ------------------------------------------------

    def _ref(self, face, ch):
        """Define this letter once; hand back the id to point at."""
        key = (face.key, ch)
        if key not in self.defs:
            d = face.d(ch)
            if not d:
                return None
            self.defs[key] = ("g%d" % len(self.defs), d)
        return self.defs[key][0]

    def _put(self, face, ch, x, base, k, fill, extra=""):
        i = self._ref(face, ch)
        if i:
            self.body.append(
                '<use href="#%s" transform="translate(%.2f,%.2f) '
                'scale(%.6f,-%.6f)%s" fill="%s"/>'
                % (i, x, base, k, k, extra, fill))

    def width_of(self, face, text, px):
        k = px / float(face.upem)
        return sum(face.advance(c) for c in text) * k

    # ---- rows -----------------------------------------------------------

    def gap(self, h=10.0):
        self.y += h

    def rule(self):
        self.y += 6
        self.body.append('<line x1="0" y1="%.1f" x2="%d" y2="%.1f" '
                         'stroke="#e6e6e6"/>' % (self.y, self.width, self.y))
        self.y += 10

    def vrule(self, x, y0, y1):
        """The boundary between two columns of the same rows.

        Adjacent is the whole point of a comparison band -- a tenth of a stem
        is invisible between two pictures a screen apart -- so the two columns
        are set close, and something has to say where one ends.
        """
        self.body.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" '
                         'stroke="#e0e0e0"/>' % (x, y0, x, y1))

    def _words(self, face, text, x, base, px, fill):
        """A run of the sheet's own words, drawn as outlines like everything else."""
        if face is None:
            self.body.append(
                '<text x="%.1f" y="%.1f" font-family="ui-monospace,monospace" '
                'font-size="%d" fill="%s">%s</text>'
                % (x, base, px, fill, esc(text)))
            return
        k = px / float(face.upem)
        for ch in text:
            if ch != " ":
                self._put(face, ch, x, base, k, fill)
            x += face.advance(ch) * k

    def heading(self, text, size=17):
        self.y += size * 1.4
        self._words(self.label_bold, text, 10, self.y, size, "#1a1a1a")
        self.y += size * 0.6

    def note(self, text, size=13):
        self.y += size * 1.3
        self._words(self.label, text, 10, self.y, size, "#6a6a6a")
        self.y += size * 0.45

    def line(self, segments, px, label=None, lx=150):
        """One line of running text as outlines.

        `segments` is [(face, text, fill)], so a code line can carry its
        comment in the italic and its string in another colour without the
        row being three images stitched together.
        """
        base = self.y + px * 1.02
        if label:
            self._words(self.label, label, 10, base, 12, "#9a9a9a")
        x = float(lx)
        for face, text, fill in segments:
            k = px / float(face.upem)
            for ch in text:
                if ch != " ":
                    self._put(face, ch, x, base, k, fill)
                x += face.advance(ch) * k
        self.y += px * 1.5
        return x

    def glyphs(self, face, chars, px, before=None, fill="#000", lx=None,
               skew=None, xform=None):
        """A row of letters at `px` per em, optionally over a red before-outline.

        Never one letter alone: the caller passes the company, and the row keeps
        the face's own advance so the spacing is the font's, not the sheet's.
        """
        k = px / float(face.upem)
        base = self.y + px * 1.06
        x = PAD if lx is None else float(lx)
        # A candidate can be MOCKED sheared without a build: the italic applies
        # the same shear to the upright construction, so skewing the upright
        # glyph here shows the shape the recipe would produce. Spacing is the
        # one thing it does not show, which the caption has to say.
        sk = ""
        if skew:
            import math as _m
            t = _m.tan(_m.radians(skew[0]))
            sk = " matrix(1,0,%.5f,1,%.2f,0)" % (t, -skew[1] * t)
        for ch in chars:
            # `xform` lets ONE letter in the row carry its own transform, which
            # is what a variant sheet needs: a candidate built out of another
            # letter can be shown before it is built, beside the real ones.
            e = sk
            if isinstance(xform, dict):
                e = xform.get(ch) or sk
            elif xform:
                e = xform
            self._put(face, ch, x, base, k, fill, extra=e)
            if before and ch in before:
                self.body.append(
                    '<g transform="translate(%.2f,%.2f) scale(%.6f,-%.6f)">'
                    '<path d="%s" fill="none" stroke="#c81818" '
                    'stroke-width="%.1f"/></g>'
                    % (x, base, k, k, before[ch], 3.0 / k))
            x += face.advance(ch) * k + px * 0.10
        self.y += px * 1.45
        return x

    def grid(self, face, chars, px, cols=16, lx=None):
        """The whole alphabet, in rows, at one weight."""
        k = px / float(face.upem)
        step = face.advance("o") * k + px * 0.22
        x0 = PAD if lx is None else float(lx)
        for i in range(0, len(chars), cols):
            base = self.y + px * 1.06
            for j, ch in enumerate(chars[i:i + cols]):
                self._put(face, ch, x0 + j * step, base, k, "#000")
            self.y += px * 1.45
        return step * min(cols, len(chars)) + x0

    # ---- output ---------------------------------------------------------

    def save(self, path):
        defs = "".join('<path id="%s" d="%s" fill-rule="evenodd"/>' % (i, d)
                       for i, d in self.defs.values())
        h = int(self.y + 30)
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" '
               'xmlns:xlink="http://www.w3.org/1999/xlink" '
               'width="%d" height="%d" viewBox="0 0 %d %d">'
               '<title>%s</title>'
               '<rect width="100%%" height="100%%" fill="#fff"/>'
               '<defs>%s</defs>%s</svg>'
               % (self.width, h, self.width, h, esc(self.title), defs,
                  "".join(self.body)))
        open(path, "w", encoding="utf-8").write(svg)
        return path, len(svg)
