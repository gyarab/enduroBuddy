<script setup lang="ts">
import { onUnmounted, ref, watch } from "vue";

export type ContextMenuItem = {
  action: string;
  label: string;
  icon?: string;
  variant?: "default" | "danger";
};

const props = defineProps<{
  open: boolean;
  items: ContextMenuItem[];
  x: number;
  y: number;
}>();

const emit = defineEmits<{
  close: [];
  select: [action: string];
}>();

const focusedIndex = ref(0);
const menuEl = ref<HTMLElement | null>(null);

function onKeydown(e: KeyboardEvent) {
  if (!props.open) return;
  if (e.key === "Escape") {
    e.stopPropagation();
    emit("close");
    return;
  }
  if (e.key === "ArrowDown") {
    e.preventDefault();
    focusedIndex.value = (focusedIndex.value + 1) % props.items.length;
  }
  if (e.key === "ArrowUp") {
    e.preventDefault();
    focusedIndex.value = (focusedIndex.value - 1 + props.items.length) % props.items.length;
  }
  if (e.key === "Enter" && props.items[focusedIndex.value]) {
    emit("select", props.items[focusedIndex.value]!.action);
  }
}

function onOutsideMousedown(e: MouseEvent) {
  if (props.open && menuEl.value && !menuEl.value.contains(e.target as Node)) {
    emit("close");
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      focusedIndex.value = 0;
      document.addEventListener("keydown", onKeydown);
      document.addEventListener("mousedown", onOutsideMousedown);
    } else {
      document.removeEventListener("keydown", onKeydown);
      document.removeEventListener("mousedown", onOutsideMousedown);
    }
  },
  { immediate: true },
);

onUnmounted(() => {
  document.removeEventListener("keydown", onKeydown);
  document.removeEventListener("mousedown", onOutsideMousedown);
});
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      ref="menuEl"
      class="eb-ctx"
      :style="{ left: `${x}px`, top: `${y}px` }"
      role="menu"
      aria-label="Athlete actions"
    >
      <button
        v-for="(item, i) in items"
        :key="item.action"
        class="eb-ctx__item"
        :class="[
          `eb-ctx__item--${item.variant ?? 'default'}`,
          { 'eb-ctx__item--focused': i === focusedIndex },
        ]"
        type="button"
        role="menuitem"
        @click="emit('select', item.action)"
        @mouseenter="focusedIndex = i"
      >
        <span v-if="item.icon" class="eb-ctx__icon" aria-hidden="true">{{ item.icon }}</span>
        {{ item.label }}
      </button>
    </div>
  </Teleport>
</template>

<style scoped>
.eb-ctx {
  position: fixed;
  z-index: 500;
  background: #1c1c1f;
  border: 1px solid #3f3f46;
  border-radius: var(--eb-radius-md);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5), 0 2px 6px rgba(0, 0, 0, 0.3);
  min-width: 10rem;
  overflow: hidden;
  padding: 0.25rem 0;
}

.eb-ctx__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.45rem 0.875rem;
  border: 0;
  background: transparent;
  color: var(--eb-text-soft);
  font-size: 0.8125rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: background 100ms;
}

.eb-ctx__item--focused,
.eb-ctx__item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--eb-text);
}

.eb-ctx__item--danger {
  color: var(--eb-danger);
}

.eb-ctx__item--danger.eb-ctx__item--focused,
.eb-ctx__item--danger:hover {
  background: rgba(244, 63, 94, 0.08);
  color: var(--eb-danger);
}

.eb-ctx__icon {
  width: 1rem;
  text-align: center;
  opacity: 0.7;
  font-style: normal;
}
</style>
