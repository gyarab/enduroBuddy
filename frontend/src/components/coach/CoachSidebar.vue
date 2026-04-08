<script setup lang="ts">
import type { CoachAthlete } from "@/api/coach";

defineProps<{
  athletes: CoachAthlete[];
}>();

const emit = defineEmits<{
  select: [athleteId: number];
}>();
</script>

<template>
  <aside class="coach-sidebar">
    <div class="coach-sidebar__header">Athletes</div>
    <div class="coach-sidebar__list">
      <button
        v-for="athlete in athletes"
        :key="athlete.id"
        class="coach-sidebar__item"
        :class="{ 'coach-sidebar__item--active': athlete.selected }"
        type="button"
        @click="emit('select', athlete.id)"
      >
        <span class="coach-sidebar__dot" :class="{ 'coach-sidebar__dot--muted': !athlete.selected }" />
        <span class="coach-sidebar__name">{{ athlete.name }}</span>
        <span v-if="athlete.focus" class="coach-sidebar__focus">{{ athlete.focus }}</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.coach-sidebar {
  padding: 1rem 0;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-lg);
  background: var(--eb-surface);
  box-shadow: var(--eb-shadow-soft);
}

.coach-sidebar__header {
  padding: 0 1rem 0.75rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.coach-sidebar__list {
  display: grid;
}

.coach-sidebar__item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.875rem 1rem;
  border: 0;
  border-left: 2px solid transparent;
  background: transparent;
  color: var(--eb-text-soft);
  text-align: left;
}

.coach-sidebar__item:hover {
  background: var(--eb-surface-hover);
  color: var(--eb-text);
}

.coach-sidebar__item--active {
  border-left-color: var(--eb-lime);
  background: rgba(200, 255, 0, 0.06);
  color: var(--eb-text);
}

.coach-sidebar__dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 999px;
  background: var(--eb-lime);
}

.coach-sidebar__dot--muted {
  background: var(--eb-border);
}

.coach-sidebar__name {
  flex: 1;
}

.coach-sidebar__focus {
  color: var(--eb-blue);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
</style>
