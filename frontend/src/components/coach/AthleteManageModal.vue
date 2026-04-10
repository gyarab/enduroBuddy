<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { CoachAthlete, CoachJoinRequest } from "@/api/coach";
import { fetchCoachCode, fetchJoinRequests, approveJoinRequest, rejectJoinRequest, removeAthlete } from "@/api/coach";
import EbButton from "@/components/ui/EbButton.vue";
import EbModal from "@/components/ui/EbModal.vue";
import { useI18n } from "@/composables/useI18n";
import { useToastStore } from "@/stores/toasts";

const props = defineProps<{
  athletes: CoachAthlete[];
  open: boolean;
  saving?: boolean;
}>();

const emit = defineEmits<{
  close: [];
  save: [athleteIds: number[]];
  toggleHidden: [athleteId: number, hidden: boolean];
  athleteRemoved: [athleteId: number];
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

watch(
  () => [props.open, props.athletes] as const,
  () => {
    draft.value = props.athletes.map((athlete) => ({ ...athlete }));
  },
  { immediate: true },
);

watch(activeTab, async (tab) => {
  if (tab === "code" && !coachCode.value) {
    try {
      const data = await fetchCoachCode();
      coachCode.value = data.coach_join_code;
    } catch {
      toastStore.push("Could not load coach code.", "danger");
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

async function copyCode() {
  try {
    await navigator.clipboard.writeText(coachCode.value);
    toastStore.push(t("coachCode.copied"), "success");
  } catch {
    toastStore.push("Could not copy.", "danger");
  }
}

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

function startRemove(athleteId: number) {
  removeAthleteId.value = athleteId;
  removeConfirmName.value = "";
}

async function confirmRemove() {
  if (!removeAthleteId.value) return;
  isRemoving.value = true;
  try {
    await removeAthlete(removeAthleteId.value, removeConfirmName.value);
    emit("athleteRemoved", removeAthleteId.value);
    draft.value = draft.value.filter((a) => a.id !== removeAthleteId.value);
    removeAthleteId.value = null;
    removeConfirmName.value = "";
    toastStore.push("Athlete removed.", "success");
  } catch {
    toastStore.push(t("removeAthlete.error"), "danger");
  } finally {
    isRemoving.value = false;
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

      <!-- Order tab -->
      <template v-if="activeTab === 'order'">
        <p class="athlete-manage__text">
          {{ t("coachManage.summary", { count: visibleCount }) }}
        </p>

        <div class="athlete-manage__list">
          <div v-for="(athlete, index) in draft" :key="athlete.id" class="athlete-manage__item">
            <div class="athlete-manage__meta">
              <div class="athlete-manage__name">{{ athlete.name }}</div>
              <div class="athlete-manage__detail">
                <span v-if="athlete.focus">{{ athlete.focus }}</span>
                <span v-else>{{ t("coachManage.noFocus") }}</span>
                <span v-if="athlete.hidden" class="athlete-manage__hidden">{{ t("coachManage.hidden") }}</span>
              </div>
            </div>

            <div class="athlete-manage__actions">
              <EbButton
                variant="secondary"
                :disabled="saving"
                @click="emit('toggleHidden', athlete.id, !athlete.hidden)"
              >
                {{ athlete.hidden ? t("coachManage.show") : t("coachManage.hide") }}
              </EbButton>
              <EbButton variant="ghost" :disabled="index === 0 || saving" @click="moveItem(index, -1)">{{ t("coachManage.up") }}</EbButton>
              <EbButton
                variant="ghost"
                :disabled="index === draft.length - 1 || saving"
                @click="moveItem(index, 1)"
              >
                {{ t("coachManage.down") }}
              </EbButton>
              <EbButton variant="ghost" class="athlete-manage__remove-btn" @click="startRemove(athlete.id)">
                {{ t("removeAthlete.button") }}
              </EbButton>
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
          <EbButton :disabled="saving" @click="save">{{ saving ? t("coachManage.saving") : t("coachManage.saveOrder") }}</EbButton>
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
  padding: 0.9rem 1rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: var(--eb-bg-elevated);
}

.athlete-manage__meta {
  margin-bottom: 0.5rem;
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
  justify-content: space-between;
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

.athlete-manage__hidden {
  color: var(--eb-warning);
}

.athlete-manage__remove-btn {
  color: var(--eb-danger);
}

.athlete-manage__remove-confirm {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--eb-border);
  display: grid;
  gap: 0.5rem;
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
