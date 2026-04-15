<script setup lang="ts">
import { computed, reactive, ref } from "vue";

import type { DashboardWeek, TrainingRow, PlannedTrainingDraft } from "@/api/training";
import { garminWeekSync } from "@/api/imports";
import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";
import { useCoachStore } from "@/stores/coach";
import { useTrainingStore } from "@/stores/training";
import { useToastStore } from "@/stores/toasts";
import EbCard from "@/components/ui/EbCard.vue";

const props = defineProps<{
  week: DashboardWeek;
  editorContext?: "athlete" | "coach";
}>();

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
    authStore.user?.capabilities.has_garmin_connection &&
    authStore.user?.capabilities.garmin_sync_enabled,
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
  if (val === null || val === undefined || val === "" || val === "0" || val === 0) return "-";
  const m = typeof val === "string" ? parseInt(val) : val;
  if (isNaN(m) || m === 0) return "-";
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

function openEdit(slot: DaySlot, focusField = "title") {
  if (editingRows.has(slot.date)) return;
  const planned = slot.planned.find((r) => !r.is_second_phase) ?? null;
  const completed = slot.completed[0] ?? null;
  const canEditPlanned = planned ? planned.editable : true; // empty days are editable for coaches/athletes
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

async function saveRow(slot: DaySlot, edit: RowEdit) {
  if (!edit.isDirty) {
    editingRows.delete(slot.date);
    return;
  }
  if (edit.isSaving) return;
  edit.isSaving = true;
  try {
    // Save / create planned
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

    // Save completed
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

// ── Flash feedback ───────────────────────────────────────────
const flashingRows = reactive<Set<string>>(new Set());

function flashRow(date: string) {
  flashingRows.add(date);
  setTimeout(() => flashingRows.delete(date), 600);
}

// ── Auto-save helpers ────────────────────────────────────────
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

function canEditCompleted(slot: DaySlot): boolean {
  const c = slot.completed[0];
  return !!c && c.editable && !c.has_linked_activity;
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
          :class="{
            'wt__row--editing': isEditing(slot.date),
            'wt__row--done': slot.completed[0]?.status === 'done',
            'wt__row--missed': slot.completed[0]?.status === 'missed',
            'wt__row--saved': flashingRows.has(slot.date),
          }"
          @focusout="onRowFocusOut(slot, $event)"
        >
          <!-- Date -->
          <div class="wt__cell wt__cell--date wt__cell--readonly">{{ slot.dateLabel }}</div>

          <!-- Day -->
          <div class="wt__cell wt__cell--day wt__cell--readonly">{{ slot.dayLabel }}</div>

          <!-- Session type -->
          <div class="wt__cell wt__cell--type" @click.stop>
            <button
              v-if="isEditing(slot.date) && getEdit(slot.date)"
              class="wt__type-pill"
              :class="`wt__type-pill--${getEdit(slot.date)!.sessionType.toLowerCase()}`"
              type="button"
              @click.stop="toggleSessionType(slot)"
            >{{ getEdit(slot.date)!.sessionType === 'RUN' ? 'RUN' : 'WKT' }}</button>
            <button
              v-else-if="slot.planned[0]"
              class="wt__type-pill"
              :class="`wt__type-pill--${slot.planned[0].session_type.toLowerCase()}`"
              type="button"
              @click.stop="toggleSessionType(slot)"
            >{{ slot.planned[0].session_type === 'RUN' ? 'RUN' : 'WKT' }}</button>
            <span v-else class="wt__type-dot wt__type-dot--empty" />
          </div>

          <!-- Training title -->
          <div class="wt__cell wt__cell--title" @click.stop="!isEditing(slot.date) && openEdit(slot, 'title')">
            <template v-if="isEditing(slot.date) && getEdit(slot.date)">
              <textarea
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

          <!-- Separator -->
          <div class="wt__sep-col" />

          <!-- km -->
          <div class="wt__cell wt__cell--num" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'km')">
            <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input v-model="getEdit(slot.date)!.km" v-autofocus="getEdit(slot.date)!.focusField === 'km'" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" @click.stop @input="onFieldInput(slot.date, slot)" />
            </template>
            <template v-else>
              <span class="wt__num-val wt__num-val--done">{{ slot.completed[0]?.completed_metrics?.km || "-" }}</span>
            </template>
          </div>

          <!-- Time (HH:MM) -->
          <div class="wt__cell wt__cell--num" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'minutes')">
            <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input v-model="getEdit(slot.date)!.minutes" v-autofocus="getEdit(slot.date)!.focusField === 'minutes'" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" placeholder="min" @click.stop @input="onFieldInput(slot.date, slot)" />
            </template>
            <template v-else>
              <span class="wt__num-val wt__num-val--done">{{ formatMinutes(slot.completed[0]?.completed_metrics?.minutes) }}</span>
            </template>
          </div>

          <!-- Intervals / details -->
          <div class="wt__cell wt__cell--intervals" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'details')">
            <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input v-model="getEdit(slot.date)!.details" v-autofocus="getEdit(slot.date)!.focusField === 'details'" class="wt__input" :disabled="getEdit(slot.date)!.isSaving" @click.stop @input="onFieldInput(slot.date, slot)" />
            </template>
            <template v-else>
              <span class="wt__intervals-text">{{ slot.completed[0]?.completed_metrics?.details }}</span>
            </template>
          </div>

          <!-- Avg HR -->
          <div class="wt__cell wt__cell--num" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'avgHr')">
            <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input v-model="getEdit(slot.date)!.avgHr" v-autofocus="getEdit(slot.date)!.focusField === 'avgHr'" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" @click.stop @input="onFieldInput(slot.date, slot)" />
            </template>
            <template v-else>
              <span class="wt__num-val wt__num-val--hr">{{ slot.completed[0]?.completed_metrics?.avg_hr ?? "-" }}</span>
            </template>
          </div>

          <!-- Max HR -->
          <div class="wt__cell wt__cell--num" @click.stop="!isEditing(slot.date) && canEditCompleted(slot) && openEdit(slot, 'maxHr')">
            <template v-if="isEditing(slot.date) && getEdit(slot.date) && getEdit(slot.date)!.completedId">
              <input v-model="getEdit(slot.date)!.maxHr" v-autofocus="getEdit(slot.date)!.focusField === 'maxHr'" class="wt__input wt__input--num" :disabled="getEdit(slot.date)!.isSaving" @click.stop @input="onFieldInput(slot.date, slot)" />
            </template>
            <template v-else>
              <span class="wt__num-val wt__num-val--hr">{{ slot.completed[0]?.completed_metrics?.max_hr ?? "-" }}</span>
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
        <div class="wt__summary-label" style="grid-column: 1 / 6">{{ t("weekCard.total") }}</div>
        <div class="wt__sep-col" />
        <div class="wt__cell wt__cell--num wt__summary-val">{{ week.completed_total.km }}</div>
        <div class="wt__cell wt__cell--num wt__summary-val">{{ formatMinutes(week.completed_total.time) }}</div>
        <div class="wt__cell wt__cell--intervals" />
        <div class="wt__cell wt__cell--num wt__summary-val wt__num-val--hr">{{ week.completed_total.avg_hr ?? "-" }}</div>
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
  min-width: 100%;
  width: max-content;
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
  grid-template-columns: 52px 40px 44px minmax(12rem, 2fr) minmax(6rem, 1fr) 2px 64px 56px max-content 52px 52px;
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
  padding: 0 1rem;
  border-bottom: 1px solid var(--eb-border-soft);
  min-height: 2.75rem;
  align-items: center;
  transition: background-color 100ms;
}

.wt__row:last-of-type { border-bottom: none; }

.wt__row--clickable { cursor: pointer; }
.wt__row--clickable:hover { background: rgba(255,255,255,.025); }

.wt__row--editing {
  background: rgba(200,255,0,.04);
  cursor: default;
}

.wt__row--done { border-left: 2px solid var(--eb-lime); padding-left: calc(1rem - 2px); }
.wt__row--missed { border-left: 2px solid rgba(244,63,94,.5); padding-left: calc(1rem - 2px); }

.wt__row--p2 { opacity: 0.75; }

.wt__row--saved {
  animation: row-saved-flash 600ms ease-out forwards;
}

@keyframes row-saved-flash {
  0%   { background-color: rgba(200,255,0,.12); }
  100% { background-color: transparent; }
}

/* ── Cells ── */
.wt__cell {
  padding: 0.3rem 0.35rem;
  font-size: 0.8125rem;
}

.wt__cell--date {
  color: var(--eb-text-soft);
  font-family: var(--eb-font-mono);
  font-size: 0.75rem;
  padding-left: 0;
}

.wt__cell--day {
  color: var(--eb-text-muted);
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
  color: var(--eb-text-muted);
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
  color: var(--eb-text-muted);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}
.wt__num-val--done { color: var(--eb-lime); }
.wt__num-val--hr { color: var(--eb-text-soft); }

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
  white-space: nowrap;
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

.wt__summary-val {
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
  font-weight: 600;
}

/* ── Responsive ── */
@media (max-width: 1023px) {
  .wt__cols {
    grid-template-columns: 48px 36px 40px minmax(10rem, 2fr) minmax(5rem, 1fr) 2px 54px 48px 0 44px 44px;
  }
  .wt__cell--intervals { display: none; }
}

@media (max-width: 767px) {
  .wt__cols {
    grid-template-columns: 44px 32px 38px minmax(8rem, 1fr) 2px 52px 46px 42px 42px;
  }
  .wt__h--type,
  .wt__cell--type,
  .wt__cell--notes,
  .wt__h:nth-child(5) { display: none; }
}
</style>
