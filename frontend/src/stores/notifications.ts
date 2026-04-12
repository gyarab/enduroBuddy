import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { useI18n } from "@/composables/useI18n";
import {
  fetchNotifications,
  markNotificationsRead,
  type AppNotification,
} from "@/api/notifications";

export const useNotificationsStore = defineStore("notifications", () => {
  const items = ref<AppNotification[]>([]);
  const isLoading = ref(false);
  const isOpen = ref(false);
  const hasBootstrapped = ref(false);
  const errorMessage = ref("");
  const { t } = useI18n();
  const unreadCount = computed(() => items.value.filter((item) => item.unread).length);

  let pollTimer: number | null = null;

  function applyItems(nextItems: AppNotification[]) {
    items.value = [...nextItems];
  }

  async function refresh(options?: { silent?: boolean }) {
    if (!options?.silent) {
      isLoading.value = true;
    }
    errorMessage.value = "";
    try {
      const payload = await fetchNotifications();
      applyItems(payload.notifications);
      hasBootstrapped.value = true;
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : t("notifications.loadError");
    } finally {
      isLoading.value = false;
    }
  }

  async function markVisibleAsRead() {
    const unreadIds = items.value.filter((item) => item.unread).map((item) => item.id);
    if (!unreadIds.length) {
      return;
    }

    for (const item of items.value) {
      item.unread = false;
      item.read_at = item.read_at || new Date().toISOString();
    }

    try {
      await markNotificationsRead(unreadIds);
    } catch {
      await refresh({ silent: true });
    }
  }

  async function openDropdown() {
    isOpen.value = true;
    if (!hasBootstrapped.value) {
      await refresh();
    }
    await markVisibleAsRead();
  }

  function closeDropdown() {
    isOpen.value = false;
  }

  function toggleDropdown() {
    if (isOpen.value) {
      closeDropdown();
      return;
    }
    void openDropdown();
  }

  function startPolling() {
    if (pollTimer !== null) {
      return;
    }
    pollTimer = window.setInterval(() => {
      void refresh({ silent: true });
    }, 15000);
  }

  function stopPolling() {
    if (pollTimer !== null) {
      window.clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function initialize() {
    if (typeof window === "undefined") {
      return;
    }
    if (!hasBootstrapped.value) {
      void refresh();
    }
    startPolling();
  }

  return {
    closeDropdown,
    errorMessage,
    hasBootstrapped,
    initialize,
    isLoading,
    isOpen,
    items,
    markVisibleAsRead,
    openDropdown,
    refresh,
    stopPolling,
    toggleDropdown,
    unreadCount,
  };
});
