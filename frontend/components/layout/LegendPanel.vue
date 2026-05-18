<script setup lang="ts">
import { ref, watch, onUnmounted } from "vue";

import { fetchLegend, saveLegend, PR_DISTANCES, type LegendPR, type LegendState } from "~/utils/api/legend";

const props = defineProps<{
  open: boolean;
  title: string;
  subtitle?: string;
  editable?: boolean;
  athleteId?: number;
}>();

const emit = defineEmits<{ close: [] }>();

const { t } = useI18n();
const ZONES = ["z1", "z2", "z3", "z4", "z5"] as const;

function emptyDraft(): LegendState {
  return {
    zones: {
      z1: { from: "", to: "" },
      z2: { from: "", to: "" },
      z3: { from: "", to: "" },
      z4: { from: "", to: "" },
      z5: { from: "", to: "" },
    },
    aerobic_threshold: "",
    anaerobic_threshold: "",
    prs: [],
  };
}

const draft = ref<LegendState>(emptyDraft());
const isLoading = ref(false);
const isSaving = ref(false);
const loadError = ref("");
const saveError = ref("");
const isEditing = ref(false);
let saveTimer: ReturnType<typeof setTimeout> | null = null;

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      isEditing.value = false;
      return;
    }
    isLoading.value = true;
    loadError.value = "";
    try {
      const data = await fetchLegend(props.athleteId);
      const s = data.state as Partial<LegendState> & { zones?: Partial<LegendState["zones"]> };
      draft.value = {
        zones: {
          z1: s.zones?.z1 ?? { from: "", to: "" },
          z2: s.zones?.z2 ?? { from: "", to: "" },
          z3: s.zones?.z3 ?? { from: "", to: "" },
          z4: s.zones?.z4 ?? { from: "", to: "" },
          z5: s.zones?.z5 ?? { from: "", to: "" },
        },
        aerobic_threshold: s.aerobic_threshold ?? "",
        anaerobic_threshold: s.anaerobic_threshold ?? "",
        prs: s.prs ?? [],
      };
    } catch {
      loadError.value = t("legend.loadError");
    } finally {
      isLoading.value = false;
    }
  }
);

watch(
  draft,
  () => {
    if (!props.open || !props.editable || !isEditing.value) return;
    if (saveTimer !== null) clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      isSaving.value = true;
      saveError.value = "";
      try {
        await saveLegend(draft.value, props.athleteId);
      } catch {
        saveError.value = t("legend.saveError");
      } finally {
        isSaving.value = false;
      }
    }, 800);
  },
  { deep: true }
);

async function flushSave() {
  if (saveTimer === null) return;
  clearTimeout(saveTimer);
  saveTimer = null;
  if (!props.editable || !isEditing.value) return;
  isSaving.value = true;
  try {
    await saveLegend(draft.value, props.athleteId);
  } catch {
    // save error on unmount — nothing to show
  } finally {
    isSaving.value = false;
  }
}

onUnmounted(() => {
  flushSave();
});

defineExpose({ draft });

function addPr() {
  draft.value.prs.push({ distance: PR_DISTANCES[0] as string, time: "" });
}

function removePr(index: number) {
  draft.value.prs.splice(index, 1);
}
</script>

<template>
  <aside class="legend-panel" :class="{ 'legend-panel--open': open }" aria-label="Legend panel">
    <div class="legend-panel__header">
      <div class="legend-panel__header-text">
        <div class="legend-panel__title">{{ title }}</div>
        <div v-if="subtitle" class="legend-panel__subtitle">{{ subtitle }}</div>
      </div>
      <button class="legend-panel__close" type="button" :aria-label="t('legend.close')" @click="emit('close')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <div v-if="isLoading" class="legend-panel__loading">
      <span>{{ t("legend.loading") }}</span>
    </div>
    <div v-else-if="loadError" class="legend-panel__load-error">
      {{ loadError }}
    </div>

    <div v-else class="legend-panel__body">
      <!-- HR Zones -->
      <section class="legend-panel__section">
        <h3 class="legend-panel__section-title">{{ t("legend.hrZones") }}</h3>
        <table class="legend-panel__table">
          <thead>
            <tr>
              <th>{{ t("legend.zone") }}</th>
              <th>{{ t("legend.from") }}</th>
              <th>{{ t("legend.to") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="zone in ZONES" :key="zone">
              <td class="legend-panel__zone-label">{{ zone.toUpperCase() }}</td>
              <td>
                <input v-if="editable && isEditing" v-model="draft.zones[zone].from" class="legend-panel__input" />
                <span v-else>{{ draft.zones[zone].from || "—" }}</span>
              </td>
              <td>
                <input v-if="editable && isEditing" v-model="draft.zones[zone].to" class="legend-panel__input" />
                <span v-else>{{ draft.zones[zone].to || "—" }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Thresholds -->
      <section class="legend-panel__section">
        <h3 class="legend-panel__section-title">{{ t("legend.thresholds") }}</h3>
        <div class="legend-panel__threshold-grid">
          <label class="legend-panel__field">
            <span class="legend-panel__label">{{ t("legend.aerobicThreshold") }}</span>
            <input v-if="editable && isEditing" v-model="draft.aerobic_threshold" class="legend-panel__input" />
            <span v-else>{{ draft.aerobic_threshold || "—" }}</span>
          </label>
          <label class="legend-panel__field">
            <span class="legend-panel__label">{{ t("legend.anaerobicThreshold") }}</span>
            <input v-if="editable && isEditing" v-model="draft.anaerobic_threshold" class="legend-panel__input" />
            <span v-else>{{ draft.anaerobic_threshold || "—" }}</span>
          </label>
        </div>
      </section>

      <!-- PRs -->
      <section class="legend-panel__section">
        <h3 class="legend-panel__section-title">{{ t("legend.prs") }}</h3>
        <table v-if="draft.prs.length > 0" class="legend-panel__table">
          <thead>
            <tr>
              <th>{{ t("legend.distance") }}</th>
              <th>{{ t("legend.time") }}</th>
              <th v-if="editable && isEditing" />
            </tr>
          </thead>
          <tbody>
            <tr v-for="(pr, index) in draft.prs" :key="index">
              <td>
                <select v-if="editable && isEditing" v-model="pr.distance" class="legend-panel__select">
                  <option v-for="d in PR_DISTANCES" :key="d" :value="d">{{ d }}</option>
                </select>
                <span v-else>{{ pr.distance }}</span>
              </td>
              <td>
                <input v-if="editable && isEditing" v-model="pr.time" class="legend-panel__input" />
                <span v-else>{{ pr.time }}</span>
              </td>
              <td v-if="editable && isEditing">
                <button class="legend-panel__remove-btn" type="button" @click="removePr(index)">
                  {{ t("legend.removePr") }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <button v-if="editable && isEditing" class="legend-panel__add-btn" type="button" @click="addPr">
          {{ t("legend.addPr") }}
        </button>
      </section>
    </div>

    <div class="legend-panel__footer">
      <!-- Status (only visible while editing) -->
      <span v-if="editable && isEditing && saveError" class="legend-panel__save-error">{{ saveError }}</span>
      <span v-else-if="editable && isEditing && isSaving" class="legend-panel__saving">{{ t("legend.saving") }}</span>
      <span v-else-if="editable && isEditing" class="legend-panel__autosave">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        {{ t("legend.autoSave") }}
      </span>
      <span v-else />

      <!-- Pencil toggle (only when editable) -->
      <button
        v-if="editable"
        class="legend-panel__edit-btn"
        :class="{ 'legend-panel__edit-btn--active': isEditing }"
        type="button"
        :title="isEditing ? t('legend.doneEditing') : t('legend.edit')"
        @click="isEditing = !isEditing"
      >
        <svg v-if="!isEditing" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4Z"/>
        </svg>
        <svg v-else width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        {{ isEditing ? t("legend.doneEditing") : t("legend.edit") }}
      </button>
    </div>
  </aside>
</template>

<style scoped>
.legend-panel {
  position: fixed;
  top: 52px;
  right: 0;
  bottom: 0;
  width: 340px;
  background: #111113;
  border-left: 1px solid var(--eb-border);
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 90;
  overflow: hidden;
}

.legend-panel--open {
  transform: translateX(0);
}

.legend-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 1rem 1.125rem 0.875rem;
  border-bottom: 1px solid var(--eb-border);
  flex-shrink: 0;
}

.legend-panel__title {
  font-family: var(--eb-font-display);
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--eb-text);
}

.legend-panel__subtitle {
  margin-top: 0.15rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.legend-panel__close {
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
  transition: color 150ms ease-out;
}

.legend-panel__close:hover {
  color: var(--eb-text);
}

.legend-panel__loading {
  padding: 1.5rem;
  color: var(--eb-text-muted);
  font-size: 0.875rem;
}

.legend-panel__body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.125rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.legend-panel__section {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.legend-panel__section-title {
  margin: 0;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.legend-panel__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.legend-panel__table th {
  padding: 0.3rem 0.5rem;
  color: var(--eb-text-muted);
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-align: left;
  text-transform: uppercase;
  border-bottom: 1px solid var(--eb-border);
}

.legend-panel__table td {
  padding: 0.35rem 0.5rem;
  border-bottom: 1px solid rgba(39, 39, 42, 0.5);
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}

.legend-panel__zone-label {
  color: var(--eb-lime);
  font-weight: 600;
}

.legend-panel__input,
.legend-panel__select {
  width: 100%;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--eb-border);
  border-radius: 5px;
  background: var(--eb-bg);
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.8125rem;
}

.legend-panel__input:focus,
.legend-panel__select:focus {
  outline: none;
  border-color: rgba(200, 255, 0, 0.4);
}

.legend-panel__threshold-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.legend-panel__field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.legend-panel__label {
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
}

.legend-panel__add-btn {
  align-self: flex-start;
  padding: 0.35rem 0.75rem;
  border: 1px solid var(--eb-border);
  border-radius: 6px;
  background: transparent;
  color: var(--eb-text-muted);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: border-color 150ms, color 150ms;
}

.legend-panel__add-btn:hover {
  border-color: rgba(200, 255, 0, 0.3);
  color: var(--eb-lime);
}

.legend-panel__remove-btn {
  padding: 0.2rem 0.5rem;
  border: 0;
  background: transparent;
  color: var(--eb-text-muted);
  font-size: 0.75rem;
  cursor: pointer;
}

.legend-panel__remove-btn:hover {
  color: var(--eb-danger);
}

.legend-panel__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.625rem 1.125rem;
  border-top: 1px solid var(--eb-border);
  flex-shrink: 0;
}

.legend-panel__edit-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  height: 28px;
  padding: 0 0.75rem;
  border: 1px solid #3f3f46;
  border-radius: 6px;
  background: transparent;
  color: var(--eb-text-muted, #71717a);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 0.6875rem;
  cursor: pointer;
  flex-shrink: 0;
  transition: color 150ms, border-color 150ms, background 150ms;
}

.legend-panel__edit-btn:hover {
  color: #a1a1aa;
  border-color: #52525b;
}

.legend-panel__edit-btn--active {
  border-color: rgba(200, 255, 0, 0.4);
  background: rgba(200, 255, 0, 0.07);
  color: var(--eb-lime, #c8ff00);
}

.legend-panel__edit-btn--active:hover {
  border-color: rgba(200, 255, 0, 0.6);
  background: rgba(200, 255, 0, 0.12);
  color: var(--eb-lime, #c8ff00);
}

.legend-panel__autosave,
.legend-panel__saving {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
}

.legend-panel__autosave svg {
  color: #4ade80;
}

.legend-panel__load-error {
  padding: 1.5rem;
  color: #f43f5e;
  font-size: 0.875rem;
}

.legend-panel__save-error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #f43f5e;
  font-size: 0.6875rem;
}
</style>
