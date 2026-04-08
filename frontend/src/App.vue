<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";

import AppShell from "@/components/layout/AppShell.vue";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const authStore = useAuthStore();

const shellVariant = computed(() => {
  const variant = route.meta.appVariant;
  return variant === "coach" ? "coach" : "athlete";
});

onMounted(() => {
  if (!authStore.hasBootstrapped) {
    void authStore.initialize();
  }
});
</script>

<template>
  <AppShell :variant="shellVariant">
    <RouterView />
  </AppShell>
</template>
