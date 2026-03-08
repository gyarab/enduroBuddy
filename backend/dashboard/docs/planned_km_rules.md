# Planned KM Rules

This document is the source of truth for how planned weekly kilometers are calculated from the `Training` column.

## Goal

The weekly sum should be predictable for coaches and athletes and should avoid extreme miscalculations.

## What Is Counted

1. Explicit kilometer values:
- `8 km`
- `17-19 km` (range -> upper bound, here `19.0 km`)

2. Explicit meter values and interval structures:
- `6x300m`
- `2x(1000-800-600-400-200)`
- `3R 2x5x300m ... 2V`

3. Warm-up / cool-down markers:
- `2R` means `2 km`
- `2V` means `2 km`
- Only uppercase `R` / `V` are valid markers.

## What Is Not Counted

1. Walking segments:
- `MCH`
- `chůze`

2. Non-running parts without distance:
- `mobilita`
- `posilka`
- `plyometrie`

3. Rest:
- `volno`

## Required Writing Style For Coaches

1. Always include units for numeric distances:
- Use `km` or `m` directly after value (optional space is ok).
- Correct: `1200m`, `8 km`

2. Use uppercase warm-up/cool-down:
- Correct: `2R`, `2V`
- Avoid lowercase in plain sentence contexts.

3. Write intervals in explicit forms:
- `6x400m`
- `2x(1000-800-600-400-200)`
- `2-3x(2km + 1km)`

4. Keep walking explicit:
- Write `MCH` or `chůze` when a segment is walking.

5. For long easy runs, always include range/value:
- Preferred: `17-19 km volný běh`
- Avoid only: `delší klus na pocit`

## Parsing Rules (Summary)

1. Ranges use upper bound:
- `6-8 km` -> `8.0 km`
- `2-3x(...)` -> multiplier `3`

2. Interval blocks multiply:
- `3x5x150m` -> `2.25 km`

3. Walk segments are excluded.

4. Safety limits prevent extreme values from malformed text.

## Real Examples From Training Plan

### Good / Recommended

- `2R 4x(1200m - 400m), P=1,5' po 1200m a 3' po sérii, tempo 10K - 3K (1500m) 2V`
- `2R 8 km fartlek (30' svižně, 120' klus) 2V`
- `3R 2x(100-200-300-400-300-200-100) kopce s MK, P=5' 3V`
- `2R mobilita, plyometrie, prudší kopce 6-8x100m s MCH 5V`
- `volný běh 17-19 km`

### Ambiguous / Not Recommended

- `delší klus na pocit` (missing explicit distance/range)
- `400 v tempu` (plain sentence, not a marker)
- distance numbers without unit where context is unclear

## UI Copy (CZ)

Suggested inline helper text near `Training` column:

`Piš vzdálenosti jako 8 km, 6-8 km, 6x300m, 2x(1000-800-600). Rozklus/výklus: 2R/2V. Chůze: MCH/chůze (nepočítá se).`
