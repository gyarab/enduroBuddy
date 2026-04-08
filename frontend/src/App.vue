<script setup lang="ts">
import { computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";

import AppShell from "@/components/layout/AppShell.vue";
import { useAuthStore } from "@/stores/auth";
import { useNotificationsStore } from "@/stores/notifications";

const route = useRoute();
const authStore = useAuthStore();
const notificationsStore = useNotificationsStore();

const shellVariant = computed(() => {
  const variant = route.meta.appVariant;
  return variant === "coach" ? "coach" : "athlete";
});

onMounted(() => {
  if (!authStore.hasBootstrapped) {
    void authStore.initialize();
  }
});

watch(
  () => authStore.user?.id,
  (userId) => {
    if (userId) {
      notificationsStore.initialize();
    }
  },
  { immediate: true },
);
</script>

<template>
  <AppShell :variant="shellVariant">
    <RouterView />
  </AppShell>
</template>
