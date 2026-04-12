<script setup lang="ts">
defineProps<{
  open: boolean;
}>();
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="eb-modal">
      <div class="eb-modal__overlay" />
      <div class="eb-modal__panel">
        <slot />
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.eb-modal {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: grid;
  place-items: center;
  padding: var(--eb-spacing-4);
}

.eb-modal__overlay {
  position: absolute;
  inset: 0;
  background: rgba(9, 9, 11, 0.78);
  backdrop-filter: blur(14px);
}

.eb-modal__panel {
  position: relative;
  width: min(100%, 40rem);
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-lg);
  background: var(--eb-surface);
  box-shadow: var(--eb-shadow-soft);
}
</style>
