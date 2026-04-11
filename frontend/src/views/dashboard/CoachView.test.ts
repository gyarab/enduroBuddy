import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CoachView from "@/views/dashboard/CoachView.vue";
import { useCoachStore } from "@/stores/coach";

const dashboardPayload = {
  selected_athlete: {
    id: 101,
    name: "Alice Runner",
    focus: "10K",
  },
  athletes: [
    { id: 101, name: "Alice Runner", focus: "10K", hidden: false, sort_order: 1, selected: true },
    { id: 202, name: "Bob Climber", focus: "", hidden: false, sort_order: 2, selected: false },
  ],
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
    is_coach: true,
    can_edit_planned: true,
    can_edit_completed: false,
  },
};

function mountCoachView() {
  return mount(CoachView, {
    global: {
      stubs: {
        RouterLink: { template: "<a><slot /></a>" },
        CoachSidebar: {
          template: "<div class='coach-sidebar-stub' />",
        },
        AthleteManageModal: {
          template: "<div class='athlete-manage-modal-stub' />",
        },
        MonthSummaryBar: { template: "<div class='summary-bar-stub' />" },
        WeekCard: { template: "<div class='week-card-stub' />" },
        WeekCardSkeleton: { template: "<div class='week-skeleton-stub' />" },
        EbButton: {
          template: "<button><slot /></button>",
        },
        EbCard: { template: "<div class='eb-card-stub'><slot /></div>" },
      },
    },
  });
}

describe("CoachView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("loads coach dashboard on mount when store is empty", () => {
    const store = useCoachStore();
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);

    mountCoachView();

    expect(store.loadDashboard).toHaveBeenCalledOnce();
  });

  it("saves focus from toolbar input", async () => {
    const store = useCoachStore();
    store.dashboard = { ...dashboardPayload };
    store.saveFocus = vi.fn().mockResolvedValue(undefined);
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);

    const wrapper = mountCoachView();
    const input = wrapper.get("#coach-focus-input");
    await input.setValue("Trail");

    const saveButton = wrapper.findAll("button").find((candidate) => candidate.text().includes("Save focus"));
    expect(saveButton).toBeTruthy();
    await saveButton!.trigger("click");

    expect(store.saveFocus).toHaveBeenCalledWith("Trail");
  });

  it("opens manage flow by loading athletes before modal use", async () => {
    const store = useCoachStore();
    store.dashboard = { ...dashboardPayload };
    store.loadAthletes = vi.fn().mockResolvedValue(undefined);
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);

    const wrapper = mountCoachView();
    const manageButton = wrapper.findAll("button").find((candidate) => candidate.text().includes("Manage athletes"));
    expect(manageButton).toBeTruthy();
    await manageButton!.trigger("click");

    expect(store.loadAthletes).toHaveBeenCalledOnce();
  });
});
