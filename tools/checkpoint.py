"""Render the review sheet for a checkpoint.

    python tools/checkpoint.py A

Produces tools/out/checkpoint.png with, in order: a numbered grid of every
new glyph, the same text set in this font and in JetBrains Mono for
comparison, real text at the sizes actually used, and a mixed-script line.
The grid is numbered so a glyph can be reported by number.
"""

import sys

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from classify import TIERS          # noqa: E402

FONT = "fonts/ttf/SUSEMono-%s.ttf"
JB = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/JetBrainsMono-%s.ttf"
LABEL = "/mnt/c/Windows/Fonts/segoeui.ttf"
W = 1500
PAD = 24


def present(weight="Regular"):
    cm = TTFont(FONT % weight).getBestCmap()
    return [(cp, chr(cp)) for cp, _, _, _ in TIERS if cp in cm]


def grid(chars, weight="Regular", cols=12, cell=104):
    rows = (len(chars) + cols - 1) // cols
    im = Image.new("RGB", (cols * cell, rows * cell + 8), "white")
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(FONT % weight, 58)
    small = ImageFont.truetype(LABEL, 15)
    for i, (cp, ch) in enumerate(chars):
        r, c = divmod(i, cols)
        x, y = c * cell, r * cell
        d.rectangle([x, y, x + cell - 1, y + cell - 1], outline=(228, 228, 228))
        d.text((x + 6, y + 4), str(i + 1), font=small, fill=(150, 150, 150))
        bb = d.textbbox((0, 0), ch, font=big)
        d.text((x + (cell - (bb[2] - bb[0])) / 2 - bb[0],
                y + 22), ch, font=big, fill=(0, 0, 0))
    return im


def line_block(title, rows, height_hint=0):
    """rows: list of (label, font, size, text)."""
    tmp = Image.new("RGB", (10, 10))
    dt = ImageDraw.Draw(tmp)
    lab = ImageFont.truetype(LABEL, 15)
    h = 30
    sizes = []
    for label, fp, size, text in rows:
        f = ImageFont.truetype(fp, size)
        bb = dt.textbbox((0, 0), text, font=f)
        sizes.append((f, bb))
        h += max(bb[3] - bb[1], size) + 22
    im = Image.new("RGB", (W, h), "white")
    d = ImageDraw.Draw(im)
    d.text((0, 4), title, font=ImageFont.truetype(LABEL, 17), fill=(60, 60, 60))
    y = 30
    for (label, fp, size, text), (f, bb) in zip(rows, sizes):
        d.text((0, y + 2), label, font=lab, fill=(140, 140, 140))
        d.text((150, y), text, font=f, fill=(0, 0, 0))
        y += max(bb[3] - bb[1], size) + 22
    return im


def matched(pairs, weights=("Regular", "Bold"), size=58):
    """Each lowercase scaled so its x-height equals the capital's cap height.

    The one view that answers "does this lowercase belong to that capital".
    Setting them at their real sizes only ever shows that one is smaller than
    the other; scaling the size away leaves the silhouette, which is the thing
    actually in question.
    """
    tmp = Image.new("RGB", (10, 10))
    lab = ImageFont.truetype(LABEL, 15)
    head = ImageFont.truetype(LABEL, 17)
    rowh = int(size * 1.75)
    im = Image.new("RGB", (W, 30 + rowh * len(weights)), "white")
    d = ImageDraw.Draw(im)
    d.text((0, 4), "Each lowercase scaled so its x-height equals the "
           "capital's cap height -- size removed, silhouette left",
           font=head, fill=(60, 60, 60))
    y = 30
    for wt in weights:
        f = TTFont(FONT % wt)
        k = f["OS/2"].sCapHeight / float(f["OS/2"].sxHeight)
        big = ImageFont.truetype(FONT % wt, size)
        small = ImageFont.truetype(FONT % wt, int(round(size * k)))
        d.text((0, y + rowh // 3), wt, font=lab, fill=(140, 140, 140))
        x = 150
        for i in range(0, len(pairs), 2):
            d.text((x, y), pairs[i], font=big, fill=(0, 0, 0))
            # the capital's own advance, so the two sit side by side rather
            # than on top of each other -- this face is monospaced at 600/1000
            d.text((x + int(size * 0.60), y - int(size * (k - 1) * 0.98)),
                   pairs[i + 1], font=small, fill=(180, 30, 30))
            x += int(size * 1.72)
        y += rowh
    return im


def stack(images, gap=26):
    w = max(i.width for i in images)
    h = sum(i.height for i in images) + gap * (len(images) - 1)
    out = Image.new("RGB", (w + 2 * PAD, h + 2 * PAD), "white")
    y = PAD
    for i in images:
        out.paste(i, (PAD, y))
        y += i.height + gap
    return out


def main():
    chars = present()
    have = {c for _, c in chars}
    caps = "".join(c for _, c in chars if c.isupper())

    def ok(text):
        """A specimen that quietly renders .notdef boxes is worse than none:
        it looks like a drawing fault in a letter that simply is not there."""
        missing = {c for c in text
                   if c.isalpha() and ord(c) > 0x400 and c not in have}
        if missing:
            raise SystemExit(f"specimen uses unbuilt glyphs: "
                             f"{''.join(sorted(missing))}  in {text!r}")
        return text

    sentence = "ПОЛЕ ЦВІТЕ, ВІТЕР ДМЕ"
    # Ukrainian alone never sets Ы Ъ Э, so those three had only ever been
    # reviewed as isolated glyphs. Both scripts from here on.
    russian = "ПОДЪЕЗД, БЫЛЫЕ ВЫБОРЫ, ЭХО"
    ua = ok("ґрунт, юність, єднати")
    ru = ok("юность, форты, тёщи")

    parts = [grid(chars)]

    # The one image that settles whether a lowercase belongs to its capitals:
    # each new letter directly under the capital it has to stand beside.
    parts.append(line_block(
        "Each new lowercase against its own capital, and against the Latin "
        "lowercase it shares a line with",
        [("pairs", FONT % "Regular", 44, ok("Фф Юю Єє Ґґ Дд Жж Лл Чч Ээ Яя")),
         ("pairs bold", FONT % "Bold", 44, ok("Фф Юю Єє Ґґ Дд Жж Лл Чч Ээ Яя")),
         ("vs Latin", FONT % "Regular", 44, ok("oф oю cє rґ vд nл")),
         ("JetBrains", JB % "Regular", 44, ok("Фф Юю Єє Ґґ Дд Жж Лл Чч Ээ Яя"))]))

    parts.append(matched(ok("ФфЮюЄєҐґДдЛл")))

    parts.append(line_block(
        "Same text, this font above JetBrains Mono below (professionally drawn Cyrillic)",
        [("SUSE Mono", FONT % "Regular", 40, ua),
         ("JetBrains", JB % "Regular", 40, ua),
         ("SUSE Mono Bold", FONT % "Bold", 40, ru),
         ("JetBrains Bold", JB % "Bold", 40, ru)]))

    parts.append(line_block(
        "Real sizes (twenty-two lowercase; б з к м still to come)",
        [("14px UA", FONT % "Regular", 14, ua),
         ("14px RU", FONT % "Regular", 14, ru),
         ("12px UA", FONT % "Regular", 12, ua),
         ("12px RU", FONT % "Regular", 12, ru),
         ("14px caps", FONT % "Regular", 14, caps),
         ("14px bold", FONT % "Bold", 14, sentence)]))

    parts.append(line_block(
        "Mixed Latin and Cyrillic in one line -- where a bolted-on script shows",
        [("18px", FONT % "Regular", 18,
          ok("git commit -m 'юність' v2.1 build/ґрунт-єднати.log")),
         ("14px", FONT % "Regular", 14,
          ok("git commit -m 'юність' v2.1 build/ґрунт-єднати.log")),
         ("JetBrains 18px", JB % "Regular", 18,
          ok("git commit -m 'юність' v2.1 build/ґрунт-єднати.log")),
         ("18px caps", FONT % "Regular", 18,
          "git commit -m ПОЛЕ FIXED ЦВІТЕ v2.1 ВІТЕР build/ДМЕ.log")]))

    out = stack(parts)
    out.save("tools/out/checkpoint.png")
    print(f"tools/out/checkpoint.png  {out.size}  ({len(chars)} glyphs)")


main()
