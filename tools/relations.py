"""METHOD §2's internal relations, read across the whole drawn set.

    ./venv/bin/python tools/relations.py --selftest   # shapes with known answers
    ./venv/bin/python tools/relations.py --latin      # calibration: must be quiet
    ./venv/bin/python tools/relations.py              # the audit
    ./venv/bin/python tools/relations.py --growth     # light to heavy, ours vs theirs

§2 says a letter can be correct on every absolute measure and still read
wrong, and that the way to catch it is to measure a glyph's parts **against
each other** and against the panel *bucketed by weight*. Every letter that has
needed that so far got a bespoke probe -- `harmony.py` for the bowl family,
`bowls.py` for counters against o, `diagonals.py` for Ж, `seam.py` for б --
each written after the eye had already found the fault. Nothing has ever read
the list across the set, so a letter nobody has complained about has never
been asked.

Four readings, chosen because they are the ones §2 names that no existing
probe covers, and because each is generic enough to mean the same thing in
every letter:

  width/adv     does the letter widen as the face gets heavier? §2 step 1,
                and ф's whole fault -- 0.863 flat against a panel going
                0.832 to 0.938.
  counter agp   the largest counter's width over its height. §2 step 3: a
                bowl widened without being made taller is a squashed oval,
                correct in every stroke and still wrong.
  counter/stem  the largest disc that fits in that counter, over the face's
                own stem. §2 step 4 -- how much white survives.
  solid         the fraction of the letter's inked rows where a scanline
                reads ONE run: where the letter has gone solid. Я's fault
                class, and never computed for anything but Я.

And the reading §2 actually turns on, which nothing has ever computed for any
letter: **growth**, each of the four from the light cut to the heavy one, ours
against the panel's own. A face's parts do not scale together, and a ratio
that is right at both ends can still travel wrong between them.

NOT A GATE. It re-reports readings already recorded as accepted at approval --
Ж's arm, я's counters, ф's width -- and a gate born red is a gate that gets
grepped. `verify.sh` does not run it; `docs/APPROVALS.md` is the authority on
which flags were known when a glyph was frozen.

Ours and the panel go through ONE lens: the rendered glyph, scaled so each
face's own o stands `weights.XH` high, which is the same lens `weights.py` and
`seam.py` read through. Measuring ours off the outlines and theirs off a
raster is how 1.40 became 1.46.

**Every reading is a multiple of the face's OWN Latin median for that reading
and that case**, which is the normalisation `panel.profile` already uses for
ink and the reason it works. Read raw, three of the four readings say mostly
that this face has its own proportions: the Latin calibration pass flagged
thirty-three of fifty-two letters, including O, B, P, R and o, p, q, whose
outlines nobody has ever questioned. A panel bracket for O's width holds
0.850–0.868 and this face draws 0.882, and that is the face, not the letter --
§8's rule that a width outside the panel is a finding only if the letter it
should be measured against is inside it. Divided by the face's own Latin the
question becomes the one worth asking: **does this Cyrillic letter stand in
the same relation to its own alphabet as the panel's does to theirs?**

Each font is opened once and the letters loop inside it (§4's rule, and
`harmony.read_all`'s reason): opened per letter, the sweep costs fifty times
what it needs to.
"""

import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

import probe as P
import weights as W
from classify import TIERS

KEYS = ("width/adv", "counter asp", "counter/stem", "solid")

# The drawn Cyrillic, and the face's own Latin to calibrate the thresholds
# against. A reading that flags half the Latin is miscalibrated, not evidence
# about the Cyrillic -- the same two-pass shape `audit.py` and `signature.py`
# already use.
LATIN_LC = "abcdefghijklmnopqrstuvwxyz"
LATIN_UC = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

OURS = [("Thin", "fonts/ttf/SUSEMono-Thin.ttf"),
        ("Regular", "fonts/ttf/SUSEMono-Regular.ttf"),
        ("Bold", "fonts/ttf/SUSEMono-Bold.ttf"),
        ("ExtraBold", "fonts/ttf/SUSEMono-ExtraBold.ttf")]


def cyrillic():
    """(char, is_lowercase) for every Cyrillic letter the project draws."""
    return [(chr(cp), chr(cp).islower()) for cp, _n, _t, _nn in TIERS]


def runs_per_row(m):
    """How many separate ink runs each row of the mask has."""
    d = np.diff(m.astype(np.int8), axis=1)
    return (d == 1).sum(axis=1) + m[:, 0].astype(np.int8)


def read_mask(m, adv_px, stem_px):
    """The four readings off one ink mask. No font, so the selftest can drive
    it with shapes whose answers are known by construction."""
    rows = m.any(axis=1)
    if not rows.any() or not adv_px or not stem_px:
        return None
    cols = m.any(axis=0)
    out = {"width/adv": float(cols.sum()) / adv_px}

    n_runs = runs_per_row(m)
    out["solid"] = float((n_runs[rows] == 1).sum()) / float(rows.sum())

    holes = W.holes(m)
    lab, n = ndimage.label(holes)
    if n:
        big = int(np.argmax(ndimage.sum(holes, lab, range(1, n + 1)))) + 1
        sel = lab == big
        ys, xs = np.where(sel)
        h = max(1, ys.max() - ys.min() + 1)
        w = max(1, xs.max() - xs.min() + 1)
        out["counter asp"] = float(w) / float(h)
        # the largest disc that fits in the counter, the same quantity
        # weights.py reads a stroke with -- direction-free, and it survives a
        # counter that is not a rectangle
        out["counter/stem"] = W.width(ndimage.distance_transform_edt(sel)) \
            / stem_px
    return out


class Face:
    """One font, opened once, with everything the readings need precomputed."""

    def __init__(self, path, xh=W.XH):
        self.path = path
        self.f = TTFont(path, fontNumber=0, lazy=True)
        self.cm = self.f.getBestCmap()
        self.gs = self.f.getGlyphSet()
        upem = self.f["head"].unitsPerEm
        o = P.contours(self.f, "o", self.cm, self.gs)
        if not o:
            raise ValueError("no o")
        ys = [q[1] for p in o for q in p]
        self.size = int(round(xh / ((max(ys) - min(ys)) / float(upem))))
        if not 40 <= self.size <= 4000:
            raise ValueError("scale")
        self.k = self.size / float(upem)
        self.font = ImageFont.truetype(path, self.size)
        self.stem = {False: (P.stem_of(self.f, self.cm, self.gs) or 0) * self.k,
                     True: (P.lc_stem_of(self.f, self.cm, self.gs) or 0) * self.k}
        self.upem = upem
        # The Latin is read to build the divisor and again for the calibration
        # pass, and a render is the expensive thing here, so it is kept.
        self._cache, self._base = {}, None

    def close(self):
        self.f.close()

    def mask(self, ch):
        s = self.size
        img = Image.new("L", (int(s * 1.8), int(s * 2.4)), 0)
        ImageDraw.Draw(img).text((int(s * 0.3), int(s * 0.3)), ch,
                                 font=self.font, fill=255)
        a = np.asarray(img) > 127
        return a if a.any() else None

    def read_raw(self, ch, lower):
        if ord(ch) not in self.cm:
            return None
        if (ch, lower) in self._cache:
            return self._cache[(ch, lower)]
        m = self.mask(ch)
        v = None
        if m is not None:
            adv = self.f["hmtx"][self.cm[ord(ch)]][0] * self.k
            v = read_mask(m, adv, self.stem[lower])
        self._cache[(ch, lower)] = v
        return v

    def stem_em(self):
        return self.stem[False] / float(self.size)

    def base(self):
        """The face's own Latin median for each reading, per case.

        The divisor that makes a reading a proportion rather than a
        measurement. Median over the whole Latin alphabet of the case, so no
        single letter's opinion moves it -- and computed inside the face, so
        whatever this face does differently from every other face divides
        out of both sides of the comparison.
        """
        if self._base is None:
            self._base = {}
            for lower, alpha in ((True, LATIN_LC), (False, LATIN_UC)):
                acc = {}
                for c in alpha:
                    v = self.read_raw(c, lower)
                    for k, x in (v or {}).items():
                        acc.setdefault(k, []).append(x)
                self._base[lower] = {k: float(np.median(v))
                                     for k, v in acc.items() if len(v) >= 6}
        return self._base

    def relative(self, ch, lower):
        """The four readings as multiples of this face's own Latin."""
        v = self.read_raw(ch, lower)
        b = self.base()[lower]
        if not v:
            return None
        return {k: v[k] / b[k] for k in v if b.get(k)}


# ---------------------------------------------------------------- selftest

def selftest():
    """Shapes whose answers are true by construction.

    A rectangular annulus: outer W by H, wall t, in a cell of `adv`. Then
    width/adv, the counter's aspect, the largest disc inside it and the solid
    fraction are all arithmetic, and the reading either recovers them or the
    instrument is not usable. Nobody had ever shown the four gauges in this
    file a shape whose answer was known -- which is the rule METHOD sets after
    weights.py failed its own first selftest at +5 per cent.
    """
    ok = True
    for (Wd, Ht, t, adv) in ((240, 300, 30, 300), (180, 180, 20, 260),
                             (300, 200, 45, 340)):
        img = Image.new("L", (adv + 40, Ht + 40), 0)
        d = ImageDraw.Draw(img)
        d.rectangle([20, 20, 20 + Wd - 1, 20 + Ht - 1], fill=255)
        d.rectangle([20 + t, 20 + t, 20 + Wd - 1 - t, 20 + Ht - 1 - t], fill=0)
        m = np.asarray(img) > 127
        got = read_mask(m, float(adv), float(t))
        want = {"width/adv": Wd / float(adv),
                "counter asp": (Wd - 2 * t) / float(Ht - 2 * t),
                "counter/stem": min(Wd - 2 * t, Ht - 2 * t) / float(t),
                # only the two bars read one run; the walls read two
                "solid": 2 * t / float(Ht)}
        for k in KEYS:
            e = abs(got[k] - want[k]) / want[k]
            flag = "ok" if e < 0.04 else "FAILED"
            ok = ok and e < 0.04
            print("   %-12s want %8.3f  got %8.3f  %+5.1f%%  %s"
                  % (k, want[k], got[k], 100 * (got[k] - want[k]) / want[k],
                     flag))
        print("   " + "-" * 56)
    print("   instrument usable" if ok else "   INSTRUMENT NOT USABLE")
    return ok


# ---------------------------------------------------------------- the sweep

CACHE = "tools/out/relations_panel_%s.json"

# There is no threshold constant here, on purpose, and getting to that was
# most of the work.
#
# `compare` brackets the eleven nearest faces between their second-lowest and
# second-highest value. That is right for a designed ratio and far too tight
# for a geometric one read off a raster -- it hands back brackets like
# 1.000-1.000 for D's counter, where eleven faces agree to three decimals.
# Applied bare it flags the face's OWN Latin thirty-three times, O, B, P, R,
# a, e and g among them, and a threshold that flags the host is measuring the
# threshold rather than the glyph.
#
# A flat margin does not rescue it either. Calibrated against the host, the
# margin that would silence the Latin is **0.80**, and it is g -- whose solid
# fraction is 1.8 to 2.0 times the Latin median against a panel holding
# 0.53-1.11, because its tail is a flat bar where every other face draws a
# curve. That is not noise to be tuned away. It is the face's loudest letter,
# and an instrument that finds it is working.
#
# So the bar is the host itself, per reading and per weight: **a Cyrillic
# reading is reported only when it departs further than the face's own Latin
# ever does on that same reading at that same weight.** Nothing to tune,
# nothing to keep in step with the panel, and the claim it makes is one worth
# making -- this letter is doing something the face's own alphabet does not.
BAR_FLOOR = 0.05


def sweep(chars, refresh=False):
    """Every panel face, opened once each: {ch: [(stem/em, relative), ...]}
    and the per-family light->heavy growth of the RAW readings.

    Cached, because it is six minutes and the report is read more than once.
    `--refresh` rebuilds it; delete the file if the panel changes.
    """
    import json
    import os
    key = "".join(c for c, _l in chars)
    path_c = CACHE % ("latin" if key.isascii() else "cyrillic")
    if not refresh and os.path.exists(path_c):
        with open(path_c) as fh:
            blob = json.load(fh)
        if blob.get("key") == key:
            return ({c: [(s, v) for s, v in rows]
                     for c, rows in blob["ref"].items()}, blob["growth"])

    from panel import families
    out, growth, pend = {}, {}, {}
    for name, path in families():
        try:
            fc = Face(path)
        except Exception:
            continue
        try:
            se = fc.stem_em()
            raw = {}
            for ch, lower in chars:
                rel = fc.relative(ch, lower)
                if rel and len(rel) == len(KEYS):
                    out.setdefault(ch, []).append((se, rel))
                    raw[ch] = fc.read_raw(ch, lower)
            fam = name.replace(" (heaviest)", "")
            if name.endswith("(heaviest)") and fam in pend:
                for ch, hi in raw.items():
                    lo = pend[fam].get(ch)
                    if lo:
                        growth.setdefault(ch, []).append(
                            {k: hi[k] / lo[k] for k in KEYS
                             if lo.get(k) and hi.get(k)})
            else:
                pend[fam] = raw
        except Exception:
            pass
        finally:
            fc.close()
    with open(path_c, "w") as fh:
        json.dump({"key": key, "ref": out, "growth": growth}, fh)
    return out, growth


def outside(c, value):
    """How far past the bracket a reading sits, as a share of its own edge.

    Zero when inside. Signed so the direction is visible: a letter narrower
    than the panel and one wider than it are different findings.
    """
    _med, lo, hi, ok = c
    if ok:
        return 0.0
    return (value - hi) / hi if value > hi else (value - lo) / lo


def band(vals):
    v = sorted(vals)
    return v[len(v) // 10], v[len(v) // 2], v[-1 - len(v) // 10]


def report(subject="cyrillic", show_growth=False, calibrate=False):
    chars = (cyrillic() if subject == "cyrillic"
             else [(c, True) for c in LATIN_LC] +
                  [(c, False) for c in LATIN_UC])
    print("panel sweep -- %s, one lens, each font opened once" % subject)
    ref, gro = sweep(chars, "--refresh" in sys.argv)

    if show_growth:
        print("\n=== growth, light cut to heavy, ours against the panel's "
              "own ===")
        flo, fhi = Face(OURS[0][1]), Face(OURS[-1][1])
        lo = {ch: flo.read_raw(ch, lw) for ch, lw in chars}
        hi = {ch: fhi.read_raw(ch, lw) for ch, lw in chars}
        flo.close()
        fhi.close()
        for ch, _lw in chars:
            if not (lo.get(ch) and hi.get(ch) and ch in gro):
                continue
            rows = gro[ch]
            line, flagged = "  %s  " % ch, False
            for k in KEYS:
                vs = [r[k] for r in rows if k in r]
                if len(vs) < 6 or not lo[ch].get(k):
                    line += "%22s" % "--"
                    continue
                p10, med, p90 = band(vs)
                mine = hi[ch][k] / lo[ch][k]
                bad = not (p10 <= mine <= p90)
                flagged = flagged or bad
                line += "  %s %.2f [%.2f-%.2f]%s" % (
                    k[:4], mine, p10, p90, "!" if bad else " ")
            if flagged:
                print(line + "  (%d families)" % len(rows))
        return

    print("every reading is a multiple of the face's own Latin median for "
          "that reading and case\n")
    every = deviations(chars, ref)

    if calibrate:
        print("=== how far the HOST's own Latin departs -- this IS the bar ===\n")
        for d, name, ch, k, val, c, n in sorted(every, reverse=True)[:14]:
            print("  %-10s %s %-12s %8.3f  %+6.0f%% past  %.3f .. %-6.3f %3d"
                  % (name, ch, k, val, 100 * outside(c, val), c[1], c[2], n))
        return

    bar = bars()
    print("bar per reading per weight = the furthest the face's OWN Latin "
          "departs there\n")
    for name, _path in OURS:
        hits = [(d, "  %s  %-12s %8.3f  %+6.0f%% past %.3f..%-6.3f  "
                    "(the Latin's own worst here: %+.0f%%)  %3d faces"
                 % (ch, k, val, 100 * outside(c, val), c[1], c[2],
                    100 * bar.get((nm, k), 0.0), n))
                for d, nm, ch, k, val, c, n in every
                if nm == name and d > max(bar.get((nm, k), 0.0), BAR_FLOOR)]
        print("=" * 74)
        print("%s -- %d readings past the host's own bar" % (name, len(hits)))
        for _d, h in sorted(hits, reverse=True):
            print(h)


def deviations(chars, ref):
    """(|dev|, weight, ch, key, value, bracket, faces) for every reading."""
    every = []
    for name, path in OURS:
        fc = Face(path)
        for ch, lower in chars:
            v = fc.relative(ch, lower)
            if not v:
                continue
            for k in KEYS:
                if k not in v:
                    continue
                pts = [(s, r[k]) for s, r in ref.get(ch, []) if k in r]
                if len(pts) < 6:
                    continue
                c = P.compare(pts, fc.stem_em(), v[k])
                if c:
                    every.append((abs(outside(c, v[k])), name, ch, k, v[k],
                                  c, len(pts)))
        fc.close()
    return every


_BARS = {}


def bars():
    """The host Latin's own worst departure, per weight and per reading.

    Computed from the Latin sweep rather than written down, so it cannot go
    stale against the panel or against a change to the readings.
    """
    if not _BARS:
        chars = [(c, True) for c in LATIN_LC] + [(c, False) for c in LATIN_UC]
        ref, _g = sweep(chars)
        for d, name, _ch, k, _v, _c, _n in deviations(chars, ref):
            _BARS[(name, k)] = max(_BARS.get((name, k), 0.0), d)
    return _BARS


def main():
    if "--selftest" in sys.argv:
        print("=== relations.py against shapes of known answer ===")
        raise SystemExit(0 if selftest() else 1)
    latin = "--latin" in sys.argv or "--calibrate" in sys.argv
    report("latin" if latin else "cyrillic",
           "--growth" in sys.argv, "--calibrate" in sys.argv)


if __name__ == "__main__":
    main()
