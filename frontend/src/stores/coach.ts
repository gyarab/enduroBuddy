import { computed, ref } from "vue";
import { defineStore } from "pinia";

import {
  addCoachSecondPhaseTraining,
  fetchCoachAthletes,
  fetchCoachDashboard,
  removeCoachSecondPhaseTraining,
  reorderCoachAthletes,
  updateCoachAthleteVisibility,
  updateCoachPlannedTraining,
  updateCoachAthleteFocus,
  type CoachDashboardPayload,
  type CoachAthlete,
} from "@/api/coach";
import { useI18n } from "@/composables/useI18n";
import type { TrainingRow } from "@/api/training";
import { useToastStore } from "@/stores/toasts";
import { parseTrainingPreview } from "@/utils/trainingPreview";

export const useCoachStore = defineStore("coach", () => {
  const dashboard = ref<CoachDashboardPayload | null>(null);
  const managedAthletes = ref<CoachAthlete[]>([]);
  const isLoading = ref(false);
  const isManagingAthletes = ref(false);
  const errorMessage = ref("");
  const toastStore = useToastStore();
  const { t } = useI18n();

  const athletes = computed(() => dashboard.value?.athletes ?? []);
  const selectedAthlete = computed(() => dashboard.value?.selected_athlete ?? null);
  const summary = computed(() => dashboard.value?.summary ?? null);
  const weeks = computed(() => dashboard.value?.weeks ?? []);
  const selectedMonth = computed(() => dashboard.value?.selected_month ?? null);
  const navigation = computed(() => dashboard.value?.navigation ?? null);

  async function loadDashboard(athleteId?: number, month?: string) {
    isLoading.value = true;
    errorMessage.value = "";
    try {
      dashboard.value = await fetchCoachDashboard(athleteId, month);
      applyManagedAthletes(await fetchCoachAthletes(dashboard.value.selected_athlete?.id).then((payload) => payload.athletes));
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : t("coachStore.loadError");
    } finally {
      isLoading.value = false;
    }
  }

  async function selectAthlete(athleteId: number) {
    await loadDashboard(athleteId, selectedMonth.value?.value);
  }

  async function goToPreviousMonth() {
    const previous = navigation.value?.previous?.value;
    if (!previous) {
      return;
    }
    await loadDashboard(selectedAthlete.value?.id, previous);
  }

  async function goToNextMonth() {
    const next = navigation.value?.next?.value;
    if (!next) {
      return;
    }
    await loadDashboard(selectedAthlete.value?.id, next);
  }

  async function saveFocus(focus: string) {
    if (!selectedAthlete.value) {
      return;
    }
    const payload = await updateCoachAthleteFocus(selectedAthlete.value.id, focus);
    if (dashboard.value?.selected_athlete) {
      dashboard.value.selected_athlete.focus = payload.focus;
    }
    const athlete = dashboard.value?.athletes.find((item) => item.id === payload.athlete_id);
    if (athlete) {
      athlete.focus = payload.focus;
    }
    toastStore.push(t("coachStore.focusUpdated"), "success");
  }

  function isSubstantivePlannedRow(row: TrainingRow) {
    return Boolean(
      (row.title && row.title !== "-")
      || row.notes.trim()
      || (row.planned_metrics?.planned_km_value || 0) > 0,
    );
  }

  function formatFixed(value: number, decimals: number, useCommaDecimal: boolean) {
    const formatted = value.toFixed(decimals);
    return useCommaDecimal ? formatted.replace(".", ",") : formatted;
  }

  function formatPlannedWeekLabel(totalKm: number, previousLabel: string) {
    const useCommaDecimal = previousLabel.includes(",");
    const suffix = previousLabel.includes("km/t") ? "km/t\u00fdden" : "km/week";
    return `${formatFixed(totalKm, 1, useCommaDecimal)} ${suffix}`;
  }

  function recomputePlannedWeekTotals() {
    if (!dashboard.value) {
      return;
    }

    for (const week of dashboard.value.weeks) {
      const totalKm = week.planned_rows.reduce((sum, row) => sum + (row.planned_metrics?.planned_km_value || 0), 0);
      week.planned_total_km_text = formatPlannedWeekLabel(totalKm, week.planned_total_km_text);
    }
  }

  function recomputeSummary() {
    if (!dashboard.value) {
      return;
    }

    let plannedSessions = 0;
    let completedSessions = 0;
    let plannedKm = 0;
    let completedKm = 0;
    let completedMinutes = 0;

    for (const week of dashboard.value.weeks) {
      for (const row of week.planned_rows) {
        if (isSubstantivePlannedRow(row)) {
          plannedSessions += 1;
          plannedKm += row.planned_metrics?.planned_km_value || 0;
        }
      }

      for (const row of week.completed_rows) {
        const metrics = row.completed_metrics;
        if (metrics && (metrics.km || metrics.minutes || metrics.details || metrics.avg_hr !== null || metrics.max_hr !== null || row.has_linked_activity)) {
          completedSessions += 1;
        }
      }

      const weekKm = Number.parseFloat((week.completed_total.km || "").replace(",", "."));
      const weekMinutes = Number.parseInt(week.completed_total.time || "", 10);
      if (Number.isFinite(weekKm)) {
        completedKm += weekKm;
      }
      if (Number.isFinite(weekMinutes)) {
        completedMinutes += weekMinutes;
      }
    }

    dashboard.value.summary = {
      planned_sessions: plannedSessions,
      completed_sessions: completedSessions,
      planned_km: Math.round(plannedKm * 10) / 10,
      completed_km: Math.round(completedKm * 10) / 10,
      completed_minutes: completedMinutes,
      completion_rate: plannedSessions > 0 ? Math.round((completedSessions / plannedSessions) * 100) : 0,
    };
  }

  function patchPlannedRow(
    plannedId: number,
    payload: {
      field: "title" | "notes" | "session_type";
      value: string;
    },
  ) {
    if (!dashboard.value) {
      return;
    }

    for (const week of dashboard.value.weeks) {
      const row = week.planned_rows.find((candidate) => candidate.id === plannedId);
      if (!row) {
        continue;
      }

      if (payload.field === "title") {
        row.title = payload.value.trim() || "-";
        const preview = parseTrainingPreview(payload.value);
        row.planned_metrics = {
          planned_km_value: preview.totalKm,
          planned_km_text: preview.kmText,
          planned_km_confidence: preview.confidence,
        };
      }
      if (payload.field === "notes") {
        row.notes = payload.value.trim();
      }
      if (payload.field === "session_type") {
        row.session_type = payload.value === "WORKOUT" ? "WORKOUT" : "RUN";
      }

      row.status = isSubstantivePlannedRow(row) ? "planned" : "rest";
      break;
    }

    recomputePlannedWeekTotals();
    recomputeSummary();
  }

  async function loadAthletes() {
    applyManagedAthletes(await fetchCoachAthletes(selectedAthlete.value?.id).then((payload) => payload.athletes));
  }

  async function saveAthleteOrder(athleteIds: number[]) {
    isManagingAthletes.value = true;
    try {
      const payload = await reorderCoachAthletes(athleteIds);
      applyManagedAthletes(payload.athletes);
      toastStore.push(t("coachStore.athleteOrderUpdated"), "success");
    } finally {
      isManagingAthletes.value = false;
    }
  }

  function applyManagedAthletes(nextAthletes: CoachAthlete[]) {
    managedAthletes.value = nextAthletes;
    if (!dashboard.value) {
      return;
    }

    const visibleAthletes = nextAthletes.filter((athlete) => !athlete.hidden);
    const selectedId = dashboard.value.selected_athlete?.id ?? null;
    dashboard.value.athletes = visibleAthletes.map((athlete) => ({
      ...athlete,
      selected: athlete.id === selectedId,
    }));
  }

  async function setAthleteHidden(athleteId: number, hidden: boolean) {
    isManagingAthletes.value = true;
    try {
      const payload = await updateCoachAthleteVisibility(athleteId, hidden);
      applyManagedAthletes(payload.athletes);
      toastStore.push(hidden ? t("coachStore.athleteHidden") : t("coachStore.athleteShown"), "success");

      if (hidden && selectedAthlete.value?.id === athleteId) {
        const nextVisible = payload.athletes.find((athlete) => !athlete.hidden);
        if (nextVisible) {
          await loadDashboard(nextVisible.id, selectedMonth.value?.value);
        }
      }
    } finally {
      isManagingAthletes.value = false;
    }
  }

  async function savePlannedDraft(
    plannedId: number,
    updates: Array<{
      field: "title" | "notes" | "session_type";
      value: string;
    }>,
  ) {
    for (const update of updates) {
      await updateCoachPlannedTraining(plannedId, update);
      patchPlannedRow(plannedId, update);
    }
    toastStore.push(t("coachStore.planUpdated"), "success");
  }

  async function addSecondPhase(plannedId: number) {
    await addCoachSecondPhaseTraining(plannedId);
    await loadDashboard(selectedAthlete.value?.id, selectedMonth.value?.value);
    toastStore.push(t("coachStore.secondPhaseAdded"), "success");
  }

  async function removeSecondPhase(plannedId: number) {
    await removeCoachSecondPhaseTraining(plannedId);
    await loadDashboard(selectedAthlete.value?.id, selectedMonth.value?.value);
    toastStore.push(t("coachStore.secondPhaseRemoved"), "success");
  }

  return {
    addSecondPhase,
    athletes,
    dashboard,
    errorMessage,
    goToNextMonth,
    goToPreviousMonth,
    isLoading,
    isManagingAthletes,
    loadAthletes,
    loadDashboard,
    managedAthletes,
    navigation,
    removeSecondPhase,
    saveFocus,
    saveAthleteOrder,
    savePlannedDraft,
    setAthleteHidden,
    selectAthlete,
    selectedAthlete,
    selectedMonth,
    summary,
    weeks,
  };
});
