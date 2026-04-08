<script setup lang="ts">
defineProps<{
  unreadCount?: number;
}>();
</script>

<template>
  <button class="notification-bell" type="button" aria-label="Notifikace">
    <span class="notification-bell__icon">!</span>
    <span v-if="unreadCount" class="notification-bell__badge">{{ unreadCount > 9 ? "9+" : unreadCount }}</span>
  </button>
</template>

<style scoped>
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
</style>
