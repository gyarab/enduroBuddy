# Dashboard Layout Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign TopNav to CSS Grid with logo+username/month/buttons, replace LegendModal and AthleteManageModal with fixed-position slide panels (LegendPanel right, ManagePanel left), remove NotificationBell, and add auto-save.

**Architecture:** `LegendPanel` is a `position: fixed` right-side drawer (translateX transition); `ManagePanel` is a `position: fixed` left-side drawer. TopNav uses `grid-template-columns: 1fr auto 1fr` so the month label stays geometrically centred. `legendStore.isPanelOpen` relays the legend button click (in TopNav) to the panel mount (in AthleteView). Coach's athlete-legend uses an optional `athleteId` query param on the existing `/api/v1/legend/` endpoint.

**Tech Stack:** Vue 3 Composition API, Pinia, Vitest + @vue/test-utils, scoped CSS with design tokens, inline SVG icons, `setTimeout`-based debounce (no `@vueuse/core`).

---

## File Map

| Status | Path |
|--------|------|
| Create | `frontend/components/layout/LegendPanel.vue` |
| Create | `frontend/components/layout/LegendPanel.test.ts` |
| Create | `frontend/components/coach/ManagePanel.vue` |
| Create | `frontend/components/coach/ManagePanel.test.ts` |
| Modify | `backend/api/views/legend.py` |
| Modify | `frontend/utils/api/legend.ts` |
| Modify | `frontend/stores/legend.ts` |
| Modify | `frontend/i18n/locales/cs.json` |
| Modify | `frontend/i18n/locales/en.json` |
| Rewrite | `frontend/components/layout/TopNav.vue` |
| Rewrite | `frontend/components/layout/TopNav.test.ts` |
| Modify | `frontend/components/coach/CoachSidebar.vue` |
| Modify | `frontend/components/views/dashboard/AthleteView.vue` |
| Modify | `frontend/components/views/dashboard/CoachView.vue` |
| Delete | `frontend/components/layout/NotificationBell.vue` |
| Delete | `frontend/components/layout/LegendModal.vue` |
| Delete | `frontend/components/coach/AthleteManageModal.vue` |

---

## Task 1: Backend legend endpoint + frontend legend.ts + legendStore + i18n

Extend the existing `/api/v1/legend/` endpoint to accept `?athlete_id=X` so a coach can read/write an athlete's legend. Extend the TS API util to pass that param. Add `isPanelOpen` to legendStore. Add all new i18n keys.

**Files:**
- Modify: `backend/api/views/legend.py`
- Modify: `frontend/utils/api/legend.ts`
- Modify: `frontend/stores/legend.ts`
- Modify: `frontend/i18n/locales/cs.json`
- Modify: `frontend/i18n/locales/en.json`
- Test: `backend/api/tests/test_legend_api.py` (create if absent)

---

- [ ] **Step 1: Write failing backend test**

Create `backend/api/tests/test_legend_api.py` (or add to existing if file exists):

```python
# backend/api/tests/test_legend_api.py
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()

class LegendAthleteIdTest(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            username="coach@test.com", password="pass", email="coach@test.com"
        )
        self.coach.profile.is_coach = True
        self.coach.profile.save()
        self.athlete = User.objects.create_user(
            username="ath@test.com", password="pass", email="ath@test.com"
        )
        self.athlete.profile.legend_state = {"zones": {"z1": {"from": "100", "to": "120"}}}
        self.athlete.profile.save()

    def test_coach_can_get_athlete_legend(self):
        self.client.force_login(self.coach)
        resp = self.client.get(
            f"/api/v1/legend/?athlete_id={self.athlete.id}"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["state"]["zones"]["z1"]["from"], "100")

    def test_athlete_cannot_get_others_legend(self):
        self.client.force_login(self.athlete)
        resp = self.client.get(
            f"/api/v1/legend/?athlete_id={self.coach.id}"
        )
        self.assertEqual(resp.status_code, 403)

    def test_invalid_athlete_id_returns_404(self):
        self.client.force_login(self.coach)
        resp = self.client.get("/api/v1/legend/?athlete_id=999999")
        self.assertEqual(resp.status_code, 404)
```

- [ ] **Step 2: Run test to confirm it fails**

```
cd backend && python manage.py test api.tests.test_legend_api -v 2
```
Expected: FAIL — endpoint doesn't accept athlete_id yet.

- [ ] **Step 3: Extend the backend legend view**

Full replacement of `backend/api/views/legend.py`:

```python
from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from dashboard.api import json_error
from dashboard.texts import ApiText
from dashboard.views_shared import sanitize_legend_state

User = get_user_model()


@login_required
@require_http_methods(["GET", "POST"])
def legend(request):
    profile = request.user.profile

    athlete_id_raw = request.GET.get("athlete_id")
    if athlete_id_raw is not None:
        if not profile.is_coach:
            return json_error("Only coaches can access athlete legends.", status=403)
        try:
            athlete_id = int(athlete_id_raw)
            target_user = User.objects.get(pk=athlete_id)
            profile = target_user.profile
        except (ValueError, User.DoesNotExist):
            return json_error("Athlete not found.", status=404)

    if request.method == "GET":
        state = sanitize_legend_state(getattr(profile, "legend_state", {}))
        return JsonResponse({"ok": True, "state": state})

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    next_state = sanitize_legend_state(payload.get("state"))
    profile.legend_state = next_state
    profile.save(update_fields=["legend_state"])
    return JsonResponse({"ok": True, "state": next_state})
```

- [ ] **Step 4: Run backend tests**

```
cd backend && python manage.py test api.tests.test_legend_api -v 2
```
Expected: 3 PASS.

- [ ] **Step 5: Extend frontend legend.ts**

Full replacement of `frontend/utils/api/legend.ts`:

```typescript
import { apiFetch } from "~/utils/apiFetch";

export type LegendZone = {
  from: string;
  to: string;
};

export type LegendPR = {
  distance: string;
  time: string;
};

export type LegendState = {
  zones: {
    z1: LegendZone;
    z2: LegendZone;
    z3: LegendZone;
    z4: LegendZone;
    z5: LegendZone;
  };
  aerobic_threshold: string;
  anaerobic_threshold: string;
  prs: LegendPR[];
};

export const PR_DISTANCES = [
  "800m",
  "1000m",
  "1 mile",
  "1500m",
  "2 miles",
  "3000m",
  "3k",
  "5000m",
  "5k",
  "10000m",
  "10k",
  "Půlmaraton",
  "Maraton",
] as const;

export async function fetchLegend(athleteId?: number) {
  const qs = athleteId != null ? `?athlete_id=${athleteId}` : "";
  return apiFetch<{ ok: boolean; state: LegendState }>(`/legend/${qs}`);
}

export async function saveLegend(state: LegendState, athleteId?: number) {
  const qs = athleteId != null ? `?athlete_id=${athleteId}` : "";
  return apiFetch<{ ok: boolean; state: LegendState }>(`/legend/${qs}`, {
    method: "POST",
    body: { state },
  });
}
```

- [ ] **Step 6: Add `isPanelOpen` to legendStore**

Full replacement of `frontend/stores/legend.ts`:

```typescript
import { ref } from "vue";
import { defineStore } from "pinia";

import { fetchLegend, saveLegend, type LegendState } from "~/utils/api/legend";

export const useLegendStore = defineStore("legend", () => {
  const state = ref<LegendState | null>(null);
  const isLoading = ref(false);
  const isSaving = ref(false);
  const error = ref("");
  const isPanelOpen = ref(false);

  async function load() {
    if (state.value !== null) return;
    isLoading.value = true;
    error.value = "";
    try {
      const data = await fetchLegend();
      state.value = data.state;
    } catch {
      error.value = "Nepodařilo se načíst legendu.";
    } finally {
      isLoading.value = false;
    }
  }

  async function save(nextState: LegendState) {
    isSaving.value = true;
    error.value = "";
    try {
      const data = await saveLegend(nextState);
      state.value = data.state;
    } catch {
      error.value = "Nepodařilo se uložit legendu.";
      throw error.value;
    } finally {
      isSaving.value = false;
    }
  }

  return { state, isLoading, isSaving, error, isPanelOpen, load, save };
});
```

- [ ] **Step 7: Add i18n keys to cs.json**

Under the `"legend"` object, add after `"loadError"`:
```json
"panelTitle": "Moje legenda",
"panelSubtitle": "Upravuje trenér",
"panelAthleteTitle": "Legenda — {name}",
"panelAthleteSubtitle": "Upravuje trenér · vidí sportovec",
"autoSave": "Změny se ukládají automaticky",
"saving": "Ukládám..."
```

Under `"topNav"`, add:
```json
"myPlan": "Můj plán"
```

Under `"sidebar"`, add:
```json
"manageAthletes": "Správa svěřenců"
```

Add new top-level key group:
```json
"managePanel": {
  "title": "Správa svěřenců",
  "summary": "{total} celkem · {active} aktivní",
  "athletes": "Svěřenci",
  "invite": "Pozvat",
  "requests": "Žádosti",
  "autoSave": "Změny se ukládají automaticky",
  "codeHint": "Sdílej tento kód s atlety. Kód zůstává stále stejný."
}
```

Add:
```json
"coachToolbar": {
  "legendBtn": "Legenda atleta"
}
```

- [ ] **Step 8: Mirror keys in en.json**

Under `"legend"`:
```json
"panelTitle": "My legend",
"panelSubtitle": "Edited by coach",
"panelAthleteTitle": "Legend — {name}",
"panelAthleteSubtitle": "Edited by coach · seen by athlete",
"autoSave": "Changes are saved automatically",
"saving": "Saving..."
```

Under `"topNav"`:
```json
"myPlan": "My plan"
```

Under `"sidebar"`:
```json
"manageAthletes": "Manage athletes"
```

New group:
```json
"managePanel": {
  "title": "Manage athletes",
  "summary": "{total} total · {active} active",
  "athletes": "Athletes",
  "invite": "Invite",
  "requests": "Requests",
  "autoSave": "Changes are saved automatically",
  "codeHint": "Share this code with athletes. The code stays the same."
}
```

Add:
```json
"coachToolbar": {
  "legendBtn": "Athlete legend"
}
```

- [ ] **Step 9: Run frontend type-check and tests**

```
cd frontend && npx tsc --noEmit && npm test
```
Expected: 0 TypeScript errors, all existing tests green.

- [ ] **Step 10: Commit**

```
git add backend/api/views/legend.py backend/api/tests/test_legend_api.py \
  frontend/utils/api/legend.ts frontend/stores/legend.ts \
  frontend/i18n/locales/cs.json frontend/i18n/locales/en.json
git commit -m "feat: extend legend API for coach-athlete context, add legendStore.isPanelOpen, add i18n keys"
```

---

## Task 2: Create LegendPanel.vue

A fixed-position right-side slide panel. Loads legend data on open, auto-saves with 800ms debounce on any input change. Athlete view is read-only; coach view is editable.

**Files:**
- Create: `frontend/components/layout/LegendPanel.vue`
- Create: `frontend/components/layout/LegendPanel.test.ts`

---

- [ ] **Step 1: Write failing test**

Create `frontend/components/layout/LegendPanel.test.ts`:

```typescript
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LegendPanel from "@/components/layout/LegendPanel.vue";

vi.mock("~/utils/api/legend", () => ({
  fetchLegend: vi.fn().mockResolvedValue({
    state: {
      zones: {
        z1: { from: "100", to: "120" },
        z2: { from: "121", to: "140" },
        z3: { from: "141", to: "160" },
        z4: { from: "161", to: "175" },
        z5: { from: "176", to: "190" },
      },
      aerobic_threshold: "150",
      anaerobic_threshold: "170",
      prs: [],
    },
  }),
  saveLegend: vi.fn().mockResolvedValue({ state: {} }),
  PR_DISTANCES: ["5k", "10k", "Maraton"],
}));

describe("LegendPanel", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("is hidden when open=false", () => {
    const wrapper = mount(LegendPanel, {
      props: { open: false, title: "Moje legenda", subtitle: "Upravuje trenér", editable: false },
    });
    expect(wrapper.find(".legend-panel--open").exists()).toBe(false);
  });

  it("adds open class when open=true", async () => {
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Moje legenda", subtitle: "Upravuje trenér", editable: false },
    });
    await vi.runAllTimersAsync();
    expect(wrapper.find(".legend-panel--open").exists()).toBe(true);
  });

  it("shows title and subtitle", () => {
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Moje legenda", subtitle: "Upravuje trenér", editable: false },
    });
    expect(wrapper.find(".legend-panel__title").text()).toBe("Moje legenda");
    expect(wrapper.find(".legend-panel__subtitle").text()).toBe("Upravuje trenér");
  });

  it("emits close when close button is clicked", async () => {
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Legenda", subtitle: "Sub", editable: true },
    });
    await wrapper.find(".legend-panel__close").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("calls saveLegend after debounce when editable and input changes", async () => {
    const { saveLegend } = await import("~/utils/api/legend");
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Legenda", subtitle: "Sub", editable: true },
    });
    await vi.runAllTimersAsync(); // let load complete

    const input = wrapper.find<HTMLInputElement>(".legend-panel__input");
    await input.setValue("999");
    await wrapper.vm.$nextTick();

    expect(saveLegend).not.toHaveBeenCalled();
    vi.advanceTimersByTime(800);
    await wrapper.vm.$nextTick();
    expect(saveLegend).toHaveBeenCalled();
  });

  it("does NOT auto-save when editable=false", async () => {
    const { saveLegend } = await import("~/utils/api/legend");
    const wrapper = mount(LegendPanel, {
      props: { open: true, title: "Legenda", subtitle: "Sub", editable: false },
    });
    await vi.runAllTimersAsync();

    // Inputs should not be present when read-only
    expect(wrapper.find(".legend-panel__input").exists()).toBe(false);
    expect(saveLegend).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run test to confirm it fails**

```
cd frontend && npm test -- LegendPanel.test
```
Expected: FAIL — component doesn't exist.

- [ ] **Step 3: Create LegendPanel.vue**

Create `frontend/components/layout/LegendPanel.vue`:

```vue
<script setup lang="ts">
import { ref, watch } from "vue";

import { fetchLegend, saveLegend, PR_DISTANCES, type LegendPR, type LegendState } from "~/utils/api/legend";

const props = defineProps<{
  open: boolean;
  title: string;
  subtitle: string;
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
let saveTimer: ReturnType<typeof setTimeout> | null = null;

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    isLoading.value = true;
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
    } finally {
      isLoading.value = false;
    }
  }
);

watch(
  draft,
  () => {
    if (!props.open || !props.editable) return;
    if (saveTimer !== null) clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      isSaving.value = true;
      try {
        await saveLegend(draft.value, props.athleteId);
      } finally {
        isSaving.value = false;
      }
    }, 800);
  },
  { deep: true }
);

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
        <div class="legend-panel__subtitle">{{ subtitle }}</div>
      </div>
      <button class="legend-panel__close" type="button" :aria-label="t('legend.close')" @click="emit('close')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <div v-if="isLoading" class="legend-panel__loading">
      <span>{{ t("legend.loadError") }}</span>
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
                <input v-if="editable" v-model="draft.zones[zone].from" class="legend-panel__input" />
                <span v-else>{{ draft.zones[zone].from || "—" }}</span>
              </td>
              <td>
                <input v-if="editable" v-model="draft.zones[zone].to" class="legend-panel__input" />
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
            <input v-if="editable" v-model="draft.aerobic_threshold" class="legend-panel__input" />
            <span v-else>{{ draft.aerobic_threshold || "—" }}</span>
          </label>
          <label class="legend-panel__field">
            <span class="legend-panel__label">{{ t("legend.anaerobicThreshold") }}</span>
            <input v-if="editable" v-model="draft.anaerobic_threshold" class="legend-panel__input" />
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
              <th v-if="editable" />
            </tr>
          </thead>
          <tbody>
            <tr v-for="(pr, index) in draft.prs" :key="index">
              <td>
                <select v-if="editable" v-model="(draft.prs[index] as LegendPR).distance" class="legend-panel__select">
                  <option v-for="d in PR_DISTANCES" :key="d" :value="d">{{ d }}</option>
                </select>
                <span v-else>{{ pr.distance }}</span>
              </td>
              <td>
                <input v-if="editable" v-model="(draft.prs[index] as LegendPR).time" class="legend-panel__input" />
                <span v-else>{{ pr.time }}</span>
              </td>
              <td v-if="editable">
                <button class="legend-panel__remove-btn" type="button" @click="removePr(index)">
                  {{ t("legend.removePr") }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <button v-if="editable" class="legend-panel__add-btn" type="button" @click="addPr">
          {{ t("legend.addPr") }}
        </button>
      </section>
    </div>

    <div class="legend-panel__footer">
      <span v-if="isSaving" class="legend-panel__saving">{{ t("legend.saving") }}</span>
      <span v-else class="legend-panel__autosave">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        {{ t("legend.autoSave") }}
      </span>
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
  color: var(--eb-text-soft);
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
  padding: 0.75rem 1.125rem;
  border-top: 1px solid var(--eb-border);
  flex-shrink: 0;
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
</style>
```

- [ ] **Step 4: Run tests**

```
cd frontend && npm test -- LegendPanel.test
```
Expected: 5 PASS.

- [ ] **Step 5: Run full test suite**

```
cd frontend && npm test
```
Expected: all tests green.

- [ ] **Step 6: Commit**

```
git add frontend/components/layout/LegendPanel.vue frontend/components/layout/LegendPanel.test.ts
git commit -m "feat: add LegendPanel side panel with auto-save and optional athlete context"
```

---

## Task 3: Create ManagePanel.vue

Fixed-position left-side overlay panel. Two-column layout: 116px vertical menu (Svěřenci / Pozvat / Žádosti) + content area. Replaces `AthleteManageModal`.

**Files:**
- Create: `frontend/components/coach/ManagePanel.vue`
- Create: `frontend/components/coach/ManagePanel.test.ts`

---

- [ ] **Step 1: Write failing test**

Create `frontend/components/coach/ManagePanel.test.ts`:

```typescript
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ManagePanel from "@/components/coach/ManagePanel.vue";

vi.mock("~/utils/api/coach", () => ({
  fetchCoachCode: vi.fn().mockResolvedValue({ coach_join_code: "ABC123" }),
  fetchJoinRequests: vi.fn().mockResolvedValue({ requests: [] }),
  approveJoinRequest: vi.fn().mockResolvedValue({}),
  rejectJoinRequest: vi.fn().mockResolvedValue({}),
  removeAthlete: vi.fn().mockResolvedValue({}),
}));

const athletes = [
  { id: 1, name: "Jan Novák", hidden: false, selected: true, focus: "5k", sort_order: 1 },
  { id: 2, name: "Eva Malá", hidden: true, selected: false, focus: null, sort_order: 2 },
];

describe("ManagePanel", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("is not visible when open=false", () => {
    const wrapper = mount(ManagePanel, {
      props: { open: false, athletes },
    });
    expect(wrapper.find(".manage-panel--open").exists()).toBe(false);
  });

  it("is visible when open=true", () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    expect(wrapper.find(".manage-panel--open").exists()).toBe(true);
  });

  it("shows athletes section by default", () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    expect(wrapper.find(".manage-panel__menu-item--active").text()).toContain("Svěřenci");
    expect(wrapper.find(".manage-content--athletes").exists()).toBe(true);
  });

  it("switches to invite section when menu item is clicked", async () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    const inviteBtn = wrapper
      .findAll(".manage-panel__menu-item")
      .find((el) => el.text().includes("Pozvat"));
    await inviteBtn!.trigger("click");
    expect(wrapper.find(".manage-content--invite").exists()).toBe(true);
  });

  it("emits close when close button is clicked", async () => {
    const wrapper = mount(ManagePanel, {
      props: { open: true, athletes },
    });
    await wrapper.find(".manage-panel__close").trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });
});
```

- [ ] **Step 2: Run test to confirm it fails**

```
cd frontend && npm test -- ManagePanel.test
```
Expected: FAIL — component doesn't exist.

- [ ] **Step 3: Create ManagePanel.vue**

Create `frontend/components/coach/ManagePanel.vue`:

```vue
<script setup lang="ts">
import { ref, watch } from "vue";

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
const removeConfirmName = ref("");
const isRemoving = ref(false);

const visibleCount = computed(() => props.athletes.filter((a) => !a.hidden).length);
const totalCount = computed(() => props.athletes.length);

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
                  class="manage-panel__icon-btn manage-panel__icon-btn--danger"
                  type="button"
                  :title="t('removeAthlete.button')"
                  @click="startRemove(athlete.id)"
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
                  <button class="manage-panel__btn manage-panel__btn--danger" type="button" :disabled="isRemoving" @click="confirmRemove">
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
  color: var(--eb-text-soft);
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
```

- [ ] **Step 4: Run tests**

```
cd frontend && npm test -- ManagePanel.test
```
Expected: 5 PASS.

- [ ] **Step 5: Run full test suite**

```
cd frontend && npm test
```
Expected: all tests green.

- [ ] **Step 6: Commit**

```
git add frontend/components/coach/ManagePanel.vue frontend/components/coach/ManagePanel.test.ts
git commit -m "feat: add ManagePanel left-overlay with Svěřenci/Pozvat/Žádosti sections"
```

---

## Task 4: Rewrite TopNav.vue + TopNav.test.ts

CSS Grid `1fr auto 1fr`. Logo mark + wordmark + username left. Month label centred. Context-sensitive icon buttons right. Remove NotificationBell, LegendModal, GarminImportModal imports (GarminImportModal stays via local state). `legendStore.isPanelOpen` toggled by legend button.

**Files:**
- Rewrite: `frontend/components/layout/TopNav.vue`
- Rewrite: `frontend/components/layout/TopNav.test.ts`

---

- [ ] **Step 1: Write new tests first**

Replace the entire content of `frontend/components/layout/TopNav.test.ts`:

```typescript
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createRouter, createMemoryHistory } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import TopNav from "@/components/layout/TopNav.vue";

vi.mock("@/components/layout/ProfileDropdown.vue", () => ({ default: { template: "<div />" } }));

const mockAuthStore = {
  user: {
    initials: "JN",
    first_name: "Jan",
    last_name: "Novák",
    capabilities: { garmin_connect_enabled: true, coached_athlete_count: 0 },
  },
  isAuthenticated: true,
  isCoach: false,
};
const mockTrainingStore = { selectedMonth: { label: "Červen 2026" } };
const mockCoachStore = { selectedMonth: { label: "Červen 2026" } };
const mockLegendStore = { isPanelOpen: false };

vi.mock("@/stores/auth", () => ({ useAuthStore: vi.fn(() => mockAuthStore) }));
vi.mock("@/stores/training", () => ({ useTrainingStore: vi.fn(() => mockTrainingStore) }));
vi.mock("@/stores/coach", () => ({ useCoachStore: vi.fn(() => mockCoachStore) }));
vi.mock("@/stores/legend", () => ({ useLegendStore: vi.fn(() => mockLegendStore) }));
vi.mock("@/components/training/GarminImportModal.vue", () => ({ default: { template: "<div />" } }));

function makeRouter(path = "/app/dashboard") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/app/dashboard", component: { template: "<div/>" } },
      { path: "/coach/plans", component: { template: "<div/>" } },
    ],
  });
  router.push(path);
  return router;
}

describe("TopNav", () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    mockAuthStore.user = {
      initials: "JN",
      first_name: "Jan",
      last_name: "Novák",
      capabilities: { garmin_connect_enabled: true, coached_athlete_count: 0 },
    };
    mockAuthStore.isAuthenticated = true;
    mockAuthStore.isCoach = false;
    mockTrainingStore.selectedMonth = { label: "Červen 2026" };
    mockCoachStore.selectedMonth = { label: "Červen 2026" };
    mockLegendStore.isPanelOpen = false;
  });

  it("renders logo mark", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-brand__mark").exists()).toBe(true);
  });

  it("shows username from auth store", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-brand__username").text()).toBe("Jan Novák");
  });

  it("shows month label", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-month").text()).toContain("Červen 2026");
  });

  it("shows sync button when garmin_connect_enabled=true", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--sync").exists()).toBe(true);
  });

  it("hides sync button when garmin_connect_enabled=false", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    vi.mocked(useAuthStore).mockReturnValueOnce({
      ...mockAuthStore,
      user: { ...mockAuthStore.user, capabilities: { garmin_connect_enabled: false, coached_athlete_count: 0 } },
    } as any);
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--sync").exists()).toBe(false);
  });

  it("shows legend button in athlete variant", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--legend").exists()).toBe(true);
  });

  it("hides legend button in coach variant", async () => {
    const router = makeRouter("/coach/plans");
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "coach" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--legend").exists()).toBe(false);
  });

  it("shows coach badge when isCoach=true and variant=athlete", async () => {
    const { useAuthStore } = await import("@/stores/auth");
    vi.mocked(useAuthStore).mockReturnValueOnce({ ...mockAuthStore, isCoach: true } as any);
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--coach").exists()).toBe(true);
  });

  it("shows myPlan button in coach variant", async () => {
    const router = makeRouter("/coach/plans");
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "coach" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-btn--myplan").exists()).toBe(true);
  });

  it("shows avatar with initials", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    expect(wrapper.find(".nav-avatar").text()).toBe("JN");
  });

  it("clicking legend button sets legendStore.isPanelOpen = true", async () => {
    const router = makeRouter();
    await router.isReady();
    const wrapper = mount(TopNav, { props: { variant: "athlete" }, global: { plugins: [router, pinia] } });
    await wrapper.find(".nav-btn--legend").trigger("click");
    expect(mockLegendStore.isPanelOpen).toBe(true);
  });
});
```

- [ ] **Step 2: Run test to confirm it fails**

```
cd frontend && npm test -- TopNav.test
```
Expected: multiple failures — wrong CSS classes and structure.

- [ ] **Step 3: Rewrite TopNav.vue**

Replace the full content of `frontend/components/layout/TopNav.vue`:

```vue
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import GarminImportModal from "@/components/training/GarminImportModal.vue";
import ProfileDropdown from "@/components/layout/ProfileDropdown.vue";
import ProfileSettingsModal from "@/components/layout/ProfileSettingsModal.vue";
import { useAuthStore } from "@/stores/auth";
import { useCoachStore } from "@/stores/coach";
import { useLegendStore } from "@/stores/legend";
import { useTrainingStore } from "@/stores/training";

const props = defineProps<{
  variant: "athlete" | "coach";
}>();

const authStore = useAuthStore();
const coachStore = useCoachStore();
const legendStore = useLegendStore();
const trainingStore = useTrainingStore();
const { t } = useI18n();

const isProfileOpen = ref(false);
const isProfileSettingsOpen = ref(false);
const isGarminOpen = ref(false);
const profileRootRef = ref<HTMLElement | null>(null);

const monthLabel = computed(() => {
  if (props.variant === "coach") return coachStore.selectedMonth?.label ?? "";
  return trainingStore.selectedMonth?.label ?? "";
});

const showSync = computed(() => !!authStore.user?.capabilities?.garmin_connect_enabled);
const showCoachBtn = computed(() => authStore.isCoach && props.variant === "athlete");
const showLegendBtn = computed(() => props.variant === "athlete");
const showMyPlanBtn = computed(() => props.variant === "coach");

const username = computed(() => {
  const u = authStore.user;
  if (!u) return "";
  return `${u.first_name ?? ""} ${u.last_name ?? ""}`.trim();
});

function handleDocumentClick(event: MouseEvent) {
  const target = event.target;
  if (!(target instanceof Node)) return;
  if (profileRootRef.value && !profileRootRef.value.contains(target)) {
    isProfileOpen.value = false;
  }
}

function openProfileSettings() {
  isProfileOpen.value = false;
  isProfileSettingsOpen.value = true;
}

function openGarmin() {
  isProfileOpen.value = false;
  isGarminOpen.value = true;
}

onMounted(() => document.addEventListener("click", handleDocumentClick));
onBeforeUnmount(() => document.removeEventListener("click", handleDocumentClick));
</script>

<template>
  <header class="top-nav">
    <!-- Left: logo + username -->
    <div class="nav-left">
      <RouterLink class="nav-brand" :to="variant === 'coach' ? '/coach/plans' : '/app/dashboard'">
        <span class="nav-brand__mark" aria-hidden="true">
          <span /><span /><span />
        </span>
        <span class="nav-brand__text">
          <span class="nav-brand__name">EnduroBuddy</span>
          <span class="nav-brand__username">{{ username }}</span>
        </span>
      </RouterLink>
    </div>

    <!-- Center: month -->
    <div class="nav-center">
      <div class="nav-month">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" class="nav-month__icon">
          <rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        {{ monthLabel }}
      </div>
    </div>

    <!-- Right: action buttons -->
    <div class="nav-right">
      <!-- Coach btn (athlete view, isCoach) -->
      <RouterLink v-if="showCoachBtn" class="nav-btn nav-btn--coach" to="/coach/plans" :title="t('topNav.switchToCoach')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="M16 21l4-4-4-4"/><path d="M20 17H4"/>
        </svg>
        {{ t("topNav.switchToCoach") }}
      </RouterLink>
      <div v-if="showCoachBtn" class="nav-divider" aria-hidden="true" />

      <!-- Sync btn (Garmin enabled) -->
      <button v-if="showSync" class="nav-btn nav-btn--sync" type="button" :title="t('imports.open')" @click="isGarminOpen = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
          <path d="M21 3v5h-5"/>
          <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
          <path d="M3 21v-5h5"/>
        </svg>
      </button>
      <div v-if="showSync" class="nav-divider" aria-hidden="true" />

      <!-- Legend btn (athlete view only) -->
      <button v-if="showLegendBtn" class="nav-btn nav-btn--legend" type="button" :title="t('legend.button')" @click="legendStore.isPanelOpen = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
      </button>

      <!-- Můj plán btn (coach view) -->
      <RouterLink v-if="showMyPlanBtn" class="nav-btn nav-btn--myplan" to="/app/dashboard" :title="t('topNav.myPlan')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M8 3 4 7l4 4"/><path d="M4 7h16"/><path d="M16 21l4-4-4-4"/><path d="M20 17H4"/>
        </svg>
        {{ t("topNav.myPlan") }}
      </RouterLink>
      <div v-if="showMyPlanBtn && showSync" class="nav-divider" aria-hidden="true" />

      <!-- Avatar -->
      <div v-if="authStore.isAuthenticated" ref="profileRootRef" class="nav-profile">
        <button class="nav-avatar" type="button" @click.stop="isProfileOpen = !isProfileOpen">
          {{ authStore.user?.initials || "?" }}
        </button>
        <ProfileDropdown v-if="isProfileOpen" @open-settings="openProfileSettings" @open-garmin="openGarmin" />
      </div>
    </div>
  </header>

  <ProfileSettingsModal :open="isProfileSettingsOpen" @close="isProfileSettingsOpen = false" />
  <GarminImportModal v-if="showSync" :open="isGarminOpen" @close="isGarminOpen = false" />
</template>

<style scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 52px;
  background: var(--eb-bg-elevated, #18181b);
  border-bottom: 1px solid var(--eb-border);
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 1rem;
  padding: 0 20px;
  backdrop-filter: blur(12px);
}

/* Left */
.nav-left {
  display: flex;
  align-items: center;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.nav-brand__mark {
  display: inline-flex;
  align-items: flex-end;
  gap: 0.2rem;
  height: 22px;
  transform: skewX(-6deg);
  flex-shrink: 0;
}

.nav-brand__mark span {
  width: 5px;
  border-radius: 2px;
  background: var(--eb-lime, #c8ff00);
  box-shadow: 0 0 8px rgba(200, 255, 0, 0.2);
}

.nav-brand__mark span:nth-child(1) { height: 38%; opacity: 0.35; }
.nav-brand__mark span:nth-child(2) { height: 65%; opacity: 0.65; }
.nav-brand__mark span:nth-child(3) { height: 100%; }

.nav-brand__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  line-height: 1;
}

.nav-brand__name {
  font-family: 'Syne', var(--eb-font-display, sans-serif);
  font-weight: 700;
  font-size: 15px;
  color: var(--eb-text, #fafafa);
  letter-spacing: -0.3px;
}

.nav-brand__username {
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 400;
  font-size: 10.5px;
  color: var(--eb-text-muted, #71717a);
}

/* Center */
.nav-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-month {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--eb-font-display, 'Outfit', sans-serif);
  font-weight: 600;
  font-size: 14px;
  color: #e4e4e7;
  white-space: nowrap;
}

.nav-month__icon {
  color: #52525b;
}

/* Right */
.nav-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 7px;
}

.nav-divider {
  width: 1px;
  height: 20px;
  background: #2e2e34;
  flex-shrink: 0;
}

/* Icon-only nav button */
.nav-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  border: 1px solid #3f3f46;
  border-radius: 7px;
  background: transparent;
  color: #71717a;
  cursor: pointer;
  flex-shrink: 0;
  text-decoration: none;
  transition: border-color 150ms ease-out, color 150ms ease-out;
  padding: 0;
  width: 32px;
}

.nav-btn:hover {
  border-color: #52525b;
  color: #a1a1aa;
}

/* Sync — green tint */
.nav-btn--sync {
  border-color: #2d5a2d;
  color: #7ecf7e;
  background: rgba(126, 207, 126, 0.06);
}

.nav-btn--sync:hover {
  border-color: #3a6e3a;
  color: #9ade9a;
}

/* Coach badge — lime, has text */
.nav-btn--coach {
  width: auto;
  padding: 0 11px;
  gap: 6px;
  border-color: #4d5e1a;
  background: rgba(200, 255, 0, 0.07);
  color: var(--eb-lime, #c8ff00);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.nav-btn--coach:hover {
  border-color: rgba(200, 255, 0, 0.4);
  background: rgba(200, 255, 0, 0.12);
}

/* Můj plán — blue, has text */
.nav-btn--myplan {
  width: auto;
  padding: 0 11px;
  gap: 6px;
  border-color: rgba(56, 189, 248, 0.3);
  background: rgba(56, 189, 248, 0.07);
  color: var(--eb-blue, #38bdf8);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.nav-btn--myplan:hover {
  border-color: rgba(56, 189, 248, 0.5);
  background: rgba(56, 189, 248, 0.12);
}

/* Avatar */
.nav-profile {
  position: relative;
}

.nav-avatar {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 1px solid #3f3f46;
  border-radius: 50%;
  background: #27272a;
  color: var(--eb-lime, #c8ff00);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-weight: 700;
  font-size: 10px;
  cursor: pointer;
  flex-shrink: 0;
  transition: border-color 150ms ease-out;
}

.nav-avatar:hover {
  border-color: rgba(200, 255, 0, 0.3);
}

@media (max-width: 767px) {
  .top-nav {
    padding: 0 12px;
    gap: 0.5rem;
  }

  .nav-brand__text {
    display: none;
  }

  .nav-month {
    font-size: 13px;
  }
}
</style>
```

- [ ] **Step 4: Run tests**

```
cd frontend && npm test -- TopNav.test
```
Expected: all tests PASS.

- [ ] **Step 5: Run full test suite**

```
cd frontend && npm test
```
Expected: all tests green.

- [ ] **Step 6: Commit**

```
git add frontend/components/layout/TopNav.vue frontend/components/layout/TopNav.test.ts
git commit -m "feat: rewrite TopNav with CSS Grid 1fr/auto/1fr, icon buttons, remove NotificationBell"
```

---

## Task 5: Update CoachSidebar.vue

Add a footer section with the "Správa svěřenců" button. Add `isManageOpen` prop for active state. Add `open-manage` emit.

**Files:**
- Modify: `frontend/components/coach/CoachSidebar.vue`

---

- [ ] **Step 1: Add prop, emit, and footer to CoachSidebar.vue**

In `frontend/components/coach/CoachSidebar.vue`, make these three changes:

**Change 1** — Add `isManageOpen` prop and `open-manage` emit. Replace the props/emits block:

```typescript
// FIND (lines 8–18 approx):
const props = defineProps<{
  athletes: CoachAthlete[];
}>();

const emit = defineEmits<{
  select: [athleteId: number];
  reorder: [athleteIds: number[]];
  toggleHidden: [athleteId: number, hidden: boolean];
  remove: [athleteId: number];
  goToDashboard: [];
}>();

// REPLACE WITH:
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
```

**Change 2** — Add footer to template. After the closing `</div>` of `.coach-sidebar__list` and before `<EbContextMenu`, insert:

```html
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
```

**Change 3** — Add footer CSS. At the end of `<style scoped>`, before `</style>`, add:

```css
.coach-sidebar__footer {
  margin-top: auto;
  padding: 0.75rem 0.75rem 0.5rem;
  border-top: 1px solid var(--eb-border);
}

.coach-sidebar__manage-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.6rem 0.75rem;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--eb-text-muted);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 150ms, color 150ms;
}

.coach-sidebar__manage-btn:hover {
  background: rgba(200, 255, 0, 0.06);
  color: var(--eb-lime, #c8ff00);
}

.coach-sidebar__manage-btn--active {
  background: rgba(200, 255, 0, 0.08);
  color: var(--eb-lime, #c8ff00);
}
```

Also, to make the footer stick to the bottom, the sidebar needs to be a flex column. Update `.coach-sidebar`:

```css
/* Find .coach-sidebar and add: */
.coach-sidebar {
  /* existing styles... */
  display: flex;
  flex-direction: column;
}
```

- [ ] **Step 2: Run TypeScript check**

```
cd frontend && npx tsc --noEmit
```
Expected: 0 errors.

- [ ] **Step 3: Run full test suite**

```
cd frontend && npm test
```
Expected: all tests green.

- [ ] **Step 4: Commit**

```
git add frontend/components/coach/CoachSidebar.vue
git commit -m "feat: add Správa svěřenců footer button to CoachSidebar"
```

---

## Task 6: Update AthleteView.vue

Wire `LegendPanel` to `legendStore.isPanelOpen`. Remove the standalone Garmin import toolbar (sync button is now in TopNav).

**Files:**
- Modify: `frontend/components/views/dashboard/AthleteView.vue`

---

- [ ] **Step 1: Edit AthleteView.vue — script**

**Add import** near top of `<script setup>`:
```typescript
import LegendPanel from "@/components/layout/LegendPanel.vue";
import { useLegendStore } from "@/stores/legend";
```

**Add store**:
```typescript
const legendStore = useLegendStore();
```

**Remove** `isGarminModalOpen` ref (it's no longer used in this view — sync is in TopNav).

- [ ] **Step 2: Edit AthleteView.vue — template**

**Remove** the Garmin toolbar block:
```html
<!-- REMOVE THIS: -->
<div v-if="showGarminImportButton" class="dashboard-view__toolbar">
  <EbButton variant="ghost" @click="isGarminModalOpen = true">
    {{ t("imports.open") }}
  </EbButton>
</div>
```

**Add LegendPanel** at the very end of `<template>`, after the closing `</section>` and after `<GarminImportModal ...>` (remove the GarminImportModal too since it's in TopNav now):

```html
<LegendPanel
  :open="legendStore.isPanelOpen"
  :title="t('legend.panelTitle')"
  :subtitle="t('legend.panelSubtitle')"
  :editable="false"
  @close="legendStore.isPanelOpen = false"
/>
```

**Remove** the `<GarminImportModal v-if="showGarminImportButton" ...>` block from the template (the TopNav handles Garmin now).

- [ ] **Step 3: Edit AthleteView.vue — script cleanup**

Remove `showGarminImportButton` computed (no longer needed) and the `GarminImportModal` import (if not already imported elsewhere). Also remove `EbButton` import if it was only used for the Garmin toolbar.

Check that these imports remain (keep):
```typescript
import MonthBar from "@/components/training/MonthBar.vue";
import MonthSummaryBar from "@/components/training/MonthSummaryBar.vue";
import WeekCard from "@/components/training/WeekCard.vue";
import WeekCardSkeleton from "@/components/training/WeekCardSkeleton.vue";
import EbCard from "@/components/ui/EbCard.vue";
```

- [ ] **Step 4: Run TypeScript check + tests**

```
cd frontend && npx tsc --noEmit && npm test
```
Expected: 0 TS errors, all tests green.

- [ ] **Step 5: Commit**

```
git add frontend/components/views/dashboard/AthleteView.vue
git commit -m "feat: wire LegendPanel to athleteView via legendStore.isPanelOpen, remove garmin toolbar"
```

---

## Task 7: Update CoachView.vue

New simplified toolbar (auto-save focus on blur, no save button). Wire `LegendPanel` (right) and `ManagePanel` (left). Mutual exclusion between panels. Remove `AthleteManageModal`.

**Files:**
- Modify: `frontend/components/views/dashboard/CoachView.vue`

---

- [ ] **Step 1: Update imports and refs**

In `frontend/components/views/dashboard/CoachView.vue`:

**Remove imports:**
```typescript
import AthleteManageModal from "@/components/coach/AthleteManageModal.vue";
import { RouterLink, useRouter } from "vue-router";
```

**Add imports:**
```typescript
import LegendPanel from "@/components/layout/LegendPanel.vue";
import ManagePanel from "@/components/coach/ManagePanel.vue";
import { useRouter } from "vue-router";
```

**Replace refs and handler for manage:**
Remove `isManageOpen = ref(false)` and `startRemoveId = ref(...)`. Replace with:
```typescript
const isManageOpen = ref(false);
const isLegendOpen = ref(false);
```

**Update `openManageModal`** (no longer needs `coachStore.loadAthletes` as separate step — ManagePanel loads lazily):
```typescript
function openManage() {
  void coachStore.loadAthletes();
  isLegendOpen.value = false;
  isManageOpen.value = true;
}

function openLegend() {
  isManageOpen.value = false;
  isLegendOpen.value = true;
}
```

**Remove** unused handlers: `handleModalAutoSave`, `handleSidebarRemove` (its modal trigger part), `handleAthleteRemoved` (move into `ManagePanel`'s `@athlete-removed` handler inline).

**Update `saveFocus`** to auto-save on blur (fire-and-forget, no `isSavingFocus` state needed):
```typescript
async function saveFocus() {
  await coachStore.saveFocus(focusDraft.value);
}
```
Remove `isSavingFocus = ref(false)`.

- [ ] **Step 2: Rewrite the template**

Replace the entire `<template>` section of `CoachView.vue`:

```html
<template>
  <section class="coach-view">
    <!-- Sidebar (200px) -->
    <aside class="coach-view__sidebar">
      <CoachSidebar
        :athletes="coachStore.athletes"
        :is-manage-open="isManageOpen"
        @select="handleSidebarSelect"
        @open-manage="openManage"
        @reorder="handleSidebarReorder"
        @toggle-hidden="handleToggleHidden"
        @remove="handleSidebarRemove"
        @go-to-dashboard="handleGoToDashboard"
      />
    </aside>

    <!-- Main content area -->
    <div class="coach-view__main">
      <!-- Toolbar -->
      <div class="coach-toolbar">
        <template v-if="coachStore.selectedAthlete">
          <span class="coach-toolbar__name">{{ coachStore.selectedAthlete.name }}</span>
          <div class="coach-toolbar__divider" aria-hidden="true" />
          <div class="coach-toolbar__focus-pill">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            <input
              v-model="focusDraft"
              class="coach-toolbar__focus-input"
              maxlength="10"
              :placeholder="t('coachView.focus')"
              @blur="saveFocus"
            />
          </div>
        </template>
        <template v-else>
          <span class="coach-toolbar__workspace">{{ t("coachView.workspace") }}</span>
        </template>

        <div class="coach-toolbar__spacer" />

        <button
          v-if="coachStore.selectedAthlete"
          class="coach-toolbar__legend-btn"
          :class="{ 'coach-toolbar__legend-btn--active': isLegendOpen }"
          type="button"
          @click="openLegend"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
          </svg>
          {{ t("coachToolbar.legendBtn") }}
        </button>
      </div>

      <!-- Content -->
      <div v-if="coachStore.isLoading" class="coach-view__loading">
        <WeekCardSkeleton v-for="index in 3" :key="`coach-skeleton-${index}`" />
      </div>

      <EbCard v-else-if="coachStore.errorMessage" class="coach-card">
        <h1 class="coach-card__title">{{ t("coachView.loadErrorTitle") }}</h1>
        <p class="coach-card__text">{{ coachStore.errorMessage }}</p>
      </EbCard>

      <EbCard v-else-if="!coachStore.selectedAthlete" class="coach-card coach-card--empty">
        <h1 class="coach-card__title">{{ t("coachView.noAthletesTitle") }}</h1>
        <p class="coach-card__text">{{ t("coachView.noAthletesText") }}</p>
      </EbCard>

      <template v-else>
        <MonthSummaryBar v-if="coachStore.summary" :summary="coachStore.summary" />
        <div class="coach-view__weeks">
          <WeekCard
            v-for="(week, idx) in coachStore.weeks"
            :key="week.id"
            :ref="(el) => { if (el) weekCardRefs[idx] = el as InstanceType<typeof WeekCard> }"
            :week="week"
            editor-context="coach"
            :active-cursor="cursorForWeek(idx)"
            @navigate-out-next="(p) => handleNavOut('next', idx, p)"
            @navigate-out-prev="(p) => handleNavOut('prev', idx, p)"
            @exit-edit="handleExitEdit"
            @exit-edit-move="(dir) => handleExitEditMove(dir)"
            @cursor-set="(p) => handleCursorSet(idx, p)"
          />
        </div>
      </template>
    </div>
  </section>

  <MonthBar
    v-if="coachStore.selectedAthlete"
    :months="coachStore.navigation?.available ?? []"
    :active-month="coachStore.selectedMonth?.value"
    :adding="isAddingMonth"
    @select="handleMonthSelect"
    @add-month="handleAddMonth"
  />

  <!-- Panels -->
  <ManagePanel
    :open="isManageOpen"
    :athletes="coachStore.managedAthletes"
    @close="isManageOpen = false"
    @toggle-hidden="handleToggleHidden"
    @athlete-removed="(id) => void coachStore.loadAthletes()"
    @go-to-dashboard="handleGoToDashboard"
  />

  <LegendPanel
    v-if="coachStore.selectedAthlete"
    :open="isLegendOpen"
    :title="t('legend.panelAthleteTitle', { name: coachStore.selectedAthlete.name })"
    :subtitle="t('legend.panelAthleteSubtitle')"
    :athlete-id="coachStore.selectedAthlete.id"
    :editable="true"
    @close="isLegendOpen = false"
  />
</template>
```

- [ ] **Step 3: Rewrite the CSS**

Replace the `<style scoped>` section. Keep the coach-card and week-card styles; replace the layout and toolbar styles:

```css
<style scoped>
.coach-view {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 0;
  min-height: calc(100vh - 52px - 3rem);
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-lg);
  overflow: hidden;
  background: var(--eb-surface);
}

.coach-view__sidebar {
  border-right: 1px solid var(--eb-border);
}

.coach-view__main {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 0;
  align-content: start;
}

/* Toolbar */
.coach-toolbar {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0 1rem;
  height: 48px;
  border-bottom: 1px solid #1e1e22;
  background: #111113;
  flex-shrink: 0;
}

.coach-toolbar__name {
  font-family: var(--eb-font-display, 'Outfit', sans-serif);
  font-size: 15px;
  font-weight: 700;
  color: var(--eb-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 14rem;
}

.coach-toolbar__divider {
  width: 1px;
  height: 18px;
  background: #2e2e34;
  flex-shrink: 0;
}

.coach-toolbar__focus-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.2rem 0.65rem;
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.08);
  color: var(--eb-blue, #38bdf8);
}

.coach-toolbar__focus-input {
  width: 6rem;
  border: 0;
  background: transparent;
  color: var(--eb-blue, #38bdf8);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  outline: none;
}

.coach-toolbar__focus-input::placeholder {
  color: rgba(56, 189, 248, 0.4);
  text-transform: uppercase;
}

.coach-toolbar__workspace {
  font-family: var(--eb-font-display, 'Outfit', sans-serif);
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--eb-text);
}

.coach-toolbar__spacer {
  flex: 1;
}

.coach-toolbar__legend-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0 0.75rem;
  height: 30px;
  border: 1px solid var(--eb-border);
  border-radius: 6px;
  background: transparent;
  color: var(--eb-text-muted);
  font-family: var(--eb-font-body, 'Nunito', sans-serif);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 150ms, color 150ms;
}

.coach-toolbar__legend-btn:hover,
.coach-toolbar__legend-btn--active {
  border-color: rgba(200, 255, 0, 0.3);
  color: var(--eb-lime, #c8ff00);
}

/* Content */
.coach-view__loading,
.coach-view__weeks {
  display: grid;
  gap: 1rem;
  padding: 1rem;
}

/* Cards */
.coach-card {
  padding: 1.5rem;
}

.coach-card__title {
  margin: 0;
  font-family: var(--eb-font-display, 'Outfit', sans-serif);
  font-size: 1.25rem;
  font-weight: 700;
}

.coach-card__text {
  margin: 0.75rem 0 0;
  color: var(--eb-text-muted);
  font-size: 0.875rem;
}

.coach-card--empty {
  padding: 2.5rem 1.5rem;
  text-align: center;
}

@media (max-width: 767px) {
  .coach-view {
    grid-template-columns: 1fr;
  }

  .coach-view__sidebar {
    display: none;
  }
}
</style>
```

- [ ] **Step 4: Handle removed `handleSidebarRemove` dependency**

The `handleSidebarRemove` function previously opened the `AthleteManageModal`. Now the manage panel is always available via `openManage()`. Simplify:

```typescript
async function handleSidebarRemove(_athleteId: number) {
  openManage();
}
```

Remove `startRemoveId` ref — it's no longer needed (remove confirm is inside `ManagePanel`).

- [ ] **Step 5: Run TypeScript check + tests**

```
cd frontend && npx tsc --noEmit && npm test
```
Expected: 0 TS errors, all tests green.

- [ ] **Step 6: Commit**

```
git add frontend/components/views/dashboard/CoachView.vue
git commit -m "feat: rebuild CoachView with new sidebar/toolbar/legend/manage panel layout"
```

---

## Task 8: Delete old components

Remove `NotificationBell.vue`, `LegendModal.vue`, and `AthleteManageModal.vue`. These are no longer imported anywhere after Tasks 4, 6, and 7.

**Files:**
- Delete: `frontend/components/layout/NotificationBell.vue`
- Delete: `frontend/components/layout/LegendModal.vue`
- Delete: `frontend/components/coach/AthleteManageModal.vue`

---

- [ ] **Step 1: Verify no remaining imports**

```
cd frontend && grep -r "NotificationBell\|LegendModal\|AthleteManageModal" --include="*.vue" --include="*.ts" src/ components/ views/ pages/ stores/ utils/ || echo "None found"
```

Expected output: "None found" (or the grep returns nothing). If any files are listed, open them and remove the stale import/usage before deleting.

- [ ] **Step 2: Delete the files**

```
git rm frontend/components/layout/NotificationBell.vue
git rm frontend/components/layout/LegendModal.vue
git rm frontend/components/coach/AthleteManageModal.vue
```

- [ ] **Step 3: Run TypeScript check + tests**

```
cd frontend && npx tsc --noEmit && npm test
```
Expected: 0 TS errors, all tests green.

- [ ] **Step 4: Run backend tests**

```
cd backend && python manage.py test --verbosity=2
```
Expected: all backend tests pass.

- [ ] **Step 5: Final commit**

```
git commit -m "chore: delete NotificationBell, LegendModal, AthleteManageModal (replaced by panels)"
```

---

## Post-implementation checklist

After all tasks are committed, update `CLAUDE.md` under "Aktivní plány a změny":

```markdown
### 2026-05-18 — Dashboard Layout Redesign ✅ KOMPLETNÍ

**Spec:** `docs/superpowers/specs/2026-05-18-dashboard-layout-redesign.md`
**Plán:** `docs/superpowers/plans/2026-05-18-dashboard-layout-redesign.md`

- TopNav: CSS Grid `1fr auto 1fr`, logo mark + username left, month label always centered
- Icon buttons: coach badge (lime), sync (green, Garmin-only), legend (athlete only), Můj plán (coach only)
- LegendPanel: `position:fixed` right drawer (340px, translateX transition), auto-save 800ms debounce
- ManagePanel: `position:fixed` left drawer (480px), two-column layout, Svěřenci/Pozvat/Žádosti
- AthleteView: wired to `legendStore.isPanelOpen`, no own Garmin toolbar
- CoachView: 200px sidebar + 48px toolbar with inline focus editing + mutual panel exclusion
- Backend: `/api/v1/legend/?athlete_id=X` for coach-athlete legend access
- Deleted: NotificationBell.vue, LegendModal.vue, AthleteManageModal.vue
```
