import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { nextTick } from "vue";

import EbContextMenu from "@/components/ui/EbContextMenu.vue";
import type { ContextMenuItem } from "@/components/ui/EbContextMenu.vue";

const items: ContextMenuItem[] = [
  { action: "go", label: "Go to dashboard" },
  { action: "hide", label: "Hide athlete" },
  { action: "remove", label: "Remove...", variant: "danger" },
];

describe("EbContextMenu", () => {
  it("renders nothing when closed", () => {
    const wrapper = mount(EbContextMenu, {
      props: { open: false, items, x: 100, y: 100 },
      attachTo: document.body,
    });
    expect(document.querySelector(".eb-ctx")).toBeNull();
    wrapper.unmount();
  });

  it("renders all items when open", () => {
    const wrapper = mount(EbContextMenu, {
      props: { open: true, items, x: 100, y: 100 },
      attachTo: document.body,
    });
    const menu = document.querySelector(".eb-ctx");
    expect(menu).not.toBeNull();
    expect(menu!.textContent).toContain("Go to dashboard");
    expect(menu!.textContent).toContain("Hide athlete");
    expect(menu!.textContent).toContain("Remove...");
    wrapper.unmount();
  });

  it("emits select with action when item clicked", async () => {
    const wrapper = mount(EbContextMenu, {
      props: { open: true, items, x: 100, y: 100 },
      attachTo: document.body,
    });
    const buttons = document.querySelectorAll(".eb-ctx__item");
    (buttons[1] as HTMLElement).click();
    expect(wrapper.emitted("select")).toEqual([["hide"]]);
    wrapper.unmount();
  });

  it("emits close on Escape key", async () => {
    const wrapper = mount(EbContextMenu, {
      props: { open: true, items, x: 100, y: 100 },
      attachTo: document.body,
    });
    await nextTick();
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    await nextTick();
    expect(wrapper.emitted("close")).toBeTruthy();
    wrapper.unmount();
  });

  it("applies danger variant class", () => {
    const wrapper = mount(EbContextMenu, {
      props: { open: true, items, x: 100, y: 100 },
      attachTo: document.body,
    });
    const buttons = document.querySelectorAll(".eb-ctx__item");
    expect(buttons[2]!.classList.contains("eb-ctx__item--danger")).toBe(true);
    wrapper.unmount();
  });
});
