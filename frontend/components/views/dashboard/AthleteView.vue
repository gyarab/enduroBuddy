<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";

import MonthBar from "@/components/training/MonthBar.vue";
import MonthSummaryBar from "@/components/training/MonthSummaryBar.vue";
import WeekCard from "@/components/training/WeekCard.vue";
import WeekCardSkeleton from "@/components/training/WeekCardSkeleton.vue";
import GarminImportModal from "@/components/training/GarminImportModal.vue";
import EbButton from "@/components/ui/EbButton.vue";
import EbCard from "@/components/ui/EbCard.vue";
import { useAuthStore } from "@/stores/auth";
import { useToastStore } from "@/stores/toasts";
import { useTrainingStore } from "@/stores/training";
import { useGridNav } from "~/composables/useGridNav";
import { addNextMonth } from "~/utils/api/training";

const trainingStore = useTrainingStore();
const toastStore = useToastStore();
const { t } = useI18n();
const isAddingMonth = ref(false);
const authStore = useAuthStore();
const isGarminModalOpen = ref(false);

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

  const weekCount = trainingStore.weeks.length

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

// ── Lifecycle ────────────────────────────────────────────────
function handleOutsideClick(e: MouseEvent) {
  if (!(e.target as HTMLElement).closest('.week-card')) {
    gridNav.clearCursor()
  }
}

onMounted(() => {
  void trainingStore.loadDashboard().then(() => {
    gridNav.initCursor(trainingStore.weeks)
  })
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('mousedown', handleOutsideClick)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('mousedown', handleOutsideClick)
})

// Re-init cursor only when the user navigates to a different month (not on silent reloads after saves)
watch(() => trainingStore.selectedMonthValue, () => {
  weekCardRefs.length = 0
  if (trainingStore.weeks.length) gridNav.initCursor(trainingStore.weeks)
})

// ── Cross-week navigation (legacy compatible) ──────────────
function handleNavOut(
  dir: "next" | "prev",
  idx: number,
  payload: { field: string; zone: "planned" | "completed" },
) {
  const targetIdx = dir === "next" ? idx + 1 : idx - 1
  const card = weekCardRefs[targetIdx]
  if (card) card.focusCell(payload.field, payload.zone, dir === "prev")
}

// ── Exit edit (WeekCard emits when ESC/Enter/Tab in input) ──
function handleExitEdit() {
  gridNav.exitEdit()
}

function handleExitEditMove(dir: 'up' | 'down') {
  gridNav.exitEdit()
  gridNav.moveCursor(dir, trainingStore.weeks.length)
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

// ── Other ───────────────────────────────────────────────────
const showGarminImportButton = computed(
  () => !!authStore.user?.capabilities?.garmin_connect_enabled,
);

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
</script>

<template>
  <section class="dashboard-view">
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
      <div v-if="showGarminImportButton" class="dashboard-view__toolbar">
        <EbButton variant="ghost" @click="isGarminModalOpen = true">
          {{ t("imports.open") }}
        </EbButton>
      </div>

      <MonthSummaryBar v-if="trainingStore.summary" :summary="trainingStore.summary" />

      <div class="dashboard-view__weeks">
        <WeekCard
          v-for="(week, idx) in trainingStore.weeks"
          :key="week.id"
          :ref="(el) => { if (el) weekCardRefs[idx] = el as InstanceType<typeof WeekCard> }"
          :week="week"
          :active-cursor="cursorForWeek(idx)"
          @navigate-out-next="(p) => handleNavOut('next', idx, p)"
          @navigate-out-prev="(p) => handleNavOut('prev', idx, p)"
          @exit-edit="handleExitEdit"
          @exit-edit-move="(dir) => handleExitEditMove(dir)"
          @cursor-set="(p) => handleCursorSet(idx, p)"
        />
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

  <GarminImportModal
    v-if="showGarminImportButton"
    :open="isGarminModalOpen"
    @close="isGarminModalOpen = false"
  />
</template>

<style scoped>
.dashboard-view {
  display: grid;
  gap: 1rem;
}

.dashboard-view__toolbar {
  display: flex;
  justify-content: flex-end;
}

.dashboard-view__weeks {
  display: grid;
  gap: 1rem;
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
  font-size: var(--eb-type-h2-size);
  font-weight: var(--eb-type-h2-weight);
  letter-spacing: var(--eb-type-h2-tracking);
}

.dashboard-view__state-card p {
  margin: 0.75rem 0 0;
  color: var(--eb-text-soft);
  font-size: var(--eb-type-body-size);
  line-height: var(--eb-type-body-line);
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
