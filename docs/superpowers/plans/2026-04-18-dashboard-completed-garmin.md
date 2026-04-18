# Implementation Plan: Dashboard — editace completed trainingu + Garmin modal

**Datum:** 2026-04-18
**Spec:** `docs/superpowers/specs/2026-04-18-dashboard-completed-garmin.md`
**Status:** Schváleno, čeká na implementaci

---

## Soubory k úpravě

- `frontend/src/components/training/WeekCard.vue`
- `frontend/src/views/dashboard/AthleteView.vue`

---

## Změna 1: WeekCard.vue — editace completed bez existujícího záznamu

### Kořenový problém (3 místa)

**A. `canEditCompleted(slot)` (line ~263)** vrací `false` když `slot.completed[0]` neexistuje → click handlery v šabloně nedělají nic.

**B. `openEdit()` (line ~147-162)** — `completedId` je `null` když žádný completed záznam neexistuje → v `saveRow` se completed neuloží.

**C. Šablona (lines ~408, 417, 427, 437, 447)** — inputy se zobrazí jen když `getEdit(slot.date)!.completedId` je truthy. (Toto je správné — stačí opravit A a B.)

### Kroky

**Krok 1 — přidat computed za `showGarminSync`:**
```ts
const canEditCompletedGlobal = computed(
  () => props.editorContext !== "coach" && !!trainingStore.dashboard?.flags.can_edit_completed,
);
```

**Krok 2 — přepsat `canEditCompleted(slot)`:**
```ts
function canEditCompleted(slot: DaySlot): boolean {
  if (!canEditCompletedGlobal.value) return false;
  const c = slot.completed[0];
  if (c) return c.editable && !c.has_linked_activity;
  const planned = slot.planned.find((r) => !r.is_second_phase) ?? null;
  return planned !== null;
}
```

**Krok 3 — opravit `openEdit()`:**

Nahradit:
```ts
const canEditCompleted = completed ? (completed.editable && !completed.has_linked_activity) : false;
// ...
if (!canEditPlanned && !canEditCompleted) return;
// ...
completedId: canEditCompleted ? (completed?.id ?? null) : null,
```

Za:
```ts
const completedEditable = completed
  ? (completed.editable && !completed.has_linked_activity)
  : (canEditCompletedGlobal.value && planned !== null);
const completedId = completedEditable
  ? (completed?.id ?? planned?.id ?? null)
  : null;
// ...
if (!canEditPlanned && !completedEditable) return;
// ...
completedId: completedId,
```

> `PATCH /training/completed/{planned_id}/` vytváří záznam pokud neexistuje — `saveRow` nevyžaduje žádnou změnu.

**Krok 4 — silent reload po vytvoření nového záznamu:**

V `saveRow()`, za `flashRow(slot.date)` přidat:
```ts
if (edit.completedId && slot.completed.length === 0) {
  await trainingStore.loadDashboard(trainingStore.selectedMonthValue, { silent: true });
}
```

---

## Změna 2: AthleteView.vue — Garmin Import Modal

**Krok 1 — přidat importy:**
```ts
import GarminImportModal from "@/components/training/GarminImportModal.vue";
import { useAuthStore } from "@/stores/auth";
```

**Krok 2 — přidat store, stav a computed:**
```ts
const authStore = useAuthStore();
const isGarminModalOpen = ref(false);

const showGarminImportButton = computed(
  () => !!authStore.user?.capabilities.garmin_connect_enabled,
);
```

**Krok 3 — tlačítko v šabloně** (dovnitř `<template v-else>`, nad `<MonthSummaryBar>`):
```html
<div v-if="showGarminImportButton" class="dashboard-view__toolbar">
  <EbButton variant="ghost" @click="isGarminModalOpen = true">
    {{ t("imports.open") }}
  </EbButton>
</div>
```

**Krok 4 — mount modal** (na konec šablony, mimo v-if/v-else bloky):
```html
<GarminImportModal
  v-if="showGarminImportButton"
  :open="isGarminModalOpen"
  @close="isGarminModalOpen = false"
/>
```

**Krok 5 — přidat CSS:**
```css
.dashboard-view__toolbar {
  display: flex;
  justify-content: flex-end;
}
```

---

## Ověření

### Completed editing
1. Den s planned trainingem ale bez completed záznamu → klik na km buňku → otevře se inline edit
2. Zadat hodnotu, počkat 1s nebo focusout → `PATCH /api/v1/training/completed/{planned_id}/` v network tabu
3. Řádek se reloadne a zobrazí zadaná data
4. Den bez planned trainingu → pole nejsou klikatelná

### Garmin modal
1. `garmin_connect_enabled: true` → tlačítko "Import" nahoře vpravo
2. Klik → modal se otevře
3. Zavřít → modal se zavře
4. `garmin_connect_enabled: false` → tlačítko není vidět
