"""What IS the italic, letter by letter -- a slant, or a redrawing?

    ./venv/bin/python tools/italic.py

The italic is a second source file, `sources/SUSEMono-Italic.glyphs`, with its
own two masters and no Cyrillic in it at all. Before a single Cyrillic glyph is
built there, one thing has to be known for every letter the Cyrillic borrows
from: whether the italic's version of it is the upright SLANTED, or a different
drawing.

The answer is not the same for the two cases, and "sloped roman in the
capitals, true italic in the lowercase" is a description, not a measurement.
This measures it. For every Latin glyph in both files, the upright outline is
sheared by the italic's own angle about the baseline, moved to sit on the
italic's own left sidebearing, and compared point for point against the italic
drawing. What comes back is the worst distance between them, in units of the
em, and a letter that is a pure slant reads near zero.

A letter that reads near zero can have its Cyrillic built by slanting whatever
the upright already builds. A letter that does not has to be drawn again from
the italic's own parts, and the list of those is the real size of this job.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import math                                                    # noqa: E402

import glyphsLib                                               # noqa: E402

UP = "sources/SUSEMono.glyphs"
IT = "sources/SUSEMono-Italic.glyphs"
CAPS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWER = "abcdefghijklmnopqrstuvwxyz"


def points(layer):
    return [(n.position.x, n.position.y)
            for p in layer.paths for n in p.nodes]


def worst(a, b):
    """The furthest any point of one drawing sits from the nearest of the
    other, both ways round, over the em.

    Both ways matter: a letter can have every point of the slant land on the
    italic and still be missing a whole stroke.
    """
    if not a or not b:
        return None

    def one(u, v):
        return max(min(math.hypot(px - qx, py - qy) for qx, qy in v)
                   for px, py in u)
    return max(one(a, b), one(b, a)) / 1000.0


def main():
    up = glyphsLib.load(open(UP))
    it = glyphsLib.load(open(IT))
    ug = {g.name: g for g in up.glyphs}
    ig = {g.name: g for g in it.glyphs}
    angle = it.masters[0].italicAngle
    t = math.tan(math.radians(angle))
    print("\n   italic angle %g degrees\n" % angle)

    for mi, m in enumerate(it.masters):
        print("   %s -- how far the italic is from the upright sheared %g deg"
              % (m.name, angle))
        for label, s in (("capitals", CAPS), ("lowercase", LOWER)):
            out = []
            for ch in s:
                if ch not in ug or ch not in ig:
                    continue
                a = points(ug[ch].layers[mi])
                b = points(ig[ch].layers[mi])
                if not a or not b:
                    continue
                # shear about the baseline, then register on the left edge so
                # a pure slant is not scored for where it was placed
                sh = [(x + t * y, y) for x, y in a]
                dx = min(q[0] for q in b) - min(q[0] for q in sh)
                d = worst([(x + dx, y) for x, y in sh], b)
                if d is not None:
                    out.append((d, ch, -dx / t))
            out.sort()
            same = [c for d, c, _ in out if d < 0.010]
            near = [c for d, c, _ in out if 0.010 <= d < 0.040]
            drawn = [(c, d) for d, c, _ in out if d >= 0.040]
            # The height the face shears ABOUT. Registering the sheared upright
            # on the italic's left edge costs dx, and dx = -tan(angle) * pivot,
            # so every letter that IS a pure slant reports the pivot directly.
            # Read only off those: a redrawn letter's dx is not a pivot.
            piv = sorted(round(p) for d, c, p in out if d < 0.010)
            if piv:
                print("     %s -- sheared about y = %d..%d (median %d)"
                      % (label, piv[0], piv[-1], piv[len(piv) // 2]))
            print("     %s" % label)
            print("       a pure slant (under 0.010 em) : %s"
                  % ("".join(same) or "none"))
            print("       within 0.040                  : %s"
                  % ("".join(near) or "none"))
            print("       drawn again                   : %s"
                  % (" ".join("%s %.02f" % (c, d) for c, d in drawn)
                     or "none"))
        print()


if __name__ == "__main__":
    main()
