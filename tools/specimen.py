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

# EVERY drawn letter is here. The list was hand-written and stood at 33 of
# the 99 in classify.TIERS, so letters shipped and were approved without ever
# reaching this sheet; only the nine Serbian letters are absent now, and they
# are absent because they are not built. Check it against classify.TIERS when
# a letter is added.
#
# Alphabetical order is not the point of this row; adjacency is. A letter
# built from another sits in its cluster -- Г Ґ Ѓ, Е Ё Ѐ, И Й Ѝ, І Ї, К Ќ,
# У Ў, Ц Џ -- so a mark placed a unit off reads against the letter it was
# placed on. Ѕ and Ј come from Latin S and J, so they take the slots
# Macedonian order gives them instead.
CAPS = "АБВГҐЃДЕЁЀЄЖЗЅИЙЍІЇЈКЌЛМНОПРСТУЎФХЦЏЧШЩЬЮЯЭЫЪ"
LOWER = "абвгґѓдеёѐєжзѕийѝіїјкќлмнопрстуўфхцчшщьюяэыъ"
PAIRS = "Фф Юю Єє Ґґ Дд Жж Лл Чч Ээ Яя Зз Бб Кк Мм"
VS_LATIN = "oф oю cє rґ vд nл oз ob кk мm"

UA = "ґанок, аґрус, дзиґа, ґречний"
RU = "юность, борьба, тёщи"
# Belarusian needs three pairs the other two do not both supply -- ў, ё and
# і -- and its apostrophe is a letter of the word, not punctuation around it.
# All four are in this line, so a Belarusian reader's own text is what judges
# them rather than a row of bare letters.
BE = "зноў, аўтар, сямʼя, лёс, ідэя"
MIXED = "git commit -m 'юність' v2.1 build/ґрунт-єднати.log"
SENTENCE = "ПОЛЕ ЦВІТЕ, ВІТЕР ДМЕ"
RUSSIAN = "ПОДЪЕЗД, БЫЛЫЕ ВЫБОРИ, ЭХО".replace("ВЫБОРИ", "ВЫБОРЫ")

# ґ is loaded on purpose. It is rare in Ukrainian, so a paragraph written
# naturally carries it once or not at all -- and the one place it appeared
# here was `ґ, є, і, ї`, a bare letter between commas, which is the only
# setting in which it cannot be judged at all.
PROSE = [
    "Монопростірний шрифт живе не в зразку, а в абзаці: очі йдуть по рядку",
    "і спотикаються там, де одна літера темніша або ширша за сусідів. Ґанок,",
    "ґрунт, аґрус, ґудзик, дзиґа: ґ трапляється рідко, і саме тому її",
    "у зразку ставлять зумисне — поодинці вона не доводить нічого.",
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


# Running text, for the reading a letter is finally judged by. Ukrainian,
# because і and ї are the letters this face has least of elsewhere: a specimen
# built out of words that avoid them proves nothing about them.
PARAGRAPH = (
    "Кирилиця в цьому шрифті не є перекладом латиниці. Її літери мають "
    "власну історію, свій ритм і свої правила: там, де латинська i стоїть "
    "рівно, українська і нахиляється разом з усім рядком. Їхні форми різні, "
    "але вага, ширина і нахил спільні, інакше текст читається як дві різні "
    "руки на одному аркуші. Ґанок, ґрунт, аґрус, ґудзик, дзиґа, ґречний, "
    "ґелґотати, ремиґати: ґ трапляється рідко, тож у зразку її ставлять "
    "зумисне, поряд з є, і та ї. Дрібний кегль вирішує все: те, що на "
    "великому виглядає вдалим, у рядку коду може зникнути або, навпаки, "
    "кричати."
)


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
        sh.grid(f, CAPS, 46, cols=23, lx=PADX)
        sh.grid(f, LOWER, 46, cols=23, lx=PADX)
        sh.gap(6)
    sh.rule()
    sh.heading("In words, and in a line that mixes the scripts")
    for w in ("Regular", "Bold"):
        for t in (UA, RU, BE, MIXED):
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


def wrap(text, cols):
    """Break the text at spaces to `cols` monospaced columns."""
    out, line = [], ""
    for word in text.split(" "):
        if line and len(line) + 1 + len(word) > cols:
            out.append(line)
            line = word
        else:
            line = (line + " " + word) if line else word
    return out + ([line] if line else [])


def prose_sheet(sh, up, it, width):
    """Running text at the sizes it is read at, upright beside italic.

    The letter sheets answer "is this the right shape"; only prose answers
    "does it disappear into a paragraph", which is the whole job of a text
    face. A letter can be right in a frame and wrong in a line -- and where it
    sits in its cell shows here and nowhere else.
    """
    for px in (17, 14, 12):
        for label, face in (("Regular Italic", it("Regular")),
                            ("Regular", up("Regular"))):
            sh.heading("%s, %d px" % (label, px), 15)
            cols = int((width - PADX - 40) / (face.advance("i") * px / 1000.0))
            for row in wrap(guard(up("Regular"), PARAGRAPH), cols):
                sh.line([(face, row, INK)], px, lx=PADX)
            sh.gap(6)
        sh.rule()

    sh.heading("Bold Italic and ExtraBold Italic, 14 px")
    for w in ("Bold", "ExtraBold"):
        face = it(w)
        cols = int((width - PADX - 40) / (face.advance("i") * 14 / 1000.0))
        for row in wrap(PARAGRAPH, cols)[:3]:
            sh.line([(face, row, INK)], 14, lx=PADX)
        sh.gap(6)
    sh.rule()

    sh.heading("Large, where the drawing is judged")
    for w, f in (("Regular Italic", it("Regular")),
                 ("ExtraBold Italic", it("ExtraBold"))):
        sh.line([(f, "мій київ — інші ідеї", INK)], 44, label=w, lx=PADX)
    sh.gap(6)
    sh.rule()


def full_sheet(sh, up, it, jb):
    reg, bold = up("Regular"), up("Bold")

    sh.heading("The set — Regular, then Bold, then Italic")
    for f in (reg, bold, it("Regular")):
        sh.grid(f, guard(reg, CAPS), 62, cols=23, lx=PADX)
        sh.grid(f, guard(reg, LOWER), 62, cols=23, lx=PADX)
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
    # the whole paragraph, not the first two lines: the italic is the case
    # under review and ґ lives in the third
    for t in PROSE:
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
                      ("14px BE", reg, BE),
                      ("14px italic", it("Regular"), UA),
                      ("14px caps", reg, SENTENCE),
                      ("14px russian", reg, RUSSIAN)):
        sh.line([(f, guard(reg, t), INK)], 14, label=lab)
    for lab, f, t in (("12px UA", reg, UA), ("12px RU", reg, RU),
                      ("12px BE", reg, BE),
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
    # Belarusian on its own line: added to the row above it runs past the page,
    # and ў is the one letter here whose mark has to clear an open top.
    sh.gap(6)
    for w in ("Thin", "Regular", "Bold", "ExtraBold"):
        sh.line([(up(w), BE, INK)], 30, label=w + " BE")
        sh.line([(it(w), BE, INK)], 30, label=w + " BE Italic")


PADX = 170

def flag(name, default=None):
    return (sys.argv[sys.argv.index(name) + 1] if name in sys.argv
            else default)


if __name__ == "__main__":
    letters = flag("--letters")
    against = flag("--against")
    prose = "--prose" in sys.argv

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
                  letters if letters else "prose" if prose else "specimen"),
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
    elif prose:
        prose_sheet(sh, up, it, width)
    elif letters:
        letter_sheet(sh, up, it, letters)
    else:
        full_sheet(sh, up, it, jb)

    out = "tools/out/specimen%s%s%s.svg" % (
        "-against" if against else "", "-prose" if prose else "",
        "-" + letters if letters else "")
    path, size = sh.save(out)
    up.close(); it.close()
    for f in (old_up, old_it, jb):
        if f:
            f.close()
    print("%s  (%d glyph defs, %.0f KB)" % (path, len(sh.defs), size / 1024.0))
