# Feature Parity — chybějící tlačítka a funkce

**Datum:** 2026-04-10
**Status:** Schváleno, připraveno k implementaci
**Kontext:** Vue SPA obsahuje ~70 % funkcí původní Django aplikace. Tento spec pokrývá zbývajících 30 %.

---

## Přehled změn

### Backend — nové API endpointy

| Endpoint | Metoda | Účel |
|----------|--------|------|
| `/api/v1/legend/` | GET | Načtení legend state (HR zóny, prahy, PRs) pro přihlášeného uživatele |
| `/api/v1/legend/` | POST | Uložení legend state |
| `/api/v1/coach/code/` | GET | Vrátí `coach_join_code` trenéra (generuje ho pokud chybí) |
| `/api/v1/coach/join-requests/` | GET | Seznam čekajících join requestů (pro trenéra) |
| `/api/v1/coach/join-requests/{id}/approve/` | POST | Schválení join requestu |
| `/api/v1/coach/join-requests/{id}/reject/` | POST | Zamítnutí join requestu |
| `/api/v1/coach/join-request/` | POST | Athlete žádá o trenéra pomocí coach kódu |
| `/api/v1/coach/athletes/{id}/` | DELETE | Odebrání atleta (vyžaduje `confirm_name`) |
| `/api/v1/training/months/` | POST | Vytvoření dalšího měsíce (athlete nebo coach pro atleta) |
| `/api/v1/imports/garmin/week-sync/` | POST | Garmin sync pro konkrétní týden (`week_start: YYYY-MM-DD`) |
| `/api/v1/invites/{token}/` | GET | Informace o skupinové pozvánce (je platná, kdo ji vytvořil) |
| `/api/v1/invites/{token}/accept/` | POST | Přijetí skupinové pozvánky |

---

## Detail: Legend management

### Data structure (JSONField na Profile)
```json
{
  "zones": {
    "z1": { "from": "100", "to": "130" },
    "z2": { "from": "131", "to": "148" },
    "z3": { "from": "149", "to": "163" },
    "z4": { "from": "164", "to": "174" },
    "z5": { "from": "175", "to": "190" }
  },
  "aerobic_threshold": "148",
  "anaerobic_threshold": "163",
  "prs": [
    { "distance": "5k", "time": "20:15" },
    { "distance": "Maraton", "time": "3:45:00" }
  ]
}
```

### Backend
- `GET /api/v1/legend/` — vrátí `legend_state` přihlášeného uživatele
- `POST /api/v1/legend/` — přijme `{"state": {...}}`, zavolá `sanitize_legend_state()`, uloží

### Frontend: LegendModal.vue
- Trigger: tlačítko "Legenda" v TopNav (viditelné pro oba role)
- Modal přes `EbModal.vue`
- **Athlete**: read-only zobrazení HR zón, prahů, PRů
- **Coach (vlastní plán)**: edit mode — inline editace zón, prahů; add/remove PRs
- Struktura modalu:
  - Sekce HR Zóny: tabulka Z1–Z5, sloupce Od / Do (bpm)
  - Sekce Prahy: Aerobní práh / Anaerobní práh (input nebo text)
  - Sekce PR: tabulka vzdálenost + čas, tlačítko "Přidat PR"
- Uložení: single POST na `/api/v1/legend/` s celým `state`
- Přidat `legend` do store `auth` nebo standalone `stores/legend.ts`

### Podporované vzdálenosti pro PR
`800m`, `1000m`, `1 mile`, `1500m`, `2 miles`, `3000m`, `3k`, `5000m`, `5k`, `10000m`, `10k`, `Půlmaraton`, `Maraton`

---

## Detail: Coach kód + Join requesty

### Coach kód (záložka "Kód trenéra")
- `GET /api/v1/coach/code/` — vrátí `{ coach_join_code: "ABC123456789" }`, generuje pokud chybí
- Rozšíření AthleteManageModal o záložku "Kód trenéra" — zobrazí kód s tlačítkem kopírování

### Join requesty trenéra (záložka "Žádosti")
- `GET /api/v1/coach/join-requests/` — vrátí seznam `{ id, athlete_name, athlete_username, created_at }`
- `POST /api/v1/coach/join-requests/{id}/approve/` — schválí, vytvoří `CoachAthlete` + `TrainingGroupAthlete`
- `POST /api/v1/coach/join-requests/{id}/reject/` — zamítne
- UI: seznam žádostí, každá řádka má tlačítka "Schválit" / "Zamítnout"

### Join request atleta (záložka "Trenér" v athlete dashboardu)
- `POST /api/v1/coach/join-request/` s `{ coach_code: "ABC..." }`
- Nová záložka v athlete AthleteView nebo standalone "request coach" widget
- Input na kód, tlačítko "Požádat o trenéra"

### Odebrání atleta (existující modal, chybí confirm)
- `DELETE /api/v1/coach/athletes/{id}/` s tělem `{ confirm_name: "Jan Novák" }`
- Backend ověří shodu s `display_name(athlete)`
- V AthleteManageModal přidat tlačítko "Odebrat atleta" → confirmation dialog (inline, ne nový modal)

---

## Detail: Přidání měsíce

### Backend
- `POST /api/v1/training/months/` — přijme `{ athlete_id?: number }` (optional pro coach)
  - Atletický kontext: `add_next_month_for_athlete(athlete=request.user)`
  - Coach kontext: `add_next_month_for_athlete(athlete=target_athlete)` — ověřit, že je coach atleta

### Frontend
- Tlačítko "Přidat měsíc" na konci stránky v `AthleteView.vue` i `CoachView.vue`
- Zobrazit vždy (i když jsou data), ale jen pokud je přihlášení OK
- Po úspěchu: zavolat `trainingStore.loadDashboard()` / `coachStore.loadDashboard()`

---

## Detail: Garmin week sync

### Backend
- `POST /api/v1/imports/garmin/week-sync/` — wrapper volající existující `garmin_sync_week` logiku
  - Přijme `{ week_start: "2026-03-31" }`
  - Vrátí `{ ok, replaced, untouched, message }`

### Frontend
- Tlačítko "Sync Garmin" v `WeekCard.vue` — viditelné jen pokud `garmin_connected && !week_in_future`
- Informace o Garmin připojení přidána do dashboard API response nebo globálního auth store
- Loading stav tlačítka během syncu; toast po dokončení

---

## Detail: Pozvánka do skupiny

### Situace
URL `/coach/invite/<token>/` je zachycena SPA catch-allem (`^coach/(?P<path>.*)`). Django view je nedostupný. Musíme ho zpracovat ve Vue.

### Backend
- `GET /api/v1/invites/{token}/` — vrátí `{ group_name, coach_name, is_expired, is_used }`
- `POST /api/v1/invites/{token}/accept/` — provede přijetí (stejná logika jako existující Django view)

### Frontend
- Nová Vue route: `/coach/invite/:token` → `InviteView.vue` (mimo AppShell, standalone)
- Stavy: loading / platná pozvánka + "Přijmout" button / already used / expired / error

---

## Detail: Planned KM detail popover

### Situace
API dashboard response už vrací `planned_km_show`, `planned_km_line_km`, `planned_km_line_reason`, `planned_km_line_where` (pole `planned_metrics` objektu TrainingRow).

### Frontend
- Rozšířit `TrainingRow` type v `api/training.ts` o tato pole
- V `PlannedRow.vue` — na km metrice přidat hover popover (HTML `<details>` nebo CSS tooltip)
- Zobrazit: km / důvod / kde — jen pokud `planned_km_show === true`

---

## Detail: Linked activity lock

### Situace
Kompletovaný trénink propojený s Garmin aktivitou má `has_linked_activity: true`. Pole km/min jsou read-only.

### Frontend
- Rozšířit `TrainingRow` type o `has_linked_activity: boolean`
- V `CompletedRow.vue` / `CompletedEditor.vue` — pokud `has_linked_activity`, skrýt edit button, zobrazit badge "🔗 Garmin" nebo lock ikonku

---

## Soubory k vytvoření / úpravě

### Backend
```
backend/api/views/legend.py          (nový)
backend/api/views/invites.py         (nový)
backend/api/urls.py                  (přidat nové routy)
backend/api/views/coach.py           (rozšířit o code, join-requests, remove athlete)
backend/api/views/training.py        (přidat months endpoint)
backend/api/views/imports.py         (přidat week-sync endpoint)
```

### Frontend
```
frontend/src/api/legend.ts           (nový)
frontend/src/api/invites.ts          (nový)
frontend/src/stores/legend.ts        (nový)
frontend/src/components/layout/LegendModal.vue        (nový)
frontend/src/views/invite/InviteView.vue              (nový)
frontend/src/components/training/WeekCard.vue         (+ Garmin week sync button)
frontend/src/components/training/PlannedRow.vue       (+ km popover)
frontend/src/components/training/CompletedRow.vue     (+ linked activity lock)
frontend/src/components/training/CompletedEditor.vue  (+ disable when linked)
frontend/src/components/coach/AthleteManageModal.vue  (+ code tab, requests tab, remove)
frontend/src/views/dashboard/AthleteView.vue          (+ add month button, request coach widget)
frontend/src/views/dashboard/CoachView.vue            (+ add month button)
frontend/src/components/layout/TopNav.vue             (+ legend button)
frontend/src/router/index.ts                          (+ /coach/invite/:token route)
frontend/src/api/training.ts                          (rozšířit typy)
frontend/src/api/imports.ts                           (+ weekSync)
frontend/src/api/coach.ts                             (+ join requests, code, remove)
frontend/src/locales/cs.json                          (nové klíče)
frontend/src/locales/en.json                          (nové klíče)
```

---

## Design principy

- Backend: minimální nový kód — wrappery nad existující service functions
- Frontend: `<style scoped>` + design tokeny, žádné inline styly
- Texty: výhradně přes `useI18n()` a `t()`
- Nové API endpointy vrací `{ ok: true, ... }` nebo `{ ok: false, error: "..." }`
- Garmin info (connected / not) dostupné přes `/api/v1/auth/me/` nebo rozšíření dashboard response

---

## Verifikace

- `npm run build` bez chyb
- `npm test` — 75+ testů zelené
- `python manage.py test` — Django testy zelené
- Manuální: legend zobrazení, HR zóny uložení, coach kód zkopírován, join request schválen, měsíc přidán, week sync button, invite stránka
