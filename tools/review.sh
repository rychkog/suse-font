#!/usr/bin/env bash
# Regenerate EVERY review image from the CURRENT build, so nothing shown is
# stale. Reviewing an image rendered before the last fix wastes a round.
#
# It said EVERY and regenerated four, which is the same lie as a stale picture
# and worse for being automated: the italic sheets, the cursive pair and the
# outline sheet were all left behind, and the ones it did make were the only
# ones anyone thought were current.
#
# Every sheet here is drawn well above its delivered size and resolved down --
# see CLAUDE.md. Anything added below has to do the same or it does not belong
# on a review sheet.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
./venv/bin/python tools/checkpoint.py A >/dev/null
./venv/bin/python tools/signature_sheet.py >/dev/null
./venv/bin/python tools/be_sheet.py >/dev/null
./venv/bin/python tools/italic_sheet.py >/dev/null
./venv/bin/python tools/cursive_sheet.py >/dev/null
./venv/bin/python tools/specimen.py >/dev/null
./venv/bin/python tools/outlines.py >/dev/null
./venv/bin/python tools/gd_donors.py >/dev/null
./venv/bin/python tools/de_arm.py >/dev/null
./venv/bin/python tools/de_vs_d.py >/dev/null
./venv/bin/python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
F = "fonts/ttf/SUSEMono-%s.ttf"
import sys; sys.path.insert(0, 'tools')
from panel import font_dirs
def _jb():
    """JetBrains Mono's path pattern, found rather than hardcoded."""
    import glob as _g
    for d in font_dirs():
        hit = _g.glob(d + "/JetBrainsMono-Regular.ttf")
        if hit:
            return hit[0].replace("Regular", "%s")
    raise SystemExit("JetBrains Mono not found; set SUSE_FONT_DIRS")

JB = _jb()

# Every size on these two sheets is a display size -- there is no real-reading
# row here -- so the whole sheet is simply drawn twice as large. Rendering at
# the delivered size and hoping the screen is 1:1 is what made them pixelate.
SCALE = 2


def _lab(sz):
    import glob as _g
    for d in font_dirs():
        for n in ("segoeui.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
            hit = _g.glob(d + "/" + n)
            if hit:
                return ImageFont.truetype(hit[0], sz)
    return ImageFont.load_default()


lab = _lab(17 * SCALE)


def sheet(path, rows, text, size, adv):
    """One row per weight. `adv` is generous so descenders and wide letters
    never collide -- overlapping glyphs make a sheet unreadable."""
    size, adv = size * SCALE, adv * SCALE
    rh = int(size * 1.55)
    im = Image.new("RGB", (200 * SCALE + adv * len(text),
                           len(rows) * rh + 30 * SCALE), "white")
    d = ImageDraw.Draw(im)
    y = 15 * SCALE
    for name, fp in rows:
        col = (0, 110, 0) if "JetBrains" in name else (140, 140, 140)
        d.text((6 * SCALE, y + size * 0.45), name, font=lab, fill=col)
        f = ImageFont.truetype(fp, size)
        for i, ch in enumerate(text):
            d.text((190 * SCALE + i * adv, y - size * 0.08), ch, font=f,
                   fill=(0, 0, 0))
        d.line([(0, y + rh - 10 * SCALE), (im.width, y + rh - 10 * SCALE)],
               fill=(235, 235, 235))
        y += rh
    im.save(path)


sheet("tools/out/audit.png",
      [("SUSE " + w, F % w) for w in ("Thin", "Regular", "Bold", "ExtraBold")],
      "ФҐДБЮЦЩЛ", 120, 150)
sheet("tools/out/be_big.png",
      [("SUSE Regular", F % "Regular"), ("JetBrains Regular", JB % "Regular"),
       ("SUSE Bold", F % "Bold"), ("JetBrains Bold", JB % "Bold"),
       ("SUSE ExtraBold", F % "ExtraBold"), ("JetBrains ExtraBold", JB % "ExtraBold")],
      "БДЦЩ", 150, 190)
print("regenerated audit.png and be_big.png")
PY
echo "regenerated: checkpoint signature be_sheet italic_sheet cursive_sheet" \
     "specimen outlines gd_donors de_arm de_vs_d audit be_big"
