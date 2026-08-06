# Method

How to investigate a glyph in this project, and the mistakes that keep
recurring. Nothing here restates a per-glyph value — those live in
`tools/recipes.py`, next to the code, with their reasoning. This is the layer
that lives nowhere else.

Each rule is tagged with what enforces it. **prose only** means nothing checks
it; it survives because it is written here.

---

## The objective

**The Cyrillic must read as SUSE Mono — not as Cyrillic added to SUSE Mono.**
A reader should not be able to tell which letters came later. This is the goal
every rule below serves, and when a rule and this goal disagree, this goal
wins.

The user is a native Ukrainian reader and not a type designer, so the reports
that matter arrive in exactly these terms: *"ю simply doesn't belong and
doesn't have SUSEMono signature"*, *"ґ has [the] defect you've fixed with
[the] uppercase version before which drops SUSEMono signature"*. Both were
real, and neither was visible to any measurement running at the time.

### The signature is concrete

It is not a feeling. It can be enumerated, and every item is readable off the
Latin:

- **Where one stroke turns, it rounds. Where two cross, it stays square.**
  This is the single most characteristic thing about the face.
- **A corner's radius tracks stroke weight, not letter height** — L's outer
  turn runs 103 at Thin and 122 at ExtraBold while its inner runs 78 and 20.
- **A short stroke takes the reduced corner** (`RADIUS`), because a bend is
  bounded by the shorter of the two strokes it joins.
- **Terminals are cut square and flat**, on the cap line, the baseline and the
  x-height alike.
- **A lowercase turn is never tighter than the capital's.** At ExtraBold this
  face turns *wider* in t and f (168) than in E, F and L (122).
- Everything sits in a **600-unit cell** that the Latin has already been
  condensed and optically fitted to.

When a letter "doesn't belong", one of those is usually missing. г's corner had
been halved by a reduction meant for short strokes; ґ's notch had been squared
by a subtraction that went negative; ю's join had been made too short to read.

### The host is the authority, the panel is not

This is why **host before panel** (§1) is the first rule of method, and it is
worth being blunt about the asymmetry:

- The **panel** can only tell you **which relations exist** across monospace
  design generally — that ф widens with weight, that г's arm is shorter than
  Г's, that a tick rises about 0.21 of the cap.
- The **host** tells you **what the value is** in *this* face, and what the
  shape must look like.

A panel median is never a reason to change something the face already does
consistently, and never a reason to change a letter the user has approved.
Sixty other faces are evidence about typefaces in general; they are not
evidence about this one.

### Derived beats drawn, for this reason

The tier system (§5) is not an efficiency measure. The Latin has already been
condensed, fitted and optically corrected inside its cell. A glyph derived from
it — a component, or a construction reading its corners and stems off it —
**inherits that work**. A glyph drawn fresh throws it away and has to re-earn
it, and will not fully succeed. Take the highest tier the letter honestly
allows.

### How to test it

Not by looking at the letter alone:

- **`checkpoint.py`'s "vs Latin" row** — each new lowercase beside the Latin
  lowercase it shares a line with.
- **The mixed Latin/Cyrillic line** — `git commit -m 'юність' v2.1
  build/ґрунт-єднати.log`. A bolted-on script shows here before anywhere else,
  because the eye compares scripts directly across a word boundary.
- **The JetBrains rows** are for calibration, not imitation. They answer
  "is this within the range a professional Cyrillic occupies", not "does this
  belong to SUSE Mono".
- **Reading sizes, 12px and 14px.** Signature failures that survive at display
  size often vanish or invert at text size, which is where the face is used.

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

## 2 · Internal relations

**A glyph's parts must be measured against each other, not only against the
face's stem or the advance.** This is the principle the ф and Ф work came out
of, and it is worth stating on its own because a letter can be correct on
every absolute measure and still read wrong.

### Why the relations exist

As a face gets heavier its parts do **not** scale together. Across the panel,
light cut to heavy cut:

| | growth |
| --- | --- |
| the face's stem | **×2.51** |
| ф's bowl wall | ×1.92 |
| ф's middle stem | ×1.78 |
| ф's counter | ×0.57 — *shrinks* |
| ф's total width | ×1.05 |

Interior strokes thicken at roughly **three-quarters the rate the stem does**,
the letter widens a little to buy room, and the counters give up the
difference. Scale everything uniformly instead and the counters are what pays,
which is exactly how a bold letter turns ugly.

Stated as ratios rather than growth, the same thing:

| ÷ the face's own stem | panel light | panel heavy |
| --- | --- | --- |
| ф bowl wall | 0.99 | 0.85 |
| ф middle stem | 0.97 | 0.81 |
| Ф bowl wall | 1.03 | 0.86 |
| Ф middle stem | 1.00 | 0.78 |

### The ratios worth reading

One scanline through the middle of a letter gives most of these at once
(`tools/probe.py: runs`, `gaps`, `vruns`):

- **part ÷ the face's own stem** — does the interior thin as the face
  thickens, or is it still at full weight?
- **middle stem ÷ counter** — the ratio that actually reads as *ugly*. See
  below.
- **counter ÷ stem** — how much white survives.
- **bowl width ÷ bowl height** — is the bowl round, or squashed?
- **counter width ÷ counter height** — the same question of the white.
- **symmetry** of the parts either side of a crossing stroke.
- **the letter's width ÷ the advance** — the room the rest is competing for.

### Absolute measures can all pass while the letter is wrong

This is the part that matters. When the capital Ф was reported as ugly at
heavy weights, its counters were **0.35 of the stem against a panel 0.42–0.61**
— outside, but only somewhat. The reading that matched what the eye saw was
**middle stem ÷ counter at 2.83 against a panel 1.14–1.83**: the stem was
nearly three times the white it sat between.

Conversely the lowercase ф's counters were, weight-matched, *inside* the panel
all along. Its fault was elsewhere — the bowl never widened — and no
counter-only check would have found it.

**A ratio between two parts of the same glyph carries information that neither
part carries alone.** Measure the pair.

### The order things give way

Counters first, stroke weight last — and *before either*, the letter widens.
That third term is easy to miss and was the whole of ф's fault: it had the
right strokes and the right counters for its width, and the width was frozen.

### Diagnosing "it gets ugly when bold"

In this order, because each step changes what the later ones read:

1. **Does the letter widen with weight?** Compare width ÷ advance against the
   panel *bucketed by weight*. (ф's fault: 0.863 flat against 0.832 → 0.938.)
2. **Do the interior strokes thin?** wall ÷ stem and middle ÷ stem against the
   same buckets. (Ф's fault: 1.01–1.02 flat against 1.03 → 0.86.)
3. **Is the bowl's aspect right?** A bowl widened without being made taller is
   a squashed oval — correct in every stroke and still wrong. (Both letters'
   second round.)
4. **Only then the counters themselves**, which by this point are usually
   fixed as a consequence.

Steps 1–3 are all about relations between parts. The counters are the
symptom, and going straight at them treats the symptom.

---

## 3 · Fault catalogue

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

## 4 · Probe inventory

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
| `classify.py` | the tier table — what is derived, and from what | — |
| `geom.py` | outline algebra over Glyphs paths (22 primitives) | — |
| `build_cyrillic.py` | writes recipes into the Glyphs source; `--rebuild` drops and redraws | — |

`verify.sh` runs all five gates in order and exits non-zero on any failure.
`review.sh` regenerates **every** review image from the current build — use it
rather than rendering one sheet, because reviewing an image made before the
last fix wastes a round.

Only `probe.py` reads built fonts and the panel through one lens, which is what
makes "ours" and "theirs" the same quantity. Everything above it reads the
source, one master at a time.

---

## 5 · Rendering for review

Every report is a picture. Text-only progress is useless to the user, who is a
native Ukrainian reader and not a type designer — the render *is* the finding,
and a bad render wastes the round.

### Quality is not optional — *prose only*

A sheet was shipped this session with hard-aliased edges because the outlines
were filled into **1-bit masks**. Every edge was thresholded, nothing was
antialiased, and the user's response was that it was unreadable. The
requirements:

- **Supersample ×4, then downsample with Lanczos.** Fill into an oversized
  mask and resize; never draw at final size.
- **Even-odd fill per contour** — XOR each contour into the accumulator so
  counters punch through. Filling contours independently makes every bowl
  solid.
- **Flatten curves to at least 24 steps.** Control points are not vertices;
  see F6.
- **Real TrueType labels** at a readable size, not PIL's default bitmap font.
- **Check for collisions** before sending. Glyphs that overshoot their box
  will sit on top of their own captions.
- **Write to `tools/out/`.** The session scratchpad under `/tmp` is not
  reachable by the user; images left there cannot be looked at.

### Never show a glyph alone — *prose only*

A letter judged in isolation tells you almost nothing. The failures in this
project were all visible only in company:

- **Beside its own capital or lowercase** — the case pair.
- **Beside the Latin it shares a line with.** The `vs Latin` row.
- **In words**, so the eye reads rhythm and colour rather than shape.
- **At 12px and 14px as well as display size.** Faults at display size often
  invert or vanish at the size the face is used at.
- **Beside JetBrains** for calibration — is this within the range a
  professional Cyrillic occupies — never for imitation.

### Comparing two candidates — *prose only*

Put them **side by side, adjacent, per weight** — not one block above another.
Stacked variants force the eye across a gap and the difference stops being
legible. Label which is which under each, and include the same comparison in
a word at reading size.

State plainly which candidate is on disk. A rendered alternative that has
never been built has not been through the gates, and the user should be told
that rather than left to assume.

### Regenerate after every change — *`tools/review.sh`*

`review.sh` rebuilds **every** review image from the current build. Reviewing a
sheet made before the last fix wastes a round, and it has happened.

---

## 6 · Approval

**Every glyph needs the user's explicit approval, per glyph.** Not per batch,
not implied by a checkpoint sheet having been shown.

The loop:

1. Draw or change the glyph.
2. Build, and run `tools/verify.sh` **unfiltered**. Every gate passes before
   anything is shown — objective quality is not the user's job.
3. Regenerate the preview (`review.sh`) and show it, in context and in
   comparison.
4. Wait for the user's verdict. A glyph is *in review* until they say
   otherwise.
5. On approval, record it in `docs/APPROVALS.md`.

After **any** change to a glyph, however small, the preview is regenerated and
shown again. The user judges from the picture, so a stale picture is a false
report.

### Why the ledger exists

`docs/APPROVALS.md` is the record of what has been approved and therefore what
is frozen. Without it the rule "never change an approved glyph" is unenforceable
— this session reached the point of asking *"is Ф approved?"* with no way to
answer, having already changed Ґ twice without noticing it was approved.

An approved glyph is frozen. A panel median is not evidence against it; if it
genuinely must change, say so and ask first. When a new sibling should match an
approved one, **copy the approved construction** rather than generalising it
into a shared helper and re-deriving it — that is precisely how ґ's work
destroyed Ґ's.

---

## 7 · How the code is organised

Worth knowing before reading `recipes.py`, because none of it is obvious from
a single function.

### Tiers — *`tools/classify.py`*

Every target letter is assigned the **highest tier it can honestly take**, to
keep fresh drawing to a minimum. The Latin has already been condensed and
optically fitted to a 600-unit cell; a derived glyph inherits that work and a
freshly drawn one throws it away.

- **T1** — the same drawing as a Latin glyph, as a Glyphs **component**, never
  a copied path, so it tracks the Latin through both masters for free.
- **T2** — assembled from components and parts that already exist.
- **T3** — genuinely new outlines, drawn once and node-matched across masters.

Two rules rule out the obvious shortcuts, and a Cyrillic reader sees a breach
of either immediately: **no mirroring** (И is not a flipped Н, Я not a flipped
R, Э not a flipped С — mirroring reverses terminal cuts and stroke modulation)
and **no scaling capitals down for lowercase**.

### The `Lower` view — *`tools/params.py`*, applied by `lc()` in `recipes.py`

Cyrillic lowercase is largely small-capital in shape, so for most letters the
**construction** carries over unchanged — and *only* the construction.

`Lower` wraps a `Params` and answers with the lowercase's own figures: the
x-height for `cap`, 150 against 161 for the stem, 106 against 135 for the bar,
the lowercase sidebearings. `paths` still hands back the real Latin, so a
recipe reading L's corner or O's bowl gets exactly what it always got.

This is what lets one recipe serve both cases. It is also where **F1** hides:
a recipe that hard-codes a capital's proportion instead of reading it off `pr`
will silently carry that proportion down into the lowercase. `getattr(pr,
"lower", False)` is the test for which case a recipe is running in.

### Outline algebra — *`tools/geom.py`*

`node` / `path` / `rect` / `bbox` / `reverse` / `translate` / `mirror_x` /
`scale_x` / `slant` / `piecewise_y`, plus `corner_radius` and `inner_radius`,
which read the face's own turns off L. Recipes are written in these, not in
raw coordinates.

---

## 8 · Settled findings

Things established by measurement that are not method and not a fault.

### Node parity says nothing about size

Э was drawn at **cap height** while being a lowercase letter, and the
interpolation-compatibility check passed it without complaint. Parity checks
path count, node count, order, start node and direction. It cannot see that a
glyph is the wrong size, in the wrong place, or the wrong letter. A green
mechanical run is not evidence that a glyph is right.

### Optical width is not bbox width — *no metric captures this*

л read "too wide" twice while every width metric said it was fine. The cause
was its **sloped leg**: a slanted stroke reads wider than its bounding box
against upright neighbours. There is no measurement in this project that sees
it, and the user's report was the only signal. When a width complaint survives
a clean width measurement, look for a diagonal.

The same asymmetry is why `check.py` reads Л and Д on their vertical right
stem rather than their leading slanted leg — a horizontal cut across a slope
always measures wide.

### A lowercase's corner set is its capital's

г matches Г **exactly** — `[78, 103]` at Thin, `[20, 122]` at ExtraBold. So ґ
must be г plus the tick's two corners, which is precisely Ґ's set. Reasoning
from that identity found three wrong corners in ґ at once, where measuring
them one at a time had missed them.

Corollary: at ExtraBold this face turns **wider** in the lowercase t and f
(168) than in E, F and L (122). The capital's radius is a **floor** for a
lowercase corner, never a ceiling.

### Not every constant hides a relation

The weight sweep checked eleven flat constants and found **one** genuine
instance (`EF_WIDTH`). `EF_HEIGHT` (4% spread), `TICK_RISE` (4%) and
`YERU_INK` came back genuinely flat or already tracking the panel.

`TICK_RISE` matters twice over: the panel holds Ґ's tick rise at 0.212–0.221
of cap height at *every* weight, so the approved 0.21 is right — and a
"rise follows the stem" alternative that had been proposed would have moved it
**away** from the panel. Measure before changing an approved glyph, and the
measurement may well defend it.

---

## 9 · Open threads

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
