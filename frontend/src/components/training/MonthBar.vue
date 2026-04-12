<script setup lang="ts">
import { useI18n } from "@/composables/useI18n";

defineProps<{
  months: Array<{ id: number; value: string; label: string }>;
  activeMonth?: string;
  adding?: boolean;
}>();

const emit = defineEmits<{
  select: [value: string];
  addMonth: [];
}>();

const { t } = useI18n();
</script>

<template>
  <nav class="month-bar">
    <button class="month-bar__add" :disabled="adding" @click="emit('addMonth')">
      <svg width="11" height="11" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
      </svg>
      {{ adding ? t("addMonth.adding") : t("addMonth.button") }}
    </button>

    <div class="month-bar__divider" aria-hidden="true" />

    <div class="month-bar__pills" role="tablist" :aria-label="t('monthBar.label')">
      <button
        v-for="month in months"
        :key="month.id"
        class="month-bar__pill"
        :class="{ 'month-bar__pill--active': month.value === activeMonth }"
        role="tab"
        :aria-selected="month.value === activeMonth"
        @click="emit('select', month.value)"
      >
        {{ month.label }}
      </button>
    </div>
  </nav>
</template>

<style scoped>
.month-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 44px;
  background: rgba(17, 17, 19, 0.92);
  backdrop-filter: blur(12px);
  border-top: 1px solid var(--eb-border);
  padding: 0 1.5rem;
}

.month-bar__add {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 28px;
  padding: 0 12px;
  border-radius: var(--eb-radius-sm);
  border: 1px dashed rgba(200, 255, 0, 0.35);
  background: transparent;
  color: var(--eb-lime);
  font-family: var(--eb-font-body);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 120ms, border-color 120ms, opacity 120ms;
}

.month-bar__add:hover:not(:disabled) {
  background: rgba(200, 255, 0, 0.08);
  border-color: rgba(200, 255, 0, 0.6);
}

.month-bar__add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.month-bar__divider {
  width: 1px;
  height: 20px;
  background: var(--eb-border);
  flex-shrink: 0;
  margin: 0 4px;
}

.month-bar__pills {
  display: flex;
  gap: 2px;
  overflow-x: auto;
  flex: 1;
  scrollbar-width: none;
}

.month-bar__pills::-webkit-scrollbar {
  display: none;
}

.month-bar__pill {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  border-radius: var(--eb-radius-sm);
  border: 1px solid transparent;
  background: transparent;
  color: var(--eb-text-muted);
  font-family: var(--eb-font-body);
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  cursor: pointer;
  white-space: nowrap;
  transition: background 120ms, color 120ms, border-color 120ms;
}

.month-bar__pill:hover:not(.month-bar__pill--active) {
  background: rgba(255, 255, 255, 0.05);
  color: var(--eb-text);
}

.month-bar__pill--active {
  background: rgba(200, 255, 0, 0.08);
  border-color: rgba(200, 255, 0, 0.18);
  color: var(--eb-lime);
  font-family: var(--eb-font-display);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}
</style>
