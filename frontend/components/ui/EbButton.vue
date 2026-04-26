<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "ghost" | "danger";
    type?: "button" | "submit";
    disabled?: boolean;
  }>(),
  {
    variant: "primary",
    type: "button",
    disabled: false,
  },
);
</script>

<template>
  <button :type="props.type" class="eb-button" :class="`eb-button--${props.variant}`" :disabled="props.disabled">
    <slot />
  </button>
</template>

<style scoped>
.eb-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--eb-spacing-2);
  min-height: 2.5rem;
  padding: 0.625rem 1rem;
  border-radius: var(--eb-radius-md);
  border: 1px solid transparent;
  font-family: var(--eb-font-display);
  font-size: var(--eb-type-small-size);
  font-weight: 600;
  letter-spacing: 0.02em;
  transition:
    background-color 150ms ease-out,
    border-color 150ms ease-out,
    transform 150ms ease-out;
}

.eb-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.eb-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.eb-button--primary {
  background: var(--eb-lime);
  color: var(--eb-bg);
  box-shadow: var(--eb-glow-lime);
}

.eb-button--secondary {
  background: rgba(56, 189, 248, 0.12);
  color: var(--eb-blue);
  border-color: rgba(56, 189, 248, 0.2);
}

.eb-button--ghost {
  background: transparent;
  color: var(--eb-text-soft);
  border-color: var(--eb-border);
}

.eb-button--ghost:hover:not(:disabled) {
  background: var(--eb-surface-hover);
  color: var(--eb-text);
}

.eb-button--danger {
  background: rgba(244, 63, 94, 0.14);
  color: var(--eb-danger);
  border-color: rgba(244, 63, 94, 0.24);
}
</style>
