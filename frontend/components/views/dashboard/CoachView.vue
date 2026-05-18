<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from "vue";

import { useRouter } from "vue-router";

import CoachSidebar from "@/components/coach/CoachSidebar.vue";
import LegendPanel from "@/components/layout/LegendPanel.vue";
import ManagePanel from "@/components/coach/ManagePanel.vue";
import MonthBar from "@/components/training/MonthBar.vue";
import MonthSummaryBar from "@/components/training/MonthSummaryBar.vue";
import WeekCard from "@/components/training/WeekCard.vue";
import WeekCardSkeleton from "@/components/training/WeekCardSkeleton.vue";
import EbCard from "@/components/ui/EbCard.vue";
import { useToastStore } from "@/stores/toasts";
import { useCoachStore } from "@/stores/coach";
import { addNextMonth } from "~/utils/api/training";
import { useGridNav } from "~/composables/useGridNav";

const router = useRouter();
const coachStore = useCoachStore();
const toastStore = useToastStore();
const focusDraft = ref("");
const isManageOpen = ref(false);
const isLegendOpen = ref(false);
const isAddingMonth = ref(false);

const weekCardRefs: InstanceType<typeof WeekCard>[] = []

// ── Grid navigation ──────────────────────────────────────────
const gridNav = useGridNav()
const { cursor, editMode } = gridNav

function cursorForWeek(idx: number): { dayIdx: number; fieldIdx: number } | null {
  if (!cursor.value || cursor.value.weekIdx !== idx) return null
  return { dayIdx: cursor.value.dayIdx, fieldIdx: cursor.value.fieldIdx }
}

const PRINTABLE = /^[a-zA-Z0-9\-.,;:!?@#%&*()/\\'"= ]$/

function openCellByIdx(weekIdx: number, dayIdx: number, fieldIdx: number, replaceContent?: string) {
  gridNav.enterEdit(replaceContent)
  weekCardRefs[weekIdx]?.focusCellByIdx(dayIdx, fieldIdx, replaceContent)
}

function handleKeyDown(e: KeyboardEvent) {
  const active = document.activeElement
  const inInput = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement
  if (editMode.value && !inInput) gridNav.exitEdit()
  if (editMode.value) return
  const weekCount = coachStore.weeks.length
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    const dir = e.key.replace('Arrow', '').toLowerCase() as 'up' | 'down' | 'left' | 'right'
    gridNav.moveCursor(dir, weekCount)
    return
  }
  if (e.key === 'Tab') {
    e.preventDefault()
    gridNav.moveCursor(e.shiftKey ? 'left' : 'right', weekCount)
    return
  }
  if (!cursor.value) return
  const { weekIdx, dayIdx, fieldIdx } = cursor.value
  if (e.key === 'Enter' || (e.key === ' ' && fieldIdx === 0)) {
    e.preventDefault()
    if (fieldIdx === 0) {
      weekCardRefs[weekIdx]?.toggleTypeByDayIdx(dayIdx)
    } else {
      openCellByIdx(weekIdx, dayIdx, fieldIdx)
    }
    return
  }
  if ((e.key === 'Backspace' || e.key === 'Delete') && fieldIdx !== 0) {
    e.preventDefault()
    openCellByIdx(weekIdx, dayIdx, fieldIdx, '')
    return
  }
  if (e.key === 'Escape') {
    e.preventDefault()
    gridNav.clearCursor()
    return
  }
  if (PRINTABLE.test(e.key) && !e.ctrlKey && !e.metaKey && fieldIdx !== 0) {
    e.preventDefault()
    openCellByIdx(weekIdx, dayIdx, fieldIdx, e.key)
  }
}

function handleExitEdit() {
  gridNav.exitEdit()
}

function handleExitEditMove(dir: 'up' | 'down') {
  gridNav.exitEdit()
  gridNav.moveCursor(dir, coachStore.weeks.length)
}

function handleCursorSet(
  weekIdx: number,
  payload: { dayIdx: number; fieldIdx: number }
) {
  cursor.value = { weekIdx, dayIdx: payload.dayIdx, fieldIdx: payload.fieldIdx }
}

watch(cursor, (newCursor) => {
  if (!newCursor || editMode.value) return
  void nextTick(() => {
    const el = document.querySelector<HTMLElement>('.wt__cell--nav-selected-p, .wt__cell--nav-selected-c')
    el?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' })
  })
})

function handleNavOut(
  dir: "next" | "prev",
  idx: number,
  payload: { field: string; zone: "planned" | "completed" },
) {
  const targetIdx = dir === "next" ? idx + 1 : idx - 1
  const card = weekCardRefs[targetIdx]
  if (card) card.focusCell(payload.field, payload.zone, dir === "prev")
}

const { t } = useI18n();

function handleOutsideClick(e: MouseEvent) {
  if (!(e.target as HTMLElement).closest('.week-card')) {
    gridNav.clearCursor()
  }
}

onMounted(() => {
  if (!coachStore.dashboard && !coachStore.isLoading) {
    void coachStore.loadDashboard().then(() => {
      gridNav.initCursor(coachStore.weeks)
    })
  } else if (coachStore.weeks.length) {
    gridNav.initCursor(coachStore.weeks)
  }
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('mousedown', handleOutsideClick)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('mousedown', handleOutsideClick)
})

watch(
  () => coachStore.selectedAthlete?.focus,
  (value) => {
    focusDraft.value = value || "";
  },
  { immediate: true },
);

// Re-init cursor only on month or athlete change, not on silent reloads after saves
watch(
  () => [coachStore.selectedMonth?.value, coachStore.selectedAthlete?.id] as const,
  () => {
    weekCardRefs.length = 0
    if (coachStore.weeks.length) gridNav.initCursor(coachStore.weeks)
  },
)

async function saveFocus() {
  await coachStore.saveFocus(focusDraft.value);
}

function openManage() {
  void coachStore.loadAthletes();
  isLegendOpen.value = false;
  isManageOpen.value = true;
}

function openLegend() {
  isManageOpen.value = false;
  isLegendOpen.value = true;
}

async function handleSidebarReorder(athleteIds: number[]) {
  const hidden = coachStore.managedAthletes.filter((a) => a.hidden);
  const allIds = [...athleteIds, ...hidden.map((a) => a.id)];
  await coachStore.saveAthleteOrder(allIds);
}

async function handleToggleHidden(athleteId: number, hidden: boolean) {
  await coachStore.setAthleteHidden(athleteId, hidden);
}

async function handleSidebarRemove(_athleteId: number) {
  openManage();
}

async function handleSidebarSelect(athleteId: number) {
  await coachStore.selectAthlete(athleteId);
}

function handleMonthSelect(monthValue: string) {
  const athlete = coachStore.selectedAthlete;
  if (athlete) void coachStore.loadDashboard(athlete.id, monthValue);
}

function handleGoToDashboard() {
  void router.push("/dashboard");
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
    <!-- Sidebar (200px) -->
    <aside class="coach-view__sidebar">
      <CoachSidebar
        :athletes="coachStore.athletes"
        :is-manage-open="isManageOpen"
        @select="handleSidebarSelect"
        @open-manage="openManage"
        @reorder="handleSidebarReorder"
        @toggle-hidden="handleToggleHidden"
        @remove="handleSidebarRemove"
        @go-to-dashboard="handleGoToDashboard"
      />
    </aside>

    <!-- Main content area -->
    <div class="coach-view__main">
      <!-- Toolbar -->
      <div class="coach-toolbar">
        <template v-if="coachStore.selectedAthlete">
          <span class="coach-toolbar__name">{{ coachStore.selectedAthlete.name }}</span>
          <div class="coach-toolbar__divider" aria-hidden="true" />
          <div class="coach-toolbar__focus-pill">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            <div class="coach-toolbar__focus-sizer">
              <span class="coach-toolbar__focus-mirror" aria-hidden="true">{{ focusDraft || t('coachView.focus') }}</span>
              <input
                v-model="focusDraft"
                class="coach-toolbar__focus-input"
                maxlength="10"
                :placeholder="t('coachView.focus')"
                @blur="saveFocus"
              />
            </div>
          </div>
        </template>
        <template v-else>
          <span class="coach-toolbar__workspace">{{ t("coachView.workspace") }}</span>
        </template>

        <div class="coach-toolbar__spacer" />

        <button
          v-if="coachStore.selectedAthlete"
          class="coach-toolbar__legend-btn"
          :class="{ 'coach-toolbar__legend-btn--active': isLegendOpen }"
          type="button"
          @click="openLegend"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
          </svg>
          {{ t("coachToolbar.legendBtn") }}
        </button>
      </div>

      <!-- Content -->
      <div v-if="coachStore.isLoading" class="coach-view__loading">
        <WeekCardSkeleton v-for="index in 3" :key="`coach-skeleton-${index}`" />
      </div>

      <EbCard v-else-if="coachStore.errorMessage" class="coach-card">
        <h1 class="coach-card__title">{{ t("coachView.loadErrorTitle") }}</h1>
        <p class="coach-card__text">{{ coachStore.errorMessage }}</p>
      </EbCard>

      <EbCard v-else-if="!coachStore.selectedAthlete" class="coach-card coach-card--empty">
        <h1 class="coach-card__title">{{ t("coachView.noAthletesTitle") }}</h1>
        <p class="coach-card__text">{{ t("coachView.noAthletesText") }}</p>
      </EbCard>

      <template v-else>
        <MonthSummaryBar v-if="coachStore.summary" :summary="coachStore.summary" />
        <div class="coach-view__weeks">
          <WeekCard
            v-for="(week, idx) in coachStore.weeks"
            :key="week.id"
            :ref="(el) => { if (el) weekCardRefs[idx] = el as InstanceType<typeof WeekCard> }"
            :week="week"
            editor-context="coach"
            :active-cursor="cursorForWeek(idx)"
            @navigate-out-next="(p) => handleNavOut('next', idx, p)"
            @navigate-out-prev="(p) => handleNavOut('prev', idx, p)"
            @exit-edit="handleExitEdit"
            @exit-edit-move="(dir) => handleExitEditMove(dir)"
            @cursor-set="(p) => handleCursorSet(idx, p)"
          />
        </div>
      </template>
    </div>
  </section>

  <MonthBar
    v-if="coachStore.selectedAthlete"
    :months="coachStore.navigation?.available ?? []"
    :active-month="coachStore.selectedMonth?.value"
    :adding="isAddingMonth"
    @select="handleMonthSelect"
    @add-month="handleAddMonth"
  />

  <!-- Panels -->
  <ManagePanel
    :open="isManageOpen"
    :athletes="coachStore.managedAthletes"
    @close="isManageOpen = false"
    @toggle-hidden="handleToggleHidden"
    @athlete-removed="(id) => void coachStore.loadAthletes()"
    @go-to-dashboard="handleGoToDashboard"
  />

  <LegendPanel
    v-if="coachStore.selectedAthlete"
    :open="isLegendOpen"
    :title="t('legend.panelAthleteTitle', { name: coachStore.selectedAthlete.name })"
    :subtitle="t('legend.panelAthleteSubtitle')"
    :athlete-id="coachStore.selectedAthlete.id"
    :editable="true"
    @close="isLegendOpen = false"
  />
</template>

<style scoped>
.coach-view {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 0;
  min-height: calc(100vh - 52px);
  background: var(--eb-surface);
  align-items: start;
}

.coach-view__sidebar {
  position: sticky;
  top: 52px;
  height: calc(100vh - 52px);
  overflow-y: auto;
  border-right: 1px solid var(--eb-border);
}

.coach-view__main {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 0;
  align-content: start;
}

/* Toolbar */
.coach-toolbar {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0 1rem;
  height: 48px;
  border-bottom: 1px solid #1e1e22;
  background: #111113;
  flex-shrink: 0;
}

.coach-toolbar__name {
  font-family: var(--eb-font-display, 'Outfit', sans-serif);
  font-size: 15px;
  font-weight: 700;
  color: var(--eb-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 14rem;
}

.coach-toolbar__divider {
  width: 1px;
  height: 18px;
  background: #2e2e34;
  flex-shrink: 0;
}

.coach-toolbar__focus-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.2rem 0.65rem;
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.08);
  color: var(--eb-blue, #38bdf8);
}

.coach-toolbar__focus-sizer {
  display: inline-grid;
}

.coach-toolbar__focus-sizer > * {
  grid-area: 1 / 1;
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.coach-toolbar__focus-mirror {
  visibility: hidden;
  white-space: pre;
  padding: 0;
  border: 0;
  min-width: 2ch;
}

.coach-toolbar__focus-input {
  width: 100%;
  min-width: 0;
  border: 0;
  background: transparent;
  color: var(--eb-blue, #38bdf8);
  outline: none;
}

.coach-toolbar__focus-input::placeholder {
  color: rgba(56, 189, 248, 0.4);
}

.coach-toolbar__workspace {
  font-family: var(--eb-font-display, 'Outfit', sans-serif);
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--eb-text);
}

.coach-toolbar__spacer {
  flex: 1;
}

.coach-toolbar__legend-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0 0.75rem;
  height: 30px;
  border: 1px solid var(--eb-border);
  border-radius: 6px;
  background: transparent;
  color: var(--eb-text-muted);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 150ms, color 150ms;
}

.coach-toolbar__legend-btn:hover,
.coach-toolbar__legend-btn--active {
  border-color: rgba(200, 255, 0, 0.3);
  color: var(--eb-lime, #c8ff00);
}

/* Content */
.coach-view__loading,
.coach-view__weeks {
  display: grid;
  gap: 1rem;
  padding: 1rem;
}

/* Cards */
.coach-card {
  padding: 1.5rem;
}

.coach-card__title {
  margin: 0;
  font-family: var(--eb-font-display, 'Outfit', sans-serif);
  font-size: 1.25rem;
  font-weight: 700;
}

.coach-card__text {
  margin: 0.75rem 0 0;
  color: var(--eb-text-muted);
  font-size: 0.875rem;
}

.coach-card--empty {
  padding: 2.5rem 1.5rem;
  text-align: center;
}

@media (max-width: 767px) {
  .coach-view {
    grid-template-columns: 1fr;
  }

  .coach-view__sidebar {
    display: none;
  }
}
</style>
