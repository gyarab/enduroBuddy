import { ref } from "vue";
import { defineStore } from "pinia";

import { fetchLegend, saveLegend, type LegendState } from "@/api/legend";

export const useLegendStore = defineStore("legend", () => {
  const state = ref<LegendState | null>(null);
  const isLoading = ref(false);
  const isSaving = ref(false);
  const error = ref("");

  async function load() {
    if (state.value !== null) return;
    isLoading.value = true;
    error.value = "";
    try {
      const data = await fetchLegend();
      state.value = data.state;
    } catch {
      error.value = "Nepodařilo se načíst legendu.";
    } finally {
      isLoading.value = false;
    }
  }

  async function save(nextState: LegendState) {
    isSaving.value = true;
    error.value = "";
    try {
      const data = await saveLegend(nextState);
      state.value = data.state;
    } catch {
      error.value = "Nepodařilo se uložit legendu.";
      throw error.value;
    } finally {
      isSaving.value = false;
    }
  }

  return { state, isLoading, isSaving, error, load, save };
});
