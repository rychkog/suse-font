"""The picture that goes with `signature.py`.

The probe answers in numbers and the verdict is by eye, so the readings are
worth nothing on their own: this sheet puts each of them beside the Latin
letter whose habit it was measured against. Three sections, in the order the
question is actually asked -- does every stroke end the way the face ends its
own, is any horizontal the wrong weight for its case, and does the whole thing
still hold at the sizes the face is read at.

The letters named under HOW HEAVY A HORIZONTAL IS are the ones in the probe's
`ACCEPTED` table. They are shown rather than hidden, because "explained" is a
claim the eye should be able to check.
"""

import glob
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from PIL import Image, ImageDraw, ImageFont  # noqa: E402
from fontTools.ttLib import TTFont  # noqa: E402
from panel import font_dirs  # noqa: E402

SS = 4
W, H = 1660, 1655
BG, FG, MUT, HOT = (250, 250, 249), (24, 24, 24), (140, 140, 140), (176, 32, 32)

OURS = [("Thin", "fonts/ttf/SUSEMono-Thin.ttf"),
        ("Regular", "fonts/ttf/SUSEMono-Regular.ttf"),
        ("Bold", "fonts/ttf/SUSEMono-Bold.ttf"),
        ("ExtraBold", "fonts/ttf/SUSEMono-ExtraBold.ttf")]

# з к м б are not drawn yet, so no string here may contain one -- a .notdef
# box in a review sheet reads as a broken glyph and costs the round it appears
# in. This one caught з on its first render.
CAPS_ROW = "ГЕЖЗИЙЛПТУФЦЧШЩЭЮЯ  KVWXZEFTLS"
LC_ROW = "гежийлптуфцчшщэюя  kvwxzeftls"


def lab(sz):
    for d in font_dirs():
        for n in ("segoeui.ttf", "DejaVuSans.ttf",
                  "LiberationSans-Regular.ttf"):
            hit = glob.glob(d + "/" + n)
            if hit:
                return ImageFont.truetype(hit[0], sz)
    return ImageFont.load_default()


def cap_of(path):
    f = TTFont(path, lazy=True)
    c = f["OS/2"].sCapHeight / float(f["head"].unitsPerEm)
    f.close()
    return c


def matched(path, px):
    """Point size at which this weight's cap height is `px`.

    Comparing at equal point size compares nothing: the weights would differ
    in size as well as in the thing being looked at.
    """
    return int(round(px / cap_of(path)))


def main():
    img = Image.new("RGB", (W * SS, H * SS), BG)
    d = ImageDraw.Draw(img)

    def S(v):
        return v * SS

    title, head, note = lab(S(27)), lab(S(20)), lab(S(16))

    y = S(28)
    d.text((S(40), y), "Does it belong? — the drawn Cyrillic against the "
           "face's own Latin", font=title, fill=FG)
    y += S(40)
    d.text((S(40), y), "Two habits read off the Latin and applied to the "
           "forty-five glyphs this project actually draws: how a stroke ends, "
           "and how heavy a horizontal is.", font=note, fill=MUT)
    y += S(26)
    d.text((S(40), y), "The other forty drawn glyphs are the face's own "
           "outlines reused, so they carry the signature by construction.",
           font=note, fill=MUT)
    y += S(48)

    d.text((S(40), y), "HOW EVERY STROKE ENDS — clean, at both masters",
           font=head, fill=FG)
    y += S(30)
    d.text((S(40), y), "The face ends a stroke square, or chamfers it by up "
           "to 45°, and nothing else. Every terminal in every drawn letter "
           "does one of those two.", font=note, fill=MUT)
    y += S(34)

    for row in (CAPS_ROW, LC_ROW):
        for name, path in OURS:
            f = ImageFont.truetype(path, matched(path, S(40)))
            d.text((S(40), y + S(6)), name, font=note, fill=MUT)
            d.text((S(200), y), row, font=f, fill=FG)
            y += S(66)
        y += S(6)

    y += S(12)
    d.text((S(40), y), "The one it called foreign first, and why it was not — "
           "э's opening at the heavy end", font=head, fill=FG)
    y += S(30)
    d.text((S(40), y), "э chamfers where Э is square. So does c where C is "
           "square: it is the lowercase's own treatment, appearing on the "
           "side the letter opens on.", font=note, fill=MUT)
    y += S(34)
    big = ImageFont.truetype(OURS[3][1], matched(OURS[3][1], S(104)))
    d.text((S(200), y), "э Э   c C", font=big, fill=FG)
    y += S(168)

    d.text((S(40), y), "HOW HEAVY A HORIZONTAL IS — three letters sit outside "
           "the Latin's own range, each for a reason", font=head, fill=HOT)
    y += S(30)
    for line in ("в — its horizontals take B's own figures, which fall from "
                 "0.96 of the bar to 0.90. Recorded when it was approved.",
                 "Ы ы — three strokes have to fit across one cell, so the "
                 "whole letter is shaved. That is the answer Ш already gives.",
                 "Ф ф — one unit over the Latin's heaviest at Thin, two per "
                 "cent under its lightest at Regular. Both approved."):
        d.text((S(40), y), line, font=note, fill=MUT)
        y += S(24)
    y += S(10)

    for name, path in OURS:
        f = ImageFont.truetype(path, matched(path, S(44)))
        d.text((S(40), y + S(8)), name, font=note, fill=MUT)
        d.text((S(200), y), "в В   ы Ы   ф Ф      n t   B Ш", font=f, fill=FG)
        y += S(76)

    y += S(16)
    d.text((S(40), y), "IN WORDS, AT READING SIZE — where a foreign letter "
           "shows first", font=head, fill=FG)
    y += S(34)

    for px in (18, 14, 12):
        for name, path in (OURS[1], OURS[2]):
            f = ImageFont.truetype(path, px * SS)
            d.text((S(40), y), f"{name} {px}px", font=note, fill=MUT)
            d.text((S(230), y), "эхо тоже выше сыр   жовтий вечір їжа   "
                   "git commit -m 'ежа' v2.1", font=f, fill=FG)
            y += S(30)
        y += S(10)

    img.resize((W, H), Image.LANCZOS).save("tools/out/signature.png")


if __name__ == "__main__":
    main()
    print("tools/out/signature.png")
