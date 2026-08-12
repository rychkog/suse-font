"""Where a mark sits over its letter, ours beside the face's own.

    ./venv/bin/python tools/marks.py            # every marked letter we draw
    ./venv/bin/python tools/marks.py Ё ё Ў ў    # only these

Every marked Cyrillic here is a composite: the face's own combining mark over
a base this project drew, placed by an anchor at **x = 300**, the middle of
the cell. That is a decision, not a fact -- it is right only if this face
centres its own marks on the cell rather than on the letter. A monospace can
do either, and the difference does not show in any gate: a composite passes
node parity, panel ink and every signature reading with its mark a stem off
centre.

The reading, off the BUILT fonts at every weight, in units:

- **off**: the mark's own middle less the base's, so a positive number means
  the mark sits right of its letter. The face's own accented Latin is the bar
  -- whatever Ë Ï Ü Ă É È do with the same mark is what ours should do.
- **gap**: from the base's top to the mark's underside, which is what makes a
  mark read as attached or as floating, and the first thing to go wrong at the
  heavy end where the mark thickens and the letter grows.

One raster per glyph per weight, drawn at the em so a pixel is a unit and
nothing has to be converted back.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np                                            # noqa: E402
from PIL import Image, ImageDraw, ImageFont                   # noqa: E402
from fontTools.ttLib import TTFont                            # noqa: E402

WEIGHTS = ("Thin", "Regular", "Bold", "ExtraBold")
F = "fonts/ttf/SUSEMono-%s.ttf"

# ours, and under each the face's own letters carrying the same mark
OURS = "ЁёЇїЙйЎўЃѓЌќЀѐЍѝ"
HOST = {"dieresis": "ËËÏÏÜü", "breve": "ĂăŬŭ", "acute": "ÉéÓó",
        "grave": "ÈèÒò"}
MARK = {"Ё": "dieresis", "ё": "dieresis", "Ї": "dieresis", "ї": "dieresis",
        "Й": "breve", "й": "breve", "Ў": "breve", "ў": "breve",
        "Ѓ": "acute", "ѓ": "acute", "Ќ": "acute", "ќ": "acute",
        "Ѐ": "grave", "ѐ": "grave", "Ѝ": "grave", "ѝ": "grave"}


def split(path, ch, upem):
    """(mark box, base box, gap) in units, or None if they touch."""
    fnt = ImageFont.truetype(path, upem)
    img = Image.new("L", (upem * 2, int(upem * 2.4)), 0)
    ImageDraw.Draw(img).text((upem // 2, upem // 2), ch, font=fnt, fill=255)
    m = np.asarray(img) > 127
    rows = np.nonzero(m.any(axis=1))[0]
    if not len(rows):
        return None
    # the topmost band of clear rows inside the ink is the join
    clear = [r for r in range(rows[0], rows[-1])
             if not m[r].any() and m[r + 1:].any()]
    if not clear:
        return None
    cut = clear[0]
    end = cut
    while end + 1 < len(m) and not m[end + 1].any():
        end += 1

    def box(sub, off):
        ys, xs = np.nonzero(sub)
        return xs.min(), xs.max(), ys.min() + off, ys.max() + off

    return box(m[:cut], 0), box(m[end + 1:], end + 1), end + 1 - cut


def read(ch):
    out = []
    for w in WEIGHTS:
        path = F % w
        f = TTFont(path, lazy=True)
        upem = f["head"].unitsPerEm
        f.close()
        r = split(path, ch, upem)
        if r is None:
            out.append(None)
            continue
        mk, base, gap = r
        out.append((((mk[0] + mk[1]) - (base[0] + base[1])) / 2.0, gap,
                    (mk[0] + mk[1]) / 2.0 - upem // 2,
                    (base[0] + base[1]) / 2.0 - upem // 2))
    return out


def line(ch, rows):
    def col(v, i):
        return "  --  " if rows[i] is None else "%6.0f" % rows[i][v]
    return ("   %-3s off %s%s%s%s   mark at %s%s%s%s   letter at %s%s%s%s"
            % (ch, *[col(0, i) for i in range(4)],
               *[col(2, i) for i in range(4)],
               *[col(3, i) for i in range(4)]))


def main():
    want = sys.argv[1:] or list(OURS)
    print("                Thin   Reg   Bold    XB")
    seen = set()
    for ch in want:
        kind = MARK.get(ch)
        print(line(ch, read(ch)))
        if kind and kind not in seen:
            seen.add(kind)
            for host in HOST[kind]:
                print(line(host, read(host)))


if __name__ == "__main__":
    main()
