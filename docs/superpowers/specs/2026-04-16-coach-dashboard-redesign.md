# Coach Dashboard Redesign

**Date:** 2026-04-16  
**Status:** Approved  
**Scope:** CoachView, CoachSidebar, AthleteManageModal, AthleteView (empty state only)

---

## Overview

Redesign of the coach dashboard focusing on four goals:

1. **Toolbar layout** — compact single-line header, logical grouping of controls
2. **Athlete reordering** — drag-and-drop in sidebar and modal, auto-save on drop, no explicit Save Order button
3. **Athlete context menu** — right-click on any athlete row (sidebar or modal) opens a context menu
4. **Keyboard navigation** — arrow keys in sidebar, Tab/Enter in toolbar, Escape for modals/menus
5. **Always-visible coach panel** — toolbar visible even when no athletes exist yet

---

## 1. Toolbar (CoachView header)

### When no athlete is selected (empty state)

A minimal always-visible `EbCard` strip at the top of the content area:

```
┌────────────────────────────────────────────────────┐
│ COACH WORKSPACE                  [Manage athletes] │
└────────────────────────────────────────────────────┘
```

Below it: an empty-state card prompting the coach to add their first athlete via Manage Athletes (coach code / join requests).

### When an athlete is selected

The same card expands to a compact **single-line** layout — all controls on one row:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ Jan Novák  [● Z1]      [___________]  [Save focus]  [Manage]  [← Dash]  │
│            focus pill  focus input                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Athlete name** — `font-family: Syne`, large, flex: 1
- **Focus pill** — blue badge showing current focus value (read-only indicator)
- **Focus input** — editable text field, `maxlength="10"`, `min-width: 8rem`
- **Save focus** — secondary button, disabled while saving
- **Manage athletes** — ghost button, opens AthleteManageModal
- **← Athlete dashboard** — ghost button, RouterLink to `/app/dashboard`

On mobile (< 1024px): wraps to two rows — name + pill on top, focus controls + actions below.

---

## 2. Sidebar — Athlete List (CoachSidebar)

### Layout per row

```
[⠿] [●] Jan Novák                              [Z1]
     dot  full name (ellipsis if overflow)    focus tag
```

- **Drag handle** (⠿): visible on row hover, `cursor: grab`, width ~12px
- **Status dot**: lime if selected, `--eb-border` color otherwise
- **Full name**: `text-overflow: ellipsis; white-space: nowrap; overflow: hidden` + `title` attribute with full name for native browser tooltip
- **Focus tag**: blue, uppercase, only if focus is set; `flex-shrink: 0`

### Hidden athletes

Remain in the sidebar list — dimmed (`opacity: 0.4`), name has `text-decoration: line-through`.

### Drag-and-drop ordering

- HTML5 Drag API (`draggable`, `dragstart`, `dragover`, `drop` events)
- Visual feedback: dragged item becomes semi-transparent, drop target gets a highlight line
- **Auto-save on drop**: calls `PATCH /api/v1/coach/reorder-athletes/` immediately after drop
- No explicit "Save order" button anywhere

### Keyboard navigation

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move focus between athlete rows |
| `Enter` | Select focused athlete (load their dashboard) |
| Context menu keys — see section 4 |

### Right-click context menu

Triggered by `contextmenu` event on any athlete row. Dismisses on `Escape`, outside click, or item selection.

Menu items:
1. **→ Go to athlete dashboard** — navigates to `/app/dashboard` with that athlete's session (coach visits athlete's own view)
2. **○ Hide athlete** / **● Show athlete** — toggles visibility, calls existing `PATCH /api/v1/coach/athlete-visibility/`, updates sidebar immediately
3. **✕ Remove…** — opens inline confirm dialog (existing behavior: type athlete name to confirm)

Menu is positioned relative to the clicked row, flips upward if near viewport bottom.

---

## 3. Manage Athletes Modal — Athletes Tab

### Changes from current implementation

- **Removed**: Up/Down buttons for ordering
- **Added**: Drag-and-drop (same HTML5 API as sidebar), auto-save on drop
- **Added**: Right-click context menu (identical to sidebar: Go to dashboard / Hide-Show / Remove…)
- **Footer**: Cancel button only — no Save Order button (order saves automatically)

### Layout per row

```
[⠿] Jan Novák                          [Z1]
[⠿] Eva Horáčková
[⠿] ~~Marek Kovář~~                  [Hidden]   ← dimmed, strikethrough
```

- Hidden athletes are always shown in the modal list (to allow showing them again via context menu)
- Hidden badge: `--eb-warning` color

### Tabs unchanged

- **Athletes** (redesigned as above)
- **Coach Code** (no change)
- **Join Requests** (no change)

---

## 4. Keyboard Navigation — Full Spec

### Sidebar

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move between athlete rows |
| `Enter` | Select athlete |
| `Tab` | Exit sidebar, move to main content |

### Toolbar

| Key | Action |
|-----|--------|
| `Tab` | Move through: focus input → Save focus → Manage → ← Dash |
| `Enter` on Save focus | Submit focus |
| `Enter` on Manage | Open modal |

### Context menu

| Key | Action |
|-----|--------|
| `↑` / `↓` | Move between menu items |
| `Enter` | Activate item |
| `Escape` | Close menu |

### Modal

| Key | Action |
|-----|--------|
| `Tab` | Move between tabs and interactive elements |
| `Escape` | Close modal |
| Arrow keys inside athlete list | Same as sidebar |

---

## 5. Athlete Dashboard (AthleteView) — No Change

AthleteView structure is unchanged. The "Go to athlete dashboard" context menu item in the coach sidebar navigates to `/app/dashboard` — this is the **coach's own athlete dashboard** (RouterLink `to="/app/dashboard"`), not the selected athlete's view. It serves as a quick way for the coach to switch back to their own training view. The link does not impersonate the athlete.

---

## 6. Implementation Notes

### Drag-and-drop library

Use the **HTML5 Drag and Drop API** natively — no third-party library. The list is short (typically < 20 athletes) so a simple dragstart/dragover/drop implementation suffices.

Pattern:
```ts
// on dragstart: store dragged index
// on dragover: compute target index, reorder local draft array
// on drop: persist via API
```

### Context menu component

New shared component: `frontend/src/components/ui/EbContextMenu.vue`

Props:
- `items: ContextMenuItem[]` — `{ label, icon?, action, variant? }`
- `position: { x, y }` — pixel coords relative to viewport
- `open: boolean`

Emits: `close`, `select(item)`

Rendered in a teleport to `<body>` to avoid overflow clipping from sidebar.

### Auto-save debounce

After a drop event, call the reorder API directly (no debounce needed — drop is a discrete event, not continuous input).

### Existing API endpoints used

| Action | Endpoint |
|--------|----------|
| Reorder athletes | `PATCH /api/v1/coach/reorder-athletes/` |
| Hide/show athlete | `PATCH /api/v1/coach/athlete-visibility/` |
| Remove athlete | `DELETE /api/v1/coach/athletes/{id}/` |
| Save focus | `PATCH /api/v1/coach/athlete-focus/` |

No new backend endpoints needed.

---

## 7. Files to Change

| File | Change |
|------|--------|
| `frontend/src/views/dashboard/CoachView.vue` | Toolbar redesign, always-visible panel, mobile layout |
| `frontend/src/components/coach/CoachSidebar.vue` | DnD, keyboard nav, context menu, full names + ellipsis |
| `frontend/src/components/coach/AthleteManageModal.vue` | DnD, context menu, remove Up/Down buttons, remove Save Order button |
| `frontend/src/components/ui/EbContextMenu.vue` | New shared context menu component |
| `frontend/src/locales/cs.json` | New keys for context menu, empty state |
| `frontend/src/locales/en.json` | Same |
