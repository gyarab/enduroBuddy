<script setup lang="ts">
import { computed } from "vue";

import EbCard from "@/components/ui/EbCard.vue";
import { useI18n } from "@/composables/useI18n";

const props = defineProps<{
  summary: {
    planned_sessions: number;
    completed_sessions: number;
    planned_km: number;
    completed_km: number;
    completed_minutes: number;
    completion_rate: number;
  };
}>();

const { t } = useI18n();

function formatMinutes(totalMinutes: number) {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return `${hours}h ${String(minutes).padStart(2, "0")}m`;
}

const completionTone = computed(() => {
  const rate = props.summary.completion_rate;
  if (rate >= 80) {
    return "summary-bar__value--good";
  }
  if (rate >= 50) {
    return "summary-bar__value--warn";
  }
  return "summary-bar__value--bad";
});
</script>

<template>
  <div class="summary-bar">
    <EbCard class="summary-bar__card">
      <div class="summary-bar__label">{{ t("summaryBar.trainings") }}</div>
      <div class="summary-bar__value">{{ props.summary.completed_sessions }} / {{ props.summary.planned_sessions }}</div>
      <div class="summary-bar__meta">{{ t("summaryBar.trainingsSubtext") }}</div>
    </EbCard>
    <EbCard class="summary-bar__card">
      <div class="summary-bar__label">{{ t("summaryBar.kilometers") }}</div>
      <div class="summary-bar__value">{{ props.summary.completed_km.toFixed(1) }} km</div>
      <div class="summary-bar__meta">{{ t("summaryBar.kmSubtext", { planned: props.summary.planned_km.toFixed(1) }) }}</div>
    </EbCard>
    <EbCard class="summary-bar__card">
      <div class="summary-bar__label">{{ t("summaryBar.time") }}</div>
      <div class="summary-bar__value">{{ formatMinutes(props.summary.completed_minutes) }}</div>
      <div class="summary-bar__meta">{{ t("summaryBar.timeSubtext") }}</div>
    </EbCard>
    <EbCard class="summary-bar__card">
      <div class="summary-bar__label">{{ t("summaryBar.completion") }}</div>
      <div class="summary-bar__value" :class="completionTone">{{ props.summary.completion_rate }} %</div>
      <div class="summary-bar__meta">{{ t("summaryBar.completionSubtext") }}</div>
    </EbCard>
  </div>
</template>

<style scoped>
.summary-bar {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.summary-bar__card {
  padding: 1rem 1.25rem;
}

.summary-bar__label {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary-bar__value {
  margin-top: 0.45rem;
  font-family: var(--eb-font-mono);
  font-size: 1.35rem;
}

.summary-bar__meta {
  margin-top: 0.3rem;
  color: var(--eb-text-muted);
  font-size: 0.75rem;
}

.summary-bar__value--good {
  color: var(--eb-lime);
}

.summary-bar__value--warn {
  color: var(--eb-warning);
}

.summary-bar__value--bad {
  color: var(--eb-danger);
}

@media (max-width: 1023px) {
  .summary-bar {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .summary-bar {
    grid-template-columns: 1fr;
  }
}
</style>
