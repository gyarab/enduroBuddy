<script setup lang="ts">
import { ref } from "vue";

import type { TrainingRow } from "@/api/training";
import { useI18n } from "@/composables/useI18n";
import CompletedEditor from "@/components/training/CompletedEditor.vue";
import EbBadge from "@/components/ui/EbBadge.vue";

const props = defineProps<{
  row: TrainingRow;
}>();
const { t } = useI18n();

const editorRef = ref<InstanceType<typeof CompletedEditor>>();

function handleRowClick() {
  if (props.row.editable && !props.row.has_linked_activity && !editorRef.value?.isOpen) {
    editorRef.value?.openEditor();
  }
}
</script>

<template>
  <article
    class="completed-row"
    :class="[`completed-row--${row.status}`, { 'completed-row--clickable': row.editable && !row.has_linked_activity }]"
    @click="handleRowClick"
  >
    <div class="completed-row__main">
      <div class="completed-row__content">
        <div class="completed-row__metrics">
          {{ row.completed_metrics?.km || "-" }} km - {{ row.completed_metrics?.minutes || "-" }} min
        </div>
        <div v-if="row.completed_metrics?.details" class="completed-row__details">
          {{ row.completed_metrics?.details }}
        </div>
      </div>

      <div class="completed-row__meta">
        <div class="completed-row__hr">
          {{ t("completedRow.hr", { avg: row.completed_metrics?.avg_hr ?? "-", max: row.completed_metrics?.max_hr ?? "-" }) }}
        </div>
        <EbBadge v-if="row.has_linked_activity" tone="neutral" class="completed-row__garmin-badge">
          {{ t("completedRow.garminLinked") }}
        </EbBadge>
        <EbBadge :tone="row.status === 'done' ? 'done' : 'missed'">
          {{ row.status === "done" ? t("completedRow.done") : t("completedRow.missed") }}
        </EbBadge>
      </div>
    </div>

    <CompletedEditor v-if="row.editable && !row.has_linked_activity" ref="editorRef" :row="row" />
  </article>
</template>

<style scoped>
.completed-row {
  display: grid;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border: 1px solid var(--eb-border);
  border-left-width: 3px;
  border-radius: var(--eb-radius-md);
  background: var(--eb-surface);
}

.completed-row--clickable {
  cursor: pointer;
}

.completed-row--done {
  border-left-color: var(--eb-lime);
}

.completed-row--missed {
  border-left-color: rgba(244, 63, 94, 0.45);
}

.completed-row__main {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.completed-row__metrics {
  color: var(--eb-lime);
  font-family: var(--eb-font-mono);
  font-size: 0.875rem;
}

.completed-row--missed .completed-row__metrics {
  color: var(--eb-text-soft);
}

.completed-row__details {
  margin-top: 0.25rem;
  color: var(--eb-text-muted);
  font-size: 0.75rem;
}

.completed-row__meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.completed-row__hr {
  color: var(--eb-text-soft);
  font-family: var(--eb-font-mono);
  font-size: 0.75rem;
}

@media (max-width: 767px) {
  .completed-row__main,
  .completed-row__meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
