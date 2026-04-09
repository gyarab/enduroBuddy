import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  addSecondPhaseTraining,
  type DashboardPayload,
  fetchDashboard,
  removeSecondPhaseTraining,
  updateCompletedTraining,
  updatePlannedTraining,
} from "@/api/training";
import { useTrainingStore } from "@/stores/training";

vi.mock("@/api/training", () => ({
  addSecondPhaseTraining: vi.fn(),
  fetchDashboard: vi.fn(),
  removeSecondPhaseTraining: vi.fn(),
  updateCompletedTraining: vi.fn(),
  updatePlannedTraining: vi.fn(),
}));

vi.mock("@/stores/toasts", () => ({
  useToastStore: () => ({ push: vi.fn() }),
}));

vi.mock("@/composables/useI18n", () => ({
  useI18n: () => ({ t: (k: string) => k }),
}));

const dashboardPayload: DashboardPayload = {
  selected_month: { id: 1, value: "2026-04", label: "Duben 2026", year: 2026, month: 4 },
  navigation: {
    previous: { value: "2026-03", label: "Březen 2026" },
    next: null,
    available: [],
  },
  summary: {
    planned_sessions: 1,
    completed_sessions: 0,
    planned_km: 10,
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
      planned_total_km_text: "10.0 km/week",
      completed_total: { km: "-", time: "-", avg_hr: null, max_hr: null },
      planned_rows: [
        {
          id: 501,
          kind: "planned",
          status: "planned",
          date: "2026-04-08",
          day_label: "St",
          title: "10 km easy",
          notes: "",
          session_type: "RUN",
          planned_metrics: {
            planned_km_value: 10,
            planned_km_text: "10.0 km",
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
      completed_rows: [
        {
          id: 601,
          kind: "completed",
          status: "done",
          date: "2026-04-08",
          day_label: "St",
          title: "-",
          notes: "",
          session_type: "RUN",
          planned_metrics: null,
          completed_metrics: {
            km: "9.5",
            minutes: "55",
            details: "",
            avg_hr: 145,
            max_hr: 165,
          },
          editable: true,
          has_linked_activity: false,
        },
      ],
    },
  ],
  flags: { is_coach: false, can_edit_planned: true, can_edit_completed: true },
};

describe("useTrainingStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.mocked(fetchDashboard).mockResolvedValue(structuredClone(dashboardPayload));
    vi.mocked(updatePlannedTraining).mockResolvedValue({ ok: true });
    vi.mocked(updateCompletedTraining).mockResolvedValue({ ok: true });
    vi.mocked(addSecondPhaseTraining).mockResolvedValue({ ok: true });
    vi.mocked(removeSecondPhaseTraining).mockResolvedValue({ ok: true });
  });

  // -------------------------------------------------------------------------
  // 1. Loading state
  // -------------------------------------------------------------------------
  describe("loadDashboard — loading state", () => {
    it("sets isLoading true while fetching and resets to false after", async () => {
      let capturedDuringFetch: boolean | undefined;

      vi.mocked(fetchDashboard).mockImplementation(async () => {
        capturedDuringFetch = store.isLoading;
        return structuredClone(dashboardPayload);
      });

      const store = useTrainingStore();
      expect(store.isLoading).toBe(false);
      expect(store.hasData).toBe(false);

      await store.loadDashboard();

      expect(capturedDuringFetch).toBe(true);
      expect(store.isLoading).toBe(false);
      expect(store.hasData).toBe(true);
    });

    it("exposes weeks and summary after a successful load", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      expect(store.weeks).toHaveLength(1);
      expect(store.summary?.planned_km).toBe(10);
    });
  });

  // -------------------------------------------------------------------------
  // 2. Error state
  // -------------------------------------------------------------------------
  describe("loadDashboard — error state", () => {
    it("sets errorMessage when fetchDashboard rejects and resets isLoading", async () => {
      vi.mocked(fetchDashboard).mockRejectedValueOnce(new Error("Network error"));

      const store = useTrainingStore();
      await store.loadDashboard();

      expect(store.errorMessage).toBe("Network error");
      expect(store.isLoading).toBe(false);
    });

    it("uses fallback translation key when error is not an Error instance", async () => {
      vi.mocked(fetchDashboard).mockRejectedValueOnce("something went wrong");

      const store = useTrainingStore();
      await store.loadDashboard();

      expect(store.errorMessage).toBe("trainingStore.loadError");
    });
  });

  // -------------------------------------------------------------------------
  // 3. Silent refresh
  // -------------------------------------------------------------------------
  describe("loadDashboard — silent refresh", () => {
    it("uses isRefreshing instead of isLoading when silent: true", async () => {
      let capturedIsLoading: boolean | undefined;
      let capturedIsRefreshing: boolean | undefined;

      vi.mocked(fetchDashboard).mockImplementation(async () => {
        capturedIsLoading = store.isLoading;
        capturedIsRefreshing = store.isRefreshing;
        return structuredClone(dashboardPayload);
      });

      const store = useTrainingStore();
      await store.loadDashboard("2026-04", { silent: true });

      expect(capturedIsLoading).toBe(false);
      expect(capturedIsRefreshing).toBe(true);
      expect(store.isRefreshing).toBe(false);
      expect(store.isLoading).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // 4. Month navigation
  // -------------------------------------------------------------------------
  describe("goToPreviousMonth / goToNextMonth", () => {
    it("goToPreviousMonth calls loadDashboard with previous month value", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      vi.mocked(fetchDashboard).mockClear();
      await store.goToPreviousMonth();

      expect(fetchDashboard).toHaveBeenCalledWith("2026-03");
    });

    it("goToNextMonth does nothing when navigation.next is null", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      vi.mocked(fetchDashboard).mockClear();
      await store.goToNextMonth();

      expect(fetchDashboard).not.toHaveBeenCalled();
    });

    it("goToNextMonth navigates when next is available", async () => {
      const payloadWithNext = structuredClone(dashboardPayload);
      payloadWithNext.navigation.next = { value: "2026-05", label: "Květen 2026" };
      vi.mocked(fetchDashboard).mockResolvedValueOnce(payloadWithNext);

      const store = useTrainingStore();
      await store.loadDashboard();

      vi.mocked(fetchDashboard).mockClear();
      await store.goToNextMonth();

      expect(fetchDashboard).toHaveBeenCalledWith("2026-05");
    });
  });

  // -------------------------------------------------------------------------
  // 5. Optimistic planned patch via savePlannedDraft
  // -------------------------------------------------------------------------
  describe("savePlannedDraft — optimistic patch", () => {
    it("calls updatePlannedTraining and patches row title in weeks", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      await store.savePlannedDraft(501, [{ field: "title", value: "8 km easy" }]);

      expect(updatePlannedTraining).toHaveBeenCalledWith(501, { field: "title", value: "8 km easy" });
      expect(store.weeks[0]?.planned_rows[0]?.title).toBe("8 km easy");
    });

    it("updates planned_total_km_text on the week after a title change", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      // "8 km easy" should parse to 8 km, changing week total from 10.0 to 8.0
      await store.savePlannedDraft(501, [{ field: "title", value: "8 km easy" }]);

      expect(store.weeks[0]?.planned_total_km_text).toContain("8.0");
    });

    it("applies multiple updates in order", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      await store.savePlannedDraft(501, [
        { field: "title", value: "12 km easy" },
        { field: "notes", value: "recovery pace" },
      ]);

      expect(updatePlannedTraining).toHaveBeenCalledTimes(2);
      expect(store.weeks[0]?.planned_rows[0]?.title).toBe("12 km easy");
      expect(store.weeks[0]?.planned_rows[0]?.notes).toBe("recovery pace");
    });
  });

  // -------------------------------------------------------------------------
  // 6. Completed row patch via saveCompletedDraft
  // -------------------------------------------------------------------------
  describe("saveCompletedDraft — completed row patch", () => {
    it("calls updateCompletedTraining and patches completed_metrics.km", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      await store.saveCompletedDraft(601, [{ field: "km", value: "10.2" }]);

      expect(updateCompletedTraining).toHaveBeenCalledWith(601, { field: "km", value: "10.2" });
      expect(store.weeks[0]?.completed_rows[0]?.completed_metrics?.km).toBe("10.2");
    });

    it("patches completed_metrics.minutes", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      await store.saveCompletedDraft(601, [{ field: "min", value: "62" }]);

      expect(store.weeks[0]?.completed_rows[0]?.completed_metrics?.minutes).toBe("62");
    });

    it("patches avg_hr as a number", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      await store.saveCompletedDraft(601, [{ field: "avg_hr", value: "152" }]);

      expect(store.weeks[0]?.completed_rows[0]?.completed_metrics?.avg_hr).toBe(152);
    });
  });

  // -------------------------------------------------------------------------
  // 7. Second phase add
  // -------------------------------------------------------------------------
  describe("addSecondPhase", () => {
    it("calls addSecondPhaseTraining then silently reloads the dashboard", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      vi.mocked(fetchDashboard).mockClear();
      await store.addSecondPhase(501);

      expect(addSecondPhaseTraining).toHaveBeenCalledWith(501);
      // silent reload should use the current selected month
      expect(fetchDashboard).toHaveBeenCalledWith("2026-04");
    });

    it("silent reload uses isRefreshing not isLoading", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      let capturedIsLoading: boolean | undefined;
      let capturedIsRefreshing: boolean | undefined;

      vi.mocked(fetchDashboard).mockImplementation(async () => {
        capturedIsLoading = store.isLoading;
        capturedIsRefreshing = store.isRefreshing;
        return structuredClone(dashboardPayload);
      });

      await store.addSecondPhase(501);

      expect(capturedIsLoading).toBe(false);
      expect(capturedIsRefreshing).toBe(true);
    });
  });

  // -------------------------------------------------------------------------
  // 8. Summary recompute after planned patch
  // -------------------------------------------------------------------------
  describe("summary recompute", () => {
    it("updates planned_km in summary after a title patch changes the km value", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      expect(store.summary?.planned_km).toBe(10);

      // "5 km easy" → 5 km
      await store.savePlannedDraft(501, [{ field: "title", value: "5 km easy" }]);

      expect(store.summary?.planned_km).toBe(5);
    });

    it("sets planned_km to 0 when title is cleared to a rest value", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      await store.savePlannedDraft(501, [{ field: "title", value: "volno" }]);

      expect(store.summary?.planned_km).toBe(0);
    });

    it("recomputes completed_km in summary after completed patch", async () => {
      const store = useTrainingStore();
      await store.loadDashboard();

      // "9.5" km in fixture → completed_km starts at 0 (summary from server)
      // After patch to "11.5", recomputeCompletedTotals runs and summary picks it up
      await store.saveCompletedDraft(601, [{ field: "km", value: "11.5" }]);

      expect(store.summary?.completed_km).toBe(11.5);
    });
  });
});
