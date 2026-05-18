<script setup lang="ts">
import { ref, watch, computed } from "vue";

import type { CoachAthlete, CoachJoinRequest } from "~/utils/api/coach";
import {
  fetchCoachCode,
  fetchJoinRequests,
  approveJoinRequest,
  rejectJoinRequest,
  removeAthlete,
} from "~/utils/api/coach";
import { useToastStore } from "@/stores/toasts";

const props = defineProps<{
  open: boolean;
  athletes: CoachAthlete[];
}>();

const emit = defineEmits<{
  close: [];
  toggleHidden: [athleteId: number, hidden: boolean];
  athleteRemoved: [athleteId: number];
  goToDashboard: [];
}>();

const { t } = useI18n();
const toastStore = useToastStore();

type Section = "athletes" | "invite" | "requests";
const activeSection = ref<Section>("athletes");

const coachCode = ref("");
const joinRequests = ref<CoachJoinRequest[]>([]);
const processingRequestId = ref<number | null>(null);
const removeAthleteId = ref<number | null>(null);
const removeAthleteName = ref("");
const removeConfirmName = ref("");
const isRemoving = ref(false);

const visibleCount = computed(() => props.athletes.filter((a) => !a.hidden).length);
const totalCount = computed(() => props.athletes.length);

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    try {
      const data = await fetchJoinRequests();
      joinRequests.value = data.requests;
    } catch {
      // silently ignore — badge simply won't show
    }
  }
);

watch(activeSection, async (section) => {
  if (section === "invite" && !coachCode.value) {
    try {
      const data = await fetchCoachCode();
      coachCode.value = data.coach_join_code;
    } catch {
      toastStore.push(t("coachCode.loadError"), "danger");
    }
  }
  if (section === "requests") {
    try {
      const data = await fetchJoinRequests();
      joinRequests.value = data.requests;
    } catch {
      toastStore.push("Could not load join requests.", "danger");
    }
  }
});

function startRemove(athleteId: number, athleteName: string) {
  removeAthleteId.value = athleteId;
  removeAthleteName.value = athleteName;
  removeConfirmName.value = "";
}

async function confirmRemove() {
  const athleteId = removeAthleteId.value;
  if (!athleteId) return;
  isRemoving.value = true;
  try {
    await removeAthlete(athleteId, removeConfirmName.value);
    emit("athleteRemoved", athleteId);
    removeAthleteId.value = null;
    removeConfirmName.value = "";
    toastStore.push(t("removeAthlete.success"), "success");
  } catch {
    toastStore.push(t("removeAthlete.error"), "danger");
  } finally {
    isRemoving.value = false;
  }
}

async function copyCode() {
  try {
    await navigator.clipboard.writeText(coachCode.value);
    toastStore.push(t("coachCode.copied"), "success");
  } catch {
    toastStore.push(t("coachCode.copyError"), "danger");
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
</script>

<template>
  <aside class="manage-panel" :class="{ 'manage-panel--open': open }" aria-label="Manage athletes panel">
    <!-- Header -->
    <div class="manage-panel__header">
      <div>
        <div class="manage-panel__title">{{ t("managePanel.title") }}</div>
        <div class="manage-panel__summary">
          {{ t("managePanel.summary", { total: totalCount, active: visibleCount }) }}
        </div>
      </div>
      <button class="manage-panel__close" type="button" :aria-label="t('legend.close')" @click="emit('close')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <!-- Two-column body -->
    <div class="manage-panel__body">
      <!-- Left vertical menu -->
      <nav class="manage-panel__menu">
        <button
          class="manage-panel__menu-item"
          :class="{ 'manage-panel__menu-item--active': activeSection === 'athletes' }"
          type="button"
          @click="activeSection = 'athletes'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <span>{{ t("managePanel.athletes") }}</span>
        </button>

        <button
          class="manage-panel__menu-item"
          :class="{ 'manage-panel__menu-item--active': activeSection === 'invite' }"
          type="button"
          @click="activeSection = 'invite'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
          </svg>
          <span>{{ t("managePanel.invite") }}</span>
        </button>

        <button
          class="manage-panel__menu-item"
          :class="{ 'manage-panel__menu-item--active': activeSection === 'requests' }"
          type="button"
          @click="activeSection = 'requests'"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
          </svg>
          <span>{{ t("managePanel.requests") }}</span>
          <span v-if="joinRequests.length > 0" class="manage-panel__badge">{{ joinRequests.length }}</span>
        </button>
      </nav>

      <!-- Right content -->
      <div class="manage-panel__content">
        <!-- Athletes section -->
        <div v-if="activeSection === 'athletes'" class="manage-content--athletes">
          <div class="manage-panel__athlete-list">
            <div
              v-for="athlete in athletes"
              :key="athlete.id"
              class="manage-panel__athlete-row"
              :class="{ 'manage-panel__athlete-row--hidden': athlete.hidden }"
            >
              <span class="manage-panel__dot" :class="{ 'manage-panel__dot--muted': athlete.hidden }" />
              <span class="manage-panel__athlete-name">{{ athlete.name }}</span>
              <span v-if="athlete.focus" class="manage-panel__focus-tag">{{ athlete.focus }}</span>

              <div class="manage-panel__row-actions">
                <button
                  class="manage-panel__icon-btn"
                  type="button"
                  :title="athlete.hidden ? t('athleteCtx.show') : t('athleteCtx.hide')"
                  @click="emit('toggleHidden', athlete.id, !athlete.hidden)"
                >
                  <svg v-if="athlete.hidden" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                  </svg>
                  <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                </button>
                <button
                  class="manage-panel__icon-btn"
                  type="button"
                  :title="t('athleteCtx.switchToDashboard')"
                  @click="emit('goToDashboard')"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M8 3 4 7l4 4"/><path d="M4 7h16"/>
                    <path d="M16 21l4-4-4-4"/><path d="M20 17H4"/>
                  </svg>
                </button>
                <button
                  class="manage-panel__icon-btn manage-panel__icon-btn--danger"
                  type="button"
                  :title="t('removeAthlete.button')"
                  @click="startRemove(athlete.id, athlete.name)"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/>
                    <path d="M10 11v6m4-6v6"/><path d="M9 6V4h6v2"/>
                  </svg>
                </button>
              </div>

              <!-- Inline remove confirm -->
              <div v-if="removeAthleteId === athlete.id" class="manage-panel__remove-confirm">
                <p class="manage-panel__remove-text">{{ t("removeAthlete.confirmText") }}</p>
                <input
                  v-model="removeConfirmName"
                  class="manage-panel__remove-input"
                  :placeholder="t('removeAthlete.confirmPlaceholder')"
                  :disabled="isRemoving"
                />
                <div class="manage-panel__remove-actions">
                  <button class="manage-panel__btn manage-panel__btn--ghost" type="button" :disabled="isRemoving" @click="removeAthleteId = null">
                    {{ t("coachManage.cancel") }}
                  </button>
                  <button class="manage-panel__btn manage-panel__btn--danger" type="button" :disabled="isRemoving || removeConfirmName !== removeAthleteName" @click="confirmRemove">
                    {{ isRemoving ? t("removeAthlete.confirming") : t("removeAthlete.confirm") }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Invite section -->
        <div v-else-if="activeSection === 'invite'" class="manage-content--invite">
          <div class="manage-panel__code-wrap">
            <code class="manage-panel__code">{{ coachCode || "..." }}</code>
            <button class="manage-panel__btn manage-panel__btn--secondary" type="button" :disabled="!coachCode" @click="copyCode">
              {{ t("coachCode.copy") }}
            </button>
          </div>
          <p class="manage-panel__hint">{{ t("managePanel.codeHint") }}</p>
        </div>

        <!-- Requests section -->
        <div v-else-if="activeSection === 'requests'" class="manage-content--requests">
          <p v-if="joinRequests.length === 0" class="manage-panel__empty">{{ t("joinRequests.empty") }}</p>
          <div v-for="req in joinRequests" :key="req.id" class="manage-panel__request-row">
            <div class="manage-panel__request-meta">
              <div class="manage-panel__request-name">{{ req.athlete_name }}</div>
              <div class="manage-panel__request-email">{{ req.athlete_username }}</div>
            </div>
            <div class="manage-panel__request-actions">
              <button
                class="manage-panel__btn manage-panel__btn--secondary"
                type="button"
                :disabled="processingRequestId === req.id"
                @click="approve(req.id)"
              >
                {{ processingRequestId === req.id ? t("joinRequests.approving") : t("joinRequests.approve") }}
              </button>
              <button
                class="manage-panel__btn manage-panel__btn--ghost"
                type="button"
                :disabled="processingRequestId === req.id"
                @click="reject(req.id)"
              >
                {{ processingRequestId === req.id ? t("joinRequests.rejecting") : t("joinRequests.reject") }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="manage-panel__footer">
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
        <polyline points="20 6 9 17 4 12" />
      </svg>
      {{ t("managePanel.autoSave") }}
    </div>
  </aside>
</template>

<style scoped>
.manage-panel {
  position: fixed;
  top: 52px;
  left: 0;
  bottom: 0;
  width: 480px;
  background: #111113;
  border-right: 1px solid #27272a;
  box-shadow: 6px 0 32px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 90;
}

.manage-panel--open {
  transform: translateX(0);
}

.manage-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1rem 1.25rem 0.875rem;
  border-bottom: 1px solid var(--eb-border);
  flex-shrink: 0;
}

.manage-panel__title {
  font-family: var(--eb-font-display);
  font-size: 1rem;
  font-weight: 700;
  color: var(--eb-text);
}

.manage-panel__summary {
  margin-top: 0.15rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
}

.manage-panel__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid var(--eb-border);
  border-radius: 6px;
  background: transparent;
  color: var(--eb-text-muted);
  cursor: pointer;
  flex-shrink: 0;
  transition: color 150ms;
}

.manage-panel__close:hover {
  color: var(--eb-text);
}

.manage-panel__body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Left vertical menu */
.manage-panel__menu {
  width: 116px;
  flex-shrink: 0;
  border-right: 1px solid var(--eb-border);
  padding: 0.75rem 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  overflow-y: auto;
}

.manage-panel__menu-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  padding: 0.85rem 0.5rem;
  border: 0;
  border-left: 2px solid transparent;
  background: transparent;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: color 150ms, border-color 150ms;
  position: relative;
}

.manage-panel__menu-item:hover {
  color: var(--eb-text);
}

.manage-panel__menu-item--active {
  border-left-color: var(--eb-lime);
  color: var(--eb-lime);
}

.manage-panel__badge {
  position: absolute;
  top: 6px;
  right: 8px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: #f59e0b;
  color: #09090b;
  font-size: 0.625rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Right content */
.manage-panel__content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

/* Athletes */
.manage-panel__athlete-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.manage-panel__athlete-row {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 0.75rem;
  border: 1px solid var(--eb-border);
  border-radius: 8px;
  background: var(--eb-bg);
  flex-wrap: wrap;
}

.manage-panel__athlete-row--hidden {
  opacity: 0.45;
}

.manage-panel__athlete-row--hidden .manage-panel__athlete-name {
  text-decoration: line-through;
}

.manage-panel__dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--eb-lime);
  flex-shrink: 0;
}

.manage-panel__dot--muted {
  background: var(--eb-border);
}

.manage-panel__athlete-name {
  flex: 1;
  min-width: 0;
  font-size: 0.875rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.manage-panel__focus-tag {
  color: var(--eb-blue);
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.manage-panel__row-actions {
  display: flex;
  gap: 0.25rem;
  margin-left: auto;
}

.manage-panel__icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: 1px solid var(--eb-border);
  border-radius: 5px;
  background: transparent;
  color: var(--eb-text-muted);
  cursor: pointer;
  transition: color 150ms, border-color 150ms;
}

.manage-panel__icon-btn:hover {
  color: var(--eb-text);
}

.manage-panel__icon-btn--danger:hover {
  color: var(--eb-danger);
  border-color: rgba(244, 63, 94, 0.4);
}

.manage-panel__remove-confirm {
  width: 100%;
  padding-top: 0.625rem;
  border-top: 1px solid var(--eb-border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.manage-panel__remove-text {
  margin: 0;
  color: var(--eb-text-muted);
  font-size: 0.8125rem;
}

.manage-panel__remove-input {
  padding: 0.4rem 0.65rem;
  border: 1px solid var(--eb-danger);
  border-radius: 5px;
  background: var(--eb-bg);
  color: var(--eb-text);
  font-size: 0.8125rem;
}

.manage-panel__remove-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

/* Invite */
.manage-panel__code-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.manage-panel__code {
  flex: 1;
  padding: 0.65rem 0.875rem;
  border: 1px solid var(--eb-border);
  border-radius: 8px;
  background: var(--eb-bg);
  color: var(--eb-lime);
  font-family: var(--eb-font-mono);
  font-size: 1.125rem;
  letter-spacing: 0.16em;
}

.manage-panel__hint {
  margin: 0;
  color: var(--eb-text-muted);
  font-size: 0.8125rem;
  line-height: 1.5;
}

.manage-panel__empty {
  color: var(--eb-text-muted);
  font-size: 0.875rem;
  text-align: center;
  padding: 1.5rem;
}

/* Requests */
.manage-panel__request-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid var(--eb-border);
  border-radius: 8px;
  background: var(--eb-bg);
  margin-bottom: 0.5rem;
}

.manage-panel__request-name {
  font-weight: 600;
  font-size: 0.875rem;
}

.manage-panel__request-email {
  color: var(--eb-text-muted);
  font-size: 0.75rem;
  margin-top: 0.15rem;
}

.manage-panel__request-actions {
  display: flex;
  gap: 0.5rem;
}

/* Shared buttons */
.manage-panel__btn {
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 150ms;
}

.manage-panel__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.manage-panel__btn--secondary {
  border: 1px solid rgba(200, 255, 0, 0.3);
  background: rgba(200, 255, 0, 0.07);
  color: var(--eb-lime);
}

.manage-panel__btn--ghost {
  border: 1px solid var(--eb-border);
  background: transparent;
  color: var(--eb-text-muted);
}

.manage-panel__btn--danger {
  border: 1px solid rgba(244, 63, 94, 0.4);
  background: rgba(244, 63, 94, 0.08);
  color: var(--eb-danger);
}

/* Footer */
.manage-panel__footer {
  padding: 0.75rem 1.25rem;
  border-top: 1px solid var(--eb-border);
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  flex-shrink: 0;
}

.manage-panel__footer svg {
  color: #4ade80;
}
</style>
