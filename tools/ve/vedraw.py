"""The candidate в from source, sheared, both masters, beside б and о."""
import sys, math
sys.path.insert(0, "tools")
from PIL import Image, ImageDraw
import glyphsLib
from params import Params, Lower
from geom import _segments, seg_at, slant, area
import recipes as R

PX, PAD, SS = 250, 20, 2


def poly(p, n=20):
    segs, _ = _segments(p)
    return [seg_at(sg, k / float(n))[0] for sg in segs for k in range(n)]


font = glyphsLib.load(open("sources/SUSEMono-Italic.glyphs"))
cells = 3
W = PAD + cells * (PX + PAD)
H = PAD + 2 * (PX + PAD)
im = Image.new("L", (W * SS, H * SS), 255)
dr = ImageDraw.Draw(im)
for r, mi in enumerate((0, 1)):
    base = Params(font, mi)
    pr = Lower(base)
    k = PX / 1000.0 * SS
    made = [R.Ve_cursive(pr), R.clone_all(base.paths("b")),
            R.clone_all(base.paths("o"))]
    for c, ps in enumerate(made):
        ox = (PAD + c * (PX + PAD)) * SS
        oy = (PAD + r * (PX + PAD)) * SS + PX * SS * 0.72
        for p in slant(ps, base.italic, base.pivot):
            dr.polygon([(ox + x * k, oy - y * k) for x, y in poly(p)],
                       fill=0 if area(p) > 0 else 255)
im.resize((W, H), Image.LANCZOS).save(sys.argv[1])
print("ok")
