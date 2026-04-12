# WeekCard Inline Editing — Design Spec

**Date:** 2026-04-12
**Branch:** vue-frontend-codex
**Scope:** `frontend/src/components/training/WeekCard.vue` only

---

## Goal

Replace the current expand/collapse row editing (with action bar) with true inline editing. Clicking an editable field places a cursor directly in that field. Changes save automatically via debounce. Days cannot be deleted.

---

## Visual Layout

The grid columns are split into two visual zones:

```
[ datum | den ]  ·  [ type | trenink | poznámky ]  ·  [ km | čas | intervaly | ⌀HR | HR↑ ]
  ─────────────────────────────────────────────────────────────────────────────────────────
  read-only zone      planned zone                      completed zone
```

**Read-only zone** (datum + den):
- Darker background: `rgba(0,0,0,.2)` or a subtle right border (`var(--eb-border)`)
- `cursor: default` — no hover effect
- Never becomes an input

**Editable zone** (everything from "type" onward):
- On row hover: `rgba(255,255,255,.025)` background
- On row edit active: `rgba(200,255,0,.04)` background (same as today)

---

## Row Edit Mode

### Activation
- Click on any editable cell in the row → entire row enters edit mode
- Focus is placed on the specific clicked field (not the first field)
- Session type pill is separately always-clickable (does not require entering row edit mode)

### In edit mode
- Date + day columns: unchanged, no input shown
- All other columns: inputs/textarea rendered with `border: 1px solid rgba(200,255,0,.25)`
- No action bar appears — no Cancel, Save, or Delete buttons

### Deactivation
- `focusout` event from the entire row (focus moved outside the row)
- If unsaved changes exist at this point: immediate save (bypasses debounce)
- Row returns to display mode after save completes

### Editable fields (per row)
| Field | Type | Maps to |
|-------|------|---------|
| session type | pill toggle | `planned.session_type` |
| trenink (title) | `<textarea rows="2">` | `planned.title` |
| poznámky (notes) | `<input>` | `planned.notes` |
| km | `<input type="text">` mono | `completed_metrics.km` |
| čas | `<input type="text">` mono | `completed_metrics.minutes` |
| intervaly | `<input type="text">` | `completed_metrics.details` |
| ⌀HR | `<input type="text">` mono | `completed_metrics.avg_hr` |
| HR↑ | `<input type="text">` mono | `completed_metrics.max_hr` |

Completed fields are only editable when `completed[0]?.editable && !completed[0]?.has_linked_activity` (same guard as today).

---

## Auto-Save Logic

1. **Debounce 1000ms** — any change in any field of the row resets the timer
2. **Blur save** — when focus leaves the entire row before debounce fires, save immediately
3. **Save scope** — always saves the entire row in one pass (planned patch + completed patch, same as existing `saveRow()` logic)
4. **Success feedback** — row receives CSS class `wt__row--saved` for 600ms:
   - `border-left: 2px solid var(--eb-lime)` pulsing to transparent via `@keyframes saved-flash`
   - Or: `box-shadow: inset 0 0 0 1px rgba(200,255,0,.3)` fading out
5. **Error feedback** — existing toast system (`toastStore.push(...)`)
6. **No duplicate saves** — if no fields changed from original values, skip the API call

---

## Session Type Pill

- Always-clickable `<button>` element, independent of row edit mode
- Click toggles RUN ↔ WORKOUT immediately
- Saves immediately (no debounce — single-field discrete change)
- Visual:
  - RUN: `color: var(--eb-blue)`, `border: 1px solid rgba(56,189,248,.35)`
  - WORKOUT/WKT: `color: var(--eb-lime)`, `border: 1px solid rgba(200,255,0,.35)`
  - Size: `font-size: 0.5625rem`, uppercase, `border-radius: 999px`, `padding: 0.15rem 0.45rem`

---

## What Is Removed

| Removed | Reason |
|---------|--------|
| Action bar (Cancel / Save / Delete) | Replaced by auto-save + blur-save |
| `deletePlannedRow()` function | Days auto-generated, cannot be deleted |
| Delete button | Removed with action bar |
| `isEditing()` → click-to-expand pattern | Replaced by per-field focus activation |
| `wt__action-bar` CSS block | No longer needed |
| `wt__btn` CSS variants | No longer needed |

`isCreating` logic is **kept** — empty days can still be filled in by typing in the title field.

---

## State Shape

The existing `RowEdit` interface and `editingRows: Map<string, RowEdit>` remain. Changes:

- Add `isDirty: boolean` — true if any field differs from original values
- Add `debounceTimer: ReturnType<typeof setTimeout> | null`
- Remove `isSaving` from UI (no action bar to disable) — keep internally for guard logic
- Remove `error` from RowEdit (errors go to toast only)

---

## Implementation Scope

**Only `WeekCard.vue` is modified.** No changes to:
- `useInlineEditor.ts` (composable unused here, stays as-is)
- Training store or coach store save methods
- API layer
- Other training components

---

## Edge Cases

| Case | Behavior |
|------|----------|
| User edits field, immediately closes tab | Best-effort — browser may not complete XHR on unload. Acceptable. |
| Save fails mid-edit | Toast shown, row stays in edit mode, user can retry by making another change |
| Two rows edited simultaneously | Each row has its own independent state in `editingRows` map — no conflict |
| Completed row has linked activity | Completed fields show as read-only text (same guard as today), only planned fields editable |
| Empty day (no planned) | Title field shows placeholder "Přidat trénink…", clicking creates new planned row on save |
