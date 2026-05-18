<script setup lang="ts">
import { ref } from "vue";

import type { CoachAthlete } from "~/utils/api/coach";
import EbContextMenu from "@/components/ui/EbContextMenu.vue";
import type { ContextMenuItem } from "@/components/ui/context-menu-types";

const props = defineProps<{
  athletes: CoachAthlete[];
  isManageOpen?: boolean;
}>();

const emit = defineEmits<{
  select: [athleteId: number];
  "open-manage": [];
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
        <span class="coach-sidebar__dot" :class="{ 'coach-sidebar__dot--active': athlete.selected }" />
        <span class="coach-sidebar__name" :title="athlete.name">{{ athlete.name }}</span>
        <span v-if="athlete.focus" class="coach-sidebar__focus">{{ athlete.focus }}</span>
      </button>
    </div>

    <div class="coach-sidebar__footer">
      <button
        class="coach-sidebar__manage-btn"
        :class="{ 'coach-sidebar__manage-btn--active': isManageOpen }"
        type="button"
        @click="emit('open-manage')"
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
        </svg>
        {{ t("sidebar.manageAthletes") }}
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
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #111113;
  overflow-y: auto;
}

.coach-sidebar__header {
  padding: 14px 16px 10px;
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #52525b;
  border-bottom: 1px solid #1e1e22;
  flex-shrink: 0;
}

.coach-sidebar__list {
  display: flex;
  flex-direction: column;
}

.coach-sidebar__item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  padding: 10px 16px;
  border: 0;
  border-left: 2px solid transparent;
  background: transparent;
  color: #71717a;
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-size: 13px;
  font-weight: 600;
  text-align: left;
  cursor: pointer;
  transition: background 120ms, color 120ms;
}

.coach-sidebar__item:hover {
  background: rgba(255, 255, 255, 0.03);
  color: #a1a1aa;
}

.coach-sidebar__item:focus-visible {
  outline: 2px solid var(--eb-lime);
  outline-offset: -2px;
}

.coach-sidebar__item--active {
  border-left-color: var(--eb-lime);
  background: rgba(200, 255, 0, 0.04);
  color: #fafafa;
}

.coach-sidebar__item--hidden {
  opacity: 0.45;
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
  color: #3f3f46;
  opacity: 0;
  transition: opacity 150ms;
  cursor: grab;
  flex-shrink: 0;
}

.coach-sidebar__item:hover .coach-sidebar__drag-handle {
  opacity: 1;
}

/* Dot — outlined by default, filled when active */
.coach-sidebar__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1.5px solid #3f3f46;
  background: transparent;
  flex-shrink: 0;
}

.coach-sidebar__dot--active {
  background: var(--eb-lime);
  border-color: var(--eb-lime);
}

.coach-sidebar__name {
  flex: 1;
  min-width: 0;
  word-break: break-word;
  line-height: 1.3;
}

.coach-sidebar__focus {
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.08);
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 4px;
  padding: 2px 5px;
  flex-shrink: 0;
}

.coach-sidebar__footer {
  margin-top: auto;
  padding: 12px 16px;
  border-top: 1px solid #1e1e22;
  flex-shrink: 0;
}

.coach-sidebar__manage-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  height: 32px;
  border: 1px solid #3f3f46;
  border-radius: 7px;
  background: transparent;
  color: #71717a;
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: border-color 150ms, color 150ms, background 150ms;
}

.coach-sidebar__manage-btn:hover,
.coach-sidebar__manage-btn--active {
  border-color: rgba(200, 255, 0, 0.4);
  color: var(--eb-lime, #c8ff00);
  background: rgba(200, 255, 0, 0.06);
}
</style>
