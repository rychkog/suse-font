# SUSE Mono — Cyrillic

Adding Ukrainian + Russian Cyrillic to SUSE Mono, a Latin-only monospace with
Glyphs.app sources. Two masters (Thin 100, ExtraBold 800), sloped-roman italic
to come. Glyphs are **generated from recipes**, not drawn by hand — see
`tools/recipes.py`.

The brief lives at `~/suse-mono-cyrillic-prompt.md` and is binding.
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
bash tools/verify.sh          # all five gates, in order
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

Record every approval in `docs/APPROVALS.md`. Without that record the rule
above cannot be honoured — this session reached the point of asking "is Ф
approved?" with no way to answer, having already changed Ґ twice without
noticing it was frozen.

## Machine

Memory-constrained: one heavy job at a time, stream rather than slurp, no
background pollers. A `make build` has been OOM-killed mid-run, deleting
`fonts/`. Use `grep`, not `rg`. Fork remote is `rychkog/suse-font` over HTTPS.

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
