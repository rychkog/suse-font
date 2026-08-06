"""Write Cyrillic glyphs into a Glyphs source.

    python tools/build_cyrillic.py sources/SUSEMono.glyphs

Each glyph is created in EVERY master or not at all, and a glyph is either
component-based in every master or drawn in every master -- mixing the two
breaks interpolation. T1 letters are Glyphs components pointing at the Latin,
never copied paths, so they follow the Latin through the weight axis for free.
"""

import sys

import glyphsLib
from glyphsLib.classes import GSGlyph, GSLayer, GSComponent, GSAnchor
from glyphsLib.types import Point

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from params import Params          # noqa: E402
from classify import TIERS         # noqa: E402
import recipes                     # noqa: E402

WIDTH = 600

# base + mark, both already drawn in place in this family, so the composite
# needs no offset; the marks track the weight axis because they are components
COMPOSITES = {
    "Io-cy": ("Ie-cy", "dieresiscomb.case"),
    "Yi-cy": ("I-cy", "dieresiscomb.case"),
    "Iegrave-cy": ("Ie-cy", "gravecomb.case"),
    "Gje-cy": ("Ge-cy", "acutecomb.case"),
    "Kje-cy": ("Ka-cy", "acutecomb.case"),
    "Iishort-cy": ("Ii-cy", "brevecomb.case"),
    "Igrave-cy": ("Ii-cy", "gravecomb.case"),
    "Ushort-cy": ("U-cy", "brevecomb.case"),
    "io-cy": ("ie-cy", "dieresiscomb"),
    "yi-cy": ("idotless", "dieresiscomb"),
    "iegrave-cy": ("ie-cy", "gravecomb"),
    "ushort-cy": ("u-cy", "brevecomb"),
    "gje-cy": ("ge-cy", "acutecomb"),
    "kje-cy": ("ka-cy", "acutecomb"),
    "iishort-cy": ("ii-cy", "brevecomb"),
    "igrave-cy": ("ii-cy", "gravecomb"),
}


def plan(font):
    """Which target glyphs can be built now, given what already exists.

    A glyph is buildable when every part it needs is present -- so composites
    wait for their base, and the set grows as tiers land.
    """
    have = {g.name for g in font.glyphs}
    out = []
    for cp, name, tier, note in TIERS:
        if name in have:
            continue
        if name in COMPOSITES:
            base, mark = COMPOSITES[name]
            if base in have or base in {n for _, n, _, _ in out}:
                out.append((cp, name, "comp", (base, mark)))
        elif tier == 1:
            if note in have:
                out.append((cp, name, "donor", note))
        elif name in recipes.RECIPES:
            out.append((cp, name, "draw", recipes.RECIPES[name]))
    return out


def anchors(pr, name):
    top = pr.cap if name[0].isupper() else pr.xh
    return [("top", 300, top), ("bottom", 300, 0)]


def rebuild(font):
    """Drop every glyph this script owns, so they are drawn again.

    `plan` deliberately skips whatever already exists, which is what lets the
    set grow a tier at a time. The cost is that changing a recipe changes
    nothing: the glyph is already there. Reverting the source with git worked
    only while the Cyrillic was uncommitted -- afterwards a checkout restores
    the OLD glyphs and the rebuild silently does nothing, which is how a
    corrected tail depth came back identical.
    """
    mine = {name for _, name, _, _ in TIERS}
    gone = [g.name for g in font.glyphs if g.name in mine]
    for name in gone:
        del font.glyphs[name]
    return gone


def main():
    src = sys.argv[1]
    font = glyphsLib.load(src)
    if "--rebuild" in sys.argv:
        print(f"  dropped {len(rebuild(font))} glyphs to redraw them")
    prs = [Params(font, mi) for mi in range(len(font.masters))]

    added = []
    # two passes so composites can see bases added in the first
    for _ in range(2):
        for cp, name, kind, arg in plan(font):
            g = GSGlyph()
            g.name = name
            g.unicodes = ["%04X" % cp]
            for mi, master in enumerate(font.masters):
                layer = GSLayer()
                layer.layerId = master.id
                layer.associatedMasterId = master.id
                layer.width = WIDTH
                if kind == "donor":
                    layer.components.append(GSComponent(arg))
                elif kind == "comp":
                    layer.components.append(GSComponent(arg[0]))
                    layer.components.append(GSComponent(arg[1]))
                else:
                    for p in arg(prs[mi]):
                        layer.paths.append(p)
                    for an, ax, ay in anchors(prs[mi], name):
                        a = GSAnchor()
                        a.name = an
                        a.position = Point(ax, ay)
                        layer.anchors.append(a)
                g.layers.append(layer)
            font.glyphs.append(g)
            added.append(name)

    bad = []
    for g in font.glyphs:
        if g.name not in added:
            continue
        sig = [([len(p.nodes) for p in L.paths],
                [c.name for c in L.components], L.width) for L in g.layers]
        if len(set(map(str, sig))) != 1:
            bad.append(f"{g.name}: {sig[0][0]} vs {sig[1][0]}")
    if bad:
        raise SystemExit("layers differ between masters -- the font will not "
                         "build:\n  " + "\n  ".join(bad))

    before = open(src, encoding="utf-8").read()
    font.save(src)
    restore_instance_names(src, before)
    print(f"  {len(added)} glyphs -> {src}")
    return added


def restore_instance_names(src, before):
    """Put back the instance name glyphsLib renames on write.

    Saving emits the variable-font instance's name under the key
    `variablename` where the original file used `name`. Re-read, that
    instance's name falls back to `Regular` -- and the file already has a
    `Regular`, so the source ends up declaring two instances with the same
    name. The built fonts are unaffected (it sits at axesValues (100,100) on a
    single-axis font and emits nothing), but it is a semantic change to a part
    of the file this tool has no business touching.

    Located by its own Axis Values parameter, which is unique in the file.
    """
    import re
    marker = "ital; 0.0>1.0=Roman*"
    if marker not in before:
        return
    want = re.search(re.escape(marker) + r"[^\n]*\n(?:[^\n]*\n){0,4}?"
                     r"(name = ([^;]+);)", before)
    if not want:
        return
    text = open(src, encoding="utf-8").read()
    fixed, n = re.subn(
        re.escape(marker) + r"([^\n]*\n(?:[^\n]*\n){0,4}?)"
        r"(?:variablename|name) = [^;]+;",
        lambda m: marker + m.group(1) + want.group(1), text, count=1)
    if n:
        open(src, "w", encoding="utf-8").write(fixed)


if __name__ == "__main__":
    main()
