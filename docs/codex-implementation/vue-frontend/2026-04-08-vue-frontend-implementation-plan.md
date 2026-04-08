# Vue Frontend Migration Implementation Plan

## Purpose

Tento dokument je Codex implementacni plan pro migraci prihlasene casti EnduroBuddy do Vue 3. Je zamerne ulozen mimo `docs/superpowers/specs/`, aby zustaly puvodni Claudeovy podklady nedotcene a slouzily pouze jako vstupni reference.

Vychazi z techto dokumentu:

- `docs/superpowers/specs/2026-04-06-vue-frontend-migration-design.md`
- `docs/superpowers/specs/2026-04-06-vue-app-visual-design.md`
- `docs/visual-style-guide.md`

## Goals

- Presunout prihlasenou aplikacni cast z Django templates + vanilla JS do `Vue 3 + TypeScript + Vite`.
- Zachovat Django jako jediny server pro auth, public pages, API, session a deployment.
- Prenest visual language "Neon Lab x Swiss Precision" do SPA od prvni faze, ne az jako pozdejsi polish.
- Zachovat existujici business logiku v `dashboard.services.*`, `dashboard.handlers.*`, `activities.services.*` a menit hlavne presentation/API vrstvu.
- Umoznit inkrementalni rollout bez rozbiti stavajiciho produkcniho chovani.

## Non-Goals

- Neprepisovat verejne stranky v `backend/templates/public/`.
- Neprepisovat allauth flow nebo auth stranky do Vue.
- Nemenit databazovy model pouze kvuli migraci frontendu.
- Nepresouvat backend na samostatny API server nebo nezavadet JWT.

## Target Structure

```text
docs/
  codex-implementation/
    vue-frontend/
      2026-04-08-vue-frontend-implementation-plan.md

frontend/
  src/
    main.ts
    App.vue
    router/
    stores/
    api/
    composables/
    components/
      ui/
      layout/
      training/
      coach/
    views/
    assets/
      design-tokens.css
      fonts.css
  package.json
  vite.config.ts
  tsconfig.json
  vitest.config.ts

backend/
  api/
    __init__.py
    urls.py
    serializers/
    views/
  templates/
    spa.html
```

## Source Of Truth Mapping

Migrace ma navazovat na dnesni backend, ne na idealizovanou greenfield architekturu.

- `backend/dashboard/services/month_cards.py` a souvisejici `month_cards_*` moduly zustanou primarnim zdrojem dashboard dat.
- `backend/dashboard/handlers/planned_training_api.py` zustane zdrojem validace planned/completed editaci.
- `backend/dashboard/views_home.py` a `backend/dashboard/views_coach.py` jsou referencni body pro athlete a coach use-cases.
- `backend/templates/dashboard/_month_cards.html` a souvisejici partials slouzi jako funkcni mapa toho, co musi byt ve Vue znovu sestaveno.
- `backend/dashboard/static/js/dashboard_editor_planned.js` a pribuzne soubory se budou postupne portovat do Vue composables.

## Architecture Decisions

### Server and Routing

- Django zustane jediny server.
- Verejne routy zustanou server-rendered:
  - `/`
  - `/about/`
  - `/terms/`
  - `/privacy/`
  - `/accounts/*`
- Vue SPA bude obsluhovat pouze prihlasene routy:
  - `/app/`
  - `/app/dashboard`
  - `/app/profile/complete`
  - `/coach/`
  - `/coach/plans`
- Django vrati pro `/app/*` a `/coach/*` `spa.html`, Vue Router pak dokonci navigaci na klientu.

### Auth

- Session auth zustane zachovana pres Django + allauth.
- `LOGIN_REDIRECT_URL` zustane `/app/`.
- Frontend bude cist current user z `/api/v1/auth/me/`.
- Axios klient bude posilat CSRF pres existujici cookie `endurobuddy_csrftoken`.
- JWT ani token-based auth se nezavadi.

### API Strategy

- Nove API pobezi pod `/api/v1/`.
- V prvni iteraci budou endpointy obalovat existujici backend logiku misto toho, aby ji nahrazovaly.
- Dashboard payload se bude skladat na backendu z existujicich `month_cards` services, aby frontend nemusel slozite rekonstruovat mesic/tydny/radky z mnoha endpointu.
- Access control zustane na backendu role-aware stejne jako dnes.

## Frontend Design System Rules

Vue aplikace musi od prvni faze respektovat design spec, ne jen funkcni rozhrani.

- Globalni tokeny budou v `frontend/src/assets/design-tokens.css`.
- Fonty budou v `frontend/src/assets/fonts.css`.
- Globalni reset a shell setup pobezi z `main.ts` nebo `App.vue`.
- Zakladni principy:
  - tmavy workspace shell
  - compact topnav
  - minimum dekorativnich efektu v datove casti
  - JetBrains Mono pro ciselne a vykonnostni udaje
  - lime pro done/coach/highlight
  - blue pro planned/athlete/info
  - reduced motion respektovat vsude

Minimalni token set musi zahrnout:

- barvy pozadi, surface, border, text, muted text
- lime, blue, danger, warning
- spacing scale
- radius scale
- shadow/glow scale
- display/body/mono font tokens

## Implementation Phases

### Phase 1: SPA Bootstrap and Shell

#### Backend

- Pridat `backend/api/` modul.
- Pridat `backend/templates/spa.html`.
- Rozsirit `backend/config/urls.py` o:
  - `path("api/v1/", include("api.urls"))`
  - SPA entry pro `/app/*` a `/coach/*`
- Rozsirit `backend/config/settings.py` o:
  - `rest_framework`
  - dev-only `corsheaders` pokud bude potreba pro Vite dev server
  - konfiguraci pro Vite build output ve static files

#### Frontend

- Inicializovat `frontend/`:
  - Vue 3
  - TypeScript
  - Vite
  - vue-router
  - Pinia
  - axios
  - vitest
  - `@vue/test-utils`
- Implementovat:
  - `src/main.ts`
  - `src/App.vue`
  - `src/router/index.ts`
  - `src/stores/auth.ts`
  - `src/api/client.ts`
- Vytvorit zakladni layout:
  - `components/layout/AppShell.vue`
  - `components/layout/TopNav.vue`
  - `components/layout/NotificationBell.vue`
  - `components/layout/ProfileDropdown.vue`
- Vytvorit zakladni UI komponenty:
  - `EbButton`
  - `EbBadge`
  - `EbCard`
  - `EbModal`
  - `EbToast`
  - `EbSpinner`

#### Visual Acceptance

- `/app/` zobrazi prazdny shell v cilovem dark designu.
- Topnav ma compact vysku, sticky chovani a odpovidajici tokeny.
- App shell funguje na desktopu i mobilu.

### Phase 2: Athlete Dashboard Read-Only

#### Backend

- Pridat endpoint `GET /api/v1/dashboard/`.
- Endpoint prijme aspon:
  - `month=YYYY-MM` volitelne
- Vrati payload slozeny z:
  - current month identity
  - month summary stats
  - tydny
  - planned/completed rows
  - role-aware flags
  - notification/import capabilities potrebne pro dalsi faze

#### Frontend

- Pridat `stores/training.ts`.
- Pridat `api/training.ts`.
- Implementovat:
  - `views/dashboard/AthleteView.vue`
  - `components/training/MonthSummaryBar.vue`
  - `components/training/MonthSwitcher.vue`
  - `components/training/WeekCard.vue`
  - `components/training/PlannedRow.vue`
  - `components/training/CompletedRow.vue`
  - skeleton states
  - empty state pro prazdny mesic

#### Visual Acceptance

- Month summary odpovida visual spec.
- Week cards maji oddeleny header a body.
- Training rows rozlisuji planned/done/missed stav borderem, badge a typografii.

### Phase 3: Athlete Editing, Notifications, Imports

#### Backend

- Pridat nebo presunout endpointy:
  - `GET /api/v1/training/planned/`
  - `POST /api/v1/training/planned/`
  - `PATCH /api/v1/training/planned/{id}/`
  - `DELETE /api/v1/training/planned/{id}/`
  - `GET /api/v1/training/completed/`
  - `POST /api/v1/training/completed/`
  - `PATCH /api/v1/training/completed/{id}/`
  - `POST /api/v1/training/planned/{id}/second-phase/`
  - `DELETE /api/v1/training/planned/{id}/second-phase/`
  - `GET /api/v1/notifications/`
  - `POST /api/v1/notifications/mark-read/`
  - `POST /api/v1/imports/garmin/start/`
  - `GET /api/v1/imports/jobs/{id}/status/`
  - `POST /api/v1/imports/fit/`
- Reuse validace z `planned_training_api.py` a navaznych shared helpers.

#### Frontend

- Implementovat `useTrainingParser.ts` portovany ze stavajiciho editoru planned training.
- Implementovat `useInlineEditor.ts`.
- Implementovat expanded row editory pro:
  - planned training
  - completed training
- Pridat `stores/notifications.ts`.
- Pridat `useGarminImport.ts`.
- Doplnit:
  - notification dropdown
  - toast system
  - Garmin import modal
  - FIT upload flow

#### Visual Acceptance

- Aktivni inline editor ma lime outline a glow.
- Parsed preview pouziva tlumeny lime panel.
- Notification dropdown, toasty a import modal odpovidaji visual spec.

### Phase 4: Coach Workspace

#### Backend

- Pridat coach endpointy:
  - `GET /api/v1/coach/athletes/`
  - `GET /api/v1/coach/dashboard/`
  - `PATCH /api/v1/coach/training/planned/{id}/`
  - `PATCH /api/v1/coach/training/completed/{id}/`
  - `PATCH /api/v1/coach/athlete-focus/`
  - `PATCH /api/v1/coach/reorder-athletes/`
- Znovu pouzit access control z `views_coach.py` a shared helperu.

#### Frontend

- Pridat `stores/coach.ts`.
- Implementovat:
  - `views/dashboard/CoachView.vue`
  - `components/coach/CoachSidebar.vue`
  - `components/coach/AthleteManageModal.vue`
- Sdilet `WeekCard`, `PlannedRow`, `CompletedRow` mezi athlete a coach pohledem.
- Coach-specific rozdily resit daty a props, ne duplikaci celeho UI.

#### Visual Acceptance

- Sidebar odpovida spec pro coach shell.
- Aktivni athlete focus je vizualne odlisitelny.
- Na mobilu je sidebar schovany za hamburger.

### Phase 5: Profile, i18n, Legacy Cleanup

#### Backend

- Dodat API/route podporu pro profile completion flow, pokud nebude stacit stavajici server-rendered route.
- Napojit jazykove prepinani na Django i18n.

#### Frontend

- Implementovat:
  - `views/profile/CompleteProfileView.vue`
  - profile modal nebo settings surface
- Zavadet i18n az po stabilizaci hlavni funkcnosti.
- Presunout hardcoded texty do locale souboru:
  - `cs.json`
  - `en.json`

#### Cleanup

- Jakmile budou Vue flows funkcne hotove, postupne odstranit zavislost na:
  - starem dashboard JS
  - dashboard partialech pouzivanych jen pro SPA nahrazenou cast
  - Bootstrap-specifickych prvkach v prihlasene casti

## API Contracts

### `GET /api/v1/auth/me/`

Vraci:

- user id
- full name
- email
- role
- initials
- capability flags
- default app route

### `GET /api/v1/dashboard/`

Vraci:

- selected month
- available month navigation info
- month summary stats
- array tydnu
- rows planned/completed v poradi, ktere frontend rovnou vykresli
- editable flags
- import capability flags
- notification metadata pokud je potreba pro shell bootstrap

### Training Row Shape

Kazdy row objekt musi obsahovat aspon:

- `id`
- `kind` (`planned`, `completed`, `second_phase`)
- `status` (`planned`, `done`, `missed`, `rest`)
- `date`
- `day_label`
- `title`
- `notes`
- `session_type`
- planned metrics
- completed metrics
- editability flags
- linked activity info

### Coach Dashboard Shape

Coach dashboard payload musi navic obsahovat:

- selected athlete summary
- athlete list
- focus metadata
- reorder metadata
- role-based edit flags

## File-Level Implementation Checklist

### Backend

- `backend/config/settings.py`
- `backend/config/urls.py`
- `backend/templates/spa.html`
- `backend/api/urls.py`
- `backend/api/views/auth.py`
- `backend/api/views/dashboard.py`
- `backend/api/views/training.py`
- `backend/api/views/notifications.py`
- `backend/api/views/imports.py`
- `backend/api/views/coach.py`
- `backend/api/serializers/`

### Frontend

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/vitest.config.ts`
- `frontend/src/main.ts`
- `frontend/src/App.vue`
- `frontend/src/router/index.ts`
- `frontend/src/assets/design-tokens.css`
- `frontend/src/assets/fonts.css`
- `frontend/src/api/client.ts`
- `frontend/src/api/*.ts`
- `frontend/src/stores/*.ts`
- `frontend/src/composables/*.ts`
- `frontend/src/components/ui/*.vue`
- `frontend/src/components/layout/*.vue`
- `frontend/src/components/training/*.vue`
- `frontend/src/components/coach/*.vue`
- `frontend/src/views/**/*.vue`

## Testing Strategy

### Documentation Safety

- Oveit, ze vznikl pouze novy dokument v `docs/codex-implementation/`.
- Oveit, ze `docs/superpowers/specs/*` nebyly upraveny.

### Backend Tests

- `auth/me` vraci spravneho uzivatele a capability flags.
- dashboard endpoint vraci ocekavanou strukturu pro athlete.
- coach dashboard endpoint respektuje access control.
- planned/completed editace zustanou kompatibilni s dnesnim chovanim.
- second phase create/remove zustane funkcni.
- notifications mark-read zustane funkcni.
- import job status zustane kompatibilni.

### Frontend Tests

- parser planned training notace ma unit testy.
- inline editor ma testy pro open/save/cancel/error states.
- `WeekCard`, `PlannedRow`, `CompletedRow` maji render testy.
- `TopNav`, `NotificationBell`, `CoachSidebar` maji interakcni testy.
- stores maji testy pro loading, success, error, polling a optimistic update scenare.

### Integration Scenarios

- login pres allauth -> redirect na `/app/`.
- athlete otevre dashboard a vidi month summary + tydny.
- athlete upravi planned training inline editorem.
- athlete ulozi completed training.
- athlete spusti Garmin import a vidi progress.
- coach otevre `/coach/plans`, prepina athlete a vidi spravny dashboard.
- coach nemuze editovat completed data ciziho atleta, pokud to dnesni pravidla nedovoluji.

### Visual Acceptance

- shell, topnav, month summary, week cards, rows, inline editory, sidebar, dropdowny a modaly odpovidaji visual spec.
- mobilni breakpointy pod `768px` fungují podle navrhu.
- focus states a reduced-motion jsou zachovane.

## Rollout Notes

- Implementovat inkrementalne, ne big bang prepisem.
- Nejdriv zprovoznit shell a read-only dashboard.
- Teprve po stabilizaci shellu a dashboard dat portovat editory a import flow.
- Coach rozhrani stavet na sdilenych athlete komponentach.
- Legacy dashboard assets odebirat az po funkcni nahrade ve Vue.

## Done Definition

Migrace bude povazovana za pripravenou k rollout fazi, kdyz plati:

- existuje `frontend/` workspace se sestavitelnou Vue aplikaci
- Django obslouzi `spa.html` pro `/app/*` a `/coach/*`
- athlete dashboard funguje aspon read-only nad `/api/v1/dashboard/`
- design tokens a shell odpovidaji schvalenemu visual smeru
- existuje jasna cesta pro port inline editoru, notifikaci, importu a coach pohledu
- puvodni Claudeovy spec dokumenty zustaly beze zmen

## Defaults Chosen In This Plan

- Codex vystupy patri do `docs/codex-implementation/`.
- Dashboard payload se bude skládat na backendu z `month_cards` services.
- Session auth a CSRF zustavaji.
- Vue SPA bude obsluhovat jen prihlasenou cast.
- Vizuální design se implementuje od prvni faze.
- i18n prijde az po stabilizaci hlavnich athlete a coach flows.
