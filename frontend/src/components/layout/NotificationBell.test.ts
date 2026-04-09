import { createPinia, setActivePinia } from "pinia";
import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { AppNotification } from "@/api/notifications";
import NotificationBell from "@/components/layout/NotificationBell.vue";
import { useNotificationsStore } from "@/stores/notifications";

function buildNotification(overrides: Partial<AppNotification> = {}): AppNotification {
  return {
    id: 1,
    kind: "plan_updated",
    tone: "success",
    text: "Plan updated",
    actor: "Coach",
    created_at: "2026-04-09T10:00:00Z",
    read_at: null,
    unread: true,
    ...overrides,
  };
}

describe("NotificationBell", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renders unread badge and notification items", async () => {
    const store = useNotificationsStore();
    store.isOpen = true;
    store.items = [buildNotification(), buildNotification({ id: 2, unread: false, text: "Garmin sync finished" })];

    const wrapper = mount(NotificationBell);

    expect(wrapper.text()).toContain("2");
    expect(wrapper.text()).toContain("Notifikace");
    expect(wrapper.text()).toContain("Plan updated");
    expect(wrapper.text()).toContain("Garmin sync finished");
  });

  it("toggles dropdown through store action", async () => {
    const store = useNotificationsStore();
    store.toggleDropdown = vi.fn();

    const wrapper = mount(NotificationBell);
    await wrapper.get("button[aria-label='Notifikace']").trigger("click");

    expect(store.toggleDropdown).toHaveBeenCalledOnce();
  });

  it("refreshes from dropdown action and closes on outside click", async () => {
    const store = useNotificationsStore();
    store.isOpen = true;
    store.items = [buildNotification()];
    store.refresh = vi.fn().mockResolvedValue(undefined);
    store.closeDropdown = vi.fn();

    const wrapper = mount(NotificationBell, {
      attachTo: document.body,
    });

    const refreshButton = wrapper.findAll("button").find((candidate) => candidate.text() === "Refresh");
    expect(refreshButton).toBeTruthy();
    await refreshButton!.trigger("click");
    expect(store.refresh).toHaveBeenCalledWith({ silent: true });

    document.body.click();
    expect(store.closeDropdown).toHaveBeenCalled();
  });
});
