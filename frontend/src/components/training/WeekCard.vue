<script setup lang="ts">
import { ref } from "vue";

import type { DashboardWeek, PlannedTrainingDraft } from "@/api/training";
import { useI18n } from "@/composables/useI18n";
import { useCoachStore } from "@/stores/coach";
import { useTrainingStore } from "@/stores/training";
import { useToastStore } from "@/stores/toasts";
import CompletedRow from "@/components/training/CompletedRow.vue";
import PlannedRow from "@/components/training/PlannedRow.vue";
import EbCard from "@/components/ui/EbCard.vue";
import EbButton from "@/components/ui/EbButton.vue";

const props = defineProps<{
  week: DashboardWeek;
  editorContext?: "athlete" | "coach";
}>();
const { t } = useI18n();
const trainingStore = useTrainingStore();
const coachStore = useCoachStore();
const toastStore = useToastStore();
const isCreateOpen = ref(false);
const isCreating = ref(false);
const createError = ref("");
const createDraft = ref<PlannedTrainingDraft>({
  date: props.week.week_start,
  title: "",
  session_type: "RUN",
});

function formatRange(start: string, end: string) {
  const startDate = new Date(start);
  const endDate = new Date(end);
  return `${startDate.getDate()}.${startDate.getMonth() + 1}. - ${endDate.getDate()}.${endDate.getMonth() + 1}.`;
}

function openCreate() {
  createDraft.value = {
    date: props.week.week_start,
    title: "",
    session_type: "RUN",
  };
  createError.value = "";
  isCreateOpen.value = true;
}

async function createPlanned() {
  isCreating.value = true;
  createError.value = "";
  try {
    if (props.editorContext === "coach") {
      await coachStore.addPlannedTraining(createDraft.value);
    } else {
      await trainingStore.addPlannedTraining(createDraft.value);
    }
    isCreateOpen.value = false;
  } catch (error) {
    createError.value = error instanceof Error ? error.message : t("weekCard.createError");
    toastStore.push(createError.value, "danger");
  } finally {
    isCreating.value = false;
  }
}
</script>

<template>
  <EbCard class="week-card">
    <div class="week-card__header">
      <div>
        <div class="week-card__eyebrow">{{ t("weekCard.week", { index: week.week_index }) }}</div>
        <div class="week-card__range">{{ formatRange(week.week_start, week.week_end) }}</div>
      </div>
      <div class="week-card__stats">
        <span>{{ week.planned_total_km_text }}</span>
        <span>{{ t("weekCard.completedKm", { value: week.completed_total.km }) }}</span>
        <span>{{ t("weekCard.completedMinutes", { value: week.completed_total.time }) }}</span>
      </div>
    </div>

    <div class="week-card__columns">
      <section class="week-card__column">
        <div class="week-card__column-label">{{ t("weekCard.planned") }}</div>
        <div class="week-card__rows">
          <PlannedRow
            v-for="(row, index) in week.planned_rows"
            :key="`planned-${row.id}-${row.date}-${index}`"
            :row="row"
            :editor-context="editorContext || 'athlete'"
          />
          <div v-if="week.planned_rows.length === 0" class="week-card__empty">{{ t("weekCard.emptyPlanned") }}</div>
          <EbButton variant="secondary" @click="openCreate">{{ t("weekCard.addPlanned") }}</EbButton>

          <form v-if="isCreateOpen" class="week-card__create" @submit.prevent="createPlanned">
            <label class="week-card__create-field">
              <span>{{ t("weekCard.date") }}</span>
              <input v-model="createDraft.date" type="date" :disabled="isCreating" />
            </label>
            <label class="week-card__create-field">
              <span>{{ t("weekCard.newTitle") }}</span>
              <input v-model="createDraft.title" :disabled="isCreating" />
            </label>
            <label class="week-card__create-field">
              <span>{{ t("weekCard.session") }}</span>
              <select v-model="createDraft.session_type" :disabled="isCreating">
                <option value="RUN">{{ t("weekCard.run") }}</option>
                <option value="WORKOUT">{{ t("weekCard.workout") }}</option>
              </select>
            </label>
            <p v-if="createError" class="week-card__create-error">{{ createError }}</p>
            <div class="week-card__create-actions">
              <EbButton type="button" variant="ghost" :disabled="isCreating" @click="isCreateOpen = false">{{ t("plannedRow.cancel") }}</EbButton>
              <EbButton type="submit" :disabled="isCreating">{{ isCreating ? t("weekCard.creating") : t("weekCard.create") }}</EbButton>
            </div>
          </form>
        </div>
      </section>

      <section class="week-card__column">
        <div class="week-card__column-label">{{ t("weekCard.completed") }}</div>
        <div class="week-card__rows">
          <CompletedRow v-for="(row, index) in week.completed_rows" :key="`completed-${row.id}-${row.notes}-${index}`" :row="row" />
          <div v-if="week.completed_rows.length === 0" class="week-card__empty">{{ t("weekCard.emptyCompleted") }}</div>
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

.week-card__create {
  display: grid;
  gap: 0.85rem;
  padding: 1rem;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: var(--eb-radius-md);
  background: rgba(56, 189, 248, 0.05);
}

.week-card__create-field {
  display: grid;
  gap: 0.4rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.week-card__create-field input,
.week-card__create-field select {
  width: 100%;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.7rem 0.8rem;
  font: inherit;
  letter-spacing: normal;
  text-transform: none;
}

.week-card__create-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.week-card__create-error {
  margin: 0;
  color: var(--eb-danger);
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
