# WeekCard — editing UX improvements

**Date:** 2026-04-30  
**Scope:** `frontend/components/training/WeekCard.vue`, `AthleteView.vue`, `CoachView.vue`  
**Branch:** main

---

## Problem

Three UX gaps in the current inline editor:

1. After the 1-second auto-save debounce fires, the edit state is destroyed (`editingRows.delete`) and focus is lost — the user is unexpectedly kicked out of the cell.
2. A success toast is not shown (correct), but there is also no visual confirmation that the save happened.
3. There is no keyboard navigation — users must click every cell.

---

## Goals

- Cursor stays in the cell after background auto-save.
- Successful save → brief green glow on the active zone cells.
- Failed save → brief red glow on the active zone cells + error toast.
- Full keyboard navigation within planned **or** completed zone (never crossing zones).
- Cross-week navigation: reaching Sunday goes to Monday of the next week and vice versa.

---

## Design

### 1. Save state management

Split the current `saveRow(slot, edit)` into two functions:

**`autoSave(slot, edit)`** — called by the debounce timer (1 s after typing):
- Sends API calls for dirty planned and/or completed fields.
- On success: `edit.isDirty = false`, trigger zone success flash, **do not delete the editingRows entry**.
- On error: trigger zone error flash + `toastStore.push(error, "danger")`.
- Result: cursor stays exactly where it is.

**`closeAndSave(slot, edit)`** — called by `onRowFocusOut` and keyboard navigation when leaving a row:
- Sends API calls if `edit.isDirty`.
- Always calls `editingRows.delete(date)` at the end.
- On success: whole-row green flash (current `flashRow` behaviour).
- On error: whole-row red flash + toast.

`onFieldInput` debounce now calls `autoSave`.  
`onRowFocusOut` now calls `closeAndSave`.

### 2. Flash feedback

Four reactive sets replace the single `flashingRows`:

| Reactive set | Trigger | Visual target |
|---|---|---|
| `flashingPlannedOk` `Set<date>` | `autoSave` success, planned zone | `.wt__cell-p` cells |
| `flashingCompletedOk` `Set<date>` | `autoSave` success, completed zone | `.wt__cell-c` cells |
| `flashingError` `Set<date>` | any save failure (auto or close) | both zone cells, red |
| `flashingRows` `Set<date>` | `closeAndSave` success | whole row, green (existing) |

All sets use a `setTimeout(600 ms)` to self-clear (same pattern as current `flashRow`).

CSS classes added to the row element via `:class` binding:

```
.wt__row--flash-planned-ok  → .wt__cell-p  animation: zone-ok
.wt__row--flash-completed-ok → .wt__cell-c animation: zone-ok
.wt__row--flash-err         → .wt__cell-p, .wt__cell-c  animation: zone-err
```

Keyframe `zone-ok`: fades from `rgba(200,255,0,.22)` to `rgba(200,255,0,.07)` (lands on the existing editing tint — no jarring reset).  
Keyframe `zone-err`: fades from `rgba(244,63,94,.20)` to `transparent`.

### 3. Keyboard navigation

#### Field order (per zone)

```ts
const PLANNED_FIELDS   = ["title", "notes"]                          // 2 cols
const COMPLETED_FIELDS = ["km", "minutes", "details", "avgHr", "maxHr"]  // 5 cols
```

Day order = `daySlots` array (Mon → Sun within each WeekCard).

#### Key map

| Key | Behaviour |
|---|---|
| **Tab** | Next field in row; at last field → first field of next day |
| **Shift+Tab** | Prev field in row; at first field → last field of prev day |
| **Enter** | Next day, same field (down in column) |
| **Shift+Enter** | Prev day, same field (up in column) |
| **Arrow Down** | Same as Enter |
| **Arrow Up** | Same as Shift+Enter |
| **Arrow Right** | Same as Tab — single-line inputs only (not textarea) |
| **Arrow Left** | Same as Shift+Tab — single-line inputs only |

Navigation is always confined to the active zone. Pressing Tab in the planned zone cannot move focus into the completed zone.

#### Cross-week boundary

When navigation would go past Sunday (forward) or past Monday (backward):

- WeekCard emits `navigate-out-next` or `navigate-out-prev` with payload `{ field, zone }`.
- If there is no adjacent week, navigation stops (no wrap-around within the month itself).

**WeekCard** adds:
```ts
defineExpose({
  focusCell(field: string, zone: "planned" | "completed"): void
})
```
`focusCell` opens edit on the appropriate boundary day (first day for `navigate-out-next`, last day for `navigate-out-prev`) and focuses the target field via DOM query.

**AthleteView + CoachView** (minimal change):
- Add template ref array for WeekCard instances.
- Handle `@navigate-out-next` / `@navigate-out-prev`: find the sibling WeekCard at index ± 1, call `.focusCell(field, zone)`.

#### DOM focus targeting

Each input element gets two data attributes:
- `data-field="title"` (or `"km"`, `"notes"`, etc.)
- `data-date="2026-05-01"`

After `openEdit(slot, field, zone)`, focus is applied with:
```ts
await nextTick()
document.querySelector<HTMLElement>(
  `[data-field="${field}"][data-date="${date}"]`
)?.focus()
```

`vAutofocus` directive handles initial focus when a fresh edit entry is created (mounted). DOM query handles focus when navigating within an already-open edit.

#### Textarea (title field)

- **Enter / Shift+Enter**: intercepted, `event.preventDefault()`, navigation fires.
- **Arrow Up / Down**: intercepted, navigation fires.
- **Arrow Left / Right**: NOT intercepted — browser moves cursor within text.
- **Tab / Shift+Tab**: intercepted, navigation fires.

---

## Tests to add / update

| # | Description |
|---|---|
| 1 | `autoSave` keeps edit state open after debounce save |
| 2 | `autoSave` success triggers `flashingPlannedOk` / `flashingCompletedOk` |
| 3 | `autoSave` error triggers `flashingError` + toast |
| 4 | Tab from last planned field moves to planned field of next day |
| 5 | Shift+Tab from first planned field moves to planned field of prev day |
| 6 | Enter moves down in the same column (next day, same field) |
| 7 | Shift+Enter moves up in the same column |
| 8 | Tab in planned zone does NOT move focus to completed zone |
| 9 | Tab on last day emits `navigate-out-next` with correct field + zone |
| 10 | Shift+Tab on first day emits `navigate-out-prev` |

Existing save tests (2 tests using `onRowFocusOut`) remain valid — `closeAndSave` still deletes the edit entry on focusout, matching current assertions.

---

## Files changed

| File | Change |
|---|---|
| `frontend/components/training/WeekCard.vue` | All logic + CSS changes |
| `frontend/components/training/WeekCard.test.ts` | New tests 1–10 above |
| `frontend/views/dashboard/AthleteView.vue` | Template refs + navigate-out handlers |
| `frontend/pages/coach/plans.vue` | Same (coach view) |
| `frontend/i18n/locales/cs.json` | No new keys needed |
| `frontend/i18n/locales/en.json` | No new keys needed |
