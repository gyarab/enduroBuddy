import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import type { CoachAthlete } from "@/api/coach";
import CoachSidebar from "@/components/coach/CoachSidebar.vue";

const athletes: CoachAthlete[] = [
  { id: 101, name: "Alice Runner", focus: "10K", hidden: false, sort_order: 1, selected: true },
  { id: 202, name: "Bob Climber", focus: "", hidden: false, sort_order: 2, selected: false },
  { id: 303, name: "Alexandr Procházka-Müller", focus: "", hidden: true, sort_order: 3, selected: false },
];

describe("CoachSidebar", () => {
  it("renders all athletes including hidden ones", () => {
    const wrapper = mount(CoachSidebar, { props: { athletes } });
    expect(wrapper.text()).toContain("Alice Runner");
    expect(wrapper.text()).toContain("Bob Climber");
    expect(wrapper.text()).toContain("Alexandr Procházka-Müller");
  });

  it("applies active class to selected athlete", () => {
    const wrapper = mount(CoachSidebar, { props: { athletes } });
    const active = wrapper.find(".coach-sidebar__item--active");
    expect(active.exists()).toBe(true);
    expect(active.text()).toContain("Alice Runner");
  });

  it("applies hidden class to hidden athlete", () => {
    const wrapper = mount(CoachSidebar, { props: { athletes } });
    const buttons = wrapper.findAll(".coach-sidebar__item");
    expect(buttons[2]!.classes()).toContain("coach-sidebar__item--hidden");
  });

  it("shows focus tag when athlete has focus", () => {
    const wrapper = mount(CoachSidebar, { props: { athletes } });
    expect(wrapper.find(".coach-sidebar__focus").text()).toBe("10K");
  });

  it("shows full name with title attribute for tooltip", () => {
    const wrapper = mount(CoachSidebar, { props: { athletes } });
    const nameEls = wrapper.findAll(".coach-sidebar__name");
    expect(nameEls[2]!.attributes("title")).toBe("Alexandr Procházka-Müller");
  });

  it("emits select on click", async () => {
    const wrapper = mount(CoachSidebar, { props: { athletes } });
    await wrapper.findAll(".coach-sidebar__item")[1]!.trigger("click");
    expect(wrapper.emitted("select")).toEqual([[202]]);
  });

  it("emits reorder after drag-and-drop sequence", async () => {
    const wrapper = mount(CoachSidebar, { props: { athletes } });
    const items = wrapper.findAll(".coach-sidebar__item");
    await items[0]!.trigger("dragstart");
    await items[1]!.trigger("dragover");
    await items[1]!.trigger("drop");
    expect(wrapper.emitted("reorder")).toBeTruthy();
    const [emittedIds] = wrapper.emitted("reorder")![0] as [number[]];
    expect(emittedIds).toContain(101);
    expect(emittedIds).toContain(202);
  });

  it("opens context menu on contextmenu event", async () => {
    const wrapper = mount(CoachSidebar, { props: { athletes }, attachTo: document.body });
    await wrapper.findAll(".coach-sidebar__item")[1]!.trigger("contextmenu");
    const ctxItems = document.querySelectorAll(".eb-ctx__item");
    expect(ctxItems.length).toBeGreaterThan(0);
    wrapper.unmount();
  });

  it("moves focus down with ArrowDown key", async () => {
    const wrapper = mount(CoachSidebar, { props: { athletes }, attachTo: document.body });
    const items = wrapper.findAll(".coach-sidebar__item");
    items[0]!.element.focus();
    await items[0]!.trigger("keydown", { key: "ArrowDown" });
    expect(document.activeElement).toBe(items[1]!.element);
    wrapper.unmount();
  });

  it("moves focus up with ArrowUp key", async () => {
    const wrapper = mount(CoachSidebar, { props: { athletes }, attachTo: document.body });
    const items = wrapper.findAll(".coach-sidebar__item");
    items[1]!.element.focus();
    await items[1]!.trigger("keydown", { key: "ArrowUp" });
    expect(document.activeElement).toBe(items[0]!.element);
    wrapper.unmount();
  });
});
