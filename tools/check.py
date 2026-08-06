"""Mechanical checks that must pass before anything is shown for review.

These are the failures a reader cannot be expected to catch: a glyph that is
mapped but blank, an advance that differs from the family width, a stem that
does not match the Latin at its own master, or an outline that looks right at
both masters and tears apart between them.

    python tools/check.py
"""

import glob
import subprocess
import sys

from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from classify import TIERS         # noqa: E402

WIDTH = 600
TARGET = [(cp, name) for cp, name, _, _ in TIERS]


def flat(gs, name):
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    polys, cur = [], []
    for op, a in pen.value:
        if op == "moveTo":
            cur = [a[0]]
        elif op == "lineTo":
            cur.append(a[0])
        elif op in ("qCurveTo", "curveTo"):
            cur += [p for p in a if p]
        elif op == "closePath" and cur:
            polys.append(cur)
            cur = []
    return polys


def stem_at(polys, y, last=False, pair=0):
    xs = []
    for poly in polys:
        for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
            if (y0 - y) * (y1 - y) < 0:
                xs.append(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
    xs.sort()
    if len(xs) < 2 * (pair + 1):
        return None
    return (xs[-1] - xs[-2]) if last else (xs[2 * pair + 1] - xs[2 * pair])


def check_font(path, present):
    f = TTFont(path)
    cmap = f.getBestCmap()
    gs = f.getGlyphSet()
    hmtx = f["hmtx"]
    upem = f["head"].unitsPerEm
    want = WIDTH * upem / 1000.0
    fails = []

    for cp, name in TARGET:
        if name not in present:
            continue
        g = cmap.get(cp)
        if g is None:
            fails.append(f"U+{cp:04X} {chr(cp)} not in cmap")
            continue
        if not flat(gs, g):
            fails.append(f"U+{cp:04X} {chr(cp)} mapped but blank")
        if hmtx[g][0] != want:
            fails.append(f"U+{cp:04X} {chr(cp)} advance {hmtx[g][0]} != {want:.0f}")
        if g.startswith("uni") and g[3:7].isalnum() and int(g[3:7], 16) != cp:
            fails.append(f"U+{cp:04X} production name {g} disagrees with cmap")

    # Stroke weight against the Latin at this same weight -- each letter
    # against a LIKE-SHAPED Latin. A horizontal scanline cuts a curve
    # obliquely, so a round letter always measures wider than a flat-sided
    # one; comparing Ф to H flags a 28% error that is not there.
    cap = f["OS/2"].sCapHeight
    for ch, latin, frac in (("П", "H", .25), ("Ц", "H", .25), ("Ш", "H", .25),
                            ("Щ", "H", .25), ("Ч", "H", .25), ("Г", "E", .25),
                            ("Б", "B", .25), ("Ь", "B", .25), ("Ы", "B", .25),
                            ("Ъ", "B", .25), ("Л", "H", .25), ("Д", "H", .25),
                            # Round letters are read at 0.62 cap: high enough
                            # to clear Ю's and Є's crossbars, near enough the
                            # bowl's widest point that the cut is close to the
                            # true stroke. Ю leads with its stem, so its bowl
                            # is the SECOND stroke across.
                            ("Ф", "O", .62), ("Ю", "O", .62), ("Є", "C", .62)):
        y = cap * frac
        if ord(ch) not in cmap or latin not in gs:
            continue
        # Л and Д lead with a SLANTED leg, which a horizontal cut always
        # measures wide, so their vertical right stem is checked instead
        last = ch in "ЛД"
        pair = 1 if ch == "Ю" else 0
        ref = stem_at(flat(gs, latin), y, last)
        v = stem_at(flat(gs, cmap[ord(ch)]), y, last, pair)
        if v and ref and abs(v - ref) / ref > 0.20:
            fails.append(f"{ch} stroke {v:.0f} vs Latin {latin} {ref:.0f} "
                         f"({100 * (v - ref) / ref:+.0f}%)")
    return fails


def pinned_toolchain():
    """The build must use the versions requirements.txt pins.

    Installing from the unpinned requirements.in instead gave fontmake 3.12
    and gftools 0.9.998 against the pinned 3.9.0 and 0.9.63, and the newer
    gftools silently dropped PANOSE: the released font carries (2,11,9) and
    that build emitted (0,0,0), which turns fontbakery's monospace check from
    a WARN into a FAIL. Nothing about the glyphs was involved.
    """
    import re
    from importlib.metadata import version, PackageNotFoundError
    want = {}
    for line in open("requirements.txt"):
        m = re.match(r"^([A-Za-z0-9_.-]+)==([^\s;]+)", line)
        keep = ("fontmake", "gftools", "fonttools", "glyphslib", "ufo2ft")
        if m and m.group(1).lower() in keep:
            want[m.group(1)] = m.group(2)
    out = []
    for pkg, ver in want.items():
        try:
            got = version(pkg)
        except PackageNotFoundError:
            out.append(f"{pkg} not installed (pinned {ver})")
            continue
        if got != ver:
            out.append(f"{pkg} {got} != pinned {ver}")
    return out


# Donors that a recipe reaches into by node index rather than as a whole.
# Indexing only holds while the donor keeps its structure, and the italic
# does NOT match the upright everywhere: D is [10,12] upright but [9,11]
# italic, O is [14,14] vs [12,12], C is [28] vs [26]. E happens to match,
# which is the only reason Ghe() works -- nothing guaranteed it.
NODE_INDEXED = {"E": "Ghe() takes E's nodes 6..15 for the rounded corner"}


def donor_structure():
    """Fail if a node-indexed donor differs between the two sources."""
    import glyphsLib
    out = []
    up = {g.name: g for g in glyphsLib.load("sources/SUSEMono.glyphs").glyphs}
    it = {g.name: g for g in
          glyphsLib.load("sources/SUSEMono-Italic.glyphs").glyphs}
    for name, why in NODE_INDEXED.items():
        if name not in up or name not in it:
            out.append(f"node-indexed donor {name} missing")
            continue
        a = [len(p.nodes) for p in up[name].layers[0].paths]
        b = [len(p.nodes) for p in it[name].layers[0].paths]
        if a != b:
            out.append(f"node-indexed donor {name}: upright {a} != italic {b}"
                       f" -- {why}")
    return out


def source_fidelity():
    """The Latin must survive the round-trip unchanged.

    glyphsLib rewrites component scales at 3 decimals, so 0.9552 becomes
    0.955 on 15 components in the quote marks and some Vietnamese. That is
    ~0.04 units and invisible, and it is not invertible (0.9981 and 0.9979
    both land on 0.998), so it is accepted -- but anything LARGER than a
    rounding would be a real regression and must fail.
    """
    import subprocess
    import glyphsLib
    orig = subprocess.run(["git", "show", "HEAD:sources/SUSEMono.glyphs"],
                          capture_output=True, text=True).stdout
    if not orig:
        return []
    open("/tmp/_orig.glyphs", "w").write(orig)
    a = glyphsLib.load("/tmp/_orig.glyphs")
    b = glyphsLib.load("sources/SUSEMono.glyphs")
    out = []
    if len(a.instances) != len(b.instances):
        out.append(f"instances {len(a.instances)} -> {len(b.instances)}")
    an = [i.name for i in a.instances]
    bn = [i.name for i in b.instances]
    if an != bn:
        out.append(f"instance names changed: {an} -> {bn}")
    if len(a.features) != len(b.features) or len(a.classes) != len(b.classes):
        out.append("feature or class count changed")
    B = {g.name: g for g in b.glyphs}
    worst = 0.0
    for g in a.glyphs:
        h = B.get(g.name)
        if not h:
            out.append(f"Latin glyph {g.name} lost")
            continue
        for la, lb in zip(g.layers, h.layers):
            for ca, cb in zip(la.components, lb.components):
                for x, y in zip(ca.transform, cb.transform):
                    worst = max(worst, abs(x - y))
            for pa, pb in zip(la.paths, lb.paths):
                if len(pa.nodes) != len(pb.nodes):
                    out.append(f"{g.name}: node count changed")
                    break
                for na, nb in zip(pa.nodes, pb.nodes):
                    worst = max(worst,
                                abs(na.position.x - nb.position.x),
                                abs(na.position.y - nb.position.y))
    if worst > 0.5:
        out.append(f"Latin outlines moved by up to {worst:.3f} units")
    return out


def build_is_current():
    """The Makefile computes its dependency list from config.yaml -- the
    PROPORTIONAL family -- so SOURCES is SUSE.glyphs and SUSE-Italic.glyphs.
    Editing SUSEMono.glyphs never invalidates build.stamp, and `make build`
    exits 0 having done nothing. Two rounds of review ran against stale
    binaries before this was noticed, so the freshness is now asserted.
    """
    import os
    src = "sources/SUSEMono.glyphs"
    out = "fonts/variable/SUSEMono[wght].ttf"
    if not os.path.exists(out):
        return ["no build output"]
    if os.path.getmtime(src) > os.path.getmtime(out):
        return ["sources are newer than the build -- "
                "run `rm -f build.stamp && make build`"]
    return []


def main():
    import glyphsLib
    # each binary is checked against the source that produced it, so the
    # italic is not judged against glyphs only the upright has yet
    present = {}
    for key, path in (("upright", "sources/SUSEMono.glyphs"),
                      ("italic", "sources/SUSEMono-Italic.glyphs")):
        present[key] = {g.name for g in glyphsLib.load(path).glyphs}

    problems = [f"stale: {x}" for x in build_is_current()]
    problems += [f"toolchain: {x}" for x in pinned_toolchain()]
    problems += [f"donor: {x}" for x in donor_structure()]
    problems += [f"source: {x}" for x in source_fidelity()]
    # only the Mono family: `make build` also builds the proportional SUSE,
    # which has no Cyrillic and would report every target glyph as missing
    for p in sorted(glob.glob("fonts/ttf/SUSEMono*.ttf")) + \
             sorted(glob.glob("fonts/variable/SUSEMono*.ttf")):
        key = "italic" if "Italic" in p else "upright"
        for f in check_font(p, present[key]):
            problems.append(f"{p.split('/')[-1]}: {f}")

    # interpolation: catches mismatched start nodes and path order, which look
    # fine at both masters and tear apart between them
    for vf in sorted(glob.glob("fonts/variable/SUSEMono*.ttf")):
        r = subprocess.run([sys.executable, "-m", "fontTools.varLib.interpolatable",
                            vf], capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip()
        if out and "Glyph" in out:
            for line in out.splitlines():
                if line.strip():
                    problems.append(f"{vf.split('/')[-1]}: interpolatable: {line.strip()}")

    # ligatures and powerline must be untouched
    for p in ["fonts/ttf/SUSEMono-Regular.ttf"]:
        f = TTFont(p)
        feats = {r.FeatureTag for r in f["GSUB"].table.FeatureList.FeatureRecord}
        for t in ("liga", "calt"):
            if t not in feats:
                problems.append(f"{p}: {t} feature missing")
        cm = f.getBestCmap()
        pl = [c for c in range(0xE0A0, 0xE0D5) if c in cm]
        if not pl:
            problems.append(f"{p}: powerline glyphs missing")

    if problems:
        print("MECHANICAL CHECKS FAILED:")
        for x in problems[:40]:
            print("  !", x)
        print(f"  ({len(problems)} total)")
        sys.exit(1)
    print("all mechanical checks pass")


main()
