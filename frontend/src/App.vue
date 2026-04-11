<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";

import AppShell from "@/components/layout/AppShell.vue";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";

const route = useRoute();
const authStore = useAuthStore();
const notificationsStore = useNotificationsStore();
const usesAppShell = computed(() => !["auth", "auth-preview"].includes(String(route.meta.layout || "")));

const shellVariant = computed(() => {
  const variant = route.meta.appVariant;
  return variant === "coach" ? "coach" : "athlete";
});

onMounted(() => {
  if (usesAppShell.value && !authStore.hasBootstrapped) {
    void authStore.initialize();
  }
});

watch(
  () => [usesAppShell.value, authStore.user?.id] as const,
  ([shouldUseAppShell, userId]) => {
    if (shouldUseAppShell && !authStore.hasBootstrapped) {
      void authStore.initialize();
    }

    if (shouldUseAppShell && userId) {
      notificationsStore.initialize();
    }
  },
  { immediate: true },
);
</script>

<template>
  <RouterView v-if="!usesAppShell" />

  <AppShell v-else :variant="shellVariant">
    <RouterView />
  </AppShell>
</template>
