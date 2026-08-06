#!/usr/bin/env bash
# Regenerate EVERY review image from the CURRENT build, so nothing shown is
# stale. Reviewing an image rendered before the last fix wastes a round.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
./venv/bin/python tools/checkpoint.py A >/dev/null
./venv/bin/python - <<'PY'
from PIL import Image, ImageDraw, ImageFont
F = "fonts/ttf/SUSEMono-%s.ttf"
JB = "/mnt/c/Users/Admin/AppData/Local/Microsoft/Windows/Fonts/JetBrainsMono-%s.ttf"
lab = ImageFont.truetype("/mnt/c/Windows/Fonts/segoeui.ttf", 17)


def sheet(path, rows, text, size, adv):
    """One row per weight. `adv` is generous so descenders and wide letters
    never collide -- overlapping glyphs make a sheet unreadable."""
    rh = int(size * 1.55)
    im = Image.new("RGB", (200 + adv * len(text), len(rows) * rh + 30), "white")
    d = ImageDraw.Draw(im)
    y = 15
    for name, fp in rows:
        col = (0, 110, 0) if "JetBrains" in name else (140, 140, 140)
        d.text((6, y + size * 0.45), name, font=lab, fill=col)
        f = ImageFont.truetype(fp, size)
        for i, ch in enumerate(text):
            d.text((190 + i * adv, y - size * 0.08), ch, font=f, fill=(0, 0, 0))
        d.line([(0, y + rh - 10), (im.width, y + rh - 10)], fill=(235, 235, 235))
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
print("regenerated audit.png, be_big.png, checkpoint.png")
PY
