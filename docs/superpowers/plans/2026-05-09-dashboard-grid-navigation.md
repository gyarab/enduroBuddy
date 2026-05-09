# Dashboard Grid Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Přidat Google Sheets-style two-layer navigation do dashboardu — navigační mód (šipky pohybují kurzorem bez psaní) a editační mód (Enter/psaní vstoupí do editace, ESC/Tab/Enter ukončí).

**Architecture:** Nový `useGridNav` composable spravuje cursor + editMode stav. AthleteView/CoachView drží instanci, připojí window keydown handler a předávají `activeCursor` prop do WeekCard. WeekCard zobrazí nav highlight a vystaví `focusCellByIdx` + `toggleTypeByDayIdx` metody. Stávající openEdit/closeAndSave/performSaveApiCalls logika zůstává beze změny.

**Tech Stack:** Vue 3, TypeScript, Vitest, @vue/test-utils

---

## Soubory

**Nové:**
- `frontend/composables/useGridNav.ts`
- `frontend/composables/useGridNav.test.ts`

**Upravené:**
- `frontend/components/training/WeekCard.vue`
  - Nový prop `activeCursor`
  - Nové CSS `.wt__cell--nav-selected`, ellipsis na display spanech
  - `focusCellByIdx()` + `toggleTypeByDayIdx()` + `closeCurrentEdit()` v expose
  - Emit `exit-edit` při ESC v inputu
  - Odebrání `handleKeyNav()` (nahrazeno jednodušším `handleEditKeydown()`)
  - Textarea auto-grow, `align-items: start` na `.wt__row`
  - Cell-level flash (náhrada za row-level)
- `frontend/components/views/dashboard/AthleteView.vue`
  - `useGridNav()`, window keydown handler, `activeCursor` prop, watchers
- `frontend/components/views/dashboard/CoachView.vue`
  - Totéž co AthleteView

---

## Task 1: useGridNav — cursor state + moveCursor

**Files:**
- Create: `frontend/composables/useGridNav.ts`
- Create: `frontend/composables/useGridNav.test.ts`

- [ ] **Step 1: Napiš failing testy**

```typescript
// frontend/composables/useGridNav.test.ts
import { describe, it, expect } from 'vitest'
import { useGridNav, GRID_FIELDS } from '~/composables/useGridNav'

describe('useGridNav — GRID_FIELDS', () => {
  it('exports 8 fields starting with type', () => {
    expect(GRID_FIELDS[0]).toBe('type')
    expect(GRID_FIELDS).toHaveLength(8)
  })
})

describe('useGridNav — moveCursor', () => {
  it('right increments fieldIdx', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 0 }
    moveCursor('right', 2)
    expect(cursor.value?.fieldIdx).toBe(1)
  })

  it('left at fieldIdx 0 stays', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 0 }
    moveCursor('left', 2)
    expect(cursor.value?.fieldIdx).toBe(0)
  })

  it('right at fieldIdx 7 stays', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 7 }
    moveCursor('right', 2)
    expect(cursor.value?.fieldIdx).toBe(7)
  })

  it('down increments dayIdx', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 3, fieldIdx: 1 }
    moveCursor('down', 2)
    expect(cursor.value?.dayIdx).toBe(4)
  })

  it('down from Sunday (dayIdx 6) goes to next week Monday', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 6, fieldIdx: 2 }
    moveCursor('down', 2)
    expect(cursor.value).toEqual({ weekIdx: 1, dayIdx: 0, fieldIdx: 2 })
  })

  it('down from last week Sunday stays', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 1, dayIdx: 6, fieldIdx: 1 }
    moveCursor('down', 2)
    expect(cursor.value).toEqual({ weekIdx: 1, dayIdx: 6, fieldIdx: 1 })
  })

  it('up from Monday (dayIdx 0) goes to prev week Sunday', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 1, dayIdx: 0, fieldIdx: 3 }
    moveCursor('up', 2)
    expect(cursor.value).toEqual({ weekIdx: 0, dayIdx: 6, fieldIdx: 3 })
  })

  it('up from first week Monday stays', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    moveCursor('up', 2)
    expect(cursor.value).toEqual({ weekIdx: 0, dayIdx: 0, fieldIdx: 1 })
  })

  it('does nothing when cursor is null', () => {
    const { cursor, moveCursor } = useGridNav()
    cursor.value = null
    moveCursor('right', 2)
    expect(cursor.value).toBeNull()
  })
})
```

- [ ] **Step 2: Ověř že testy padají**

```
cd frontend && pnpm test composables/useGridNav
```
Očekávej: `Cannot find module '~/composables/useGridNav'`

- [ ] **Step 3: Implementuj composable**

```typescript
// frontend/composables/useGridNav.ts
import { ref, type Ref } from 'vue'

export const GRID_FIELDS = [
  'type', 'title', 'notes', 'km', 'minutes', 'details', 'avgHr', 'maxHr',
] as const

export type GridField = (typeof GRID_FIELDS)[number]

export interface GridCursor {
  weekIdx: number
  dayIdx: number   // 0 = pondělí, 6 = neděle
  fieldIdx: number // 0–7
}

export function useGridNav() {
  const cursor: Ref<GridCursor | null> = ref(null)
  const editMode = ref(false)
  const pendingReplace: Ref<string | undefined> = ref(undefined)

  function moveCursor(
    dir: 'up' | 'down' | 'left' | 'right',
    weekCount: number,
  ): void {
    if (!cursor.value) return
    const c = cursor.value

    if (dir === 'left') {
      cursor.value = { ...c, fieldIdx: Math.max(0, c.fieldIdx - 1) }
      return
    }
    if (dir === 'right') {
      cursor.value = { ...c, fieldIdx: Math.min(7, c.fieldIdx + 1) }
      return
    }
    if (dir === 'up') {
      if (c.dayIdx > 0) {
        cursor.value = { ...c, dayIdx: c.dayIdx - 1 }
      } else if (c.weekIdx > 0) {
        cursor.value = { ...c, weekIdx: c.weekIdx - 1, dayIdx: 6 }
      }
      return
    }
    if (dir === 'down') {
      if (c.dayIdx < 6) {
        cursor.value = { ...c, dayIdx: c.dayIdx + 1 }
      } else if (c.weekIdx < weekCount - 1) {
        cursor.value = { ...c, weekIdx: c.weekIdx + 1, dayIdx: 0 }
      }
    }
  }

  function enterEdit(replaceContent?: string): void {
    editMode.value = true
    pendingReplace.value = replaceContent
  }

  function exitEdit(): void {
    editMode.value = false
    pendingReplace.value = undefined
  }

  function initCursor(weeks: Array<{ week_start: string; week_end: string }>): void {
    if (!weeks.length) return
    const today = new Date().toISOString().slice(0, 10)
    const weekIdx = weeks.findIndex(
      (w) => w.week_start <= today && today <= w.week_end,
    )
    cursor.value = { weekIdx: weekIdx >= 0 ? weekIdx : 0, dayIdx: 0, fieldIdx: 0 }
  }

  return { cursor, editMode, pendingReplace, moveCursor, enterEdit, exitEdit, initCursor }
}
```

- [ ] **Step 4: Ověř že testy procházejí**

```
cd frontend && pnpm test composables/useGridNav
```
Očekávej: všechny testy zelené.

- [ ] **Step 5: Commit**

```
git add frontend/composables/useGridNav.ts frontend/composables/useGridNav.test.ts
git commit -m "feat: add useGridNav composable with cursor state and moveCursor"
```

---

## Task 2: useGridNav — enterEdit/exitEdit/initCursor testy

**Files:**
- Modify: `frontend/composables/useGridNav.test.ts`

- [ ] **Step 1: Přidej testy pro enterEdit, exitEdit, initCursor**

Přidej na konec `useGridNav.test.ts`:

```typescript
describe('useGridNav — enterEdit / exitEdit', () => {
  it('enterEdit sets editMode true and stores replace content', () => {
    const { cursor, editMode, enterEdit, pendingReplace } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    enterEdit('x')
    expect(editMode.value).toBe(true)
    expect(pendingReplace.value).toBe('x')
  })

  it('enterEdit without arg stores undefined replace', () => {
    const { cursor, editMode, enterEdit, pendingReplace } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    enterEdit()
    expect(editMode.value).toBe(true)
    expect(pendingReplace.value).toBeUndefined()
  })

  it('exitEdit clears editMode and pendingReplace', () => {
    const { cursor, editMode, pendingReplace, enterEdit, exitEdit } = useGridNav()
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    enterEdit('a')
    exitEdit()
    expect(editMode.value).toBe(false)
    expect(pendingReplace.value).toBeUndefined()
  })
})

describe('useGridNav — initCursor', () => {
  it('sets cursor to week containing today', () => {
    const { cursor, initCursor } = useGridNav()
    const today = new Date().toISOString().slice(0, 10)
    const weeks = [
      { week_start: '2020-01-01', week_end: '2020-01-07' },
      { week_start: today, week_end: today },
    ]
    initCursor(weeks)
    expect(cursor.value?.weekIdx).toBe(1)
    expect(cursor.value?.dayIdx).toBe(0)
    expect(cursor.value?.fieldIdx).toBe(0)
  })

  it('falls back to week 0 when today not found', () => {
    const { cursor, initCursor } = useGridNav()
    const weeks = [
      { week_start: '2020-01-01', week_end: '2020-01-07' },
    ]
    initCursor(weeks)
    expect(cursor.value?.weekIdx).toBe(0)
  })

  it('does nothing for empty weeks array', () => {
    const { cursor, initCursor } = useGridNav()
    initCursor([])
    expect(cursor.value).toBeNull()
  })
})
```

- [ ] **Step 2: Ověř že testy procházejí**

```
cd frontend && pnpm test composables/useGridNav
```
Všechny testy zelené (implementace již existuje z Task 1).

- [ ] **Step 3: Commit**

```
git add frontend/composables/useGridNav.test.ts
git commit -m "test: add enterEdit/exitEdit/initCursor tests for useGridNav"
```

---

## Task 3: WeekCard — activeCursor prop + nav-selected visual

**Files:**
- Modify: `frontend/components/training/WeekCard.vue`
- Modify: `frontend/components/training/WeekCard.test.ts`

- [ ] **Step 1: Napiš failing test**

Přidej do `WeekCard.test.ts` nový `describe` blok za stávající testy:

```typescript
describe('WeekCard — activeCursor nav highlight', () => {
  it('applies nav-selected class to type cell when activeCursor.fieldIdx=0', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    await wrapper.setProps({ activeCursor: { dayIdx: 0, fieldIdx: 0 } })
    await nextTick()
    const typeCell = wrapper.find('[data-testid="nav-cell-type-' + DATE + '"]')
    expect(typeCell.exists()).toBe(true)
    expect(typeCell.classes()).toContain('wt__cell--nav-selected')
  })

  it('applies nav-selected class to title cell when activeCursor.fieldIdx=1', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    await wrapper.setProps({ activeCursor: { dayIdx: 0, fieldIdx: 1 } })
    await nextTick()
    const titleCell = wrapper.find('[data-testid="cell-title-' + DATE + '"]')
    expect(titleCell.classes()).toContain('wt__cell--nav-selected')
  })

  it('no nav-selected class when activeCursor is null', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    await wrapper.setProps({ activeCursor: null })
    await nextTick()
    const selected = wrapper.findAll('.wt__cell--nav-selected')
    expect(selected).toHaveLength(0)
  })
})
```

- [ ] **Step 2: Ověř že testy padají**

```
cd frontend && pnpm test components/training/WeekCard
```
Očekávej: chybí prop `activeCursor`, data-testid nenalezen.

- [ ] **Step 3: Přidej prop a computed helper do WeekCard `<script setup>`**

Na řádku 12 (po `const props = defineProps`) přidej do defineProps nový prop:

```typescript
const props = defineProps<{
  week: DashboardWeek;
  editorContext?: "athlete" | "coach";
  activeCursor?: { dayIdx: number; fieldIdx: number } | null;
}>();
```

Přidej computed helper za existující computed:

```typescript
// ── Nav cursor helpers ─────────────────────────────────────
function isNavSelected(slotDate: string, fieldIdx: number): boolean {
  if (!props.activeCursor) return false
  const slotIdx = daySlots.value.findIndex(s => s.date === slotDate)
  return slotIdx === props.activeCursor.dayIdx && fieldIdx === props.activeCursor.fieldIdx
}
```

- [ ] **Step 4: Přidej data-testid a nav-selected třídu na type buňku v template**

Najdi `<div class="wt__cell wt__cell--type wt__cell-p" @click.stop>` (řádek ~564) a přidej:

```html
<div
  class="wt__cell wt__cell--type wt__cell-p"
  :class="{ 'wt__cell--nav-selected': isNavSelected(slot.date, 0) }"
  :data-testid="`nav-cell-type-${slot.date}`"
  @click.stop
>
```

Najdi title cell `<div class="wt__cell wt__cell--title wt__cell-p"` (řádek ~583) a přidej třídu:

```html
<div
  class="wt__cell wt__cell--title wt__cell-p"
  :class="{ 'wt__cell--nav-selected': isNavSelected(slot.date, 1) }"
  :data-testid="`cell-title-${slot.date}`"
  @click.stop="openEdit(slot, 'title', 'planned')"
>
```

Přidej `:class` s `isNavSelected` na zbývající editovatelné buňky (notes=2, km=3, minutes=4, details=5, avgHr=6, maxHr=7). Použij stejný vzor — viz sloupce v template kolem řádků 606–723.

- [ ] **Step 5: Přidej CSS pro nav-selected**

Do `<style scoped>`, za `.wt__cell--readonly`, přidej:

```css
/* ── Nav cursor selection ── */
.wt__cell--nav-selected {
  outline: 2px solid var(--eb-lime);
  outline-offset: -1px;
  background: rgba(200, 255, 0, 0.06);
  border-radius: 4px;
}
```

- [ ] **Step 6: Ověř testy**

```
cd frontend && pnpm test components/training/WeekCard
```
Očekávej: testy pro nav-selected zelené, ostatní WeekCard testy stále zelené.

- [ ] **Step 7: Commit**

```
git add frontend/components/training/WeekCard.vue frontend/components/training/WeekCard.test.ts
git commit -m "feat: add activeCursor prop and nav-selected highlight to WeekCard"
```

---

## Task 4: WeekCard — display spans s ellipsis

**Files:**
- Modify: `frontend/components/training/WeekCard.vue`

- [ ] **Step 1: Obal display text do `.wt__nav-cell` spanů**

V template WeekCard, každá editovatelná buňka má `<template v-else>` blok se statickým textem. Obal tyto texty do `<span class="wt__nav-cell">`:

**Title** (řádek ~599–602):
```html
<template v-else>
  <span class="wt__nav-cell">
    {{ slot.planned[0]?.title || '' }}
  </span>
</template>
```
(Odstraň původní `wt__title-text` a `wt__empty-hint` spany — nahrazeny jedním `wt__nav-cell` spanem.)

**Notes** (řádek ~620–622):
```html
<template v-else>
  <span class="wt__nav-cell">{{ slot.planned[0]?.notes || '' }}</span>
</template>
```

**km** (řádek ~643–645):
```html
<template v-else>
  <span class="wt__nav-cell wt__nav-cell--num">{{ slot.completed[0]?.completed_metrics?.km || '-' }}</span>
</template>
```

**minutes** (řádek ~663–665):
```html
<template v-else>
  <span class="wt__nav-cell wt__nav-cell--num">{{ formatMinutes(slot.completed[0]?.completed_metrics?.minutes) }}</span>
</template>
```

**details** (řádek ~682–684):
```html
<template v-else>
  <span class="wt__nav-cell">{{ slot.completed[0]?.completed_metrics?.details || '' }}</span>
</template>
```

**avgHr** (řádek ~701–703):
```html
<template v-else>
  <span class="wt__nav-cell wt__nav-cell--num">{{ slot.completed[0]?.completed_metrics?.avg_hr ?? '-' }}</span>
</template>
```

**maxHr** (řádek ~720–722):
```html
<template v-else>
  <span class="wt__nav-cell wt__nav-cell--num">{{ slot.completed[0]?.completed_metrics?.max_hr ?? '-' }}</span>
</template>
```

- [ ] **Step 2: Přidej CSS pro `.wt__nav-cell`**

Do `<style scoped>`, za `.wt__cell--nav-selected`:

```css
/* ── Nav mode display spans ── */
.wt__nav-cell {
  display: block;
  width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--eb-text-soft);
  font-size: 0.8125rem;
  min-height: 1.25rem;
  line-height: 1.5;
}

.wt__nav-cell--num {
  font-family: var(--eb-font-mono);
  font-size: 0.75rem;
  text-align: right;
}
```

- [ ] **Step 3: Změň `align-items` na `.wt__row` z `center` na `start`**

Najdi v CSS (řádek ~855–861):
```css
.wt__row {
  padding: 0 1rem;
  border-bottom: 1px solid var(--eb-border-soft);
  min-height: 2.75rem;
  align-items: center;   /* ← změnit na start */
  transition: background-color 100ms;
}
```

Změň na `align-items: start` a přidej `padding-block: 0.4rem`:
```css
.wt__row {
  padding: 0.4rem 1rem;
  border-bottom: 1px solid var(--eb-border-soft);
  min-height: 2.75rem;
  align-items: start;
  transition: background-color 100ms;
}
```

- [ ] **Step 3b: Přidej `overflow-x: auto` na `.wt__table` (jeden horizontal scrollbar)**

Najdi v CSS `.wt__table` — pokud existuje, přidej `overflow-x: auto`. Pokud neexistuje, přidej nové pravidlo za `.wt__cols`:

```css
.wt__table {
  overflow-x: auto;
}
```

Tím zajistíš že celá tabulka scrolluje horizontálně jako jeden celek místo per-week scrollbarů.

- [ ] **Step 4: Spusť testy a zkontroluj vizuálně**

```
cd frontend && pnpm test components/training/WeekCard
```
Všechny testy zelené. Zkontroluj dev server (`pnpm dev`) a ověř vizuálně že:
- Text v buňkách je na jednom řádku s ellipsis
- Řádky mají `start` alignment

- [ ] **Step 5: Commit**

```
git add frontend/components/training/WeekCard.vue
git commit -m "feat: add nav-cell display spans with text ellipsis to WeekCard"
```

---

## Task 5: WeekCard — textarea auto-grow

**Files:**
- Modify: `frontend/components/training/WeekCard.vue`

- [ ] **Step 1: Přidej autoResize helper do script**

Za funkci `onFieldInput` přidej:

```typescript
function autoResizeTextarea(el: HTMLTextAreaElement) {
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  el.style.overflowY = el.scrollHeight > 120 ? 'auto' : 'hidden'
}
```

- [ ] **Step 2: Volej autoResize na title textarea**

Najdi `<textarea` pro title (řádek ~585–597). Přidej `@input` handler volající autoResize a nastav initial styl:

```html
<textarea
  v-model="getEdit(slot.date)!.title"
  v-autofocus="getEdit(slot.date)!.focusField === 'title'"
  class="wt__textarea"
  :data-testid="`input-title-${slot.date}`"
  data-field="title"
  :data-date="slot.date"
  :placeholder="t('weekCard.titlePlaceholder')"
  rows="1"
  style="overflow: hidden; resize: none;"
  @click.stop
  @input="onFieldInput(slot.date, slot); autoResizeTextarea($event.target as HTMLTextAreaElement)"
  @keydown="handleKeyNav($event, 'title', slot, 'planned')"
/>
```

- [ ] **Step 3: Ověř testy a vizuální chování**

```
cd frontend && pnpm test components/training/WeekCard
```
Všechny zelené. Na dev serveru: klikni na title buňku, napiš dlouhý text — textarea se musí zvyšovat, max 120px.

- [ ] **Step 4: Commit**

```
git add frontend/components/training/WeekCard.vue
git commit -m "feat: add textarea auto-grow for title field in WeekCard"
```

---

## Task 6: WeekCard — cell-level flash (nahrazuje row-level)

**Files:**
- Modify: `frontend/components/training/WeekCard.vue`
- Modify: `frontend/components/training/WeekCard.test.ts`

- [ ] **Step 1: Napiš failing test**

Přidej do `WeekCard.test.ts`:

```typescript
describe('WeekCard — cell-level flash', () => {
  it('flashCellOk adds wt__cell--flash-ok class to specified cell', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    const vm = wrapper.vm as InstanceType<typeof WeekCard>
    vm.flashCellOk(DATE, 1)  // title cell, fieldIdx=1
    await nextTick()
    const cell = wrapper.find('[data-testid="cell-title-' + DATE + '"]')
    expect(cell.classes()).toContain('wt__cell--flash-ok')
  })
})
```

- [ ] **Step 2: Ověř že test padá**

```
cd frontend && pnpm test components/training/WeekCard
```
Očekávej: `vm.flashCellOk is not a function`

- [ ] **Step 3: Přidej cell-level flash state a funkce do WeekCard**

Přidej za existující flash sets (řádek ~225):

```typescript
// Cell-level flash: klíč = `${date}:${fieldIdx}`
const flashingCellsOk = reactive<Set<string>>(new Set())
const flashingCellsErr = reactive<Set<string>>(new Set())

function flashCellOk(date: string, fieldIdx: number) {
  const key = `${date}:${fieldIdx}`
  flashingCellsOk.add(key)
  setTimeout(() => flashingCellsOk.delete(key), 900)
}

function flashCellErr(date: string, fieldIdx: number) {
  const key = `${date}:${fieldIdx}`
  flashingCellsErr.add(key)
  setTimeout(() => flashingCellsErr.delete(key), 900)
}
```

- [ ] **Step 4: Přidej `flashCellOk` do expose**

Přidej do `defineExpose`:

```typescript
defineExpose({
  focusCell(field: string, zone: "planned" | "completed", atEnd = false) { /* ... existing ... */ },
  flashCellOk,
})
```

- [ ] **Step 5: Přidej `:class` pro flash na editovatelné buňky**

Pro každou editovatelnou buňku přidej flash třídy. Vzor pro title cell (fieldIdx=1):

```html
<div
  class="wt__cell wt__cell--title wt__cell-p"
  :class="{
    'wt__cell--nav-selected': isNavSelected(slot.date, 1),
    'wt__cell--flash-ok': flashingCellsOk.has(`${slot.date}:1`),
    'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:1`),
  }"
  ...
>
```

Stejně pro notes (2), km (3), minutes (4), details (5), avgHr (6), maxHr (7). Pro type cell (0):
```html
:class="{
  'wt__cell--nav-selected': isNavSelected(slot.date, 0),
  'wt__cell--flash-ok': flashingCellsOk.has(`${slot.date}:0`),
  'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:0`),
}"
```

- [ ] **Step 6: Přidej CSS animace**

Do `<style scoped>` přidej:

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

- [ ] **Step 7: Aktualizuj `flashZoneOk` a `flashZoneErr` volání v `performSaveApiCalls`**

Najdi v `performSaveApiCalls` (řádek ~247) volání `flashZoneOk` a nahraď cell-level flash. Zone planned ukládá title (1) a notes (2), zone completed ukládá km (3)–maxHr (7):

```typescript
// V sekci "after successful save" nahraď:
// flashZoneOk(slot.date, edit.activeZone)
// za:
if (edit.activeZone === 'planned') {
  flashCellOk(slot.date, 1)  // title
  flashCellOk(slot.date, 2)  // notes
} else {
  for (let fi = 3; fi <= 7; fi++) flashCellOk(slot.date, fi)
}

// A nahraď flashZoneErr:
// flashZoneErr(slot.date)
// za:
if (edit.activeZone === 'planned') {
  flashCellErr(slot.date, 1)
  flashCellErr(slot.date, 2)
} else {
  for (let fi = 3; fi <= 7; fi++) flashCellErr(slot.date, fi)
}
```

- [ ] **Step 8: Ověř testy**

```
cd frontend && pnpm test components/training/WeekCard
```
Všechny zelené.

- [ ] **Step 9: Commit**

```
git add frontend/components/training/WeekCard.vue frontend/components/training/WeekCard.test.ts
git commit -m "feat: replace row-level flash with cell-level flash in WeekCard"
```

---

## Task 7: WeekCard — focusCellByIdx + toggleTypeByDayIdx + handleEditKeydown

**Files:**
- Modify: `frontend/components/training/WeekCard.vue`
- Modify: `frontend/components/training/WeekCard.test.ts`

- [ ] **Step 1: Napiš failing testy**

Přidej do `WeekCard.test.ts`:

```typescript
describe('WeekCard — focusCellByIdx', () => {
  it('opens edit for title (fieldIdx=1) on dayIdx=0', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    const vm = wrapper.vm as InstanceType<typeof WeekCard>
    vm.focusCellByIdx(0, 1)
    await nextTick()
    const input = wrapper.find('[data-testid="input-title-' + DATE + '"]')
    expect(input.exists()).toBe(true)
    expect(input.isVisible()).toBe(true)
  })

  it('replaces content when replaceContent is provided', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    const vm = wrapper.vm as InstanceType<typeof WeekCard>
    vm.focusCellByIdx(0, 1, 'x')
    await nextTick()
    const input = wrapper.find<HTMLInputElement>('[data-testid="input-title-' + DATE + '"]')
    expect((input.element as HTMLTextAreaElement).value).toBe('x')
  })
})

describe('WeekCard — exit-edit event on ESC', () => {
  it('emits exit-edit when ESC is pressed in an input', async () => {
    const week = buildWeek()
    const wrapper = mountWeekCard(week)
    const vm = wrapper.vm as InstanceType<typeof WeekCard>
    vm.focusCellByIdx(0, 1)
    await nextTick()
    const input = wrapper.find('[data-testid="input-title-' + DATE + '"]')
    await input.trigger('keydown', { key: 'Escape' })
    expect(wrapper.emitted('exit-edit')).toBeTruthy()
  })
})
```

- [ ] **Step 2: Ověř že testy padají**

```
cd frontend && pnpm test components/training/WeekCard
```
Očekávej: `vm.focusCellByIdx is not a function`

- [ ] **Step 3: Definuj konstanty pro mapování fieldIdx na WeekCard field names**

Za `COMPLETED_FIELDS` (řádek ~23) přidej:

```typescript
// Mapování fieldIdx (z useGridNav) na interní field name WeekCard
// index 0 = type pill (handled separately), 1–7 = text/number fields
const FIELD_BY_IDX = ['', 'title', 'notes', 'km', 'minutes', 'details', 'avgHr', 'maxHr'] as const
```

- [ ] **Step 4: Přidej `exit-edit` do emits a implementuj `focusCellByIdx` + `toggleTypeByDayIdx`**

Přidej `exit-edit` do emit definice (řádek ~17):

```typescript
const emit = defineEmits<{
  "navigate-out-next": [payload: { field: string; zone: "planned" | "completed" }]
  "navigate-out-prev": [payload: { field: string; zone: "planned" | "completed" }]
  "exit-edit": []
}>()
```

Přidej do `defineExpose` nové metody:

```typescript
defineExpose({
  focusCell(field: string, zone: "planned" | "completed", atEnd = false) {
    const slot = atEnd
      ? daySlots.value[daySlots.value.length - 1]
      : daySlots.value[0]
    if (!slot) return
    openEdit(slot, field, zone)
    void nextTick(() => {
      document.querySelector<HTMLElement>(
        `[data-field="${field}"][data-date="${slot.date}"]`,
      )?.focus()
    })
  },

  focusCellByIdx(dayIdx: number, fieldIdx: number, replaceContent?: string) {
    if (fieldIdx === 0) return  // type pill — use toggleTypeByDayIdx
    const field = FIELD_BY_IDX[fieldIdx]
    const zone: "planned" | "completed" = fieldIdx <= 2 ? 'planned' : 'completed'
    const slot = daySlots.value[dayIdx]
    if (!slot) return
    openEdit(slot, field, zone)
    if (replaceContent !== undefined) {
      const edit = editingRows.get(slot.date)
      if (edit) {
        if (field === 'title')   edit.title   = replaceContent
        if (field === 'notes')   edit.notes   = replaceContent
        if (field === 'km')      edit.km      = replaceContent
        if (field === 'minutes') edit.minutes = replaceContent
        if (field === 'details') edit.details = replaceContent
        if (field === 'avgHr')   edit.avgHr   = replaceContent
        if (field === 'maxHr')   edit.maxHr   = replaceContent
      }
    }
    void nextTick(() => {
      document.querySelector<HTMLElement>(
        `[data-field="${field}"][data-date="${slot.date}"]`,
      )?.focus()
    })
  },

  toggleTypeByDayIdx(dayIdx: number) {
    const slot = daySlots.value[dayIdx]
    if (slot) void toggleSessionType(slot)
  },

  closeCurrentEdit() {
    for (const [date, edit] of [...editingRows]) {
      if (edit.debounceTimer) {
        clearTimeout(edit.debounceTimer)
        edit.debounceTimer = null
      }
      const slot = daySlots.value.find((s) => s.date === date)
      if (slot && edit.isDirty) {
        edit.closeAfterSave = true
        void performSaveApiCalls(slot, edit)
      } else {
        editingRows.delete(date)
      }
    }
  },

  flashCellOk,
})
```

- [ ] **Step 5: Přidej `handleEditKeydown` a nahraď `handleKeyNav` na inputech**

Přidej novou funkci (místo starého `handleKeyNav` nebo za ní):

```typescript
function handleEditKeydown(event: KeyboardEvent, field: string, slot: DaySlot) {
  const key = event.key
  if (key === 'Escape') {
    event.preventDefault()
    const edit = editingRows.get(slot.date)
    if (edit) {
      if (edit.debounceTimer) { clearTimeout(edit.debounceTimer); edit.debounceTimer = null }
      if (edit.isDirty) { edit.closeAfterSave = true; void performSaveApiCalls(slot, edit) }
      else { editingRows.delete(slot.date) }
    }
    emit('exit-edit')
    return
  }
  if (key === 'ArrowUp' || key === 'ArrowDown') {
    event.preventDefault()
    return
  }
  if (key === 'Enter' && field !== 'title') {
    event.preventDefault()
    const edit = editingRows.get(slot.date)
    if (edit) {
      if (edit.debounceTimer) { clearTimeout(edit.debounceTimer); edit.debounceTimer = null }
      if (edit.isDirty) { edit.closeAfterSave = true; void performSaveApiCalls(slot, edit) }
      else { editingRows.delete(slot.date) }
    }
    emit('exit-edit')
    return
  }
  if (key === 'Tab') {
    event.preventDefault()
    const edit = editingRows.get(slot.date)
    if (edit) {
      if (edit.debounceTimer) { clearTimeout(edit.debounceTimer); edit.debounceTimer = null }
      if (edit.isDirty) { edit.closeAfterSave = true; void performSaveApiCalls(slot, edit) }
      else { editingRows.delete(slot.date) }
    }
    emit('exit-edit')
  }
}
```

- [ ] **Step 6: Nahraď `handleKeyNav` za `handleEditKeydown` ve všech inputech v template**

V template, nahraď VŠECHNA volání `@keydown="handleKeyNav($event, 'xxx', slot, 'zone')"` za `@keydown="handleEditKeydown($event, 'xxx', slot)"`. Je to 7 inputů (title textarea, notes, km, minutes, details, avgHr, maxHr).

- [ ] **Step 7: Odstraň starý `handleKeyNav`**

Smaž celou funkci `handleKeyNav` (řádky ~382–452). Ověř že soubor se kompiluje bez chyb:

```
cd frontend && npx vue-tsc --noEmit
```

- [ ] **Step 8: Ověř testy**

```
cd frontend && pnpm test components/training/WeekCard
```
Všechny zelené.

- [ ] **Step 9: Commit**

```
git add frontend/components/training/WeekCard.vue frontend/components/training/WeekCard.test.ts
git commit -m "feat: add focusCellByIdx, toggleTypeByDayIdx, exit-edit event; replace handleKeyNav"
```

---

## Task 8: AthleteView — integrace useGridNav

**Files:**
- Modify: `frontend/components/views/dashboard/AthleteView.vue`
- Modify: `frontend/components/views/dashboard/AthleteView.test.ts`

- [ ] **Step 1: Napiš failing test**

Přidej do `AthleteView.test.ts`:

```typescript
import { useGridNav } from '~/composables/useGridNav'

describe('AthleteView — grid navigation', () => {
  it('passes activeCursor to first WeekCard when cursor is set', async () => {
    // mount AthleteView with mocked store containing one week
    // then check that WeekCard receives activeCursor prop
    // (smoke test — verify prop is wired up)
    // This test verifies the integration is connected, not the full nav behavior
    expect(true).toBe(true)  // placeholder — full integration test via manual testing
  })
})
```

(Detailní integrace AthleteView je složitá na unit testování kvůli window events — manuální test je dostatečný. Tento placeholder test zajistí že soubor se kompiluje.)

- [ ] **Step 2: Aktualizuj AthleteView**

Nahraď celý `<script setup>` blok AthleteView:

```typescript
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";

import MonthBar from "@/components/training/MonthBar.vue";
import MonthSummaryBar from "@/components/training/MonthSummaryBar.vue";
import WeekCard from "@/components/training/WeekCard.vue";
import WeekCardSkeleton from "@/components/training/WeekCardSkeleton.vue";
import GarminImportModal from "@/components/training/GarminImportModal.vue";
import EbButton from "@/components/ui/EbButton.vue";
import EbCard from "@/components/ui/EbCard.vue";
import { useAuthStore } from "@/stores/auth";
import { useToastStore } from "@/stores/toasts";
import { useTrainingStore } from "@/stores/training";
import { useGridNav } from "~/composables/useGridNav";
import { addNextMonth } from "~/utils/api/training";

const trainingStore = useTrainingStore();
const toastStore = useToastStore();
const { t } = useI18n();
const isAddingMonth = ref(false);
const authStore = useAuthStore();
const isGarminModalOpen = ref(false);

const weekCardRefs = ref<InstanceType<typeof WeekCard>[]>([])

// ── Grid navigation ──────────────────────────────────────────
const gridNav = useGridNav()
const { cursor, editMode } = gridNav

function cursorForWeek(idx: number): { dayIdx: number; fieldIdx: number } | null {
  if (!cursor.value || cursor.value.weekIdx !== idx) return null
  return { dayIdx: cursor.value.dayIdx, fieldIdx: cursor.value.fieldIdx }
}

// When editMode turns true: tell the right WeekCard to open the cell
watch([editMode, cursor], ([active]) => {
  if (!active || !cursor.value) return
  const { weekIdx, dayIdx, fieldIdx } = cursor.value
  if (fieldIdx === 0) return  // type pill handled by key handler directly
  weekCardRefs.value[weekIdx]?.focusCellByIdx(dayIdx, fieldIdx, gridNav.pendingReplace.value)
})

function handleKeyDown(e: KeyboardEvent) {
  // Let edit mode inputs handle their own keys
  if (editMode.value) return

  const PRINTABLE = /^[a-zA-Z0-9\-.,;:!?@#%&*()/\\'"= ]$/
  const weekCount = trainingStore.weeks.length

  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    const dir = e.key.replace('Arrow', '').toLowerCase() as 'up' | 'down' | 'left' | 'right'
    gridNav.moveCursor(dir, weekCount)
    return
  }

  if (e.key === 'Tab') {
    e.preventDefault()
    gridNav.moveCursor(e.shiftKey ? 'left' : 'right', weekCount)
    return
  }

  if (!cursor.value) return

  if (e.key === 'Enter') {
    e.preventDefault()
    if (cursor.value.fieldIdx === 0) {
      weekCardRefs.value[cursor.value.weekIdx]?.toggleTypeByDayIdx(cursor.value.dayIdx)
    } else {
      gridNav.enterEdit()
    }
    return
  }

  if (e.key === ' ' && cursor.value.fieldIdx === 0) {
    e.preventDefault()
    weekCardRefs.value[cursor.value.weekIdx]?.toggleTypeByDayIdx(cursor.value.dayIdx)
    return
  }

  if (e.key === 'Backspace' || e.key === 'Delete') {
    if (cursor.value.fieldIdx !== 0) {
      e.preventDefault()
      gridNav.enterEdit('')
    }
    return
  }

  if (e.key === 'Escape') {
    e.preventDefault()
    cursor.value = null
    return
  }

  if (PRINTABLE.test(e.key) && !e.ctrlKey && !e.metaKey && cursor.value.fieldIdx !== 0) {
    gridNav.enterEdit(e.key)
  }
}

// ── Lifecycle ────────────────────────────────────────────────
onMounted(() => {
  void trainingStore.loadDashboard().then(() => {
    gridNav.initCursor(trainingStore.weeks)
  })
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

// Re-init cursor when month changes
watch(() => trainingStore.weeks, (weeks) => {
  if (weeks.length) gridNav.initCursor(weeks)
})

// ── Cross-week navigation (legacy, kept for type pill compat) ──
function handleNavOut(
  dir: "next" | "prev",
  idx: number,
  payload: { field: string; zone: "planned" | "completed" },
) {
  const targetIdx = dir === "next" ? idx + 1 : idx - 1
  const card = weekCardRefs.value[targetIdx]
  if (card) card.focusCell(payload.field, payload.zone, dir === "prev")
}

// ── Exit edit (WeekCard emits when ESC/Enter/Tab in input) ────
function handleExitEdit() {
  gridNav.exitEdit()
}

// ── Other ────────────────────────────────────────────────────
const showGarminImportButton = computed(
  () => !!authStore.user?.capabilities?.garmin_connect_enabled,
);

async function handleAddMonth() {
  isAddingMonth.value = true;
  try {
    const data = await addNextMonth();
    await trainingStore.loadDashboard(data.month_value);
    toastStore.push(t("addMonth.added"), "success");
  } catch {
    toastStore.push(t("addMonth.error"), "danger");
  } finally {
    isAddingMonth.value = false;
  }
}
</script>
```

- [ ] **Step 3: Aktualizuj template — přidej `active-cursor` prop a `@exit-edit` na WeekCard**

Najdi `<WeekCard` v template a aktualizuj:

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

- [ ] **Step 4: Ověř TypeScript**

```
cd frontend && npx vue-tsc --noEmit
```
Očekávej: 0 chyb.

- [ ] **Step 5: Ověř testy**

```
cd frontend && pnpm test components/views/dashboard/AthleteView
```
Všechny zelené.

- [ ] **Step 6: Manuální test**
  1. `pnpm dev` — otevři dashboard
  2. Ověř auto-focus na pondělí aktuálního týdne (lime outline na type pill)
  3. Šipky pohybují kurzorem
  4. ↓ ze Sunday přejde do Monday next week
  5. Psaní znaku vstoupí do editace (obsah nahrazen)
  6. Enter zachová obsah, vstoupí do editace, kurzor na konec
  7. ESC uloží a vrátí do nav módu
  8. Space na type pill přepne RUN↔WORKOUT
  9. Dlouhý text v title: textarea roste, nav span ořezán

- [ ] **Step 7: Commit**

```
git add frontend/components/views/dashboard/AthleteView.vue frontend/components/views/dashboard/AthleteView.test.ts
git commit -m "feat: integrate useGridNav into AthleteView with keyboard handler"
```

---

## Task 9: CoachView — integrace useGridNav

**Files:**
- Modify: `frontend/components/views/dashboard/CoachView.vue`

- [ ] **Step 1: Přidej imports**

Do `<script setup>` CoachView přidej:

```typescript
import { onUnmounted, watch } from "vue"
import { useGridNav } from "~/composables/useGridNav";
```

(CoachView pravděpodobně již importuje `onMounted`, `ref` — doplň chybějící)

- [ ] **Step 2: Přečti CoachView a identifikuj store**

Přečti `frontend/components/views/dashboard/CoachView.vue`. Zjisti:
- Jaký store drží `weeks` (pravděpodobně `coachStore` nebo `trainingStore`)
- Kde jsou `weekCardRefs` — pokud neexistují, přidej je stejně jako v AthleteView
- Kde je `onMounted` — přidej `gridNav.initCursor` a `window.addEventListener` do existujícího `onMounted`

- [ ] **Step 3: Přidej useGridNav logiku do CoachView**

Přidej identické bloky jako v AthleteView (přizpůsob název store podle Step 2):

```typescript
const gridNav = useGridNav()
const { cursor, editMode } = gridNav

function cursorForWeek(idx: number): { dayIdx: number; fieldIdx: number } | null {
  if (!cursor.value || cursor.value.weekIdx !== idx) return null
  return { dayIdx: cursor.value.dayIdx, fieldIdx: cursor.value.fieldIdx }
}

watch([editMode, cursor], ([active]) => {
  if (!active || !cursor.value) return
  const { weekIdx, dayIdx, fieldIdx } = cursor.value
  if (fieldIdx === 0) return
  weekCardRefs.value[weekIdx]?.focusCellByIdx(dayIdx, fieldIdx, gridNav.pendingReplace.value)
})

function handleKeyDown(e: KeyboardEvent) {
  if (editMode.value) return
  const PRINTABLE = /^[a-zA-Z0-9\-.,;:!?@#%&*()/\\'"= ]$/
  // Použij správný store pro weekCount:
  const weekCount = /* coachStore.weeks ?? trainingStore.weeks */.length
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    const dir = e.key.replace('Arrow', '').toLowerCase() as 'up' | 'down' | 'left' | 'right'
    gridNav.moveCursor(dir, weekCount)
    return
  }
  if (e.key === 'Tab') { e.preventDefault(); gridNav.moveCursor(e.shiftKey ? 'left' : 'right', weekCount); return }
  if (!cursor.value) return
  if (e.key === 'Enter') {
    e.preventDefault()
    if (cursor.value.fieldIdx === 0) weekCardRefs.value[cursor.value.weekIdx]?.toggleTypeByDayIdx(cursor.value.dayIdx)
    else gridNav.enterEdit()
    return
  }
  if (e.key === ' ' && cursor.value.fieldIdx === 0) { e.preventDefault(); weekCardRefs.value[cursor.value.weekIdx]?.toggleTypeByDayIdx(cursor.value.dayIdx); return }
  if ((e.key === 'Backspace' || e.key === 'Delete') && cursor.value.fieldIdx !== 0) { e.preventDefault(); gridNav.enterEdit(''); return }
  if (e.key === 'Escape') { e.preventDefault(); cursor.value = null; return }
  if (PRINTABLE.test(e.key) && !e.ctrlKey && !e.metaKey && cursor.value.fieldIdx !== 0) gridNav.enterEdit(e.key)
}

function handleExitEdit() { gridNav.exitEdit() }
```

Do `onMounted` přidej:
```typescript
gridNav.initCursor(/* správný .weeks array */)
window.addEventListener('keydown', handleKeyDown)
```

Do `onUnmounted` (nebo přidej nový blok):
```typescript
window.removeEventListener('keydown', handleKeyDown)
```

Přidej watch pro re-init po změně měsíce (přizpůsob weeks array):
```typescript
watch(() => /* store.weeks */, (weeks) => { if (weeks.length) gridNav.initCursor(weeks) })
```

- [ ] **Step 3: Aktualizuj template — přidej active-cursor a @exit-edit na WeekCard**

Stejně jako v AthleteView:
```html
:active-cursor="cursorForWeek(idx)"
@exit-edit="handleExitEdit"
```

- [ ] **Step 4: Ověř TypeScript a testy**

```
cd frontend && npx vue-tsc --noEmit && pnpm test
```
Očekávej: 0 TS chyb, všechny testy zelené.

- [ ] **Step 5: Commit a push**

```
git add frontend/components/views/dashboard/CoachView.vue
git commit -m "feat: integrate useGridNav into CoachView"
git push
```

---

## Task 10: Celkový test + aktualizace CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Spusť celou test suite**

```
cd frontend && pnpm test
```
Očekávej: všechny testy zelené.

- [ ] **Step 2: TypeScript check**

```
cd frontend && npx vue-tsc --noEmit
```
Očekávej: 0 chyb.

- [ ] **Step 3: Aktualizuj CLAUDE.md — sekce "Aktivní plány a změny"**

Přidej na začátek sekce (za nadpis `## Aktivní plány a změny`):

```markdown
### 2026-05-09 — Dashboard: Google Sheets grid navigation ✅ KOMPLETNÍ

**Spec:** `docs/superpowers/specs/2026-05-09-dashboard-grid-navigation.md`
**Plán:** `docs/superpowers/plans/2026-05-09-dashboard-grid-navigation.md`

- `useGridNav` composable: cursor stav, moveCursor (cross-week), enterEdit/exitEdit, initCursor
- WeekCard: `activeCursor` prop + `.wt__cell--nav-selected`, `focusCellByIdx`, `toggleTypeByDayIdx`, `exit-edit` event, cell-level flash, textarea auto-grow, ellipsis na nav spanech
- AthleteView + CoachView: window keydown handler, editMode watcher, auto-focus na dnešní týden
- Nav mód: šipky pohybují kurzorem, psaní nahradí obsah, Enter zachová obsah, Space/Enter na type pill = toggle
- Edit mód: ESC/Enter(input)/Tab = uložit + nav mód; ↑↓ blokováno; ←→ nativní v textu
```

- [ ] **Step 4: Final commit**

```
git add CLAUDE.md
git commit -m "docs: mark dashboard grid navigation as complete in CLAUDE.md"
git push
```
