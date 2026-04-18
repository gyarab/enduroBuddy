import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AthleteView from "@/views/dashboard/AthleteView.vue";
import { useTrainingStore } from "@/stores/training";

const dashboardPayload = {
  selected_month: {
    id: 1,
    value: "2026-04",
    label: "Duben 2026",
    year: 2026,
    month: 4,
  },
  navigation: {
    previous: null,
    next: null,
    available: [],
  },
  summary: {
    planned_sessions: 1,
    completed_sessions: 0,
    planned_km: 8,
    completed_km: 0,
    completed_minutes: 0,
    completion_rate: 0,
  },
  weeks: [
    {
      id: 1,
      week_index: 14,
      week_start: "2026-04-06",
      week_end: "2026-04-12",
      has_started: true,
      planned_total_km_text: "8.0 km/week",
      completed_total: { km: "-", time: "-", avg_hr: null, max_hr: null },
      planned_rows: [],
      completed_rows: [],
    },
  ],
  flags: {
    is_coach: false,
    can_edit_planned: true,
    can_edit_completed: true,
  },
};

function mountAthleteView() {
  return mount(AthleteView, {
    global: {
      stubs: {
        MonthSwitcher: { template: "<div class='month-switcher-stub' />" },
        GarminImportModal: { template: "<div class='garmin-modal-stub' />" },
        MonthSummaryBar: { template: "<div class='summary-bar-stub' />" },
        WeekCard: { template: "<div class='week-card-stub' />" },
        WeekCardSkeleton: { template: "<div class='week-skeleton-stub' />" },
        EbCard: { template: "<div class='eb-card-stub'><slot /></div>" },
      },
    },
  });
}

describe("AthleteView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("loads dashboard on mount when store is empty", async () => {
    const store = useTrainingStore();
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);

    mountAthleteView();

    expect(store.loadDashboard).toHaveBeenCalledOnce();
  });

  it("renders empty state when month has no data", () => {
    const store = useTrainingStore();
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);
    store.dashboard = { ...dashboardPayload, weeks: [] };
    store.errorMessage = "";
    store.isLoading = false;

    const wrapper = mountAthleteView();

    expect(wrapper.text()).toContain("Zatim zadny plan pro tento mesic");
  });

  it("renders error state when dashboard load fails", () => {
    const store = useTrainingStore();
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);
    store.dashboard = null;
    store.errorMessage = "API error";
    store.isLoading = false;

    const wrapper = mountAthleteView();

    expect(wrapper.text()).toContain("Dashboard se nepodarilo nacist");
    expect(wrapper.text()).toContain("API error");
  });
});
