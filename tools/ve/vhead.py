"""Try head_spine settings side by side: `att,r,reach` per tile, Thin or ExtraBold."""
import sys
from PIL import Image
from vform import head_spine
from vpen import ink
from vpen2 import measure
FONT = {"thin": ("fonts/ttf/SUSEMono-ThinItalic.ttf", 28.0),
        "eb": ("fonts/ttf/SUSEMono-ExtraBoldItalic.ttf", 132.0)}
path, w = FONT[sys.argv[1]]
tiles = []
for spec in sys.argv[2:]:
    att, r, reach, q = (float(x) for x in spec.split(","))
    p = head_spine(path, w, att, r, reach, q if q >= 0 else None)
    m, k = ink([(p, True)], w, px=420.0)
    q1, med, q3, holes = measure(m, k)
    print("%-6s %-16s q3/q1 %.2f  counters %d" % (sys.argv[1], spec, q3 / q1, holes))
    tiles.append(Image.fromarray(((~m) * 255).astype("uint8")))
out = Image.new("L", (sum(t.width + 20 for t in tiles), max(t.height for t in tiles)), 255)
x = 0
for t in tiles:
    out.paste(t, (x, 0)); x += t.width + 20
out.save("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
         "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/vhead.png")
