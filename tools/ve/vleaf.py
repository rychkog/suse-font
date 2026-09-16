"""leaf_spine settings side by side, with the reference scaled beside them.
Each tile: `att,neck,leanL,leanR,eye`."""
import sys
import numpy as np
from PIL import Image
from vform import leaf_spine, strip_spine
from vpen import ink
from vpen2 import measure
FONT = {"thin": ("fonts/ttf/SUSEMono-ThinItalic.ttf", 28.0),
        "eb": ("fonts/ttf/SUSEMono-ExtraBoldItalic.ttf", 132.0)}
path, w = FONT[sys.argv[1]]
tiles = []
for spec in sys.argv[2:]:
    att, neck, lean, eye, close, bow = (float(x) for x in spec.split(","))
    p = strip_spine(path, w, att, neck, lean, eye, close, 0.80, bow=bow, curl=True)
    m, k = ink([(p, False)], w, px=420.0)
    q1, med, q3, holes = measure(m, k)
    print("%-6s %-22s q3/q1 %.2f  counters %d" % (sys.argv[1], spec, q3 / q1, holes))
    tiles.append(Image.fromarray(((~m) * 255).astype("uint8")))
ref = Image.open('/mnt/c/Users/Admin/AppData/Local/Packages/Microsoft.Paint_8wekyb3d8bbwe/'
                 'TempState/2026-09-16_07-26.png').convert("L")
ref = ref.resize((int(ref.width * 460 / ref.height), 460))
tiles.insert(0, ref)
out = Image.new("L", (sum(t.width + 30 for t in tiles), max(t.height for t in tiles)), 255)
x = 0
for t in tiles:
    out.paste(t, (x, 0)); x += t.width + 30
out.save("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
         "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/vleaf.png")
