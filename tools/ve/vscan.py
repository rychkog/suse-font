"""Which installed italics draw в as the CURSIVE form, and how light do they go.

The tell is height: the upright sheared stays inside the x-height, the cursive
rises onto the ascender line. Everything is reported over the face's own o, so
a light face and a heavy one are on one ruler.
"""
import glob, os, sys
sys.path.insert(0, "tools")
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from panel import font_dirs

SKIP = ("Nerd Font", " NF", "Term")


def main():
    seen, rows = set(), []
    for d in font_dirs():
        for p in sorted(glob.glob(d + "/*.ttf") + glob.glob(d + "/*.otf")):
            try:
                f = TTFont(p, fontNumber=0, lazy=True)
            except Exception:
                continue
            try:
                cm = f.getBestCmap()
                sub = f["name"].getDebugName(2) or ""
                fam = f["name"].getDebugName(1) or ""
                if "Italic" not in sub and "Oblique" not in sub:
                    continue
                if any(s in fam for s in SKIP) or ord("в") not in cm:
                    continue
                upem = f["head"].unitsPerEm
                xh = getattr(f["OS/2"], "sxHeight", 0) or 0.5 * upem
                gs = f.getGlyphSet()
                b = {}
                for c in "во":
                    bp = BoundsPen(gs)
                    gs[cm[ord(c)]].draw(bp)
                    b[c] = bp.bounds
                if not b["в"] or not b["о"]:
                    continue
                tall = (b["в"][3] - b["в"][1]) / xh
                if tall < 1.20:
                    continue
                # o's wall, as a share of the x-height: the lightness ruler
                ow = (b["о"][2] - b["о"][0]) / xh
                key = (fam, round(tall, 2))
                if key in seen:
                    continue
                seen.add(key)
                rows.append((ow, fam, sub, tall, os.path.basename(p)))
            except Exception:
                pass
            finally:
                f.close()
    print("italics drawing в taller than 1.2 x-heights: %d" % len(rows))
    for ow, fam, sub, tall, base in sorted(rows):
        print("  %-34s %-18s в %.2f xh tall   o %.2f xh wide"
              % (fam[:34], sub[:18], tall, ow))


if __name__ == "__main__":
    main()
