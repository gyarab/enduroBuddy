import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PlannedRow from "@/components/training/PlannedRow.vue";
import { useCoachStore } from "@/stores/coach";
import { useTrainingStore } from "@/stores/training";
function buildRow(overrides = {}) {
    return {
        id: 501,
        kind: "planned",
        status: "planned",
        date: "2026-04-08",
        day_label: "St",
        title: "8 km easy",
        notes: "Keep it relaxed",
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
        ...overrides,
    };
}
describe("PlannedRow", () => {
    beforeEach(() => {
        setActivePinia(createPinia());
    });
    it("saves planned draft through athlete training store by default", async () => {
        const trainingStore = useTrainingStore();
        const coachStore = useCoachStore();
        trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined);
        coachStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined);
        const wrapper = mount(PlannedRow, {
            props: {
                row: buildRow(),
            },
        });
        await wrapper.get("button").trigger("click");
        await wrapper.get("textarea").setValue("6x400m");
        const buttons = wrapper.findAll("button");
        await buttons[buttons.length - 1].trigger("click");
        expect(trainingStore.savePlannedDraft).toHaveBeenCalledWith(501, [{ field: "title", value: "6x400m" }]);
        expect(coachStore.savePlannedDraft).not.toHaveBeenCalled();
    });
    it("routes save through coach store when editorContext is coach", async () => {
        const trainingStore = useTrainingStore();
        const coachStore = useCoachStore();
        trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined);
        coachStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined);
        const wrapper = mount(PlannedRow, {
            props: {
                row: buildRow(),
                editorContext: "coach",
            },
        });
        await wrapper.get("button").trigger("click");
        await wrapper.get("textarea").setValue("3x(1 km)");
        const buttons = wrapper.findAll("button");
        await buttons[buttons.length - 1].trigger("click");
        expect(coachStore.savePlannedDraft).toHaveBeenCalledWith(501, [{ field: "title", value: "3x(1 km)" }]);
        expect(trainingStore.savePlannedDraft).not.toHaveBeenCalled();
    });
    it("uses coach second-phase action in coach context", async () => {
        const trainingStore = useTrainingStore();
        const coachStore = useCoachStore();
        trainingStore.addSecondPhase = vi.fn().mockResolvedValue(undefined);
        coachStore.addSecondPhase = vi.fn().mockResolvedValue(undefined);
        const wrapper = mount(PlannedRow, {
            props: {
                row: buildRow(),
                editorContext: "coach",
            },
        });
        await wrapper.get("button").trigger("click");
        const addSecondPhaseButton = wrapper
            .findAll("button")
            .find((candidate) => candidate.text().includes("Add 2nd phase"));
        expect(addSecondPhaseButton).toBeTruthy();
        await addSecondPhaseButton.trigger("click");
        expect(coachStore.addSecondPhase).toHaveBeenCalledWith(501);
        expect(trainingStore.addSecondPhase).not.toHaveBeenCalled();
    });
    it("renders parser preview after entering structured workout text", async () => {
        const trainingStore = useTrainingStore();
        trainingStore.savePlannedDraft = vi.fn().mockResolvedValue(undefined);
        const wrapper = mount(PlannedRow, {
            props: {
                row: buildRow(),
            },
        });
        await wrapper.get("button").trigger("click");
        await wrapper.get("textarea").setValue("6x400m");
        expect(wrapper.text()).toContain("Parsed preview");
        expect(wrapper.text()).toContain("2.4 km");
    });
});
