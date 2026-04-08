import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  addCoachSecondPhaseTraining,
  type CoachAthletesPayload,
  type CoachDashboardPayload,
  fetchCoachAthletes,
  fetchCoachDashboard,
  removeCoachSecondPhaseTraining,
  reorderCoachAthletes,
  updateCoachAthleteVisibility,
  updateCoachPlannedTraining,
} from "@/api/coach";
import { useCoachStore } from "@/stores/coach";

vi.mock("@/api/coach", () => ({
  addCoachSecondPhaseTraining: vi.fn(),
  fetchCoachAthletes: vi.fn(),
  fetchCoachDashboard: vi.fn(),
  removeCoachSecondPhaseTraining: vi.fn(),
  reorderCoachAthletes: vi.fn(),
  updateCoachAthleteFocus: vi.fn(),
  updateCoachAthleteVisibility: vi.fn(),
  updateCoachPlannedTraining: vi.fn(),
}));

const dashboardPayload: CoachDashboardPayload = {
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
      completed_total: {
        km: "-",
        time: "-",
        avg_hr: null,
        max_hr: null,
      },
      planned_rows: [
        {
          id: 501,
          kind: "planned",
          status: "planned",
          date: "2026-04-08",
          day_label: "St",
          title: "8 km easy",
          notes: "",
          session_type: "RUN",
          planned_metrics: {
            planned_km_value: 8,
            planned_km_text: "8.0 km",
            planned_km_confidence: "high",
          },
          completed_metrics: null,
          editable: true,
          is_second_phase: false,
          can_add_second_phase: true,
          can_remove_second_phase: false,
          has_linked_activity: false,
        },
      ],
      completed_rows: [],
    },
  ],
  flags: {
    is_coach: true,
    can_edit_planned: true,
    can_edit_completed: false,
  },
};

const managedAthletesPayload: CoachAthletesPayload = {
  athletes: [
    { id: 101, name: "Alice Runner", focus: "10K", hidden: false, sort_order: 1, selected: true },
    { id: 202, name: "Bob Climber", focus: "", hidden: false, sort_order: 2, selected: false },
    { id: 303, name: "Cara Trail", focus: "Hill", hidden: true, sort_order: 3, selected: false },
  ],
};

describe("useCoachStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.mocked(fetchCoachDashboard).mockResolvedValue(structuredClone(dashboardPayload));
    vi.mocked(fetchCoachAthletes).mockResolvedValue(structuredClone(managedAthletesPayload));
    vi.mocked(reorderCoachAthletes).mockResolvedValue(structuredClone(managedAthletesPayload));
    vi.mocked(updateCoachAthleteVisibility).mockResolvedValue({
      ok: true,
      athlete_id: 202,
      hidden: true,
      athletes: [
        { id: 101, name: "Alice Runner", focus: "10K", hidden: false, sort_order: 1, selected: true },
        { id: 202, name: "Bob Climber", focus: "", hidden: true, sort_order: 2, selected: false },
        { id: 303, name: "Cara Trail", focus: "Hill", hidden: true, sort_order: 3, selected: false },
      ],
    });
    vi.mocked(updateCoachPlannedTraining).mockResolvedValue({ ok: true });
    vi.mocked(addCoachSecondPhaseTraining).mockResolvedValue({ ok: true });
    vi.mocked(removeCoachSecondPhaseTraining).mockResolvedValue({ ok: true });
  });

  it("loads dashboard and managed athletes together", async () => {
    const store = useCoachStore();

    await store.loadDashboard();

    expect(fetchCoachDashboard).toHaveBeenCalledOnce();
    expect(fetchCoachAthletes).toHaveBeenCalledWith(101);
    expect(store.selectedAthlete?.name).toBe("Alice Runner");
    expect(store.athletes).toHaveLength(2);
    expect(store.managedAthletes).toHaveLength(3);
  });

  it("reorders athletes and keeps sidebar filtered to visible ones", async () => {
    const store = useCoachStore();
    await store.loadDashboard();

    await store.saveAthleteOrder([202, 101, 303]);

    expect(reorderCoachAthletes).toHaveBeenCalledWith([202, 101, 303]);
    expect(store.managedAthletes).toHaveLength(3);
    expect(store.athletes).toHaveLength(2);
    expect(store.athletes.every((athlete) => !athlete.hidden)).toBe(true);
  });

  it("hides athlete from sidebar while keeping managed list intact", async () => {
    const store = useCoachStore();
    await store.loadDashboard();

    await store.setAthleteHidden(202, true);

    expect(updateCoachAthleteVisibility).toHaveBeenCalledWith(202, true);
    expect(store.managedAthletes.find((athlete) => athlete.id === 202)?.hidden).toBe(true);
    expect(store.athletes.find((athlete) => athlete.id === 202)).toBeUndefined();
  });

  it("patches planned row locally after coach save", async () => {
    const store = useCoachStore();
    await store.loadDashboard();

    await store.savePlannedDraft(501, [{ field: "title", value: "6x400m" }]);

    expect(updateCoachPlannedTraining).toHaveBeenCalledWith(501, { field: "title", value: "6x400m" });
    expect(store.weeks[0]?.planned_rows[0]?.title).toBe("6x400m");
    expect(store.weeks[0]?.planned_rows[0]?.planned_metrics?.planned_km_value).toBe(2.4);
  });
});
