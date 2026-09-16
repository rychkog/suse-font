"""draw_spine settings beside the user's drawing.
Each tile: `att,q,lean,W,drop,rlean`."""
import sys
from PIL import Image
from vform import draw_spine
from vpen import ink
from vpen2 import measure
S = ("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
     "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/")
FONT = {"thin": ("fonts/ttf/SUSEMono-ThinItalic.ttf", 28.0),
        "eb": ("fonts/ttf/SUSEMono-ExtraBoldItalic.ttf", 132.0)}
path, w = FONT[sys.argv[1]]
tiles = []
for spec in sys.argv[2:]:
    att, q, lean, W, drop, rlean, pull, rnd, apex, soft = (float(x) for x in spec.split(","))
    p = draw_spine(path, w, att, q, lean, W, 0.80, drop, rlean, pull, rnd, apex, int(soft), cap=rnd < 0)
    m, k = ink([(p, False)], w, px=420.0)
    q1, med, q3, holes = measure(m, k)
    print("%-6s %-26s q3/q1 %.2f  counters %d" % (sys.argv[1], spec, q3 / q1, holes))
    tiles.append(Image.fromarray(((~m) * 255).astype("uint8")))
ref = Image.open(S + "ref2.png").convert("L").crop((20, 85, 185, 420))
ref = ref.resize((int(ref.width * 460 / ref.height), 460))
tiles.insert(0, ref)
out = Image.new("L", (sum(t.width + 30 for t in tiles), max(t.height for t in tiles)), 255)
x = 0
for t in tiles:
    out.paste(t, (x, 0)); x += t.width + 30
out.save(S + "vdraw.png")
