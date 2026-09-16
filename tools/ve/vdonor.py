"""Can Radon serve as в's donor? Three facts, in order of what would kill it.

1. Do its weights carry the same segments in the same order -- is it an axis?
2. Do our two masters land INSIDE its weight range, or off the end of it?
3. What does it draw, in nodes, and are the extremes on nodes (the F15 test)?
"""
import sys
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
from donor import segments_of, find
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

LIGHT = "MonaspaceRadon-ExtraLightItalic_1.otf"
MID = "MonaspaceRadon-Italic_1.otf"
BOLD = "MonaspaceRadon-ExtraBoldItalic_1.otf"


def wall(path, ch):
    """The letter's thinnest wall, over the face's own o wall."""
    f = TTFont(path, fontNumber=0, lazy=True)
    gs, cm = f.getGlyphSet(), f.getBestCmap()
    out = {}
    for c in (ch, "o"):
        bp = BoundsPen(gs)
        gs[cm[ord(c)]].draw(bp)
        out[c] = bp.bounds
    upem = f["head"].unitsPerEm
    xh = getattr(f["OS/2"], "sxHeight", 0) or 0.5 * upem
    f.close()
    return out, xh


def main():
    segs = {}
    for name, fn in (("light", LIGHT), ("reg", MID), ("bold", BOLD)):
        s, deg = segments_of(find(fn), ord("в"))
        segs[name] = [[k for k, _p in c] for c in s]
        print("%-6s %d contours, %d segments, italic angle %.1f"
              % (name, len(s), sum(len(c) for c in s), deg))
    ok = segs["light"] == segs["reg"] == segs["bold"]
    print("\nsame drawing across three weights: %s" % ("YES" if ok else "NO"))
    if not ok:
        for n in ("light", "reg", "bold"):
            print("  %-6s %s" % (n, segs[n]))
        return
    nodes = sum(len(c) for c in segs["light"])
    print("nodes: %d   (this face's own o draws 8)" % nodes)

    # the F15 format test is already answered -- CFF, so these are the
    # designer's own cubics -- but the node COUNT is the thing that caught
    # Sudo's г at 34, so it is reported rather than assumed.
    print("\nstroke weight, each face against its own o:")
    for label, fn in (("Radon light", LIGHT), ("Radon bold", BOLD)):
        b, xh = wall(find(fn), "в")
        print("  %-12s в %.2f xh wide, o %.2f xh wide"
              % (label, (b["в"][2] - b["в"][0]) / xh,
                 (b["o"][2] - b["o"][0]) / xh))


if __name__ == "__main__":
    main()
