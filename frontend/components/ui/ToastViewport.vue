<script setup lang="ts">
import EbToast from "@/components/ui/EbToast.vue";
import { useToastStore } from "@/stores/toasts";

const toastStore = useToastStore();
</script>

<template>
  <div class="toast-viewport" aria-live="polite" aria-atomic="true">
    <EbToast
      v-for="toast in toastStore.items"
      :key="toast.id"
      class="toast-viewport__item"
      :class="`toast-viewport__item--${toast.tone}`"
    >
      <div class="toast-viewport__content">
        <span>{{ toast.message }}</span>
        <button class="toast-viewport__close" type="button" @click="toastStore.remove(toast.id)">Close</button>
      </div>
    </EbToast>
  </div>
</template>

<style scoped>
.toast-viewport {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 220;
  display: grid;
  gap: 0.75rem;
  width: min(22rem, calc(100vw - 2rem));
}

.toast-viewport__item--success {
  border-color: rgba(200, 255, 0, 0.22);
}

.toast-viewport__item--warning {
  border-color: rgba(245, 158, 11, 0.28);
}

.toast-viewport__item--danger {
  border-color: rgba(244, 63, 94, 0.28);
}

.toast-viewport__content {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.toast-viewport__close {
  border: 0;
  background: transparent;
  color: var(--eb-text-muted);
}
</style>
