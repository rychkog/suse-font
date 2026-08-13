"""Does a monospace italic use the CURSIVE Cyrillic lowercase, or the upright
sloped?

    ./venv/bin/python tools/italic_forms.py
    ./venv/bin/python tools/italic_forms.py --draw

This is the italic's version of the К question, and it has to be answered
before a single lowercase italic recipe is written, because the two answers do
not differ by a proportion -- they are different letters.

Cyrillic italic has a set of lowercase forms inherited from handwriting, and
they are not the upright shapes leaning over:

    и becomes a u        п becomes an n        т becomes an m
    г becomes a curve    д becomes a g-like    й is that u with a breve

A reader of Russian or Ukrainian expects them in a text italic and would read
"пиши" set in sloped-upright forms as a different, stiffer register. A
monospace is not a text face, though, and some of them keep the upright shapes
on purpose so that a name in italics still spells itself the same way at 12px.
Both answers exist. The panel says which one this kind of font takes.

The reading is deliberately structural rather than metric, because that is
what F13 cost: for each face, its italic Cyrillic letter is compared with its
OWN italic Latin counterpart -- и against u, п against n, т against m, д
against g. One file, no cross-font registration, no shear. A cursive и IS that
face's u, to within its own fitting; a sloped upright и is nowhere near it,
because it still has a diagonal in it and u has none.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import math                                                    # noqa: E402

from fontTools.ttLib import TTFont                             # noqa: E402
from fontTools.pens.recordingPen import DecomposingRecordingPen  # noqa: E402

# the letter, the Latin its cursive form is, and what the upright form is
PAIRS = (("и", "u", "two stems and a diagonal"),
         ("п", "n", "two stems under a flat bar"),
         ("т", "m", "one stem under a flat bar"),
         ("д", "g", "a body on a plinth with two legs"),
         ("в", "b", "two lobes on a stem"),
         ("г", "r", "a stem under a flat arm"))
SAME = 0.075            # closer than this and it IS the Latin letter


def outline(f, cm, gs, ch, em):
    if ord(ch) not in cm:
        return None
    pen = DecomposingRecordingPen(gs)
    gs[cm[ord(ch)]].draw(pen)
    pts = [(v[0][0] / em, v[0][1] / em) for op, v in pen.value
           if op in ("moveTo", "lineTo", "curveTo", "qCurveTo") for v in [v]]
    # curveTo/qCurveTo carry control points too; take every one, they all sit
    # on or near the drawing and the metric below is a nearest-point distance
    pts = [(x, y) for op, v in pen.value if op != "closePath"
           for x, y in [(p[0] / em, p[1] / em) for p in v]]
    return pts or None


def worst(a, b):
    """Furthest either drawing sits from the nearest point of the other."""
    def one(u, v):
        return max(min(math.hypot(px - qx, py - qy) for qx, qy in v)
                   for px, py in u)
    return max(one(a, b), one(b, a))


def register(pts):
    """On the ink's own left edge and baseline: a monospace italic fits each
    letter in its cell separately, and that is not the question here."""
    x0 = min(p[0] for p in pts)
    y0 = min(p[1] for p in pts)
    return [(x - x0, y - y0) for x, y in pts]


LOWER = "абвгдежзийклмнопрстуфхцчшщъыьэюя"


def changed():
    """Which lowercase does a face REDRAW in its italic, rather than slope?

    The и=u reading answers "is this letter the Latin one", which is the wrong
    question for every cursive form that has no Latin counterpart -- the
    cursive д is a ∂ and the cursive г is a stroke of its own, so comparing
    them to g and r said "not cursive" about faces that visibly draw both. That
    is F13 from the other side: a test that can only find the letters it was
    told to look for.

    This asks the question with no Latin in it. For each family that ships both,
    its italic Cyrillic is compared with its OWN upright Cyrillic sheared by its
    own angle. A letter the face merely slopes reads near zero. A letter it
    redraws does not, whatever shape it redrew it into.

    Registration is on the ink's own box, which absorbs the pivot -- a shear
    about a different height differs from this one by a translation only.
    """
    from panel import families, italics
    from fontTools.ttLib import TTFont
    ups = {}
    for fam, p in families():
        ups.setdefault(fam.replace(" (heaviest)", ""), p)
    rows, tally = [], {c: [0, 0] for c in LOWER}
    for fam, ip in italics():
        if fam not in ups:
            continue
        try:
            fi = TTFont(ip, fontNumber=0, lazy=True)
            fu = TTFont(ups[fam], fontNumber=0, lazy=True)
        except Exception:
            continue
        try:
            ang = abs(getattr(fi["post"], "italicAngle", 0.0)) or 12.0
            t = math.tan(math.radians(ang))
            ci, cu = fi.getBestCmap(), fu.getBestCmap()
            gi, gu = fi.getGlyphSet(), fu.getGlyphSet()
            ei = fi["head"].unitsPerEm / 1000.0
            eu = fu["head"].unitsPerEm / 1000.0
            got = {}
            for ch in LOWER:
                a = outline(fu, cu, gu, ch, eu)
                b = outline(fi, ci, gi, ch, ei)
                if a is None or b is None:
                    continue
                sh = [(x + t * y, y) for x, y in a]
                d = worst(register(sh), register(b)) / 1000.0
                got[ch] = d
                tally[ch][0 if d >= 0.045 else 1] += 1
            if got:
                rows.append((fam, got))
        except Exception:
            pass
        finally:
            fi.close()
            fu.close()
    print("\n   %d families ship both an upright and an italic with Cyrillic"
          % len(rows))
    print("   a letter REDRAWN in the italic, rather than sloped:\n")
    order = sorted(LOWER, key=lambda c: -tally[c][0])
    for ch in order:
        a, b = tally[ch]
        if not a + b:
            continue
        bar = "#" * int(round(20.0 * a / (a + b)))
        print("     %s  %2d of %2d redraw it  %-20s %.0f%%"
              % (ch, a, a + b, bar, 100.0 * a / (a + b)))
    print("\n   per face, the letters it redraws:\n")
    for fam, got in rows:
        red = "".join(c for c in LOWER if got.get(c, 0) >= 0.045)
        print("     %-24s %s" % (fam, red or "(slopes everything)"))


# The letters a cursive Cyrillic italic actually restructures, as opposed to
# the ones any true italic redraws because a sheared bowl is an ellipse leaning
# the wrong way. Every face on this machine that takes the cursive forms
# redraws these; the round letters are redrawn by the sloped-upright faces too,
# and this project's italic already gets them right for free by building from
# the italic's own donors.
TARGETS = "гдийптм"
CURSIVE = ("Consolas", "Inconsolata LGC", "Ioskeley Mono", "Ioskeley Tuned",
           "JetBrains Mono", "Lilex", "Lyth Mono", "Monaspace Xenon",
           "Victor Mono")


def targets():
    """The seven, as the faces that draw them draw them -- and as we have
    them, which is sloped."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from panel import italics
    paths = dict(italics())
    rows = [(f, paths[f]) for f in CURSIVE if f in paths]
    rows.insert(0, ("SUSE Mono (ours, sloped)",
                    "fonts/ttf/SUSEMono-RegularItalic.ttf"))
    SZ, left, top = 84, 300, 96
    lab = ImageFont.truetype("fonts/ttf/SUSEMono-Regular.ttf", 18)
    head = ImageFont.truetype("fonts/ttf/SUSEMono-Regular.ttf", 27)
    cells = []
    for fam, p in rows:
        try:
            f = ImageFont.truetype(p, SZ)
        except Exception:
            continue
        im = Image.new("L", (int(SZ * 8), int(SZ * 1.6)), 0)
        ImageDraw.Draw(im).text((6, 2), "  ".join(TARGETS), font=f, fill=255)
        cells.append((fam, Image.fromarray(255 - np.asarray(im)).convert("RGB")))
        im.close()
    W, H = left + int(SZ * 8) + 20, top + len(cells) * (int(SZ * 1.6) + 8)
    out = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(out)
    d.text((20, 22), "г д и й п т м -- the seven a cursive italic restructures",
           font=head, fill=(170, 30, 30))
    d.text((20, 58), "ours is the top row and it is still the upright sloped; "
           "the rest is what the cursive houses draw",
           font=lab, fill=(140, 140, 140))
    y = top
    for fam, c in cells:
        d.text((20, y + SZ // 2), fam, font=lab,
               fill=(170, 30, 30) if "ours" in fam else (110, 110, 110))
        out.paste(c, (left, y))
        y += int(SZ * 1.6) + 8
    out.save("tools/out/italic_targets.png")
    print("wrote tools/out/italic_targets.png", out.size)


def main():
    if "--changed" in sys.argv:
        return changed()
    if "--targets" in sys.argv:
        return targets()
    from panel import italics
    tally = {cy: [0, 0] for cy, _, _ in PAIRS}
    rows, seen = [], 0
    for fam, path in italics():
        try:
            f = TTFont(path, fontNumber=0, lazy=True)
        except Exception:
            continue
        try:
            cm, gs = f.getBestCmap(), f.getGlyphSet()
            em = f["head"].unitsPerEm / 1000.0
            got = {}
            for cy, la, _ in PAIRS:
                a, b = outline(f, cm, gs, cy, em), outline(f, cm, gs, la, em)
                if a is None or b is None:
                    continue
                d = worst(register(a), register(b)) / 1000.0
                got[cy] = d
                tally[cy][0 if d < SAME else 1] += 1
            if got:
                seen += 1
                rows.append((fam, got))
        except Exception:
            pass
        finally:
            f.close()

    print("\n   %d monospace italics carry Cyrillic\n" % seen)
    print("   %-26s %s" % ("", "  ".join("%s=%s" % (c, l)
                                         for c, l, _ in PAIRS)))
    for fam, got in rows:
        print("   %-26s %s"
              % (fam, "  ".join(("%5.3f" % got[c]) if c in got else "   -- "
                                for c, _, _ in PAIRS)))
    print("\n   %-26s %s" % ("cursive / upright", ""))
    for cy, la, up in PAIRS:
        a, b = tally[cy]
        if a + b:
            print("     %s -> %s   %2d cursive, %2d kept the upright form "
                  "(%s)   %.0f%% cursive"
                  % (cy, la, a, b, up, 100.0 * a / (a + b)))
    if "--draw" in sys.argv:
        draw(rows)


def draw(rows):
    """The letters themselves, because a distance is not a shape."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from panel import italics
    want = [f for f, _ in italics()][:14]
    paths = dict(italics())
    SZ, pad, left, top = 76, 16, 250, 92
    text = "".join(c for c, _, _ in PAIRS) + " " + "".join(
        l for _, l, _ in PAIRS)
    lab = ImageFont.truetype("fonts/ttf/SUSEMono-Regular.ttf", 17)
    head = ImageFont.truetype("fonts/ttf/SUSEMono-Regular.ttf", 26)
    cells = []
    for fam in want:
        try:
            f = ImageFont.truetype(paths[fam], SZ)
        except Exception:
            continue
        im = Image.new("L", (int(SZ * 11), int(SZ * 1.5)), 0)
        ImageDraw.Draw(im).text((4, 2), text, font=f, fill=255)
        a = np.asarray(im)
        cells.append((fam, Image.fromarray(255 - a).convert("RGB")))
        im.close()
    W = left + int(SZ * 11) + pad
    H = top + len(cells) * (int(SZ * 1.5) + 8)
    out = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(out)
    d.text((20, 22), "и п т д в г  beside  u n m g b r  -- every monospace "
           "italic on this machine that carries Cyrillic",
           font=head, fill=(170, 30, 30))
    d.text((20, 56), "where the Cyrillic letter IS the Latin one, that face "
           "took the cursive form", font=lab, fill=(140, 140, 140))
    y = top
    for fam, c in cells:
        d.text((20, y + SZ // 2), fam, font=lab, fill=(110, 110, 110))
        out.paste(c, (left, y))
        y += int(SZ * 1.5) + 8
    out.save("tools/out/italic_forms.png")
    print("\n   wrote tools/out/italic_forms.png", out.size)


if __name__ == "__main__":
    main()
