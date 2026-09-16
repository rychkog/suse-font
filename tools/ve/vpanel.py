"""Heaviest italic в of every monospace family, one contact sheet."""
import glob, os, sys
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
import panel
S = sys.argv[1]
best = {}
for d in panel.font_dirs():
    for p in sorted(glob.glob(d + "/*.ttf") + glob.glob(d + "/*.otf")):
        try:
            f = TTFont(p, fontNumber=0, lazy=True)
            cm = f.getBestCmap()
            if ord("в") not in cm or ord("б") not in cm:
                continue
            sub = f["name"].getDebugName(2) or ""
            fam = f["name"].getDebugName(16) or f["name"].getDebugName(1) or ""
            full = f["name"].getDebugName(4) or ""
            if "Italic" not in sub and "Oblique" not in sub and "Italic" not in full:
                continue
            if any(s in fam for s in panel.SKIP):
                continue
            hm = f["hmtx"]
            if hm[cm[ord("i")]][0] != hm[cm[ord("m")]][0]:
                continue
            wt = f["OS/2"].usWeightClass
            key = fam
            for suf in (" Extra", " Semi", " Heavy", " Light", " Medium", " Thin", " Black", " Bold"):
                key = key.split(suf)[0]
            if wt >= best.get(key, (0, ""))[0]:
                best[key] = (wt, p)
            f.close()
        except Exception:
            continue
tiles = []
for fam, (wt, p) in sorted(best.items()):
    try:
        fnt = ImageFont.truetype(p, 110)
    except Exception:
        continue
    im = Image.new("L", (300, 190), 255); dr = ImageDraw.Draw(im)
    dr.text((10, 10), "бвьв", font=fnt, fill=0)
    dr.text((5, 170), "%s %d" % (fam[:30], wt), fill=0)
    tiles.append(im)
cols = 6
out = Image.new("L", (300 * cols, 190 * ((len(tiles) + cols - 1) // cols)), 255)
for i, t in enumerate(tiles):
    out.paste(t, ((i % cols) * 300, (i // cols) * 190))
out.save(S + "/vpanel.png"); print(len(tiles))
