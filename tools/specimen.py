"""The one review sheet: every letter in the company it actually keeps.

    ./venv/bin/python tools/specimen.py                 the whole sheet
    ./venv/bin/python tools/specimen.py --letters Зз     one question, bigger
    ./venv/bin/python tools/specimen.py --against OLD    this build vs a stash

There were ten of these, and there were ten for one reason: a PNG holding the
alphabet, the case pairs, the prose, the code, the italic and four reading
sizes is either unreadably small or too big to open. So the sheet was split by
LETTER -- one for б, one for к, one for м, one for the cursive г and д -- and
each split copied the same four rows again: the letters in company, a few
words, a mixed git line, the reading sizes. Nine files, one shape.

SVG removes the reason. The file carries outlines rather than pixels, so all of
it fits in one document and the reader zooms into the section they want instead
of opening a different file. `--letters` is the old per-letter sheet, which is
still worth having when one letter is the question -- it is the same rows with
fewer letters and more room, not another script.

What every section is for:

  alphabet      the set at a glance, upright and italic, so a letter that is
                the wrong size or colour shows against its own neighbours
  case pairs    the one image that settles whether a lowercase belongs to its
                capitals -- and the `vs Latin` row, which is the letter beside
                the Latin it will actually sit next to
  prose         a paragraph has a texture and one letter too dark or too wide
                stains it, which no per-glyph reading finds
  code          Latin identifiers with Ukrainian strings and comments, because
                that is how this font is really used, and the italic doing its
                real job rather than being inspected
  reading sizes 12 and 14, which is where a monospace lives. No magnification
                trick is needed here: the line says 12px and the viewer
                rasterises it the way a screen will.

`--against OLD_DIR` is `em_sheet.py` folded in, and it folded in because the
only thing that script had that this one lacked was ADJACENCY: two builds set
touching on one line per weight, because a difference of a tenth of a stem is
invisible between two pictures a screen apart and obvious between two letters
that touch. Everything else it carried is gone. Its magnification machinery
went with the raster -- the reading rows here say 12px and the viewer does the
rasterising -- and its `--company/--words/--line` flags went because they
existed to re-point a м-specific default that a general sheet does not have.
OLD_DIR is any stashed build, a directory of `SUSEMono-<weight>.ttf`; copy the
statics aside before rebuilding. The four upright statics are assumed to be
there and an ITALIC the older build predates is skipped; a glyph it does not
have is drawn as a gap and named in a note -- an old build is by definition
allowed to be missing letters, which is usually the thing being looked at.

JetBrains Mono sits under the rows that compare, as a professionally drawn
Cyrillic to be measured against. It is skipped rather than fatal if absent.
"""
import glob
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from panel import font_dirs                                    # noqa: E402
from svgsheet import Faces, Sheet                               # noqa: E402

WIDTH = 1500
INK = "#18181c"
DIM = "#80848c"
COMMENT = "#6e7680"
STR = "#963c28"

CAPS = "АБВГҐДЕЄЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЮЯЭЫЪ"
LOWER = "абвгґдеєжзийклмнопрстуфхцчшщьюяэыъії"
PAIRS = "Фф Юю Єє Ґґ Дд Жж Лл Чч Ээ Яя Зз Бб Кк Мм"
VS_LATIN = "oф oю cє rґ vд nл oз ob кk мm"

UA = "ґрунт, боротьба, єднати"
RU = "юность, борьба, тёщи"
MIXED = "git commit -m 'юність' v2.1 build/ґрунт-єднати.log"
SENTENCE = "ПОЛЕ ЦВІТЕ, ВІТЕР ДМЕ"
RUSSIAN = "ПОДЪЕЗД, БЫЛЫЕ ВЫБОРИ, ЭХО".replace("ВЫБОРИ", "ВЫБОРЫ")

PROSE = [
    "Монопростірний шрифт живе не в зразку, а в абзаці: очі йдуть по рядку",
    "і спотикаються там, де одна літера темніша або ширша за сусідів. Саме",
    "тому ґ, є, і, ї та апостроф перевіряються в тексті, а не поодинці —",
    "у слові «п'ятдесят» апостроф несе стільки ж ваги, скільки й літера.",
]

# Real code, written the way it is really written: Latin identifiers, Ukrainian
# comments and messages. A listing with Cyrillic keywords would prove nothing.
CODE = [
    ("com", "// Poll слухає чергу оголошень і повертає лише нові лоти."),
    ("code", "func (s *Scanner) Poll(ctx context.Context) ([]Lot, error) {"),
    ("code", "    req, err := http.NewRequestWithContext(ctx, \"GET\", s.url, nil)"),
    ("code", "    if err != nil {"),
    ("str", "        return nil, fmt.Errorf(\"не вдалося створити запит: %w\", err)"),
    ("code", "    }"),
    ("com", "    // ETag economises: сервер віддає 304 і тіло не їде взагалі."),
    ("str", "    log.Printf(\"знайдено %d нових лотів за %s\", len(lots), dt)"),
    ("code", "}"),
]

SHELL = [
    ("dim", "$ git log --oneline --graph"),
    ("code", "* 3489939 ґ і ї тепер мають свої власні контури"),
    ("code", "* 73503d1 д росте з чаші, а не лежить на ній"),
    ("dim", "$ go test ./... -run 'Сканер'"),
    ("code", "ok      github.com/geo/sizif/scan   0.412s  (12 з 12 пройшли)"),
]


def jetbrains():
    """JetBrains Mono's path pattern, found rather than hardcoded."""
    for d in font_dirs():
        hit = glob.glob(d + "/JetBrainsMono-Regular.ttf")
        if hit:
            return hit[0].replace("Regular", "%s")
    return None


def guard(up, text):
    """A specimen that quietly renders .notdef boxes is worse than none: it
    looks like a drawing fault in a letter that simply is not there."""
    missing = {c for c in text
               if c.isalpha() and ord(c) > 0x400 and not up.has(c)}
    if missing:
        raise SystemExit("specimen uses unbuilt glyphs: %s in %r"
                         % ("".join(sorted(missing)), text))
    return text


def letter_sheet(sh, up, it, letters):
    """The old per-letter sheet: one question, in company, at every weight.

    The company is not decoration. A letter shown alone can only be compared
    with the memory of the last one, and every per-letter sheet this replaces
    hand-picked neighbours for exactly that reason -- б between о and 6, к
    beside the Latin k. Picked generically here: each letter between a ROUND
    and a STRAIGHT, which is where a width or a weight fault shows, and then
    the whole alphabet so it is seen among everything it will stand next to.
    """
    frame = "  ".join("о%sо н%sн" % (c, c) for c in letters)
    sh.heading("%s — between a round and a straight, upright then italic"
               % letters)
    for w in ("Thin", "Regular", "Bold", "ExtraBold"):
        sh.glyphs(up(w), guard(up("Regular"), frame), 64, lx=170)
        sh.glyphs(it(w), frame, 64, lx=170)
        sh.gap(4)
    sh.rule()

    sh.heading("Among the whole set, where it has to keep the rhythm")
    for f in (up("Regular"), it("Regular"), up("Bold")):
        sh.grid(f, CAPS, 46, cols=18, lx=PADX)
        sh.grid(f, LOWER, 46, cols=18, lx=PADX)
        sh.gap(6)
    sh.rule()
    sh.heading("In words, and in a line that mixes the scripts")
    for w in ("Regular", "Bold"):
        for t in (UA, RU, MIXED):
            sh.line([(up(w), t, INK)], 34, label=w)
    sh.rule()
    sh.heading("At the sizes it is read at")
    for px in (14, 12):
        sh.line([(up("Regular"), MIXED, INK)], px, label="%dpx" % px)
        sh.line([(it("Regular"), MIXED, INK)], px, label="%dpx italic" % px)


AGAINST_WEIGHTS = ("Thin", "Regular", "Bold", "ExtraBold")


def _adjacent(sh, fold, fnew, text, px, label=None):
    """The same text in both builds on ONE line -- old left, new right."""
    y0 = sh.y
    mid = PADX + sh.width_of(fold, text, px) + sh.width_of(fold, "   ", px) / 2
    sh.line([(fold, text, INK), (fold, "   ", INK), (fnew, text, INK)],
            px, label=label, lx=PADX)
    sh.vrule(mid, y0, sh.y - px * 0.2)


def against_frame(letters):
    """What the big band compares -- the named letters, or the case pairs."""
    return ("  ".join("о%sо н%sн" % (c, c) for c in letters) if letters
            else PAIRS)


def against_width(face, frame):
    """How wide the page has to be for two columns to stand side by side.

    Adjacency is the whole reason this mode exists, so the PAGE gives way, not
    the columns: set to 1500 the second column simply falls off the right edge,
    which is the fault the mode was folded in to fix. An SVG has no fixed
    paper.
    """
    def span(text, px):
        k = px / float(face.upem)
        w = sum(face.advance(c) for c in text) * k
        return PADX + 2 * w + sum(face.advance(c) for c in "   ") * k + 40
    return int(max(WIDTH, span(frame, 56), span(LOWER, 26),
                   span(MIXED, 14), span(UA, 30)))


def against_sheet(sh, old_up, old_it, up, it, letters, left, right):
    """This build beside a stashed one, the same rows, the columns touching.

    Four weights, not six: what gets stashed is the statics, and the two ends
    plus the two middles are where a change either holds across the axis or
    does not.
    """
    reg = up("Regular")
    frame = against_frame(letters)
    guard(reg, frame)

    sh.heading("%s — the two builds adjacent, one line per weight"
               % (letters if letters else "The case pairs"))
    sh.note("left column: %s      right column: %s" % (left, right))
    gone = sorted({c for c in frame + LOWER + CAPS
                   if c.strip() and not old_up("Regular").has(c)})
    if gone:
        sh.note("not in %s, so drawn as a gap: %s" % (left, "".join(gone)))
    sh.gap(6)
    for w in AGAINST_WEIGHTS:
        _adjacent(sh, old_up(w), up(w), frame, 56, label=w)
    for w in AGAINST_WEIGHTS:
        o, n = old_it.get(w), it.get(w)
        if o and n:
            _adjacent(sh, o, n, frame, 56, label=w + " Italic")
    sh.rule()

    sh.heading("Among the whole drawn lowercase, where the rhythm shows")
    for w in AGAINST_WEIGHTS:
        _adjacent(sh, old_up(w), up(w), LOWER, 26, label=w)
    sh.rule()

    sh.heading("In words")
    for w in AGAINST_WEIGHTS:
        _adjacent(sh, old_up(w), up(w), UA, 30, label=w)
    sh.rule()

    sh.heading("At the sizes it is read at")
    for w in AGAINST_WEIGHTS:
        for px in (14, 12):
            _adjacent(sh, old_up(w), up(w), MIXED, px,
                      label="%s %dpx" % (w, px))


def full_sheet(sh, up, it, jb):
    reg, bold = up("Regular"), up("Bold")

    sh.heading("The set — Regular, then Bold, then Italic")
    for f in (reg, bold, it("Regular")):
        sh.grid(f, guard(reg, CAPS), 62, cols=18, lx=PADX)
        sh.grid(f, guard(reg, LOWER), 62, cols=18, lx=PADX)
        sh.gap(8)
    sh.rule()

    sh.heading("Each new lowercase against its own capital, and against the "
               "Latin it shares a line with")
    for lab, f, t in (("Regular", reg, PAIRS), ("Bold", bold, PAIRS),
                      ("vs Latin", reg, VS_LATIN)):
        sh.line([(f, guard(reg, t), INK)], 44, label=lab)
    if jb:
        sh.line([(jb("Regular"), PAIRS, INK)], 44, label="JetBrains")
    sh.rule()

    sh.heading("Prose — the texture a single wrong letter stains")
    for t in PROSE:
        sh.line([(reg, guard(reg, t), INK)], 30, label=None, lx=PADX)
    sh.gap(6)
    for t in PROSE[:2]:
        sh.line([(it("Regular"), t, INK)], 30, lx=PADX)
    sh.rule()

    sh.heading("Code — Latin identifiers, Ukrainian strings, italic comments")
    kind = {"com": (it("Regular"), COMMENT), "str": (reg, STR),
            "code": (reg, INK), "dim": (reg, DIM)}
    for block in (CODE, SHELL):
        for k, t in block:
            f, col = kind[k]
            sh.line([(f, guard(reg, t), col)], 22, lx=PADX)
        sh.gap(10)
    sh.rule()

    sh.heading("Mixed scripts in one line — where a bolted-on script shows")
    for px in (18, 14, 12):
        sh.line([(reg, guard(reg, MIXED), INK)], px, label="%dpx" % px)
    if jb:
        sh.line([(jb("Regular"), MIXED, INK)], 18, label="JetBrains 18px")
    sh.rule()

    sh.heading("At the sizes it is read at")
    for lab, f, t in (("14px UA", reg, UA), ("14px RU", reg, RU),
                      ("14px caps", reg, SENTENCE),
                      ("14px russian", reg, RUSSIAN)):
        sh.line([(f, guard(reg, t), INK)], 14, label=lab)
    for lab, f, t in (("12px UA", reg, UA), ("12px RU", reg, RU),
                      ("12px italic", it("Regular"), UA),
                      ("12px bold", bold, UA)):
        sh.line([(f, t, INK)], 12, label=lab)
    sh.rule()

    sh.heading("The same words through the weights")
    for w in ("Thin", "Light", "Regular", "SemiBold", "Bold", "ExtraBold"):
        sh.line([(up(w), UA + "   " + RU, INK)], 30, label=w)
    sh.gap(6)
    for w in ("Thin", "Regular", "Bold", "ExtraBold"):
        sh.line([(it(w), UA + "   " + RU, INK)], 30, label=w + " Italic")


PADX = 170

def flag(name, default=None):
    return (sys.argv[sys.argv.index(name) + 1] if name in sys.argv
            else default)


if __name__ == "__main__":
    letters = flag("--letters")
    against = flag("--against")

    up = Faces("fonts/ttf/SUSEMono-%s.ttf")
    it = Faces("fonts/ttf/SUSEMono-%sItalic.ttf")
    jbp = jetbrains()
    jb = Faces(jbp) if jbp else None

    # The sheet's own headings are set in the face too, so that no letter
    # anywhere on the page is a fallback the reader might take for ours.
    width = WIDTH
    if against:
        width = against_width(up("Regular"), against_frame(letters))
    elif letters:
        # The per-letter sheet frames EVERY named letter on one line, so eight
        # letters is eight frames and the row runs off a fixed page. The page
        # gives way, the same as in against mode: an SVG has no fixed paper,
        # and a row cut off at the right edge is a picture that lies.
        f, frame = up("Regular"), against_frame(letters)
        k = 64 / float(f.upem)
        # `glyphs` adds a tenth of the size after EVERY character, so the row
        # is its advances plus that, once per character and not once per
        # letter -- counted per letter it fell short and cut the last frame.
        row = sum(f.advance(c) for c in frame) * k + 64 * 0.10 * len(frame)
        width = int(max(WIDTH, PADX + row + 80))

    sh = Sheet(width, "SUSE Mono Cyrillic — %s%s"
               % ("against %s: " % against if against else "",
                  letters if letters else "specimen"),
               label=up("Regular"), label_bold=up("SemiBold"))
    sh.note("SUSE Mono Cyrillic   ·   generated from the current build")
    sh.gap(6)
    old_up = old_it = None
    if against:
        old_up = Faces(against.rstrip("/") + "/SUSEMono-%s.ttf")
        old_it = Faces(against.rstrip("/") + "/SUSEMono-%sItalic.ttf")
        against_sheet(sh, old_up, old_it, up, it, letters,
                      flag("--left", against.rstrip("/").rsplit("/", 1)[-1]),
                      flag("--right", "this build"))
    elif letters:
        letter_sheet(sh, up, it, letters)
    else:
        full_sheet(sh, up, it, jb)

    out = "tools/out/specimen%s%s.svg" % (
        "-against" if against else "", "-" + letters if letters else "")
    path, size = sh.save(out)
    up.close(); it.close()
    for f in (old_up, old_it, jb):
        if f:
            f.close()
    print("%s  (%d glyph defs, %.0f KB)" % (path, len(sh.defs), size / 1024.0))
