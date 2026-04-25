# WeekCard Zone Editing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rozdělit inline editování WeekCard na dvě nezávislé zóny (planned / completed), které se vzájemně vylučují, vizuálně odlišit proporce 3/5 : 2/5, přidat plánované km do summary row a optimalizovat mobilní layout.

**Architecture:** Jediný dotčený soubor je `frontend/components/training/WeekCard.vue`. Do `RowEdit` přidáme pole `activeZone: "planned" | "completed"`, `openEdit` dostane třetí parametr `zone` a řídí mutual exclusion. CSS používá třídy `.wt__cell-p` / `.wt__cell-c` na buňkách a `:has()` pseudoclass pro hover efekty zón.

**Tech Stack:** Vue 3 + TypeScript, Vitest + @vue/test-utils, CSS Grid, Pinia

---

## Soubory

| Soubor | Akce |
|--------|------|
| `frontend/components/training/WeekCard.vue` | Modify — veškeré změny |
| `frontend/components/training/WeekCard.test.ts` | Create — nové testy zone switching + summary |

---

### Task 1: Failing testy pro zone switching

**Files:**
- Create: `frontend/components/training/WeekCard.test.ts`

- [ ] **Krok 1: Napiš failing test file**

```ts
// frontend/components/training/WeekCard.test.ts
import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DashboardWeek } from "~/utils/api/training";
import WeekCard from "./WeekCard.vue";
import { useAuthStore } from "@/stores/auth";
import { useTrainingStore } from "@/stores/training";

const DATE = "2026-05-01";

function buildWeek(overrides: Partial<DashboardWeek> = {}): DashboardWeek {
  return {
    id: 1,
    week_index: 1,
    week_start: DATE,
    week_end: "2026-05-07",
    has_started: true,
    planned_total_km_text: "38 km",
    completed_total: { km: "0", time: "0", avg_hr: null, max_hr: null },
    planned_rows: [
      {
        id: 10,
        kind: "planned",
        status: "planned",
        date: DATE,
        day_label: "Po",
        title: "Tempo run",
        notes: "Keep pace",
        session_type: "RUN",
        planned_metrics: null,
        completed_metrics: null,
        editable: true,
        is_second_phase: false,
        can_add_second_phase: false,
        can_remove_second_phase: false,
        has_linked_activity: false,
      },
    ],
    completed_rows: [],
    ...overrides,
  };
}

function mountWeekCard(week: DashboardWeek = buildWeek()) {
  const wrapper = mount(WeekCard, {
    props: { week, editorContext: "athlete" },
  });

  const authStore = useAuthStore();
  authStore.user = {
    capabilities: { has_garmin_connection: false, garmin_sync_enabled: false },
  } as any;

  const trainingStore = useTrainingStore();
  trainingStore.dashboard = {
    flags: { can_edit_completed: true, can_edit_planned: true, is_coach: false },
  } as any;
  trainingStore.selectedMonthValue = "2026-05";

  return wrapper;
}

describe("WeekCard — zone editing mutual exclusion", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("clicking planned cell shows title input, hides km input", async () => {
    const wrapper = mountWeekCard();
    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true);
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(false);
  });

  it("clicking completed cell shows km input, hides title input", async () => {
    const wrapper = mountWeekCard();
    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(true);
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(false);
  });

  it("switching from planned to completed zone hides planned inputs", async () => {
    const wrapper = mountWeekCard();

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true);

    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(false);
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(true);
  });

  it("switching from completed to planned zone hides completed inputs", async () => {
    const wrapper = mountWeekCard();

    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(true);

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(false);
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true);
  });
});

describe("WeekCard — summary row", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("shows planned_total_km_text in summary row", () => {
    const wrapper = mountWeekCard();
    expect(wrapper.text()).toContain("38 km");
  });
});
```

- [ ] **Krok 2: Ověř, že testy failují**

```bash
cd frontend && pnpm test WeekCard.test.ts --reporter=verbose
```

Očekávaný výsledek: 5 FAIL — `data-testid` atributy neexistují, `activeZone` není implementováno.

- [ ] **Krok 3: Commit failing testů**

```bash
git add frontend/components/training/WeekCard.test.ts
git commit -m "test(weekcard): add failing tests for zone mutual exclusion"
```

---

### Task 2: Rozšíření RowEdit + openEdit + data-testid

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` — `<script setup>` sekce

- [ ] **Krok 1: Přidej `activeZone` do rozhraní `RowEdit`**

V sekci `// ── Edit state ───────────────────────────────────────────────────────`:

```ts
interface RowEdit {
  date: string
  activeZone: "planned" | "completed"   // ← NOVÉ
  // planned
  plannedId: number | null
  title: string
  notes: string
  sessionType: "RUN" | "WORKOUT"
  isCreating: boolean
  // completed
  completedId: number | null
  km: string
  minutes: string
  details: string
  avgHr: string
  maxHr: string
  // ui
  isSaving: boolean
  isDirty: boolean
  debounceTimer: ReturnType<typeof setTimeout> | null
  focusField: string
}
```

- [ ] **Krok 2: Přidej helper `isEditingZone`**

Za funkci `isEditing` přidej:

```ts
function isEditingZone(date: string, zone: "planned" | "completed"): boolean {
  const edit = editingRows.get(date);
  return edit ? edit.activeZone === zone : false;
}
```

- [ ] **Krok 3: Nahraď `openEdit` novou implementací**

Celou funkci `openEdit` nahraď:

```ts
function openEdit(slot: DaySlot, focusField = "title", zone: "planned" | "completed" = "planned") {
  const existing = editingRows.get(slot.date);

  if (existing) {
    if (existing.activeZone === zone) return;
    // Přepnutí zóny: uloží dirty data, pak přepne
    if (existing.isDirty) {
      if (existing.debounceTimer) {
        clearTimeout(existing.debounceTimer);
        existing.debounceTimer = null;
      }
      saveRow(slot, existing); // fire-and-forget
    }
    existing.activeZone = zone;
    existing.focusField = focusField;
    return;
  }

  const planned = slot.planned.find((r) => !r.is_second_phase) ?? null;
  const completed = slot.completed[0] ?? null;
  const canEditPlanned = planned ? planned.editable : true;
  const completedEditable = completed
    ? completed.editable && !completed.has_linked_activity
    : canEditCompletedGlobal.value && planned !== null;

  if (zone === "planned" && !canEditPlanned) return;
  if (zone === "completed" && !completedEditable) return;

  const completedId = completedEditable
    ? (completed?.id ?? planned?.id ?? null)
    : null;

  if (!canEditPlanned && !completedEditable) return;

  editingRows.set(slot.date, {
    date: slot.date,
    activeZone: zone,
    plannedId: planned?.id ?? null,
    title: planned ? (planned.title === "-" ? "" : planned.title) : "",
    notes: planned?.notes ?? "",
    sessionType: (planned?.session_type as "RUN" | "WORKOUT") ?? "RUN",
    isCreating: !planned,
    completedId,
    km: completed?.completed_metrics?.km ?? "",
    minutes: completed?.completed_metrics?.minutes ?? "",
    details: completed?.completed_metrics?.details ?? "",
    avgHr: completed?.completed_metrics?.avg_hr?.toString() ?? "",
    maxHr: completed?.completed_metrics?.max_hr?.toString() ?? "",
    isSaving: false,
    isDirty: false,
    debounceTimer: null,
    focusField,
  });
}
```

- [ ] **Krok 4: Oprav volání `openEdit` v `toggleSessionType`**

Najdi `openEdit(slot, "title")` v těle `toggleSessionType` a změň na:

```ts
openEdit(slot, "title", "planned");
```

- [ ] **Krok 5: Ověř TypeScript**

```bash
cd frontend && pnpm vue-tsc --noEmit
```

Očekávaný výsledek: 0 chyb.

---

### Task 3: Template — podmíněné renderování + data-testid

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` — `<template>` sekce

- [ ] **Krok 1: Aktualizuj třídy hlavního řádku**

Najdi:
```html
:class="{
  'wt__row--editing': isEditing(slot.date),
  'wt__row--done': ...
```

Změň na:
```html
:class="{
  'wt__row--editing-planned': isEditingZone(slot.date, 'planned'),
  'wt__row--editing-completed': isEditingZone(slot.date, 'completed'),
  'wt__row--done': slot.completed[0]?.status === 'done',
  'wt__row--missed': slot.completed[0]?.status === 'missed',
  'wt__row--saved': flashingRows.has(slot.date),
}"
```

- [ ] **Krok 2: Aktualizuj buňky planned zóny**

**Session type buňka** — přidej třídu `wt__cell-p` (click handler beze změny, je na tlačítku uvnitř):
```html
<div class="wt__cell wt__cell--type wt__cell-p" @click.stop>
```

**Training title buňka** — přidej `wt__cell-p`, `data-testid`, uprav click handler a v-if:
```html
<div
  class="wt__cell wt__cell--title wt__cell-p"
  :data-testid="`cell-title-${slot.date}`"
  @click.stop="openEdit(slot, 'title', 'planned')"
>
  <template v-if="isEditingZone(slot.date, 'planned') && getEdit(slot.date)">
    <textarea
      :data-testid="`input-title-${slot.date}`"
      v-model="getEdit(slot.date)!.title"
      v-autofocus="getEdit(slot.date)!.focusField === 'title'"
      class="wt__textarea"
      :disabled="getEdit(slot.date)!.isSaving"
      :placeholder="t('weekCard.titlePlaceholder')"
      rows="1"
      @click.stop
      @input="onFieldInput(slot.date, slot)"
    />
  </template>
  <template v-else>
    <span v-if="slot.planned[0]" class="wt__title-text">{{ slot.planned[0].title }}</span>
    <span v-else class="wt__empty-hint">{{ t("weekCard.clickToAdd") }}</span>
  </template>
</div>
```

**Coach notes buňka** — přidej `wt__cell-p`, uprav click handler a v-if:
```html
<div
  class="wt__cell wt__cell--notes wt__cell-p"
  @click.stop="openEdit(slot, 'notes', 'planned')"
>
  <template v-if="isEditingZone(slot.date, 'planned') && getEdit(slot.date)">
    <input
      v-model="getEdit(slot.date)!.notes"
      v-autofocus="getEdit(slot.date)!.focusField === 'notes'"
      class="wt__input"
      :disabled="getEdit(slot.date)!.isSaving"
      :placeholder="t('weekCard.notesPlaceholder')"
      @click.stop
      @input="onFieldInput(slot.date, slot)"
    />
  </template>
  <template v-else>
    <span class="wt__notes-text">{{ slot.planned[0]?.notes }}</span>
  </template>
</div>
```

- [ ] **Krok 3: Aktualizuj buňky completed zóny**

**km buňka** — přidej `wt__cell-c wt__cell-km`, `data-testid`, uprav click handler a v-if:
```html
<div
  class="wt__cell wt__cell--num wt__cell-c wt__cell-km"
  :data-testid="`cell-km-${slot.date}`"
  @click.stop="canEditCompleted(slot) && openEdit(slot, 'km', 'completed')"
>
  <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input
      :data-testid="`input-km-${slot.date}`"
      v-model="getEdit(slot.date)!.km"
      v-autofocus="getEdit(slot.date)!.focusField === 'km'"
      class="wt__input wt__input--num"
      :disabled="getEdit(slot.date)!.isSaving"
      @click.stop
      @input="onFieldInput(slot.date, slot)"
    />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--done">{{ slot.completed[0]?.completed_metrics?.km || "-" }}</span>
  </template>
</div>
```

**Time buňka:**
```html
<div
  class="wt__cell wt__cell--num wt__cell-c wt__cell-time"
  @click.stop="canEditCompleted(slot) && openEdit(slot, 'minutes', 'completed')"
>
  <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input
      v-model="getEdit(slot.date)!.minutes"
      v-autofocus="getEdit(slot.date)!.focusField === 'minutes'"
      class="wt__input wt__input--num"
      :disabled="getEdit(slot.date)!.isSaving"
      placeholder="min"
      @click.stop
      @input="onFieldInput(slot.date, slot)"
    />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--done">{{ formatMinutes(slot.completed[0]?.completed_metrics?.minutes) }}</span>
  </template>
</div>
```

**Intervals buňka:**
```html
<div
  class="wt__cell wt__cell--intervals wt__cell-c"
  @click.stop="canEditCompleted(slot) && openEdit(slot, 'details', 'completed')"
>
  <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input
      v-model="getEdit(slot.date)!.details"
      v-autofocus="getEdit(slot.date)!.focusField === 'details'"
      class="wt__input"
      :disabled="getEdit(slot.date)!.isSaving"
      @click.stop
      @input="onFieldInput(slot.date, slot)"
    />
  </template>
  <template v-else>
    <span class="wt__intervals-text">{{ slot.completed[0]?.completed_metrics?.details }}</span>
  </template>
</div>
```

**Avg HR buňka:**
```html
<div
  class="wt__cell wt__cell--num wt__cell-c wt__cell-avghr"
  @click.stop="canEditCompleted(slot) && openEdit(slot, 'avgHr', 'completed')"
>
  <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input
      v-model="getEdit(slot.date)!.avgHr"
      v-autofocus="getEdit(slot.date)!.focusField === 'avgHr'"
      class="wt__input wt__input--num"
      :disabled="getEdit(slot.date)!.isSaving"
      @click.stop
      @input="onFieldInput(slot.date, slot)"
    />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--hr">{{ slot.completed[0]?.completed_metrics?.avg_hr ?? "-" }}</span>
  </template>
</div>
```

**Max HR buňka:**
```html
<div
  class="wt__cell wt__cell--num wt__cell-c wt__cell-maxhr"
  @click.stop="canEditCompleted(slot) && openEdit(slot, 'maxHr', 'completed')"
>
  <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input
      v-model="getEdit(slot.date)!.maxHr"
      v-autofocus="getEdit(slot.date)!.focusField === 'maxHr'"
      class="wt__input wt__input--num"
      :disabled="getEdit(slot.date)!.isSaving"
      @click.stop
      @input="onFieldInput(slot.date, slot)"
    />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--hr">{{ slot.completed[0]?.completed_metrics?.max_hr ?? "-" }}</span>
  </template>
</div>
```

- [ ] **Krok 4: Spusť testy**

```bash
cd frontend && pnpm test WeekCard.test.ts --reporter=verbose
```

Očekávaný výsledek: 5 PASS.

- [ ] **Krok 5: Commit**

```bash
git add frontend/components/training/WeekCard.vue
git commit -m "feat(weekcard): split edit state into planned/completed zones with mutual exclusion"
```

---

### Task 4: CSS — vizuální zóny, proporce, hover efekty

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` — `<style scoped>` sekce

- [ ] **Krok 1: Aktualizuj grid proporce**

Najdi `.wt__cols` (grid-template-columns) a nahraď oba výskyty (`.wt__cols` a `/* ── Table grid ──*/`):

```css
/* ── Table grid ── */
.wt__cols {
  display: grid;
  grid-template-columns:
    44px 30px 42px minmax(11rem, 2.5fr) minmax(5rem, 1fr)
    1px
    60px 52px minmax(5rem, 1fr) 46px 46px;
  align-items: start;
  min-height: 2.5rem;
}
```

- [ ] **Krok 2: Přidej zone CSS třídy za existující `.wt__cell` pravidla**

Za blok `/* ── Cells ── */` přidej:

```css
/* ── Zone classes ── */
.wt__cell-p,
.wt__cell-c {
  border-radius: 4px;
  transition: background 120ms;
}

/* Hover: planned zone — modré podbarvení */
.wt__row:has(.wt__cell-p:hover):not(.wt__row--editing-planned):not(.wt__row--editing-completed) .wt__cell-p {
  background: rgba(56, 189, 248, .05);
  cursor: pointer;
}

/* Hover: completed zone — lime podbarvení */
.wt__row:has(.wt__cell-c:hover):not(.wt__row--editing-planned):not(.wt__row--editing-completed) .wt__cell-c {
  background: rgba(200, 255, 0, .05);
  cursor: pointer;
}

/* Editing planned: planned buňky modrý tón */
.wt__row--editing-planned .wt__cell-p {
  background: rgba(56, 189, 248, .07);
}

/* Editing completed: completed buňky lime tón */
.wt__row--editing-completed .wt__cell-c {
  background: rgba(200, 255, 0, .07);
}

/* Neaktivní zóna při editování — ztmavení */
.wt__row--editing-planned .wt__cell-c {
  opacity: 0.45;
  pointer-events: none;
}

.wt__row--editing-completed .wt__cell-p {
  opacity: 0.45;
  pointer-events: none;
}
```

- [ ] **Krok 3: Nahraď starý `.wt__row--editing` styl**

Najdi a **smaž**:
```css
.wt__row--editing {
  background: rgba(200,255,0,.04);
  cursor: default;
}
```

Nahraď border-left pro editing stavy — přidej za kroky výše:
```css
.wt__row--editing-planned {
  border-left: 2px solid rgba(56, 189, 248, .45);
  padding-left: calc(1rem - 2px);
}

.wt__row--editing-completed {
  border-left: 2px solid rgba(200, 255, 0, .4);
  padding-left: calc(1rem - 2px);
}
```

- [ ] **Krok 4: Spusť testy (žádná CSS změna by neměla rozbít testy)**

```bash
cd frontend && pnpm test WeekCard.test.ts --reporter=verbose
```

Očekávaný výsledek: 5 PASS.

- [ ] **Krok 5: Commit**

```bash
git add frontend/components/training/WeekCard.vue
git commit -m "feat(weekcard): add visual zone backgrounds and grid proportions (3/5 : 2/5)"
```

---

### Task 5: Summary row — planned km total

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` — `<template>` sekce (summary row)

- [ ] **Krok 1: Aktualizuj summary row v template**

Najdi blok `<!-- ── Summary row ── -->` a nahraď:

```html
<!-- ── Summary row ── -->
<div class="wt__cols wt__summary-row">
  <div class="wt__summary-label" style="grid-column: 1 / 4">{{ t("weekCard.total") }}</div>
  <div class="wt__summary-planned-km" style="grid-column: 4 / 6">{{ week.planned_total_km_text }}</div>
  <div class="wt__sep-col" />
  <div class="wt__cell wt__cell--num wt__summary-val">{{ week.completed_total.km }}</div>
  <div class="wt__cell wt__cell--num wt__summary-val">{{ formatMinutes(week.completed_total.time) }}</div>
  <div class="wt__cell wt__cell--intervals" />
  <div class="wt__cell wt__cell--num wt__summary-val wt__num-val--hr">{{ week.completed_total.avg_hr ?? "-" }}</div>
  <div class="wt__cell wt__cell--num" />
</div>
```

- [ ] **Krok 2: Přidej CSS pro `.wt__summary-planned-km`**

Za `.wt__summary-label` pravidla v `<style scoped>` přidej:

```css
.wt__summary-planned-km {
  display: flex;
  align-items: center;
  padding: 0 0.35rem;
  color: var(--eb-blue);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
  font-weight: 600;
}
```

- [ ] **Krok 3: Ověř test**

```bash
cd frontend && pnpm test WeekCard.test.ts --reporter=verbose
```

Očekávaný výsledek: 5 PASS (test "shows planned_total_km_text in summary row" byl failing, teď projde).

- [ ] **Krok 4: Commit**

```bash
git add frontend/components/training/WeekCard.vue
git commit -m "feat(weekcard): show planned km total in summary row"
```

---

### Task 6: Mobilní CSS — stacked layout

**Files:**
- Modify: `frontend/components/training/WeekCard.vue` — `<style scoped>` (media queries)

- [ ] **Krok 1: Nahraď media queries**

Najdi a **smaž** celý blok:
```css
@media (max-width: 1023px) { ... }
@media (max-width: 767px) { ... }
```

Nahraď:

```css
/* ── Tablet ── */
@media (max-width: 1023px) {
  .wt__cols {
    grid-template-columns:
      44px 30px 40px minmax(9rem, 2.5fr) minmax(4rem, 1fr)
      1px
      56px 48px 0 44px 44px;
  }
  .wt__cell--intervals { display: none; }
}

/* ── Mobil ── */
@media (max-width: 767px) {
  /* Sloupcové hlavičky skryjeme — jsou přebytečné při stacked layoutu */
  .wt__head-row { display: none; }

  /* Každý řádek: 2 řady — planned nahoře, completed pod ním */
  .wt__cols {
    grid-template-columns: 44px 32px 36px 1fr;
    grid-template-rows: auto auto;
    min-height: unset;
  }

  /* Planned buňky — 1. řada */
  .wt__cell--date  { grid-row: 1; grid-column: 1; padding-left: 0.9rem; }
  .wt__cell--day   { grid-row: 1; grid-column: 2; }
  .wt__cell--type  { grid-row: 1; grid-column: 3; }
  .wt__cell--title { grid-row: 1; grid-column: 4; }
  .wt__cell--notes { display: none; }

  /* Separator — skrýt na mobilu */
  .wt__sep-col { display: none; }

  /* Completed buňky — 2. řada */
  .wt__cell-km, .wt__cell-time, .wt__cell-avghr, .wt__cell-maxhr {
    grid-row: 2;
    text-align: left;
    justify-content: flex-start;
    padding-left: 0.9rem;
  }

  .wt__cell-km      { grid-column: 1 / 3; }
  .wt__cell-time    { grid-column: 3 / 5; }
  .wt__cell-avghr   { grid-column: 1 / 3; }
  .wt__cell-maxhr   { grid-column: 3 / 5; }

  /* intervaly — skrýt na mobilu */
  .wt__cell--intervals { display: none; }

  /* Summary na mobilu */
  .wt__summary-row {
    grid-template-columns: 44px 32px 36px 1fr;
    grid-template-rows: auto auto;
  }
  .wt__summary-label { grid-row: 1; grid-column: 1 / 3; padding-left: 0.9rem; }
  .wt__summary-planned-km { grid-row: 1; grid-column: 3 / 5; }
  .wt__summary-val { grid-row: 2; text-align: left; padding-left: 0.9rem; }
}
```

- [ ] **Krok 2: Spusť všechny testy**

```bash
cd frontend && pnpm test --reporter=verbose
```

Očekávaný výsledek: všechny existující testy zelené (WeekCard: 5 PASS, ostatní beze změny).

- [ ] **Krok 3: Commit**

```bash
git add frontend/components/training/WeekCard.vue
git commit -m "feat(weekcard): mobile stacked zone layout — planned above completed"
```

---

### Task 7: Finální ověření

**Files:** žádné nové soubory

- [ ] **Krok 1: TypeScript check**

```bash
cd frontend && pnpm vue-tsc --noEmit
```

Očekávaný výsledek: 0 chyb.

- [ ] **Krok 2: Kompletní test suite**

```bash
cd frontend && pnpm test --reporter=verbose
```

Očekávaný výsledek: všechny testy zelené (≥ 101 testů — původních 96 + 5 nových WeekCard testů).

- [ ] **Krok 3: Aktualizuj CLAUDE.md**

V sekci `## Aktivní plány a změny` přidej pod poslední dokončenou položku:

```markdown
### 2026-04-25 — WeekCard: split-zone editing + layout redesign

**Spec:** `docs/superpowers/specs/2026-04-25-weekcard-zone-editing.md`
**Plán:** `docs/superpowers/plans/2026-04-25-weekcard-zone-editing.md`

**Co bylo implementováno:**
- `WeekCard.vue`: planned (3/5) a completed (2/5) zóna se vzájemně vylučují při editování
- Kliknutím na planned zónu se otevřou jen inputy pro trénink/poznámky (modré podbarvení)
- Kliknutím na completed zónu se otevřou jen inputy pro km/čas/HR (lime podbarvení)
- Přepnutí zóny uloží dirty data a okamžitě otevře novou zónu
- Summary row zobrazuje `planned_total_km_text` (plánované km) v planned sekci
- Mobilní layout: planned nahoře (plná šířka), completed jako kompaktní řádek pod ním
- Nový test soubor: `WeekCard.test.ts` (5 testů)
```

- [ ] **Krok 4: Commit CLAUDE.md**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — WeekCard zone editing complete"
```
