import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { TrainingRow } from "@/api/training";
import CompletedRow from "@/components/training/CompletedRow.vue";
import { useTrainingStore } from "@/stores/training";

function buildCompletedRow(overrides: Partial<TrainingRow> = {}): TrainingRow {
  return {
    id: 701,
    kind: "completed",
    status: "done",
    date: null,
    day_label: "",
    title: "",
    notes: "Steady finish",
    session_type: "RUN",
    planned_metrics: {
      planned_km_value: 8,
      planned_km_text: "8.0 km",
      planned_km_confidence: "high",
      planned_km_show: true,
      planned_km_line_km: "8.0 km",
      planned_km_line_reason: "",
      planned_km_line_where: "",
    },
    completed_metrics: {
      km: "7.5",
      minutes: "42",
      details: "Steady finish",
      avg_hr: 148,
      max_hr: 172,
    },
    editable: true,
    is_second_phase: false,
    can_add_second_phase: false,
    can_remove_second_phase: false,
    has_linked_activity: false,
    ...overrides,
  };
}

describe("CompletedRow", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renders completed metrics and hr summary", () => {
    const wrapper = mount(CompletedRow, {
      props: {
        row: buildCompletedRow(),
      },
    });

    expect(wrapper.text()).toContain("7.5 km - 42 min");
    expect(wrapper.text()).toContain("Steady finish");
    expect(wrapper.text()).toContain("HR 148 / 172");
    expect(wrapper.text()).toContain("Done");
  });

  it("saves completed draft through training store", async () => {
    const trainingStore = useTrainingStore();
    trainingStore.saveCompletedDraft = vi.fn().mockResolvedValue(undefined);

    const wrapper = mount(CompletedRow, {
      props: {
        row: buildCompletedRow(),
      },
    });

    await wrapper.trigger("click");

    const inputs = wrapper.findAll("input");
    await inputs[0]!.setValue("8.2");
    await inputs[1]!.setValue("45");
    await inputs[2]!.setValue("150");
    await inputs[3]!.setValue("176");
    await wrapper.get("textarea").setValue("Strong finish");

    const saveButton = wrapper.findAll("button").find((candidate) => candidate.text().includes("Save completed"));
    expect(saveButton).toBeTruthy();
    await saveButton!.trigger("click");

    expect(trainingStore.saveCompletedDraft).toHaveBeenCalledWith(701, [
      { field: "km", value: "8.2" },
      { field: "min", value: "45" },
      { field: "third", value: "Strong finish" },
      { field: "avg_hr", value: "150" },
      { field: "max_hr", value: "176" },
    ]);
  });

  it("does not call store when completed draft stays unchanged", async () => {
    const trainingStore = useTrainingStore();
    trainingStore.saveCompletedDraft = vi.fn().mockResolvedValue(undefined);

    const wrapper = mount(CompletedRow, {
      props: {
        row: buildCompletedRow(),
      },
    });

    await wrapper.trigger("click");

    const saveButton = wrapper.findAll("button").find((candidate) => candidate.text().includes("Save completed"));
    await saveButton!.trigger("click");

    expect(trainingStore.saveCompletedDraft).not.toHaveBeenCalled();
  });
});
