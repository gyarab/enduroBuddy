<script setup lang="ts">
import { onMounted, ref, watch } from "vue";

import { RouterLink, useRouter } from "vue-router";

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

const router = useRouter();
const coachStore = useCoachStore();
const toastStore = useToastStore();
const focusDraft = ref("");
const isSavingFocus = ref(false);
const isManageOpen = ref(false);
const isSidebarOpen = ref(false);
const isAddingMonth = ref(false);
const startRemoveId = ref<number | null>(null);
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

async function handleSidebarReorder(athleteIds: number[]) {
  const hidden = coachStore.managedAthletes.filter((a) => a.hidden);
  const allIds = [...athleteIds, ...hidden.map((a) => a.id)];
  await coachStore.saveAthleteOrder(allIds);
}

async function handleModalAutoSave(athleteIds: number[]) {
  await coachStore.saveAthleteOrder(athleteIds);
}

async function handleToggleHidden(athleteId: number, hidden: boolean) {
  await coachStore.setAthleteHidden(athleteId, hidden);
}

function handleSidebarRemove(athleteId: number) {
  void openManageModal().then(() => {
    startRemoveId.value = athleteId;
  });
}

function handleAthleteRemoved(athleteId: number) {
  coachStore.managedAthletes.splice(
    coachStore.managedAthletes.findIndex((a) => a.id === athleteId),
    1,
  );
}

function handleGoToDashboard() {
  void router.push("/app/dashboard");
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
        @reorder="handleSidebarReorder"
        @toggle-hidden="handleToggleHidden"
        @remove="handleSidebarRemove"
        @go-to-dashboard="handleGoToDashboard"
      />
    </aside>

    <div class="coach-view__content">
      <!-- Always-visible toolbar -->
      <EbCard class="coach-toolbar">
        <!-- Mobile toggle -->
        <EbButton variant="ghost" class="coach-toolbar__mobile-button" @click="isSidebarOpen = !isSidebarOpen">
          {{ isSidebarOpen ? t("coachView.hideAthletes") : t("coachView.showAthletes") }}
        </EbButton>

        <template v-if="coachStore.selectedAthlete">
          <!-- Athlete name -->
          <span class="coach-toolbar__name" :title="coachStore.selectedAthlete.name">
            {{ coachStore.selectedAthlete.name }}
          </span>

          <!-- Focus pill (read-only indicator) -->
          <span v-if="coachStore.selectedAthlete.focus" class="coach-toolbar__focus-pill">
            ● {{ coachStore.selectedAthlete.focus }}
          </span>

          <!-- Focus form -->
          <div class="coach-toolbar__focus-form">
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

          <!-- Actions -->
          <div class="coach-toolbar__actions">
            <EbButton variant="ghost" @click="openManageModal">{{ t("coachView.manageAthletes") }}</EbButton>
            <RouterLink to="/app/dashboard" class="coach-toolbar__back-link">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M19 12H5M12 5l-7 7 7 7" />
              </svg>
              {{ t("coachView.backToDashboard") }}
            </RouterLink>
          </div>
        </template>

        <template v-else>
          <!-- Empty state toolbar: title + manage button -->
          <span class="coach-toolbar__workspace-title">{{ t("coachView.workspace") }}</span>
          <div class="coach-toolbar__actions" style="margin-left: auto;">
            <EbButton variant="ghost" @click="openManageModal">{{ t("coachView.manageAthletes") }}</EbButton>
          </div>
        </template>
      </EbCard>

      <!-- Loading state -->
      <div v-if="coachStore.isLoading" class="coach-view__loading">
        <WeekCardSkeleton v-for="index in 3" :key="`coach-skeleton-${index}`" />
      </div>

      <!-- Error state -->
      <EbCard v-else-if="coachStore.errorMessage" class="coach-card">
        <div class="coach-card__eyebrow">{{ t("coachView.workspace") }}</div>
        <h1 class="coach-card__title">{{ t("coachView.loadErrorTitle") }}</h1>
        <p class="coach-card__text">{{ coachStore.errorMessage }}</p>
      </EbCard>

      <!-- Empty state: no athlete selected -->
      <EbCard v-else-if="!coachStore.selectedAthlete" class="coach-card coach-card--empty">
        <div class="coach-card__eyebrow">{{ t("coachView.workspace") }}</div>
        <h1 class="coach-card__title">{{ t("coachView.noAthletesTitle") }}</h1>
        <p class="coach-card__text">{{ t("coachView.noAthletesText") }}</p>
        <EbButton variant="primary" class="coach-card__action" @click="openManageModal">
          {{ t("coachView.manageAthletes") }}
        </EbButton>
      </EbCard>

      <!-- Athlete content -->
      <template v-else>
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
    :start-remove-id="startRemoveId"
    @close="isManageOpen = false; startRemoveId = null"
    @auto-save="handleModalAutoSave"
    @toggle-hidden="handleToggleHidden"
    @athlete-removed="handleAthleteRemoved"
    @go-to-dashboard="handleGoToDashboard"
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

/* ── Toolbar ─────────────────────────────────────────── */
.coach-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.625rem;
  padding: 0.75rem 1.125rem;
  min-height: 3.25rem;
}

.coach-toolbar__workspace-title {
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h2-size);
  font-weight: var(--eb-type-h2-weight);
}

.coach-toolbar__name {
  flex: 1;
  min-width: 0;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-h2-size);
  font-weight: var(--eb-type-h2-weight);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 14rem;
}

.coach-toolbar__focus-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.6rem;
  background: rgba(56, 189, 248, 0.1);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 999px;
  color: var(--eb-blue);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  flex-shrink: 0;
}

.coach-toolbar__focus-form {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.coach-toolbar__input {
  min-width: 8rem;
  width: 8rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.5rem 0.75rem;
  font-size: var(--eb-type-small-size);
}

.coach-toolbar__input:focus {
  outline: none;
  border-color: var(--eb-lime);
}

.coach-toolbar__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
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
  text-decoration: none;
  transition:
    border-color 150ms ease-out,
    color 150ms ease-out;
}

.coach-toolbar__back-link:hover {
  color: var(--eb-text-soft);
}

.coach-toolbar__mobile-button {
  display: none;
}

/* ── Cards ───────────────────────────────────────────── */
.coach-card {
  padding: 1.5rem;
}

.coach-card--empty {
  text-align: center;
  padding: 3rem 2rem;
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

.coach-card__action {
  margin-top: 1.5rem;
}

/* ── Mobile ──────────────────────────────────────────── */
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

  .coach-toolbar__mobile-button {
    display: inline-flex;
  }

  .coach-toolbar__focus-form {
    margin-left: 0;
    width: 100%;
  }

  .coach-toolbar__actions {
    width: 100%;
    justify-content: flex-start;
  }

  .coach-toolbar__input {
    flex: 1;
    width: auto;
  }
}
</style>
