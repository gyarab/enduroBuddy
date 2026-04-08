<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { CoachAthlete } from "@/api/coach";
import EbButton from "@/components/ui/EbButton.vue";
import EbModal from "@/components/ui/EbModal.vue";

const props = defineProps<{
  athletes: CoachAthlete[];
  open: boolean;
  saving?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [athleteIds: number[]];
  toggleHidden: [athleteId: number, hidden: boolean];
}>();

const draft = ref<CoachAthlete[]>([]);

watch(
  () => [props.open, props.athletes] as const,
  () => {
    draft.value = props.athletes.map((athlete) => ({ ...athlete }));
  },
  { immediate: true },
);

const visibleCount = computed(() => draft.value.filter((athlete) => !athlete.hidden).length);

function moveItem(index: number, direction: -1 | 1) {
  const targetIndex = index + direction;
  if (targetIndex < 0 || targetIndex >= draft.value.length) {
    return;
  }
  const next = [...draft.value];
  const [moved] = next.splice(index, 1);
  next.splice(targetIndex, 0, moved);
  draft.value = next.map((athlete, orderIndex) => ({
    ...athlete,
    sort_order: orderIndex + 1,
  }));
}

function save() {
  emit("save", draft.value.map((athlete) => athlete.id));
}
</script>

<template>
  <EbModal :open="open">
    <div class="athlete-manage">
      <div class="athlete-manage__header">
        <div>
          <div class="athlete-manage__eyebrow">Coach workspace</div>
          <h2 class="athlete-manage__title">Manage athlete order</h2>
          <p class="athlete-manage__text">
            {{ visibleCount }} visible athletes in sidebar. Hidden athletes stay in the list so their order is preserved.
          </p>
        </div>

        <EbButton variant="ghost" @click="emit('close')">Close</EbButton>
      </div>

      <div class="athlete-manage__list">
        <div v-for="(athlete, index) in draft" :key="athlete.id" class="athlete-manage__item">
          <div class="athlete-manage__meta">
            <div class="athlete-manage__name">{{ athlete.name }}</div>
            <div class="athlete-manage__detail">
              <span v-if="athlete.focus">{{ athlete.focus }}</span>
              <span v-else>No focus</span>
              <span v-if="athlete.hidden" class="athlete-manage__hidden">Hidden</span>
            </div>
          </div>

          <div class="athlete-manage__actions">
            <EbButton
              variant="secondary"
              :disabled="saving"
              @click="emit('toggleHidden', athlete.id, !athlete.hidden)"
            >
              {{ athlete.hidden ? "Show" : "Hide" }}
            </EbButton>
            <EbButton variant="ghost" :disabled="index === 0 || saving" @click="moveItem(index, -1)">Up</EbButton>
            <EbButton
              variant="ghost"
              :disabled="index === draft.length - 1 || saving"
              @click="moveItem(index, 1)"
            >
              Down
            </EbButton>
          </div>
        </div>
      </div>

      <div class="athlete-manage__footer">
        <EbButton variant="ghost" :disabled="saving" @click="emit('close')">Cancel</EbButton>
        <EbButton :disabled="saving" @click="save">{{ saving ? "Saving..." : "Save order" }}</EbButton>
      </div>
    </div>
  </EbModal>
</template>

<style scoped>
.athlete-manage {
  display: grid;
  gap: 1rem;
  padding: 1.25rem;
}

.athlete-manage__header,
.athlete-manage__footer,
.athlete-manage__item,
.athlete-manage__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.athlete-manage__eyebrow {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.athlete-manage__title {
  margin: 0.5rem 0 0;
  font-family: var(--eb-font-display);
  font-size: 1.35rem;
}

.athlete-manage__text {
  margin: 0.5rem 0 0;
  color: var(--eb-text-soft);
  font-size: 0.875rem;
}

.athlete-manage__list {
  display: grid;
  gap: 0.75rem;
}

.athlete-manage__item {
  padding: 0.9rem 1rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-bg-elevated);
}

.athlete-manage__name {
  font-weight: 600;
}

.athlete-manage__detail {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.25rem;
  color: var(--eb-text-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.athlete-manage__hidden {
  color: var(--eb-warning);
}

@media (max-width: 767px) {
  .athlete-manage__header,
  .athlete-manage__footer,
  .athlete-manage__item {
    display: grid;
  }

.athlete-manage__actions {
  justify-content: start;
}
}
</style>
