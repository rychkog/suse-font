"""pen_spine settings beside the user's drawing. Tile: `lean,r,gap,vee,bulge`."""
import sys
from PIL import Image
from vform import pen_spine
from vpen import ink
from vpen2 import measure, fill_specks
S = ("/tmp/claude-1000/-home-geo-Projects-pets-suse-mono-cyrillic/"
     "f723bc1d-71b6-4ff5-8fc8-7b61e648f507/scratchpad/")
FONT = {"thin": ("fonts/ttf/SUSEMono-ThinItalic.ttf", 28.0),
        "eb": ("fonts/ttf/SUSEMono-ExtraBoldItalic.ttf", 132.0)}
path, w = FONT[sys.argv[1]]
tiles = []
for spec in sys.argv[2:]:
    r, merge, scale, wide = (float(x) for x in spec.split(","))
    p = pen_spine(path, w, 18.0, r, 0.0, 65.0, 0.0, scale=scale, split=0.6, merge=merge,
                  full=0.65, psi=-40.0, wide=wide)
    xs = [q[0] for q in p]
    print("   ink width %3.0f" % (max(xs) - min(xs) + w))
    print("   turn crosses at u=%.0f" % 0 if False else "", end="")
    m, k = ink([(p, False)], w, px=420.0)
    m = fill_specks(m, k, w)
    q1, med, q3, holes = measure(m, k)
    print("%-6s %-24s q3/q1 %.2f  counters %d" % (sys.argv[1], spec, q3 / q1, holes))
    tiles.append(Image.fromarray(((~m) * 255).astype("uint8")))
ref = Image.open(S + "ref3.png").convert("L").crop((60, 0, 280, 420))
ref = ref.resize((int(ref.width * 460 / ref.height), 460))
tiles.insert(0, ref)
out = Image.new("L", (sum(t.width + 30 for t in tiles), max(t.height for t in tiles)), 255)
x = 0
for t in tiles:
    out.paste(t, (x, 0)); x += t.width + 30
out.save(S + "vpenform.png")
