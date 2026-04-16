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
        MonthSummaryBar: { template: "<div />" },
        WeekCard: { template: "<div />" },
        WeekCardSkeleton: { template: "<div />" },
        EbButton: {
          template: "<button><slot /></button>",
        },
        EbCard: { template: "<div class='eb-card-stub'><slot /></div>" },
        MonthBar: { template: "<div />" },
      },
    },
  });
}

describe("CoachView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("1. loads coach dashboard on mount when store is empty", () => {
    const store = useCoachStore();
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);

    mountCoachView();

    expect(store.loadDashboard).toHaveBeenCalledOnce();
  });

  it("2. Manage athletes button is visible with no selected athlete", async () => {
    const store = useCoachStore();
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);
    store.loadAthletes = vi.fn().mockResolvedValue(undefined);
    // no dashboard set → no selected athlete

    const wrapper = mountCoachView();

    const manageButton = wrapper.findAll("button").find((btn) => btn.text().includes("Manage athletes"));
    expect(manageButton).toBeTruthy();
  });

  it("3. empty state card shown when no athlete selected", async () => {
    const store = useCoachStore();
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);
    // Ensure isLoading is false so the empty-state branch renders
    store.isLoading = false;

    const wrapper = mountCoachView();
    // Wait for onMounted microtasks to settle
    await wrapper.vm.$nextTick();

    // i18n may return czech or english depending on locale; check for the empty-state class
    expect(wrapper.find(".coach-card--empty").exists()).toBe(true);
  });

  it("4. athlete name shown in toolbar when athlete is selected", async () => {
    const store = useCoachStore();
    store.dashboard = { ...dashboardPayload };
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);

    const wrapper = mountCoachView();

    expect(wrapper.html()).toContain("Alice Runner");
  });

  it("5. focus input and Save focus button call coachStore.saveFocus", async () => {
    const store = useCoachStore();
    store.dashboard = { ...dashboardPayload };
    store.saveFocus = vi.fn().mockResolvedValue(undefined);
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);

    const wrapper = mountCoachView();
    const input = wrapper.get("#coach-focus-input");
    await input.setValue("Trail");

    const saveButton = wrapper.findAll("button").find((btn) => btn.text().includes("Save focus"));
    expect(saveButton).toBeTruthy();
    await saveButton!.trigger("click");

    expect(store.saveFocus).toHaveBeenCalledWith("Trail");
  });

  it("6. clicking Manage athletes button opens modal (calls loadAthletes)", async () => {
    const store = useCoachStore();
    store.dashboard = { ...dashboardPayload };
    store.loadAthletes = vi.fn().mockResolvedValue(undefined);
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);

    const wrapper = mountCoachView();
    const manageButton = wrapper.findAll("button").find((btn) => btn.text().includes("Manage athletes"));
    expect(manageButton).toBeTruthy();
    await manageButton!.trigger("click");

    expect(store.loadAthletes).toHaveBeenCalledOnce();
  });

  it("7. handleSidebarReorder calls saveAthleteOrder with hidden athletes appended", async () => {
    const store = useCoachStore();
    store.dashboard = {
      ...dashboardPayload,
      athletes: [
        { id: 101, name: "Alice Runner", focus: "10K", hidden: false, sort_order: 1, selected: true },
      ],
    };
    // managedAthletes includes a hidden athlete
    store.managedAthletes = [
      { id: 101, name: "Alice Runner", focus: "10K", hidden: false, sort_order: 1, selected: true },
      { id: 202, name: "Bob Climber", focus: "", hidden: true, sort_order: 2, selected: false },
    ] as any;
    store.saveAthleteOrder = vi.fn().mockResolvedValue(undefined);
    store.loadDashboard = vi.fn().mockResolvedValue(undefined);

    const wrapper = mountCoachView();

    // Get the CoachSidebar stub and emit a reorder event
    const sidebar = wrapper.findComponent({ name: "CoachSidebar" });
    // Directly invoke the handler via vm
    const vm = wrapper.vm as any;
    await vm.handleSidebarReorder([101]);

    expect(store.saveAthleteOrder).toHaveBeenCalledWith([101, 202]);
  });
});
