"""The face doing the two jobs it will actually do: prose, and code.

    ./venv/bin/python tools/specimen.py

Every other sheet here shows the alphabet, or a letter beside its neighbours,
or one command line. None of them shows what this font is FOR. A monospace
Cyrillic is read as running text in a terminal and as source in an editor, and
both of those are pages of it at twelve to fifteen pixels, mixed with Latin on
every line, with the italic doing real work rather than being inspected.

Three things only this sheet can catch:

  colour        a paragraph has a texture, and one letter too dark or too wide
                shows up as a stain in it that no per-glyph reading finds. The
                Ukrainian pangram carries Ґ Є І Ї and the apostrophe, which are
                the letters this project exists for.
  mixed lines   code is Latin identifiers with Cyrillic strings and comments on
                the same line. Where the two scripts do not sit at the same
                weight or on the same rhythm, this is where it shows.
  the italic    editors set comments in it. That is the italic's real job and
                it is the first time the cursive г and д appear in one.

Sizes are the sizes it is read at. There is one display row and everything
else is 12 to 15 pixels, which is where a monospace lives.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from PIL import Image, ImageDraw, ImageFont                    # noqa: E402

R = "fonts/ttf/SUSEMono-%s.ttf"
I = "fonts/ttf/SUSEMono-%sItalic.ttf"

# SS is the supersample used to get a clean edge; SCALE is how much bigger than
# its nominal size the whole sheet is DELIVERED.
#
# They are not the same thing and confusing them is what made this sheet look
# terrible. Supersampling alone gives a properly antialiased 14-pixel line --
# which is then fourteen actual pixels tall in the PNG, and anything that shows
# the PNG larger than 1:1 is enlarging fourteen pixels. The sheet was sharp and
# tiny, which reads as low quality and is.
#
# So every row is rendered at SCALE times its nominal size, natively, at the
# real outline. The rows that exist to show what a READING size looks like
# cannot be rendered large -- a 12-pixel letter drawn at 36 pixels is a
# different rasterisation -- so those are drawn at 12 and enlarged by whole
# pixels with NEAREST, which magnifies the actual pixel grid instead of
# inventing a smoother one. See `line`.
SS = 4
SCALE = 3

INK = (24, 24, 28)
DIM = (128, 132, 140)
COMMENT = (110, 118, 128)
STR = (150, 60, 40)
KEY = (60, 70, 150)

PANGRAM = "Жебракують філософи при ґанку церкви в Гадячі, ще й шатро їхнє п'яне"
RU = "Съешь же ещё этих мягких французских булок, да выпей чаю."

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
    ("code", "\treq, err := http.NewRequestWithContext(ctx, \"GET\", s.url, nil)"),
    ("code", "\tif err != nil {"),
    ("str", "\t\treturn nil, fmt.Errorf(\"не вдалося створити запит: %w\", err)"),
    ("code", "\t}"),
    ("com", "\t// ETag economises: сервер віддає 304 і тіло не їде взагалі."),
    ("code", "\treq.Header.Set(\"If-None-Match\", s.etag)"),
    ("str", "\tlog.Printf(\"знайдено %d нових лотів за %s\", len(lots), dt)"),
    ("code", "}"),
]

SHELL = [
    ("dim", "$ git log --oneline --graph"),
    ("plain", "* 3489939 ґ і ї тепер мають свої власні контури"),
    ("plain", "* 73503d1 д росте з чаші, а не лежить на ній"),
    ("dim", "$ go test ./... -run 'Сканер'"),
    ("plain", "ok      github.com/geo/sizif/scan   0.412s  (12 з 12 пройшли)"),
]


def line(path, s, px, fill=INK, real=False):
    """One line at SCALE times `px`.

    `real=True` means the row is showing what that size actually looks like on
    a screen: the line is drawn at `px` and then enlarged by whole pixels, so
    what is magnified is the rasterisation and not the outline. Everything else
    is drawn at the full size against the real outline.

    Tabs become four spaces -- PIL draws a tab as nothing at all, which
    silently eats the indentation.
    """
    s = s.replace("\t", "    ")
    at = px if real else px * SCALE
    f = ImageFont.truetype(path, at * SS)
    w = int(f.getlength(s)) + at * SS
    h = int(at * SS * 1.45)
    im = Image.new("RGB", (max(w, 1), h), "white")
    ImageDraw.Draw(im).text((0, 0), s, font=f, fill=fill)
    out = im.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    im.close()
    if real:
        out = out.resize((out.width * SCALE, out.height * SCALE),
                         Image.NEAREST)
    return out


def block(rows, px, weight="Regular", real=False):
    """A run of lines, each with its own font and colour, as one image."""
    kind = {"com": (I % weight, COMMENT), "str": (R % weight, STR),
            "code": (R % weight, INK), "dim": (R % weight, DIM),
            "plain": (R % weight, INK)}
    imgs = [line(kind[k][0], s, px, kind[k][1], real) for k, s in rows]
    W = max(i.width for i in imgs)
    lh = int(px * SCALE * 1.55)
    im = Image.new("RGB", (W, lh * len(imgs) + px), "white")
    for n, i in enumerate(imgs):
        im.paste(i, (0, n * lh))
    return im


def main():
    # Labels sit ABOVE their block, not beside it. Beside, the column has to be
    # as wide as the longest label or the label runs into the specimen -- which
    # it did, and the one that says what the italic is doing was the one cut in
    # half. Above costs a line and cannot collide.
    pad = 26 * SCALE
    lab = ImageFont.truetype(R % "Regular", 17 * SCALE)
    head = ImageFont.truetype(R % "Regular", 30 * SCALE)
    sub = ImageFont.truetype(R % "Regular", 19 * SCALE)

    rows = [
        ("the Ukrainian pangram -- Ґ Є І Ї and the apostrophe are the "
         "letters this project exists for",
         [line(R % "Regular", PANGRAM, 26)]),
        ("the same, italic", [line(I % "Regular", PANGRAM, 26)]),
        ("Russian", [line(R % "Regular", RU, 26)]),
        ("prose", [block([("plain", s) for s in PROSE], 15)]),
        ("Go -- comments italic, as an editor sets them", [block(CODE, 14)]),
        ("the same, Bold", [block(CODE, 14, "Bold")]),
        ("a terminal", [block(SHELL, 13)]),
        ("and the sizes it is actually READ at, magnified %dx so the pixels "
         "are the real ones: prose at 15px" % SCALE,
         [block([("plain", s) for s in PROSE], 15, real=True)]),
        ("Go at 13px, magnified %dx" % SCALE, [block(CODE, 13, real=True)]),
        ("Go at 11px, magnified %dx" % SCALE, [block(CODE, 11, real=True)]),
    ]

    title = "prose and code -- the two jobs this face has"
    caption = ("a monospace Cyrillic is read as a page at twelve to fifteen "
               "pixels, mixed with Latin on every line, with the italic "
               "setting the comments")

    W = max(max(pad + i.width + pad for _t, im in rows for i in im),
            pad + int(sub.getlength(caption)) + pad,
            pad + max(int(lab.getlength(t)) for t, _im in rows) + pad, 900)
    H = 108 * SCALE + sum(max(i.height for i in im) + 52 * SCALE
                          for _t, im in rows)
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    d.text((pad, 22 * SCALE), title, font=head, fill=(170, 30, 30))
    d.text((pad, 60 * SCALE), caption, font=sub, fill=(140, 140, 140))
    y = 108 * SCALE
    for name, imgs in rows:
        d.text((pad, y), name, font=lab, fill=(125, 125, 125))
        y += 26 * SCALE
        x = pad
        for i in imgs:
            sheet.paste(i, (x, y))
            x += i.width + pad
        y += max(i.height for i in imgs) + 26 * SCALE
    sheet.save("tools/out/specimen.png")
    print("   wrote tools/out/specimen.png", sheet.size)


if __name__ == "__main__":
    main()
