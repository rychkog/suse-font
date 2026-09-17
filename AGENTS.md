# SUSE Mono — Cyrillic

Adding Ukrainian + Russian Cyrillic to SUSE Mono, a Latin-only monospace with
Glyphs.app sources. Two masters (Thin 100, ExtraBold 800), plus a sloped-roman
italic source. Glyphs are **generated from recipes**, not drawn by hand — see
`tools/recipes.py`.

The project brief is kept outside the repository and is binding.

## Where things live

Each fact has one home. Where another file needs it, it carries one line and a
pointer, never a second copy.

| File | Owns |
|---|---|
| `AGENTS.md` (this file) | the rules, as statements; commands; machine limits; how to report |
| `docs/METHOD.md` | why each rule exists: the fault catalogue (F1…), relations (§2), probes (§4), settled findings (§8), open threads (§9). **Read it before changing any constant** |
| `docs/APPROVALS.md` | the ledger of what is approved, and so frozen. Dated rows, never rewritten |
| `tools/recipes.py` | every per-glyph constant, with its reason beside it |

`tools/docs_check.py` runs first in `verify.sh`. It fails when a doc cites a
script, name, F or § that no longer exists, when an F-number repeats, or when a
tool has no row in METHOD §4. F-numbers, § numbers and the rule numbers below
are permanent: code and the ledger cite them.

## The objective

**The Cyrillic must read as SUSE Mono — not as Cyrillic added to SUSE Mono.**
A reader should not be able to tell which letters came later. Every rule below
serves this; when a rule and this goal disagree, this goal wins.

The face's own Latin is the authority on what the shapes are. The panel of 60
monospace faces can tell you *which relations exist* — that ф widens as it
gets bolder — but never what a SUSE Mono letter should look like. A panel
median is not a reason to change something this face already does
consistently, and never a reason to change an approved glyph.

Derived beats drawn for the same reason: the Latin is already condensed and
optically fitted to its cell, so a glyph built from it inherits that work and
a freshly drawn one throws it away.

Test it in company, never alone — the "vs Latin" row of `specimen.py`, the
mixed `git commit -m 'юність' build/ґрунт-єднати.log` line, and at 12px and
14px. What the signature concretely is: *Design rules* below.

## Pipeline

Use it. Do not invent one. `python` is not on PATH; use `./venv/bin/python`.

```
./venv/bin/python tools/build_cyrillic.py sources/SUSEMono.glyphs --rebuild
./venv/bin/python tools/build_cyrillic.py sources/SUSEMono-Italic.glyphs --rebuild
rm -f build.stamp && make mono   # NOT `make build` -- see below
bash tools/verify.sh          # every gate, in order, the docs check first
bash tools/review.sh          # regenerate EVERY review image from this build
./venv/bin/python tools/specimen.py --letters Зз   # one letter, in company
./venv/bin/python tools/specimen.py --against OLD   # this build vs a stash
```

**`make build` is the wrong target and it has cost this machine twice.** It
does `rm -rf fonts` and then rebuilds every family in `sources/config*.yaml`,
so a one-glyph Cyrillic change pays for the whole proportional family — and
the `rm` is why an OOM kill mid-build leaves no fonts at all, which is exactly
what happened. `make mono` builds the one config this work touches, leaves the
rest of `fonts/` alone, and caps ninja at `JOBS` (2) — gftools otherwise runs
ninja with no arguments, ninja defaults to one job per core plus two, and
twenty concurrent fontmake processes is what took the VM down.

Render into `tools/out/`. Never review an image made before the last fix.

Run `verify.sh` **unfiltered** before showing anything. Do not grep a gate's
output — findings have been hidden that way, including a broken interpolation.

## Before changing anything

Each rule is one statement; the story behind it is at the pointer.

1. **Never change an approved glyph without explicit confirmation.** The brief
   says never to ask about design decisions; that applies to work not yet
   approved. A panel median is not evidence against an approved glyph. A new
   sibling that should match one **copies the approved construction** — never
   a shared helper that re-derives it; Ґ was silently changed twice that way.
   METHOD §6.
2. **"It looks wrong now" after unrelated work is a regression report.** Check
   what was touched since the approval — `git log -p` answers faster than the
   panel.
3. **Measure the host before blaming the glyph.** The face's Latin says what
   the value is; the panel says which relation holds. `audit.py --selftest`
   must stay clean. METHOD §1.
   - A panel figure holds only on the row its probe read it on: read ours back
     with that same probe, in memory, before building. F1.
   - A gate that finds nothing to read in a letter has not passed it. F3.
4. **A flat proportion constant is suspect** until the panel has been bucketed
   by weight — and, where this face is heavier than the bucket, by stem share
   in advance units. METHOD §1.
5. **Two constants that justify each other are one decision.** A constant
   whose reason names another pipeline step is judged, and usually replaced,
   together with it. F11.
6. **Read a two-master construction at the weights in between.** A fault that
   scales with the correction a master needs is smallest where it is being
   looked at. `tools/seam.py` blends without a build. F11.
7. **A figure read off a donor outline is checked at both masters, in units,
   before it is used.** F8.
   - A constant that compensates one source's figure is only as right as that
     figure: re-read the figure by ink before keeping the constant. F17.
8. **An assembled glyph has a placement decision no gate reads.** Ask what
   the host does with the same assembly; a Latin letter nearly always carries
   the same mark. `tools/marks.py`. F12.
9. **Ask whether it is the right LETTER before asking whether it is the right
   size.** A count sees it — runs of ink beside the stem, what touches what,
   how many strokes cross. A tier-1 donation is where this hides. F13.
10. **A change to a counter is a change to a stroke — run `tools/wrap.py`
    before showing it.** A donor's counter figure transfers only where the
    donor's outer is the same shape. METHOD §8, *A counter is the far side of
    a stroke*.
11. **Bowls, and bowls in the italic:**
    - Read a lowercase bowl whole, tall over wide, against b; the face draws
      nothing under 0.87. F26.
    - An italic letter built upright and slanted reads its donor figures off
      the roman (`recipes.sloped`). F27.
    - A stroke check on an italic change reads the SHEARED, built letter at
      every weight; `wrap.py` reads only the upright recipe. Compare the tight
      turn to the loose one against the italic P and R. F28.
    - A correction switched by a per-style flag switches at BOTH masters: gate
      it on what each master does. F28.
    - Before taking a shape from the panel, find the Latin letter with the
      same construction and take its answer. F28.
    - A sloped bowl that is a shortened o tips further than o: read its long
      axis against o at every weight. F29.
12. **A node that sits on its neighbour at one master draws a corner at
    another.** It cannot be removed — node counts must match — and it must
    not be moved, however idle it looks: the weights between average the
    masters node by node, so moving it walks a cusp across them.
    Reparameterise the NEIGHBOUR along the neighbour's own curve. F32.
    - A collapsed pair also hides the corner it sits on: a probe whose arms
      reach 25 units either way reads the junction as flat. Read the corner
      angle at every master, before and after. F32, F3.

## Reporting

- **Always show a rendered sheet, and always as SVG.** Text-only progress is
  useless. Write to `tools/out/` and copy the file to
  `/mnt/c/Users/Admin/Downloads/` — a path under the WSL filesystem is one the
  user cannot open.
- **`tools/svgsheet.py` is how they are drawn.** An SVG carries the font's own
  path data, so one file answers a join question at 12px and at 1200 and the
  reader does the zooming. Counters punch through with
  `fill-rule="evenodd"`. A line that says 12px is rasterised by the viewer the
  way a screen will. Why this replaced PNG sheets: METHOD §5.
- **Every letter on the sheet is the face's own, labels included.** Live
  `<text>` falls back to whatever the viewer has installed, and a heading set
  in Cascadia put a tailed `l` and a two-storey `g` on a specimen where every
  Latin letter reads as ours. Headings and row labels go in as outlines too.
- **I cannot see an SVG directly.** Rasterise a throwaway copy with headless
  Edge (`--headless --screenshot=`, Windows paths both sides) into the
  scratchpad — never into Downloads, which is the delivery folder. Check it for
  collisions before sending.
- **Never show a glyph alone.** In context and in comparison: beside its own
  case pair, beside the Latin it shares a line with, in words, at 12px and
  14px as well as display size. JetBrains rows are for calibration, never for
  imitation.
- **Comparing candidates means side by side and adjacent, per weight** —
  never one block above another, which is what `specimen.py --against OLD_DIR`
  draws against a stashed build. Say which candidate is on disk: one that was
  never built has not been through the gates.
- **Never show coordinates, node counts or point data.**
- Own the objective quality: every gate passes *before* anything is shown.
- No `Co-Authored-By` trailer in commits.

## Approval

**Every glyph needs explicit approval, per glyph** — not per batch, and not
implied by a sheet having been shown. Draw → build → `verify.sh` unfiltered →
regenerate the preview → show it → wait for the verdict. A glyph is *in
review* until the user says otherwise.

**After any change to a glyph, regenerate the preview and show it again.** The
user judges from the picture; a stale picture is a false report.

**Approval does not cross the case pair**, however much construction the two
share — record the case that was named. And **record what was still outside
the panel when the glyph was approved**, or the next measuring pass will find
it, call it a defect, and change a frozen glyph.

Record every approval in `docs/APPROVALS.md`. Why the ledger exists: METHOD §6.

## Write down what the round taught, every time

**A glyph is not finished when it is approved. It is finished when what it
taught is written down** — as the last step of the round, while the
measurements are still on screen.

Ask three questions:

1. **What was the fault, as a class rather than as a letter?** An instance of
   an existing F-entry, or a new entry at the next free number.
2. **What is now known that was not?** A relation between parts → METHOD §2.
   A settled question → §8, and take its thread out of §9. A new instrument →
   a row in §4 (`docs_check.py` fails until it has one).
3. **What would have caught it sooner?** One statement in *Before changing
   anything* or *Approval* here, with a pointer. The story goes to METHOD,
   never here.

Keep the numbers — the readings at both masters and the band they were
compared against; a finding without them cannot be re-checked. A thread that
resolves comes out of §9; a probe that is fixed stops being listed as broken.

The test of whether it is worth writing: **would it change what the next
glyph does?** A note that only records that something happened is not worth
the line.

## Machine

Treat memory as scarce: one heavy job at a time, stream rather than slurp, no
background pollers. **Write the code frugally too** — least RAM, fastest run —
and install a better library or tool when that is what it takes.

**Cap the parallelism of anything you did not write.** `make build` has now
OOM-killed this machine twice, and the second time took the whole VM down: it
hands the work to ninja with no arguments, ninja defaults to one job per core
plus two, and eighteen cores means twenty concurrent fontmake processes. Use
`make mono`, which caps it at `JOBS` — see *Pipeline*. Because the full target
does `rm -rf fonts` first, an OOM mid-run leaves **no fonts at all**; check for
a half-removed output directory before assuming the tree is intact.

**One heavy job per command, and read a gate's output from a file.** The two
things that hung this machine outright:

- `build_cyrillic && make build && verify.sh` in a single command. `verify.sh`
  opens all 65 panel fonts, and it started while fontmake's peak was still
  resident. Run the three steps as three commands.
- Running `verify.sh` a *second* time to look at a different part of its
  output. It is the most expensive thing in the repo. Run it once into a file
  and read the file:

  ```
  bash tools/verify.sh 2>&1 | tee $SCRATCH/verify.log; tail -2 $SCRATCH/verify.log
  ```

  This is not a licence to grep the gate — the whole log must be read, just
  not regenerated.

  **And never pipe it into `head`.** `head` closes the pipe as soon as it has
  its lines, `tee` takes the SIGPIPE, and the gate is killed part way through:
  the log looked complete at 99 lines against the real 208, with the signature
  readings and the verdict simply absent. Redirect to the file and read the
  file — which then costs the second run this rule exists to avoid.

The same applies to probes. A numpy crop `a[y0:y1, x0:x1]` is a **view** that
keeps the entire canvas alive, so a probe holding a dozen cropped glyphs was
holding a dozen full rasters — `.copy()` at the crop. And rasterise no larger
than the question needs: canvas cost is quadratic in the pixel size.

**Any script you write is written to be run again, so write it efficiently.**
Open a file once, loop the expensive thing on the outside, hoist out of the
inner loop anything that does not vary with it, and search coarse before
searching fine. A probe that takes minutes stops being run, and a question
that stops being asked gets answered by guessing. METHOD §4 has the four rules
and what each one cost.

Font discovery for the panel and the specimen reads the host system's
installed fonts; override the search roots with `SUSE_FONT_DIRS` (colon
separated) if they live elsewhere.

## Design rules that are not in any gate

This is the signature: when a letter "doesn't belong", one of these is
usually missing.

- Where one stroke **turns**, it rounds; where two **cross**, it stays square.
- Corner radius tracks **stroke weight**, not letter height — L's outer turn
  runs 103 at Thin and 122 at ExtraBold, its inner 78 and 20.
- A short stroke takes the reduced corner (`RADIUS`): a bend is bounded by
  the shorter of the two strokes it joins.
- Terminals are cut square and flat, on the cap line, baseline and x-height.
- A lowercase turn is never tighter than the capital's — at ExtraBold this
  face turns *wider* in t and f (168) than in E, F, L (122).
- Everything sits in a 600-unit cell the Latin is already fitted to.
- Never mirror: И, Я, Э are not flipped N, R, C.
- Never scale a capital down for a lowercase. Redraw stems at lowercase weight.
- **The letter widens, then counters give way, then stroke weight** — in that
  order. Interior strokes thicken at about three-quarters the rate the stem
  does. Measure the parts **against each other**, not only against the stem.
  METHOD §2 has the ratios and the order to diagnose them in.
- Design the heaviest master first.

## How the code is organised

Details: METHOD §7.

- `classify.py` assigns every letter a **tier**: T1 a Latin component, T2
  assembled from existing parts, T3 newly drawn. Take the highest tier the
  letter honestly allows.
- `recipes.py` builds each glyph per master; `lc()` runs a recipe through the
  `Lower` view (`params.py`), which answers with the lowercase's own stem, bar
  and sidebearings while `paths` still returns the real Latin.
- `geom.py` is the outline algebra. Recipes are written in it, not in raw
  coordinates.
- **A green mechanical run is not evidence a glyph is right.** Node parity
  cannot see that a glyph is the wrong size — it passed Э drawn at cap height.
- **The font never depends on another face.** A donated outline is fitted
  once and committed as data (`be_donor.py`, `ge_donor.py`, `de_donor.py`);
  its generator is not kept.
  Other faces are read only to measure — the panel, the `tools/ve` probes.
  METHOD §4, *Retired*.
- **Every gate here reads the INK. None of them reads the OUTLINE.** Run
  `tools/outlines.py` on anything donated or newly drawn, and prefer a **CFF**
  donor — a TrueType one arrives as quadratics and expands to a node every few
  units. г shipped at 34 nodes against o's 8 before this was checked.
