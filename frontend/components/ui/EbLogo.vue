<script setup lang="ts">
withDefaults(defineProps<{
  variant?: "full" | "compact" | "mark"
  size?: "sm" | "md" | "lg"
}>(), {
  variant: "full",
  size: "md",
})
</script>

<template>
  <span class="eb-logo" :class="[`eb-logo--${size}`]">
    <span class="eb-logo__mark" aria-hidden="true">
      <span></span>
      <span></span>
      <span></span>
    </span>
    <span v-if="variant === 'full'" class="eb-logo__wordmark">EnduroBuddy</span>
    <span v-else-if="variant === 'compact'" class="eb-logo__wordmark">EB</span>
  </span>
</template>

<style scoped>
.eb-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  font-family: var(--eb-font-display);
  font-weight: 700;
  color: var(--eb-text);
  line-height: 1;
  user-select: none;
}

.eb-logo--sm  { font-size: 0.875rem; }
.eb-logo--md  { font-size: 1.0625rem; }
.eb-logo--lg  { font-size: 1.375rem; }

.eb-logo__mark {
  display: inline-flex;
  align-items: flex-end;
  gap: 0.2rem;
  transform: skewX(-6deg);
}

.eb-logo--sm  .eb-logo__mark { height: 0.9rem; }
.eb-logo--md  .eb-logo__mark { height: 1.15rem; }
.eb-logo--lg  .eb-logo__mark { height: 1.5rem; }

.eb-logo__mark span {
  width: 0.3125rem;
  border-radius: 0.15rem;
  background: var(--eb-lime);
  box-shadow: 0 0 10px rgba(200, 255, 0, 0.20);
}

.eb-logo--sm .eb-logo__mark span { width: 0.25rem; }
.eb-logo--lg .eb-logo__mark span { width: 0.375rem; }

.eb-logo__mark span:nth-child(1) { height: 38%; opacity: 0.35; }
.eb-logo__mark span:nth-child(2) { height: 65%; opacity: 0.65; }
.eb-logo__mark span:nth-child(3) { height: 100%; }
</style>
