import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { fetchCoachDashboard, updateCoachAthleteFocus, type CoachDashboardPayload } from "@/api/coach";
import { useToastStore } from "@/stores/toasts";

export const useCoachStore = defineStore("coach", () => {
  const dashboard = ref<CoachDashboardPayload | null>(null);
  const isLoading = ref(false);
  const errorMessage = ref("");
  const toastStore = useToastStore();

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
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "Nepodarilo se nacist coach dashboard.";
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
    toastStore.push("Coach focus updated.", "success");
  }

  return {
    athletes,
    dashboard,
    errorMessage,
    goToNextMonth,
    goToPreviousMonth,
    isLoading,
    loadDashboard,
    navigation,
    saveFocus,
    selectAthlete,
    selectedAthlete,
    selectedMonth,
    summary,
    weeks,
  };
});
