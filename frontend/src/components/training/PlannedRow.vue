<script setup lang="ts">
import { computed } from "vue";

import type { TrainingRow } from "@/api/training";
import { useInlineEditor } from "@/composables/useInlineEditor";
import { useI18n } from "@/composables/useI18n";
import { useTrainingParser } from "@/composables/useTrainingParser";
import { useCoachStore } from "@/stores/coach";
import { useTrainingStore } from "@/stores/training";
import { useToastStore } from "@/stores/toasts";
import EbBadge from "@/components/ui/EbBadge.vue";
import EbButton from "@/components/ui/EbButton.vue";

const props = defineProps<{
  row: TrainingRow;
  editorContext?: "athlete" | "coach";
}>();

const trainingStore = useTrainingStore();
const coachStore = useCoachStore();
const toastStore = useToastStore();
const { t } = useI18n();
const editor = useInlineEditor(() => ({
  title: props.row.title === "-" ? "" : props.row.title,
  notes: props.row.notes,
  sessionType: props.row.session_type,
}));
const parserSource = computed(() => editor.draft.value.title);
const parser = useTrainingParser(parserSource);
const parserPreview = computed(() => parser.preview.value);
const dayLabel = computed(() => {
  if (props.row.day_label) {
    return props.row.day_label;
  }
  return props.row.is_second_phase ? "P2" : "?";
});

const metricsLabel = computed(() => props.row.planned_metrics?.planned_km_text || t("plannedRow.noKmHint"));
const confidenceClass = computed(() => {
  const confidence = props.row.planned_metrics?.planned_km_confidence || "low";
  return `training-row__metrics--${confidence}`;
});

function openEditor() {
  editor.open({
    title: props.row.title === "-" ? "" : props.row.title,
    notes: props.row.notes,
    sessionType: props.row.session_type,
  });
}

async function save() {
  if (!props.row.id) {
    editor.close();
    return;
  }

  editor.isSaving.value = true;
  editor.errorMessage.value = "";
  try {
    const updates: Array<{
      field: "title" | "notes" | "session_type";
      value: string;
    }> = [];

    if (editor.draft.value.title.trim() !== (props.row.title === "-" ? "" : props.row.title)) {
      updates.push({
        field: "title",
        value: editor.draft.value.title.trim(),
      });
    }

    if (editor.draft.value.notes.trim() !== props.row.notes) {
      updates.push({
        field: "notes",
        value: editor.draft.value.notes.trim(),
      });
    }

    if (editor.draft.value.sessionType !== props.row.session_type) {
      updates.push({
        field: "session_type",
        value: editor.draft.value.sessionType,
      });
    }

    if (updates.length > 0) {
      if (props.editorContext === "coach") {
        await coachStore.savePlannedDraft(props.row.id, updates);
      } else {
        await trainingStore.savePlannedDraft(props.row.id, updates);
      }
    }

    editor.close();
  } catch (error) {
    editor.errorMessage.value = error instanceof Error ? error.message : t("plannedRow.saveError");
    toastStore.push(editor.errorMessage.value, "danger");
  } finally {
    editor.isSaving.value = false;
  }
}

async function addSecondPhase() {
  if (!props.row.id) {
    return;
  }

  editor.isSaving.value = true;
  editor.errorMessage.value = "";
  try {
    if (props.editorContext === "coach") {
      await coachStore.addSecondPhase(props.row.id);
    } else {
      await trainingStore.addSecondPhase(props.row.id);
    }
    editor.close();
  } catch (error) {
    editor.errorMessage.value = error instanceof Error ? error.message : t("plannedRow.addSecondPhaseError");
    toastStore.push(editor.errorMessage.value, "danger");
  } finally {
    editor.isSaving.value = false;
  }
}

async function removeSecondPhase() {
  if (!props.row.id) {
    return;
  }

  editor.isSaving.value = true;
  editor.errorMessage.value = "";
  try {
    if (props.editorContext === "coach") {
      await coachStore.removeSecondPhase(props.row.id);
    } else {
      await trainingStore.removeSecondPhase(props.row.id);
    }
    editor.close();
  } catch (error) {
    editor.errorMessage.value = error instanceof Error ? error.message : t("plannedRow.removeSecondPhaseError");
    toastStore.push(editor.errorMessage.value, "danger");
  } finally {
    editor.isSaving.value = false;
  }
}

async function deletePlanned() {
  if (!props.row.id) {
    return;
  }
  const confirmed = window.confirm(t("plannedRow.confirmDelete"));
  if (!confirmed) {
    return;
  }

  editor.isSaving.value = true;
  editor.errorMessage.value = "";
  try {
    if (props.editorContext === "coach") {
      await coachStore.deletePlannedTrainingRow(props.row.id);
    } else {
      await trainingStore.deletePlannedTrainingRow(props.row.id);
    }
    editor.close();
  } catch (error) {
    editor.errorMessage.value = error instanceof Error ? error.message : t("plannedRow.deleteError");
    toastStore.push(editor.errorMessage.value, "danger");
  } finally {
    editor.isSaving.value = false;
  }
}
</script>

<template>
  <article class="training-row" :class="[`training-row--${row.status}`, { 'training-row--editing': editor.isOpen.value, 'training-row--second-phase': row.is_second_phase }]">
    <div
      class="training-row__head"
      :class="{ 'training-row__head--clickable': row.editable && !editor.isOpen.value }"
      @click="row.editable && !editor.isOpen.value && openEditor()"
    >
      <div class="training-row__body">
        <div class="training-row__day">
          <span class="training-row__day-label">{{ dayLabel }}</span>
          <span class="training-row__date">{{ row.date || "" }}</span>
        </div>

        <div class="training-row__content">
          <div class="training-row__title-wrap">
            <span class="training-row__type-dot" :class="`training-row__type-dot--${row.session_type.toLowerCase()}`" />
            <span v-if="row.is_second_phase" class="training-row__phase-label">{{ t("plannedRow.phase2") }}</span>
            <div class="training-row__title">{{ row.title }}</div>
          </div>
          <div v-if="row.notes" class="training-row__notes">{{ row.notes }}</div>
        </div>
      </div>

      <div class="training-row__meta">
        <div class="training-row__metrics-wrap">
          <div class="training-row__metrics" :class="confidenceClass">{{ metricsLabel }}</div>
          <div v-if="row.planned_metrics?.planned_km_show" class="training-row__km-popover">
            <div class="training-row__km-popover-content">
              <span v-if="row.planned_metrics.planned_km_line_km" class="training-row__km-line">{{ row.planned_metrics.planned_km_line_km }}</span>
              <span v-if="row.planned_metrics.planned_km_line_reason" class="training-row__km-reason">{{ row.planned_metrics.planned_km_line_reason }}</span>
              <span v-if="row.planned_metrics.planned_km_line_where" class="training-row__km-where">{{ row.planned_metrics.planned_km_line_where }}</span>
            </div>
          </div>
        </div>
        <EbBadge :tone="row.status === 'rest' ? 'neutral' : 'planned'">
          {{ row.status === "rest" ? t("plannedRow.rest") : t("plannedRow.plan") }}
        </EbBadge>
        <EbButton v-if="row.editable" variant="ghost" @click.stop="openEditor">{{ t("plannedRow.edit") }}</EbButton>
      </div>
    </div>

    <div v-if="editor.isOpen.value" class="training-row__editor">
      <div class="training-row__editor-grid">
        <label class="training-row__field">
          <span class="training-row__field-label">{{ t("plannedRow.session") }}</span>
          <select v-model="editor.draft.value.sessionType" class="training-row__select" :disabled="!editor.canInteract.value">
            <option value="RUN">{{ t("plannedRow.run") }}</option>
            <option value="WORKOUT">{{ t("plannedRow.workout") }}</option>
          </select>
        </label>

        <label class="training-row__field training-row__field--wide">
          <span class="training-row__field-label">{{ t("plannedRow.title") }}</span>
          <textarea v-model="editor.draft.value.title" class="training-row__textarea" :disabled="!editor.canInteract.value" />
        </label>

        <label class="training-row__field training-row__field--wide">
          <span class="training-row__field-label">{{ t("plannedRow.coachNotes") }}</span>
          <textarea v-model="editor.draft.value.notes" class="training-row__textarea" :disabled="!editor.canInteract.value" />
        </label>
      </div>

      <p v-if="editor.errorMessage.value" class="training-row__error">{{ editor.errorMessage.value }}</p>

        <div v-if="parserPreview.hasStructuredPreview" class="training-row__preview">
        <div class="training-row__preview-head">
          <span>{{ t("plannedRow.parsedPreview") }}</span>
          <span>{{ parserPreview.kmText }}</span>
        </div>

        <div v-if="parserPreview.detectedTags.length" class="training-row__preview-tags">
          <span v-for="tag in parserPreview.detectedTags" :key="tag" class="training-row__preview-tag">{{ tag }}</span>
        </div>

        <div v-if="parserPreview.intervals.length" class="training-row__preview-list">
          <div v-for="(interval, index) in parserPreview.intervals" :key="`${interval.label}-${index}`" class="training-row__preview-item">
            <span>{{ interval.label }}</span>
            <span>{{ interval.reps }}x {{ interval.distanceLabel }}</span>
            <span>{{ interval.estimatedKm.toFixed(1) }} km</span>
          </div>
        </div>

        <p v-if="parserPreview.warning" class="training-row__preview-warning">
          {{ parserPreview.warning }}
        </p>
      </div>

      <div class="training-row__editor-actions">
        <EbButton
          v-if="row.can_add_second_phase"
          variant="secondary"
          :disabled="editor.isSaving.value"
          @click="addSecondPhase"
        >
          {{ t("plannedRow.addSecondPhase") }}
        </EbButton>
        <EbButton
          v-if="row.can_remove_second_phase"
          variant="danger"
          :disabled="editor.isSaving.value"
          @click="removeSecondPhase"
        >
          {{ t("plannedRow.removeSecondPhase") }}
        </EbButton>
        <EbButton
          v-if="row.editable && !row.is_second_phase"
          variant="danger"
          :disabled="editor.isSaving.value"
          @click="deletePlanned"
        >
          {{ t("plannedRow.delete") }}
        </EbButton>
        <EbButton variant="ghost" :disabled="editor.isSaving.value" @click="editor.close">{{ t("plannedRow.cancel") }}</EbButton>
        <EbButton :disabled="editor.isSaving.value" @click="save">
          {{ editor.isSaving.value ? t("plannedRow.saving") : t("plannedRow.save") }}
        </EbButton>
      </div>
    </div>
  </article>
</template>

<style scoped>
.training-row {
  display: grid;
  gap: 0.9rem;
  padding: 0.875rem 1rem;
  border: 1px solid var(--eb-border);
  border-left-width: 3px;
  border-radius: var(--eb-radius-md);
  background: var(--eb-surface);
}

.training-row--planned {
  border-left-color: var(--eb-blue);
}

.training-row--rest {
  border-left-color: var(--eb-border);
}

.training-row--editing {
  border-color: rgba(200, 255, 0, 0.22);
  box-shadow: var(--eb-glow-lime);
}

.training-row--second-phase {
  margin-left: 1.25rem;
  border-left-style: dashed;
  background: rgba(255, 255, 255, 0.02);
}

.training-row__head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.training-row__head--clickable {
  cursor: pointer;
}

.training-row__body {
  display: flex;
  gap: 1rem;
}

.training-row__day {
  min-width: 4.5rem;
}

.training-row__day-label {
  display: block;
  color: var(--eb-text-soft);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.training-row__date {
  color: var(--eb-text-muted);
  font-size: 0.75rem;
}

.training-row__title-wrap {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.training-row__phase-label {
  display: inline-flex;
  align-items: center;
  min-height: 1.25rem;
  padding: 0 0.45rem;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: 999px;
  color: var(--eb-blue);
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.training-row__type-dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 999px;
  background: var(--eb-text-muted);
}

.training-row__type-dot--run {
  background: var(--eb-blue);
}

.training-row__type-dot--workout {
  background: var(--eb-lime);
}

.training-row__title {
  font-size: 0.9375rem;
  font-weight: 500;
}

.training-row__notes {
  margin-top: 0.2rem;
  color: var(--eb-text-muted);
  font-size: 0.75rem;
}

.training-row__meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.training-row__metrics {
  color: var(--eb-text-soft);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}

.training-row__metrics--high {
  color: var(--eb-text);
}

.training-row__metrics--medium {
  color: var(--eb-warning);
}

.training-row__metrics--low {
  color: var(--eb-text-muted);
}

.training-row__metrics-wrap {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.training-row__km-popover {
  display: none;
  position: absolute;
  bottom: calc(100% + 0.4rem);
  right: 0;
  z-index: 10;
  min-width: 12rem;
  padding: 0.6rem 0.75rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-surface);
  box-shadow: var(--eb-shadow-soft);
}

.training-row__metrics-wrap:hover .training-row__km-popover {
  display: block;
}

.training-row__km-popover-content {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.training-row__km-line {
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}

.training-row__km-reason {
  color: var(--eb-text-soft);
  font-size: 0.75rem;
}

.training-row__km-where {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
}

.training-row__editor {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid rgba(200, 255, 0, 0.18);
  border-radius: var(--eb-radius-md);
  background: rgba(200, 255, 0, 0.04);
}

.training-row__editor-grid {
  display: grid;
  grid-template-columns: 10rem minmax(0, 1fr);
  gap: 0.9rem 1rem;
}

.training-row__field {
  display: grid;
  gap: 0.45rem;
}

.training-row__field--wide {
  grid-column: 1 / -1;
}

.training-row__field-label {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.training-row__textarea,
.training-row__select {
  width: 100%;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.75rem 0.85rem;
}

.training-row__textarea {
  min-height: 5rem;
  resize: vertical;
  font-family: var(--eb-font-mono);
}

.training-row__textarea:focus,
.training-row__select:focus {
  outline: none;
  border-color: rgba(200, 255, 0, 0.4);
  box-shadow: var(--eb-glow-lime);
}

.training-row__editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.training-row__preview {
  display: grid;
  gap: 0.7rem;
  padding: 0.9rem 1rem;
  border: 1px solid rgba(200, 255, 0, 0.16);
  border-radius: var(--eb-radius-sm);
  background: rgba(200, 255, 0, 0.06);
}

.training-row__preview-head,
.training-row__preview-item {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.75rem;
  align-items: center;
}

.training-row__preview-head {
  color: var(--eb-text-soft);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.training-row__preview-list {
  display: grid;
  gap: 0.45rem;
}

.training-row__preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.training-row__preview-tag {
  display: inline-flex;
  align-items: center;
  min-height: 1.5rem;
  padding: 0 0.55rem;
  border: 1px solid rgba(200, 255, 0, 0.18);
  border-radius: 999px;
  color: var(--eb-text-soft);
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.training-row__preview-item {
  color: var(--eb-lime);
  font-family: var(--eb-font-mono);
  font-size: 0.75rem;
}

.training-row__preview-warning {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: 0.75rem;
}

.training-row__error {
  margin: 0;
  color: var(--eb-danger);
  font-size: 0.8125rem;
}

@media (max-width: 767px) {
  .training-row__head,
  .training-row__body,
  .training-row__meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .training-row__editor-grid {
    grid-template-columns: 1fr;
  }
}
</style>
