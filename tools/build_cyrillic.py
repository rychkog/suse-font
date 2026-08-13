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

# base + mark. The marks track the weight axis for free because they are
# components; WHERE they sit is set below, from the base's own top anchor.
#
# They were placed at the origin at first, on the reasoning that both parts
# are "already drawn in place". Every combining mark in this face does carry
# its `_top` at 300 -- but the letters do not: a mark dropped at the origin
# lands on the middle of the CELL, and this face puts its marks on the middle
# of the LETTER. Nothing in the pipeline could see it. `tools/marks.py` reads
# it against the face's own accented Latin.
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


# Where a mark goes over a letter is the HOST's decision, not the middle of
# the cell. This face places a top anchor per letter and they are not all 300:
# E carries 318 at Thin and 327 at ExtraBold, K 312 and 354, e 313 and 303,
# idotless 332 and 336, y 310 and 307 -- while I, N, T, Y, u, n sit on 300.
# Every base that takes a mark therefore names the host letter it came from,
# and the anchor is read off that letter at that master.
ANCHOR_FROM = {
    "Ie-cy": "E",       # tier 1: it IS E
    "I-cy": "I",
    # К is NOT here any more. It was, while it was the Latin K donated whole,
    # and K's anchor travels further than any other in this table -- 312 at
    # Thin to 354 at ExtraBold. Ќ followed that and its drawn ќ could not, so
    # the pair was knowingly out of step; the ledger says so. К is drawn now
    # and it is symmetric about nothing K is symmetric about, so it takes the
    # middle of the cell, which is where Ѓ ѓ ќ already sit.
    "U-cy": "Y",        # drawn from Y's fork, and a mark sits over the fork
    "Ii-cy": "N",
    "ie-cy": "e",       # tier 1: it IS e
    "u-cy": "y",        # tier 1: it IS y
    "ii-cy": "n",
}


def top_anchor(glyphs, name, mi, which="top"):
    """Where this face puts a mark over that letter, at this master.

    Read through a donor component, because a tier 1 glyph carries no anchor
    of its own -- it IS the host letter, and so is its answer. `which` is
    "top" on a letter and "_top" on a combining mark, which is the anchor the
    mark is aligned BY.
    """
    layer = glyphs[name].layers[mi]
    for a in layer.anchors:
        if a.name == which:
            return a.position.x
    if len(layer.components) == 1:
        return top_anchor(glyphs, layer.components[0].name, mi)
    donor = ANCHOR_FROM.get(name)
    return top_anchor(glyphs, donor, mi) if donor else 300


def anchors(pr, name):
    top = pr.cap if name[0].isupper() else pr.xh
    donor = ANCHOR_FROM.get(name)
    x = top_anchor(pr.G, donor, pr.mi) if donor else 300
    return [("top", x, top), ("bottom", 300, 0)]


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
    marks = []
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
                    marks.append((layer, mi, arg[0], arg[1]))
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

    # Slide each mark onto its base's own top anchor. Done here rather than
    # where the component is made, because a composite can be written before
    # its base in the same pass and the base's anchor has to exist to be read.
    glyphs = {g.name: g for g in font.glyphs}
    for layer, mi, base, mark in marks:
        dx = (top_anchor(glyphs, base, mi)
              - top_anchor(glyphs, mark, mi, "_top"))
        if dx:
            layer.components[1].position = Point(dx, 0)

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
