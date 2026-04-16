<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { CoachAthlete, CoachJoinRequest } from "@/api/coach";
import { fetchCoachCode, fetchJoinRequests, approveJoinRequest, rejectJoinRequest, removeAthlete } from "@/api/coach";
import EbButton from "@/components/ui/EbButton.vue";
import EbModal from "@/components/ui/EbModal.vue";
import EbContextMenu from "@/components/ui/EbContextMenu.vue";
import type { ContextMenuItem } from "@/components/ui/context-menu-types";
import { useI18n } from "@/composables/useI18n";
import { useToastStore } from "@/stores/toasts";

const props = defineProps<{
  athletes: CoachAthlete[];
  open: boolean;
  saving?: boolean;
  startRemoveId?: number | null;
}>();

const emit = defineEmits<{
  close: [];
  autoSave: [athleteIds: number[]];
  toggleHidden: [athleteId: number, hidden: boolean];
  athleteRemoved: [athleteId: number];
  goToDashboard: [];
}>();

const draft = ref<CoachAthlete[]>([]);
const { t } = useI18n();
const toastStore = useToastStore();

type Tab = "order" | "code" | "requests";
const activeTab = ref<Tab>("order");

const coachCode = ref("");
const joinRequests = ref<CoachJoinRequest[]>([]);
const processingRequestId = ref<number | null>(null);

const removeAthleteId = ref<number | null>(null);
const removeConfirmName = ref("");
const isRemoving = ref(false);

// Drag and drop state
const dragSourceIndex = ref<number | null>(null);
const dragOverIndex = ref<number | null>(null);

// Context menu state
const ctxMenu = ref<{
  open: boolean;
  athlete: CoachAthlete | null;
  x: number;
  y: number;
}>({ open: false, athlete: null, x: 0, y: 0 });

watch(
  () => [props.open, props.athletes] as const,
  () => {
    draft.value = props.athletes.map((athlete) => ({ ...athlete }));
  },
  { immediate: true },
);

// When startRemoveId is set, immediately open the confirm dialog for that athlete
watch(
  () => props.startRemoveId,
  (id) => {
    if (id != null) {
      removeAthleteId.value = id;
      removeConfirmName.value = "";
      activeTab.value = "order";
    }
  },
  { immediate: true },
);

watch(activeTab, async (tab) => {
  if (tab === "code" && !coachCode.value) {
    try {
      const data = await fetchCoachCode();
      coachCode.value = data.coach_join_code;
    } catch {
      toastStore.push(t("coachCode.loadError"), "danger");
    }
  }
  if (tab === "requests") {
    try {
      const data = await fetchJoinRequests();
      joinRequests.value = data.requests;
    } catch {
      toastStore.push("Could not load join requests.", "danger");
    }
  }
});

const visibleCount = computed(() => draft.value.filter((athlete) => !athlete.hidden).length);

// --- Drag and drop ---

function onDragStart(e: DragEvent, index: number) {
  dragSourceIndex.value = index;
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", String(index));
  }
}

function onDragOver(e: DragEvent, index: number) {
  e.preventDefault();
  if (e.dataTransfer) e.dataTransfer.dropEffect = "move";
  dragOverIndex.value = index;
}

function onDragLeave(e: DragEvent, el: HTMLElement) {
  if (el.contains(e.relatedTarget as Node)) return;
  dragOverIndex.value = null;
}

function onDrop(e: DragEvent, targetIndex: number) {
  e.preventDefault();
  const sourceIndex = dragSourceIndex.value;
  if (sourceIndex === null || sourceIndex === targetIndex) {
    dragSourceIndex.value = null;
    dragOverIndex.value = null;
    return;
  }
  const next = [...draft.value];
  const [moved] = next.splice(sourceIndex, 1);
  next.splice(targetIndex, 0, moved);
  draft.value = next.map((athlete, i) => ({ ...athlete, sort_order: i + 1 }));
  emit("autoSave", draft.value.map((a) => a.id));
  dragSourceIndex.value = null;
  dragOverIndex.value = null;
}

function onDragEnd() {
  dragSourceIndex.value = null;
  dragOverIndex.value = null;
}

// --- Context menu ---

function openCtxMenu(e: MouseEvent, athlete: CoachAthlete) {
  e.preventDefault();
  ctxMenu.value = { open: true, athlete, x: e.clientX, y: e.clientY };
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
  ctxMenu.value.athlete = null;
  if (!athlete) return;

  if (action === "go") {
    emit("close");
    emit("goToDashboard");
  } else if (action === "hide") {
    emit("toggleHidden", athlete.id, true);
  } else if (action === "show") {
    emit("toggleHidden", athlete.id, false);
  } else if (action === "remove") {
    startRemove(athlete.id);
  }
}

// --- Remove athlete ---

function startRemove(athleteId: number) {
  removeAthleteId.value = athleteId;
  removeConfirmName.value = "";
}

async function confirmRemove() {
  const athleteId = removeAthleteId.value;
  if (!athleteId) return;
  isRemoving.value = true;
  try {
    await removeAthlete(athleteId, removeConfirmName.value);
    emit("athleteRemoved", athleteId);
    draft.value = draft.value.filter((a) => a.id !== athleteId);
    removeAthleteId.value = null;
    removeConfirmName.value = "";
    toastStore.push(t("removeAthlete.success"), "success");
  } catch {
    toastStore.push(t("removeAthlete.error"), "danger");
  } finally {
    isRemoving.value = false;
  }
}

// --- Coach code ---

async function copyCode() {
  try {
    await navigator.clipboard.writeText(coachCode.value);
    toastStore.push(t("coachCode.copied"), "success");
  } catch {
    toastStore.push(t("coachCode.copyError"), "danger");
  }
}

// --- Join requests ---

async function approve(requestId: number) {
  processingRequestId.value = requestId;
  try {
    await approveJoinRequest(requestId);
    joinRequests.value = joinRequests.value.filter((r) => r.id !== requestId);
    toastStore.push(t("joinRequests.approve"), "success");
  } catch {
    toastStore.push(t("joinRequests.approveError"), "danger");
  } finally {
    processingRequestId.value = null;
  }
}

async function reject(requestId: number) {
  processingRequestId.value = requestId;
  try {
    await rejectJoinRequest(requestId);
    joinRequests.value = joinRequests.value.filter((r) => r.id !== requestId);
    toastStore.push(t("joinRequests.reject"), "success");
  } catch {
    toastStore.push(t("joinRequests.rejectError"), "danger");
  } finally {
    processingRequestId.value = null;
  }
}
</script>

<template>
  <EbModal :open="open">
    <div class="athlete-manage">
      <div class="athlete-manage__header">
        <div>
          <div class="athlete-manage__eyebrow">{{ t("coachManage.workspace") }}</div>
          <h2 class="athlete-manage__title">{{ t("coachManage.title") }}</h2>
        </div>
        <EbButton variant="ghost" @click="emit('close')">{{ t("coachManage.close") }}</EbButton>
      </div>

      <div class="athlete-manage__tabs">
        <button
          class="athlete-manage__tab"
          :class="{ 'athlete-manage__tab--active': activeTab === 'order' }"
          type="button"
          @click="activeTab = 'order'"
        >
          {{ t("coachManage.title") }}
        </button>
        <button
          class="athlete-manage__tab"
          :class="{ 'athlete-manage__tab--active': activeTab === 'code' }"
          type="button"
          @click="activeTab = 'code'"
        >
          {{ t("coachCode.tabLabel") }}
        </button>
        <button
          class="athlete-manage__tab"
          :class="{ 'athlete-manage__tab--active': activeTab === 'requests' }"
          type="button"
          @click="activeTab = 'requests'"
        >
          {{ t("joinRequests.tabLabel") }}
        </button>
      </div>

      <!-- Athletes tab -->
      <template v-if="activeTab === 'order'">
        <p class="athlete-manage__text">
          {{ t("coachManage.summary", { count: visibleCount }) }}
        </p>

        <div class="athlete-manage__list">
          <div
            v-for="(athlete, index) in draft"
            :key="athlete.id"
            class="athlete-manage__item"
            :class="{
              'athlete-manage__item--hidden': athlete.hidden,
              'athlete-manage__item--drag-over': dragOverIndex === index,
              'athlete-manage__item--dragging': dragSourceIndex === index,
            }"
            draggable="true"
            @dragstart="onDragStart($event, index)"
            @dragover="onDragOver($event, index)"
            @dragleave="onDragLeave($event, $event.currentTarget as HTMLElement)"
            @drop="onDrop($event, index)"
            @dragend="onDragEnd"
            @contextmenu="openCtxMenu($event, athlete)"
          >
            <div class="athlete-manage__item-row">
              <div class="athlete-manage__drag-handle" aria-hidden="true">⠿</div>

              <div class="athlete-manage__meta">
                <div class="athlete-manage__name">{{ athlete.name }}</div>
                <div class="athlete-manage__detail">
                  <span v-if="athlete.hidden" class="athlete-manage__hidden-badge">{{ t("coachManage.hidden") }}</span>
                </div>
              </div>
              <span v-if="athlete.focus" class="athlete-manage__focus-tag">{{ athlete.focus }}</span>
            </div>

            <!-- Inline remove confirm -->
            <div v-if="removeAthleteId === athlete.id" class="athlete-manage__remove-confirm">
              <p class="athlete-manage__remove-text">{{ t("removeAthlete.confirmText") }}</p>
              <input
                v-model="removeConfirmName"
                class="athlete-manage__remove-input"
                :placeholder="t('removeAthlete.confirmPlaceholder')"
                :disabled="isRemoving"
              />
              <div class="athlete-manage__remove-actions">
                <EbButton variant="ghost" :disabled="isRemoving" @click="removeAthleteId = null">
                  {{ t("coachManage.cancel") }}
                </EbButton>
                <EbButton variant="danger" :disabled="isRemoving" @click="confirmRemove">
                  {{ isRemoving ? t("removeAthlete.confirming") : t("removeAthlete.confirm") }}
                </EbButton>
              </div>
            </div>
          </div>
        </div>

        <div class="athlete-manage__footer">
          <EbButton variant="ghost" :disabled="saving" @click="emit('close')">{{ t("coachManage.cancel") }}</EbButton>
        </div>
      </template>

      <!-- Code tab -->
      <template v-else-if="activeTab === 'code'">
        <div class="athlete-manage__code-section">
          <p class="athlete-manage__text">{{ t("coachCode.tabLabel") }}</p>
          <div class="athlete-manage__code-wrap">
            <code class="athlete-manage__code">{{ coachCode || "..." }}</code>
            <EbButton variant="secondary" :disabled="!coachCode" @click="copyCode">
              {{ t("coachCode.copy") }}
            </EbButton>
          </div>
        </div>
      </template>

      <!-- Requests tab -->
      <template v-else-if="activeTab === 'requests'">
        <div class="athlete-manage__requests">
          <p v-if="joinRequests.length === 0" class="athlete-manage__empty">{{ t("joinRequests.empty") }}</p>
          <div v-for="req in joinRequests" :key="req.id" class="athlete-manage__request-item">
            <div class="athlete-manage__meta">
              <div class="athlete-manage__name">{{ req.athlete_name }}</div>
              <div class="athlete-manage__detail">{{ req.athlete_username }}</div>
            </div>
            <div class="athlete-manage__actions">
              <EbButton
                variant="secondary"
                :disabled="processingRequestId === req.id"
                @click="approve(req.id)"
              >
                {{ processingRequestId === req.id ? t("joinRequests.approving") : t("joinRequests.approve") }}
              </EbButton>
              <EbButton
                variant="ghost"
                :disabled="processingRequestId === req.id"
                @click="reject(req.id)"
              >
                {{ processingRequestId === req.id ? t("joinRequests.rejecting") : t("joinRequests.reject") }}
              </EbButton>
            </div>
          </div>
        </div>
      </template>
    </div>
  </EbModal>

  <!-- Context menu — Teleport to body handled inside EbContextMenu -->
  <EbContextMenu
    :open="ctxMenu.open"
    :items="ctxMenu.athlete ? ctxItems(ctxMenu.athlete) : []"
    :x="ctxMenu.x"
    :y="ctxMenu.y"
    @close="ctxMenu.open = false; ctxMenu.athlete = null"
    @select="onCtxSelect"
  />
</template>

<style scoped>
.athlete-manage {
  display: grid;
  gap: 1rem;
  padding: 1.25rem;
  max-height: 85vh;
  overflow-y: auto;
}

.athlete-manage__header {
  display: flex;
  align-items: flex-start;
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
  margin: 0;
  color: var(--eb-text-soft);
  font-size: 0.875rem;
}

.athlete-manage__tabs {
  display: flex;
  gap: 0.25rem;
  border-bottom: 1px solid var(--eb-border);
  padding-bottom: 0;
}

.athlete-manage__tab {
  padding: 0.5rem 1rem;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--eb-text-muted);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: color 150ms ease-out;
  margin-bottom: -1px;
}

.athlete-manage__tab:hover {
  color: var(--eb-text);
}

.athlete-manage__tab--active {
  border-bottom-color: var(--eb-lime);
  color: var(--eb-text);
}

.athlete-manage__list {
  display: grid;
  gap: 0.75rem;
}

.athlete-manage__item {
  display: flex;
  flex-direction: column;
  padding: 0.9rem 1rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-bg-elevated);
  cursor: grab;
  transition: border-color 150ms ease-out, opacity 150ms ease-out;
}

.athlete-manage__item-row {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.athlete-manage__item:active {
  cursor: grabbing;
}

.athlete-manage__item--drag-over {
  border-color: var(--eb-lime);
}

.athlete-manage__item--dragging {
  opacity: 0.4;
}

.athlete-manage__item--hidden {
  opacity: 0.45;
}

.athlete-manage__item--hidden .athlete-manage__name {
  text-decoration: line-through;
}

.athlete-manage__drag-handle {
  flex-shrink: 0;
  color: var(--eb-text-muted);
  font-size: 1rem;
  line-height: 1.4;
  user-select: none;
  cursor: grab;
}

.athlete-manage__meta {
  flex: 1;
  min-width: 0;
  margin-bottom: 0;
}

.athlete-manage__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.athlete-manage__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
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

.athlete-manage__hidden-badge {
  color: var(--eb-warning);
}

.athlete-manage__focus-tag {
  color: var(--eb-blue);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  flex-shrink: 0;
  margin-left: auto;
}

.athlete-manage__remove-confirm {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--eb-border);
  display: grid;
  gap: 0.5rem;
  width: 100%;
}

.athlete-manage__remove-text {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: 0.875rem;
}

.athlete-manage__remove-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--eb-danger);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  font-size: 0.875rem;
}

.athlete-manage__remove-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.athlete-manage__code-section {
  display: grid;
  gap: 1rem;
  padding: 0.5rem 0;
}

.athlete-manage__code-wrap {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.athlete-manage__code {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-bg);
  color: var(--eb-lime);
  font-family: var(--eb-font-mono);
  font-size: 1.125rem;
  letter-spacing: 0.1em;
}

.athlete-manage__requests {
  display: grid;
  gap: 0.75rem;
}

.athlete-manage__request-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-bg-elevated);
}

.athlete-manage__empty {
  color: var(--eb-text-muted);
  font-size: 0.875rem;
  text-align: center;
  padding: 1rem;
}
</style>
