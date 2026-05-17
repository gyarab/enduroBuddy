<script setup lang="ts">
import { computed, nextTick, reactive, ref } from "vue";

import type { DashboardWeek, TrainingRow, PlannedTrainingDraft } from "~/utils/api/training";
import { garminWeekSync } from "~/utils/api/imports";
import { useAuthStore } from "@/stores/auth";
import { useCoachStore } from "@/stores/coach";
import { useTrainingStore } from "@/stores/training";
import { useToastStore } from "@/stores/toasts";
import EbCard from "@/components/ui/EbCard.vue";

const props = defineProps<{
  week: DashboardWeek;
  editorContext?: "athlete" | "coach";
  activeCursor?: { dayIdx: number; fieldIdx: number } | null;
}>();

const emit = defineEmits<{
  "navigate-out-next": [payload: { field: string; zone: "planned" | "completed" }]
  "navigate-out-prev": [payload: { field: string; zone: "planned" | "completed" }]
  "exit-edit": []
  "exit-edit-move": [direction: 'up' | 'down']
  "cursor-set": [payload: { dayIdx: number; fieldIdx: number }]
}>()

const PLANNED_FIELDS = ["title", "notes"] as const
const COMPLETED_FIELDS = ["km", "minutes", "details", "avgHr", "maxHr"] as const

// Maps fieldIdx (0–7 from useGridNav) to WeekCard field names
// index 0 = type pill (handled separately via toggleTypeByDayIdx)
const FIELD_BY_IDX = ['', 'title', 'notes', 'km', 'minutes', 'details', 'avgHr', 'maxHr'] as const

const { t, locale } = useI18n();
const authStore = useAuthStore();
const trainingStore = useTrainingStore();
const coachStore = useCoachStore();
const toastStore = useToastStore();

// ── vAutofocus directive ─────────────────────────────────────
const vAutofocus = {
  mounted(el: HTMLElement, binding: { value: boolean }) {
    if (binding.value !== false) el.focus();
  },
};

// ── Garmin sync ─────────────────────────────────────────────
const isSyncingGarmin = ref(false);
const showGarminSync = computed(
  () =>
    props.editorContext !== "coach" &&
    props.week.has_started &&
    authStore.user?.capabilities?.has_garmin_connection &&
    authStore.user?.capabilities?.garmin_sync_enabled,
);

const canEditCompletedGlobal = computed(
  () => props.editorContext !== "coach" && !!trainingStore.dashboard?.flags.can_edit_completed,
);

async function syncGarmin() {
  isSyncingGarmin.value = true;
  try {
    const result = await garminWeekSync(props.week.week_start);
    toastStore.push(result.message, "success");
    await trainingStore.loadDashboard();
  } catch {
    toastStore.push(t("weekCard.garminSyncError"), "danger");
  } finally {
    isSyncingGarmin.value = false;
  }
}

// ── Date helpers ─────────────────────────────────────────────
const CS_DAYS = ["Ne", "Po", "Út", "St", "Čt", "Pá", "So"];
const EN_DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function formatDDMM(dateStr: string): string {
  const [, m, d] = dateStr.split("-");
  return `${parseInt(d)}.${parseInt(m)}`;
}

function getDayLabel(dateStr: string): string {
  const idx = new Date(dateStr).getDay();
  return locale.value === "en" ? EN_DAYS[idx] : CS_DAYS[idx];
}

function formatMinutes(val: string | number | null | undefined): string {
  if (val === null || val === undefined || val === "" || val === "0" || val === 0) return "";
  const m = typeof val === "string" ? parseInt(val) : val;
  if (isNaN(m) || m === 0) return "";
  const h = Math.floor(m / 60);
  const min = m % 60;
  return h > 0 ? `${h}:${min.toString().padStart(2, "0")}` : `${min}`;
}

function formatRange(start: string, end: string) {
  const s = new Date(start);
  const e = new Date(end);
  return `${s.getDate()}.${s.getMonth() + 1}. – ${e.getDate()}.${e.getMonth() + 1}.`;
}

// ── Day slots ────────────────────────────────────────────────
interface DaySlot {
  date: string;
  dateLabel: string;
  dayLabel: string;
  planned: TrainingRow[];
  completed: TrainingRow[];
}

const daySlots = computed<DaySlot[]>(() => {
  const slots: DaySlot[] = [];
  const cur = new Date(props.week.week_start);
  const end = new Date(props.week.week_end);
  while (cur <= end) {
    const date = cur.toISOString().split("T")[0];
    slots.push({
      date,
      dateLabel: formatDDMM(date),
      dayLabel: getDayLabel(date),
      planned: props.week.planned_rows.filter((r) => r.date === date),
      completed: props.week.completed_rows.filter((r) => r.date === date),
    });
    cur.setDate(cur.getDate() + 1);
  }
  return slots;
});

// ── Edit state ───────────────────────────────────────────────
interface RowEdit {
  date: string;
  activeZone: "planned" | "completed";   // ← NEW
  // planned
  plannedId: number | null;
  title: string;
  notes: string;
  sessionType: "RUN" | "WORKOUT";
  isCreating: boolean;
  // completed
  completedId: number | null;
  km: string;
  minutes: string;
  details: string;
  avgHr: string;
  maxHr: string;
  // ui
  isSaving: boolean;
  isDirty: boolean;
  saveError: boolean;
  closeAfterSave: boolean;
  debounceTimer: ReturnType<typeof setTimeout> | null;
  focusField: string;
}

const editingRows = reactive<Map<string, RowEdit>>(new Map());

function getEdit(date: string): RowEdit | undefined {
  return editingRows.get(date);
}

function isEditing(date: string): boolean {
  return editingRows.has(date);
}

function isEditingZone(date: string, zone: "planned" | "completed"): boolean {
  const edit = editingRows.get(date);
  return edit ? edit.activeZone === zone : false;
}

function openEdit(slot: DaySlot, focusField = "title", zone: "planned" | "completed" = "planned") {
  const dayIdx = daySlots.value.findIndex(s => s.date === slot.date)
  const fieldIdx = FIELD_BY_IDX.indexOf(focusField as typeof FIELD_BY_IDX[number])

  const existing = editingRows.get(slot.date);

  if (existing) {
    if (existing.activeZone === zone) {
      existing.focusField = focusField;
      emit('cursor-set', { dayIdx, fieldIdx })
      if (zone === 'planned') resizePlannedTextareas(slot.date)
      return;
    }
    // Guard: don't switch into a non-editable zone
    const planned = slot.planned.find((r) => !r.is_second_phase) ?? null;
    if (zone === "planned" && !(planned ? planned.editable : true)) return;
    if (zone === "completed" && !canEditCompleted(slot)) return;
    // Zone switch: save dirty data fire-and-forget, then switch
    if (existing.isDirty) {
      if (existing.debounceTimer) {
        clearTimeout(existing.debounceTimer);
        existing.debounceTimer = null;
      }
      void autoSave(slot, existing);
    }
    existing.activeZone = zone;
    existing.focusField = focusField;
    emit('cursor-set', { dayIdx, fieldIdx })
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
    saveError: false,
    closeAfterSave: false,
    debounceTimer: null,
    focusField,
  });
  emit('cursor-set', { dayIdx, fieldIdx })
  if (zone === 'planned') resizePlannedTextareas(slot.date)
}

// ── Flash feedback ────────────────────────────────────────────
const flashingError = reactive<Set<string>>(new Set())

function flashZoneErr(date: string) {
  flashingError.add(date)
  setTimeout(() => flashingError.delete(date), 700)
}

// ── Cell-level flash: key = `${date}:${fieldIdx}` ────────────
const flashingCellsErr = reactive<Set<string>>(new Set())

function flashCellErr(date: string, fieldIdx: number) {
  const key = `${date}:${fieldIdx}`
  flashingCellsErr.add(key)
  setTimeout(() => flashingCellsErr.delete(key), 900)
}

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
    // Find the newly created row and transition out of create mode to prevent duplicate creation
    const storeWeeks = props.editorContext === "coach" ? coachStore.weeks : trainingStore.weeks;
    const newRow = storeWeeks.flatMap(w => w.planned_rows).find(r => r.date === slot.date && !r.is_second_phase);
    if (newRow?.id) {
      edit.isCreating = false;
      edit.plannedId = newRow.id;
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
    edit.saveError = false;
    if (edit.completedId && slot.completed.length === 0) {
      await trainingStore.loadDashboard(trainingStore.selectedMonthValue, { silent: true });
    }
  } catch (err) {
    edit.saveError = true;
    const fi = FIELD_BY_IDX.indexOf(edit.focusField as typeof FIELD_BY_IDX[number])
    if (fi > 0) flashCellErr(slot.date, fi)
    flashZoneErr(slot.date);
    toastStore.push(t("weekCard.saveError"), "danger");
  } finally {
    edit.isSaving = false;
    if (edit.closeAfterSave) {
      edit.closeAfterSave = false;
      await nextTick();
      const rowEl = document.querySelector<HTMLElement>(`[data-row-date="${slot.date}"]`);
      if (!rowEl || !rowEl.contains(document.activeElement)) {
        editingRows.delete(slot.date);
      }
    }
  }
}

// ── Close + save (used on focusout / keyboard nav away) ───────
async function closeAndSave(slot: DaySlot, edit: RowEdit) {
  if (!edit.isDirty) {
    editingRows.delete(slot.date);
    return;
  }
  if (edit.isSaving) {
    edit.closeAfterSave = true;
    return;
  }
  edit.isSaving = true;
  try {
    await performSaveApiCalls(slot, edit);
    editingRows.delete(slot.date);
    if (edit.completedId && slot.completed.length === 0) {
      await trainingStore.loadDashboard(trainingStore.selectedMonthValue, { silent: true });
    }
  } catch (err) {
    editingRows.delete(slot.date);
    const fi = FIELD_BY_IDX.indexOf(edit.focusField as typeof FIELD_BY_IDX[number])
    if (fi > 0) flashCellErr(slot.date, fi)
    flashZoneErr(slot.date);
    toastStore.push(t("weekCard.saveError"), "danger");
  } finally {
    edit.isSaving = false;
  }
}

// ── Auto-save helpers ─────────────────────────────────────────
function onFieldInput(date: string, slot: DaySlot) {
  const edit = editingRows.get(date);
  if (!edit) return;
  edit.isDirty = true;
  edit.saveError = false;
  if (edit.debounceTimer) clearTimeout(edit.debounceTimer);
  edit.debounceTimer = setTimeout(() => {
    edit.debounceTimer = null;
    void autoSave(slot, edit);
  }, 1000);
}

function autoResizeTextarea(el: HTMLTextAreaElement) {
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
  el.style.overflowY = 'hidden'
}

function resizePlannedTextareas(date: string) {
  void nextTick(() => {
    const titleEl = document.querySelector<HTMLTextAreaElement>(`[data-field="title"][data-date="${date}"]`)
    const notesEl = document.querySelector<HTMLTextAreaElement>(`[data-field="notes"][data-date="${date}"]`)
    if (titleEl) autoResizeTextarea(titleEl)
    if (notesEl) autoResizeTextarea(notesEl)
  })
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
  emit('exit-edit')
}

function handleEditKeydown(event: KeyboardEvent, field: string, slot: DaySlot) {
  const key = event.key
  if (key === 'Escape') {
    event.preventDefault()
    const edit = editingRows.get(slot.date)
    if (edit) {
      if (edit.debounceTimer) { clearTimeout(edit.debounceTimer); edit.debounceTimer = null }
      if (edit.isDirty) { edit.closeAfterSave = true; void autoSave(slot, edit) }
      else { editingRows.delete(slot.date) }
    }
    emit('exit-edit')
    return
  }
  if (key === 'ArrowUp' || key === 'ArrowDown') {
    event.preventDefault()
    return
  }
  if (key === 'Enter') {
    if (event.ctrlKey && (field === 'title' || field === 'notes')) return
    event.preventDefault()
    const edit = editingRows.get(slot.date)
    if (edit) {
      if (edit.debounceTimer) { clearTimeout(edit.debounceTimer); edit.debounceTimer = null }
      if (edit.isDirty) { edit.closeAfterSave = true; void autoSave(slot, edit) }
      else { editingRows.delete(slot.date) }
    }
    emit('exit-edit-move', event.shiftKey ? 'up' : 'down')
    return
  }
  if (key === 'Tab') {
    event.preventDefault()
    const edit = editingRows.get(slot.date)
    if (edit) {
      if (edit.debounceTimer) { clearTimeout(edit.debounceTimer); edit.debounceTimer = null }
      if (edit.isDirty) { edit.closeAfterSave = true; void autoSave(slot, edit) }
      else { editingRows.delete(slot.date) }
    }
    emit('exit-edit')
  }
}

function isNavSelected(slotDate: string, fieldIdx: number): boolean {
  if (!props.activeCursor) return false
  if (isEditing(slotDate)) return false
  const slotIdx = daySlots.value.findIndex(s => s.date === slotDate)
  return slotIdx === props.activeCursor.dayIdx && fieldIdx === props.activeCursor.fieldIdx
}

function navSelectedClass(slotDate: string, fieldIdx: number): string {
  if (!isNavSelected(slotDate, fieldIdx)) return ''
  return fieldIdx <= 2 ? 'wt__cell--nav-selected-p' : 'wt__cell--nav-selected-c'
}

function canEditCompleted(slot: DaySlot): boolean {
  if (!canEditCompletedGlobal.value) return false;
  const c = slot.completed[0];
  if (c) return c.editable && !c.has_linked_activity;
  // No completed record yet — allow creation if a planned training exists
  const planned = slot.planned.find((r) => !r.is_second_phase) ?? null;
  return planned !== null;
}

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
    } catch (err) {
      flashCellErr(slot.date, 0);
      toastStore.push(t("weekCard.saveError"), "danger");
    }
  } else {
    openEdit(slot, "title", "planned");
    const newEdit = editingRows.get(slot.date);
    if (newEdit) newEdit.sessionType = "WORKOUT";
  }
}

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

  focusCellByIdx(dayIdx: number, fieldIdx: number, replaceContent?: string) {
    if (fieldIdx === 0) return  // type pill — use toggleTypeByDayIdx
    const field = FIELD_BY_IDX[fieldIdx]
    if (!field) return
    const zone: "planned" | "completed" = fieldIdx <= 2 ? 'planned' : 'completed'
    const slot = daySlots.value[dayIdx]
    if (!slot) return
    openEdit(slot, field, zone)
    if (replaceContent !== undefined) {
      const edit = editingRows.get(slot.date)
      if (edit) {
        if (field === 'title')        edit.title   = replaceContent
        else if (field === 'notes')   edit.notes   = replaceContent
        else if (field === 'km')      edit.km      = replaceContent
        else if (field === 'minutes') edit.minutes = replaceContent
        else if (field === 'details') edit.details = replaceContent
        else if (field === 'avgHr')   edit.avgHr   = replaceContent
        else if (field === 'maxHr')   edit.maxHr   = replaceContent
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
        void autoSave(slot, edit)
      } else {
        editingRows.delete(date)
      }
    }
  },

})
</script>

<template>
  <EbCard class="week-card">
    <!-- ── Header ── -->
    <div class="week-card__header">
      <div>
        <div class="week-card__eyebrow">{{ t("weekCard.week", { index: week.week_index }) }}</div>
        <div class="week-card__range">{{ formatRange(week.week_start, week.week_end) }}</div>
      </div>
      <div class="week-card__header-actions">
        <button v-if="showGarminSync" class="week-card__garmin-btn" type="button" :disabled="isSyncingGarmin" @click="syncGarmin">
          {{ isSyncingGarmin ? t("weekCard.garminSyncing") : t("weekCard.garminSync") }}
        </button>
      </div>
    </div>

    <div class="wt__table">
      <!-- ── Column headers ── -->
      <div class="wt__cols wt__head-row">
        <div class="wt__h wt__h--date">{{ t("weekCard.date") }}</div>
        <div class="wt__h">{{ t("weekCard.day") }}</div>
        <div class="wt__h wt__h--type"></div>
        <div class="wt__h">{{ t("weekCard.training") }}</div>
        <div class="wt__h">{{ t("weekCard.coachNotes") }}</div>
        <div class="wt__sep-col"></div>
        <div class="wt__h wt__h--num">km</div>
        <div class="wt__h wt__h--num">{{ t("weekCard.time") }}</div>
        <div class="wt__h">{{ t("weekCard.intervals") }}</div>
        <div class="wt__h wt__h--num">⌀HR</div>
        <div class="wt__h wt__h--num">HR↑</div>
      </div>

      <!-- ── Day rows ── -->
      <template v-for="slot in daySlots" :key="slot.date">
        <!-- Main planned row -->
        <div
          class="wt__cols wt__row"
          :data-row-date="slot.date"
          :class="{
            'wt__row--editing-planned': isEditingZone(slot.date, 'planned'),
            'wt__row--editing-completed': isEditingZone(slot.date, 'completed'),
            'wt__row--done': slot.completed[0]?.status === 'done',
            'wt__row--missed': slot.completed[0]?.status === 'missed',
            'wt__row--flash-err': flashingError.has(slot.date),
            'wt__row--save-error': getEdit(slot.date)?.saveError,
          }"
          @focusout="onRowFocusOut(slot, $event)"
        >
          <!-- Date -->
          <div class="wt__cell wt__cell--date wt__cell--readonly">{{ slot.dateLabel }}</div>

          <!-- Day -->
          <div class="wt__cell wt__cell--day wt__cell--readonly">{{ slot.dayLabel }}</div>

          <!-- Session type -->
          <div
            class="wt__cell wt__cell--type wt__cell-p"
            :data-testid="`nav-cell-type-${slot.date}`"
            :class="[
              navSelectedClass(slot.date, 0),
{ 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:0`) },
            ]"
            @click.stop
          >
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
            <span
              v-else
              class="wt__type-dot wt__type-dot--empty"
              :class="{ 'wt__type-dot--cursor': isNavSelected(slot.date, 0) }"
            />
          </div>

          <!-- Training title -->
          <div
            class="wt__cell wt__cell--title wt__cell-p"
            :data-testid="`cell-title-${slot.date}`"
            :class="[
              navSelectedClass(slot.date, 1),
{ 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:1`) },
            ]"
            @click.stop="openEdit(slot, 'title', 'planned')"
          >
            <template v-if="isEditingZone(slot.date, 'planned') && getEdit(slot.date)">
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
                @keydown="handleEditKeydown($event, 'title', slot)"
              />
            </template>
            <template v-else>
              <span class="wt__nav-cell">{{ slot.planned[0]?.title === '-' ? '' : (slot.planned[0]?.title || '') }}</span>
            </template>
          </div>

          <!-- Coach notes -->
          <div
            class="wt__cell wt__cell--notes wt__cell-p"
            :class="[
              navSelectedClass(slot.date, 2),
{ 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:2`) },
            ]"
            @click.stop="openEdit(slot, 'notes', 'planned')"
          >
            <template v-if="isEditingZone(slot.date, 'planned') && getEdit(slot.date)">
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
            </template>
            <template v-else>
              <span class="wt__nav-cell">{{ slot.planned[0]?.notes || '' }}</span>
            </template>
          </div>

          <!-- Separator -->
          <div class="wt__sep-col" />

          <!-- km -->
          <div
            class="wt__cell wt__cell--num wt__cell-c wt__cell-km"
            :data-testid="`cell-km-${slot.date}`"
            :class="[
              navSelectedClass(slot.date, 3),
{ 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:3`) },
            ]"
            @click.stop="canEditCompleted(slot) && openEdit(slot, 'km', 'completed')"
          >
            <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input
                v-model="getEdit(slot.date)!.km"
                v-autofocus="getEdit(slot.date)!.focusField === 'km'"
                class="wt__input wt__input--num"
                :data-testid="`input-km-${slot.date}`"
                data-field="km"
                :data-date="slot.date"
                                @click.stop
                @input="onFieldInput(slot.date, slot)"
                @keydown="handleEditKeydown($event, 'km', slot)"
              />
            </template>
            <template v-else>
              <span class="wt__nav-cell wt__nav-cell--num">{{ slot.completed[0]?.completed_metrics?.km || '' }}</span>
            </template>
          </div>

          <!-- Time (HH:MM) -->
          <div
            class="wt__cell wt__cell--num wt__cell-c wt__cell-time"
            :class="[
              navSelectedClass(slot.date, 4),
{ 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:4`) },
            ]"
            @click.stop="canEditCompleted(slot) && openEdit(slot, 'minutes', 'completed')"
          >
            <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input
                v-model="getEdit(slot.date)!.minutes"
                v-autofocus="getEdit(slot.date)!.focusField === 'minutes'"
                class="wt__input wt__input--num"
                data-field="minutes"
                :data-date="slot.date"
                                placeholder="min"
                @click.stop
                @input="onFieldInput(slot.date, slot)"
                @keydown="handleEditKeydown($event, 'minutes', slot)"
              />
            </template>
            <template v-else>
              <span class="wt__nav-cell wt__nav-cell--num">{{ formatMinutes(slot.completed[0]?.completed_metrics?.minutes) }}</span>
            </template>
          </div>

          <!-- Intervals / details -->
          <div
            class="wt__cell wt__cell--intervals wt__cell-c"
            :class="[
              navSelectedClass(slot.date, 5),
{ 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:5`) },
            ]"
            @click.stop="canEditCompleted(slot) && openEdit(slot, 'details', 'completed')"
          >
            <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input
                v-model="getEdit(slot.date)!.details"
                v-autofocus="getEdit(slot.date)!.focusField === 'details'"
                class="wt__input"
                data-field="details"
                :data-date="slot.date"
                                @click.stop
                @input="onFieldInput(slot.date, slot)"
                @keydown="handleEditKeydown($event, 'details', slot)"
              />
            </template>
            <template v-else>
              <span class="wt__nav-cell">{{ slot.completed[0]?.completed_metrics?.details || '' }}</span>
            </template>
          </div>

          <!-- Avg HR -->
          <div
            class="wt__cell wt__cell--num wt__cell-c wt__cell-avghr"
            :class="[
              navSelectedClass(slot.date, 6),
{ 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:6`) },
            ]"
            @click.stop="canEditCompleted(slot) && openEdit(slot, 'avgHr', 'completed')"
          >
            <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input
                v-model="getEdit(slot.date)!.avgHr"
                v-autofocus="getEdit(slot.date)!.focusField === 'avgHr'"
                class="wt__input wt__input--num"
                data-field="avgHr"
                :data-date="slot.date"
                                @click.stop
                @input="onFieldInput(slot.date, slot)"
                @keydown="handleEditKeydown($event, 'avgHr', slot)"
              />
            </template>
            <template v-else>
              <span class="wt__nav-cell wt__nav-cell--num">{{ slot.completed[0]?.completed_metrics?.avg_hr ?? '' }}</span>
            </template>
          </div>

          <!-- Max HR -->
          <div
            class="wt__cell wt__cell--num wt__cell-c wt__cell-maxhr"
            :class="[
              navSelectedClass(slot.date, 7),
{ 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:7`) },
            ]"
            @click.stop="canEditCompleted(slot) && openEdit(slot, 'maxHr', 'completed')"
          >
            <template v-if="isEditingZone(slot.date, 'completed') && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input
                v-model="getEdit(slot.date)!.maxHr"
                v-autofocus="getEdit(slot.date)!.focusField === 'maxHr'"
                class="wt__input wt__input--num"
                data-field="maxHr"
                :data-date="slot.date"
                                @click.stop
                @input="onFieldInput(slot.date, slot)"
                @keydown="handleEditKeydown($event, 'maxHr', slot)"
              />
            </template>
            <template v-else>
              <span class="wt__nav-cell wt__nav-cell--num">{{ slot.completed[0]?.completed_metrics?.max_hr ?? '' }}</span>
            </template>
          </div>
        </div>

        <!-- P2 sub-rows (second phase) -->
        <template v-for="p2 in slot.planned.filter(r => r.is_second_phase)" :key="`p2-${p2.id}`">
          <div class="wt__cols wt__row wt__row--p2">
            <div class="wt__cell wt__cell--date" />
            <div class="wt__cell wt__cell--day" />
            <div class="wt__cell wt__cell--type">
              <span class="wt__type-dot" :class="`wt__type-dot--${p2.session_type.toLowerCase()}`" />
            </div>
            <div class="wt__cell wt__cell--title">
              <span class="wt__p2-label">P2</span>
              <span class="wt__title-text">{{ p2.title }}</span>
            </div>
            <div class="wt__cell wt__cell--notes"><span class="wt__notes-text">{{ p2.notes }}</span></div>
            <div class="wt__sep-col" />
            <div class="wt__cell wt__cell--num" /><div class="wt__cell wt__cell--num" /><div class="wt__cell wt__cell--intervals" /><div class="wt__cell wt__cell--num" /><div class="wt__cell wt__cell--num" />
          </div>
        </template>
      </template>

      <!-- ── Summary row ── -->
      <div class="wt__cols wt__summary-row">
        <div class="wt__summary-label" style="grid-column: 1 / 4">{{ t("weekCard.total") }}</div>
        <div class="wt__summary-planned-km" style="grid-column: 4 / 6">{{ week.planned_total_km_text }}</div>
        <div class="wt__sep-col" />
        <div class="wt__cell wt__cell--num wt__summary-val">{{ week.completed_total.km }}</div>
        <div class="wt__cell wt__cell--num wt__summary-val">{{ formatMinutes(week.completed_total.time) }}</div>
        <div class="wt__cell wt__cell--intervals" />
        <div class="wt__cell wt__cell--num wt__summary-val wt__num-val--hr">{{ week.completed_total.avg_hr ?? "" }}</div>
        <div class="wt__cell wt__cell--num" />
      </div>
    </div>
  </EbCard>
</template>

<style scoped>
.week-card {
  overflow-x: auto;
  padding: 0;
}

.wt__table {
  min-width: 720px;
  width: 100%;
}

/* ── Header ── */
.week-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 1.25rem;
  border-bottom: 1px solid var(--eb-border);
  background: var(--eb-surface-strong);
}

.week-card__eyebrow {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.week-card__range {
  margin-top: 0.2rem;
  color: var(--eb-text-soft);
  font-size: 0.8125rem;
}

.week-card__header-actions {
  display: flex;
  gap: 0.5rem;
}

.week-card__garmin-btn {
  padding: 0.35rem 0.85rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: transparent;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-small-size);
  font-weight: 600;
  cursor: pointer;
  transition: border-color 150ms, color 150ms;
}
.week-card__garmin-btn:hover { border-color: rgba(200,255,0,.3); color: var(--eb-lime); }
.week-card__garmin-btn:disabled { opacity: 0.5; cursor: not-allowed; }

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

/* ── Header row ── */
.wt__head-row {
  padding: 0.4rem 1rem;
  border-bottom: 1px solid var(--eb-border);
  background: rgba(255,255,255,.025);
}

.wt__h {
  color: var(--eb-text-muted);
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0 0.35rem;
}

.wt__h--date { padding-left: 0; }
.wt__h--num { text-align: right; padding-right: 0.5rem; }
.wt__h--type { padding: 0; }

/* ── Separator column ── */
.wt__sep-col {
  align-self: stretch;
  background: var(--eb-border);
  width: 1px;
  margin: 0.25rem 0;
}

/* ── Day row ── */
.wt__row {
  padding: 0.4rem 1rem;
  border-bottom: 1px solid var(--eb-border-soft);
  min-height: 2.75rem;
  align-items: start;
  transition: background-color 100ms;
}

.wt__row:last-of-type { border-bottom: none; }

.wt__row--clickable { cursor: pointer; }
.wt__row--clickable:hover { background: rgba(255,255,255,.025); }


.wt__row--done { border-left: 2px solid var(--eb-lime); padding-left: calc(1rem - 2px); }
.wt__row--missed { border-left: 2px solid rgba(244,63,94,.5); padding-left: calc(1rem - 2px); }

.wt__row--p2 { opacity: 0.75; }


@keyframes zone-err {
  0%   { background-color: rgba(244, 63, 94, .18); }
  100% { background-color: transparent; }
}


/* ── Persistent save-error state ── */
.wt__row--save-error.wt__row--editing-planned,
.wt__row--save-error.wt__row--editing-completed {
  border-left-color: rgba(244, 63, 94, .55);
}

.wt__row--save-error .wt__input,
.wt__row--save-error .wt__textarea {
  border-color: rgba(244, 63, 94, .4);
}

.wt__row--save-error .wt__input:focus,
.wt__row--save-error .wt__textarea:focus {
  border-color: rgba(244, 63, 94, .65);
  box-shadow: 0 0 0 2px rgba(244, 63, 94, .10);
}

/* ── Cells ── */
.wt__cell {
  padding: 0.3rem 0.35rem;
  font-size: 0.8125rem;
}

.wt__cell--date {
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.75rem;
  padding-left: 0;
}

.wt__cell--day {
  color: var(--eb-text);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.wt__cell--type {
  display: flex;
  align-items: center;
  padding: 0.3rem 0;
}

.wt__cell--num {
  text-align: right;
  padding-right: 0.5rem;
}

.wt__cell--intervals {
  padding-left: 0.5rem;
}

.wt__cell--readonly {
  cursor: default;
  user-select: none;
}

/* ── Zone classes ── */
.wt__cell-p,
.wt__cell-c {
  border-radius: 4px;
  min-height: 1.75rem;
  display: flex;
  align-items: center;
}

/* Hover: planned cell — only when NOT nav-selected and NOT type cell */
.wt__row:not(.wt__row--editing-planned):not(.wt__row--editing-completed)
  .wt__cell-p:not(.wt__cell--nav-selected-p):not(.wt__cell--type):hover {
  outline: 1px solid rgba(56, 189, 248, .55);
  background: rgba(56, 189, 248, .07);
  box-shadow: inset 0 0 0 1px rgba(56, 189, 248, .18);
  border-radius: 4px;
  cursor: pointer;
}

/* Hover: completed cell — only when NOT nav-selected */
.wt__row:not(.wt__row--editing-planned):not(.wt__row--editing-completed)
  .wt__cell-c:not(.wt__cell--nav-selected-c):hover {
  outline: 1px solid rgba(200, 255, 0, .55);
  background: rgba(200, 255, 0, .07);
  box-shadow: inset 0 0 0 1px rgba(200, 255, 0, .18);
  border-radius: 4px;
  cursor: pointer;
}

/* Type cell: transparent on hover — pill handles the visual */
.wt__row:not(.wt__row--editing-planned):not(.wt__row--editing-completed)
  .wt__cell--type:hover {
  outline: none;
  background: transparent;
  box-shadow: none;
  cursor: pointer;
}

/* Type cell (fi=0): container invisible — pill/dot handles cursor visually */
.wt__cell--type.wt__cell--nav-selected-p {
  outline: none;
  background: transparent;
  box-shadow: none;
}


/* Inactive zone while editing — dimmed */
.wt__row--editing-planned .wt__cell-c {
  opacity: 0.45;
  pointer-events: none;
}

.wt__row--editing-completed .wt__cell-p {
  opacity: 0.45;
  pointer-events: none;
}


/* ── Type dot ── */
.wt__type-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 999px;
  background: var(--eb-border);
  flex-shrink: 0;
}
.wt__type-dot--run { background: var(--eb-blue); }
.wt__type-dot--workout { background: var(--eb-lime); }
.wt__type-dot--empty { background: transparent; border: 1px dashed var(--eb-border); }

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
  white-space: nowrap;
}
.wt__type-pill--run:hover {
  border-color: rgba(56, 189, 248, .75);
  background: rgba(56, 189, 248, .14);
  box-shadow: 0 0 0 2.5px rgba(56, 189, 248, .18), 0 0 6px rgba(56, 189, 248, .12);
}

.wt__type-pill--workout:hover {
  border-color: rgba(200, 255, 0, .75);
  background: rgba(200, 255, 0, .12);
  box-shadow: 0 0 0 2.5px rgba(200, 255, 0, .15), 0 0 6px rgba(200, 255, 0, .10);
}
.wt__type-pill--run {
  color: var(--eb-blue);
  border: 1px solid rgba(56,189,248,.35);
}
.wt__type-pill--workout {
  color: var(--eb-lime);
  border: 1px solid rgba(200,255,0,.35);
}

/* ── Pill/dot cursor (fi=0 nav selection) — pill-hugging ── */
.wt__type-pill--run.wt__type-pill--cursor {
  border-color: rgba(56, 189, 248, .75);
  background: rgba(56, 189, 248, .14);
  box-shadow: 0 0 0 2.5px rgba(56, 189, 248, .18), 0 0 6px rgba(56, 189, 248, .12);
}

.wt__type-pill--workout.wt__type-pill--cursor {
  border-color: rgba(200, 255, 0, .75);
  background: rgba(200, 255, 0, .12);
  box-shadow: 0 0 0 2.5px rgba(200, 255, 0, .15), 0 0 6px rgba(200, 255, 0, .10);
}

.wt__type-dot--cursor {
  border: 1.5px solid rgba(56, 189, 248, .75) !important;
  background: rgba(56, 189, 248, .14) !important;
  box-shadow: 0 0 0 2.5px rgba(56, 189, 248, .18), 0 0 6px rgba(56, 189, 248, .10);
}

.wt__type-pill--cursor:hover { opacity: 1; }

/* ── Text content ── */
.wt__title-text {
  display: block;
  white-space: nowrap;
  color: var(--eb-text);
  font-size: 0.875rem;
}

.wt__notes-text {
  display: block;
  white-space: nowrap;
  color: var(--eb-text);
  font-size: 0.75rem;
}

.wt__intervals-text {
  display: block;
  white-space: nowrap;
  color: var(--eb-text-soft);
  font-size: 0.75rem;
  font-family: var(--eb-font-mono);
}

.wt__empty-hint {
  color: var(--eb-text-muted);
  font-size: 0.75rem;
  opacity: 0.5;
}

.wt__num-val {
  display: block;
  min-height: 1.1em;
  line-height: 1.4;
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}
.wt__num-val--done { color: var(--eb-lime); }
.wt__num-val--hr { color: var(--eb-text); }

.wt__p2-label {
  display: inline-flex;
  align-items: center;
  min-height: 1.1rem;
  padding: 0 0.4rem;
  margin-right: 0.4rem;
  border: 1px solid rgba(56,189,248,.25);
  border-radius: 999px;
  color: var(--eb-blue);
  font-size: 0.5625rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  vertical-align: middle;
}

/* ── Edit inputs ── */
.wt__input,
.wt__textarea {
  width: 100%;
  border: 1px solid rgba(200,255,0,.25);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  font: inherit;
  font-size: 0.8125rem;
  padding: 0.3rem 0.45rem;
}

.wt__input:focus,
.wt__textarea:focus {
  outline: none;
  border-color: rgba(200,255,0,.5);
  box-shadow: 0 0 0 2px rgba(200,255,0,.08);
}

.wt__input--num { text-align: right; font-family: var(--eb-font-mono); }

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


/* ── Nav cursor highlight — zone-aware ── */
.wt__cell--nav-selected-p {
  outline: 1px solid rgba(56, 189, 248, .55);
  background: rgba(56, 189, 248, .07);
  box-shadow: inset 0 0 0 1px rgba(56, 189, 248, .18);
  border-radius: 4px;
}

.wt__cell--nav-selected-c {
  outline: 1px solid rgba(200, 255, 0, .55);
  background: rgba(200, 255, 0, .07);
  box-shadow: inset 0 0 0 1px rgba(200, 255, 0, .18);
  border-radius: 4px;
}

/* Nav cursor: pointer cursor on selected cells */
.wt__cell--nav-selected-p,
.wt__cell--nav-selected-c {
  cursor: pointer;
}


/* ── Cell-level flash — zone-aware ── */
@keyframes cell-flash-err {
  0%   { background-color: rgba(244, 63, 94, 0.22); }
  100% { background-color: transparent; }
}

.wt__cell--flash-err  { animation: cell-flash-err 0.8s ease-out forwards; }

/* ── Nav mode display spans ── */
.wt__nav-cell {
  display: block;
  width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--eb-text);
  font-size: 0.8125rem;
  min-height: 1.25rem;
  line-height: 1.5;
}

.wt__nav-cell--num {
  font-family: var(--eb-font-mono);
  font-size: 0.75rem;
  text-align: right;
}

/* ── Summary row ── */
.wt__summary-row {
  padding: 0.5rem 1rem;
  background: rgba(255,255,255,.015);
  border-top: 1px solid var(--eb-border);
  align-items: center;
  min-height: 2.25rem;
}

.wt__summary-label {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding-left: 0;
}

.wt__summary-planned-km {
  display: flex;
  align-items: center;
  padding: 0 0.35rem;
  color: var(--eb-blue);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
  font-weight: 600;
}

.wt__summary-val {
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
  font-weight: 600;
}

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

/* ── Mobile ── */
@media (max-width: 767px) {
  /* Column headers hidden — redundant in stacked layout */
  .wt__head-row { display: none; }

  /* Each row: 2 rows — planned on top, completed below */
  .wt__cols {
    grid-template-columns: 44px 32px 36px 1fr;
    grid-template-rows: auto auto;
    min-height: unset;
  }

  /* Planned cells — row 1 */
  .wt__cell--date  { grid-row: 1; grid-column: 1; padding-left: 0.9rem; }
  .wt__cell--day   { grid-row: 1; grid-column: 2; }
  .wt__cell--type  { grid-row: 1; grid-column: 3; }
  .wt__cell--title { grid-row: 1; grid-column: 4; }
  .wt__cell--notes { display: none; }

  /* Separator — hidden on mobile */
  .wt__sep-col { display: none; }

  /* Completed cells — row 2 */
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

  /* intervals — hidden on mobile */
  .wt__cell--intervals { display: none; }

  /* Summary on mobile */
  .wt__summary-row {
    grid-template-columns: 44px 32px 36px 1fr;
    grid-template-rows: auto auto;
  }
  .wt__summary-label      { grid-row: 1; grid-column: 1 / 3; padding-left: 0.9rem; }
  .wt__summary-planned-km { grid-row: 1; grid-column: 3 / 5; }
  .wt__summary-val        { grid-row: 2; text-align: left; padding-left: 0.9rem; }
}
</style>
