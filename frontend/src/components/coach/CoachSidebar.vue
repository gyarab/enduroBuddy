<script setup lang="ts">
import { ref } from "vue";

import type { CoachAthlete } from "@/api/coach";
import EbContextMenu from "@/components/ui/EbContextMenu.vue";
import type { ContextMenuItem } from "@/components/ui/context-menu-types";
import { useI18n } from "@/composables/useI18n";

const props = defineProps<{
  athletes: CoachAthlete[];
}>();

const emit = defineEmits<{
  select: [athleteId: number];
  reorder: [athleteIds: number[]];
  toggleHidden: [athleteId: number, hidden: boolean];
  remove: [athleteId: number];
  goToDashboard: [];
}>();

const { t } = useI18n();

// Drag state
const draggedIndex = ref<number | null>(null);
const dragOverIndex = ref<number | null>(null);

function onDragStart(index: number) {
  draggedIndex.value = index;
}

function onDragOver(index: number) {
  dragOverIndex.value = index;
}

function onDragLeave(e: DragEvent) {
  const el = e.currentTarget as HTMLElement;
  if (el.contains(e.relatedTarget as Node)) return;
  dragOverIndex.value = null;
}

function onDrop(index: number) {
  if (draggedIndex.value === null || draggedIndex.value === index) {
    draggedIndex.value = null;
    dragOverIndex.value = null;
    return;
  }
  const reordered = [...props.athletes];
  const [moved] = reordered.splice(draggedIndex.value, 1);
  reordered.splice(index, 0, moved!);
  draggedIndex.value = null;
  dragOverIndex.value = null;
  emit("reorder", reordered.map((a) => a.id));
}

function onDragEnd() {
  draggedIndex.value = null;
  dragOverIndex.value = null;
}

// Keyboard navigation
const listEl = ref<HTMLElement | null>(null);

function onKeydown(e: KeyboardEvent, index: number) {
  const items = listEl.value?.querySelectorAll<HTMLElement>(".coach-sidebar__item");
  if (!items) return;
  if (e.key === "ArrowDown") {
    e.preventDefault();
    items[index + 1]?.focus();
  }
  if (e.key === "ArrowUp") {
    e.preventDefault();
    items[index - 1]?.focus();
  }
  if (e.key === "Enter") {
    e.preventDefault();
    emit("select", props.athletes[index]!.id);
  }
}

// Context menu
const ctxMenu = ref<{ open: boolean; x: number; y: number; athlete: CoachAthlete | null }>({
  open: false,
  x: 0,
  y: 0,
  athlete: null,
});

function openCtxMenu(e: MouseEvent, athlete: CoachAthlete) {
  e.preventDefault();
  const y = e.clientY + 160 > window.innerHeight ? e.clientY - 160 : e.clientY;
  ctxMenu.value = { open: true, x: e.clientX, y, athlete };
}

function ctxItems(athlete: CoachAthlete): ContextMenuItem[] {
  return [
    { action: "go", label: t("athleteCtx.goToDashboard"), icon: "→" },
    {
      action: athlete.hidden ? "show" : "hide",
      label: athlete.hidden ? t("athleteCtx.show") : t("athleteCtx.hide"),
      icon: athlete.hidden ? "●" : "○",
    },
    { action: "remove", label: t("athleteCtx.remove"), icon: "✕", variant: "danger" },
  ];
}

function onCtxSelect(action: string) {
  const athlete = ctxMenu.value.athlete;
  ctxMenu.value.open = false;
  if (!athlete) return;
  if (action === "go") emit("goToDashboard");
  if (action === "hide") emit("toggleHidden", athlete.id, true);
  if (action === "show") emit("toggleHidden", athlete.id, false);
  if (action === "remove") emit("remove", athlete.id);
}
</script>

<template>
  <aside class="coach-sidebar">
    <div class="coach-sidebar__header">{{ t("sidebar.athletesHeading") }}</div>
    <div ref="listEl" class="coach-sidebar__list">
      <button
        v-for="(athlete, index) in athletes"
        :key="athlete.id"
        class="coach-sidebar__item"
        :class="{
          'coach-sidebar__item--active': athlete.selected,
          'coach-sidebar__item--hidden': athlete.hidden,
          'coach-sidebar__item--drag-over': dragOverIndex === index,
          'coach-sidebar__item--dragging': draggedIndex === index,
        }"
        type="button"
        :draggable="true"
        @click="emit('select', athlete.id)"
        @contextmenu="openCtxMenu($event, athlete)"
        @dragstart="onDragStart(index)"
        @dragover.prevent="onDragOver(index)"
        @dragleave="onDragLeave($event)"
        @drop.prevent="onDrop(index)"
        @dragend="onDragEnd"
        @keydown="onKeydown($event, index)"
      >
        <span class="coach-sidebar__drag-handle" aria-hidden="true">⠿</span>
        <span class="coach-sidebar__dot" :class="{ 'coach-sidebar__dot--muted': !athlete.selected }" />
        <span class="coach-sidebar__name" :title="athlete.name">{{ athlete.name }}</span>
        <span v-if="athlete.focus" class="coach-sidebar__focus">{{ athlete.focus }}</span>
      </button>
    </div>

    <EbContextMenu
      :open="ctxMenu.open"
      :items="ctxMenu.athlete ? ctxItems(ctxMenu.athlete) : []"
      :x="ctxMenu.x"
      :y="ctxMenu.y"
      :label="t('athleteCtx.goToDashboard')"
      @close="ctxMenu.open = false; ctxMenu.athlete = null"
      @select="onCtxSelect"
    />
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
  cursor: pointer;
}

.coach-sidebar__item:hover {
  background: var(--eb-surface-hover);
  color: var(--eb-text);
}

.coach-sidebar__item:focus-visible {
  outline: 2px solid var(--eb-lime);
  outline-offset: -2px;
}

.coach-sidebar__item--active {
  border-left-color: var(--eb-lime);
  background: rgba(200, 255, 0, 0.06);
  color: var(--eb-text);
}

.coach-sidebar__item--hidden {
  opacity: 0.4;
}

.coach-sidebar__item--hidden .coach-sidebar__name {
  text-decoration: line-through;
}

.coach-sidebar__item--drag-over {
  border-top: 2px solid var(--eb-lime);
}

.coach-sidebar__item--dragging {
  opacity: 0.4;
}

.coach-sidebar__drag-handle {
  font-size: 0.75rem;
  color: var(--eb-border);
  opacity: 0;
  transition: opacity 150ms;
  cursor: grab;
  flex-shrink: 0;
}

.coach-sidebar__item:hover .coach-sidebar__drag-handle {
  opacity: 1;
}

.coach-sidebar__dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 999px;
  background: var(--eb-lime);
  flex-shrink: 0;
}

.coach-sidebar__dot--muted {
  background: var(--eb-border);
}

.coach-sidebar__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.coach-sidebar__focus {
  color: var(--eb-blue);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  flex-shrink: 0;
}
</style>
