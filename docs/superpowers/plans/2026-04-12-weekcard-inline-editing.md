# WeekCard Inline Editing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace expand/collapse row editing with true inline editing — click a field, type, auto-save via debounce; remove action bar and delete button.

**Architecture:** All changes confined to `WeekCard.vue`. RowEdit state gains `isDirty`, `debounceTimer`, `focusField`. A `focusout` listener on each row triggers blur-save. A `vAutofocus` local directive focuses the clicked field on edit activation. Session type becomes a permanent pill button with immediate save.

**Tech Stack:** Vue 3, TypeScript, scoped CSS, existing training/coach stores.

---

### Task 1: Update RowEdit interface and openEdit

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue` (script section, RowEdit interface + openEdit)

- [ ] **Step 1: Update RowEdit interface**

Replace the `RowEdit` interface (lines 104–122) with:

```typescript
interface RowEdit {
  date: string;
  plannedId: number | null;
  title: string;
  notes: string;
  sessionType: "RUN" | "WORKOUT";
  isCreating: boolean;
  completedId: number | null;
  km: string;
  minutes: string;
  details: string;
  avgHr: string;
  maxHr: string;
  isSaving: boolean;
  isDirty: boolean;
  debounceTimer: ReturnType<typeof setTimeout> | null;
  focusField: string;
}
```

- [ ] **Step 2: Update openEdit to accept focusField**

Replace the `openEdit` function so it:
- Accepts a second param `focusField = "title"`
- Initialises `isDirty: false`, `debounceTimer: null`, `focusField`
- Removes the `error: ""` init

```typescript
function openEdit(slot: DaySlot, focusField = "title") {
  if (editingRows.has(slot.date)) return;
  const planned = slot.planned.find((r) => !r.is_second_phase) ?? null;
  const completed = slot.completed[0] ?? null;
  const canEditPlanned = planned ? planned.editable : true;
  const canEditCompleted = completed ? (completed.editable && !completed.has_linked_activity) : false;
  if (!canEditPlanned && !canEditCompleted) return;

  editingRows.set(slot.date, {
    date: slot.date,
    plannedId: planned?.id ?? null,
    title: planned ? (planned.title === "-" ? "" : planned.title) : "",
    notes: planned?.notes ?? "",
    sessionType: (planned?.session_type as "RUN" | "WORKOUT") ?? "RUN",
    isCreating: !planned,
    completedId: canEditCompleted ? (completed?.id ?? null) : null,
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

---

### Task 2: Replace saveRow and remove cancelEdit + deletePlannedRow

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue`

- [ ] **Step 1: Delete cancelEdit function entirely**

Remove:
```typescript
function cancelEdit(date: string) {
  editingRows.delete(date);
}
```

- [ ] **Step 2: Update saveRow — add isDirty guard, remove error field, add flash**

Replace `saveRow` with:

```typescript
async function saveRow(slot: DaySlot, edit: RowEdit) {
  if (!edit.isDirty) {
    editingRows.delete(slot.date);
    return;
  }
  if (edit.isSaving) return;
  edit.isSaving = true;
  try {
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

    editingRows.delete(slot.date);
    flashRow(slot.date);
  } catch (err) {
    toastStore.push(err instanceof Error ? err.message : t("weekCard.createError"), "danger");
  } finally {
    edit.isSaving = false;
  }
}
```

- [ ] **Step 3: Delete deletePlannedRow function entirely**

Remove the entire `deletePlannedRow` async function.

---

### Task 3: Add new helper functions

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue`

Add the following functions after `saveRow`:

- [ ] **Step 1: Add flashingRows + flashRow**

```typescript
const flashingRows = reactive<Set<string>>(new Set());

function flashRow(date: string) {
  flashingRows.add(date);
  setTimeout(() => flashingRows.delete(date), 600);
}
```

- [ ] **Step 2: Add onFieldInput**

```typescript
function onFieldInput(date: string, slot: DaySlot) {
  const edit = editingRows.get(date);
  if (!edit) return;
  edit.isDirty = true;
  if (edit.debounceTimer) clearTimeout(edit.debounceTimer);
  edit.debounceTimer = setTimeout(() => {
    edit.debounceTimer = null;
    saveRow(slot, edit);
  }, 1000);
}
```

- [ ] **Step 3: Add onRowFocusOut**

```typescript
function onRowFocusOut(slot: DaySlot, event: FocusEvent) {
  const edit = editingRows.get(slot.date);
  if (!edit) return;
  const row = event.currentTarget as HTMLElement;
  if (row.contains(event.relatedTarget as Node)) return;
  if (edit.debounceTimer) {
    clearTimeout(edit.debounceTimer);
    edit.debounceTimer = null;
  }
  saveRow(slot, edit);
}
```

- [ ] **Step 4: Add toggleSessionType**

```typescript
async function toggleSessionType(slot: DaySlot) {
  const edit = editingRows.get(slot.date);
  if (edit) {
    edit.sessionType = edit.sessionType === "RUN" ? "WORKOUT" : "RUN";
    onFieldInput(slot.date, slot);
    return;
  }
  const planned = slot.planned.find((r) => !r.is_second_phase) ?? null;
  if (planned?.id) {
    const newType = planned.session_type === "RUN" ? "WORKOUT" : "RUN";
    try {
      if (props.editorContext === "coach") {
        await coachStore.savePlannedDraft(planned.id, [{ field: "session_type", value: newType }]);
      } else {
        await trainingStore.savePlannedDraft(planned.id, [{ field: "session_type", value: newType }]);
      }
      flashRow(slot.date);
    } catch (err) {
      toastStore.push(err instanceof Error ? err.message : t("weekCard.createError"), "danger");
    }
  } else {
    openEdit(slot, "title");
    const newEdit = editingRows.get(slot.date);
    if (newEdit) newEdit.sessionType = "WORKOUT";
  }
}
```

- [ ] **Step 5: Add canEditCompleted helper**

```typescript
function canEditCompleted(slot: DaySlot): boolean {
  const c = slot.completed[0];
  return !!c && c.editable && !c.has_linked_activity;
}
```

- [ ] **Step 6: Add vAutofocus local directive**

Add before `</script>`:

```typescript
const vAutofocus = {
  mounted(el: HTMLElement, binding: { value: boolean }) {
    if (binding.value !== false) el.focus();
  },
};
```

---

### Task 4: Update template — row container and read-only zone

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue` (template section)

- [ ] **Step 1: Update main row div**

Replace:
```html
<div
  class="wt__cols wt__row"
  :class="{
    'wt__row--editing': isEditing(slot.date),
    'wt__row--done': slot.completed[0]?.status === 'done',
    'wt__row--missed': slot.completed[0]?.status === 'missed',
    'wt__row--clickable': !isEditing(slot.date) && (slot.planned[0]?.editable || (!slot.planned.length)),
  }"
  @click="!isEditing(slot.date) && openEdit(slot)"
>
```
With:
```html
<div
  class="wt__cols wt__row"
  :class="{
    'wt__row--editing': isEditing(slot.date),
    'wt__row--done': slot.completed[0]?.status === 'done',
    'wt__row--missed': slot.completed[0]?.status === 'missed',
    'wt__row--saved': flashingRows.has(slot.date),
  }"
  @focusout="onRowFocusOut(slot, $event)"
>
```

- [ ] **Step 2: Add wt__cell--readonly to date and day cells**

Date cell — replace:
```html
<div class="wt__cell wt__cell--date">{{ slot.dateLabel }}</div>
```
With:
```html
<div class="wt__cell wt__cell--date wt__cell--readonly">{{ slot.dateLabel }}</div>
```

Day cell — replace:
```html
<div class="wt__cell wt__cell--day">{{ slot.dayLabel }}</div>
```
With:
```html
<div class="wt__cell wt__cell--day wt__cell--readonly">{{ slot.dayLabel }}</div>
```

---

### Task 5: Update template — session type, title, notes

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue`

- [ ] **Step 1: Replace session type cell with pill button**

Replace the entire `wt__cell--type` div (which has the `@click.stop` block with select + dot):

```html
<!-- Session type -->
<div class="wt__cell wt__cell--type" @click.stop>
  <button
    v-if="isEditing(slot.date) && getEdit(slot.date)"
    class="wt__type-pill"
    :class="`wt__type-pill--${getEdit(slot.date)!.sessionType.toLowerCase()}`"
    type="button"
    @click.stop="toggleSessionType(slot)"
  >{{ getEdit(slot.date)!.sessionType === 'RUN' ? t('weekCard.run') : t('weekCard.workout') }}</button>
  <button
    v-else-if="slot.planned[0]"
    class="wt__type-pill"
    :class="`wt__type-pill--${slot.planned[0].session_type.toLowerCase()}`"
    type="button"
    @click.stop="toggleSessionType(slot)"
  >{{ slot.planned[0].session_type === 'RUN' ? t('weekCard.run') : t('weekCard.workout') }}</button>
  <span v-else class="wt__type-dot wt__type-dot--empty" />
</div>
```

- [ ] **Step 2: Update title cell**

Replace:
```html
<!-- Training title -->
<div class="wt__cell wt__cell--title" @click.stop="!isEditing(slot.date) && openEdit(slot)">
  <template v-if="isEditing(slot.date) && getEdit(slot.date)">
    <textarea
      v-model="getEdit(slot.date)!.title"
      class="wt__textarea"
      :disabled="getEdit(slot.date)!.isSaving"
      :placeholder="t('weekCard.titlePlaceholder')"
      rows="2"
      @click.stop
    />
  </template>
  <template v-else>
    <span v-if="slot.planned[0]" class="wt__title-text">{{ slot.planned[0].title }}</span>
    <span v-else class="wt__empty-hint">{{ t("weekCard.clickToAdd") }}</span>
  </template>
</div>
```
With:
```html
<!-- Training title -->
<div class="wt__cell wt__cell--title" @click.stop="!isEditing(slot.date) && openEdit(slot, 'title')">
  <template v-if="isEditing(slot.date) && getEdit(slot.date)">
    <textarea
      v-model="getEdit(slot.date)!.title"
      v-autofocus="getEdit(slot.date)!.focusField === 'title'"
      class="wt__textarea"
      :disabled="getEdit(slot.date)!.isSaving"
      :placeholder="t('weekCard.titlePlaceholder')"
      rows="2"
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

- [ ] **Step 3: Update notes cell**

Replace:
```html
<!-- Coach notes -->
<div class="wt__cell wt__cell--notes" @click.stop="!isEditing(slot.date) && openEdit(slot)">
  <template v-if="isEditing(slot.date) && getEdit(slot.date)">
    <input
      v-model="getEdit(slot.date)!.notes"
      class="wt__input"
      :disabled="getEdit(slot.date)!.isSaving"
      :placeholder="t('weekCard.notesPlaceholder')"
      @click.stop
    />
  </template>
  <template v-else>
    <span class="wt__notes-text">{{ slot.planned[0]?.notes }}</span>
  </template>
</div>
```
With:
```html
<!-- Coach notes -->
<div class="wt__cell wt__cell--notes" @click.stop="!isEditing(slot.date) && openEdit(slot, 'notes')">
  <template v-if="isEditing(slot.date) && getEdit(slot.date)">
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

---

### Task 6: Update template — completed fields (km, time, intervals, HR)

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue`

- [ ] **Step 1: Update km cell**

Replace:
```html
<!-- km -->
<div class="wt__cell wt__cell--num" @click.stop="!isEditing(slot.date) && slot.completed[0]?.editable && !slot.completed[0]?.has_linked_activity && openEdit(slot)">
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.km" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" @click.stop />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--done">{{ slot.completed[0]?.completed_metrics?.km || "-" }}</span>
  </template>
</div>
```
With:
```html
<!-- km -->
<div class="wt__cell wt__cell--num" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'km')">
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.km" v-autofocus="getEdit(slot.date)!.focusField === 'km'" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" @click.stop @input="onFieldInput(slot.date, slot)" />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--done">{{ slot.completed[0]?.completed_metrics?.km || "-" }}</span>
  </template>
</div>
```

- [ ] **Step 2: Update time cell**

Replace:
```html
<!-- Time (HH:MM) -->
<div class="wt__cell wt__cell--num" @click.stop>
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.minutes" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" placeholder="min" @click.stop />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--done">{{ formatMinutes(slot.completed[0]?.completed_metrics?.minutes) }}</span>
  </template>
</div>
```
With:
```html
<!-- Time (HH:MM) -->
<div class="wt__cell wt__cell--num" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'minutes')">
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.minutes" v-autofocus="getEdit(slot.date)!.focusField === 'minutes'" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" placeholder="min" @click.stop @input="onFieldInput(slot.date, slot)" />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--done">{{ formatMinutes(slot.completed[0]?.completed_metrics?.minutes) }}</span>
  </template>
</div>
```

- [ ] **Step 3: Update intervals cell**

Replace:
```html
<!-- Intervals / details -->
<div class="wt__cell wt__cell--intervals" @click.stop>
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.details" class="wt__input" :disabled="getEdit(slot.date)!.isSaving" @click.stop />
  </template>
  <template v-else>
    <span class="wt__intervals-text">{{ slot.completed[0]?.completed_metrics?.details }}</span>
  </template>
</div>
```
With:
```html
<!-- Intervals / details -->
<div class="wt__cell wt__cell--intervals" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'details')">
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.details" v-autofocus="getEdit(slot.date)!.focusField === 'details'" class="wt__input" :disabled="getEdit(slot.date)!.isSaving" @click.stop @input="onFieldInput(slot.date, slot)" />
  </template>
  <template v-else>
    <span class="wt__intervals-text">{{ slot.completed[0]?.completed_metrics?.details }}</span>
  </template>
</div>
```

- [ ] **Step 4: Update avgHr cell**

Replace:
```html
<!-- Avg HR -->
<div class="wt__cell wt__cell--num" @click.stop>
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.avgHr" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" @click.stop />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--hr">{{ slot.completed[0]?.completed_metrics?.avg_hr ?? "-" }}</span>
  </template>
</div>
```
With:
```html
<!-- Avg HR -->
<div class="wt__cell wt__cell--num" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'avgHr')">
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.avgHr" v-autofocus="getEdit(slot.date)!.focusField === 'avgHr'" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" @click.stop @input="onFieldInput(slot.date, slot)" />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--hr">{{ slot.completed[0]?.completed_metrics?.avg_hr ?? "-" }}</span>
  </template>
</div>
```

- [ ] **Step 5: Update maxHr cell**

Replace:
```html
<!-- Max HR -->
<div class="wt__cell wt__cell--num" @click.stop>
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.maxHr" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" @click.stop />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--hr">{{ slot.completed[0]?.completed_metrics?.max_hr ?? "-" }}</span>
  </template>
</div>
```
With:
```html
<!-- Max HR -->
<div class="wt__cell wt__cell--num" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'maxHr')">
  <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
    <input v-model="getEdit(slot.date)!.maxHr" v-autofocus="getEdit(slot.date)!.focusField === 'maxHr'" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" @click.stop @input="onFieldInput(slot.date, slot)" />
  </template>
  <template v-else>
    <span class="wt__num-val wt__num-val--hr">{{ slot.completed[0]?.completed_metrics?.max_hr ?? "-" }}</span>
  </template>
</div>
```

- [ ] **Step 6: Remove action bar block**

Delete the entire action bar `<div>` (the one with `v-if="isEditing(slot.date) && getEdit(slot.date)"` that contains `wt__action-bar`).

---

### Task 7: Update CSS

**Files:**
- Modify: `frontend/src/components/training/WeekCard.vue` (style section)

- [ ] **Step 1: Add read-only cell style**

After `.wt__cell--intervals` rule, add:

```css
.wt__cell--readonly {
  cursor: default;
  user-select: none;
}
```

- [ ] **Step 2: Replace wt__type-select with wt__type-pill**

Remove `.wt__type-select` block and replace with:

```css
/* ── Type pill ── */
.wt__type-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  font-size: 0.5625rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  background: transparent;
  transition: opacity 120ms;
  white-space: nowrap;
}
.wt__type-pill:hover { opacity: 0.75; }
.wt__type-pill--run {
  color: var(--eb-blue);
  border: 1px solid rgba(56,189,248,.35);
}
.wt__type-pill--workout {
  color: var(--eb-lime);
  border: 1px solid rgba(200,255,0,.35);
}
```

- [ ] **Step 3: Add saved flash animation**

After `.wt__row--p2` rule, add:

```css
.wt__row--saved {
  animation: row-saved-flash 600ms ease-out forwards;
}

@keyframes row-saved-flash {
  0%   { background-color: rgba(200,255,0,.12); }
  100% { background-color: transparent; }
}
```

- [ ] **Step 4: Remove action bar CSS**

Delete these CSS blocks:
- `.wt__action-bar`
- `.wt__action-error`
- `.wt__action-btns`
- `.wt__btn`
- `.wt__btn:disabled`
- `.wt__btn--ghost` and `:hover`
- `.wt__btn--danger` and `:hover`
- `.wt__btn--save` and `:hover`

---

### Task 8: Verify build and tests

**Files:** none

- [ ] **Step 1: Run TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors

- [ ] **Step 2: Run tests**

```bash
cd frontend && npm test -- --run
```
Expected: all 75 tests pass (no WeekCard unit tests exist — passes by default)

- [ ] **Step 3: Build**

```bash
cd frontend && npm run build
```
Expected: build succeeds, no errors
