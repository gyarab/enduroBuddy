# WeekCard Inline Editing UX — Design Spec

**Date:** 2026-04-15
**Status:** Approved
**Scope:** `frontend/src/components/training/WeekCard.vue` only

---

## Problem

Two UX issues in the WeekCard inline editor (shared by athlete dashboard and coach workspace):

1. **Row height jumps on edit** — clicking a cell opens a `<textarea rows="2">` in the title column, which pushes the row taller and shifts surrounding rows down. The table layout is visually unstable.

2. **Long text silently truncated** — title, notes, and intervals columns use `minmax(0, xfr)` grid sizing with `overflow: hidden; text-overflow: ellipsis`. On moderate viewport widths, training descriptions like `10× 1000m @ 3:50/km, 90s odpočinek, WU+WD 2km` are cut off with no way to see the full text.

---

## Solution

### Change 1 — Fixed row height during editing

**Goal:** Editing a row must not change its height. The table stays visually stable.

**Template change (`WeekCard.vue` template):**
- Replace `<textarea ... rows="2">` in the title cell with `<textarea ... rows="1">`

**CSS changes:**
- `.wt__row--editing`: remove `align-items: start`, `padding-top: 0.5rem`, `padding-bottom: 0.25rem` — keep the same layout as a normal idle row (`align-items: center`)
- `.wt__textarea`: add `resize: none; height: 1.75rem; overflow-x: auto; white-space: nowrap`

The textarea stays single-line in appearance. Long text scrolls horizontally inside the input — the user can navigate it with cursor keys or Home/End.

### Change 2 — Table expands to fit longest row

**Goal:** If any row has a long title or notes, the entire table expands horizontally so full text is visible. On narrow viewports a horizontal scrollbar appears on the card.

**CSS changes:**
- `.week-card`: `overflow: hidden` → `overflow-x: auto`
- Add `.wt__table` wrapper div (wraps all `.wt__cols` rows: head row, day rows, summary row) with `min-width: 100%; width: max-content`
- `.wt__cols` grid template: change text columns from `minmax(0, 2fr) minmax(0, 1fr)` to `max-content max-content`; same for the intervals column (`minmax(0, 1fr)` → `max-content`)
- `.wt__title-text`, `.wt__notes-text`, `.wt__intervals-text`: remove `overflow: hidden; text-overflow: ellipsis`; keep `white-space: nowrap`

The fixed-width columns (date, day, type, separator, km, time, HR×2) stay unchanged.

---

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/components/training/WeekCard.vue` | Template: `rows="2"` → `rows="1"` on title textarea. CSS: `.wt__row--editing`, `.wt__textarea`, `.week-card`, `.wt__cols`, `.wt__title-text`, `.wt__notes-text`, `.wt__intervals-text`. Add `.wt__table` class. |

No other files are affected. `PlannedRow.vue` is not rendered in any view (tests only) and is out of scope.

---

## Non-goals

- No changes to save logic, API, stores, or localization
- No changes to responsive breakpoints (they stay as-is; the `overflow-x: auto` handles narrow viewports naturally)
- No changes to `PlannedRow.vue` or `CompletedRow.vue`
