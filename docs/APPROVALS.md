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
| **ф** | 2026-08-06 | Width, wall and middle stem all linear in the stem (`EF_FIT["lc"]`, clamped at 1.0). Bowl is **not** о — `EF_BOWL_TALLER` 1.05 about о's centre. Marginally wide for its height at Regular/Bold; two masters cannot bend it. |
| **Ф** | 2026-08-06 | Same three relations (`EF_FIT["cap"]`). `EF_OVERHANG` 0.07, which sets the bowl's height as well as the stem's projection. Every internal proportion inside the panel at all four weights. |
| **Я** | 2026-08-06 | Bowl floor is R's bowl floor, taken from node 11 of R's outline — not R's leg top, which is buried inside that floor and only appears to agree with it at Thin. Roof and floor inset at the bar, not the side stroke. Leg solved over R's own leg height and standing off the stem by R's own figure. Every reading inside the panel except the letter's width, where В is equally under it — the face is narrow, not the letter. |
| **я** | 2026-08-06 | Bowl floor is R's bowl floor, taken from node 11 of R's outline as a fraction of cap — not R's leg top, which is buried inside that floor. Roof and floor inset at the lowercase bar. Leg solved over R's own leg height and standing off the stem by R's own figure. Approved with three readings still marginally outside the panel at the heavy end — counter aspect 0.689 against 0.710, counter height 0.225 against 0.230, wedge 0.524 against 0.581. No Latin lowercase hangs a bowl over a leg, so the capital's fraction is the only donor there is; do not chase these three. |

## In review — changed and shown, no verdict recorded

| glyph | shown | change |
| --- | --- | --- |
| **в** | 2026-08-06 | Two faults. The lobe's sweep is now a fraction of the **lobe's height** rather than of the letter's width — it was asking for a corner wider than the lobe was tall at ExtraBold. And the three horizontals take B's own figures, 0.96 of the bar at Thin falling to 0.90 for the roof and floor and 0.85 for the waist, instead of a flat bar each. Counter aspect goes 2.09 to 1.69 against a panel 1.17–1.83, and its direction with weight reverses to match the panel's. The setback at the waist is 1–7% under the panel at Thin, Regular and Bold. |

## Not recorded

Drawn, gates passing, but nothing on record either way. Most were shown in
checkpoint sheets, which is not approval.

**Capitals** — А Б В Г Д Е Ж З И Й К М Н О П Р С Т У Х Ц Ч Ш Щ Ъ Ы Ь Э Ю
Ё Є І Ї Ў Ѐ Ѓ Ѕ Ј Ќ Ѝ Џ

**Lowercase** — а в д е ж и й н о п р с т у х ц ч ш щ ъ ы ь э ю ё є і ї ў ѐ
ѓ ѕ ј ѝ

## Not drawn

**б з к м** — Ukrainian/Russian core. б is the hard one: no capital and no
Latin donor.

**Ђ Љ Њ Ћ ђ љ њ ћ џ** — Serbian.

**ќ** — blocked on к.

---

*Statuses above reflect only what is defensible from the session record. An
absence here means "unknown", never "approved". If the user has approved
something not listed, add it rather than inferring it.*
