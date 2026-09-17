# Italic в — chosen construction

User picked **L** on 2026-09-16 ("Version L! Looks good"), then asked for it
wider: **L3**, with the loop's top kept a true circle ("L3 round top").
Judged at Thin. Not approved in the APPROVALS sense.

Built into the font on 2026-09-17 by `recipes.Ve_pen`, with `tools/pen.py`
turning the pen path into outlines. These scripts are the probes it came from.

Construction: `vform.pen_spine` — one pen path swept at constant width.

- bowl: italic o's centreline, 80% of its height, `wide` × 80% of its width,
  standing on the baseline
- left line: continues the bowl's own left side upward at 18°
- top: exact circle in the loop's leaning frame, radius r × `loopwide`
  (`roundtop=True`), stopped 40° short of half-way
- right side: one round turn onto the bowl's top, handles 0.65 of the way
  to where the end directions cross; shares the bowl's stroke to the join
- tiny enclosed specks (< 0.5 stroke²) filled: `vpen2.fill_specks`

| master    | stroke | r   | merge | wide | loopwide |
|-----------|--------|-----|-------|------|----------|
| Thin      | 28     | 70  | 5.0   | 1.25 | 1.35     |

Common: lean 18, vee 65, bulge 0, split 0.6, full 0.65, psi -40, scale 0.80.

Ink width at Thin: 429 (о is 430). Loop 0.54 of the bowl's width.

## ExtraBold — "H", kept for now (2026-09-17)

Not approved: the user said "H is still better, keep it for now".

| stroke             | r   | merge | wide | loopwide | scale |
|--------------------|-----|-------|------|----------|-------|
| oval pen 148 × 112 | 100 | 1.8   | 1.15 | 1.10     | 0.92  |

Ink width 502 (о is 485). Loop 0.79 of the bowl's width. Counters: bowl
39.5k, loop 9.5k.

What the heavy rounds taught:

- The loop sits between x-height and the ascender. At ExtraBold that is about
  two strokes, so a round loop fills in. Shrinking the bowl to make room made
  the loop as big as the bowl, and the letter read as 8 ("F", rejected).
- The bowl must lead: near full x-height, clearly bigger than the loop.
- `merge` is a distance along the bowl's top, not a style knob. Too small at
  ExtraBold and the loop lands inside solid ink, so its white comes to a point.
- Width must stay near о's. Wider bowls ("G", 593) were rejected in words.
- A lighter pen on the loop ("J") and a wider letter ("I") were rejected.
- Landing the loop early, as at Thin, gives Thin's waist on the right ("K",
  "L"), but the user still preferred H.
- The face keeps its upper storey as heavy as its lower (8, В at ExtraBold),
  so a lighter loop has no support in the face.

Sheets: `vcompare.py` → `tools/out/в-form-thin.svg`;
`vcompare_eb.py` → `tools/out/в-form-eb.svg`. `veb.py` tries ExtraBold settings.
Rebuild the scratchpad from the transcript with `replay.py` if it is wiped.
