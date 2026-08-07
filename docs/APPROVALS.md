# Approvals

The record of which glyphs the user has approved, and therefore which are
**frozen**.

This file exists because `CLAUDE.md`'s rule — *never change an approved glyph
without explicit confirmation* — is unenforceable without it. The question
"is this one approved?" has been reached with no way to answer it, and Ґ had
by then been changed twice without anyone noticing it was frozen. Both cost a
round.

## How to use it

- A glyph is **in review** until the user says otherwise. Showing a checkpoint
  sheet does not approve anything on it.
- On an explicit verdict, move the glyph and date the entry.
- Before changing a glyph, look here first. If it is approved, ask.
- When a new sibling should match an approved one, **copy the approved
  construction**. Never generalise it into a shared helper and re-derive it —
  that is how ґ's work destroyed Ґ's.

---

## Approved — frozen

| glyph | approved | note |
| --- | --- | --- |
| **Ґ** | before 2026-08-06 | Tick rise `0.21 × cap` and the derived inner radius. Re-confirmed on 2026-08-06 after two unrequested changes were reverted. The panel independently supports it: `TICK_RISE` is flat at 0.212–0.221 across every weight band. |
| **л** | before 2026-08-06 | Confirmed after the leg-splay fix. `LEG_LEAN`; the sloped leg reads wider than its bbox and no metric sees it. |
| **ґ** | 2026-08-06 | All four of Ґ's corners — `[28,57,78,103]` Thin, `[4,20,67,122]` ExtraBold — with its own rise, `0.28 × x-height`, not the capital's 0.21. Arm takes `lc_arm_end`. |
| **г** | 2026-08-06 | Corner set matches Г exactly. Arm is a **ceiling**, `ARM_SHARE` × Г's arm × `lcCapWidth`, so Thin keeps its own 367 and only the heavy end moves. |
| **ф** | 2026-08-06 | Width, wall and middle stem all linear in the stem (`EF_FIT["lc"]`, clamped at 1.0). Bowl is **not** о — `EF_BOWL_TALLER` 1.05 about о's centre. Marginally wide for its height at Regular/Bold; two masters cannot bend it. Found after approval by `signature.py`: its horizontal is a unit over the Latin's own heaviest at Thin and two per cent under its lightest at Regular. Not a defect — the Latin's own range is 0.94–1.05 of t's crossbar and ф sits a hair outside each end. |
| **Ф** | 2026-08-06 | Same three relations (`EF_FIT["cap"]`). `EF_OVERHANG` 0.07, which sets the bowl's height as well as the stem's projection. Every internal proportion inside the panel at all four weights. A later reading the panel does not cover: `signature.py` puts its horizontal a unit over the Latin's own heaviest at Thin — 1.09 of H's crossbar against a Latin holding 0.96–1.09. At the edge, not outside the habit. |
| **Я** | 2026-08-06 | Bowl floor is R's bowl floor, taken from node 11 of R's outline — not R's leg top, which is buried inside that floor and only appears to agree with it at Thin. Roof and floor inset at the bar, not the side stroke. Leg solved over R's own leg height and standing off the stem by R's own figure. Every reading inside the panel except the letter's width, where В is equally under it — the face is narrow, not the letter. |
| **в** | 2026-08-06 | The lobe's sweep is a fraction of the **lobe's height**, not of the letter's width — taken across the width it asked for a corner wider than the lobe was tall at ExtraBold. The three horizontals take B's own figures rather than a flat bar each: 0.96 of the bar at Thin falling to 0.90 for the roof and floor, and 0.96 to 0.85 for the waist, read from B's inner contour's **on-curve nodes only**. Counter aspect 2.09 to 1.69 against a panel 1.17–1.83, and its direction with weight reverses to match the panel's. Approved with the setback at the waist 1–7% under the panel at Thin, Regular and Bold. |
| **Ъ ъ** | 2026-08-06 | The left edge falls with the weight — 0.035 of the advance at Thin to 0.013 at ExtraBold for the capital — where it used to sit flat at 0.055. The shoulder's length is a share of the cell and does not move, so that edge is what decides the bowl's width, and the bowl pays for its wall twice. Counter against Ь's runs 0.86, 0.79, 0.72, 0.67 against a panel holding 0.78–0.86. Going that far left is the face's own habit: Y starts at 18 units at Thin and −1 at ExtraBold, w at 32 and 20. |
| **Ж** | 2026-08-06 | The centre stem is the arms' own weight, `ZHE_STEM` 1.033. The old 0.86 was read off JetBrains Mono alone, which draws it at 0.95 falling to 0.87 — right about that face and wrong as a rule: across the 49 panel faces that draw Ж the ratio is flat at 1.00, and this face never lightens a diagonal at all, its X running 0.97 to 1.02 of H's stem at every weight. Built measurement 1.01–1.03, inside the panel at all four weights. **Recorded as still outside at approval:** the arm is heavier than the panel wants at Bold and ExtraBold — 0.85 and 0.83 of the face's own stem against brackets ending at 0.82 and 0.79. That is the face, not the letter; its own X is outside in the same direction at the same weights and its K sits at 0.86 where the arm sits at 0.85. Do not chase it. Re-read any of this with `tools/diagonals.py`. |
| **ж** | 2026-08-06 | The same change as Ж, approved separately on the same day. One constant serves both cases through `lc()`, so the lowercase is a redrawing at lowercase weight rather than a squashed capital — 150 against 161 for the stem at ExtraBold. Built measurement 1.02–1.04 of an arm, inside the panel at all four weights. **Recorded as still outside at approval:** the arm at 0.85 and 0.84 of n's stem at Bold and ExtraBold, against brackets ending at 0.83 and 0.82 — the same reason as the capital's, and not to be chased. |
| **К** | 2026-08-06 | A tier-1 donor: it **is** the Latin K, unchanged, so approving it approves the mapping rather than a drawing. The consequence is the one worth writing down — К cannot now be altered without altering the Latin, and any future change to K silently changes an approved Cyrillic glyph. `audit.py` already checks that a donor still matches the Latin it names. |
| **к** | 2026-08-06 | The face's own **k** with the stem cut to the x-height, the arm and leg taken unchanged. The 51 panel faces that draw both agree the two letters are one drawing — к is 1.000 of k's width with the middle half of the population inside a thousandth, the same left edge to the em, the same leg lean. Tier 2, not the tier 3 it had been listed as. The three contours are told apart by which one reaches above the x-height, never by their order: a donor's path indices are what F8 is about. Carries the same tie as К — it is k's outline, so a change to k changes it. |
| **ќ** | 2026-08-06 | `ka-cy + acutecomb`, no outline of its own — approved on the strength of к, which it is made of. `audit.py` checks the mark clears its base and sits centred. |
| **я** | 2026-08-06 | Bowl floor is R's bowl floor, taken from node 11 of R's outline as a fraction of cap — not R's leg top, which is buried inside that floor. Roof and floor inset at the lowercase bar. Leg solved over R's own leg height and standing off the stem by R's own figure. Approved with three readings still marginally outside the panel at the heavy end — counter aspect 0.689 against 0.710, counter height 0.225 against 0.230, wedge 0.524 against 0.581. No Latin lowercase hangs a bowl over a leg, so the capital's fraction is the only donor there is; do not chase these three. |

## In review — changed and shown, no verdict recorded

| Glyph | Shown | What it is |
| --- | --- | --- |
| **м** | 2026-08-07 | М's construction at x-height, and М's proportion in every part of it. М is the Latin M and Latin m is three arches, so there is no lowercase counterpart to take; box, upright weight, diagonal weight, vertex height and the junction are all read off M at each master. Only the **diagonals** take `crowd3` -- the box is М's, so the same width is crossed over two thirds of the height and they lean half again as hard. The uprights do not: М's own 0.845 of the stem already is this face's four-stroke reduction, and taking `crowd3` on top counted it twice and left м at 0.704 of n where п and и sit at 1.000. Built at 1.000, 0.877, 0.856, 0.847 of n against М's own 1.000, 0.872, 0.852, 0.845 of H; the panel's ratio between the two cases is 1.000, middle half inside 0.979-1.035. **Where the diagonal leaves the upright is М's figure too** -- its outer top corner sits inside the stem, 0.306 of it at Thin and 0.727 at ExtraBold, read off М's own centreline run up to the cap line because a scanline cannot see a corner buried in a merged run. Centred on the upright instead, it stepped on both sides at the x-height, and that fault was what made the upright weight and the vertex depth look like a trade-off: with it fixed the Bold wedge went from six units to forty-two and both readings fit at once. The vertex is `EM_VERTEX` 0.639 of М's own fraction, the panel's median for how far that landmark moves across the case -- 0.21 of the x-height at Thin, 0.19 at ExtraBold. Whites at 0.55 of the x-height are 88, 65, 41 and 34 against the face's own Latin floors of 9, 28, 26 and 15. Two earlier vertices were rejected by eye: М's own fraction with `crowd3` on both strokes, and the baseline, which passed every gate and read as standing on a point. |

## Not recorded

Drawn, gates passing, but nothing on record either way. Most were shown in
checkpoint sheets, which is not approval.

**Capitals** — А Б В Г Д Е З И Й М Н О П Р С Т У Х Ц Ч Ш Щ Ы Ь Э Ю
Ё Є І Ї Ў Ѐ Ѓ Ѕ Ј Ѝ Џ

**Lowercase** — а д е и й н о п р с т у х ц ч ш щ ы ь э ю ё є і ї ў ѐ
ѓ ѕ ј ѝ

## Not drawn

**б з м** — Ukrainian/Russian core. б is the hard one: no capital and no
Latin donor. з and м are their capitals' constructions at x-height; unlike к,
neither has a lowercase Latin counterpart to take.

**Ђ Љ Њ Ћ ђ љ њ ћ џ** — Serbian.

---

*Statuses above reflect only what is defensible from the session record. An
absence here means "unknown", never "approved". If the user has approved
something not listed, add it rather than inferring it.*
