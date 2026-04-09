<script setup lang="ts">
import { computed } from "vue";

import type { TrainingRow } from "@/api/training";
import { useInlineEditor } from "@/composables/useInlineEditor";
import { useI18n } from "@/composables/useI18n";
import { useTrainingStore } from "@/stores/training";
import { useToastStore } from "@/stores/toasts";
import EbButton from "@/components/ui/EbButton.vue";

const props = defineProps<{
  row: TrainingRow;
}>();

const trainingStore = useTrainingStore();
const toastStore = useToastStore();
const { t } = useI18n();
const editor = useInlineEditor(() => ({
  km: props.row.completed_metrics?.km || "",
  minutes: props.row.completed_metrics?.minutes || "",
  details: props.row.completed_metrics?.details || "",
  avgHr: props.row.completed_metrics?.avg_hr?.toString() || "",
  maxHr: props.row.completed_metrics?.max_hr?.toString() || "",
}));

const plannedSummary = computed(() => {
  return props.row.planned_metrics?.planned_km_text || t("completedEditor.entryFallback");
});

function openEditor() {
  editor.open({
    km: props.row.completed_metrics?.km || "",
    minutes: props.row.completed_metrics?.minutes || "",
    details: props.row.completed_metrics?.details || "",
    avgHr: props.row.completed_metrics?.avg_hr?.toString() || "",
    maxHr: props.row.completed_metrics?.max_hr?.toString() || "",
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
      field: "km" | "min" | "third" | "avg_hr" | "max_hr";
      value: string;
    }> = [];

    if ((props.row.completed_metrics?.km || "") !== editor.draft.value.km.trim()) {
      updates.push({ field: "km", value: editor.draft.value.km.trim() });
    }
    if ((props.row.completed_metrics?.minutes || "") !== editor.draft.value.minutes.trim()) {
      updates.push({ field: "min", value: editor.draft.value.minutes.trim() });
    }
    if ((props.row.completed_metrics?.details || "") !== editor.draft.value.details.trim()) {
      updates.push({ field: "third", value: editor.draft.value.details.trim() });
    }
    if ((props.row.completed_metrics?.avg_hr?.toString() || "") !== editor.draft.value.avgHr.trim()) {
      updates.push({ field: "avg_hr", value: editor.draft.value.avgHr.trim() });
    }
    if ((props.row.completed_metrics?.max_hr?.toString() || "") !== editor.draft.value.maxHr.trim()) {
      updates.push({ field: "max_hr", value: editor.draft.value.maxHr.trim() });
    }

    if (updates.length > 0) {
      await trainingStore.saveCompletedDraft(props.row.id, updates);
    }
    editor.close();
  } catch (error) {
    editor.errorMessage.value = error instanceof Error ? error.message : t("completedEditor.saveError");
    toastStore.push(editor.errorMessage.value, "danger");
  } finally {
    editor.isSaving.value = false;
  }
}
</script>

<template>
  <div class="completed-editor-wrap">
    <EbButton v-if="row.editable" variant="ghost" @click="openEditor">{{ t("completedEditor.edit") }}</EbButton>

    <div v-if="editor.isOpen.value" class="completed-editor">
      <div class="completed-editor__plan">{{ t("completedEditor.plan", { value: plannedSummary }) }}</div>

      <div class="completed-editor__grid">
        <label class="completed-editor__field">
          <span class="completed-editor__label">{{ t("completedEditor.km") }}</span>
          <input v-model="editor.draft.value.km" class="completed-editor__input" :disabled="!editor.canInteract.value" />
        </label>
        <label class="completed-editor__field">
          <span class="completed-editor__label">{{ t("completedEditor.min") }}</span>
          <input v-model="editor.draft.value.minutes" class="completed-editor__input" :disabled="!editor.canInteract.value" />
        </label>
        <label class="completed-editor__field">
          <span class="completed-editor__label">{{ t("completedEditor.avgHr") }}</span>
          <input v-model="editor.draft.value.avgHr" class="completed-editor__input" :disabled="!editor.canInteract.value" />
        </label>
        <label class="completed-editor__field">
          <span class="completed-editor__label">{{ t("completedEditor.maxHr") }}</span>
          <input v-model="editor.draft.value.maxHr" class="completed-editor__input" :disabled="!editor.canInteract.value" />
        </label>
        <label class="completed-editor__field completed-editor__field--wide">
          <span class="completed-editor__label">{{ t("completedEditor.details") }}</span>
          <textarea v-model="editor.draft.value.details" class="completed-editor__textarea" :disabled="!editor.canInteract.value" />
        </label>
      </div>

      <p v-if="editor.errorMessage.value" class="completed-editor__error">{{ editor.errorMessage.value }}</p>

      <div class="completed-editor__actions">
        <EbButton variant="ghost" :disabled="editor.isSaving.value" @click="editor.close">{{ t("completedEditor.cancel") }}</EbButton>
        <EbButton :disabled="editor.isSaving.value" @click="save">
          {{ editor.isSaving.value ? t("completedEditor.saving") : t("completedEditor.save") }}
        </EbButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.completed-editor-wrap {
  display: grid;
  gap: 0.75rem;
}

.completed-editor {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid rgba(200, 255, 0, 0.18);
  border-radius: var(--eb-radius-md);
  background: rgba(200, 255, 0, 0.04);
}

.completed-editor__plan {
  color: var(--eb-text-soft);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}

.completed-editor__grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.9rem;
}

.completed-editor__field {
  display: grid;
  gap: 0.45rem;
}

.completed-editor__field--wide {
  grid-column: 1 / -1;
}

.completed-editor__label {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.completed-editor__input,
.completed-editor__textarea {
  width: 100%;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.75rem 0.85rem;
  font-family: var(--eb-font-mono);
}

.completed-editor__textarea {
  min-height: 5rem;
  resize: vertical;
}

.completed-editor__input:focus,
.completed-editor__textarea:focus {
  outline: none;
  border-color: rgba(200, 255, 0, 0.4);
  box-shadow: var(--eb-glow-lime);
}

.completed-editor__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.completed-editor__error {
  margin: 0;
  color: var(--eb-danger);
  font-size: 0.8125rem;
}

@media (max-width: 767px) {
  .completed-editor__grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
