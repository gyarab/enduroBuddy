<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { RouterLink } from "vue-router";

import AthleteManageModal from "@/components/coach/AthleteManageModal.vue";
import CoachSidebar from "@/components/coach/CoachSidebar.vue";
import MonthBar from "@/components/training/MonthBar.vue";
import MonthSummaryBar from "@/components/training/MonthSummaryBar.vue";
import WeekCard from "@/components/training/WeekCard.vue";
import WeekCardSkeleton from "@/components/training/WeekCardSkeleton.vue";
import EbButton from "@/components/ui/EbButton.vue";
import EbCard from "@/components/ui/EbCard.vue";
import { useI18n } from "@/composables/useI18n";
import { useToastStore } from "@/stores/toasts";
import { useCoachStore } from "@/stores/coach";
import { addNextMonth } from "@/api/training";

const coachStore = useCoachStore();
const toastStore = useToastStore();
const focusDraft = ref("");
const isSavingFocus = ref(false);
const isManageOpen = ref(false);
const isSidebarOpen = ref(false);
const isAddingMonth = ref(false);
const { t } = useI18n();

onMounted(() => {
  if (!coachStore.dashboard && !coachStore.isLoading) {
    void coachStore.loadDashboard();
  }
});

watch(
  () => coachStore.selectedAthlete?.focus,
  (value) => {
    focusDraft.value = value || "";
  },
  { immediate: true },
);

async function saveFocus() {
  isSavingFocus.value = true;
  try {
    await coachStore.saveFocus(focusDraft.value);
  } finally {
    isSavingFocus.value = false;
  }
}

async function openManageModal() {
  await coachStore.loadAthletes();
  isManageOpen.value = true;
}

async function saveAthleteOrder(athleteIds: number[]) {
  await coachStore.saveAthleteOrder(athleteIds);
  isManageOpen.value = false;
}

async function toggleAthleteHidden(athleteId: number, hidden: boolean) {
  await coachStore.setAthleteHidden(athleteId, hidden);
}

async function handleAddMonth() {
  if (!coachStore.selectedAthlete) return;
  isAddingMonth.value = true;
  try {
    const data = await addNextMonth(coachStore.selectedAthlete.id);
    await coachStore.loadDashboard(coachStore.selectedAthlete.id, data.month_value);
    toastStore.push(t("addMonth.added"), "success");
  } catch {
    toastStore.push(t("addMonth.error"), "danger");
  } finally {
    isAddingMonth.value = false;
  }
}
</script>

<template>
  <section class="coach-view">
    <aside class="coach-view__sidebar" :class="{ 'coach-view__sidebar--open': isSidebarOpen }">
      <CoachSidebar
        :athletes="coachStore.athletes"
        @select="
          async (athleteId) => {
            isSidebarOpen = false;
            await coachStore.selectAthlete(athleteId);
          }
        "
      />
    </aside>

    <div class="coach-view__content">
      <div v-if="coachStore.isLoading" class="coach-view__loading">
        <WeekCardSkeleton v-for="index in 3" :key="`coach-skeleton-${index}`" />
      </div>

      <EbCard v-else-if="coachStore.errorMessage" class="coach-card">
        <div class="coach-card__eyebrow">{{ t("coachView.workspace") }}</div>
        <h1 class="coach-card__title">{{ t("coachView.loadErrorTitle") }}</h1>
        <p class="coach-card__text">{{ coachStore.errorMessage }}</p>
      </EbCard>

      <template v-else-if="coachStore.selectedAthlete">
        <EbCard class="coach-toolbar">
          <div class="coach-toolbar__identity">
            <div class="coach-card__eyebrow">{{ t("coachView.selectedAthlete") }}</div>
            <div class="coach-toolbar__name">{{ coachStore.selectedAthlete.name }}</div>
            <div class="coach-toolbar__actions">
              <RouterLink to="/app/dashboard" class="coach-toolbar__back-link">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M19 12H5M12 5l-7 7 7 7" />
                </svg>
                {{ t("coachView.backToDashboard") }}
              </RouterLink>
              <EbButton variant="ghost" class="coach-toolbar__mobile-button" @click="isSidebarOpen = !isSidebarOpen">
                {{ isSidebarOpen ? t("coachView.hideAthletes") : t("coachView.showAthletes") }}
              </EbButton>
              <EbButton variant="ghost" @click="openManageModal">{{ t("coachView.manageAthletes") }}</EbButton>
            </div>
          </div>

          <div class="coach-toolbar__focus">
            <label class="coach-toolbar__label" for="coach-focus-input">{{ t("coachView.focus") }}</label>
            <input
              id="coach-focus-input"
              v-model="focusDraft"
              class="coach-toolbar__input"
              type="text"
              maxlength="10"
              :disabled="isSavingFocus"
            />
            <EbButton variant="secondary" :disabled="isSavingFocus" @click="saveFocus">
              {{ isSavingFocus ? t("coachView.saving") : t("coachView.saveFocus") }}
            </EbButton>
          </div>
        </EbCard>

        <MonthSummaryBar v-if="coachStore.summary" :summary="coachStore.summary" />

        <div class="coach-view__weeks">
          <WeekCard v-for="week in coachStore.weeks" :key="week.id" :week="week" editor-context="coach" />
        </div>
      </template>
    </div>
  </section>

  <MonthBar
    v-if="coachStore.selectedAthlete"
    :months="coachStore.navigation?.available ?? []"
    :active-month="coachStore.selectedMonth?.value"
    :adding="isAddingMonth"
    @select="(value) => coachStore.loadDashboard(coachStore.selectedAthlete!.id, value)"
    @add-month="handleAddMonth"
  />

  <AthleteManageModal
    :athletes="coachStore.managedAthletes"
    :open="isManageOpen"
    :saving="coachStore.isManagingAthletes"
    @close="isManageOpen = false"
    @save="saveAthleteOrder"
    @toggle-hidden="toggleAthleteHidden"
  />
</template>

<style scoped>
.coach-view {
  display: grid;
  grid-template-columns: 18rem minmax(0, 1fr);
  gap: 1rem;
}

.coach-view__sidebar {
  position: sticky;
  top: calc(var(--eb-topnav-height) + 1.5rem);
  align-self: start;
}

.coach-view__content,
.coach-view__loading,
.coach-view__weeks {
  display: grid;
  gap: 1rem;
}

.coach-card {
  padding: 1.5rem;
}

.coach-card__eyebrow {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-label-tracking);
  text-transform: uppercase;
}

.coach-card__title {
  margin: 0.75rem 0 0;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h1-size);
  font-weight: var(--eb-type-h1-weight);
  line-height: var(--eb-type-h1-line);
  letter-spacing: var(--eb-type-h1-tracking);
}

.coach-card__text {
  max-width: 38rem;
  margin: 1rem 0 0;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
  line-height: var(--eb-type-body-line);
}

.coach-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: end;
  padding: 1.25rem;
}

.coach-toolbar__identity {
  display: grid;
  gap: 0.5rem;
}

.coach-toolbar__name {
  margin-top: 0.45rem;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h2-size);
  font-weight: var(--eb-type-h2-weight);
  letter-spacing: var(--eb-type-h2-tracking);
}

.coach-toolbar__actions {
  display: flex;
  gap: 0.75rem;
}

.coach-toolbar__back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.75rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: transparent;
  color: var(--eb-text-muted);
  font-size: var(--eb-type-small-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-small-tracking);
  text-decoration: none;
  transition:
    border-color 150ms ease-out,
    color 150ms ease-out;
}

.coach-toolbar__back-link:hover {
  border-color: var(--eb-border);
  color: var(--eb-text-soft);
}

.coach-toolbar__mobile-button {
  display: none;
}

.coach-toolbar__focus {
  display: flex;
  gap: 0.75rem;
  align-items: end;
}

.coach-toolbar__label {
  color: var(--eb-text-muted);
  font-size: var(--eb-type-label-size);
  font-weight: 600;
  letter-spacing: var(--eb-type-label-tracking);
  text-transform: uppercase;
}

.coach-toolbar__input {
  min-width: 12rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.75rem 0.85rem;
}

@media (max-width: 1023px) {
  .coach-view {
    grid-template-columns: 1fr;
  }

  .coach-view__sidebar {
    position: static;
    display: none;
  }

  .coach-view__sidebar--open {
    display: block;
  }

  .coach-toolbar {
    display: grid;
    align-items: start;
  }

  .coach-toolbar__focus {
    display: grid;
  }

  .coach-toolbar__mobile-button {
    display: inline-flex;
  }
}
</style>
