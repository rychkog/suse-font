"""Our в and б beside the two faces that draw the cursive form. Outlines."""
import sys, os, glob
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from panel import font_dirs

REF = ["Monaspace Radon Italic", "Monaspace Radon Bold Italic",
       "Victor Mono Italic"]
OURS = [("SUSE Mono Thin Italic", "fonts/ttf/SUSEMono-ThinItalic.ttf"),
        ("SUSE Mono Italic", "fonts/ttf/SUSEMono-Italic.ttf"),
        ("SUSE Mono ExtraBold Italic", "fonts/ttf/SUSEMono-ExtraBoldItalic.ttf")]

found = {}
for d in font_dirs():
    for p in sorted(glob.glob(os.path.join(d, "*.ttf"))
                    + glob.glob(os.path.join(d, "*.otf"))):
        try:
            f = TTFont(p, fontNumber=0, lazy=True)
            n = f["name"].getDebugName(4) or ""
            if n in REF and n not in found and 0x0432 in f.getBestCmap():
                found[n] = p
            f.close()
        except Exception:
            pass

cells = [(n, found[n], "в") for n in REF if n in found]
cells += [(n, p, "в") for n, p in OURS]
cells += [(n + "  б", p, "б") for n, p in OURS]

PX, PAD = 260, 30
W = PAD + len(cells) * (PX + PAD)
H = PX + 3 * PAD + 40
out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
       'viewBox="0 0 %d %d">' % (W, H, W, H),
       '<rect width="100%%" height="100%%" fill="#faf8f5"/>']
for i, (label, path, ch) in enumerate(cells):
    f = TTFont(path, fontNumber=0, lazy=True)
    cmap, gs, upm = f.getBestCmap(), f.getGlyphSet(), f["head"].unitsPerEm
    pen = SVGPathPen(gs)
    gs[cmap[ord(ch)]].draw(pen)
    d = pen.getCommands()
    k = PX / float(upm)
    ox = PAD + i * (PX + PAD)
    oy = PAD + PX * 0.80
    out.append('<g transform="translate(%.1f %.1f) scale(%.5f %.5f)">'
               '<path d="%s" fill="#1a1a1a" fill-rule="nonzero"/></g>'
               % (ox, oy, k, -k, d))
    out.append('<text x="%d" y="%d" font-size="11" font-family="monospace" '
               'fill="#666">%s</text>' % (ox, H - 16, label[:30]))
    f.close()
out.append('</svg>')
open(sys.argv[1], "w").write("\n".join(out))
print(sys.argv[1], len(cells), "cells")
