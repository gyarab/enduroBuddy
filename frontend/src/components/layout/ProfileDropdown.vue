<script setup lang="ts">
import { computed } from "vue";

import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
const displayName = computed(() => authStore.user?.full_name || "EnduroBuddy User");
</script>

<template>
  <div class="profile-dropdown">
    <div class="profile-dropdown__name">{{ displayName }}</div>
    <a class="profile-dropdown__item" href="/app/profile/complete">Profil</a>
    <a class="profile-dropdown__item profile-dropdown__item--danger" href="/accounts/logout/">Odhlasit se</a>
  </div>
</template>

<style scoped>
.profile-dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  width: 14rem;
  padding: 0.5rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-surface);
  box-shadow: var(--eb-shadow-soft);
}

.profile-dropdown__name {
  padding: 0.625rem 0.75rem 0.75rem;
  color: var(--eb-text-soft);
  font-size: 0.8125rem;
  border-bottom: 1px solid var(--eb-border);
}

.profile-dropdown__item {
  display: block;
  padding: 0.75rem;
  border-radius: var(--eb-radius-sm);
  color: var(--eb-text);
  transition: background-color 150ms ease-out;
}

.profile-dropdown__item:hover {
  background: var(--eb-surface-hover);
}

.profile-dropdown__item--danger {
  color: var(--eb-danger);
}
</style>
