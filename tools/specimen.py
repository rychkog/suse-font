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
SS = 4

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


def line(path, s, px, fill=INK):
    """One line, supersampled and resolved down. Tabs become four spaces --
    PIL draws a tab as nothing at all, which silently eats the indentation."""
    s = s.replace("\t", "    ")
    f = ImageFont.truetype(path, px * SS)
    w = int(f.getlength(s)) + px * SS
    h = int(px * SS * 1.45)
    im = Image.new("RGB", (max(w, 1), h), "white")
    ImageDraw.Draw(im).text((0, 0), s, font=f, fill=fill)
    out = im.resize((max(1, w // SS), max(1, h // SS)), Image.LANCZOS)
    im.close()
    return out


def block(rows, px, weight="Regular"):
    """A run of lines, each with its own font and colour, as one image."""
    kind = {"com": (I % weight, COMMENT), "str": (R % weight, STR),
            "code": (R % weight, INK), "dim": (R % weight, DIM),
            "plain": (R % weight, INK)}
    imgs = [line(kind[k][0], s, px, kind[k][1]) for k, s in rows]
    W = max(i.width for i in imgs)
    lh = int(px * 1.55)
    im = Image.new("RGB", (W, lh * len(imgs) + px // 2), "white")
    for n, i in enumerate(imgs):
        im.paste(i, (0, n * lh))
    return im


def main():
    # Labels sit ABOVE their block, not beside it. Beside, the column has to be
    # as wide as the longest label or the label runs into the specimen -- which
    # it did, and the one that says what the italic is doing was the one cut in
    # half. Above costs a line and cannot collide.
    pad = 26
    lab = ImageFont.truetype(R % "Regular", 17)
    head = ImageFont.truetype(R % "Regular", 32)
    sub = ImageFont.truetype(R % "Regular", 20)

    rows = [
        ("the Ukrainian pangram at 30px -- Ґ Є І Ї and the apostrophe are "
         "the letters this project exists for",
         [line(R % "Regular", PANGRAM, 30)]),
        ("the same, italic", [line(I % "Regular", PANGRAM, 30)]),
        ("Russian at 30px", [line(R % "Regular", RU, 30)]),
        ("prose at 15px", [block([("plain", s) for s in PROSE], 15)]),
        ("prose at 13px", [block([("plain", s) for s in PROSE], 13)]),
        ("Go at 14px -- comments italic, as an editor sets them",
         [block(CODE, 14)]),
        ("Go at 12px", [block(CODE, 12)]),
        ("Go at 14px, Bold", [block(CODE, 14, "Bold")]),
        ("a terminal at 13px", [block(SHELL, 13)]),
    ]

    title = "prose and code -- the two jobs this face has"
    caption = ("a monospace Cyrillic is read as a page at twelve to fifteen "
               "pixels, mixed with Latin on every line, with the italic "
               "setting the comments")

    W = max(max(pad + i.width + pad for _t, im in rows for i in im),
            pad + int(sub.getlength(caption)) + pad,
            pad + max(int(lab.getlength(t)) for t, _im in rows) + pad, 900)
    H = 108 + sum(max(i.height for i in im) + 52 for _t, im in rows)
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    d.text((pad, 22), title, font=head, fill=(170, 30, 30))
    d.text((pad, 62), caption, font=sub, fill=(140, 140, 140))
    y = 108
    for name, imgs in rows:
        d.text((pad, y), name, font=lab, fill=(125, 125, 125))
        y += 26
        x = pad
        for i in imgs:
            sheet.paste(i, (x, y))
            x += i.width + pad
        y += max(i.height for i in imgs) + 26
    sheet.save("tools/out/specimen.png")
    print("   wrote tools/out/specimen.png", sheet.size)


if __name__ == "__main__":
    main()
