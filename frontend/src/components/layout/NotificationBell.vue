<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

import { useNotificationsStore } from "@/stores/notifications";

const notificationsStore = useNotificationsStore();
const rootRef = ref<HTMLElement | null>(null);

function handleDocumentClick(event: MouseEvent) {
  const target = event.target;
  if (!(target instanceof Node)) {
    return;
  }
  if (rootRef.value && !rootRef.value.contains(target)) {
    notificationsStore.closeDropdown();
  }
}

onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
});

onBeforeUnmount(() => {
  document.removeEventListener("click", handleDocumentClick);
});
</script>

<template>
  <div ref="rootRef" class="notification-bell-wrap">
    <button class="notification-bell" type="button" aria-label="Notifikace" @click.stop="notificationsStore.toggleDropdown">
      <span class="notification-bell__icon">!</span>
      <span v-if="notificationsStore.unreadCount" class="notification-bell__badge">
        {{ notificationsStore.unreadCount > 9 ? "9+" : notificationsStore.unreadCount }}
      </span>
    </button>

    <div v-if="notificationsStore.isOpen" class="notification-dropdown">
      <div class="notification-dropdown__header">
        <span>Notifikace</span>
        <button class="notification-dropdown__action" type="button" @click="notificationsStore.refresh({ silent: true })">
          Refresh
        </button>
      </div>

      <div v-if="notificationsStore.errorMessage" class="notification-dropdown__state notification-dropdown__state--danger">
        {{ notificationsStore.errorMessage }}
      </div>

      <div v-else-if="notificationsStore.isLoading && !notificationsStore.items.length" class="notification-dropdown__state">
        Nacitani...
      </div>

      <div v-else-if="!notificationsStore.items.length" class="notification-dropdown__state">
        Zatim zadne notifikace.
      </div>

      <div v-else class="notification-dropdown__list">
        <div
          v-for="item in notificationsStore.items"
          :key="item.id"
          class="notification-item"
          :class="[`notification-item--${item.tone}`, { 'notification-item--unread': item.unread }]"
        >
          <span class="notification-item__dot" />
          <div class="notification-item__content">
            <div class="notification-item__text">{{ item.text }}</div>
            <div class="notification-item__meta">
              <span v-if="item.actor">{{ item.actor }}</span>
              <span v-if="item.created_at">{{ new Date(item.created_at).toLocaleString() }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notification-bell-wrap {
  position: relative;
}

.notification-bell {
  position: relative;
  display: inline-grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border: 1px solid transparent;
  border-radius: var(--eb-radius-md);
  background: transparent;
  color: var(--eb-text-soft);
  transition:
    background-color 150ms ease-out,
    color 150ms ease-out;
}

.notification-bell:hover {
  background: var(--eb-surface-hover);
  color: var(--eb-text);
}

.notification-bell__icon {
  font-size: 1rem;
  font-weight: 700;
}

.notification-bell__badge {
  position: absolute;
  top: 0.15rem;
  right: 0.15rem;
  display: inline-grid;
  place-items: center;
  min-width: 1.1rem;
  height: 1.1rem;
  padding: 0 0.2rem;
  border-radius: 999px;
  background: var(--eb-lime);
  color: var(--eb-bg);
  font-size: 0.625rem;
  font-weight: 700;
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  width: min(20rem, calc(100vw - 2rem));
  max-height: 25rem;
  overflow: auto;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-surface);
  box-shadow: var(--eb-shadow-soft);
}

.notification-dropdown__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--eb-border);
  color: var(--eb-text);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.notification-dropdown__action {
  border: 0;
  background: transparent;
  color: var(--eb-blue);
  font-size: 0.75rem;
}

.notification-dropdown__list {
  display: grid;
}

.notification-dropdown__state {
  padding: 1rem;
  color: var(--eb-text-soft);
  font-size: 0.8125rem;
}

.notification-dropdown__state--danger {
  color: var(--eb-danger);
}

.notification-item {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  border-bottom: 1px solid var(--eb-border);
}

.notification-item:last-child {
  border-bottom: 0;
}

.notification-item--unread {
  background: rgba(200, 255, 0, 0.04);
}

.notification-item__dot {
  width: 0.5rem;
  height: 0.5rem;
  margin-top: 0.35rem;
  border-radius: 999px;
  background: var(--eb-text-muted);
}

.notification-item--info .notification-item__dot,
.notification-item--success .notification-item__dot {
  background: var(--eb-lime);
}

.notification-item--warning .notification-item__dot {
  background: var(--eb-warning);
}

.notification-item--danger .notification-item__dot {
  background: var(--eb-danger);
}

.notification-item__content {
  display: grid;
  gap: 0.35rem;
}

.notification-item__text {
  color: var(--eb-text);
  font-size: 0.8125rem;
  line-height: 1.45;
}

.notification-item__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
}
</style>
