# WeekCard Editing UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cursor stays in cell after auto-save, zone flash feedback on save result, full keyboard navigation within and across weeks.

**Architecture:** Split `saveRow` → `autoSave` (keeps edit open) + `closeAndSave` (closes on focusout). Add `handleKeyNav` with Tab/Enter/Arrow key logic. Add `defineEmits` + `defineExpose` for cross-week navigation wired in AthleteView and CoachView.

**Tech Stack:** Vue 3 Composition API, Pinia, Vitest + @vue/test-utils

---

### Task 1: Split saveRow + add flash state (TDD)

**Files:**
- Modify: `frontend/components/training/WeekCard.vue`
- Modify: `frontend/components/training/WeekCard.test.ts`

- [ ] **Step 1: Write failing tests**

Add after the existing `describe("WeekCard — inline save", ...)` block in `WeekCard.test.ts`:

```ts
import { nextTick } from "vue"

describe("WeekCard — auto-save keeps edit open", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("edit input is still visible after 1-second debounce save", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await vi.advanceTimersByTimeAsync(1100)
    await nextTick()

    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true)
  })

  it("focusout still closes the edit", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await wrapper.find(".wt__row").trigger("focusout", { relatedTarget: document.body })
    await nextTick()

    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(false)
  })

  it("successful auto-save adds wt__row--flash-planned-ok class", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await vi.advanceTimersByTimeAsync(1100)
    await nextTick()

    expect(wrapper.find(".wt__row").classes()).toContain("wt__row--flash-planned-ok")
  })

  it("failed auto-save adds wt__row--flash-err class", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockRejectedValue(new Error("Network error"))

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await vi.advanceTimersByTimeAsync(1100)
    await nextTick()

    expect(wrapper.find(".wt__row").classes()).toContain("wt__row--flash-err")
  })
})
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd frontend && pnpm test WeekCard.test.ts
```

Expected: 4 new tests FAIL (edit still destroyed after debounce, flash classes missing).

- [ ] **Step 3: Add `nextTick` to the vue import in WeekCard.vue**

```ts
// Replace:
import { computed, reactive, ref } from "vue";
// With:
import { computed, nextTick, reactive, ref } from "vue";
```

- [ ] **Step 4: Replace flash state + helpers in WeekCard.vue**

Replace the current `flashingRows` declaration and `flashRow` function with:

```ts
// ── Flash feedback ────────────────────────────────────────────
const flashingRows = reactive<Set<string>>(new Set())
const flashingPlannedOk = reactive<Set<string>>(new Set())
const flashingCompletedOk = reactive<Set<string>>(new Set())
const flashingError = reactive<Set<string>>(new Set())

function flashRow(date: string) {
  flashingRows.add(date)
  setTimeout(() => flashingRows.delete(date), 600)
}

function flashZoneOk(date: string, zone: "planned" | "completed") {
  const set = zone === "planned" ? flashingPlannedOk : flashingCompletedOk
  set.add(date)
  setTimeout(() => set.delete(date), 700)
}

function flashZoneErr(date: string) {
  flashingError.add(date)
  setTimeout(() => flashingError.delete(date), 700)
}
```

- [ ] **Step 5: Replace saveRow + onFieldInput + onRowFocusOut in WeekCard.vue**

Remove the entire `saveRow` function and replace with these three functions. Keep `onFieldInput` and `onRowFocusOut` updated as shown:

```ts
// ── Shared API call logic ─────────────────────────────────────
async function performSaveApiCalls(slot: DaySlot, edit: RowEdit): Promise<void> {
  if (edit.isCreating && edit.title.trim()) {
    const draft: PlannedTrainingDraft = {
      date: slot.date,
      title: edit.title.trim(),
      notes: edit.notes.trim(),
      session_type: edit.sessionType,
    };
    if (props.editorContext === "coach") {
      await coachStore.addPlannedTraining(draft);
    } else {
      await trainingStore.addPlannedTraining(draft);
    }
  } else if (edit.plannedId) {
    const planned = slot.planned.find((r) => r.id === edit.plannedId);
    const updates: { field: "title" | "notes" | "session_type"; value: string }[] = [];
    const origTitle = planned ? (planned.title === "-" ? "" : planned.title) : "";
    if (edit.title.trim() !== origTitle) updates.push({ field: "title", value: edit.title.trim() });
    if (edit.notes.trim() !== (planned?.notes ?? "")) updates.push({ field: "notes", value: edit.notes.trim() });
    if (edit.sessionType !== planned?.session_type) updates.push({ field: "session_type", value: edit.sessionType });
    if (updates.length > 0) {
      if (props.editorContext === "coach") {
        await coachStore.savePlannedDraft(edit.plannedId, updates);
      } else {
        await trainingStore.savePlannedDraft(edit.plannedId, updates);
      }
    }
  }

  if (edit.completedId) {
    const completed = slot.completed[0];
    const updates: { field: "km" | "min" | "third" | "avg_hr" | "max_hr"; value: string }[] = [];
    if (edit.km.trim() !== (completed?.completed_metrics?.km ?? "")) updates.push({ field: "km", value: edit.km.trim() });
    if (edit.minutes.trim() !== (completed?.completed_metrics?.minutes ?? "")) updates.push({ field: "min", value: edit.minutes.trim() });
    if (edit.details.trim() !== (completed?.completed_metrics?.details ?? "")) updates.push({ field: "third", value: edit.details.trim() });
    if (edit.avgHr.trim() !== (completed?.completed_metrics?.avg_hr?.toString() ?? "")) updates.push({ field: "avg_hr", value: edit.avgHr.trim() });
    if (edit.maxHr.trim() !== (completed?.completed_metrics?.max_hr?.toString() ?? "")) updates.push({ field: "max_hr", value: edit.maxHr.trim() });
    if (updates.length > 0) {
      await trainingStore.saveCompletedDraft(edit.completedId, updates);
    }
  }
}

// ── Auto-save (keeps edit open) ───────────────────────────────
async function autoSave(slot: DaySlot, edit: RowEdit) {
  if (!edit.isDirty || edit.isSaving) return;
  edit.isSaving = true;
  const zone = edit.activeZone;
  try {
    await performSaveApiCalls(slot, edit);
    edit.isDirty = false;
    flashZoneOk(slot.date, zone);
    if (edit.completedId && slot.completed.length === 0) {
      await trainingStore.loadDashboard(trainingStore.selectedMonthValue, { silent: true });
    }
  } catch (err) {
    flashZoneErr(slot.date);
    toastStore.push(err instanceof Error ? err.message : t("weekCard.createError"), "danger");
  } finally {
    edit.isSaving = false;
  }
}

// ── Close + save (used on focusout / keyboard nav away) ───────
async function closeAndSave(slot: DaySlot, edit: RowEdit) {
  if (!edit.isDirty) {
    editingRows.delete(slot.date);
    return;
  }
  if (edit.isSaving) return;
  edit.isSaving = true;
  try {
    await performSaveApiCalls(slot, edit);
    editingRows.delete(slot.date);
    flashRow(slot.date);
    if (edit.completedId && slot.completed.length === 0) {
      await trainingStore.loadDashboard(trainingStore.selectedMonthValue, { silent: true });
    }
  } catch (err) {
    editingRows.delete(slot.date);
    flashZoneErr(slot.date);
    toastStore.push(err instanceof Error ? err.message : t("weekCard.createError"), "danger");
  } finally {
    edit.isSaving = false;
  }
}

// ── Auto-save helpers ─────────────────────────────────────────
function onFieldInput(date: string, slot: DaySlot) {
  const edit = editingRows.get(date);
  if (!edit) return;
  edit.isDirty = true;
  if (edit.debounceTimer) clearTimeout(edit.debounceTimer);
  edit.debounceTimer = setTimeout(() => {
    edit.debounceTimer = null;
    void autoSave(slot, edit);
  }, 1000);
}

function onRowFocusOut(slot: DaySlot, event: FocusEvent) {
  const edit = editingRows.get(slot.date);
  if (!edit) return;
  const row = event.currentTarget as HTMLElement;
  if (row.contains(event.relatedTarget as Node)) return;
  if (edit.debounceTimer) {
    clearTimeout(edit.debounceTimer);
    edit.debounceTimer = null;
  }
  void closeAndSave(slot, edit);
}
```

- [ ] **Step 6: Update zone-switch call inside `openEdit`**

Find the zone-switch branch in `openEdit` that calls `saveRow` and change it to `autoSave`:

```ts
// Replace:
saveRow(slot, existing);
// With:
void autoSave(slot, existing);
```

- [ ] **Step 7: Update the row `:class` binding in the template**

Find `<div class="wt__cols wt__row"` and update its `:class`:

```html
:class="{
  'wt__row--editing-planned': isEditingZone(slot.date, 'planned'),
  'wt__row--editing-completed': isEditingZone(slot.date, 'completed'),
  'wt__row--done': slot.completed[0]?.status === 'done',
  'wt__row--missed': slot.completed[0]?.status === 'missed',
  'wt__row--saved': flashingRows.has(slot.date),
  'wt__row--flash-planned-ok': flashingPlannedOk.has(slot.date),
  'wt__row--flash-completed-ok': flashingCompletedOk.has(slot.date),
  'wt__row--flash-err': flashingError.has(slot.date),
}"
```

- [ ] **Step 8: Add CSS keyframes and flash classes to `<style scoped>`**

Add after the existing `@keyframes row-saved-flash` block:

```css
@keyframes zone-ok {
  0%   { background-color: rgba(200, 255, 0, .22); }
  100% { background-color: rgba(200, 255, 0, .07); }
}

@keyframes zone-err {
  0%   { background-color: rgba(244, 63, 94, .20); }
  100% { background-color: transparent; }
}

.wt__row--flash-planned-ok .wt__cell-p {
  animation: zone-ok 700ms ease-out forwards;
}

.wt__row--flash-completed-ok .wt__cell-c {
  animation: zone-ok 700ms ease-out forwards;
}

.wt__row--flash-err .wt__cell-p,
.wt__row--flash-err .wt__cell-c {
  animation: zone-err 700ms ease-out forwards;
}
```

- [ ] **Step 9: Run tests — verify all pass**

```bash
cd frontend && pnpm test WeekCard.test.ts
```

Expected: all tests pass including the 4 new ones.

- [ ] **Step 10: Commit**

```bash
git add frontend/components/training/WeekCard.vue frontend/components/training/WeekCard.test.ts
git commit -m "feat(weekcard): cursor stays after auto-save, zone flash feedback on success/error"
```

---

### Task 2: Keyboard navigation within a week (TDD)

**Files:**
- Modify: `frontend/components/training/WeekCard.vue`
- Modify: `frontend/components/training/WeekCard.test.ts`

- [ ] **Step 1: Write failing tests**

Add after the flash describe block in `WeekCard.test.ts`:

```ts
describe("WeekCard — keyboard navigation", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it("Tab in title moves focus to notes in same row", async () => {
    const wrapper = mountWeekCard()
    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find('[data-field="title"]').trigger("keydown", { key: "Tab", shiftKey: false })
    await nextTick()

    expect(wrapper.find('[data-field="notes"]').exists()).toBe(true)
    expect(wrapper.find('[data-field="km"]').exists()).toBe(false)
  })

  it("Enter in title moves to title of next day", async () => {
    const week = buildWeek({
      planned_rows: [
        { id: 10, kind: "planned", status: "planned", date: "2026-05-01", day_label: "Po",
          title: "Run", notes: "", session_type: "RUN", planned_metrics: null,
          completed_metrics: null, editable: true, is_second_phase: false,
          can_add_second_phase: false, can_remove_second_phase: false, has_linked_activity: false },
        { id: 11, kind: "planned", status: "planned", date: "2026-05-02", day_label: "Út",
          title: "Rest", notes: "", session_type: "RUN", planned_metrics: null,
          completed_metrics: null, editable: true, is_second_phase: false,
          can_add_second_phase: false, can_remove_second_phase: false, has_linked_activity: false },
      ],
    })
    const wrapper = mountWeekCard(week)

    await wrapper.find('[data-testid="cell-title-2026-05-01"]').trigger("click")
    await wrapper.find('[data-field="title"][data-date="2026-05-01"]').trigger("keydown", { key: "Enter", shiftKey: false })
    await nextTick()

    expect(wrapper.find('[data-field="title"][data-date="2026-05-02"]').exists()).toBe(true)
  })

  it("Tab on last planned field of last day emits navigate-out-next", async () => {
    const singleDayWeek = buildWeek({ week_start: DATE, week_end: DATE })
    const wrapper = mountWeekCard(singleDayWeek)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find('[data-field="title"]').trigger("keydown", { key: "Tab", shiftKey: false })
    await nextTick()
    await wrapper.find('[data-field="notes"]').trigger("keydown", { key: "Tab", shiftKey: false })
    await nextTick()

    expect(wrapper.emitted("navigate-out-next")).toBeTruthy()
    expect(wrapper.emitted("navigate-out-next")![0][0]).toEqual({ field: "title", zone: "planned" })
  })

  it("Shift+Tab on first planned field of first day emits navigate-out-prev", async () => {
    const singleDayWeek = buildWeek({ week_start: DATE, week_end: DATE })
    const wrapper = mountWeekCard(singleDayWeek)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find('[data-field="title"]').trigger("keydown", { key: "Tab", shiftKey: true })
    await nextTick()

    expect(wrapper.emitted("navigate-out-prev")).toBeTruthy()
    expect(wrapper.emitted("navigate-out-prev")![0][0]).toEqual({ field: "notes", zone: "planned" })
  })
})
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd frontend && pnpm test WeekCard.test.ts
```

Expected: 4 new keyboard tests FAIL (no handleKeyNav, no data-field, no emit defined).

- [ ] **Step 3: Add `defineEmits` and field-order constants to WeekCard.vue**

Add after the `defineProps` line:

```ts
const emit = defineEmits<{
  "navigate-out-next": [payload: { field: string; zone: "planned" | "completed" }]
  "navigate-out-prev": [payload: { field: string; zone: "planned" | "completed" }]
}>()

const PLANNED_FIELDS = ["title", "notes"] as const
const COMPLETED_FIELDS = ["km", "minutes", "details", "avgHr", "maxHr"] as const
```

- [ ] **Step 4: Update `openEdit` to propagate focusField on same-zone re-entry**

Find the early-return inside `openEdit` where `existing.activeZone === zone` and update it:

```ts
// Replace:
if (existing.activeZone === zone) return;
// With:
if (existing.activeZone === zone) {
  existing.focusField = focusField;
  return;
}
```

- [ ] **Step 5: Add `handleKeyNav` function after `onRowFocusOut`**

```ts
// ── Keyboard navigation ───────────────────────────────────────
async function handleKeyNav(
  event: KeyboardEvent,
  field: string,
  slot: DaySlot,
  zone: "planned" | "completed",
) {
  const fields: readonly string[] = zone === "planned" ? PLANNED_FIELDS : COMPLETED_FIELDS
  const isTextarea = field === "title"
  const key = event.key
  const shift = event.shiftKey
  const fieldIdx = fields.indexOf(field)
  let targetFieldIdx = fieldIdx
  let targetSlotIdx = daySlots.value.indexOf(slot)

  if (key === "Tab") {
    event.preventDefault()
    if (shift) {
      if (fieldIdx > 0) { targetFieldIdx = fieldIdx - 1 }
      else { targetSlotIdx -= 1; targetFieldIdx = fields.length - 1 }
    } else {
      if (fieldIdx < fields.length - 1) { targetFieldIdx = fieldIdx + 1 }
      else { targetSlotIdx += 1; targetFieldIdx = 0 }
    }
  } else if (key === "Enter") {
    event.preventDefault()
    targetSlotIdx += shift ? -1 : 1
  } else if (key === "ArrowDown") {
    event.preventDefault()
    targetSlotIdx += 1
  } else if (key === "ArrowUp") {
    event.preventDefault()
    targetSlotIdx -= 1
  } else if (key === "ArrowRight" && !isTextarea) {
    event.preventDefault()
    if (fieldIdx < fields.length - 1) { targetFieldIdx = fieldIdx + 1 }
    else { targetSlotIdx += 1; targetFieldIdx = 0 }
  } else if (key === "ArrowLeft" && !isTextarea) {
    event.preventDefault()
    if (fieldIdx > 0) { targetFieldIdx = fieldIdx - 1 }
    else { targetSlotIdx -= 1; targetFieldIdx = fields.length - 1 }
  } else {
    return
  }

  const targetField = fields[targetFieldIdx]

  if (targetSlotIdx < 0) {
    emit("navigate-out-prev", { field: targetField, zone })
    return
  }
  if (targetSlotIdx >= daySlots.value.length) {
    emit("navigate-out-next", { field: targetField, zone })
    return
  }

  const targetSlot = daySlots.value[targetSlotIdx]
  const currentEdit = editingRows.get(slot.date)
  if (currentEdit?.debounceTimer) {
    clearTimeout(currentEdit.debounceTimer)
    currentEdit.debounceTimer = null
    void autoSave(slot, currentEdit)
  }
  openEdit(targetSlot, targetField, zone)

  await nextTick()
  document.querySelector<HTMLElement>(
    `[data-field="${targetField}"][data-date="${targetSlot.date}"]`,
  )?.focus()
}
```

- [ ] **Step 6: Add `data-field`, `data-date`, and `@keydown` to all inputs in the template**

For **title textarea** (planned zone):
```html
<textarea
  v-model="getEdit(slot.date)!.title"
  v-autofocus="getEdit(slot.date)!.focusField === 'title'"
  class="wt__textarea"
  :data-testid="`input-title-${slot.date}`"
  data-field="title"
  :data-date="slot.date"
  :disabled="getEdit(slot.date)!.isSaving"
  :placeholder="t('weekCard.titlePlaceholder')"
  rows="1"
  @click.stop
  @input="onFieldInput(slot.date, slot)"
  @keydown="handleKeyNav($event, 'title', slot, 'planned')"
/>
```

For **notes input** (planned zone):
```html
<input
  v-model="getEdit(slot.date)!.notes"
  v-autofocus="getEdit(slot.date)!.focusField === 'notes'"
  class="wt__input"
  data-field="notes"
  :data-date="slot.date"
  :disabled="getEdit(slot.date)!.isSaving"
  :placeholder="t('weekCard.notesPlaceholder')"
  @click.stop
  @input="onFieldInput(slot.date, slot)"
  @keydown="handleKeyNav($event, 'notes', slot, 'planned')"
/>
```

For **km input** (completed zone):
```html
<input
  v-model="getEdit(slot.date)!.km"
  v-autofocus="getEdit(slot.date)!.focusField === 'km'"
  class="wt__input wt__input--num"
  :data-testid="`input-km-${slot.date}`"
  data-field="km"
  :data-date="slot.date"
  :disabled="getEdit(slot.date)!.isSaving"
  @click.stop
  @input="onFieldInput(slot.date, slot)"
  @keydown="handleKeyNav($event, 'km', slot, 'completed')"
/>
```

For **minutes input** (completed zone):
```html
<input
  v-model="getEdit(slot.date)!.minutes"
  v-autofocus="getEdit(slot.date)!.focusField === 'minutes'"
  class="wt__input wt__input--num"
  data-field="minutes"
  :data-date="slot.date"
  :disabled="getEdit(slot.date)!.isSaving"
  placeholder="min"
  @click.stop
  @input="onFieldInput(slot.date, slot)"
  @keydown="handleKeyNav($event, 'minutes', slot, 'completed')"
/>
```

For **details input** (completed zone):
```html
<input
  v-model="getEdit(slot.date)!.details"
  v-autofocus="getEdit(slot.date)!.focusField === 'details'"
  class="wt__input"
  data-field="details"
  :data-date="slot.date"
  :disabled="getEdit(slot.date)!.isSaving"
  @click.stop
  @input="onFieldInput(slot.date, slot)"
  @keydown="handleKeyNav($event, 'details', slot, 'completed')"
/>
```

For **avgHr input** (completed zone):
```html
<input
  v-model="getEdit(slot.date)!.avgHr"
  v-autofocus="getEdit(slot.date)!.focusField === 'avgHr'"
  class="wt__input wt__input--num"
  data-field="avgHr"
  :data-date="slot.date"
  :disabled="getEdit(slot.date)!.isSaving"
  @click.stop
  @input="onFieldInput(slot.date, slot)"
  @keydown="handleKeyNav($event, 'avgHr', slot, 'completed')"
/>
```

For **maxHr input** (completed zone):
```html
<input
  v-model="getEdit(slot.date)!.maxHr"
  v-autofocus="getEdit(slot.date)!.focusField === 'maxHr'"
  class="wt__input wt__input--num"
  data-field="maxHr"
  :data-date="slot.date"
  :disabled="getEdit(slot.date)!.isSaving"
  @click.stop
  @input="onFieldInput(slot.date, slot)"
  @keydown="handleKeyNav($event, 'maxHr', slot, 'completed')"
/>
```

- [ ] **Step 7: Run tests — verify all pass**

```bash
cd frontend && pnpm test WeekCard.test.ts
```

Expected: all tests pass including the 4 new keyboard tests.

- [ ] **Step 8: Commit**

```bash
git add frontend/components/training/WeekCard.vue frontend/components/training/WeekCard.test.ts
git commit -m "feat(weekcard): keyboard navigation with Tab/Enter/Arrow keys within zone"
```

---

### Task 3: Cross-week navigation — defineExpose + parent wiring

**Files:**
- Modify: `frontend/components/training/WeekCard.vue`
- Modify: `frontend/components/views/dashboard/AthleteView.vue`
- Modify: `frontend/components/views/dashboard/CoachView.vue`

No unit tests for parent wiring (integration concern). WeekCard's `focusCell` is implicitly tested when Tab emits and the parent calls it.

- [ ] **Step 1: Add `defineExpose` at the end of WeekCard.vue `<script setup>`**

```ts
// ── Exposed API for cross-week navigation ─────────────────────
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
})
```

- [ ] **Step 2: Update AthleteView.vue**

In `<script setup>`, `WeekCard` is already imported. Add `ref` to the vue import and add these after existing refs:

```ts
// Existing import — add ref if not present:
import { computed, onMounted, ref } from "vue";

// Existing WeekCard import stays as-is:
import WeekCard from "@/components/training/WeekCard.vue";

// Add after isGarminModalOpen:
const weekCardRefs = ref<InstanceType<typeof WeekCard>[]>([])

function handleNavOut(
  dir: "next" | "prev",
  idx: number,
  payload: { field: string; zone: "planned" | "completed" },
) {
  const targetIdx = dir === "next" ? idx + 1 : idx - 1
  const card = weekCardRefs.value[targetIdx]
  if (card) card.focusCell(payload.field, payload.zone, dir === "prev")
}
```

In the template, update the WeekCard `v-for` inside `<div class="dashboard-view__weeks">`:

```html
<div class="dashboard-view__weeks">
  <WeekCard
    v-for="(week, idx) in trainingStore.weeks"
    :key="week.id"
    :ref="(el) => { if (el) weekCardRefs.value[idx] = el as InstanceType<typeof WeekCard> }"
    :week="week"
    @navigate-out-next="(p) => handleNavOut('next', idx, p)"
    @navigate-out-prev="(p) => handleNavOut('prev', idx, p)"
  />
</div>
```

- [ ] **Step 3: Update CoachView.vue**

`WeekCard` is already imported. Add `ref` to the vue import if missing and add after `isAddingMonth`:

```ts
const weekCardRefs = ref<InstanceType<typeof WeekCard>[]>([])

function handleNavOut(
  dir: "next" | "prev",
  idx: number,
  payload: { field: string; zone: "planned" | "completed" },
) {
  const targetIdx = dir === "next" ? idx + 1 : idx - 1
  const card = weekCardRefs.value[targetIdx]
  if (card) card.focusCell(payload.field, payload.zone, dir === "prev")
}
```

In the template, update the WeekCard `v-for` inside `<div class="coach-view__weeks">`:

```html
<div class="coach-view__weeks">
  <WeekCard
    v-for="(week, idx) in coachStore.weeks"
    :key="week.id"
    :ref="(el) => { if (el) weekCardRefs.value[idx] = el as InstanceType<typeof WeekCard> }"
    :week="week"
    editor-context="coach"
    @navigate-out-next="(p) => handleNavOut('next', idx, p)"
    @navigate-out-prev="(p) => handleNavOut('prev', idx, p)"
  />
</div>
```

- [ ] **Step 4: Run full test suite**

```bash
cd frontend && pnpm test
```

Expected: all 101+ tests pass, 0 TypeScript errors (`pnpm vue-tsc --noEmit` if available).

- [ ] **Step 5: Commit**

```bash
git add frontend/components/training/WeekCard.vue \
        frontend/components/views/dashboard/AthleteView.vue \
        frontend/components/views/dashboard/CoachView.vue
git commit -m "feat(dashboard): cross-week keyboard navigation via focusCell + navigate-out events"
```

---

### Task 4: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add entry to "Aktivní plány a změny"**

Add under the existing entries in that section:

```markdown
### 2026-04-30 — WeekCard: editing UX + keyboard navigation ✅ KOMPLETNÍ

**Spec:** `docs/superpowers/specs/2026-04-30-weekcard-editing-ux.md`
**Plán:** `docs/superpowers/plans/2026-04-30-weekcard-editing-ux.md`

- `autoSave` ponechá edit otevřený po debounce uložení; `closeAndSave` zavírá při focusout
- Zone flash: zelená animace na buňkách aktivní zóny při úspěchu, červená při chybě
- Klávesnicová navigace: Tab/Shift+Tab (pole+řádky), Enter/Shift+Enter (sloupec), Arrow keys
- Cross-week: WeekCard emituje `navigate-out-next/prev`, AthleteView+CoachView volají `focusCell`
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — WeekCard editing UX complete"
```
