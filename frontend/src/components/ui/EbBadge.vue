<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    tone?: "planned" | "done" | "missed" | "neutral";
  }>(),
  {
    tone: "neutral",
  },
);
</script>

<template>
  <span class="eb-badge" :class="`eb-badge--${props.tone}`">
    <slot />
  </span>
</template>

<style scoped>
.eb-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 1.75rem;
  padding: 0 0.65rem;
  border-radius: 999px;
  border: 1px solid var(--eb-border);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.eb-badge--planned {
  color: var(--eb-blue);
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.2);
}

.eb-badge--done {
  color: var(--eb-lime);
  background: rgba(200, 255, 0, 0.1);
  border-color: rgba(200, 255, 0, 0.18);
}

.eb-badge--missed {
  color: var(--eb-danger);
  background: rgba(244, 63, 94, 0.1);
  border-color: rgba(244, 63, 94, 0.18);
}

.eb-badge--neutral {
  color: var(--eb-text-soft);
  background: rgba(255, 255, 255, 0.02);
}
</style>
