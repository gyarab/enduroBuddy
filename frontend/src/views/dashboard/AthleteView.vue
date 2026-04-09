<script setup lang="ts">
import { onMounted } from "vue";

import MonthSummaryBar from "@/components/training/MonthSummaryBar.vue";
import GarminImportModal from "@/components/training/GarminImportModal.vue";
import WeekCard from "@/components/training/WeekCard.vue";
import WeekCardSkeleton from "@/components/training/WeekCardSkeleton.vue";
import EbCard from "@/components/ui/EbCard.vue";
import { useI18n } from "@/composables/useI18n";
import { useTrainingStore } from "@/stores/training";

const trainingStore = useTrainingStore();
const { t } = useI18n();

onMounted(() => {
  if (!trainingStore.dashboard && !trainingStore.isLoading) {
    void trainingStore.loadDashboard();
  }
});
</script>

<template>
  <section class="dashboard-view">
    <div class="dashboard-view__toolbar">
      <GarminImportModal />
    </div>

    <div v-if="trainingStore.isLoading" class="dashboard-view__loading">
      <div class="dashboard-view__summary-skeleton">
        <div v-for="index in 4" :key="`summary-${index}`" class="dashboard-view__summary-block" />
      </div>
      <WeekCardSkeleton v-for="index in 3" :key="`skeleton-${index}`" />
    </div>

    <EbCard v-else-if="trainingStore.errorMessage" class="dashboard-view__state-card">
      <h2>{{ t("athleteView.loadErrorTitle") }}</h2>
      <p>{{ trainingStore.errorMessage }}</p>
    </EbCard>

    <EbCard v-else-if="!trainingStore.hasData" class="dashboard-view__state-card">
      <div class="dashboard-view__empty-mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <h2>{{ t("athleteView.emptyTitle") }}</h2>
      <p>{{ t("athleteView.emptyText") }}</p>
    </EbCard>

    <template v-else>
      <MonthSummaryBar v-if="trainingStore.summary" :summary="trainingStore.summary" />

      <div class="dashboard-view__weeks">
        <WeekCard v-for="week in trainingStore.weeks" :key="week.id" :week="week" />
      </div>
    </template>
  </section>
</template>

<style scoped>
.dashboard-view {
  display: grid;
  gap: 1rem;
}

.dashboard-view__weeks {
  display: grid;
  gap: 1rem;
}

.dashboard-view__toolbar {
  display: flex;
  justify-content: flex-end;
}

.dashboard-view__loading {
  display: grid;
  gap: 1rem;
}

.dashboard-view__summary-skeleton {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.dashboard-view__summary-block {
  height: 6.5rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-lg);
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 25%, rgba(255, 255, 255, 0.08) 50%, rgba(255, 255, 255, 0.03) 75%),
    var(--eb-surface);
  background-size: 200% 100%;
  animation: dashboard-shimmer 1.5s linear infinite;
}

.dashboard-view__state-card {
  padding: 2rem;
  text-align: center;
}

.dashboard-view__state-card h2 {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: 1.5rem;
}

.dashboard-view__state-card p {
  margin: 0.75rem 0 0;
  color: var(--eb-text-soft);
  line-height: 1.6;
}

.dashboard-view__empty-mark {
  display: inline-flex;
  justify-content: center;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.dashboard-view__empty-mark span {
  display: block;
  width: 0.55rem;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(200, 255, 0, 0.75), rgba(56, 189, 248, 0.18));
}

.dashboard-view__empty-mark span:nth-child(1) {
  height: 1.5rem;
  opacity: 0.45;
}

.dashboard-view__empty-mark span:nth-child(2) {
  height: 2.3rem;
}

.dashboard-view__empty-mark span:nth-child(3) {
  height: 1.1rem;
  opacity: 0.6;
}

@keyframes dashboard-shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

@media (max-width: 1023px) {
  .dashboard-view__summary-skeleton {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .dashboard-view__summary-skeleton {
    grid-template-columns: 1fr;
  }
}
</style>
