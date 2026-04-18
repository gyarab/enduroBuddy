# Design Spec: Dashboard — editace completed trainingu + Garmin modal

**Datum:** 2026-04-18
**Status:** Schváleno, čeká na implementaci

---

## Kontext a motivace

Athlete dashboard (Vue SPA, `AthleteView.vue` + `WeekCard.vue`) zobrazuje týdenní tréninky v tabulce s inline editací. Plánovaná část funguje kompletně. Chybí dvě funkce:

1. **Editace completed trainingu** — inline editace completed polí (km, čas, HR, poznámky) funguje jen pokud completed záznam *už existuje* v databázi. Pokud den má planned training ale žádný completed záznam, pole nejsou klikatelná a nelze vytvořit nový záznam manuálně.

2. **Garmin Import Modal** — `GarminImportModal.vue` je plně implementovaný (připojení Garmin účtu, sync za rozsah datumů, upload FIT souborů), ale není přístupný z `AthleteView` — chybí tlačítko a mount komponenty.

---

## Existující infrastruktura (co se nemění)

| Komponenta | Soubor | Stav |
|-----------|--------|------|
| `WeekCard` | `components/training/WeekCard.vue` | Hotovo — inline edit planned, Garmin week-sync button |
| `GarminImportModal` | `components/training/GarminImportModal.vue` | Hotovo — nepoužívá se |
| `CompletedEditor` | `components/training/CompletedEditor.vue` | Hotovo — nepoužívá se v WeekCard |
| `useGarminImport` | `composables/useGarminImport.ts` | Hotovo |
| Backend API | `PATCH /api/v1/training/completed/{planned_id}/` | Hotovo — vytváří záznam pokud neexistuje |
| Dashboard flags | `DashboardPayload.flags.can_edit_completed` | Hotovo — řídí oprávnění |

---

## Návrh — Editace completed trainingu

### Chování

Uživatel klikne na buňku km/čas/HR/poznámky v řádku dne který má planned training ale žádný completed záznam → otevře se inline editor → uloží → vytvoří se nový `CompletedTraining` záznam přes backend.

Podmínky pro editaci:
- `dashboard.flags.can_edit_completed === true` (globální oprávnění)
- Den má alespoň jeden planned training (ne second-phase)
- Žádná linked Garmin aktivita (ta je read-only)
- Coach kontext (`editorContext === "coach"`) → zakázáno

### API chování

`PATCH /api/v1/training/completed/{planned_id}/` vytváří záznam pokud neexistuje (get_or_create). Planned training ID se použije jako klíč pro vytvoření i aktualizaci — žádná změna backendu není potřeba.

### Po uložení

Optimistický `patchCompletedRow` ve store nenajde řádek (completed_rows je prázdné), takže po úspěšném *vytvoření nového* záznamu se provede silent reload dashboardu, aby se zobrazila aktuální data včetně server-assigned ID.

---

## Návrh — Garmin Import Modal

### Chování

Tlačítko "Import" se zobrazí v pravém horním rohu dashboardu (nad `MonthSummaryBar`) pokud `authStore.user?.capabilities.garmin_connect_enabled === true`. Klik otevře `GarminImportModal`.

Modal umožňuje:
- Připojit/odpojit Garmin účet (email + heslo)
- Synchronizovat aktivity za zvolený rozsah (yesterday / last 7 days / last 30 days)
- Nahrát FIT soubor

Po dokončení importu se dashboard tiše reloadne.

### i18n

Klíč `imports.open` (hodnota "Import") již existuje v cs.json i en.json — žádný nový klíč není potřeba.

---

## Vizuální design

Konzistentní s existujícím design systémem:
- Tlačítko: `EbButton variant="ghost"` — nenápadné, nepřebíjí hlavní obsah
- Toolbar div: `justify-content: flex-end` — zarovnání vpravo
- Modal: existující `GarminImportModal` bez vizuálních změn
- Nové completed buňky: stávající `wt__input` styly — bez změny
