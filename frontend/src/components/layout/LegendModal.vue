<script setup lang="ts">
import { computed, ref, watch } from "vue";

import type { LegendPR, LegendState } from "@/api/legend";
import { PR_DISTANCES } from "@/api/legend";
import { useI18n } from "@/composables/useI18n";
import { useAuthStore } from "@/stores/auth";
import { useLegendStore } from "@/stores/legend";
import EbButton from "@/components/ui/EbButton.vue";
import EbModal from "@/components/ui/EbModal.vue";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ (e: "close"): void }>();

const { t } = useI18n();
const authStore = useAuthStore();
const legendStore = useLegendStore();

const isCoach = computed(() => authStore.user?.role === "COACH");

const draft = ref<LegendState>({
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
});

watch(
  () => props.open,
  async (open) => {
    if (open) {
      await legendStore.load();
      if (legendStore.state) {
        // Backend only stores non-empty values, so loaded state may be partial.
        // Merge with defaults so draft always has a complete shape.
        const s = legendStore.state as Partial<LegendState> & {
          zones?: Partial<LegendState["zones"]>;
        };
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
      }
    }
  },
);

const ZONES = ["z1", "z2", "z3", "z4", "z5"] as const;

function addPr() {
  draft.value.prs.push({ distance: PR_DISTANCES[0], time: "" });
}

function removePr(index: number) {
  draft.value.prs.splice(index, 1);
}

async function save() {
  try {
    await legendStore.save(draft.value);
    emit("close");
  } catch {
    // error shown via legendStore.error
  }
}
</script>

<template>
  <EbModal :open="open">
    <div class="legend-modal">
      <div class="legend-modal__header">
        <h2 class="legend-modal__title">{{ t("legend.title") }}</h2>
        <EbButton variant="ghost" @click="emit('close')">{{ t("legend.close") }}</EbButton>
      </div>

      <div v-if="legendStore.isLoading" class="legend-modal__loading">
        <span>{{ t("legend.loadError") }}</span>
      </div>

      <div v-else class="legend-modal__body">
        <!-- HR Zones -->
        <section class="legend-modal__section">
          <h3 class="legend-modal__section-title">{{ t("legend.hrZones") }}</h3>
          <table class="legend-modal__table">
            <thead>
              <tr>
                <th>{{ t("legend.zone") }}</th>
                <th>{{ t("legend.from") }}</th>
                <th>{{ t("legend.to") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="zone in ZONES" :key="zone">
                <td class="legend-modal__zone-label">{{ zone.toUpperCase() }}</td>
                <td>
                  <input
                    v-if="isCoach"
                    v-model="draft.zones[zone].from"
                    class="legend-modal__input"
                  />
                  <span v-else>{{ legendStore.state?.zones[zone].from ?? "-" }}</span>
                </td>
                <td>
                  <input
                    v-if="isCoach"
                    v-model="draft.zones[zone].to"
                    class="legend-modal__input"
                  />
                  <span v-else>{{ legendStore.state?.zones[zone].to ?? "-" }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <!-- Thresholds -->
        <section class="legend-modal__section">
          <h3 class="legend-modal__section-title">{{ t("legend.thresholds") }}</h3>
          <div class="legend-modal__threshold-grid">
            <label class="legend-modal__field">
              <span class="legend-modal__label">{{ t("legend.aerobicThreshold") }}</span>
              <input v-if="isCoach" v-model="draft.aerobic_threshold" class="legend-modal__input" />
              <span v-else>{{ legendStore.state?.aerobic_threshold ?? "-" }}</span>
            </label>
            <label class="legend-modal__field">
              <span class="legend-modal__label">{{ t("legend.anaerobicThreshold") }}</span>
              <input v-if="isCoach" v-model="draft.anaerobic_threshold" class="legend-modal__input" />
              <span v-else>{{ legendStore.state?.anaerobic_threshold ?? "-" }}</span>
            </label>
          </div>
        </section>

        <!-- PRs -->
        <section class="legend-modal__section">
          <h3 class="legend-modal__section-title">{{ t("legend.prs") }}</h3>
          <table v-if="(isCoach ? draft.prs : legendStore.state?.prs ?? []).length > 0" class="legend-modal__table">
            <thead>
              <tr>
                <th>{{ t("legend.distance") }}</th>
                <th>{{ t("legend.time") }}</th>
                <th v-if="isCoach" />
              </tr>
            </thead>
            <tbody>
              <tr v-for="(pr, index) in (isCoach ? draft.prs : legendStore.state?.prs ?? [])" :key="index">
                <td>
                  <select v-if="isCoach" v-model="(draft.prs[index] as LegendPR).distance" class="legend-modal__select">
                    <option v-for="d in PR_DISTANCES" :key="d" :value="d">{{ d }}</option>
                  </select>
                  <span v-else>{{ pr.distance }}</span>
                </td>
                <td>
                  <input v-if="isCoach" v-model="(draft.prs[index] as LegendPR).time" class="legend-modal__input" />
                  <span v-else>{{ pr.time }}</span>
                </td>
                <td v-if="isCoach">
                  <EbButton variant="ghost" @click="removePr(index)">{{ t("legend.removePr") }}</EbButton>
                </td>
              </tr>
            </tbody>
          </table>
          <EbButton v-if="isCoach" variant="secondary" @click="addPr">{{ t("legend.addPr") }}</EbButton>
        </section>

        <p v-if="legendStore.error" class="legend-modal__error">{{ legendStore.error }}</p>

        <div v-if="isCoach" class="legend-modal__footer">
          <EbButton :disabled="legendStore.isSaving" @click="save">
            {{ legendStore.isSaving ? t("legend.saving") : t("legend.save") }}
          </EbButton>
        </div>
      </div>
    </div>
  </EbModal>
</template>

<style scoped>
.legend-modal {
  display: flex;
  flex-direction: column;
  max-height: 85vh;
  overflow: hidden;
}

.legend-modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--eb-border);
}

.legend-modal__title {
  margin: 0;
  font-family: var(--eb-font-display);
  font-size: 1.125rem;
  font-weight: 700;
}

.legend-modal__loading {
  padding: 2rem 1.5rem;
  color: var(--eb-text-muted);
  font-size: 0.875rem;
  text-align: center;
}

.legend-modal__body {
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.legend-modal__section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.legend-modal__section-title {
  margin: 0;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.legend-modal__table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.legend-modal__table th {
  padding: 0.4rem 0.75rem;
  color: var(--eb-text-muted);
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-align: left;
  text-transform: uppercase;
  border-bottom: 1px solid var(--eb-border);
}

.legend-modal__table td {
  padding: 0.45rem 0.75rem;
  border-bottom: 1px solid rgba(39, 39, 42, 0.5);
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
}

.legend-modal__zone-label {
  color: var(--eb-lime);
  font-weight: 600;
}

.legend-modal__input,
.legend-modal__select {
  width: 100%;
  padding: 0.35rem 0.6rem;
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-sm);
  background: var(--eb-bg);
  color: var(--eb-text);
  font-family: var(--eb-font-mono);
  font-size: 0.875rem;
}

.legend-modal__input:focus,
.legend-modal__select:focus {
  outline: none;
  border-color: rgba(200, 255, 0, 0.4);
}

.legend-modal__threshold-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.legend-modal__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.legend-modal__label {
  color: var(--eb-text-muted);
  font-size: 0.75rem;
}

.legend-modal__error {
  margin: 0;
  color: var(--eb-danger);
  font-size: 0.8125rem;
}

.legend-modal__footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 0.5rem;
  border-top: 1px solid var(--eb-border);
}
</style>
