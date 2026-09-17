# SUSE Mono — Cyrillic

Adding Ukrainian + Russian Cyrillic to SUSE Mono, a Latin-only monospace with
Glyphs.app sources. Two masters (Thin 100, ExtraBold 800), sloped-roman italic
to come. Glyphs are **generated from recipes**, not drawn by hand — see
`tools/recipes.py`.

The project brief is kept outside the repository and is binding.
**`docs/METHOD.md` is how to investigate** — read it before changing any
constant.

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

Test it in company, never alone — the "vs Latin" row on the checkpoint sheet,
the mixed `git commit -m 'юність' build/ґрунт-єднати.log` line, and at 12px
and 14px. `docs/METHOD.md` opens with what the signature concretely consists
of.

## Pipeline

Use it. Do not invent one. `python` is not on PATH; use `./venv/bin/python`.

```
./venv/bin/python tools/build_cyrillic.py sources/SUSEMono.glyphs --rebuild
./venv/bin/python tools/build_cyrillic.py sources/SUSEMono-Italic.glyphs --rebuild
rm -f build.stamp && make mono   # NOT `make build` -- see below
bash tools/verify.sh          # all seven gates, in order
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

1. **Never change an approved glyph without explicit confirmation.** The brief
   says never to ask about design decisions; that applies to work not yet
   approved. Once the user has accepted a glyph, approval is a fact about the
   artefact — a panel median is not evidence against it. When a new sibling
   should match an approved one, **copy the approved construction**; never
   generalise it into a shared helper and re-derive it. This rule exists
   because Ґ was silently changed twice.
2. **"It looks wrong now" after unrelated work is a regression report.** Check
   what was touched since the approval — `git log -p` is a faster answer than
   the panel.
3. **Measure the host before blaming the glyph.** SUSE's own Latin is the
   authority on what this face does; the panel is the authority on what
   relation holds. `audit.py --selftest` must stay clean.
   A panel figure holds only on the row its probe read it on: after using
   one, read ours back with that same probe, in memory, before building. ю Ю's
   gap floor was set at the bowl's extreme from a figure read a quarter up,
   and the first build thinned Ю's walls through the stroke gate.
   `docs/METHOD.md` F1.
   A gate that finds nothing to read in a letter has not passed it: ю's
   crowded roof went unread until its bowl was wide enough to count
   (`docs/METHOD.md` F3).
4. **A flat proportion constant is suspect** until the panel has been bucketed
   by weight. That is how ф was found.
5. **Two constants that justify each other are one decision.** If a constant's
   reason names another step of the pipeline — "nothing moves here, because
   the next step would drag it back" — the pair has to be judged, and usually
   replaced, together. Held apart, each looks correct and the letter stays
   wrong; that is what put a blob at б's junction for three rounds.
6. **Read a two-master construction at the weights in between.** Both masters
   sat inside the panel while Regular was outside it, because a fault that
   scales with how much correction a master needs is smallest exactly where it
   is being looked at. `tools/seam.py` does this by blending, with no build.
7. **A figure read off a donor outline is checked at both masters**, in units,
   before it is used. Two figures a donor holds can sit a stroke apart at Thin
   and a tenth of the cap apart at ExtraBold — Я took R's leg top for R's bowl
   floor on exactly that basis, and only came apart at the heavy end. See
   `docs/METHOD.md` F8.
8. **A glyph that is assembled has a third decision in it, and no gate reads
   it.** Two correct parts placed wrongly pass everything: node parity, panel
   ink, every signature reading. Sixteen marked letters carried their mark on
   the middle of the CELL for a week where this face puts it on the middle of
   the LETTER — ї's by more than a stem. Ask what the host does with the same
   assembly; there is nearly always a Latin letter carrying the same mark.
   `tools/marks.py`. See `docs/METHOD.md` F12.
9. **Ask whether it is the right LETTER before asking whether it is the right
   size.** Every reading this project takes is about proportion, and a glyph
   can match its donor on width to a thousandth, on ink, on stroke weight and
   on lean while being a different letter. К was the Latin K for a week: K
   branches — its leg leaves the arm out in the counter — and Cyrillic К does
   not, and the sentence that hid it was a true one, "к's width is 1.000 of
   k's". What sees it is a **count, not a size**: how many runs of ink lie
   beside the stem, what touches what, how many strokes cross. `docs/METHOD.md` F13,
   which is the entry that reading produced; `ka.py` itself was retired once
   К was settled. A tier-1 donation is where this hides, because a
   donation is never slightly wrong.
10. **A change to a counter is a change to a stroke — run `tools/wrap.py`
   before showing it.** Every reading this project takes of a counter
   describes the white as if it were being drawn; what the eye reads is the
   stroke around it. в measured 1.000 against b on everything `soft.py` takes
   while its stroke bulged by a third at the shoulder, and it was rejected on
   sight. The probe takes a second. A donor figure about a counter also only
   transfers where the donor's OUTER is the same shape — b's bowl is 1.23–1.43
   tall for its width, в's lobes are 0.56.

11. **Read a lowercase bowl as a whole, tall over wide, against b.** A
   capital's construction run at x-height keeps the capital's heights and a
   lowercase cell's width, so every bowl in it comes out flat -- ь stood 0.60
   and я 0.71 where the face draws nothing under 0.87, while every edge
   reading passed. And an italic letter built upright and slanted reads its
   donor figures off the ROMAN (`recipes.sloped`): this face's italic b is a
   different drawing, and its figures overweighted ь's bowl and cut its stem.
   And the shear itself knots one turn of any round end — compare the tight
   turn to the loose one against the face's italic P and R, at every weight.
   A stroke check on an italic change reads the SHEARED letter: `wrap.py`
   reads the upright recipe, and passed a counter that swelled Ы in italic.
   A correction switched by a flag that is set per style switches it at BOTH
   masters: gate it on what that master actually does, then re-read the
   built font at every weight -- Ы's knot came back at all eight unseen.
   And before taking a shape from the panel, find the Latin letter with the
   same construction and take ITS answer: Ы's counter went to the panel's
   straight slot while the face's own D kept the side curved.
   A sloped bowl that is a SHORTENED o tips further than o under the same
   slant: read its long axis against o at every weight. Italic б leant 38-41
   degrees against o's 17-26 until its bowl took o's full height.
   `docs/METHOD.md` F26, F27, F28, F29.

## Reporting

- **Always show a rendered sheet, and always as SVG.** Text-only progress is
  useless. Write to `tools/out/` and copy the file to
  `/mnt/c/Users/Admin/Downloads/` — a path under the WSL filesystem is one the
  user cannot open.
- **`tools/svgsheet.py` is how they are drawn.** An SVG carries the font's own
  path data, so one file answers a join question at 12px and at 1200 and the
  reader does the zooming — which is what let ten per-letter PNG sheets become
  one `specimen.py`. Counters punch through with `fill-rule="evenodd"`, not by
  XOR-ing contours; the reading-size rows need no magnification trick, because
  a line that says 12px is rasterised by the viewer the way a screen will.
  Supersampling and Lanczos no longer apply — there is nothing to resolve.
- **Every letter on the sheet is the face's own, labels included.** Live
  `<text>` falls back to whatever the viewer has installed, and a heading set
  in Cascadia put a tailed `l` and a two-storey `g` on a specimen where every
  Latin letter reads as ours. Headings and row labels go in as outlines too.
- **I cannot see an SVG directly.** Rasterise a throwaway copy with headless
  Edge (`--headless --screenshot=`, Windows paths both sides) into the
  scratchpad — never into Downloads, which is the delivery folder.
- **Never show a glyph alone.** In context and in comparison: beside its own
  case pair, beside the Latin it shares a line with, in words, at 12px and
  14px as well as display size. Comparing two candidates means side by side
  and adjacent, per weight — never one block above another, which is what
  `specimen.py --against OLD_DIR` draws against a stashed build.
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

Record every approval in `docs/APPROVALS.md`. Without that record the rule
above cannot be honoured — this session reached the point of asking "is Ф
approved?" with no way to answer, having already changed Ґ twice without
noticing it was frozen.

## Write down what the round taught, every time

**A glyph is not finished when it is approved. It is finished when what it
taught is written down.** Do this as the last step of every design and every
change that worked — not at the end of a session, when the measurements are
gone and only the conclusion is left.

Ask three questions and write the answers where they will be found again:

1. **What was the fault, in one sentence, as a class rather than as a letter?**
   If it matches one of `docs/METHOD.md`'s F1–F8, add the instance there. If it
   does not, it is a new class and gets its own entry.
2. **What relation or measurement is now known that was not?** Into
   `docs/METHOD.md` §2 if it is a relation between parts, §8 if it is a
   settled question, §4 if it is a new instrument.
3. **What would have caught it sooner?** That answer belongs in this file, in
   *Before changing anything* or *Approval* — the short list of things to do
   differently next time. Keep it to what changes an action.

Also delete: a thread that has been resolved comes out of §9, and a probe that
has been fixed stops being listed as broken. A stale open thread costs a round
the same way a stale picture does.

The test of whether it was worth writing: **would it change what the next
glyph does?** ф's weight fits, о's stem trap and Я's donor fault all did — they
are why к, ж and б have a method to follow instead of a fresh start. A note
that only records that something happened is not worth the line.

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
than the question needs: canvas cost is quadratic in the pixel size, and
`ka.py`, retired now, took every figure as a ratio that resolved fine at
160px.

**Any script you write is written to be run again, so write it efficiently.**
Open a file once, loop the expensive thing on the outside, hoist out of the
inner loop anything that does not vary with it, and search coarse before
searching fine. This is not tidiness — a probe that takes minutes stops being
run, and a question that stops being asked gets answered by guessing.
`harmony.py` took minutes before its loops were inverted and takes 25 seconds
after. `docs/METHOD.md` §4 has the four rules and what each one cost.

Font discovery for the panel and the checkpoint sheet reads the host system's
installed fonts; override the search roots with `SUSE_FONT_DIRS` (colon
separated) if they live elsewhere.

## Design rules that are not in any gate

- Where one stroke **turns**, it rounds; where two **cross**, it stays square.
- Corner radius tracks **stroke weight**, not letter height.
- A lowercase turn is never tighter than the capital's — at ExtraBold this
  face turns *wider* in t and f (168) than in E, F, L (122).
- Never mirror: И, Я, Э are not flipped N, R, C.
- Never scale a capital down for a lowercase. Redraw stems at lowercase weight.
- **The letter widens, then counters give way, then stroke weight** — in that
  order. A glyph's parts do not scale together as the face gets heavier:
  interior strokes thicken at about three-quarters the rate the stem does.
  Measure the parts **against each other**, not only against the stem — a
  letter can pass every absolute check and still read wrong. `docs/METHOD.md`
  §2 has the ratios and the order to diagnose them in.
- Design the heaviest master first.

## How the code is organised

- `classify.py` assigns every letter a **tier**: T1 a Latin component, T2
  assembled from existing parts, T3 newly drawn. Take the highest tier the
  letter honestly allows — derived glyphs inherit the Latin's optical fitting.
- `recipes.py` builds each glyph per master; `lc()` runs a recipe through the
  `Lower` view (`params.py`), which answers with the lowercase's own stem, bar
  and sidebearings while `paths` still returns the real Latin.
- `geom.py` is the outline algebra. Recipes are written in it, not in raw
  coordinates.
- **A green mechanical run is not evidence a glyph is right.** Node parity
  cannot see that a glyph is the wrong size — it passed Э drawn at cap height.
- **Every gate here reads the INK. None of them reads the OUTLINE.** A curve
  can be lumpy, a node can sit where no extreme is, a join can kink, and a
  hundred nodes can do the work of twelve, with every ink reading in band. г
  shipped at 34 nodes against o's 8 that way. Run `tools/outlines.py` on
  anything donated or newly drawn, and prefer a **CFF** donor — a TrueType
  one arrives as quadratics and expands to a node every few units.
