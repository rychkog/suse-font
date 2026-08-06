# Method

How to investigate a glyph in this project, and the mistakes that keep
recurring. Nothing here restates a per-glyph value — those live in
`tools/recipes.py`, next to the code, with their reasoning. This is the layer
that lives nowhere else.

Each rule is tagged with what enforces it. **prose only** means nothing checks
it; it survives because it is written here.

---

## 1 · Method

### Host before panel — *prose only*

Two authorities, and they answer different questions.

- The **panel** (60 monospace faces on this machine, `tools/panel.py`)
  establishes **that** a relation holds, and roughly where.
- The **host** — SUSE Mono's own Latin — supplies **what** the value is.

Before calling anything a defect, measure the face's own Latin first. When г's
arm looked long, the panel said it was; but the check that mattered was whether
SUSE's Latin lowercase runs as wide as its capitals. It does (0.98–1.06, panel
median 1.012), so the spacing was normal and г really was the fault. Had the
Latin been unusual, the panel's opinion would have been beside the point.

**Corollary, and it has caught two bad checks:** run every new check over the
face's own Latin. `tools/audit.py --selftest` exists for this and is a gate.
A width-ratio check was withdrawn for flagging в and ж; a self-crossing check
was withdrawn for flagging B five times, e three times, b twice, and three
digits. A check that condemns the host is measuring the wrong thing.

### Bucket the panel by weight before believing a median — *prose only*

**A median taken across every face at once averages light and heavy cuts
together and hides any relation that moves with weight.**

`EF_WIDTH = 0.863` was "the panel's median across the 51 faces that draw ф".
Bucketed by the face's own stroke weight, the same panel reads 0.832 / 0.842 /
0.871 / **0.938**. Faces widen ф as it gets bolder so the counters survive.
Held flat, this face was too wide at Thin and below the entire panel range at
ExtraBold — which is exactly how it read, a fat bar between two slits.

This is the single most productive question to ask of any flat constant: *does
the panel hold this steady across weight, or did I average a slope into a
point?*

### Compare nearest-neighbour, not by band — *`tools/probe.py: compare`*

Bands put a face sitting at its own band edge next to faces two steps away.
SUSE's Regular (stem 0.086 of the em) falls in a "light" bucket whose median is
set by cuts far lighter than it, and that produced a confident-looking "counter
well under the band" that was pure banding artefact. Bracket against the ~11
panel faces nearest in stem weight instead.

### Prefer relations linear in the stem — *prose only*

There are two masters and instances interpolate **linearly**. A relation that
is a straight line in the stem is therefore reproduced *exactly* at Regular and
Bold; a curved one drifts off itself in the middle of the axis.

Every relation fitted so far is a least-squares line of the quantity against
`stem / em` (`tools/probe.py: fit`). See `EF_FIT` and `ARM_SHARE` in
`recipes.py`.

### Clamp any fit to the range it was fitted over — *`tools/strokes.py`*

This face draws Thin at **0.029** of the em. The panel's lightest face is
around 0.05. Every line fitted over the panel is therefore **extrapolating** at
Thin, and extrapolation there asked for a ф bowl wall heavier than the stem it
crosses (1.03 against a panel maximum of 1.02). The stroke gate refused it,
correctly. `ef_fit` now clamps at 1.0.

### Two masters cannot hold three points — *prose only*

You may set the ends. The middle is forced.

Promising "Thin and Regular stay untouched" while changing ExtraBold is not
something the format can deliver: shortening г's ExtraBold arm pulled Regular
from 407 to 383 by interpolation. Say what will actually move.

### Ceilings, not assignments — *prose only*

Where the face already does better than the panel's share, keep the face's own
value: `min(own, panel_target)`. The face is the authority on what it already
does well; the panel is only the authority on the relation. This is how
`lc_arm_end` leaves Thin alone and pulls only the heavy end back.

### Verify a gate by breaking it — *prose only*

After writing or rewriting a check, feed it an impossible threshold and confirm
it fires. `check.py`'s stroke comparison was re-verified at a 2% tolerance,
where it flags seven glyphs. A gate that has never been seen to fail has not
been shown to work.

---

## 2 · Fault catalogue

Seven classes. Each has recurred at least twice.

### F1 · A constant measured in one condition, carried to another

The most frequent fault in this project by a wide margin.

- `legSplay`, measured on the capital A, carried to л.
- Ґ's tick rise — the capital's `0.21 × cap` applied to ґ, whose panel figure
  is `0.28 × x-height`. A shorter letter needs proportionally more tick; the
  capital's number made the notch read thick.
- `EF_OVERHANG`, a capital constant, borrowed to the lowercase ф and flattening
  its bowl.
- `midY`, H's, applied where the case's own middle was wanted.

**Tell:** a constant whose name or docstring mentions one glyph, used in
another. **Fix:** re-derive it in the new condition; do not scale the old one.

### F2 · `outer − stroke` as an inner radius

Goes negative once the stroke outgrows the corner, floors at its minimum, and
squares off a turn this face holds round.

Fixed at: г's corner, в's counter, `bowl_pair`'s counter, ґ's stem-into-arm
corner (which was at 4 units at ExtraBold where the face turns at 20).

**Legitimate** where the *shorter* stroke bounds the bend — Ґ's tick
(`recipes.py:483`), ґ's matching tick bend (`:595`), and `comb` (`:241`, where
the arc branch must not vanish or node parity breaks).

**Still unreviewed:** `shoulder_spine` (`:1304`). It has not produced a visible
defect, but it is the same expression in the same position.

**Fix:** `inner_radius(pr)` — the face's own, read off L.

### F3 · `crowd3` applied where it does not belong — in both directions

`crowd3` is m's *three-stems-in-one-cell* reduction.

- **Applied too widely:** to the bowls of Б, Ь, Ъ, Я, ю and Ф. A bowl is not
  three stems.
- **Left in place where the panel wants less:** the lowercase ф kept it and
  came out at 0.78 of the stem where the panel holds 0.82–0.93 — which is why
  its counters read airy once the bowl was widened.

**Tell:** `crowd3` on anything that is not literally three stems in a cell.

### F4 · A median across a mixed population hiding a relation

See `EF_WIDTH` above. **Tell:** any constant whose comment reads "the panel's
median across N faces". Re-measure it bucketed by weight before trusting it.

### F5 · A metric reused whose definition does not match the question

`capWidest` / `lcWidest` are maxima over the *whole* alphabet, so the capital
side is Y at 565 and their ratio measures how splayed the widest capital is —
not how the two cases are spaced. Using them for г's arm would have been
wrong by a different route than the bug being fixed. `lcCapWidth` was added
instead, measuring the same letters the panel reading was normalised by.

**Tell:** the metric exists and is *nearly* right. That is the dangerous case.

### F6 · A broken probe reported as a finding

Every one of these was announced as a defect before being caught:

- `check.py`'s `flat()` took curve **control points** as polygon vertices
  instead of flattening. At Bold it missed ф's counter crossing the scanline,
  so the "first stroke" ran from the outer wall across the counter to the stem
  — 221 units against a true 125, reported as a +52% error that did not exist.
  **Fixed**; it had been mis-measuring every round letter it touched.
- The `HARD_SHOULDER` probe scanned at 0.93 of cap, *below* Ъ's 28-unit bar at
  Thin, and read 0.000. **Still broken.**
- The `EF_OVERHANG` probe measured the stem above the **cap line** rather than
  above the **bowl**, read 0.000, and was reported as "the constant is lying
  about itself". It was not. **Corrected.**
- `checkpoint.py`'s red silhouette row scales each lowercase so its x-height
  equals cap height. Meaningful for ю, є, ґ, д, л; meaningless for ф, which
  runs ascender to descender — and it will misreport б once б exists.
  **Still broken.**

**Tell:** a reading of exactly 0.000, or one wildly out of family with its
neighbours. Reproduce it with an independent probe before reporting it.

### F7 · Silent failure

A step that does nothing and says nothing.

Observed: the build piped to `/dev/null`; a `git push` error swallowed by
`tail`; gates exiting 0 while holding findings; a `grep` filter hiding a broken
interpolation; `build_cyrillic` doing nothing after a commit; `check.py`
running its entire suite on import, so importing one function runs the gate.

**Rule:** run `tools/verify.sh` unfiltered and read all of it. Do not grep the
output of a gate.

---

## 3 · Probe inventory

| tool | measures | gate? |
| --- | --- | --- |
| `check.py` | mechanical + interpolation compatibility, stroke vs a like-shaped Latin | yes |
| `audit.py` | defect classes over drawn glyphs | yes |
| `audit.py --selftest` | the same thresholds over the face's own Latin — must stay clean | yes |
| `panel.py` | ink area vs 60 faces | yes |
| `strokes.py` | lightest stroke ÷ own stem vs 49 faces | yes |
| `probe.py` | scanline runs on **built** fonts + panel comparison and fitting | no |
| `params.py` | per-master figures measured off the Latin | — |
| `latin_metrics.py` | what the Latin says about the face | — |
| `preview.py` | rasterise from recipes without a build | — |
| `checkpoint.py` | the review sheet | — |

`verify.sh` runs all five gates in order and exits non-zero on any failure.

Only `probe.py` reads built fonts and the panel through one lens, which is what
makes "ours" and "theirs" the same quantity. Everything above it reads the
source, one master at a time.

---

## 4 · Open threads

- **о does not follow the panel's weight relation.** Relative to the face's own
  о, ф's bowl measured 1.205 at Thin and 1.040 at ExtraBold against a panel
  1.000–1.188 / 1.062–1.157 — crooked in the opposite direction from the
  advance-normalised reading. о underlies every round letter in the set, so
  this is the highest-value thread left.
- **`shoulder_spine` (`recipes.py:1304`)** still carries the F2 subtraction.
- **Three broken probes**: `HARD_SHOULDER`, `ZHE_STEM`, `YU_GAP` (the last two
  return too few faces to judge — Ж's diagonals and ю's join give variable run
  counts at a fixed height).
- **`checkpoint.py`'s red silhouette row** misreports ascender-to-descender
  letters.
- **ф at Regular and Bold** is marginally wide for its height (1.06 against a
  1.02 ceiling; 1.07 against 1.06). Its bowl cannot grow — the height is
  already at the panel's ceiling at ExtraBold — and the residual is the linear
  width fit running generous mid-axis, which two masters cannot bend.
- **14 glyphs undrawn**: б з к м, the Serbian Ђ Љ Њ Ћ ђ љ њ ћ џ, and ќ (blocked
  on к). б is the hard one — no capital, no Latin donor.
- **Checkpoint C: the italic.**
