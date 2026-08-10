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

Review comes from a fluent reader of the script rather than a type designer,
so the reports that matter arrive in those terms — a letter "doesn't belong",
or "drops the SUSE Mono signature". Such reports have been consistently right,
and typically describe something no measurement running at the time could
see.

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

- The **panel** (the monospace faces installed on the host, `tools/panel.py`; 60 at the time of writing)
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
  thickens, or is it still at full weight? For a lowercase that means **n's**
  stem (`probe.lc_stem_of`), not H's; this face's differ by 7%.
- **middle stem ÷ counter** — the ratio that actually reads as *ugly*. See
  below.
- **counter ÷ stem** — how much white survives.
- **bowl width ÷ bowl height** — is the bowl round, or squashed?
- **counter width ÷ counter height** — the same question of the white.
- **symmetry** of the parts either side of a crossing stroke.
- **the letter's width ÷ the advance** — the room the rest is competing for.
- **the height of the band where a scanline reads ONE run** — where the letter
  goes solid. Every assembled glyph has one somewhere and it grows with the
  weight; what matters is how fast. Я's ran to 0.23 of the cap against a panel
  0.17 while its counter above it closed to 0.085 against 0.28. One sweep
  gives both, and the pair localises the fault to the join between them.

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

0. **What is the counter cut out of, and does that grow?** Every counter is a
   span minus the strokes that bound it. Find the span, and check it against
   the panel *as a span* — the bowl's depth, the arm's reach, the gap between
   two stems. A span that is a fixed fraction of the letter while the strokes
   bounding it grow five and a half times is a counter with a countdown on it,
   and no reading of the counter itself says which of the three terms is
   wrong. This is the step Я needed and the one the list above did not have:
   Я passed 1, 2 and 3 — it widened with weight at ×1.16 against the panel's
   ×1.13, its strokes were the face's own, its bowl's aspect tracked the panel
   — and its counter had still closed to a third of what the panel holds,
   because the bowl's floor never moved. Ъ is the same fault in the other
   axis: its shoulder is a share of the cell and cannot move, so its left edge
   alone decides how wide the bowl is, and that edge was flat. A bowl pays for
   its wall twice, so 15% off the span cost half the counter by ExtraBold.
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

Eight classes. Each but the last has recurred at least twice; F8 is here
because the one time it happened it cost the letter its counter.

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
- **Counted twice:** м's uprights took it on top of М's own 0.845 of the stem,
  and М's 0.845 *is* this face's reduction for four strokes across a cell. The
  uprights landed at 0.704 of n where the panel puts them at 0.922 and this
  face's own М puts them at 0.845, and the letter read visibly leaner than the
  п and и beside it. The diagonals keep it: they are what the shorter cell
  actually crowds.

**Tell:** `crowd3` on anything that is not literally three stems in a cell —
and, separately, `crowd3` on a figure already read off a crowded donor. A
ratio taken from М, m or Ж carries that donor's own crowding inside it
already. See F1: this is the same fault, with the condition hidden in a
measured ratio rather than in a written constant.

### F4 · A median across a mixed population hiding a relation

See `EF_WIDTH` above. **Tell:** any constant whose comment reads "the panel's
median across N faces". Re-measure it bucketed by weight before trusting it.

### F5 · A metric reused whose definition does not match the question

`capWidest` / `lcWidest` are maxima over the *whole* alphabet, so the capital
side is Y at 565 and their ratio measures how splayed the widest capital is —
not how the two cases are spaced. Using them for г's arm would have been
wrong by a different route than the bug being fixed. `lcCapWidth` was added
instead, measuring the same letters the panel reading was normalised by.

The same fault, in its cheapest form: `probe.stem_of` reads **H**. Divide a
lowercase part by it and the answer is wrong by however much the face's n
differs from its H — here 7%, which was enough to make a bowl that exactly
matches its own stem read as 0.93 and "outside the panel". `lc_stem_of` reads
n; use it for anything at x-height.

Its most expensive instance was a metric that was exactly right and answering a
different question. б's bowl is 1.000 of о's width, measured correctly over 50
faces — and it was used to decide what *shape* the bowl is, which a width does
not say. Three versions of the letter were built on it and all three were
rejected by eye. See §8.

**Tell:** the metric exists and is *nearly* right — or is exactly right about
something adjacent. That is the dangerous case.

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

- A one-off census of which letters cut a terminal obliquely reported **zero
  Cyrillic letters out of forty-nine** and five Latin ones. `params.paths()`
  is keyed by glyph NAME, and Latin names are their own characters while
  Cyrillic ones are not, so every Cyrillic lookup raised `KeyError` into a
  `try/except Exception: continue` and the letter was silently skipped. Read
  by name instead, the Cyrillic answer is one at Thin and three at ExtraBold.
  **Corrected.** The tell was that the number was a round zero and the loop
  never said how many glyphs it had managed to read; a census that does not
  report its own denominator cannot be checked, and this one was one line away
  from being published as "the Cyrillic has no expressive terminals at all".
- Я's first probe assumed a cut through the bowl gives **three** runs — wall,
  counter, stem. Я's bowl hangs off the stem, so the stem *is* the bowl's
  right side and the cut gives two. The probe returned **zero** faces out of
  sixty-one, including this font's own. **Corrected.** A probe that cannot
  read your own font is broken; it is not evidence the glyph is missing.
- The same probe took the bowl's wall as `widest cut's first run end − the
  letter's leftmost point`. In Я the leftmost point is the **leg's foot**, not
  the bowl, so the wall came out at twice the stem in the light faces.
  **Corrected** to read both edges off the same run.

- `signature.py`'s terminal census took any straight segment about as long as
  the stroke is wide, with the outline turning away at both ends, for a stroke
  **end**. At ExtraBold the stroke is 161 units, so Ж's upper arms — 295 units
  of straight *side* — landed inside that window and were reported as two
  oblique terminals in a letter whose every real terminal is cut flat.
  **Corrected**: a cut is shorter than what it cuts across, so a terminal's
  neighbours are the stroke's two long sides while a side's neighbours are its
  own two short terminals.
- The same file's horizontal census took the shortest ink run up a vertical
  line for a bar, and read the tip of a diagonal or the sliver above a corner
  instead. It flagged **forty-three of the face's own letters**. **Corrected**
  to require a run that persists across a fifth of the width at one height —
  after which Ж still had a phantom horizontal, because near the stem its
  upper and lower arm pairs each cut a short run out of the line. That one was
  caught by its own numbers: it swung from 1.61 of the face's bar at Regular
  to 0.72 at Bold, which no drawn stroke does. **Corrected** by requiring the
  run to hold its height as well as its position.

- Ж's probe swept for the first height where a cut gives three clean runs and
  reported that one. The arm's measured thickness drifts with the height it is
  read at — cut flat against the cap line at the top, running into the stem at
  the bottom — so at Regular the same letter read 0.983 low in the band and
  1.035 high in it, for a ratio the source holds at exactly 1.033 at both
  masters. Interpolation cannot change a ratio both masters agree on, which is
  what gave it away. **Corrected** to a median over the whole band. It had been
  about to send a correct constant back for a second round of tuning.

**Tell:** a reading of exactly 0.000, an empty result set, or one wildly out
of family with its neighbours. Reproduce it with an independent probe before
reporting it. **And a reading that jumps around between the interpolated
weights is a probe, not a glyph** — the two masters interpolate linearly, so a
drawn quantity moves monotonically between them and one that does not is
measuring different features at different weights.

A terminal running out is not a stroke, and `strokes.py` could not tell them
apart. Its lean test cannot: a tip tapers symmetrically, so its centre does not
move and its slope reads zero. Its width window cannot either, because a tip
passes through every width on its way to nothing — so the number reported was
whatever the sampling grid happened to catch. з flagged at 0.374 of the stem;
the face's own **c** read 0.407 and its own **e** 0.431 on the same probe, and
those two are the Latin unchanged.

**Tell, and it is a general one: halve the sampling step.** A reading of the
drawing does not move. c went to 0.360, e to 0.363, э to 0.335 — all sliding
toward the window's own floor of a third of a stem, which is a property of the
probe and not of any letter. Fixed by rejecting a run that loses width fast
between the two scanlines, at a ceiling read off the face: 95 per cent of its
own runs change by no more than 0.061 of themselves over those twelve units,
and every taper it draws exceeds 0.34. After the fix c reads 0.969, e 0.885,
э 0.971 and з 0.892, and none of them moves when the step is halved.

### F6b · A reference set that cannot express the answer

A subtler relative of F6: the probe reads correctly, the reference is honestly
measured, and the comparison is still meaningless because the reference has no
entry the right answer could match.

`signature.py` collected the angles the face cuts its terminals at and
compared the Cyrillic against them. The Latin has no left-opening round
lowercase, so its chamfers are all recorded on one side — and э's chamfer,
which is c's own treatment appearing on the side э opens on, came out as its
mirror and was reported as a foreign terminal. The face's answer is "square,
or chamfered by up to 45 degrees"; which *side* is not part of it.

**Tell:** the finding is a single letter whose construction has no counterpart
in the reference set. Ask what the face would have had to draw for the right
answer to be in the reference at all. If it never draws that thing, the
reference is the wrong shape and not the letter.

### F7 · Silent failure

A step that does nothing and says nothing.

Observed: the build piped to `/dev/null`; a `git push` error swallowed by
`tail`; gates exiting 0 while holding findings; a `grep` filter hiding a broken
interpolation; `build_cyrillic` doing nothing after a commit; `check.py`
running its entire suite on import, so importing one function runs the gate.
`preview.py` and `checkpoint.py` had the same fault and now guard `main()`
behind `__name__`; importing one of their helpers used to re-render the sheet
underneath whatever was being looked at.

A gate that reads only some of the weights is the same fault wearing a clean
result. `audit.py` read Thin, Regular and ExtraBold and never Bold, so м's
wedge counter — 8 units against the face's own 26 — sat in the tree through a
build, a full `verify.sh` and a review sheet without a single gate looking at
it. Regular passed at 35 and ExtraBold has no wedge there at all; the failure
existed at exactly one weight, and that weight was the one not read. Adding
Bold flagged м and nothing else, which is also what makes it safe.

**Rule:** run `tools/verify.sh` unfiltered and read all of it. Do not grep the
output of a gate. And a gate reads **every** weight the family ships that its
own reasoning applies to — an interpolated weight is where a fault lives when
both masters are clean.

### F8 · The wrong figure off the right donor

F1 is the right number carried to the wrong condition. This is its mirror: the
right condition, the right donor, and the wrong number read out of it —
because the donor holds two figures that mean different things and happen to
sit near each other at the light master.

Я took R's **leg top** for R's **bowl floor**. R buries the leg's top edge
inside the bowl's floor, 13 units above it at Thin and 69 at ExtraBold. At
Thin the substitution is invisible; at ExtraBold it is a tenth of the cap, and
it held Я's bowl at a flat 0.44 of the cap while the stroke crossing it grew
five and a half times.

The recipe's own docstring said it read "where the bowl stops", and it did
not. A comment describing the intent is not evidence the code has it.

**Tell:** a figure read off a donor outline that was never checked at *both*
masters. A wrong read that is nearly right at the light master leaves no trace
there at all — the letter only comes apart at the heavy end, which reads as
"it deteriorates when bold" rather than as "this number is wrong".

**Fix:** read the figure at both masters and say what each one is in units
before using either. If the two differ by less than a stroke at Thin and more
than a stroke at ExtraBold, they are two different quantities.

Two smaller traps in the same act of reading a donor:

- **A fraction is a fraction *of* something, and the denominator decides even
  the sign of its trend.** в's lobe sweep, taken over the letter's WIDTH, fell
  from 0.494 to 0.410 and looked like a well-behaved figure narrowing with the
  weight. The same reach over the LOBE'S HEIGHT — which is what a corner
  radius actually competes with — rose from 0.57 to 0.65, because the letter
  widens while the sweep narrows. The fraction was right; what it multiplied
  was not. When a shape is squatter than the donor the fraction came from,
  a share of width stops meaning what it meant.
- **`Params.box` and any max over `path.nodes` include the OFF-CURVE points**,
  which for a bowl's corner sit outside the curve. B's inner contour reads 45
  units taller at ExtraBold than the outline it describes. Read on-curve nodes
  only, or flatten. This is F6 one step earlier — in the source rather than in
  a probe.

### F9 · A junction that cannot be unioned

Two contours laid over each other have to be unioned, and a union is only as
good as the angle at which the two boundaries cross. Where one stroke leaves
another **tangentially**, they do not cross — they run alongside each other,
and the union closes on a sliver no one drew.

б's stroke leaves its bowl along the bowl's own tangent, which is what makes
the two one figure rather than two shapes meeting at a seam. Built as a bowl
with a stroke over it, the union came out with a one-degree spike of ink at
the departure, where this face's own sharpest corner is 42 degrees. Four ways
of forcing the two apart were tried and each bought one artefact with another:
starting the stroke thin, sinking it bodily into the bowl (which crossed the
inner wall and bit a white wedge out of the counter), snapping its edges onto
the walls to coincide with them (two curves are only ever coincident to the
precision they were flattened at), and holding the inner edge back at the
counter (which then grazed *that*).

The heavy master hid it. At ExtraBold the wall is thicker than the stroke and
the two can be made to cross at 52 degrees or better; at Thin the wall and the
stroke are the same width and no arrangement of them gives a crossing this
face would draw.

**Tell:** an overlap whose crossing angle cannot be improved by moving the
overlap. If every parameter sweep returns the same sharpest angle, the angle
is not a parameter — it is the geometry.

**Fix:** stop unioning. Emit the letter as ONE contour, walked: round the
donor's own wall from where the outer edge leaves it to where the inner edge
does, out to the terminal and back. There is then no crossing to go wrong.
`_be_paths` in `recipes.py` is the worked example.

Two things the walk needs, and both were faults before they were fixed:

- **The walk closes on the point it started from**, so that point is written
  twice. Dropped, its two handles carry into the first node, which becomes the
  curve's endpoint rather than the start of a line.
- **Sample the donor's wall by ANGLE, not by arc length.** By arc length the
  two masters put their nodes in different places, so the interpolation ran
  between nodes that do not correspond: the letter kept its full overshoot at
  both ends of the axis and lost half of it in the middle, sitting 4 units
  below the baseline at Regular where this face sits 9 or 10. Node parity
  passed throughout — it counts nodes, it cannot see that they mean different
  things.

---

### F10 · A silhouette summarised instead of measured

A landmark — an apex, a terminal, a place where something "goes flat" — is a
scalar squeezed out of a curve, and the squeezing is where the error enters.
Three separate readings of б's top were taken this way and all three misled:

- an **apex band** at 0.71–0.85 of the width, read as the midpoint of a
  plateau. There is no plateau. The top edge climbs from the bowl to the
  terminal without a break, and the band was a summary of the climb. Built as
  a plateau it made a letter that read as the digit 6 — which this face's own
  6 also is, a bowl with a stroke rising to the right out of it.
- a **lean**, divided by the stem, which reported the spine leaning further
  right than the letter is wide. A lean is a share of the WIDTH; the stem got
  into it because the spine's weight was on the mind at the time. (F5.)
- a **flat point**, whose median sat at 0.71 of the width with quartiles from
  0.52 to 0.76 — a spread wide enough to mean the population was not
  describing one thing.

**Fix:** measure the silhouette as a PROFILE. The top of the ink at each x is
single valued; it needs no skeleton, no offsetting and no decision about which
stroke is which; and it is exactly what the eye reads as the letter's gesture.
That construction of б was later abandoned for a donor outline and the profile
table went with it, so there is nothing in `recipes.py` to look at now; what it
did was hold 21 samples across the letter, median over the 59 panel faces that
draw it, and **solve** the construction's two handles and its arrival angle
against them at build time rather than choosing them. The fit landed within
about 1% of the panel at every sample, at both masters.

That last point matters on its own: the handles are lengths in units of the
distance from the bowl to the terminal, and that distance is not the same
share of the two letters. Held as constants, one pair fitted the light cut
four times worse than its own. Solving beats a table of per-master numbers,
which is how a figure measured on one master gets carried onto another that
never earned it. (F1.)

### F11 · A donor's outline kept for the part the host already draws

An outline donor is a legitimate answer when the host has no counterpart to
build from. What it is not is a licence to keep the whole letter, because a
donor's outline carries the donor's own design language, and most of the
language sits in the round parts.

Sudo's б came across whole. It is a good б — for Sudo, whose bowls are rounded
rectangles: its counter fills 0.854 of its own box and so does its o's, which
is internal consistency, not a defect. Dropped into a face whose o fills 0.810,
the same outline read 0.845 and 0.851, and the eye saw it before any probe did
— a straight left wall with the branch meeting it at a corner, where every
other round letter in the face turns continuously.

Every mechanical gate passed. It had to: the letter was self-consistent,
correctly interpolated, correctly weighted, correctly fitted to the cell. What
was wrong was a relation to a letter the checks were not comparing it against.

**Tell:** a donated outline that includes a shape the host draws elsewhere —
a bowl, a shoulder, an arch, a counter. If the host has an o, the donor's o is
not needed and its presence is a fault waiting to be noticed.

**Fix:** cut the donor down to the part that is genuinely missing. б keeps
Sudo's branch and takes its bowl from this face's own o, squashed to the
donor's bowl height and spliced at the two points where the donor's outline
leaves the oval. A squash is affine, so the counter keeps o's fill *exactly* —
the target is met by construction rather than by fitting, which is the whole
reason to prefer this shape of fix over tuning the donor's curves.

**What would have caught it sooner:** asking the panel what б's bowl is *for
each face's own o* rather than in absolute terms. That reading is unanimous in
a way panel readings rarely are — 60 faces, median fill difference 0.001,
tenth to ninetieth percentile −0.014 to +0.014, width ratio median 1.00 — and
it says the bowl is not a design decision at all. See `bowls.py` in §4.

**The seam is its own fault, and it cost a second round.** Cutting the donor
down is half the job; the kept part then has to be re-seated onto a host shape
it was not drawn for, and the obvious way to do that is wrong. Sudo's underside
ends on Sudo's straight wall; ours has to end on an oval, so the end point
moves. Moving *only the end point* — with its handle, which keeps the tangent
and looks safe — drags the whole last segment straight: a stretch leaning 78
degrees stood up at 88 and ran parallel to the branch's own outer edge. What
that destroys is the FLARE, the widening where the stroke enters the bowl, and
the flare is the entire difference between a stroke that grew out of the bowl
and two strokes laid over each other. The user saw it immediately; every gate
passed; three separate probes said nothing was wrong. The aperture's opening
angle read 40 degrees against a panel median of 39. The wall's thickness at
the landing read 0.97 of the stem, identical to the rest of the bowl, against
a panel tenth percentile of 0.40. The corner's turn read *gentler* than the
panel median. All three were measuring real quantities, and none of them was
the one that had changed.

**Fix:** move the root RIGIDLY and fade the move out over the segments above
it. Then the geometry the donor drew at the seam survives intact and only the
part far enough away to be unnoticed absorbs the difference.

**Tell:** any re-seating where an end point moves and its neighbours do not.
Ask what the segment's *shape* was doing, not just where its ends were.

**And a second-order one, worth as much as the fix.** When the eye reports a
fault and the probes all come back clean, the probes are answering questions
that were not asked. Overlay the two outlines and look. It took one picture to
find what three panel comparisons missed, and it should have been the first
move rather than the fourth.

**A donor's axis buys shape, not weight — once it is only supplying a part.**
The third round on this letter was the branch reading nearly twice the weight
of the bowl it grows out of: 1.73 of the bowl's wall at Thin, against a panel
holding 0.85 to 0.99 taken nearest-neighbour by stem. The axis was still being
solved against the donor's own bowl wall, which had made sense while the bowl
was the donor's, and left the one part that survived the cut unmeasured.

Solving the axis against the branch instead does not work either, and the
reason generalises. This face's Thin is far lighter than the donor's lightest
cut — its bowl wall is a sixteenth of the x-height where the donor's lightest
is a tenth — so buying that weight off the axis means extrapolating a long way
past the end, and a glyph does not thin gracefully out there. Between t −0.8
and t −1.0 the branch's root fell from 1.30 to 0.74 while its terminal went to
a hairline: that is an outline coming apart, not a lighter one. §1's rule about
clamping a fit to the range it was fitted over applies to a donor's own axis
too.

**Fix:** clamp the axis to the donor's ends, one per master, and take the
weight from a separate lever — move the stroke's underside toward its outer
edge, each point by a share of *its own* distance across the stroke. A share,
not a fixed offset: this branch is twice as thick at its middle as at its
terminal, and taking a constant off both leaves the terminal a hairline while
the middle is still right. Weight first, at the face's own ratio, then shape —
which is what з already does to the digit three, in §8.

**And the measure has to survive the thing it measures.** Two gauges were
built for this stroke and both were wrong, in the same way and for the same
reason: each read the *model* of the glyph rather than the glyph.

- A **scanline with a slope correction** read a near-horizontal stroke at four
  times its weight, and barely moved when the stroke was thinned to a sliver,
  so a bisection against it ran to its bracket end and reported success.
- A **ray cast between the two contours** was better posed and still wrong. It
  said the branch had been thinned to 0.92 of the bowl's wall. Built, it
  measured 1.73. The gauge was telling the truth about the intermediate and
  the intermediate was not what shipped: a later step re-seated the branch's
  root onto the bowl by translating it, and after thinning, the root sat far
  enough away that the translation dragged the whole underside back out and
  undid the thinning exactly. Every number in between was correct. None of
  them was measured on the artefact.

**Fix, and it is a rule not a patch: measure the rendered glyph.**
`tools/weights.py` rasterises the letter, takes the exact Euclidean distance
from every ink pixel to the nearest non-ink pixel, and reads the stroke's
thickness as twice that — the largest disc that fits inside the ink at a point
IS the weight there, whatever direction the stroke runs, whatever contour it
came from, and after every transform the pipeline applies. It decides nothing
and so can be wrong about nothing. The same code renders the panel, which is
what makes ours and theirs the same quantity.

**Tell:** a solve whose target is computed anywhere other than the end of the
pipeline. If the number is taken before the last step that moves points, it is
a prediction, and a prediction is not a measurement however carefully it is
derived. Close the loop: bisect the lever against the finished artefact even
when that costs a rasterise per iteration. It costs seconds and it is the
difference between shipping 0.93 and shipping 1.73.

**What it cost:** three rounds on one stroke, each ending in a confident report
with a number in it, and each of those numbers wrong. The user caught all
three by eye.

**And then the instrument was validated, and most of it had not been real.**
`tools/weights.py --selftest` builds strokes whose width is true by
construction -- shapely buffers a centreline by half of it -- and asserts the
reading recovers them. It failed on its first run at +5 per cent: a pixel is
ink when its centre is inside the outline, so twice the distance to the
nearest non-ink pixel overstates a stroke by about one pixel. Nobody had ever
shown any of the four gauges a shape whose answer was known.

Two more faults surfaced in what the probe called "the branch". It took every
raster row above the counter's top, but the bowl's own crown sits above its
counter one wall thick -- 28 per cent of the kept rows at ExtraBold against a
trim of 12 -- so those rows reported the wall. And the top was the minimum
over EVERY enclosed region, while this letter encloses a single-pixel pocket
at the seam, so one pixel was deciding where the branch began.

Corrected, the branch had been within the panel for two rounds already. The
1.73 that three rounds were spent chasing was substantially the region, not
the letter. **A measurement that has not been checked against a known answer
is not evidence, and acting on it costs more than not measuring at all** --
because not measuring at least leaves the doubt visible.

**Rule, and it is cheap:** every probe that produces a number a decision rests
on gets a `--selftest` against ground truth. `audit.py` and `signature.py`
already had one; the pattern was there to copy and was not copied.

**A fourth, from the same root: an unmeasured word in a report is a guess.**
Having fixed the weight along the branch's body, the heel still read 1.41 of
the bowl's wall, and the report called that "the flare where it meets the
bowl, which is intended and normal." Nothing had measured it. Measured, the
panel does not flare a branch into its bowl at all: over 60 faces the weight
at the heel is 0.89 of the bowl's wall against 0.86 along the body, flat
within the noise, ninetieth percentile 0.98. The flare was four points of the
underside deliberately exempted from the thinning to protect something that
does not exist. Removing the exemption put the whole profile inside the panel
— 0.81, 0.89, 0.98, 0.98 from terminal to heel at Thin.

The general form: **any word in a report that names a design intention is a
claim, and a claim needs a measurement.** "Intended", "normal", "as expected",
"that's the flare" — each is a place where a number should be. The panel can
answer almost all of them, cheaply, and it disagrees more often than not.

**A fifth, and it is the one that ended the letter: two fixes holding each
other up are one decision, and neither can be judged alone.** After all of the
above, the junction still carried a blob — the widest disc anywhere in the
letter read 2.47 of the bowl's wall at Thin and 1.52 at Regular, against a
panel of 62 faces holding p10 1.06, median 1.24, p90 1.39. Both masters had
looked settled for two rounds because Bold and ExtraBold were inside at 1.33
and 1.29 and nobody had read the weights in between.

The two parts, each with its own recorded reason and each defensible:

- the splice **translated** the underside's end point onto the oval, because
  the underside has to end on the bowl and, drawn for a straight wall, it does
  not;
- the reweight therefore **exempted** that end point from the thinning,
  because the translation would drag it straight back out and undo the
  thinning exactly — which had been measured, and was true.

Together they say: the last stretch of the branch keeps the donor's own
weight. At ExtraBold the donor needs no thinning at all and that costs
nothing. At Thin the stroke is cut to 0.33 of what the donor drew and the
exempt stretch is therefore three times too heavy — sitting exactly in the
corner where the two strokes meet. The fault scaled with (1 − k), which is
why it read 2.44 at Thin and 1.28 at ExtraBold, and why every fix aimed at
the *junction* missed: nothing was wrong with the junction.

A sweep of the landing angle had already reported that no angle satisfies both
the mass and the branch's thinnest point, and that conclusion was correct.
It was also useless, because the landing angle was not the lever — moving it
only dragged the same unthinned root somewhere else.

**Fix: remove both at once, and replace them with a construction rather than a
correction.** Thin the stroke through to its end, exempting nothing; then let
the underside simply run on along its own tangent until it reaches the oval,
and splice there. Nothing is translated, so nothing needs exempting, and the
tangent is the donor's own, so the angle the stroke enters the bowl at is
preserved exactly — which is what the rigid-root-plus-fade was built to
protect in the first place. **Where it lands is then not chosen at all.** It
falls out of the geometry, at 152 degrees round the bowl at Thin and 111 at
ExtraBold: the lighter the stroke, the lower it meets the bowl, which is what
the panel draws. The mass went to 1.40, 1.30, 1.30, 1.31 across the four
weights — flat, where before it swung by a factor of two.

**Tell:** a constant whose justification names another part of the
construction instead of a measurement. "Nothing moves here, because the next
step would drag it back" is not a fact about the letter; it is a fact about
the pipeline, and it means the two steps are one decision wearing two hats.
Judge them together or replace them together.

**Corollary, and it is a new hazard the fix introduced:** a landing solved per
master can fall in a *different segment* of the host contour at each, and the
arc is rotated to start there — so the two masters would carry the same node
COUNT with node five meaning a different place on the bowl. Every mechanical
check passes and every interpolated weight is nonsense. Ours land 41 degrees
apart and, as it happens, in the same segment; `be_from_sudo.py` now asserts
it rather than relying on it. §8's "node parity says nothing about size" has a
sibling: **node parity says nothing about correspondence either.**

**What would have caught it sooner:** drawing the disc. `seam.py` reported the
mass *and* its position, which was already the fix for an earlier round's "a
right number in the wrong place" — and it still was not enough, because the
position was two fractions of the counter's box and the question was which two
edges the disc was touching. `tools/blob.py` draws the largest inscribed disc
on the glyph it was measured in and marks the two boundaries it rests against,
ours beside the panel's at one scale. The blob's contacts were the bowl's
outer edge and the aperture's tip, which is where they are in every panel face
too — so the junction's *shape* was never the fault, only the ink between
those two edges. One picture, again, and again it should have been first.

---

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
| `harmony.py` | the bowl family read as a family — reach, wall, counter, each against our own median *and* the panel | no |
| `weights.py` | stroke weight off the RENDERED glyph -- distance transform, ours and the panel through one lens | no |
| `bowls.py` | a bowl's counter against the face's own o -- fill, width, height, bucketed by stem | no |
| `seam.py` | б's junction at **all four** weights without a build, by blending the two masters; `--check` proves the blend against the built fonts | no |
| `relations.py` | §2's four relations — width/adv, counter aspect, counter/stem, solid band — over every drawn glyph at all four weights, each as a multiple of the face's own Latin. `--selftest` against shapes of known answer; `--calibrate` prints the host's own departures, which ARE the bar | no |
| `blob.py` | the same disc, drawn on the glyph with the two edges it touches marked, ours beside the panel at one scale | — |
| `be_sheet.py` | б in company, in words, and at 12px and 14px, from the built fonts | — |
| `signature.py` | how a stroke ends and how heavy a horizontal is, against the Latin's own answers | yes |
| `signature.py --selftest` | the same two readings over the Latin itself — must stay clean | yes |
| `signature_sheet.py` | the picture that goes with it: each reading beside the Latin it was measured against | — |
| `diagonals.py` | Ж and ж's centre stem against an arm, and the face's own X V W K Y measured **perpendicular** to the stroke | no |
| `params.py` | per-master figures measured off the Latin | — |
| `latin_metrics.py` | what the Latin says about the face | — |
| `preview.py` | rasterise from recipes without a build | — |
| `checkpoint.py` | the review sheet | — |
| `classify.py` | the tier table — what is derived, and from what | — |
| `geom.py` | outline algebra over Glyphs paths (22 primitives) | — |
| `build_cyrillic.py` | writes recipes into the Glyphs source; `--rebuild` drops and redraws | — |

`verify.sh` runs all seven gates in order and exits non-zero on any failure.
`review.sh` regenerates **every** review image from the current build — use it
rather than rendering one sheet, because reviewing an image made before the
last fix wastes a round.

Only `probe.py` reads built fonts and the panel through one lens, which is what
makes "ours" and "theirs" the same quantity. Everything above it reads the
source, one master at a time — except `signature.py`, which reads the source
for terminals, where a real node is the only place a stroke's end exists, and
the build for horizontals, where a scanline needs the overlaps removed.

### A gate's known exceptions are pinned, not waved through — *`tools/signature.py: ACCEPTED`*

A gate with exceptions in it decays in one of two directions. Exempt a letter
by name and it stops being measured, so the next real drift in it passes
silently. Leave the finding standing and the gate is red on purpose, which is
the same as having no gate — nobody reads a report that always says the same
thing.

`ACCEPTED` does neither: it records the letter, the weight and **the figure it
was accepted at**. A reading within two points of that figure is quiet; в
drifting to 0.80 fails exactly as a new letter would. And an entry that stops
firing is itself a finding, because a table nobody prunes goes on excusing a
reading that is not there any more, and the next real drift in that letter is
waved through under an obsolete figure.

Every entry is a marginal already recorded in `docs/APPROVALS.md`. The two
records are the same fact for the same reason — see §6.

### Ask a reading twice — *`tools/harmony.py`*

A letter's reading means two different things depending on what it is compared
against, and a whole class of faults is invisible unless both are asked:

- **against the rest of our own family** — does this letter sit in the row?
- **against the panel's own copy of that letter** — is the row in the right
  place?

A letter can be an outlier in the family and still be right, because that is
what the letter is: Ю and Ф sit 15% under the family's wall because they
carry a stroke through the bowl, and the panel agrees with them. And every
letter can sit comfortably in a family that is uniformly wrong. Ъ needed both
answers — it was an outlier *and* outside the panel, which is what separated
it from Ю.

### Write the script so it can be run again — *prose only*

Every probe in the table above gets run dozens of times: once to ask the
question, again after each fix, again at the next glyph that touches the same
relation. A probe that takes minutes is a probe that stops being run, and a
question that stops being asked gets answered by guessing. The machine is also
short of memory — a `make build` has been OOM-killed mid-run — so a script
that slurps where it could stream costs more than its own runtime.

So efficiency here is not tidiness, it is whether the instrument survives.
Four rules, each of which has already cost a round:

- **Open the expensive thing once, and loop it on the outside.** A sweep over
  the panel loops fonts outer and letters inner. Written the other way round —
  a full pass over sixty faces per letter — `harmony.py` opened and parsed
  each face thirty-one times and took minutes instead of seconds.
- **Hoist everything that does not vary with the inner loop.** The cmap, the
  glyph set and both stems are built once per face in `read_all`, not once per
  letter. They are the same object every time; deriving them again is the
  whole cost of the letter.
- **Coarse, then fine.** Find a scanline extremum with a coarse sweep plus a
  short fine pass around the winner, not a fine sweep throughout — every
  scanline walks the whole flattened outline, so the step count is the price.
  48 then 12 reads the same extremum as a flat 240 for a quarter of the work.
- **Stream, and close what you opened.** `TTFont(..., lazy=True)` inside a
  `try/finally` that closes it. Sixty faces held open at once is sixty parsed
  font tables resident for no reason.

The test before writing a loop: **how many times does this open a file, and
does anything inside it depend on the loop variable?** Both answers are
usually visible without running anything.

---

## 5 · Rendering for review

Every report is a picture. Text-only progress is useless when review is by
eye rather than by number — the render *is* the finding, and a bad render
wastes the round.

### Quality is not optional — *prose only*

A sheet was shipped this session with hard-aliased edges because the outlines
were filled into **1-bit masks**. Every edge was thresholded, nothing was
antialiased, and the user's response was that it was unreadable. The
requirements:

- **Supersample ×4, then downsample with Lanczos — to *twice* the layout, not
  to the layout.** Fill into an oversized mask and resize; never draw at
  final size. Downsampling all the way to 1 gives away the resolution the
  render already paid for and the sheet pixelates the moment it is zoomed,
  which is what a review sheet is for. Two samples per delivered pixel is as
  much antialiasing as a screen at this density shows. `preview.py` was worse
  than that — it drew 1-bit masks straight at the delivered size, so its edges
  were a hard staircase with no grey in them at all.
- **A reading-size row is the exception and must not be enlarged.** 14px set
  at 28px is a different rasterization — different hinting, a different
  stem-to-pixel fit — and that fit is the whole point of the row. Draw those
  at their true pixel size and enlarge afterwards with **nearest-neighbour**,
  so one rendered pixel becomes one block and the row stays an honest picture
  of what the rasterizer produced. `checkpoint.py: line_block(real=True)`.
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
6. **Write down what the round taught** — into this file, before starting the
   next glyph. See below.

After **any** change to a glyph, however small, the preview is regenerated and
shown again. The user judges from the picture, so a stale picture is a false
report.

### Why the ledger exists

`docs/APPROVALS.md` is the record of what has been approved and therefore what
is frozen. Without it the rule "never change an approved glyph" is
unenforceable — the question "is this one approved?" has been reached with no
way to answer it, after a glyph had already been changed twice without anyone
noticing it was frozen.

An approved glyph is frozen. A panel median is not evidence against it; if it
genuinely must change, say so and ask first. When a new sibling should match an
approved one, **copy the approved construction** rather than generalising it
into a shared helper and re-deriving it — that is precisely how ґ's work
destroyed Ґ's.

### Step 6 — what the round taught, into this file

**A glyph is finished when what it taught is written down, not when it is
approved.** Do it while the measurements are still on screen; a day later only
the conclusion survives, and the conclusion without the numbers behind it is
the kind of note nobody trusts enough to act on.

Every entry in this document exists because it was written at this point in
some earlier round, and every one of them has since saved a round:

| written after | saved |
| --- | --- |
| ф's weight fits (§2) | Ф, drawn from the same three relations, first try |
| the stem trap (F5) | о, which would otherwise have been "fixed" |
| Я's donor fault (F8) | every remaining letter that reads a figure off a donor |
| the diagonal rule (§8) | к, ж, у, х, џ — all still to be drawn |

Where things go:

- a **fault** → §3, as an instance of an existing class or as a new one
- a **relation between parts** → §2
- a **settled question** → §8, and take the thread out of §9
- a **new instrument** → §4, and if a probe was fixed, stop listing it as broken
- **what would have caught it sooner** → `CLAUDE.md`, which is the short list
  read before touching anything

Write the class, not the letter. "Я's bowl floor was wrong" helps nobody; "a
donor holds two figures that coincide at the light master" is what stops the
next glyph making the same mistake in a different place. And keep the numbers
— the readings, both masters, and the panel band they were compared against.
A finding stated without them cannot be re-checked, and everything in this
document has to survive being doubted.

The test of whether a line is worth writing: **would it change what the next
glyph does?** If not, leave it out. This file is read in full at the start of
every round and its length is a cost.

Two things the ledger has to carry that are easy to leave out:

- **Approval does not cross the case pair**, even when both cases come out of
  one recipe. Я and я were shown together and share all three of their
  constructions; я was approved on its own and the capital had no verdict for
  another round. Record the case that was named and no other.
- **Record what was still outside the panel when the glyph was approved.** я
  was frozen with three readings marginally out at the heavy end. Written down
  they are a decision; left out, the next measuring pass finds them, reports
  them as a defect, and changes a frozen glyph to chase them.

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

### о is not an outlier — the face is narrow, and its lowercase is lighter

о underlies every round letter, so "о does not follow the panel's weight
relation" was carried as the highest-value open thread. Measured, it is not a
thread at all, and both halves of it were the probe:

- **The bowl is not light.** о's side wall measured 0.93 of the stem where the
  panel holds 1.00 — but that stem was H's. Against **n's** stem it is 1.000,
  1.000, 1.008, 1.000 at the four weights: о is monolinear with the lowercase
  it stands in, exactly. What is genuinely unlike the panel is face-wide and
  not о's: this face draws n at **0.93–0.94 of H** where the panel's median is
  **0.98**. Every lowercase reading taken against the capital stem inherits
  that. See F5.
- **The bowl is not narrow *for this face*.** At Thin о fills 0.675 of its
  advance against a panel 0.683–0.771 — low, but so is everything: c 0.628,
  e 0.641, n 0.612, u, v, x all below the band, and **c and e sit further
  below it than о does**. SUSE Mono is a narrow face and о is narrow with its
  own family. The ф-bowl-to-о ratio of 1.205 at Thin was ф's width taken from
  the panel's *absolute* figure while о kept the face's own.

The lesson generalises to every letter still to be drawn: **take a width as a
ratio to the face's own counterpart, never as an absolute share of the advance
read off the panel.** The panel says which relation holds; the host says what
the value is, and on width this host is 9% away from the panel at Thin.

The pairwise form of that test is the one to reach for. Я reads 0.803 of its
advance at ExtraBold against a panel band starting at 0.828 — outside, and
meaningless on its own. Against В, which is the letter it shares a bowl with,
Я is 1.010 where the panel is 1.014. The letter is right and the face is
narrow. **A width that is outside the panel is a finding only if the letter it
should be measured against is inside it.**

Checked at the same time, against n's stem: о, е, ь and ъ draw their bowl at
the full lowercase stem; ы and ф take a deliberate reduction. с, э, з and ю
cannot be read this way at all — they are open, so the widest scanline's first
run is a terminal or the stem, not a wall (F6).

**And a corollary that reads a flag off the sheet.** б was added to
`harmony.py`'s letter set after it was approved — it had never been in it, so
the family reading had never been asked about the one letter whose bowl is
literally о's. Asked, it answers that б is **identical to о on all three
readings at all four weights**, to three decimals: reach 0.838 / 0.880 / 0.923
/ 0.937, wall 1.000 / 1.000 / 1.008 / 1.000, white 11.97 / 3.62 / 1.83 / 1.49.
It is not similar to о; it is о, which is what the construction says it should
be and what nothing had yet checked.

The instructive part is the one `!` it carries. At Regular б's reach is outside
the panel's own **б** bracket, 0.880 against 0.882–0.920. At Thin the same
reading is outside the panel's own **о** bracket, 0.838 against 0.842–0.895 —
and б, at the identical 0.838, is inside, because the panel draws б a shade
narrower than о and its bracket starts lower. One value, two letters, two
brackets two thousandths apart, and which letter gets flagged depends on the
master. **A flag that moves between two letters drawn from one outline is a
fact about the brackets, not about either letter** — the same shape as the
pairwise test above, and the reason to reach for it before touching anything.

### The set covers Belarusian as well as Ukrainian and Russian

Asked and measured on the built fonts rather than inferred from the tier
table, because the question comes up and the answer is cheap: all **64**
Belarusian letters are in the cmap at all four weights, along with both
apostrophes — U+2019 and U+0027, which the orthography needs for *сям'я* and
*аб'ект* — and Ґ ґ, so Taraškievica is covered too. Nothing is missing. И, Щ
and Ъ are present and simply unused by Belarusian.

The letter that carries the language is **Ў ў**, and the two cases do not
share a base: **ў is the Latin y plus a breve**, since Cyrillic у is a tier-1
donor of y, while **Ў is the drawn Cyrillic У plus a case-height breve**. Both
are `base + mark` composites, so `audit.py`'s composite rule already gates
them — the mark must clear its base and sit within 12 units of the advance's
centre — and both pass at every weight. At 12px the breve is a single pixel
but it does separate ў from у.

**Ў ў, І і and Ё ё are drawn and gate-clean but have never been reviewed.**
Coverage is not approval, and the Belarusian-specific letter is one of the
letters nobody has looked at.

### A family is read as a family, and the outliers are not all faults

Reading the bowl letters together — `tools/harmony.py`, §4 — the family turned
out to be in good order on the two things that carry across a line of text.
Walls hold 1.00 to 1.04 of the stem for every letter in both cases. Reach
splits into exactly two groups, the B-group at 557 and the O-group at 571,
which is the host's own split and not a drift. Э and э agree with С and с to
a unit.

The letters that stand outside the family are worth naming, because three of
the four are correct:

- **Ю Ф ю ф** sit 13–17% under the family's wall. They carry a stroke through
  the bowl, so a scanline crosses three strokes where the others cross two,
  and the panel agrees with them at every weight. Right.
- **С с Э э** reach 0.86–0.88 of the advance against the family's 0.93. An
  open letter has no far wall to reach with. Right, and the Latin C reads the
  same.
- **Я я** reach short for the same reason on the other side. Right.
- **Ъ ъ** were outside the family *and* outside the panel. Wrong, and the
  only one of the four that was.

That is the whole argument for asking each reading twice.

### A diagonal is solved over its donor's run, not over the gap it sits in

Я's leg lands on the letter's left edge at the baseline and springs from under
the bowl. Solved over the bowl's depth — the gap it visibly occupies — it
reached the same foot through a third less rise than R's leg does, so it stood
nearer the stem the whole way down and closed the wedge of white to 0.26 of a
stem where this face's own R holds 0.63.

R's leg does not start at R's bowl's floor either; it starts inside it. The
run that fixes a diagonal's slope is **the donor's own run**, and the drawn
stroke then simply ends wherever the letter it grows out of happens to be.
Solving it that way also removes the hand-set overshoot that used to keep the
two outlines from sharing an edge exactly: the leg ends inside the bowl by the
donor's own margin, at both masters, so there is nothing to drift.

This applies to every diagonal still to be assembled — к, ж, у, х and the
Serbian џ all put a stroke across a gap that is not the stroke's own run.

### Ask whether the Latin already draws the letter, before drawing it

к was listed for three rounds as "drawn at lowercase weight" — a tier-3 job,
the whole letter to be built from К's proportions at x-height. It is not. The
face's own **k** has its arm and leg entirely below the x-height, at the
lowercase stroke, fitted to this cell; the only thing that makes it a Latin
letter is that its stem carries on up to the ascender. Cut that and the
outline *is* к. Nothing was drawn — the stem became a rectangle to the
x-height and the other two contours were taken unchanged.

The panel confirmed it rather than merely permitting it: over the 51 faces
that draw both, к is **1.000** of k's width with the middle half of the
population inside a thousandth, its left edge sits at the same place to the
em, and its leg leans the same. That is not a family resemblance, it is the
same drawing.

**So the first question for any undrawn letter is which case of the Latin to
look in.** The capital is the obvious place and it is often the wrong one:
К at x-height would have meant inventing slopes, a junction and a spring
height, all of which k already answers. Of what is left, з and м have no
lowercase counterpart — Latin m is three arches and there is no Latin three —
so those two really are their capitals' constructions at x-height. к was the
one that was not, and it was the one being planned as though it were.

**б was the second, and it was worse**, because б had been written down as the
letter with no Latin of its shape and that sentence went unchallenged for four
rounds. It is **b**: same left edge, same right edge, same bowl top, over the 50
faces that draw both. The only difference is that b's stem stops at the ascender
and б's turns right — and the face draws that turn too, in **g's tail**, which
is the same figure upside down. Nothing was drawn but the splice. See *A width
equality is not a shape identity* for how the wrong answer held for so long.

### One reference face is a population of one

`ZHE_STEM` was read off JetBrains Mono at two weights and set to 0.86 — the
centre stem of Ж drawn lighter than its arms, because it is "the one stroke
pressed on from both sides". The reading was right about JetBrains: measured
again here it runs 0.95 at Thin down to 0.87 at ExtraBold. But across the 49
panel faces that draw Ж the ratio is **flat at 1.00**, and JetBrains sits near
the bottom of that population. So the constant generalised one face's habit,
and the direction — falling with weight — was taken from an outlier too.

The face agreed with the panel and not with the donor: it does not lighten a
diagonal at all, its X running 0.97 to 1.02 of H's stem at every weight. So
there was no reason for the single upright in Ж to be the lightest thing in
it, and `strokes.py` had been saying so all along — Ж and ж were the furthest
from the panel's median of anything drawn here.

**Rule: a constant read off one face is a hypothesis, not a measurement.** It
is the same fault ф was found by, one step earlier: there the panel was
consulted but not bucketed, here it was not consulted at all. Bucket the panel
before believing a figure, *and* count how many faces answered.

### The face ends a stroke two ways, and the side is not one of them

Measured over its own alphabet and digits, both cases, both masters: **213 of
its 242 terminals are cut at exactly 0 or 90 degrees**, and every exception is
a diagonal's end — the letters that have no square way to stop. An oblique
terminal is therefore not forbidden, it is *earned by a diagonal*. And the
ceiling is exact rather than approximate: **no chamfer in the face exceeds 45
degrees**, at either master, in either case.

Which side it faces is not part of the answer. The lowercase chamfers where
its capital does not — c does and C does not, э does and Э does not, and the
two pairs agree with each other — so a chamfer appearing on the side a letter
opens on is the face's own treatment, not a mirrored one.

All forty-five glyphs this project draws pass this at both masters.

### The lowercase horizontal is a different stroke from the capital's

The face draws 106 units at ExtraBold where its capitals draw 135, and the two
are the same 28 at Thin. So the relation is not a ratio to carry — it is two
separate measurements, `bar` from H's crossbar and `lcBar` from t's, and
`params.py` reads them apart for that reason.

Against those two figures, **every Latin letter that carries a horizontal sits
between 0.89 and 1.12 of its own case's bar**, across four weights. That range
is tight enough to be a usable bracket without picking a tolerance, and three
drawn letters sit outside it, each for a reason the drawing already gives: в
takes B's own falling figures, Ы and ы are shaved because three strokes have
to fit across one cell, and Ф and ф miss by a unit at Thin.

### A corner census across every case pair cannot be made honest

"A lowercase turn is never tighter than its capital's" is the most
characteristic item on the list, and asking it of every pair rather than the
six in `audit.py` looks like free coverage. It is not. `corner_set` cannot
tell a corner from a bowl, and a bowl is genuinely a different size in the two
cases — O sweeps 361 where o sweeps 140 and 261 — so the check reports ten of
the face's own pairs. Separating the two needs a cutoff between "corner" and
"bowl" that the face does not state anywhere.

The six pairs in `audit.py` are the six whose letters are made of corners.
That is why they are the six, and the list should not be grown without a
figure the face itself supplies.

### A probe that walks in from an edge finds the edge

б was rejected by eye three times, and the second rejection was caused by a
probe, not by the drawing.

The question was where б's flag begins. The probe walked **down from the top**
looking for the first run narrow enough to be the rise alone, and called that
the rise's arrival. On a flag whose top is rounded — which is most of them —
the first narrow run going down is the **flag's own tip**, far to the right. So
it reported the panel's rise arriving at 0.72 of the width and its flag running
0.21, and ours arriving at 0.59 with a flag of 0.32.

Both numbers said ours had the *longer* flag while every render said the
opposite, and the letter was rebuilt on the strength of them. Measured properly
— the widest single run above the bowl, which is the flag by construction — the
panel's flag begins at **0.35** of the width falling to **0.16**, and runs
**0.51 to 0.76**. Ours began at 0.55 and ran 0.37. Half the flag was missing,
which is exactly what the eye had said.

**Tell: a probe that scans in from an edge stops at the first thing it meets,
and near an edge that is usually a terminal, a tip or an overshoot rather than
the feature.** Scan the whole range and take the extremum instead — the widest
run, the longest span — which cannot be fooled by what happens to be nearest.

**Second tell, and it is the one that should have fired first: the numbers
disagreed with the picture.** When a measurement says a letter is fine and the
render says it is not, the measurement is the thing to re-derive. It was
treated as the tiebreaker for a whole round.

### A width equality is not a shape identity

**This one cost three rejections, and the sentence that caused it read like a
measurement.** б's bowl is 1.000 of о's width over the 50 panel faces, middle
half 0.988 to 1.000 — the tightest reading anywhere in the letter. That was
written down as *the bowl is о*, and three versions of б were built by cloning
о and laying a stroke against its left flank. Every one was rejected by eye.

The equality is real and says nothing about the bowl. б is as wide as о because
**b's stem plus b's bowl is as wide as о** — a fact about the cell, which every
letter in a monospace shares. Asked the question it was actually being used to
answer, the same panel answers plainly: б's left edge is **b's left edge** (off
by 0.18 of a lowercase stem, and to the left), its right edge is **b's right
edge** (0.000, middle half −0.017 to +0.008 of о's width), and its bowl's top is
**b's bowl's top** to within a twentieth of the x-height. Laid over each other
the two letters are one drawing with one difference: b's stem stops at the
ascender and б's turns right.

**Tell: a scalar that agrees to a thousandth is evidence about that scalar, not
about the shape.** Two letters can share a width and share nothing else. The
check that closes the gap costs one picture — draw the candidate donor under
the reference outline and look at where it shows. Three rounds went on solving
leans and radii for a junction the letter does not have, because that picture
was never made.

**And the fourth round found the same class one level down.** Knowing the
letter is b, its top was built as a flat flag on the ascender — which put the
letter's **highest point at 0.14 of its width where every one of the 50 panel
faces puts it between 0.71 and 0.85**, and ran flat over 0.87 of the branch
against a panel 0.09 to 0.29. Every scalar the letter had been checked against
was fine; the silhouette read as a bracket. The literature says it in one line
— Type Journal: the branch makes *"one strict movement to the right and
upwards"* — and so does a single measure, **where across its own width the
letter is tallest**. A letter has a small number of such shape-level
questions, and they are cheap: ask where the extremes are before measuring
anything between them.

That article also settles which of the two constructions a face should use,
and it is not a matter of taste: *"a letter o with a branch attached to it"*
versus *"the bowl and branch have a common spine"*, decided by **the joint the
face's own ovals already make with its verticals**. This one joins b, d, p and
q rigidly, so б is the spine construction. The panel measurement and the rule
agree, which is the only reason to trust either.

So this is the second time §8's *ask whether the Latin already draws the letter*
has paid, and the second time it was reached only after the letter had been
drawn the hard way. к was planned for three rounds as К at x-height; б was
planned for four as о with a stroke on it. **Both questions should be asked
before the first constant is read**, and asked of the lowercase first.

What survives from the three wrong versions, because neither is about б:

- **A junction transfers as a rule, not as a position.** The six's rise crosses
  its own bowl's top at 0.239 of that bowl's width at Thin and 0.287 at
  ExtraBold; carried to о as a *position* it put the stroke outside the bowl on
  one side and drove it down through the counter on the other, filling it solid.
  Read as a rule — the six's rise has no offset at all, its left edge **is** its
  bowl's left edge to within a unit over the upper half at both masters — it
  transfers to any bowl. A fraction of a width is a coordinate wearing a ratio's
  clothes.
- **Tangency, where a letter does need it, is slope-matched and gives a stretch
  rather than a point.** Tangent at the bowl's *widest* makes the stroke touch at
  the waist and cut clean across the counter above it. And below where the two
  edges part company the wall turns toward the vertical while the stroke keeps
  its slope, so a stroke taken down to the widest hangs a spur outside the
  silhouette at both masters. Walk the stretch and stop at its end.

### A clone inherits the donor's *set*, not only its shape — and a control pair says which is which

З is the face's own digit three, and the question "is a three really a good З"
turned out to have two separate answers.

**The shape: yes, and there is a real test.** Over the 51 panel faces that draw
both, the two letters put their lobes in the same proportion — 0.928 upper to
lower for З, 0.926 for the three, middle halves overlapping — and end their
strokes at the same angles. The one construction that would disqualify a three
is the **flat-topped** one, drawn with a straight diagonal shoulder instead of
a round upper bowl: **13 of the 51 faces draw that, and no Cyrillic З in the
panel does.** This face's three is not one of them — its upper terminal leans
1.97 at Thin and 2.21 at ExtraBold, inside a З population holding 1.61 to 2.02
and nowhere near the flat-topped three's zero. So the borrowing is sound, and
now provably rather than by assertion.

**The width: no.** Half the panel draws З wider than its own three, which looks
like a З-specific figure to reproduce. **It is not, and the control says so.**
Divide each face's З/3 by its own **O/0** — two letters nobody claims are
different drawings — and the median is exactly **1.000**, middle half 0.972 to
1.025. The whole gap is the digit set being drawn narrow, and it says nothing
about З at all.

But it says a great deal about the clone, because this face draws its digits
narrow *and widens them less with weight than its round letters*: 13 per cent
from Thin to ExtraBold against the capitals' 18. Cloned whole, З came out at
**0.937 of O** at ExtraBold against a panel bucket holding 0.974 to 1.007, and
з at 0.925 of o against 0.933 to 1.022. One cause, both cases, the heavy end
only — invisible at Thin, where the two happen to agree.

**So a cloned donor carries every decision that was made about the donor's own
set, not only the drawing.** A digit brings the digit set's width policy; a
capital brings the capital's. Ask what family the donor belongs to and whether
that family's rules are the recipient's rules, and check it **at both masters**
— this one is exactly right at Thin and four per cent out at ExtraBold.

The fix is not a redraw. The outline stays the three's and the width becomes
the face's own O's, `squash_x` putting the difference into the whites and
leaving the wall alone. `ZE_ROUND` — 0.9814 for the capital against O, 0.9829
for the lowercase against o. Both are flat: fitted as a line in the stem the
slope is nothing, and the two agreeing to two parts in a thousand across the
case is the panel saying this is one figure rather than two.

**The general instrument is the control pair.** When the panel appears to say
that A relates to B in some particular way, find the pair in the same two
families that nobody disputes and divide by it. Whatever survives is about A
and B; whatever cancels was about the families. It cost one probe here and
overturned the reading.

### Bringing a capital down to the lowercase takes both axes, and the same trick on each

`squash` — compress cap-height artwork without thinning the horizontal bars —
was written early and then sat unused for the whole project, because every
letter that needed it turned out to have a lowercase donor or a parametric
recipe. з is the one that does not: З **is** the face's own digit three, there
is no lowercase three, there is no Latin lowercase of that shape at all, and
the parametric route is the one thing already known to fail here — built from
generated arcs the capital had a visible seam where the lobes met.

What the letter then showed is that one axis is never enough, and neither is
one factor per axis. This face makes the two cases differ in *different things
at different weights*: at Thin the strokes are shared exactly, 29 and 29, 28
and 28, and the box differs most, the lowercase being 0.884 of the capital's;
at ExtraBold the box has nearly closed at 0.956 and it is the strokes that
differ, 150 against 161 and 106 against 135. So on each axis the stroke and
the size want different factors, and each axis takes two stages: **the weight
first, at the face's own ratio, then the size, with the stroke already correct
and pinned so the second stage cannot touch it.**

Horizontally that needed `squash_x`, which is `squash` turned on its side and
is new. A plain horizontal scale thins the vertical walls exactly the way a
plain vertical scale thins the horizontal bars, and a letter derived from a
wider donor has both faults at once.

The face's own o confirms the shape of it rather than merely permitting it: o
is not an affine of O. A plain scale of O would give it a crown of 96 and a
wall of 159; o's are 111 and 150. Its crown thins *less* than its height and
its wall thins *more* than its width — which is the two squashes, one per
axis, in the face's own hand.

### A constraint that forces a trade-off is usually a missing figure

м cost four rounds, and three of them were spent trading two readings against
each other that never actually conflicted.

The readings: **м's upright against n is 1.000 of М's against H**, middle half
inside 0.979 to 1.035, as tight as anything in this project. **м's vertex
against its own x-height is 0.639 of М's against its own cap**, middle half
0.308 to 0.889 — loose enough to rule out the extremes and fix nothing else.
Held together they appeared impossible: the letter is monospaced at М's width
and cannot widen, so at the panel's vertex with the panel's upright the wedge
between diagonal and upright shut to six units at Bold. Every round after that
was an argument about which reading to bend, and each answer was rejected —
`crowd3` on the uprights starved them (F3), the baseline read as standing on a
point, М's own vertex fraction left the letter shallow.

None of it was the trade-off it looked like. **The diagonal was leaving the
upright in the wrong place.** It was centred on the upright's centre, which
put a step on *both* sides of every stem at the x-height — poking a unit past
the outer edge at the light end, sinking inside it at the heavy end. М does
not do that: it sets the diagonal's outer top corner *inside* the upright, so
the outer edge runs clean to the top and the junction opens only inward, on
the side the stroke is going. That figure is 0.306 of the upright at Thin and
0.727 at ExtraBold, and it cannot be read with a scanline — at the top the two
shapes are one run and the corner is buried. It comes off М's own centreline
run up to the cap line.

With the junction right, the wedge at the panel's own vertex went from six
units to forty-two at Bold, and every reading fits at once with room to spare.

**So when two sourced figures cannot both be had, look for the third figure
that was never read before deciding which of the two to give up.** The tell is
that the trade-off is steep — a few per cent of one reading costing tens of
per cent of the other — which is what a geometry fault looks like from inside
a parameter sweep. The user saw it in one glance: *the V does not start from
the top of the vertical bars.*

---

## 9 · Open threads

- **`shoulder_spine` (`recipes.py:1304`)** still carries the F2 subtraction.
- **Three broken probes**: `HARD_SHOULDER`, `ZHE_STEM`, `YU_GAP` (the last two
  return too few faces to judge — Ж's diagonals and ю's join give variable run
  counts at a fixed height).
- **`checkpoint.py`'s red silhouette row** misreports ascender-to-descender
  letters.
- **Д and д's LEAN — the open half of the counter, measured but untried.**
  `relations.py` found the counter closing monotonically with weight, 39 per
  cent under the panel by ExtraBold and nothing wrong at Thin. The legs were
  half of it and are fixed and approved (2026-08-10). The counter is still
  narrow, and `de.py` says why: ours leans harder than the panel at **all
  eight** readings — 0.182 against 0.122 for the capital at ExtraBold, 0.240
  against 0.191 for the lowercase — and the panel straightens its Д as it gets
  bolder where ours holds its slant. The slant is a lever on the counter's
  width that does **not** move the letter's width, which is what makes it the
  right next attempt: widening the body and plinth was tried on 2026-08-09 and
  rejected by eye, and the letter is approved at its current width
  deliberately. Д's body is Л and л is approved with its own lean chosen for
  its own reasons, but Д is not Л — it stands on a plinth, and `El()` already
  lets Д set its span independently, so the same door is open for its slant
  with nothing about л moving. **Д and д are now approved, so this needs a
  fresh verdict before anything changes.**
- **Ь and Б's counters** read just outside the panel at Bold and ExtraBold —
  0.901 and 0.938 of a stem — where В, which shares the same `soft_bowl`, is
  inside at 0.951. Eight units. `relations.py` independently reaches the same
  letters from a different reading and adds **Ы** to them, so it is a family
  and not two glyphs: at ExtraBold Б, Ь, Я and я all read 12 to 16 per cent
  under, and Ы and Ъ 19 at Bold. Я, я and Ъ ъ are approved and their counter
  readings were recorded as outside AT approval, so the live part of this
  thread is **Б, Ь and Ы**, which are not approved. Still not explained.
- **ф at Regular and Bold** is marginally wide for its height (1.06 against a
  1.02 ceiling; 1.07 against 1.06). Its bowl cannot grow — the height is
  already at the panel's ceiling at ExtraBold — and the residual is the linear
  width fit running generous mid-axis, which two masters cannot bend.
- **9 glyphs undrawn**, all Serbian: Ђ Љ Њ Ћ ђ љ њ ћ џ. **Ukrainian and
  Russian are complete, and б — the last of them, and the only glyph in the
  font whose outline comes from another face — was approved on 2026-08-09.**
- **б's landing is solved per master and asserted, not chosen.** It lands 41
  degrees apart at the two ends of the axis and happens to fall in the same
  segment of the bowl. If o's outer contour is ever redrawn with different
  extrema, `be_from_sudo.py` will stop rather than emit two masters whose
  nodes do not correspond — that is the intended behaviour, and the fix is to
  re-seat the arc, not to relax the assertion.
- **The Cyrillic's expressive terminals are deferred to the italic, on
  purpose.** Measured by glyph, the Latin lowercase cuts a terminal obliquely
  in five letters at Thin (a, e, g, k, s) and seven at ExtraBold (a, b, c, g,
  k, p, s). The Cyrillic cuts one at Thin and three at ExtraBold — and к's is
  the Latin k's own outline, inherited rather than chosen, while є's and э's
  are open terminals at the heavy master only. **No Cyrillic letter chooses an
  expressive terminal.** That is a real asymmetry: the Cyrillic is quieter than
  the Latin it stands with, and g is the Latin's loudest moment by a distance.
  The one letter with genuine construction latitude is **д** — seven of eight
  panel faces draw the neutral triangle, and Sudo draws the cursive
  single-storey form, which is structurally g's problem, a bowl with a
  descending tail. Decided on 2026-08-09 not to spend it in the upright: the
  cursive д is a strong statement in a terminal face, and Cyrillic italic
  already takes different cursive forms for д, и, т and п, which is where the
  script's character belongs and costs nothing in legibility. **Do not add
  character to an upright Cyrillic glyph without raising this again.**
- **Checkpoint C: the italic.**
