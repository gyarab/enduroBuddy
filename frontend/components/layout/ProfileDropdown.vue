<script setup lang="ts">
import { computed, ref } from "vue";

import { useAuthStore } from "@/stores/auth";
import { logoutFromSession } from "@/utils/api/auth";

const emit = defineEmits<{
  openSettings: [];
  openGarmin: [];
}>();

const authStore = useAuthStore();
const { t } = useI18n();
const displayName = computed(() => authStore.user?.full_name || "EnduroBuddy User");
const isLoggingOut = ref(false);

async function handleLogout() {
  if (isLoggingOut.value) return;
  isLoggingOut.value = true;
  try {
    await logoutFromSession();
  } catch {
    // session clear failed — still navigate to login
  } finally {
    authStore.user = null;
    const config = useRuntimeConfig();
    const appHost = config.public.appHost as string;
    const loginUrl = appHost
      ? `https://${appHost.replace(/^app\./, "")}/accounts/login/`
      : "/accounts/login/";
    if (import.meta.client) {
      window.location.href = loginUrl;
    } else {
      await navigateTo(loginUrl, { external: true });
    }
  }
}
</script>

<template>
  <div class="profile-dropdown">
    <div class="profile-dropdown__name">{{ displayName }}</div>
    <button class="profile-dropdown__item" type="button" @click="emit('openSettings')">{{ t("profileDropdown.profile") }}</button>
    <button class="profile-dropdown__item" type="button" @click="emit('openGarmin')">{{ t("profileDropdown.garmin") }}</button>
    <div class="profile-dropdown__divider" />
    <button class="profile-dropdown__item profile-dropdown__item--danger" type="button" :disabled="isLoggingOut" @click="handleLogout">{{ t("profileDropdown.logout") }}</button>
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
  margin-bottom: 0.25rem;
}

.profile-dropdown__item {
  display: block;
  width: 100%;
  padding: 0.75rem;
  border: 0;
  border-radius: var(--eb-radius-sm);
  background: transparent;
  color: var(--eb-text);
  font-size: 0.875rem;
  text-align: left;
  transition: background-color 150ms ease-out;
  cursor: pointer;
}

.profile-dropdown__item:hover {
  background: var(--eb-surface-hover);
}

.profile-dropdown__divider {
  height: 1px;
  margin: 0.25rem 0.5rem;
  background: var(--eb-border);
}

.profile-dropdown__item--danger {
  color: var(--eb-danger);
  margin-top: 0.25rem;
}
</style>
