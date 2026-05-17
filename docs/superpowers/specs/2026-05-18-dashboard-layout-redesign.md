# Dashboard Layout Redesign

**Date:** 2026-05-18  
**Branch:** `feat/dashboard-layout-redesign`  
**Status:** Approved for implementation

---

## Overview

Redesign the TopNav and dashboard shell for both athlete and coach views. The training grid (WeekCard, PlannedRow, CompletedRow, MonthSummaryBar) is **not changed** — only its container layout changes. The NotificationBell is removed entirely. The legend becomes a scrollable side panel. The coach's athlete management becomes a wider left-overlay panel with a vertical menu.

---

## TopNav

### Layout

CSS Grid with `grid-template-columns: 1fr auto 1fr` guarantees the month label is always geometrically centered regardless of how many buttons are on either side.

```
[left: 1fr]          [center: auto]          [right: 1fr]
logo + username      month / year            action buttons
```

### Left slot — logo + identity

- Logo mark SVG (28×28) + wordmark "EnduroBuddy" (Syne 700, 15px) stacked with username below (Nunito 400, 10.5px, `--eb-text-muted`)
- Username is the logged-in user's name (from `authStore.user.first_name + last_name`)

### Center slot — month label

- Calendar icon (`lucide: calendar`) + "Červen 2026" text
- Font: Outfit 600, 14px, `--eb-text` slightly muted (`#e4e4e7`)
- Month name from current `trainingStore` month/year state

### Right slot — action buttons

Three variants depending on context:

| Context | Buttons (left → right) |
|---------|------------------------|
| Athlete view, coach role | `[Coach]` · divider · `[sync icon]` · divider · `[legend icon]` · avatar |
| Athlete view, no coach role, Garmin enabled | `[sync icon]` · divider · `[legend icon]` · avatar |
| Athlete view, no coach role, Garmin disabled | `[legend icon]` · avatar |
| Coach view | `[Můj plán]` · divider · `[sync icon]` · avatar |

**Coach button** (`nav-txt-btn.coach`): lime border/text/bg tint, icon `arrow-left-right`, text "Coach". Visible only when `authStore.user.is_coach === true`. Navigates to `/coach/plans`.

**Můj plán button** (`nav-txt-btn`): blue border/text/bg tint, icon `arrow-left-right`, text "Můj plán". Visible only in coach view. Navigates to `/app/dashboard`.

**Sync button** (`nav-btn.import`): icon-only, `refresh-cw` icon, green tint border/color. Visible only when `authStore.user.garmin_connect_enabled === true`. Triggers Garmin import flow.

**Legend button** (`nav-btn`): icon-only, `book-open` icon. Athlete view only (not shown in coach view). Opens athlete's own legend side panel.

**Avatar**: initials circle, lime text, profile dropdown on click. Unchanged from current implementation.

**Dividers**: 1px × 20px `#2e2e34`, used to visually group related controls.

### Removed

- `NotificationBell` component removed from TopNav entirely. The Nuxt default notification mechanism (if any) is used instead. The bell icon and its dropdown are deleted.

---

## Athlete Dashboard View (`/app/dashboard`)

### Shell layout

```
┌─────────────────────────── TopNav (52px) ──────────────────────────────┐
│                                                                        │
│  ┌─────────────────── main (flex:1, overflow-y:auto) ────────────┐ ┌──┐│
│  │                                                               │ │Le││
│  │  WeekCard × N (unchanged)                                     │ │ge││
│  │                                                               │ │nd││
│  └───────────────────────────────────────────────────────────────┘ │  ││
│                                                                    └──┘│
├────────────────────────── MonthSummaryBar (44px) ──────────────────────┤
```

No sidebar. Full-width grid. Legend panel slides in from the right (340px, `border-left`).

### Legend panel (athlete's own)

- Triggered by legend icon button in TopNav
- Title: "Moje legenda", subtitle: "Upravuje trenér"
- All three sections visible at once without tabs (scroll for overflow):
  1. **HR zóny** — 5 zones (Z1–Z5), each with color bar label + min/max bpm inputs
  2. **Tréninkové prahy** — AeT, AnT, MaxTep, LTHR; each with bpm input + optional min/km input
  3. **Osobní rekordy** — 5K, 10K, half marathon, marathon; each a time input
- Footer: "Změny se ukládají automaticky" (auto-save indicator, no save button)
- Width: 340px, slides in from right edge, `transition: width .25s`

---

## Coach Dashboard View (`/coach/plans`)

### Shell layout

```
┌─────────────────────────── TopNav (52px) ──────────────────────────────┐
│                                                                        │
│ ┌──────────┐ ┌──────── toolbar (48px) ──────────────────────────────┐ │
│ │          │ │ [Athlete name] | [Focus pill] | spacer | [Legenda] │ │ │
│ │ Sidebar  │ ├──────────────────────────────────────────────────────┤ │
│ │ 200px    │ │                                                      │ │
│ │          │ │  WeekCard × N (unchanged)                            │ │
│ │ [Manage] │ │                                                      │ │
│ └──────────┘ └──────────────────────────────────────────────────────┘ │
├────────────────────────── MonthSummaryBar (44px) ──────────────────────┤
```

### Sidebar

- 200px fixed width, `background: #111113`, `border-right: 1px solid #27272a`
- Header: "Svěřenci" label
- Athlete rows: dot indicator (lime = active, gray = hidden) + name + optional focus badge
- Hidden athletes: strikethrough name, reduced opacity
- Active athlete: lime left-border, subtle lime bg tint
- Footer: "Správa svěřenců" button (full width, icon `users`, default gray style, lime on hover/active)

### Toolbar

- Height: 48px, `background: #111113`, `border-bottom: 1px solid #1e1e22`
- Left: selected athlete name (Outfit 700, 15px) + divider + focus pill (blue tint, `zap` icon, editable label)
- Right: "Legenda atleta" button (same style as legend-trigger: gray border, lime on active, icon `book-open`)

### Legenda atleta panel (right, 340px)

Same structure as athlete legend panel:
- Title: "Legenda — {athlete name}", subtitle: "Upravuje trenér · vidí sportovec"
- All sections visible at once: HR zóny (editable ranges) → Prahy (editable bpm/pace) → Rekordy (editable times)
- Footer: auto-save indicator
- Triggered by "Legenda atleta" button in toolbar
- Mutually exclusive with Správa svěřenců panel

### Správa svěřenců panel (left overlay, 480px)

Opens as a left-side overlay that slides over the sidebar (not pushing main content). Two-column interior layout:

```
┌──────────── header ─────────────────────────────┐
│ Správa svěřenců    4 celkem · 3 aktivní          │ [×]
├──────────┬──────────────────────────────────────┤
│          │                                      │
│ [users]  │  content of selected section         │
│ Svěřenci │                                      │
│          │                                      │
│ [copy]   │                                      │
│ Pozvat   │                                      │
│          │                                      │
│ [check]  │                                      │
│ Žádosti  │                                      │
│   [2]    │                                      │
│          │                                      │
├──────────┴──────────────────────────────────────┤
│ ✓ Změny se ukládají automaticky                 │
└─────────────────────────────────────────────────┘
```

**Left menu** (116px): vertical nav items — icon + label, active item has lime left border + lime color. Badge (orange pill) on Žádosti when count > 0.

**Right content sections:**

1. **Svěřenci** — list of athletes; each row: status dot + name + optional focus badge + [eye toggle] + [switch to dashboard] + [remove]. Remove triggers inline confirmation (name-repeat input, cancel/confirm). Hidden athletes shown with strikethrough + eye-off icon.

2. **Pozvat** — Coach code card: large mono code (lime, `JetBrains Mono` 500, 20px, letter-spacing 0.16em) + "Zkopírovat" button. Hint text below explaining usage.

3. **Žádosti** — Pending join requests; each row: avatar initials + name + email + [Přijmout btn] + [reject icon]. Badge count on menu item.

**Panel behavior:**
- `position: absolute; left: 0; top: 0; bottom: 0` within `.body` (`.body` is `position: relative`)
- Opens via `transform: translateX(0)`, closed via `transform: translateX(-100%)`, `transition .25s`
- Box shadow on right edge (`box-shadow: 6px 0 32px rgba(0,0,0,.5)`)
- Mutually exclusive with legend panel — opening one closes the other

---

## Panel mutual exclusion

Both right-side panel (legend) and left-side panel (manage) can be open independently. They don't conflict spatially (legend is right, manage is left overlay). However, opening one while the other is open closes the other, keeping the UI uncluttered.

---

## Components affected

| Component | Change |
|-----------|--------|
| `frontend/components/layout/TopNav.vue` | Full rewrite — grid layout, new button set, username display |
| `frontend/components/layout/NotificationBell.vue` | **Delete** (and remove from TopNav) |
| `frontend/components/layout/LegendModal.vue` | Convert from modal → side panel, remove tabs, add auto-save |
| `frontend/components/coach/AthleteManageModal.vue` | Convert from modal → left overlay panel, add vertical menu, auto-save |
| `frontend/views/dashboard/AthleteView.vue` | Add legend panel wiring, remove notification bell ref |
| `frontend/views/dashboard/CoachView.vue` | Add sidebar footer manage button, toolbar layout, both panel wirings |

**Not changed:**
- `WeekCard.vue` and all training grid components
- `MonthSummaryBar.vue`
- `ProfileDropdown.vue`
- All API layer

---

## Design tokens used

```css
--eb-bg:      #09090b   /* app background */
--eb-surface: #18181b   /* topnav, cards */
--eb-border:  #27272a   /* all borders */
--eb-text:    #fafafa
--eb-text-muted: #71717a
--eb-lime:    #c8ff00   /* active/coach accent */
--eb-blue:    #38bdf8   /* planned/athlete accent */
```

Panel background: `#111113` (slightly darker than surface, same as sidebar).

---

## Open questions resolved

- **Notification bell**: removed entirely, no replacement in the app shell
- **Legend in coach TopNav**: removed — legend is only accessible contextually via the toolbar "Legenda atleta" button
- **Athlete reorder**: not in the Správa panel — drag reorder is done directly on the sidebar list (future feature)
- **Garmin sync**: icon-only button, conditionally visible, no label
