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
rm -f build.stamp && make build
bash tools/verify.sh          # all seven gates, in order
bash tools/review.sh          # regenerate EVERY review image from this build
```

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

## Reporting

- **Always show rendered PNGs.** Text-only progress is useless. Write them to
  `tools/out/` (gitignored, but the user can open them) — not to a scratch
  directory under `/tmp`, which they cannot reach.
- **They must be high quality.** Supersample ×4 and downsample with Lanczos;
  XOR each contour so counters punch through; flatten curves to ≥24 steps;
  real TrueType labels; check nothing collides. A 1-bit fill produces hard
  aliased edges and has been rejected as unreadable.
- **Never show a glyph alone.** In context and in comparison: beside its own
  case pair, beside the Latin it shares a line with, in words, at 12px and
  14px as well as display size. Comparing two candidates means side by side
  and adjacent, per weight — never one block above another.
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

## Hard problems — ask a Fable advisor

For a genuinely hard or ambiguous question, get a second opinion: spawn a
subagent with the Agent tool and `model: "fable"`. Worth it for a design
judgement the measurements do not settle, a finding that might be a probe
artefact, a construction with no obvious donor (the Serbian nine are the open
case; б was, and is settled), or a choice between two constructions that both
pass every gate.

Give it **the measurements and the specific question** — it has none of this
session's context, so "what do you think of ф" gets nothing useful while "the
bowl is 1.13 wide for its height, the panel holds 0.97–1.08, the height is
already at the panel ceiling — what gives?" gets something.

Treat the answer as advice, not authority. The face's own Latin is still the
authority on the shapes, the user's eye is still the verdict, and this is not
a substitute for measuring or a shortcut around routine work.

## Machine

Treat memory as scarce: one heavy job at a time, stream rather than slurp, no
background pollers. A `make build` has been OOM-killed mid-run before now,
which deletes `fonts/` — check for a half-removed output directory before
assuming the tree is intact.

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
