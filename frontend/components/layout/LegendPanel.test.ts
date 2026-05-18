import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LegendPanel from "@/components/layout/LegendPanel.vue";

vi.mock("~/utils/api/legend", () => ({
  fetchLegend: vi.fn().mockResolvedValue({
    state: {
      zones: {
        z1: { from: "100", to: "120" },
        z2: { from: "121", to: "140" },
        z3: { from: "141", to: "160" },
        z4: { from: "161", to: "175" },
        z5: { from: "176", to: "190" },
      },
      aerobic_threshold: "150",
      anaerobic_threshold: "170",
      prs: [],
    },
  }),
  saveLegend: vi.fn().mockResolvedValue({ state: {} }),
  PR_DISTANCES: ["5k", "10k", "Maraton"],
}));

describe("LegendPanel", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("is hidden when open=false", () => {
    const wrapper = mount(LegendPanel, {
      props: { open: false, title: "Moje legenda", subtitle: "Upravuje trenér", editable: false },
    });
    expect(wrapper.find(".legend-panel--open").exists()).toBe(false);
  });

  it("adds open class when open=true", async () => {
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Moje legenda", subtitle: "Upravuje trenér", editable: false },
    });
    await vi.runAllTimersAsync();
    expect(wrapper.find(".legend-panel--open").exists()).toBe(true);
  });

  it("shows title and subtitle", () => {
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Moje legenda", subtitle: "Upravuje trenér", editable: false },
    });
    expect(wrapper.find(".legend-panel__title").text()).toBe("Moje legenda");
    expect(wrapper.find(".legend-panel__subtitle").text()).toBe("Upravuje trenér");
  });

  it("emits close when close button is clicked", async () => {
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Legenda", subtitle: "Sub", editable: true },
    });
    await wrapper.find(".legend-panel__close").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("calls saveLegend after debounce when editable and input changes", async () => {
    const { saveLegend } = await import("~/utils/api/legend");
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Legenda", subtitle: "Sub", editable: true },
    });
    await vi.runAllTimersAsync(); // let load complete

    const input = wrapper.find<HTMLInputElement>(".legend-panel__input");
    await input.setValue("999");
    await wrapper.vm.$nextTick();

    expect(saveLegend).not.toHaveBeenCalled();
    vi.advanceTimersByTime(800);
    await wrapper.vm.$nextTick();
    expect(saveLegend).toHaveBeenCalled();
  });

  it("does NOT auto-save when editable=false", async () => {
    const { saveLegend } = await import("~/utils/api/legend");
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Legenda", subtitle: "Sub", editable: false },
    });
    await vi.runAllTimersAsync();

    // Inputs should not be present when read-only
    expect(wrapper.find(".legend-panel__input").exists()).toBe(false);
    expect(saveLegend).not.toHaveBeenCalled();
  });

  it("does NOT auto-save when editable=false even if draft changes", async () => {
    const { saveLegend } = await import("~/utils/api/legend");
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Legenda", subtitle: "Sub", editable: false },
    });
    await vi.runAllTimersAsync();
    // Directly mutate the draft via exposed ref
    (wrapper.vm as any).draft.aerobic_threshold = "999";
    await wrapper.vm.$nextTick();
    vi.advanceTimersByTime(800);
    await wrapper.vm.$nextTick();
    expect(saveLegend).not.toHaveBeenCalled();
  });
});
