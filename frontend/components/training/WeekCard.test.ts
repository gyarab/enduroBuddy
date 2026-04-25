import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { DashboardWeek } from "~/utils/api/training";
import WeekCard from "./WeekCard.vue";
import { useAuthStore } from "@/stores/auth";
import { useTrainingStore } from "@/stores/training";

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
  const wrapper = mount(WeekCard, {
    props: { week, editorContext: "athlete" },
  });

  const authStore = useAuthStore();
  authStore.user = {
    capabilities: { has_garmin_connection: false, garmin_sync_enabled: false },
  } as any;

  const trainingStore = useTrainingStore();
  trainingStore.dashboard = {
    flags: { can_edit_completed: true, can_edit_planned: true, is_coach: false },
  } as any;
  trainingStore.selectedMonthValue = "2026-05";

  return wrapper;
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
