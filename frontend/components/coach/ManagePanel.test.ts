import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ManagePanel from "@/components/coach/ManagePanel.vue";

vi.mock("~/utils/api/coach", () => ({
  fetchCoachCode: vi.fn().mockResolvedValue({ coach_join_code: "ABC123" }),
  fetchJoinRequests: vi.fn().mockResolvedValue({ requests: [] }),
  approveJoinRequest: vi.fn().mockResolvedValue({}),
  rejectJoinRequest: vi.fn().mockResolvedValue({}),
  removeAthlete: vi.fn().mockResolvedValue({}),
}));

const athletes = [
  { id: 1, name: "Jan Novák", hidden: false, selected: true, focus: "5k", sort_order: 1 },
  { id: 2, name: "Eva Malá", hidden: true, selected: false, focus: null, sort_order: 2 },
];

describe("ManagePanel", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("is not visible when open=false", () => {
    const wrapper = mount(ManagePanel, {
      props: { open: false, athletes },
    });
    expect(wrapper.find(".manage-panel--open").exists()).toBe(false);
  });

  it("is visible when open=true", () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    expect(wrapper.find(".manage-panel--open").exists()).toBe(true);
  });

  it("shows athletes section by default", () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    expect(wrapper.find(".manage-panel__menu-item--active").text()).toContain("Svěřenci");
    expect(wrapper.find(".manage-content--athletes").exists()).toBe(true);
  });

  it("switches to invite section when menu item is clicked", async () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    const inviteBtn = wrapper
      .findAll(".manage-panel__menu-item")
      .find((el) => el.text().includes("Pozvat"));
    await inviteBtn!.trigger("click");
    expect(wrapper.find(".manage-content--invite").exists()).toBe(true);
  });

  it("emits close when close button is clicked", async () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    await wrapper.find(".manage-panel__close").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("disables remove confirm button when typed name does not match athlete name", async () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    // Click the remove button on the first athlete (Jan Novák)
    const removeBtn = wrapper
      .findAll(".manage-panel__icon-btn--danger")
      .at(0);
    await removeBtn!.trigger("click");
    // Confirm dialog appears — confirm button should be disabled with empty input
    const confirmBtn = wrapper.find(".manage-panel__btn--danger");
    expect(confirmBtn.attributes("disabled")).toBeDefined();
    // Type wrong name
    const input = wrapper.find(".manage-panel__remove-input");
    await input.setValue("Wrong Name");
    expect(wrapper.find(".manage-panel__btn--danger").attributes("disabled")).toBeDefined();
    // Type correct name
    await input.setValue("Jan Novák");
    expect(wrapper.find(".manage-panel__btn--danger").attributes("disabled")).toBeUndefined();
  });

  it("emits athleteRemoved after confirming remove with correct name", async () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    const removeBtn = wrapper.findAll(".manage-panel__icon-btn--danger").at(0);
    await removeBtn!.trigger("click");
    const input = wrapper.find(".manage-panel__remove-input");
    await input.setValue("Jan Novák");
    const confirmBtn = wrapper.find(".manage-panel__btn--danger");
    await confirmBtn.trigger("click");
    // Wait for async removeAthlete mock to resolve
    await new Promise((r) => setTimeout(r, 0));
    await wrapper.vm.$nextTick();
    expect(wrapper.emitted("athleteRemoved")).toBeTruthy();
    expect(wrapper.emitted("athleteRemoved")![0]).toEqual([1]);
  });
});
