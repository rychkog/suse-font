"""Cursive в in six heavy monospaces: lightest and heaviest italic, with x-height and ascender lines."""
import glob, sys
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageDraw, ImageFont
import panel
S = sys.argv[1]
WANT = ("Inconsolata LGC", "Ioskeley Mono", "Lilex", "Lyth Mono", "Maple Mono", "Monaspace Radon", "SUSE Mono")
got = {}
for d in panel.font_dirs():
    for p in glob.glob(d + "/*.ttf") + glob.glob(d + "/*.otf"):
        try:
            f = TTFont(p, fontNumber=0, lazy=True)
            fam = f["name"].getDebugName(16) or f["name"].getDebugName(1) or ""
            full = (f["name"].getDebugName(4) or "") + (f["name"].getDebugName(2) or "")
            if "Italic" not in full or ord("в") not in f.getBestCmap() or "NF" in fam or "Nerd" in fam:
                continue
            for w in WANT:
                if fam.startswith(w) and "Tuned" not in fam and "Variable" not in full:
                    wt = f["OS/2"].usWeightClass
                    lo, hi = got.get(w, ((9999, ""), (0, "")))
                    got[w] = (min(lo, (wt, p)), max(hi, (wt, p)))
            f.close()
        except Exception:
            pass
rows = []
for w in WANT:
    if w not in got:
        continue
    im = Image.new("L", (900, 260), 255); dr = ImageDraw.Draw(im)
    for i, (wt, p) in enumerate(got[w]):
        f = TTFont(p, fontNumber=0); upm = f["head"].unitsPerEm
        xh = f["OS/2"].sxHeight; gs = f.getGlyphSet(); cm = f.getBestCmap()
        bp = BoundsPen(gs); gs[cm[ord("в")]].draw(bp); top = bp.bounds[3]
        bp = BoundsPen(gs); gs[cm[ord("б")]].draw(bp); btop = bp.bounds[3]
        size = 170; base = 215; k = size / upm
        x0 = 20 + i * 440
        for yv, c in ((0, 180), (xh, 120), (btop, 200)):
            dr.line([(x0, base - yv * k), (x0 + 420, base - yv * k)], fill=c)
        fnt = ImageFont.truetype(p, size)
        dr.text((x0, base), "бвоь", font=fnt, fill=0, anchor="ls")
        dr.text((x0, 240), "%s %d  в top %.2f of x-height, б %.2f" % (w, wt, top / xh, btop / xh), fill=0)
    rows.append(im)
out = Image.new("L", (900, 260 * len(rows)), 255)
for i, r in enumerate(rows):
    out.paste(r, (0, 260 * i))
out.save(S + "/vpanel2.png"); print(len(rows))
