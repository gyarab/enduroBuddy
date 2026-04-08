<script setup lang="ts">
import { computed } from "vue";

import EbSpinner from "@/components/ui/EbSpinner.vue";
import ToastViewport from "@/components/ui/ToastViewport.vue";
import TopNav from "@/components/layout/TopNav.vue";
import { useAuthStore } from "@/stores/auth";

const props = defineProps<{
  variant: "athlete" | "coach";
}>();

const authStore = useAuthStore();
const shellClass = computed(() => `app-shell--${props.variant}`);
</script>

<template>
  <div class="app-shell" :class="shellClass">
    <TopNav :variant="props.variant" />
    <ToastViewport />

    <main class="app-shell__main">
      <div v-if="authStore.isLoading && !authStore.user" class="app-shell__loading">
        <EbSpinner />
        <span>Nacitani workspace...</span>
      </div>

      <div v-else class="app-shell__content">
        <slot />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: transparent;
}

.app-shell__main {
  padding: 1.5rem 1rem 2rem;
}

.app-shell__content,
.app-shell__loading {
  max-width: var(--eb-shell-max-width);
  margin: 0 auto;
}

.app-shell__loading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-height: calc(100vh - var(--eb-topnav-height) - 5rem);
  color: var(--eb-text-soft);
}

@media (min-width: 768px) {
  .app-shell__main {
    padding: 1.5rem 1.5rem 2.5rem;
  }
}
</style>
