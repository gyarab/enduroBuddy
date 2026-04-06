# Vue 3 Frontend Migration — Design Spec

**Datum:** 2026-04-06  
**Status:** Schváleno, připraveno k implementaci

---

## Kontext

EnduroBuddy má 58 Django templates a 5 150 řádků vanilla JS bez frameworku, bez build toolchainu a bez testů. Komplexita dashboard editoru (1 372 řádků v jednom souboru, regex parser tréninkové notace, undo/redo systém) přerůstá možnosti čistého vanilla přístupu. Zároveň chceme přenést design language "Neon Lab × Swiss Precision" konzistentně do celé aplikace.

Cíl: přepsat aplikační část frontendu do Vue 3 + TypeScript + Vite, zachovat Django jako jediný server (auth, veřejné stránky, API), přinést design systém jako první třídu Vue komponent.

---

## Architektura

### Repozitář

```
endurobuddy-personal/
  backend/                    # Django — beze změny struktury
    accounts/
    activities/
    dashboard/                # views_*.py přepsat na DRF ViewSets
    training/
    api/                      # nový modul — DRF router + serializers + views
    templates/
      public/                 # zůstává beze změny (home, about, legal)
      registration/           # allauth templates — zůstávají
      spa.html                # nový — entry point pro Vue SPA
    static/brand/             # SVG loga — zůstávají
    config/
      settings.py             # přidat: DRF, CORS (jen dev), SPA_TEMPLATE
      urls.py                 # přidat: spa_view + catch-all pro /app/ a /coach/
  frontend/                   # nové
    src/
      main.ts
      App.vue
      router/index.ts
      stores/                 # Pinia
      api/                    # axios klient + wrappery
      components/
        ui/                   # design system komponenty
        training/
        coach/
        layout/
      views/
      assets/
        design-tokens.css
        fonts.css
    vite.config.ts
    tsconfig.json
    vitest.config.ts
    package.json
  docker-compose.yml
```

### Routing — Django jako jediný server

Django URL patterny rozhodují, co je SPA a co je template:

```python
# config/urls.py
urlpatterns = [
    path("api/v1/", include("api.urls")),
    path("accounts/", include("allauth.urls")),   # auth — zůstává
    path("admin/", admin.site.urls),
    path("", include("public.urls")),              # landing, about, legal
    re_path(r"^(app|coach)/", spa_view),           # → spa.html (Vue entry)
]
```

`spa_view` vrátí `spa.html` — prázdný HTML soubor s Vite build outputem. Vue Router pak obsluhuje vše pod `/app/*` a `/coach/*`.

**Produkce:** Nginx → Gunicorn/Django. Whitenoise servuje statické soubory včetně Vite buildu.  
**Vývoj:** `vite dev` na `:5173`, proxy `/api/*` na Django `:8000`. Hot-reload pro Vue, Django dev server pro API.

### Auth

Session-based auth zůstane (django-allauth). Po přihlášení allauth přesměruje na `/app/` — Django vrátí `spa.html`, Vue SPA se inicializuje, Pinia načte current user přes `/api/v1/auth/me/`. CSRF cookie (`endurobuddy_csrftoken`) funguje automaticky přes axios interceptor. Žádné JWT tokeny.

---

## Backend — API vrstva (DRF)

### Nový modul `backend/api/`

```
backend/api/
  __init__.py
  urls.py           # DRF router
  serializers/
    training.py     # PlannedTraining, CompletedTraining
    accounts.py     # UserProfile, CoachAthlete
    activities.py   # Activity, FITImport
  views/
    auth.py         # /api/v1/auth/me/ — current user info
    training.py     # ViewSets — planned + completed training
    dashboard.py    # dashboard data (měsíc, týdny)
    notifications.py
    imports.py      # Garmin start, FIT upload, job status
    coach.py        # coach-specific endpoints
```

### Nové závislosti

```
djangorestframework
django-cors-headers   # jen pro development (CORS pro Vite dev server)
```

### API endpointy

```
GET  /api/v1/auth/me/
GET  /api/v1/dashboard/                     # měsíc + týdny + tréninky
GET  /api/v1/training/planned/
POST /api/v1/training/planned/
PATCH /api/v1/training/planned/{id}/
DELETE /api/v1/training/planned/{id}/
GET  /api/v1/training/completed/
POST /api/v1/training/completed/
PATCH /api/v1/training/completed/{id}/
POST /api/v1/training/planned/{id}/second-phase/
DELETE /api/v1/training/planned/{id}/second-phase/
GET  /api/v1/notifications/
POST /api/v1/notifications/mark-read/
POST /api/v1/imports/garmin/start/
GET  /api/v1/imports/jobs/{id}/status/
POST /api/v1/imports/fit/
GET  /api/v1/coach/athletes/
GET  /api/v1/coach/dashboard/
PATCH /api/v1/coach/training/planned/{id}/
PATCH /api/v1/coach/training/completed/{id}/
```

Existující business logika v `handlers/planned_training_api.py` a validátory se přepoužijí — mění se jen presentační vrstva.

---

## Frontend — tech stack

### Závislosti

| Balíček | Účel |
|---------|------|
| `vue@3` | framework |
| `vue-router@4` | routing (history mode) |
| `pinia` | state management |
| `axios` | HTTP klient (CSRF interceptor) |
| `typescript` | typy |
| `vite` | build + dev server |
| `vitest` | unit testy |
| `@vue/test-utils` | component testy |
| `@vitejs/plugin-vue` | Vite Vue plugin |

**Bootstrap se vynechá.** Layout přes CSS Grid/Flexbox s `eb-` třídami. Ušetří ~30 kB, odstraní konflikty s vlastním design systémem.

### Struktura `src/`

```
src/
  main.ts                 # app init, importuje design-tokens.css + fonts.css
  App.vue                 # RouterView wrapper
  router/
    index.ts              # routes: /app/dashboard, /app/profile, /coach/plans...
  stores/
    auth.ts               # currentUser, role (athlete/coach), isAuthenticated
    training.ts           # activeMonth, weeks, planned/completed data
    notifications.ts      # notifikace, unread count, polling (15s interval)
    coach.ts              # athletes list, active athlete focus
  api/
    client.ts             # axios instance — baseURL, CSRF header, error handling
    training.ts           # wrappers pro training endpointy
    notifications.ts
    imports.ts
    coach.ts
  composables/
    useTrainingParser.ts  # přepis dashboard_editor_planned.js — regex parser,
                          # interval kalkulace, undo/redo (unit testováno)
    useInlineEditor.ts    # sdílená inline edit logika (planned + completed)
    useGarminImport.ts    # Garmin import flow + polling
  components/
    ui/
      EbButton.vue        # lime/blue/ghost/danger varianty
      EbBadge.vue         # status: planned, done, missed, rest
      EbCard.vue          # surface + border + radius wrapper
      EbToast.vue         # notifikační toast (přepis toast systému z base_ui.js)
      EbModal.vue         # modal wrapper (teleport do body)
      EbSpinner.vue       # loading state
    training/
      WeekTable.vue       # týdenní přehled (planned + completed řádky)
      PlannedRow.vue      # řádek plánovaného tréninku + inline editor
      CompletedRow.vue    # řádek splněného tréninku + inline editor
      MonthSwitcher.vue   # navigace mezi měsíci
      MonthCards.vue      # přehledové karty měsíce
    coach/
      CoachSidebar.vue    # seznam atletů, focus výběr
      AthleteManageModal.vue
    layout/
      AppShell.vue        # celkový layout (sidebar + main)
      TopNav.vue          # topbar s notifikacemi + profilem
      NotificationBell.vue
      ProfileModal.vue
  views/
    dashboard/
      AthleteView.vue     # hlavní pohled sportovce
      CoachView.vue       # hlavní pohled trenéra
    profile/
      CompleteProfileView.vue  # po Google OAuth
```

---

## Design language v Vue

### CSS tokeny

`src/assets/design-tokens.css` — přeneseno z `public-base.css`, importováno globálně v `main.ts`:

```css
:root {
  --eb-bg: #09090b;
  --eb-surface: #18181b;
  --eb-border: #27272a;
  --eb-text: #fafafa;
  --eb-text-muted: #71717a;
  --eb-lime: #c8ff00;
  --eb-blue: #38bdf8;
  --eb-danger: #f43f5e;
  --eb-warning: #f59e0b;
  --eb-radius-sm: 6px;
  --eb-radius-md: 10px;
  --eb-radius-lg: 16px;
  --eb-font-display: 'Syne', sans-serif;
  --eb-font-body: 'Inter', sans-serif;
  --eb-font-mono: 'JetBrains Mono', monospace;
}
```

`src/assets/fonts.css` — Google Fonts import (Syne 700–800, Inter 400–600, JetBrains Mono 500). `base_public.html` si je načítá nezávisle jako dnes — žádná duplikace.

### CSS v komponentách

Každá Vue komponenta používá `<style scoped>` s tokeny — žádný CSS framework, žádné inline styly:

```vue
<style scoped>
.training-row {
  background: var(--eb-surface);
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-md);
  font-family: var(--eb-font-body);
  color: var(--eb-text);
}
.training-row--done {
  border-left: 3px solid var(--eb-lime);
}
.training-row__distance {
  font-family: var(--eb-font-mono);
  color: var(--eb-lime);
}
</style>
```

### Globální body reset

`App.vue` nebo `main.ts` nastaví:

```css
body {
  background: var(--eb-bg);
  color: var(--eb-text);
  font-family: var(--eb-font-body);
  margin: 0;
}
```

### Prefix konvence

- `eb-` — sdílené UI komponenty a utility třídy (stejně jako dosud)
- Scoped CSS v komponentách — bez prefixu, izolace zajistí Vite

---

## Migrační strategie — fáze

### Fáze 1 — Základ

**Backend:**
- Nainstalovat DRF + django-cors-headers
- Přidat `backend/api/` modul s URL routerem
- Přepsat existující JSON endpoints z `views_athlete_api.py` na DRF ViewSets (business logika se nemění)
- Přidat `/api/v1/auth/me/` endpoint
- Přidat `spa_view` a URL catch-all pro `/app/*`, `/coach/*`
- Přidat `spa.html` template

**Frontend:**
- Inicializovat `frontend/` — Vite + Vue 3 + TypeScript + Pinia + Vue Router
- Nastavit `vite.config.ts` s proxy na Django dev server
- Importovat `design-tokens.css` + `fonts.css` v `main.ts`
- Implementovat `api/client.ts` (axios + CSRF interceptor)
- Implementovat `stores/auth.ts` — načtení current user z `/api/v1/auth/me/`
- Implementovat `AppShell.vue` + `TopNav.vue` (prázdný shell ale se správným designem)
- CI krok: `npm run build` → output do `backend/static/spa/`

**Výsledek:** `/app/` načte Vue SPA, uvidí prázdný shell se správnými barvami a fonty. Allauth login funguje.

### Fáze 2 — Dashboard (atletův pohled)

- Implementovat `stores/training.ts` + `api/training.ts`
- Přepsat `useTrainingParser.ts` z `dashboard_editor_planned.js` — s unit testy
- Implementovat `WeekTable.vue`, `PlannedRow.vue`, `CompletedRow.vue`
- Implementovat inline editor (planned + completed) — `useInlineEditor.ts`
- Implementovat `MonthSwitcher.vue`, `MonthCards.vue`
- Implementovat `stores/notifications.ts` + `NotificationBell.vue` + `EbToast.vue`
- Garmin import flow — `useGarminImport.ts` + progress polling
- FIT file upload
- `AthleteView.vue` — sestavit z komponent

**Výsledek:** Sportovec může plně používat aplikaci přes Vue SPA.

### Fáze 3 — Coach rozhraní

- Implementovat `stores/coach.ts` + `api/coach.ts`
- `CoachSidebar.vue` — seznam atletů, výběr focusu
- `AthleteManageModal.vue`
- `CoachView.vue` — sdílí komponenty z fáze 2, přidá coach-specific logiku

**Výsledek:** Trenér může plně používat aplikaci přes Vue SPA.

### Fáze 4 — Zbývající funkce

- `ProfileModal.vue` — profil editace
- `CompleteProfileView.vue` — po Google OAuth
- Language switcher (i18n) — `vue-i18n` balíček, locale soubory `cs.json` + `en.json`, jazyk persistován v localStorage a synchronizován s Django `set_language` view
- Přepsat hardcoded Czech strings z JS souborů do i18n locale souborů

### Co se NEMĚNÍ (nikdy)

| Co | Proč |
|----|------|
| Veřejné stránky (home, about, legal) | SEO, stabilní obsah, Django templates jsou OK |
| Auth stránky (allauth) | Komplexní flow (email verify, password reset), není důvod přepisovat |
| Backend modely a migrace | Databáze se nemění |
| Business logika v handlers/ | Zůstává, jen se obalí DRF serializéry |
| Docker Compose | Přibyde jen `npm run build` krok v Dockerfile |

---

## Docker a deployment

```dockerfile
# Dockerfile — build stage
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Django stage
FROM python:3.12-slim
...
COPY --from=frontend-build /frontend/dist /app/backend/static/spa
RUN python manage.py collectstatic --noinput
```

```yaml
# docker-compose.yml (dev)
services:
  backend:
    build: .
    ports: ["8000:8000"]
  frontend:
    build:
      context: frontend
      dockerfile: Dockerfile.dev
    ports: ["5173:5173"]
    volumes: ["./frontend:/app"]
```

---

## Verifikace

- `npm run test` — Vitest unit testy (zejména `useTrainingParser.ts`)
- `npm run build` — Vite build proběhne bez chyb
- `python manage.py test` — Django testy zůstanou zelené
- Manuální test: login → `/app/` → dashboard se načte, data se zobrazí, inline edit funguje
- Manuální test: coach login → `/coach/` → athlete list, plans fungují
- `docker compose up --build` — celý stack nastartuje, spa.html se servuje přes whitenoise
