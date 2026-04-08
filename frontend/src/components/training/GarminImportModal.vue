<script setup lang="ts">
import { computed, ref, watch } from "vue";

import EbButton from "@/components/ui/EbButton.vue";
import EbModal from "@/components/ui/EbModal.vue";
import { useGarminImport } from "@/composables/useGarminImport";
import { useAuthStore } from "@/stores/auth";
import { useToastStore } from "@/stores/toasts";
import { useTrainingStore } from "@/stores/training";

const authStore = useAuthStore();
const toastStore = useToastStore();
const trainingStore = useTrainingStore();
const fitInput = ref<HTMLInputElement | null>(null);

const importFlow = useGarminImport(
  computed(() => authStore.user?.capabilities),
);

const ranges = [
  { value: "yesterday", label: "Yesterday" },
  { value: "last_7_days", label: "Last 7 days" },
  { value: "last_30_days", label: "Last 30 days" },
];

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
    toastStore.push(importFlow.statusMessage.value || "Garmin connected.", "success");
  } catch (error) {
    toastStore.push(importFlow.errorMessage.value || (error instanceof Error ? error.message : "Garmin connect failed."), "danger");
  }
}

async function handleDisconnect() {
  try {
    await importFlow.disconnect();
    await refreshAfterImport();
    toastStore.push(importFlow.statusMessage.value || "Garmin disconnected.", "success");
  } catch (error) {
    toastStore.push(importFlow.errorMessage.value || (error instanceof Error ? error.message : "Garmin disconnect failed."), "danger");
  }
}

async function handleSync() {
  try {
    await importFlow.sync();
    toastStore.push(importFlow.statusMessage.value || "Garmin sync started.", "success");
  } catch (error) {
    toastStore.push(importFlow.errorMessage.value || (error instanceof Error ? error.message : "Garmin sync failed."), "danger");
  }
}

async function handleFitChange(event: Event) {
  const target = event.target;
  if (!(target instanceof HTMLInputElement) || !target.files?.length) {
    return;
  }

  try {
    await importFlow.upload(target.files[0]);
    await refreshAfterImport();
    toastStore.push(importFlow.statusMessage.value || "FIT import finished.", "success");
    target.value = "";
  } catch (error) {
    toastStore.push(importFlow.errorMessage.value || (error instanceof Error ? error.message : "FIT import failed."), "danger");
  }
}

watch(
  () => importFlow.job.value?.done,
  async (done, previous) => {
    if (done && !previous) {
      await refreshAfterImport();
      toastStore.push(importFlow.statusMessage.value || "Garmin sync finished.", "success");
    }
  },
);
</script>

<template>
  <div class="import-launcher">
    <EbButton variant="secondary" @click="importFlow.open">Import</EbButton>

    <EbModal :open="importFlow.isOpen.value">
      <div class="import-modal">
        <div class="import-modal__header">
          <div>
            <div class="import-modal__eyebrow">Imports</div>
            <h2>Garmin and FIT</h2>
          </div>
          <EbButton variant="ghost" @click="importFlow.close">Close</EbButton>
        </div>

        <div class="import-modal__body">
          <section class="import-section">
            <div class="import-section__title">Garmin connection</div>
            <p class="import-section__copy">
              <template v-if="importFlow.connected.value">
                Connected{{ importFlow.connectionLabel.value ? ` as ${importFlow.connectionLabel.value}` : "" }}.
              </template>
              <template v-else>
                Connect your Garmin account to sync recent activities.
              </template>
            </p>

            <div v-if="!importFlow.connected.value && importFlow.canConnect.value" class="import-section__grid">
              <label class="import-field">
                <span>Email</span>
                <input v-model="importFlow.garminEmail.value" class="import-input" type="email" :disabled="importFlow.isBusy.value" />
              </label>
              <label class="import-field">
                <span>Password</span>
                <input v-model="importFlow.garminPassword.value" class="import-input" type="password" :disabled="importFlow.isBusy.value" />
              </label>
              <EbButton :disabled="importFlow.isBusy.value" @click="handleConnect">
                {{ importFlow.isBusy.value ? "Connecting..." : "Connect Garmin" }}
              </EbButton>
            </div>

            <div v-else-if="importFlow.connected.value" class="import-section__actions">
              <EbButton
                variant="danger"
                :disabled="importFlow.isBusy.value"
                @click="handleDisconnect"
              >
                Disconnect
              </EbButton>
            </div>
          </section>

          <section class="import-section">
            <div class="import-section__title">Garmin sync</div>
            <div class="import-section__grid import-section__grid--sync">
              <label class="import-field">
                <span>Range</span>
                <select v-model="importFlow.selectedRange.value" class="import-input" :disabled="importFlow.isBusy.value || !importFlow.connected.value">
                  <option v-for="option in ranges" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </label>

              <EbButton
                :disabled="importFlow.isBusy.value || !importFlow.connected.value || !importFlow.canSync.value"
                @click="handleSync"
              >
                {{ importFlow.isBusy.value ? "Starting..." : "Sync Garmin" }}
              </EbButton>
            </div>

            <div v-if="importFlow.job.value" class="import-job">
              <div class="import-job__head">
                <span>{{ importFlow.job.value.status_label }}</span>
                <span>{{ importFlow.job.value.progress_percent }}%</span>
              </div>
              <div class="import-job__track">
                <span class="import-job__fill" :style="{ width: `${importFlow.job.value.progress_percent}%` }" />
              </div>
              <p class="import-job__message">{{ importFlow.job.value.message }}</p>
            </div>
          </section>

          <section class="import-section">
            <div class="import-section__title">FIT upload</div>
            <p class="import-section__copy">Upload a FIT file from any supported device.</p>
            <div class="import-section__actions">
              <input
                ref="fitInput"
                class="import-file"
                type="file"
                accept=".fit"
                :disabled="importFlow.isBusy.value"
                @change="handleFitChange"
              />
            </div>
          </section>

          <p v-if="importFlow.errorMessage.value" class="import-modal__error">{{ importFlow.errorMessage.value }}</p>
          <p v-else-if="importFlow.statusMessage.value" class="import-modal__status">{{ importFlow.statusMessage.value }}</p>
        </div>
      </div>
    </EbModal>
  </div>
</template>

<style scoped>
.import-launcher {
  display: inline-flex;
}

.import-modal {
  display: grid;
}

.import-modal__header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  padding: 1.25rem 1.25rem 1rem;
  border-bottom: 1px solid var(--eb-border);
}

.import-modal__eyebrow,
.import-section__title,
.import-field span {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.import-modal__header h2 {
  margin: 0.5rem 0 0;
  font-family: var(--eb-font-display);
  font-size: 1.6rem;
}

.import-modal__body {
  display: grid;
  gap: 1rem;
  padding: 1.25rem;
}

.import-section {
  display: grid;
  gap: 0.8rem;
  padding: 1rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  background: rgba(255, 255, 255, 0.02);
}

.import-section__copy,
.import-job__message,
.import-modal__status,
.import-modal__error {
  margin: 0;
  color: var(--eb-text-soft);
  font-size: 0.8125rem;
  line-height: 1.5;
}

.import-modal__error {
  color: var(--eb-danger);
}

.import-modal__status {
  color: var(--eb-text);
}

.import-section__grid {
  display: grid;
  gap: 0.8rem;
}

.import-section__grid--sync {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
}

.import-field {
  display: grid;
  gap: 0.45rem;
}

.import-input,
.import-file {
  width: 100%;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  padding: 0.75rem 0.85rem;
}

.import-section__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.import-job {
  display: grid;
  gap: 0.6rem;
  padding: 0.9rem 1rem;
  border: 1px solid rgba(200, 255, 0, 0.16);
  border-radius: var(--eb-radius-sm);
  background: rgba(200, 255, 0, 0.05);
}

.import-job__head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.75rem;
}

.import-job__track {
  height: 0.3rem;
  border-radius: 999px;
  background: var(--eb-border);
  overflow: hidden;
}

.import-job__fill {
  display: block;
  height: 100%;
  background: var(--eb-lime);
}

@media (max-width: 767px) {
  .import-modal__header,
  .import-section__grid--sync {
    grid-template-columns: 1fr;
  }

  .import-modal__header {
    display: grid;
  }
}
</style>
