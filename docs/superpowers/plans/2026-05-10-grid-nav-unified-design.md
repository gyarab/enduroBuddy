# Grid Nav — Unified Mouse + Keyboard + Visual Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify mouse and keyboard navigation by emitting `cursor-set` from WeekCard on every `openEdit()` call, and redesign the nav cursor/hover/flash visuals to use zone-aware blue/lime colors with a pill-hugging cursor for the Type column.

**Architecture:** All CSS and template changes live in `WeekCard.vue`. Parent views (AthleteView, CoachView) each add a single `@cursor-set` listener. `useGridNav` composable is unchanged.

**Tech Stack:** Vue 3 SFC, TypeScript, scoped CSS, Vitest + Vue Test Utils

---

## File Map

| File | Change |
|------|--------|
| `frontend/components/training/WeekCard.vue` | zone-aware CSS classes, pill cursor, cell-level hover, zone-aware flash, min-height, notes→textarea, cursor-set emit, auto-resize all planned textareas |
| `frontend/components/views/dashboard/AthleteView.vue` | `@cursor-set` listener syncing `cursor.value` |
| `frontend/components/views/dashboard/CoachView.vue` | same as AthleteView |
| `frontend/components/training/WeekCard.test.ts` | update expected class names, add cursor-set test, add textarea test |

---

## Task 1: Update tests — write failing assertions for new class names

**Files:**
- Modify: `frontend/components/training/WeekCard.test.ts`

These tests currently pass with old class names. After this task they will FAIL, which is correct — they become the target the implementation must satisfy.

- [ ] **Step 1: Locate the nav-selected and flash-ok test assertions**

Open `frontend/components/training/WeekCard.test.ts`. Find the three assertions that use old class names (around lines 302–338 based on current content):
```
'wt__cell--nav-selected'   (appears 3 times)
'wt__cell--flash-ok'       (appears 1 time)
```

- [ ] **Step 2: Replace old class names with zone-aware names**

In the test block `'shows nav-selected class on type cell (fi=0)'` (or similar — it checks `data-testid="nav-cell-type-..."`) change:
```ts
expect(typeCell.classes()).toContain('wt__cell--nav-selected')
```
to:
```ts
expect(typeCell.classes()).toContain('wt__cell--nav-selected-p')
```

In the test block that checks title cell (fi=1) nav selection:
```ts
expect(titleCell.classes()).toContain('wt__cell--nav-selected')
```
to:
```ts
expect(titleCell.classes()).toContain('wt__cell--nav-selected-p')
```

In the test that checks `.wt__cell--nav-selected` count is 0 after cursor cleared:
```ts
const selected = wrapper.findAll('.wt__cell--nav-selected')
```
to:
```ts
const selected = wrapper.findAll('.wt__cell--nav-selected-p, .wt__cell--nav-selected-c')
```
(Vue Test Utils `findAll` doesn't support CSS selector lists natively — use two `findAll` calls and sum them):
```ts
const selectedP = wrapper.findAll('.wt__cell--nav-selected-p')
const selectedC = wrapper.findAll('.wt__cell--nav-selected-c')
expect(selectedP.length + selectedC.length).toBe(0)
```

In the flash test block `'flashCellOk adds wt__cell--flash-ok class to title cell'`:
```ts
expect(cell.classes()).toContain('wt__cell--flash-ok')
```
to:
```ts
expect(cell.classes()).toContain('wt__cell--flash-ok-p')
```

- [ ] **Step 3: Add a test for cursor-set emit**

At the end of the test file, inside the main describe block, add:

```ts
it('emits cursor-set with dayIdx and fieldIdx when a planned cell is clicked', async () => {
  const week = buildWeek()
  const wrapper = mountWeekCard(week)
  const titleCell = wrapper.find('[data-testid="cell-title-' + DATE + '"]')
  await titleCell.trigger('click')
  const emitted = wrapper.emitted('cursor-set')
  expect(emitted).toBeTruthy()
  expect(emitted![0][0]).toEqual({ dayIdx: 0, fieldIdx: 1 })
})
```

- [ ] **Step 4: Add a test for notes textarea (inline expansion)**

```ts
it('renders notes as textarea when planned zone is open', async () => {
  const week = buildWeek()
  const wrapper = mountWeekCard(week)
  const titleCell = wrapper.find('[data-testid="cell-title-' + DATE + '"]')
  await titleCell.trigger('click')
  await nextTick()
  const notesTextarea = wrapper.find('[data-field="notes"][data-date="' + DATE + '"]')
  expect(notesTextarea.element.tagName).toBe('TEXTAREA')
})
```

- [ ] **Step 5: Run tests — confirm they fail**

```bash
cd frontend && npm test -- --reporter=verbose WeekCard.test.ts
```

Expected: 4+ failures (nav-selected class names, flash class name, cursor-set emit, notes textarea tag).

---

## Task 2: Zone-aware nav cursor — CSS + template class bindings

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` (`<script setup>` + `<template>` + `<style scoped>`)

- [ ] **Step 1: Add `navSelectedClass` helper to `<script setup>`**

After the existing `isNavSelected` function (line ~469), add:

```ts
function navSelectedClass(slotDate: string, fieldIdx: number): string {
  if (!isNavSelected(slotDate, fieldIdx)) return ''
  return fieldIdx <= 2 ? 'wt__cell--nav-selected-p' : 'wt__cell--nav-selected-c'
}
```

- [ ] **Step 2: Replace CSS nav cursor block in `<style scoped>`**

Find (line ~1282):
```css
/* ── Nav cursor highlight ── */
.wt__cell--nav-selected {
  outline: 2px solid var(--eb-lime);
  outline-offset: -1px;
  background: rgba(200, 255, 0, 0.06);
  border-radius: 4px;
}
```

Replace with:
```css
/* ── Nav cursor highlight — zone-aware ── */
.wt__cell--nav-selected-p {
  outline: 2px solid #38bdf8;
  outline-offset: -1px;
  background: rgba(56, 189, 248, .08);
  border-radius: 4px;
}

.wt__cell--nav-selected-c {
  outline: 2px solid #c8ff00;
  outline-offset: -1px;
  background: rgba(200, 255, 0, .08);
  border-radius: 4px;
}

/* Type cell (fi=0): container has no outline, pill handles cursor */
.wt__cell--type.wt__cell--nav-selected-p {
  outline: none;
  background: transparent;
}
```

- [ ] **Step 3: Update template class bindings — replace `wt__cell--nav-selected` with `navSelectedClass()`**

In the template, for each cell that currently has `'wt__cell--nav-selected': isNavSelected(slot.date, N)`, replace with the result of `navSelectedClass()`.

**Type cell (fi=0)** — currently:
```html
:class="{
  'wt__cell--nav-selected': isNavSelected(slot.date, 0),
  'wt__cell--flash-ok': flashingCellsOk.has(`${slot.date}:0`),
  'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:0`),
}"
```
Replace with:
```html
:class="[
  navSelectedClass(slot.date, 0),
  { 'wt__cell--flash-ok-p': flashingCellsOk.has(`${slot.date}:0`) },
  { 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:0`) },
]"
```

**Title cell (fi=1)**:
```html
:class="[
  navSelectedClass(slot.date, 1),
  { 'wt__cell--flash-ok-p': flashingCellsOk.has(`${slot.date}:1`) },
  { 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:1`) },
]"
```

**Notes cell (fi=2)**:
```html
:class="[
  navSelectedClass(slot.date, 2),
  { 'wt__cell--flash-ok-p': flashingCellsOk.has(`${slot.date}:2`) },
  { 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:2`) },
]"
```

**km cell (fi=3)**:
```html
:class="[
  navSelectedClass(slot.date, 3),
  { 'wt__cell--flash-ok-c': flashingCellsOk.has(`${slot.date}:3`) },
  { 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:3`) },
]"
```

**minutes cell (fi=4)**:
```html
:class="[
  navSelectedClass(slot.date, 4),
  { 'wt__cell--flash-ok-c': flashingCellsOk.has(`${slot.date}:4`) },
  { 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:4`) },
]"
```

**details cell (fi=5)**:
```html
:class="[
  navSelectedClass(slot.date, 5),
  { 'wt__cell--flash-ok-c': flashingCellsOk.has(`${slot.date}:5`) },
  { 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:5`) },
]"
```

**avgHr cell (fi=6)**:
```html
:class="[
  navSelectedClass(slot.date, 6),
  { 'wt__cell--flash-ok-c': flashingCellsOk.has(`${slot.date}:6`) },
  { 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:6`) },
]"
```

**maxHr cell (fi=7)**:
```html
:class="[
  navSelectedClass(slot.date, 7),
  { 'wt__cell--flash-ok-c': flashingCellsOk.has(`${slot.date}:7`) },
  { 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:7`) },
]"
```

- [ ] **Step 4: Run tests — nav-selected tests should now pass**

```bash
cd frontend && npm test -- --reporter=verbose WeekCard.test.ts
```

Expected: nav-selected class name tests pass. `cursor-set` emit test and notes textarea test still fail. Flash tests may still fail (done in Task 3).

---

## Task 3: Zone-aware flash + cell-level hover + min-height — CSS only

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` (`<style scoped>` only)

- [ ] **Step 1: Replace cell-level flash CSS**

Find (line ~1290):
```css
/* ── Cell-level flash ── */
@keyframes cell-flash-ok {
  0%   { background-color: rgba(200, 255, 0, 0.22); }
  100% { background-color: transparent; }
}

@keyframes cell-flash-err {
  0%   { background-color: rgba(244, 63, 94, 0.22); }
  100% { background-color: transparent; }
}

.wt__cell--flash-ok  { animation: cell-flash-ok  0.8s ease-out forwards; }
.wt__cell--flash-err { animation: cell-flash-err 0.8s ease-out forwards; }
```

Replace with:
```css
/* ── Cell-level flash — zone-aware ── */
@keyframes cell-flash-ok-planned {
  0%   { background-color: rgba(56, 189, 248, .22); }
  60%  { background-color: rgba(56, 189, 248, .08); }
  100% { background-color: transparent; }
}

@keyframes cell-flash-ok-completed {
  0%   { background-color: rgba(200, 255, 0, .22); }
  60%  { background-color: rgba(200, 255, 0, .10); }
  100% { background-color: rgba(200, 255, 0, .05); }
}

@keyframes cell-flash-err {
  0%   { background-color: rgba(244, 63, 94, 0.22); }
  100% { background-color: transparent; }
}

.wt__cell--flash-ok-p { animation: cell-flash-ok-planned   0.8s ease-out forwards; }
.wt__cell--flash-ok-c { animation: cell-flash-ok-completed 0.8s ease-out forwards; }
.wt__cell--flash-err  { animation: cell-flash-err           0.8s ease-out forwards; }
```

- [ ] **Step 2: Replace zone-level hover with cell-level hover**

Find (line ~1115):
```css
/* Hover: planned zone — blue tint */
.wt__row:has(.wt__cell-p:hover):not(.wt__row--editing-planned):not(.wt__row--editing-completed) .wt__cell-p {
  background: rgba(56, 189, 248, .05);
  cursor: pointer;
}

/* Hover: completed zone — lime tint */
.wt__row:has(.wt__cell-c:hover):not(.wt__row--editing-planned):not(.wt__row--editing-completed) .wt__cell-c {
  background: rgba(200, 255, 0, .05);
  cursor: pointer;
}
```

Replace with:
```css
/* Hover: planned cell — blue ghost (cell-level) */
.wt__row:not(.wt__row--editing-planned):not(.wt__row--editing-completed)
  .wt__cell-p:hover {
  outline: 1px solid rgba(56, 189, 248, .38);
  background: rgba(56, 189, 248, .05);
  cursor: pointer;
}

/* Hover: completed cell — lime ghost (cell-level) */
.wt__row:not(.wt__row--editing-planned):not(.wt__row--editing-completed)
  .wt__cell-c:hover {
  outline: 1px solid rgba(200, 255, 0, .38);
  background: rgba(200, 255, 0, .05);
  cursor: pointer;
}

/* Type cell: no outline on hover — pill handles it */
.wt__row:not(.wt__row--editing-planned):not(.wt__row--editing-completed)
  .wt__cell--type:hover {
  outline: none;
  background: transparent;
}
```

- [ ] **Step 3: Add min-height to zone cells and num-val spans**

Find the `.wt__cell-p, .wt__cell-c` block (line ~1108):
```css
.wt__cell-p,
.wt__cell-c {
  border-radius: 4px;
  transition: background 120ms;
}
```

Replace with:
```css
.wt__cell-p,
.wt__cell-c {
  border-radius: 4px;
  transition: background 120ms;
  min-height: 1.75rem;
  display: flex;
  align-items: center;
}
```

Find the `.wt__num-val` block (line ~1224):
```css
.wt__num-val {
  color: var(--eb-text-muted);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}
```

Replace with:
```css
.wt__num-val {
  display: block;
  min-height: 1.1em;
  line-height: 1.4;
  color: var(--eb-text-muted);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}
```

- [ ] **Step 4: Run tests — flash tests should now pass**

```bash
cd frontend && npm test -- --reporter=verbose WeekCard.test.ts
```

Expected: flash class name test passes. `cursor-set` emit test and notes textarea test still fail.

---

## Task 4: Pill-hugging cursor for Type column (fi=0)

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` (`<template>` + `<style scoped>`)

- [ ] **Step 1: Add pill/dot cursor CSS classes**

In `<style scoped>`, add after the `.wt__type-pill--workout` block (line ~1193):

```css
/* ── Pill/dot cursor (fi=0 nav selection) ── */
.wt__type-pill--run.wt__type-pill--cursor {
  border: 1.5px solid #38bdf8;
  background: rgba(56, 189, 248, .12);
  box-shadow: 0 0 0 2px rgba(56, 189, 248, .15);
}

.wt__type-pill--workout.wt__type-pill--cursor {
  border: 1.5px solid #c8ff00;
  background: rgba(200, 255, 0, .10);
  box-shadow: 0 0 0 2px rgba(200, 255, 0, .12);
}

.wt__type-dot--cursor {
  border: 1.5px solid #38bdf8 !important;
  background: rgba(56, 189, 248, .12) !important;
  box-shadow: 0 0 0 2px rgba(56, 189, 248, .15);
}

/* Pill hover when cursor is on it */
.wt__type-pill--cursor:hover { opacity: 1; }
```

- [ ] **Step 2: Add cursor class to pill/dot elements in template**

In the Type cell template section (around line 645), there are three elements: editing pill, non-editing pill, and empty dot. Add `:class` with `wt__type-pill--cursor` / `wt__type-dot--cursor` when this cell is nav-selected.

**Editing pill** (inside `v-if="isEditingZone(slot.date, 'planned')"` branch):
```html
<button
  v-if="isEditingZone(slot.date, 'planned') && getEdit(slot.date)"
  class="wt__type-pill"
  :class="[
    `wt__type-pill--${getEdit(slot.date)!.sessionType.toLowerCase()}`,
    { 'wt__type-pill--cursor': isNavSelected(slot.date, 0) },
  ]"
  type="button"
  @click.stop="toggleSessionType(slot)"
>{{ getEdit(slot.date)!.sessionType === 'RUN' ? 'RUN' : 'WKT' }}</button>
```

**Non-editing pill** (inside `v-else-if="slot.planned[0]"` branch):
```html
<button
  v-else-if="slot.planned[0]"
  class="wt__type-pill"
  :class="[
    `wt__type-pill--${slot.planned[0].session_type.toLowerCase()}`,
    { 'wt__type-pill--cursor': isNavSelected(slot.date, 0) },
  ]"
  type="button"
  @click.stop="toggleSessionType(slot)"
>{{ slot.planned[0].session_type === 'RUN' ? 'RUN' : 'WKT' }}</button>
```

**Empty dot** (inside `v-else` branch):
```html
<span
  v-else
  class="wt__type-dot wt__type-dot--empty"
  :class="{ 'wt__type-dot--cursor': isNavSelected(slot.date, 0) }"
/>
```

- [ ] **Step 3: Run tests — confirm no regressions**

```bash
cd frontend && npm test -- --reporter=verbose WeekCard.test.ts
```

Expected: same pass/fail state as after Task 3 (no new regressions).

---

## Task 5: Inline row expansion — notes→textarea, auto-resize all planned fields

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` (`<script setup>` + `<template>` + `<style scoped>`)

- [ ] **Step 1: Remove height cap from `autoResizeTextarea`**

Find (line ~411):
```ts
function autoResizeTextarea(el: HTMLTextAreaElement) {
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  el.style.overflowY = el.scrollHeight > 120 ? 'auto' : 'hidden'
}
```

Replace with:
```ts
function autoResizeTextarea(el: HTMLTextAreaElement) {
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
  el.style.overflowY = 'hidden'
}
```

- [ ] **Step 2: Add auto-resize of all planned textareas after openEdit**

In `openEdit()`, after the `editingRows.set(slot.date, { ... })` call (line ~207) and after the existing `return` inside the `if (existing)` branch — add `nextTick` auto-resize for the planned zone in BOTH places.

For the **new row** path (after `editingRows.set(...)`), add at the end of `openEdit`:
```ts
if (zone === 'planned') {
  void nextTick(() => {
    const titleEl = document.querySelector<HTMLTextAreaElement>(
      `[data-field="title"][data-date="${slot.date}"]`
    )
    const notesEl = document.querySelector<HTMLTextAreaElement>(
      `[data-field="notes"][data-date="${slot.date}"]`
    )
    if (titleEl) autoResizeTextarea(titleEl)
    if (notesEl) autoResizeTextarea(notesEl)
  })
}
```

For the **existing row / same zone** path (inside `if (existing)` when `existing.activeZone === zone`):
```ts
if (existing) {
  if (existing.activeZone === zone) {
    existing.focusField = focusField;
    if (zone === 'planned') {
      void nextTick(() => {
        const titleEl = document.querySelector<HTMLTextAreaElement>(
          `[data-field="title"][data-date="${slot.date}"]`
        )
        const notesEl = document.querySelector<HTMLTextAreaElement>(
          `[data-field="notes"][data-date="${slot.date}"]`
        )
        if (titleEl) autoResizeTextarea(titleEl)
        if (notesEl) autoResizeTextarea(notesEl)
      })
    }
    return;
  }
  // ... rest of existing zone-switch logic
```

- [ ] **Step 3: Convert notes cell from `<input>` to `<textarea>` in template**

Find the notes cell template section (line ~704). The current `<input>` for notes:
```html
<input
  v-model="getEdit(slot.date)!.notes"
  v-autofocus="getEdit(slot.date)!.focusField === 'notes'"
  class="wt__input"
  data-field="notes"
  :data-date="slot.date"
  :placeholder="t('weekCard.notesPlaceholder')"
  @click.stop
  @input="onFieldInput(slot.date, slot)"
  @keydown="handleEditKeydown($event, 'notes', slot)"
/>
```

Replace with:
```html
<textarea
  v-model="getEdit(slot.date)!.notes"
  v-autofocus="getEdit(slot.date)!.focusField === 'notes'"
  class="wt__textarea"
  data-field="notes"
  :data-date="slot.date"
  :placeholder="t('weekCard.notesPlaceholder')"
  rows="1"
  style="overflow: hidden; resize: none;"
  @click.stop
  @input="onFieldInput(slot.date, slot); autoResizeTextarea($event.target as HTMLTextAreaElement)"
  @keydown="handleEditKeydown($event, 'notes', slot)"
/>
```

- [ ] **Step 4: Remove `white-space: nowrap` from `.wt__textarea`**

Find (line ~1270):
```css
.wt__textarea {
  resize: none;
  font-family: var(--eb-font-mono);
  line-height: 1.45;
  height: 1.75rem;
  box-sizing: border-box;
  overflow-x: hidden;
  white-space: nowrap;
}
```

Replace with:
```css
.wt__textarea {
  resize: none;
  font-family: var(--eb-font-mono);
  line-height: 1.45;
  height: 1.75rem;
  box-sizing: border-box;
  overflow-x: hidden;
  white-space: pre-wrap;
  word-break: break-word;
}
```

- [ ] **Step 5: Run tests — notes textarea test should now pass**

```bash
cd frontend && npm test -- --reporter=verbose WeekCard.test.ts
```

Expected: notes textarea tag test passes. Only `cursor-set` emit test still fails.

---

## Task 6: cursor-set emit from openEdit + update WeekCard emits

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` (`<script setup>`)

- [ ] **Step 1: Add `cursor-set` to emits declaration**

Find (line ~18):
```ts
const emit = defineEmits<{
  "navigate-out-next": [payload: { field: string; zone: "planned" | "completed" }]
  "navigate-out-prev": [payload: { field: string; zone: "planned" | "completed" }]
  "exit-edit": []
}>()
```

Replace with:
```ts
const emit = defineEmits<{
  "navigate-out-next": [payload: { field: string; zone: "planned" | "completed" }]
  "navigate-out-prev": [payload: { field: string; zone: "planned" | "completed" }]
  "exit-edit": []
  "cursor-set": [payload: { dayIdx: number; fieldIdx: number }]
}>()
```

- [ ] **Step 2: Emit `cursor-set` in `openEdit()`**

In `openEdit()`, map `focusField` to `fieldIdx` using `FIELD_BY_IDX`. Add the emit call right before the zone-guard checks (before `if (zone === "planned" && !canEditPlanned) return`), so it fires for both new and existing row paths:

Actually, emit it only when actually opening (not when same zone + same field is re-clicked and we just update focusField). The best place is at the END of `openEdit`, just before the `nextTick` block, after we've confirmed the open will proceed.

Add a helper at the top of `openEdit` to compute `dayIdx`:
```ts
const dayIdx = daySlots.value.findIndex(s => s.date === slot.date)
const fieldIdx = FIELD_BY_IDX.indexOf(focusField as typeof FIELD_BY_IDX[number])
```

Then emit at each exit point where editing is confirmed:

**In the `if (existing)` + same zone branch** (after `existing.focusField = focusField`):
```ts
if (existing.activeZone === zone) {
  existing.focusField = focusField;
  emit('cursor-set', { dayIdx, fieldIdx })
  // ... nextTick auto-resize ...
  return;
}
```

**In the `if (existing)` + zone-switch branch** (after `existing.activeZone = zone`):
```ts
existing.activeZone = zone;
existing.focusField = focusField;
emit('cursor-set', { dayIdx, fieldIdx })
return;
```

**In the new-row path** (after `editingRows.set(slot.date, { ... })`):
```ts
editingRows.set(slot.date, { ... });
emit('cursor-set', { dayIdx, fieldIdx })
// ... nextTick auto-resize ...
```

- [ ] **Step 3: Run tests — all WeekCard tests should pass**

```bash
cd frontend && npm test -- --reporter=verbose WeekCard.test.ts
```

Expected: all tests pass, including the new `cursor-set` emit test.

- [ ] **Step 4: Commit WeekCard changes**

```bash
git add frontend/components/training/WeekCard.vue frontend/components/training/WeekCard.test.ts
git commit -m "feat: zone-aware nav cursor, cell hover, flash, pill cursor, inline expansion, cursor-set emit"
```

---

## Task 7: AthleteView — cursor-set listener

**Files:**
- Modify: `frontend/components/views/dashboard/AthleteView.vue`

- [ ] **Step 1: Add `handleCursorSet` function**

In `<script setup>`, after `handleExitEdit()` (line ~129):

```ts
// ── Cursor sync from mouse clicks ──────────────────────────
function handleCursorSet(
  weekIdx: number,
  payload: { dayIdx: number; fieldIdx: number }
) {
  cursor.value = { weekIdx, dayIdx: payload.dayIdx, fieldIdx: payload.fieldIdx }
}
```

- [ ] **Step 2: Add `@cursor-set` listener to WeekCard in template**

Find the `<WeekCard>` element in the template (line ~186):
```html
<WeekCard
  v-for="(week, idx) in trainingStore.weeks"
  :key="week.id"
  :ref="(el) => { if (el && weekCardRefs.value) weekCardRefs.value[idx] = el as InstanceType<typeof WeekCard> }"
  :week="week"
  :active-cursor="cursorForWeek(idx)"
  @navigate-out-next="(p) => handleNavOut('next', idx, p)"
  @navigate-out-prev="(p) => handleNavOut('prev', idx, p)"
  @exit-edit="handleExitEdit"
/>
```

Replace with:
```html
<WeekCard
  v-for="(week, idx) in trainingStore.weeks"
  :key="week.id"
  :ref="(el) => { if (el && weekCardRefs.value) weekCardRefs.value[idx] = el as InstanceType<typeof WeekCard> }"
  :week="week"
  :active-cursor="cursorForWeek(idx)"
  @navigate-out-next="(p) => handleNavOut('next', idx, p)"
  @navigate-out-prev="(p) => handleNavOut('prev', idx, p)"
  @exit-edit="handleExitEdit"
  @cursor-set="(p) => handleCursorSet(idx, p)"
/>
```

- [ ] **Step 3: Run full test suite**

```bash
cd frontend && npm test
```

Expected: all tests pass (no AthleteView-specific tests for this event, but no regressions).

- [ ] **Step 4: Commit**

```bash
git add frontend/components/views/dashboard/AthleteView.vue
git commit -m "feat: sync cursor from mouse clicks via cursor-set in AthleteView"
```

---

## Task 8: CoachView — cursor-set listener

**Files:**
- Modify: `frontend/components/views/dashboard/CoachView.vue`

- [ ] **Step 1: Find the equivalent sections in CoachView**

CoachView has the same `gridNav` setup, `cursor`, `handleExitEdit`, and `WeekCard` template. Find the `handleExitEdit` function and the `<WeekCard>` element.

- [ ] **Step 2: Add `handleCursorSet` function**

After `handleExitEdit()` in CoachView's `<script setup>`:

```ts
function handleCursorSet(
  weekIdx: number,
  payload: { dayIdx: number; fieldIdx: number }
) {
  cursor.value = { weekIdx, dayIdx: payload.dayIdx, fieldIdx: payload.fieldIdx }
}
```

- [ ] **Step 3: Add `@cursor-set` listener to WeekCard in CoachView template**

Find the `<WeekCard>` element in CoachView. It will look similar to AthleteView. Add:
```html
@cursor-set="(p) => handleCursorSet(idx, p)"
```

- [ ] **Step 4: Run full test suite**

```bash
cd frontend && npm test
```

Expected: all tests pass, 0 TypeScript errors.

```bash
cd frontend && npx vue-tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/views/dashboard/CoachView.vue
git commit -m "feat: sync cursor from mouse clicks via cursor-set in CoachView"
```

- [ ] **Step 6: Push branch**

```bash
git push
```

---

## Self-Review

### Spec coverage check

| Spec requirement | Task |
|---|---|
| 1. cursor-set emit from openEdit | Task 6 |
| 1. Parents sync cursor.value | Task 7, 8 |
| 2. Zone-aware nav cursor (nav-selected-p / nav-selected-c) | Task 2 |
| 3. Pill-hugging cursor for fi=0 | Task 4 |
| 4. Cell-level ghost hover | Task 3 |
| 5. Zone-aware save flash (flash-ok-p / flash-ok-c) | Task 3 |
| 6. Min-height for empty cells | Task 3 |
| 7. Inline row expansion (all planned fields together) | Task 5 |
| 7. Auto-resize on open | Task 5 |
| 7. No white-space: nowrap on textarea | Task 5 |

All 9 spec requirements have a task.

### Type consistency check

- `cursor-set` payload type: `{ dayIdx: number; fieldIdx: number }` — used consistently in emit declaration (Task 6), AthleteView handler (Task 7), CoachView handler (Task 8).
- `navSelectedClass()` returns `string` — used in template `:class="[navSelectedClass(...), ...]"` array syntax — correct.
- `FIELD_BY_IDX.indexOf()` returns `-1` if not found — this only happens for `focusField = ''` (type pill) which never calls the emit path (type toggles go through `toggleTypeByDayIdx`, not `openEdit`). Safe.

### No placeholders — verified all steps have complete code.
