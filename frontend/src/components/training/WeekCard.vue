<script setup lang="ts">
import type { DashboardWeek } from "@/api/training";
import CompletedRow from "@/components/training/CompletedRow.vue";
import PlannedRow from "@/components/training/PlannedRow.vue";
import EbCard from "@/components/ui/EbCard.vue";

defineProps<{
  week: DashboardWeek;
}>();

function formatRange(start: string, end: string) {
  const startDate = new Date(start);
  const endDate = new Date(end);
  return `${startDate.getDate()}.${startDate.getMonth() + 1}. - ${endDate.getDate()}.${endDate.getMonth() + 1}.`;
}
</script>

<template>
  <EbCard class="week-card">
    <div class="week-card__header">
      <div>
        <div class="week-card__eyebrow">Tyden {{ week.week_index }}</div>
        <div class="week-card__range">{{ formatRange(week.week_start, week.week_end) }}</div>
      </div>
      <div class="week-card__stats">
        <span>{{ week.planned_total_km_text }}</span>
        <span>{{ week.completed_total.km }} km</span>
        <span>{{ week.completed_total.time }} min</span>
      </div>
    </div>

    <div class="week-card__columns">
      <section class="week-card__column">
        <div class="week-card__column-label">Planned</div>
        <div class="week-card__rows">
          <PlannedRow v-for="(row, index) in week.planned_rows" :key="`planned-${row.id}-${row.date}-${index}`" :row="row" />
          <div v-if="week.planned_rows.length === 0" class="week-card__empty">No planned sessions in this week.</div>
        </div>
      </section>

      <section class="week-card__column">
        <div class="week-card__column-label">Completed</div>
        <div class="week-card__rows">
          <CompletedRow v-for="(row, index) in week.completed_rows" :key="`completed-${row.id}-${row.notes}-${index}`" :row="row" />
          <div v-if="week.completed_rows.length === 0" class="week-card__empty">No completed sessions yet.</div>
        </div>
      </section>
    </div>
  </EbCard>
</template>

<style scoped>
.week-card {
  overflow: hidden;
}

.week-card__header {
  display: flex;
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
  margin-top: 0.25rem;
  color: var(--eb-text-soft);
  font-size: 0.8125rem;
}

.week-card__stats {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--eb-text-soft);
  font-family: var(--eb-font-mono);
  font-size: 0.75rem;
}

.week-card__columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  padding: 1rem;
}

.week-card__column-label {
  margin-bottom: 0.75rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.week-card__rows {
  display: grid;
  gap: 0.75rem;
}

.week-card__empty {
  padding: 1rem 1.1rem;
  border: 1px dashed var(--eb-border);
  border-radius: var(--eb-radius-md);
  color: var(--eb-text-muted);
  font-size: 0.8125rem;
}

@media (max-width: 1023px) {
  .week-card__columns {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .week-card__header,
  .week-card__stats {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
