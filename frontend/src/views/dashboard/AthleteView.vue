<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import MonthBar from "@/components/training/MonthBar.vue";
import MonthSummaryBar from "@/components/training/MonthSummaryBar.vue";
import GarminImportModal from "@/components/training/GarminImportModal.vue";
import WeekCard from "@/components/training/WeekCard.vue";
import WeekCardSkeleton from "@/components/training/WeekCardSkeleton.vue";
import EbButton from "@/components/ui/EbButton.vue";
import EbCard from "@/components/ui/EbCard.vue";
import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";
import { useToastStore } from "@/stores/toasts";
import { useTrainingStore } from "@/stores/training";
import { addNextMonth } from "@/api/training";
import { requestCoachByCode } from "@/api/coach";

const authStore = useAuthStore();
const trainingStore = useTrainingStore();
const toastStore = useToastStore();
const { t } = useI18n();
const isAddingMonth = ref(false);
const coachCodeInput = ref("");
const isRequestingCoach = ref(false);

async function handleRequestCoach() {
  if (!coachCodeInput.value.trim()) return;
  isRequestingCoach.value = true;
  try {
    const data = await requestCoachByCode(coachCodeInput.value.trim());
    toastStore.push(t("requestCoach.success", { name: data.coach_name }), "success");
    coachCodeInput.value = "";
  } catch {
    toastStore.push(t("requestCoach.error"), "danger");
  } finally {
    isRequestingCoach.value = false;
  }
}

async function handleAddMonth() {
  isAddingMonth.value = true;
  try {
    const data = await addNextMonth();
    await trainingStore.loadDashboard(data.month_value);
    toastStore.push(t("addMonth.added"), "success");
  } catch {
    toastStore.push(t("addMonth.error"), "danger");
  } finally {
    isAddingMonth.value = false;
  }
}

onMounted(() => {
  if (!trainingStore.dashboard && !trainingStore.isLoading) {
    void trainingStore.loadDashboard();
  }
});
</script>

<template>
  <section class="dashboard-view">
    <div class="dashboard-view__toolbar">
      <RouterLink v-if="authStore.user?.capabilities.can_view_coach" to="/coach/plans" class="dashboard-view__coach-link">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
        {{ t("topNav.coachWorkspace") }}
      </RouterLink>

      <div class="dashboard-view__toolbar-right">
        <GarminImportModal />
        <form class="dashboard-view__request-coach" @submit.prevent="handleRequestCoach">
          <div class="dashboard-view__request-eyebrow">{{ t("requestCoach.title") }}</div>
          <div class="dashboard-view__request-row">
            <input
              v-model="coachCodeInput"
              class="dashboard-view__request-input"
              :placeholder="t('requestCoach.codePlaceholder')"
              :disabled="isRequestingCoach"
            />
            <EbButton type="submit" variant="secondary" :disabled="isRequestingCoach || !coachCodeInput.trim()">
              {{ isRequestingCoach ? t("requestCoach.submitting") : t("requestCoach.submit") }}
            </EbButton>
          </div>
        </form>
      </div>
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

    <MonthBar
      :months="trainingStore.navigation?.available ?? []"
      :active-month="trainingStore.selectedMonthValue"
      :adding="isAddingMonth"
      @select="(value) => trainingStore.loadDashboard(value)"
      @add-month="handleAddMonth"
    />
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
  align-items: flex-end;
  justify-content: space-between;
  gap: 1rem;
}

.dashboard-view__coach-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.5rem 0.9rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-surface);
  color: var(--eb-text-soft);
  font-family: var(--eb-font-display);
  font-size: 0.8125rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  transition:
    border-color 150ms ease-out,
    color 150ms ease-out,
    background-color 150ms ease-out;
}

.dashboard-view__coach-link:hover {
  border-color: rgba(200, 255, 0, 0.25);
  color: var(--eb-lime);
  background: rgba(200, 255, 0, 0.04);
}

.dashboard-view__toolbar-right {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
}

.dashboard-view__request-coach {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.dashboard-view__request-eyebrow {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.dashboard-view__request-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.dashboard-view__request-input {
  min-width: 9rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.875rem;
  letter-spacing: 0.04em;
  padding: 0.65rem 0.85rem;
}

.dashboard-view__request-input::placeholder {
  color: var(--eb-text-muted);
  font-family: var(--eb-font-body);
  font-size: 0.8125rem;
  letter-spacing: 0;
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

@media (max-width: 639px) {
  .dashboard-view__toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .dashboard-view__toolbar-right {
    flex-direction: column;
    align-items: stretch;
  }

  .dashboard-view__request-input {
    min-width: 0;
    flex: 1;
  }
}
</style>
