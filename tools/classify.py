"""Tier table for the Cyrillic build: what is derived, and from what.

Target set is U+0400-U+045F plus Ґ ґ (U+0490/0491). The Ukrainian and
Belarusian letters Є є І і Ї ї Ў ў already fall inside that range.

The tiers exist to keep drawing to a minimum. The Latin in this family has
already been condensed and optically fitted to a 600-unit cell; a glyph
derived from it inherits that work, and a glyph drawn fresh throws it away.
So each letter is assigned the highest tier it can honestly take:

  T1  the same drawing as a Latin glyph -- a Glyphs COMPONENT, never a
      copied path, so it tracks the Latin through both masters for free
  T2  assembled from components and parts that already exist
  T3  genuinely new outlines, drawn once and node-matched across masters

Two rules constrain T2/T3 and are worth stating because they rule out the
obvious shortcuts:

  * No mirroring. И is not a flipped Н, Я is not a flipped R, Э is not a
    flipped С. Mirroring reverses the terminal cuts and whatever stroke
    modulation the face has, and a Cyrillic reader sees it immediately.
  * No scaling capitals down for lowercase. Cyrillic lowercase is largely
    small-capital in shape, which makes it tempting, but a scaled capital is
    too light and too narrow next to the Latin lowercase. Lowercase is drawn
    at lowercase stem weight.
"""

# (codepoint, glyph name, tier, note)
#
# T1 donors are named; T2 lists the parts it is assembled from; T3 says what
# the drawing is based on, which is not the same as being derived from it.
TIERS = [
    # ---- capitals ------------------------------------------------------
    (0x0410, "A-cy", 1, "A"),
    (0x0411, "Be-cy", 2, "Ge-cy arm + В's lower bowl"),
    (0x0412, "Ve-cy", 1, "B"),
    (0x0413, "Ge-cy", 2, "E's spine and upper arm"),
    (0x0490, "Gheupturn-cy", 2, "Ge-cy + upturn"),
    (0x0414, "De-cy", 2, "El-cy on a plinth with legs"),
    (0x0415, "Ie-cy", 1, "E"),
    (0x0401, "Io-cy", 2, "Ie-cy + dieresiscomb.case"),
    (0x0404, "E-cy", 2, "C + E's middle arm"),
    (0x0416, "Zhe-cy", 3, "drawn: stem + four arms"),
    (0x0417, "Ze-cy", 3, "drawn: two lobes, three's proportions"),
    (0x0418, "Ii-cy", 3, "drawn: two stems + rising diagonal"),
    (0x0406, "I-cy", 1, "I"),
    (0x0407, "Yi-cy", 2, "I-cy + dieresiscomb.case"),
    (0x0419, "Iishort-cy", 2, "Ii-cy + brevecomb.case"),
    (0x041A, "Ka-cy", 1, "K"),
    (0x041B, "El-cy", 2, "stem + splayed leg + arm"),
    (0x041C, "Em-cy", 1, "M"),
    (0x041D, "En-cy", 1, "H"),
    (0x041E, "O-cy", 1, "O"),
    (0x041F, "Pe-cy", 2, "two stems + arm"),
    (0x0420, "Er-cy", 1, "P"),
    (0x0421, "Es-cy", 1, "C"),
    (0x0422, "Te-cy", 1, "T"),
    (0x0423, "U-cy", 3, "drawn: Y's fork carried into a descender"),
    (0x040E, "Ushort-cy", 2, "U-cy + brevecomb.case"),
    (0x0424, "Ef-cy", 2, "bowl + full-height stem"),
    (0x0425, "Ha-cy", 1, "X"),
    (0x0426, "Tse-cy", 2, "two stems + bar + tail"),
    (0x0427, "Che-cy", 3, "drawn: cup on a full-height stem"),
    (0x0428, "Sha-cy", 2, "three stems + bar"),
    (0x0429, "Shcha-cy", 2, "Sha-cy + tail"),
    (0x042A, "Hardsign-cy", 3, "drawn: shoulder + stem + bowl"),
    (0x042B, "Yeru-cy", 3, "drawn: Softsign-cy + detached stem"),
    (0x042C, "Softsign-cy", 3, "drawn: stem + lower bowl"),
    (0x042D, "Ereversed-cy", 3, "drawn: C's aperture reversed, redrawn"),
    (0x042E, "Yu-cy", 2, "stem + bar + bowl"),
    (0x042F, "Ya-cy", 3, "drawn: bowl left, leg right"),
    # Serbian / Macedonian
    (0x0402, "Dje-cy", 3, "drawn: Tshe-cy + descending tail"),
    (0x0403, "Gje-cy", 2, "Ge-cy + acutecomb.case"),
    (0x0405, "Dze-cy", 1, "S"),
    (0x0408, "Je-cy", 1, "J"),
    (0x0409, "Lje-cy", 2, "El-cy + Softsign-cy"),
    (0x040A, "Nje-cy", 2, "En-cy + Softsign-cy"),
    (0x040B, "Tshe-cy", 3, "drawn: T with a crossbar and shoulder"),
    (0x040C, "Kje-cy", 2, "Ka-cy + acutecomb.case"),
    (0x040F, "Dzhe-cy", 2, "Tse-cy with a centred tail"),
    (0x0400, "Iegrave-cy", 2, "Ie-cy + gravecomb.case"),
    (0x040D, "Igrave-cy", 2, "Ii-cy + gravecomb.case"),
    # ---- lowercase -----------------------------------------------------
    (0x0430, "a-cy", 1, "a"),
    (0x0431, "be-cy", 3, "drawn: bowl + ascender + flag"),
    (0x0432, "ve-cy", 3, "drawn: two lobes at x-height"),
    (0x0433, "ge-cy", 3, "drawn: stem + arm at x-height"),
    (0x0491, "gheupturn-cy", 2, "ge-cy + upturn"),
    (0x0434, "de-cy", 3, "drawn: de at x-height with legs"),
    (0x0435, "ie-cy", 1, "e"),
    (0x0451, "io-cy", 2, "ie-cy + dieresiscomb"),
    (0x0454, "e-cy", 3, "drawn: c + middle arm at x-height"),
    (0x0436, "zhe-cy", 3, "drawn at lowercase weight"),
    (0x0437, "ze-cy", 3, "drawn at lowercase weight"),
    (0x0438, "ii-cy", 3, "drawn at lowercase weight"),
    (0x0456, "i-cy", 1, "i"),
    (0x0457, "yi-cy", 2, "idotless + dieresiscomb"),
    (0x0439, "iishort-cy", 2, "ii-cy + brevecomb"),
    (0x043A, "ka-cy", 2, "k's arm and leg + stem cut to x-height"),
    (0x043B, "el-cy", 3, "drawn at lowercase weight"),
    (0x043C, "em-cy", 3, "drawn at lowercase weight"),
    (0x043D, "en-cy", 3, "drawn at lowercase weight"),
    (0x043E, "o-cy", 1, "o"),
    (0x043F, "pe-cy", 3, "drawn at lowercase weight"),
    (0x0440, "er-cy", 1, "p"),
    (0x0441, "es-cy", 1, "c"),
    (0x0442, "te-cy", 3, "drawn at lowercase weight"),
    (0x0443, "u-cy", 1, "y"),
    (0x045E, "ushort-cy", 2, "u-cy + brevecomb"),
    (0x0444, "ef-cy", 3, "drawn: bowl + ascender-to-descender stem"),
    (0x0445, "ha-cy", 1, "x"),
    (0x0446, "tse-cy", 3, "drawn at lowercase weight"),
    (0x0447, "che-cy", 3, "drawn at lowercase weight"),
    (0x0448, "sha-cy", 3, "drawn at lowercase weight"),
    (0x0449, "shcha-cy", 3, "drawn at lowercase weight"),
    (0x044A, "hardsign-cy", 3, "drawn at lowercase weight"),
    (0x044B, "yeru-cy", 3, "drawn at lowercase weight"),
    (0x044C, "softsign-cy", 3, "drawn at lowercase weight"),
    (0x044D, "ereversed-cy", 3, "drawn at lowercase weight"),
    (0x044E, "yu-cy", 3, "drawn at lowercase weight"),
    (0x044F, "ya-cy", 3, "drawn at lowercase weight"),
    (0x0452, "dje-cy", 3, "drawn at lowercase weight"),
    (0x0453, "gje-cy", 2, "ge-cy + acutecomb"),
    (0x0455, "dze-cy", 1, "s"),
    (0x0458, "je-cy", 1, "j"),
    (0x0459, "lje-cy", 3, "drawn at lowercase weight"),
    (0x045A, "nje-cy", 3, "drawn at lowercase weight"),
    (0x045B, "tshe-cy", 3, "drawn at lowercase weight"),
    (0x045C, "kje-cy", 2, "ka-cy + acutecomb"),
    (0x045F, "dzhe-cy", 3, "drawn at lowercase weight"),
    (0x0450, "iegrave-cy", 2, "ie-cy + gravecomb"),
    (0x045D, "igrave-cy", 2, "ii-cy + gravecomb"),
    # the Ukrainian apostrophe, absent upstream under this encoding
    (0x02BC, "apostrophemod", 1, "quoteright"),
]


def by_tier(t):
    return [r for r in TIERS if r[2] == t]


if __name__ == "__main__":
    for t in (1, 2, 3):
        rows = by_tier(t)
        print(f"\n=== T{t}: {len(rows)} glyphs ===")
        for cp, name, _, note in rows:
            print(f"  U+{cp:04X} {chr(cp)}  {name:16} {note}")
    print(f"\ntotal {len(TIERS)}  "
          f"(T1 {len(by_tier(1))}, T2 {len(by_tier(2))}, T3 {len(by_tier(3))})")
