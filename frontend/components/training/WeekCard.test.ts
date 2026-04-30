import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import type { DashboardWeek } from "~/utils/api/training";
import WeekCard from "./WeekCard.vue";
import { useAuthStore } from "~/stores/auth";
import { useTrainingStore } from "~/stores/training";

const DATE = "2026-05-01";

function buildWeek(overrides: Partial<DashboardWeek> = {}): DashboardWeek {
  return {
    id: 1,
    week_index: 1,
    week_start: DATE,
    week_end: "2026-05-07",
    has_started: true,
    planned_total_km_text: "38 km",
    completed_total: { km: "0", time: "0", avg_hr: null, max_hr: null },
    planned_rows: [
      {
        id: 10,
        kind: "planned",
        status: "planned",
        date: DATE,
        day_label: "Po",
        title: "Tempo run",
        notes: "Keep pace",
        session_type: "RUN",
        planned_metrics: null,
        completed_metrics: null,
        editable: true,
        is_second_phase: false,
        can_add_second_phase: false,
        can_remove_second_phase: false,
        has_linked_activity: false,
      },
    ],
    completed_rows: [],
    ...overrides,
  };
}

function mountWeekCard(week: DashboardWeek = buildWeek()) {
  // Set up stores BEFORE mounting
  const authStore = useAuthStore();
  authStore.user = {
    capabilities: { has_garmin_connection: false, garmin_sync_enabled: false },
  } as any;

  const trainingStore = useTrainingStore();
  trainingStore.dashboard = {
    flags: { can_edit_completed: true, can_edit_planned: true, is_coach: false },
  } as any;

  return mount(WeekCard, {
    props: { week, editorContext: "athlete" },
  });
}

function buildWeekWithCompleted(): DashboardWeek {
  return buildWeek({
    completed_rows: [
      {
        id: 10,
        kind: "completed",
        status: "done",
        date: DATE,
        day_label: "Po",
        title: "",
        notes: "",
        session_type: "RUN",
        planned_metrics: null,
        completed_metrics: {
          km: "8.00",
          minutes: "45",
          details: "",
          avg_hr: 145,
          max_hr: 170,
        },
        editable: true,
        has_linked_activity: false,
      },
    ],
  });
}

describe("WeekCard — zone editing mutual exclusion", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("clicking planned cell shows title input, hides km input", async () => {
    const wrapper = mountWeekCard();
    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true);
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(false);
  });

  it("clicking completed cell shows km input, hides title input", async () => {
    const wrapper = mountWeekCard();
    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(true);
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(false);
  });

  it("switching from planned to completed zone hides planned inputs", async () => {
    const wrapper = mountWeekCard();

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true);

    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(false);
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(true);
  });

  it("switching from completed to planned zone hides completed inputs", async () => {
    const wrapper = mountWeekCard();

    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(true);

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    expect(wrapper.find(`[data-testid="input-km-${DATE}"]`).exists()).toBe(false);
    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true);
  });
});

describe("WeekCard — summary row", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("shows planned_total_km_text in summary row", () => {
    const wrapper = mountWeekCard();
    expect(wrapper.text()).toContain("38 km");
  });
});

describe("WeekCard — inline save", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("saves planned title edits through the training store", async () => {
    const wrapper = mountWeekCard();
    const trainingStore = useTrainingStore();
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined);

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click");
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("12 km steady");
    await wrapper.find(".wt__row").trigger("focusout", { relatedTarget: document.body });

    expect(trainingStore.savePlannedDraft).toHaveBeenCalledWith(10, [
      { field: "title", value: "12 km steady" },
    ]);
  });

  it("saves completed km edits through the training store", async () => {
    const wrapper = mountWeekCard(buildWeekWithCompleted());
    const trainingStore = useTrainingStore();
    trainingStore.saveCompletedDraft = vi.fn().mockResolvedValue(undefined);

    await wrapper.find(`[data-testid="cell-km-${DATE}"]`).trigger("click");
    await wrapper.find(`[data-testid="input-km-${DATE}"]`).setValue("9.25");
    await wrapper.find(".wt__row").trigger("focusout", { relatedTarget: document.body });

    expect(trainingStore.saveCompletedDraft).toHaveBeenCalledWith(10, [
      { field: "km", value: "9.25" },
    ]);
  });
});

describe("WeekCard — auto-save keeps edit open", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("edit input is still visible after 1-second debounce save", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await vi.advanceTimersByTimeAsync(1100)
    await nextTick()

    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(true)
  })

  it("focusout still closes the edit", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await wrapper.find(".wt__row").trigger("focusout", { relatedTarget: document.body })
    await nextTick()

    expect(wrapper.find(`[data-testid="input-title-${DATE}"]`).exists()).toBe(false)
  })

  it("successful auto-save adds wt__row--flash-planned-ok class", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined)

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await vi.advanceTimersByTimeAsync(1100)
    await nextTick()

    expect(wrapper.find(".wt__row").classes()).toContain("wt__row--flash-planned-ok")
  })

  it("failed auto-save adds wt__row--flash-err class", async () => {
    const wrapper = mountWeekCard()
    const trainingStore = useTrainingStore()
    trainingStore.savePlannedDraft = vi.fn().mockRejectedValue(new Error("Network error"))

    await wrapper.find(`[data-testid="cell-title-${DATE}"]`).trigger("click")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).setValue("10 km easy")
    await wrapper.find(`[data-testid="input-title-${DATE}"]`).trigger("input")
    await vi.advanceTimersByTimeAsync(1100)
    await nextTick()

    expect(wrapper.find(".wt__row").classes()).toContain("wt__row--flash-err")
  })
})
