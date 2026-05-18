<script setup lang="ts">
import { computed, ref, watch } from "vue";

import EbModal from "@/components/ui/EbModal.vue";
import { useGarminImport } from "@/composables/useGarminImport";
import { useAuthStore } from "@/stores/auth";
import { useToastStore } from "@/stores/toasts";
import { useTrainingStore } from "@/stores/training";

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  close: [];
}>();

const authStore = useAuthStore();
const toastStore = useToastStore();
const trainingStore = useTrainingStore();
const { t } = useI18n();

const importFlow = useGarminImport(
  computed(() => authStore.user?.capabilities),
);

const ranges = [
  { value: "yesterday", label: computed(() => t("imports.ranges.yesterday")) },
  { value: "last_7_days", label: computed(() => t("imports.ranges.last7Days")) },
  { value: "last_30_days", label: computed(() => t("imports.ranges.last30Days")) },
];

type Section = "garmin" | "fit";
const activeSection = ref<Section>("garmin");

async function refreshAfterImport() {
  await authStore.initialize();
  if (trainingStore.selectedMonthValue) {
    await trainingStore.loadDashboard(trainingStore.selectedMonthValue, { silent: true });
    return;
  }
  await trainingStore.loadDashboard(undefined, { silent: true });
}

async function handleConnect() {
  try {
    await importFlow.connect();
    await refreshAfterImport();
    toastStore.push(importFlow.statusMessage.value || t("imports.fallbacks.connected"), "success");
  } catch {
    toastStore.push(importFlow.errorMessage.value || t("imports.fallbacks.connectFailed"), "danger");
  }
}

async function handleDisconnect() {
  try {
    await importFlow.disconnect();
    await refreshAfterImport();
    toastStore.push(importFlow.statusMessage.value || t("imports.fallbacks.disconnected"), "success");
  } catch {
    toastStore.push(importFlow.errorMessage.value || t("imports.fallbacks.disconnectFailed"), "danger");
  }
}

async function handleSync() {
  try {
    await importFlow.sync();
    toastStore.push(importFlow.statusMessage.value || t("imports.fallbacks.syncStarted"), "success");
  } catch {
    toastStore.push(importFlow.errorMessage.value || t("imports.fallbacks.syncFailed"), "danger");
  }
}

async function handleFitChange(event: Event) {
  const target = event.target;
  if (!(target instanceof HTMLInputElement) || !target.files?.length) return;
  try {
    await importFlow.upload(target.files[0]);
    await refreshAfterImport();
    toastStore.push(importFlow.statusMessage.value || t("imports.fallbacks.fitFinished"), "success");
    target.value = "";
  } catch {
    toastStore.push(importFlow.errorMessage.value || t("imports.fallbacks.fitFailed"), "danger");
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      importFlow.open();
      activeSection.value = "garmin";
    }
  },
);

watch(
  () => importFlow.job.value?.done,
  async (done, previous) => {
    if (done && !previous) {
      await refreshAfterImport();
      toastStore.push(importFlow.statusMessage.value || t("imports.fallbacks.syncFinished"), "success");
    }
  },
);
</script>

<template>
  <EbModal :open="props.open">
    <div class="gi">

      <!-- Header -->
      <div class="gi__header">
        <div class="gi__header-icon">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
            <path d="M21 3v5h-5"/>
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
            <path d="M3 21v-5h5"/>
          </svg>
        </div>
        <div class="gi__header-info">
          <div class="gi__title">{{ t("imports.title") }}</div>
          <div class="gi__subtitle">
            <span v-if="importFlow.connected.value" class="gi__conn-dot gi__conn-dot--on" />
            <span v-else class="gi__conn-dot gi__conn-dot--off" />
            {{
              importFlow.connected.value
                ? (importFlow.connectionLabel.value || t("imports.connected"))
                : t("imports.connectCopy")
            }}
          </div>
        </div>
        <button class="gi__close" type="button" :aria-label="t('imports.close')" @click="emit('close')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <!-- Two-column body -->
      <div class="gi__layout">

        <!-- Left nav -->
        <nav class="gi__nav">
          <button
            class="gi__nav-item"
            :class="{ 'gi__nav-item--active': activeSection === 'garmin' }"
            type="button"
            @click="activeSection = 'garmin'"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
              <path d="M21 3v5h-5"/>
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
              <path d="M3 21v-5h5"/>
            </svg>
            Garmin
            <span
              class="gi__nav-dot"
              :class="importFlow.connected.value ? 'gi__nav-dot--on' : 'gi__nav-dot--off'"
            />
          </button>
          <button
            class="gi__nav-item"
            :class="{ 'gi__nav-item--active': activeSection === 'fit' }"
            type="button"
            @click="activeSection = 'fit'"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="17 8 12 3 7 8"/>
              <line x1="12" y1="3" x2="12" y2="15"/>
            </svg>
            FIT
          </button>
        </nav>

        <!-- Right content -->
        <div class="gi__content">

          <!-- Garmin tab -->
          <section v-if="activeSection === 'garmin'" class="gi__section">

            <!-- Connection -->
            <div class="gi__section-label">{{ t("imports.connectionTitle") }}</div>

            <!-- Connected -->
            <div v-if="importFlow.connected.value" class="gi__connected-row">
              <div class="gi__connected-info">
                <span class="gi__conn-dot gi__conn-dot--on" />
                <span class="gi__connected-name">{{ importFlow.connectionLabel.value || t("imports.connected") }}</span>
              </div>
              <button
                class="gi__danger-btn"
                type="button"
                :disabled="importFlow.isBusy.value"
                @click="handleDisconnect"
              >
                {{ t("imports.disconnect") }}
              </button>
            </div>

            <!-- Not connected -->
            <template v-else-if="importFlow.canConnect.value">
              <label class="gi__field">
                <span>{{ t("imports.email") }}</span>
                <input v-model="importFlow.garminEmail.value" type="email" :disabled="importFlow.isBusy.value" />
              </label>
              <label class="gi__field">
                <span>{{ t("imports.password") }}</span>
                <input v-model="importFlow.garminPassword.value" type="password" :disabled="importFlow.isBusy.value" />
              </label>
              <div class="gi__section-footer">
                <button
                  class="gi__primary-btn"
                  type="button"
                  :disabled="importFlow.isBusy.value"
                  @click="handleConnect"
                >
                  {{ importFlow.isBusy.value ? t("imports.connecting") : t("imports.connect") }}
                </button>
              </div>
            </template>

            <!-- Sync -->
            <div class="gi__sep" />
            <div class="gi__section-label">{{ t("imports.syncTitle") }}</div>
            <div class="gi__inline-row">
              <label class="gi__field" style="flex: 1">
                <span>{{ t("imports.range") }}</span>
                <select
                  v-model="importFlow.selectedRange.value"
                  class="gi__select"
                  :disabled="importFlow.isBusy.value || !importFlow.connected.value"
                >
                  <option v-for="opt in ranges" :key="opt.value" :value="opt.value">{{ opt.label.value }}</option>
                </select>
              </label>
              <button
                class="gi__primary-btn"
                type="button"
                :disabled="importFlow.isBusy.value || !importFlow.connected.value || !importFlow.canSync.value"
                @click="handleSync"
              >
                {{ importFlow.isBusy.value ? t("imports.starting") : t("imports.sync") }}
              </button>
            </div>

            <!-- Job progress -->
            <div v-if="importFlow.job.value" class="gi__job">
              <div class="gi__job-head">
                <span>{{ importFlow.job.value.status_label }}</span>
                <span>{{ importFlow.job.value.progress_percent }}%</span>
              </div>
              <div class="gi__job-track">
                <span class="gi__job-fill" :style="{ width: `${importFlow.job.value.progress_percent}%` }" />
              </div>
              <p v-if="importFlow.job.value.message" class="gi__job-msg">{{ importFlow.job.value.message }}</p>
            </div>

          </section>

          <!-- FIT tab -->
          <section v-else-if="activeSection === 'fit'" class="gi__section">
            <div class="gi__section-label">{{ t("imports.fitTitle") }}</div>
            <p class="gi__copy">{{ t("imports.fitCopy") }}</p>
            <label class="gi__file-label">
              <input
                class="gi__file-input"
                type="file"
                accept=".fit"
                :disabled="importFlow.isBusy.value"
                @change="handleFitChange"
              />
              <span class="gi__file-btn" :class="{ 'gi__file-btn--busy': importFlow.isBusy.value }">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="17 8 12 3 7 8"/>
                  <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                {{ importFlow.isBusy.value ? t("imports.starting") : t("imports.fitChoose") }}
              </span>
            </label>
          </section>

        </div>
      </div>

      <!-- Footer: status / error -->
      <div class="gi__footer">
        <span v-if="importFlow.errorMessage.value" class="gi__footer-error">{{ importFlow.errorMessage.value }}</span>
        <span v-else-if="importFlow.statusMessage.value" class="gi__footer-status">{{ importFlow.statusMessage.value }}</span>
      </div>

    </div>
  </EbModal>
</template>

<style scoped>
:deep(.eb-modal__panel) {
  width: min(100%, 34rem);
}

.gi {
  display: flex;
  flex-direction: column;
  height: min(88vh, 28rem);
}

/* ── Header ────────────────────────────────── */
.gi__header {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid var(--eb-border);
  flex-shrink: 0;
}

.gi__header-icon {
  display: inline-grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(126, 207, 126, 0.08);
  border: 1px solid #2d5a2d;
  color: #7ecf7e;
  flex-shrink: 0;
}

.gi__header-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.gi__title {
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.875rem;
  color: var(--eb-text, #fafafa);
}

.gi__subtitle {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--eb-text-muted, #71717a);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gi__conn-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.gi__conn-dot--on  { background: #4ade80; }
.gi__conn-dot--off { background: #52525b; }

.gi__close {
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
  transition: color 150ms, border-color 150ms;
}

.gi__close:hover {
  color: var(--eb-text);
  border-color: #52525b;
}

/* ── Layout ────────────────────────────────── */
.gi__layout {
  display: grid;
  grid-template-columns: 9.5rem 1fr;
  flex: 1;
  min-height: 0;
}

/* ── Left nav ──────────────────────────────── */
.gi__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0.75rem 0.625rem;
  border-right: 1px solid var(--eb-border);
  background: #111113;
  flex-shrink: 0;
}

.gi__nav-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 0.625rem;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--eb-text-muted, #71717a);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 600;
  font-size: 0.8125rem;
  text-align: left;
  cursor: pointer;
  transition: background 150ms, color 150ms;
}

.gi__nav-item:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #a1a1aa;
}

.gi__nav-item--active {
  background: rgba(126, 207, 126, 0.07);
  color: #7ecf7e;
}

.gi__nav-item--active svg {
  color: #7ecf7e;
}

.gi__nav-dot {
  margin-left: auto;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.gi__nav-dot--on  { background: #4ade80; }
.gi__nav-dot--off { background: #3f3f46; }

/* ── Content ───────────────────────────────── */
.gi__content {
  padding: 1rem;
  overflow-y: auto;
}

.gi__section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.gi__section-label {
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--eb-text-muted, #71717a);
  margin-bottom: 0.125rem;
}

.gi__sep {
  height: 1px;
  background: var(--eb-border);
  margin: 0.125rem 0;
}

/* ── Fields ────────────────────────────────── */
.gi__field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.gi__field span {
  font-size: 0.6875rem;
  color: var(--eb-text-muted, #71717a);
}

.gi__field input,
.gi__select {
  width: 100%;
  padding: 0.5rem 0.7rem;
  border: 1px solid var(--eb-border, #27272a);
  border-radius: var(--eb-radius-sm, 6px);
  background: var(--eb-bg, #09090b);
  color: var(--eb-text, #fafafa);
  font: inherit;
  font-size: 0.8125rem;
  transition: border-color 150ms;
}

.gi__field input:focus,
.gi__select:focus {
  outline: none;
  border-color: rgba(126, 207, 126, 0.4);
}

.gi__field input:disabled,
.gi__select:disabled {
  opacity: 0.45;
  cursor: default;
}

.gi__copy {
  margin: 0;
  font-size: 0.8125rem;
  color: var(--eb-text-muted, #71717a);
  line-height: 1.5;
}

/* ── Connected row ─────────────────────────── */
.gi__connected-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border: 1px solid #2d5a2d;
  border-radius: var(--eb-radius-sm, 6px);
  background: rgba(126, 207, 126, 0.05);
}

.gi__connected-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;
}

.gi__connected-name {
  font-size: 0.8125rem;
  color: #7ecf7e;
  font-family: var(--eb-font-mono, 'JetBrains Mono', monospace);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gi__danger-btn {
  flex-shrink: 0;
  height: 28px;
  padding: 0 0.75rem;
  border: 1px solid rgba(244, 63, 94, 0.3);
  border-radius: var(--eb-radius-sm, 6px);
  background: transparent;
  color: var(--eb-danger, #f43f5e);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background 150ms, border-color 150ms;
}

.gi__danger-btn:hover:not(:disabled) {
  background: rgba(244, 63, 94, 0.08);
  border-color: rgba(244, 63, 94, 0.5);
}

.gi__danger-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

/* ── Inline row (sync) ─────────────────────── */
.gi__inline-row {
  display: flex;
  align-items: flex-end;
  gap: 0.625rem;
}

.gi__section-footer {
  display: flex;
  justify-content: flex-end;
}

/* ── Buttons ───────────────────────────────── */
.gi__primary-btn {
  flex-shrink: 0;
  height: 34px;
  padding: 0 1rem;
  border: 1px solid rgba(126, 207, 126, 0.35);
  border-radius: var(--eb-radius-sm, 6px);
  background: rgba(126, 207, 126, 0.07);
  color: #7ecf7e;
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.8125rem;
  white-space: nowrap;
  cursor: pointer;
  transition: background 150ms, border-color 150ms;
}

.gi__primary-btn:hover:not(:disabled) {
  background: rgba(126, 207, 126, 0.13);
  border-color: rgba(126, 207, 126, 0.55);
}

.gi__primary-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

/* ── Job progress ──────────────────────────── */
.gi__job {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid rgba(126, 207, 126, 0.18);
  border-radius: var(--eb-radius-sm, 6px);
  background: rgba(126, 207, 126, 0.04);
}

.gi__job-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: #7ecf7e;
  font-family: var(--eb-font-mono, 'JetBrains Mono', monospace);
  font-size: 0.75rem;
}

.gi__job-track {
  height: 3px;
  border-radius: 999px;
  background: var(--eb-border);
  overflow: hidden;
}

.gi__job-fill {
  display: block;
  height: 100%;
  background: #4ade80;
  transition: width 400ms ease-out;
}

.gi__job-msg {
  margin: 0;
  font-size: 0.75rem;
  color: var(--eb-text-muted, #71717a);
}

/* ── FIT file input ────────────────────────── */
.gi__file-label {
  display: block;
  cursor: pointer;
}

.gi__file-input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.gi__file-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  height: 34px;
  padding: 0 1rem;
  border: 1px solid rgba(126, 207, 126, 0.35);
  border-radius: var(--eb-radius-sm, 6px);
  background: rgba(126, 207, 126, 0.07);
  color: #7ecf7e;
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.8125rem;
  white-space: nowrap;
  transition: background 150ms, border-color 150ms;
}

.gi__file-label:hover .gi__file-btn:not(.gi__file-btn--busy) {
  background: rgba(126, 207, 126, 0.13);
  border-color: rgba(126, 207, 126, 0.55);
}

.gi__file-btn--busy {
  opacity: 0.4;
  cursor: default;
}

/* ── Footer ────────────────────────────────── */
.gi__footer {
  min-height: 2.25rem;
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  border-top: 1px solid var(--eb-border);
  flex-shrink: 0;
}

.gi__footer-error {
  font-size: 0.75rem;
  color: var(--eb-danger, #f43f5e);
}

.gi__footer-status {
  font-size: 0.75rem;
  color: var(--eb-text-muted, #71717a);
}

@media (max-width: 540px) {
  .gi__layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .gi__nav {
    flex-direction: row;
    border-right: 0;
    border-bottom: 1px solid var(--eb-border);
    padding: 0.5rem;
  }

  .gi__nav-item {
    white-space: nowrap;
  }
}
</style>
