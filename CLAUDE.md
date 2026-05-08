# EnduroBuddy — Project Context for Claude

## Pravidla pro Clauda

1. **Při každé implementované změně nebo vytvoření plánu aktualizuj sekci "Aktivní plány a změny" v tomto CLAUDE.md** — napiš co bylo uděláno nebo co se plánuje, aby byl kontext viditelný napříč sezeními.

2. **Spec ukládej do `docs/superpowers/specs/YYYY-MM-DD-<tema>.md`** — design rozhodnutí, motivace, chování funkce.

3. **Implementační plán ukládej do `docs/superpowers/plans/YYYY-MM-DD-<tema>.md`** — konkrétní kroky, soubory, kód.

4. **Před implementací prohledej historii v `docs/superpowers/`** — tam jsou předchozí specs a plány, které mohou obsahovat relevantní kontext, rozhodnutí nebo hotové části.

5. **Commity bez Co-Authored-By** — autor je vždy jen uživatel, nikdy nepřidávej `Co-Authored-By: Claude` do commit message.

6. **Commit messages vždy v angličtině** — typ i popis (např. `feat: add terms checkbox to signup`).

7. **Každá nová feature = vlastní větev + push na remote** — před implementací vytvořit `feat/<tema>` větev a pushnout ji na `origin` (`git push -u origin feat/<tema>`). Commitovat průběžně a pushovat tak, aby byl remote vždy aktuální. Uživatel pracuje na více počítačích.

---

## Co je EnduroBuddy

Django webová aplikace pro plánování vytrvalostního tréninku. Propojuje trenéra a sportovce: trenér připravuje měsíční plány, sportovec zapisuje splněné tréninky a importuje aktivity z Garmin Connect nebo FIT souborů.

**Stack:** Python 3.12, Django 5.2, PostgreSQL, Nuxt 3 + TypeScript (SSR veřejné stránky + SPA přihlášená část), vlastní CSS bez frameworků, Docker Compose, Celery + Redis.

**Jazyky UI:** Česky + anglicky (django i18n, language switcher).

---

## Role uživatelů

- **Coach** — připravuje plány, spravuje sportovce a skupiny, sleduje plnění
- **Athlete** — vidí plán, zapisuje splněné tréninky, importuje aktivity

---

## Klíčové URL

| URL | Popis |
|-----|-------|
| `/` | Veřejná landing page (Nuxt SSR) |
| `/about`, `/terms`, `/privacy` | Veřejné stránky (Nuxt SSR) |
| `/accounts/*` | Auth flow (Nuxt — GET; allauth OAuth callback — Django) |
| `/app/*` | Athlete SPA (Nuxt) |
| `/coach/*` | Coach SPA (Nuxt) |
| `/api/v1/` | DRF API (session auth, CSRF) |
| `/admin/` | Django admin (jediný Django-rendered HTML) |

---

## Architektura

### Backend (Django)

```
backend/
  accounts/    # profily, role, coach-athlete vazby, skupiny, Garmin připojení
  activities/  # import aktivit, FIT soubory, intervaly, vzorky
  dashboard/   # servisní logika (handlers, validátory) — žádné views pro SPA
  training/    # měsíce, týdny, plánované a dokončené tréninky (modely + logika)
  api/         # DRF API vrstva — views/, urls.py (auth, training, coach, imports…)
  templates/
    public/    # veřejné stránky (home, about, legal) — Django server-rendered
    spa.html   # entry point pro Vue SPA (načte Vite build output)
  static/brand/  # SVG loga — neměnit
  static_build/  # Vite build output (generovaný, není v gitu)
```

### Frontend (Vue SPA)

```
frontend/src/
  main.ts              # app init, importuje design-tokens.css (fonty přes CDN v nuxt.config.ts)
  App.vue              # RouterView wrapper
  router/index.ts      # /app/dashboard, /coach/plans, /app/profile/complete
  stores/              # Pinia — auth, training, coach, notifications, toasts
  api/                 # axios klient (client.ts) + wrappery per doména
  composables/
    useI18n.ts         # vlastní i18n (cs.json + en.json), sync s Django set_language
    useInlineEditor.ts # sdílená inline editor logika
    useTrainingParser.ts  # parser tréninkové notace
    useGarminImport.ts # Garmin import flow + polling
  components/
    ui/                # EbButton, EbBadge, EbCard, EbToast, EbModal, EbSpinner
    training/          # WeekCard, PlannedRow, CompletedRow, MonthSummaryBar…
    coach/             # CoachSidebar, AthleteManageModal
    layout/            # AppShell, TopNav, NotificationBell, ProfileDropdown
  views/
    dashboard/         # AthleteView.vue, CoachView.vue
    profile/           # CompleteProfileView.vue
  locales/             # cs.json, en.json
  assets/              # design-tokens.css (fonts.css smazán — fonty přes Google Fonts CDN)
```

**Vývoj:** `npm run dev` v `frontend/` (Vite na `:5173`, proxy `/api/*` → Django `:8000`)
**Build:** `npm run build` — output do `backend/static_build/spa/`
**Testy:** `npm test` — Vitest, 75 testů

---

## Vizuální design systém — "Neon Lab × Swiss Precision"

**Koncept:** Kreativní energie s racionální čistotou. Designérský precision instrument s momenty elektrické intenzity. Ne fitness app, ne analytics dashboard — moderní training workspace s nezaměnitelnou identitou.

### Klíčové dokumenty
- Visual style guide: `docs/visual-style-guide.md` (tokeny, typografie, komponenty, CSS architektura)
- Design spec landing page: `docs/superpowers/specs/2026-04-05-landing-page-design.md`
- Visual style preview: `docs/visual-style-preview.html`
- Dashboard preview: `docs/dashboard-visual-style-preview.html`

### Paleta (celá aplikace — jednotný systém)
- Pozadí: `#09090b` (true dark, zero color cast)
- Surface: `#18181b`
- Border: `#27272a`
- Primární akcent: `#c8ff00` (electric lime — CTA, done, coach)
- Sekundární akcent: `#38bdf8` (crisp blue — info, planned, athlete)
- Danger: `#f43f5e`
- Warning: `#f59e0b`

### Typografie
- Display: **Outfit** 600–800 (headlines, brand, hero)
- Body/UI: **Nunito** 400–700 (vše funkční)
- Data/Mono: **JetBrains Mono** 400–500 (pace, distance, HR, timestamps)

Fonty načítány z **Google Fonts CDN** (`nuxt.config.ts` → `app.head.link`). Žádné lokální WOFF2 soubory v pipeline.

### Logo — "Stride Mark"
Tři horizontální pruhy rostoucí délky, nakloněné 6° dopředu.
- `backend/static/brand/eb-mark.svg` (ikona)
- `backend/static/brand/eb-logo-full.svg` (mark + wordmark)
- `backend/static/brand/eb-logo-compact.svg` (mark + "EB")
- `backend/static/brand/eb-wordmark.svg` (wordmark)
- Starší loga: `backend/static/brand/logo.png`, `biglogo.png` (PNG, legacy)

### Klíčové CSS tokeny
```css
--eb-bg: #09090b;
--eb-surface: #18181b;
--eb-border: #27272a;
--eb-text: #fafafa;
--eb-text-muted: #71717a;
--eb-lime: #c8ff00;
--eb-blue: #38bdf8;
--eb-radius-sm: 6px;
--eb-radius-md: 10px;
--eb-radius-lg: 16px;
```

---

## Public sekce — architektura šablon a CSS

Všechny veřejné stránky rozšiřují `backend/templates/public/base_public.html`, který zajišťuje:
- načtení fontů (Syne + Inter + JetBrains Mono z Google Fonts)
- SVG logo v navbaru a footeru (`eb-logo-full.svg` / `eb-logo-compact.svg`)
- sticky topbar se třemi navigačními odkazem a login CTA
- třísloupečkový footer s language switcherem

### CSS soubory public sekce

| Soubor | Obsah |
|--------|-------|
| `backend/static/css/public-base.css` | Design tokeny, body reset, `.eb-public-shell`, topbar, footer |
| `backend/static/css/public-home.css` | Landing page styly (`--lp-*` tokeny + sekce hero/features/steps/CTA) |
| `backend/static/css/public-about.css` | About page — 4 sekce (intro, story, mission, founder) |
| `backend/static/css/public-legal.css` | Privacy + Terms — back-link, card layout, typografie |

### Landing page

Soubor: `backend/templates/public/home.html` (extends `public/base_public.html`)

Sekce: Hero (dashboard mockup) → Features (6 karet) → Jak to funguje (3 kroky) → Pro koho (Coach + Athlete) → CTA

---

## Důležitá pravidla

### Veřejná sekce (Django templates)
- Page-specific styly jdou do externího CSS souboru, načteného přes `{% block page_styles %}` — **ne inline `<style>` tag**
- Bilingualita: texty v Django templates přes `{% if CURRENT_LANGUAGE == "en" %}`
- Fonty: Syne + Inter + JetBrains Mono — načítá `base_public.html`, v page templates se nepřidávají znovu
- Prefix `eb-` pro sdílené CSS třídy; `lp-` pro landing-page-only třídy
- Každý template musí mít `{% load static %}` pokud používá `{% static %}`

### Vue SPA (frontend/)
- **Nezasahuj do Django views pro `/app/*` a `/coach/*`** — tyto URL obsluhuje Vue Router
- CSS výhradně přes `<style scoped>` s design tokeny — žádný Bootstrap, žádné inline styly
- Texty v komponentách výhradně přes `useI18n()` a `t()` — žádné hardcoded stringy
- Lokalizace: klíče přidávat do obou `frontend/src/locales/cs.json` i `en.json`
- Při změně API endpointů aktualizovat `frontend/src/api/` i `backend/api/views/`
- `npm run build` musí projít bez chyb a `npm test` musí být zelené před commitem

---

## Demo

```bash
cd backend
python manage.py seed_coach_demo
# coach_demo@endurobuddy.local / demo12345
```

---

## Git workflow — aktivní migrace

```
origin:
  main                  ← produkce
  backup/pre-nuxt-20260418  ← historický snapshot (nepoužívá se)
  feat/nuxt-migration   ← veškerý vývoj probíhá zde
```

Veškerá práce probíhá na větvi `feat/nuxt-migration`. Po dokončení se mergne do `main`. Větev `backup/pre-nuxt-20260418` existuje v origin jako historický záznam — aktivně se nepoužívá.

Spec: `docs/superpowers/specs/2026-04-18-nuxt-migration-design.md`

---

## Aktivní plány a změny

### 2026-05-08 — Public header: auth-aware CTA ✅ KOMPLETNÍ (feat/public-auth-header)

**Spec:** `docs/superpowers/specs/2026-05-08-public-auth-header.md`
**Plán:** `docs/superpowers/plans/2026-05-08-public-auth-header.md`

**Co bylo implementováno:**
- `domains.global.ts`: odstraněn blok který přesměrovával přihlášené uživatele z veřejných stránek na app doménu; middleware je nyní synchronní bez závislosti na auth store
- `public.vue`: přidán `useAuthStore()` + `onMounted` inicializace; header zobrazuje "Dashboard →" (`/dashboard`) pro přihlášené, "Login →" pro nepřihlášené
- i18n: přidán klíč `nav.dashboard` do cs.json + en.json
- Testy: `frontend/middleware/domains.test.ts` (5 testů), `frontend/layouts/public.test.ts` (3 testy); celkem 137 testů zelených

---

### 2026-05-06 — Production routing + auth bugs ✅ KOMPLETNÍ (feat/registration-flow, commit 062a3dd)

**Spec:** `docs/superpowers/specs/2026-05-06-production-routing-auth-bugs.md`
**Plán:** `docs/superpowers/plans/2026-05-06-production-routing-auth-bugs.md`

**Bug 1 — `app.endurobuddy.cz` → 404:**  
`docker-compose.yml` nginx service neměl Traefik router pro `app.endurobuddy.cz` — Traefik tu doménu neznal. Přidány 4 řádky labels.

**Bug 2 — `endurobuddy.cz/admin/` → 400:**  
nginx a urls.py jsou správné. Pravděpodobná příčina je `DJANGO_ALLOWED_HOSTS` v produkčním `.env` — nutno ověřit na serveru. `.env.example` již obsahuje správnou hodnotu (`endurobuddy.cz,app.endurobuddy.cz,...`).

**Bug 3 — "EnduroBuddy User" místo jména:**  
Nuxt service v docker-compose neměl `NUXT_PUBLIC_APP_HOST` → `domains.global.ts` vrátil hned → auth nikdy neinicializován → `user = null`. Přidáno `NUXT_PUBLIC_APP_HOST: ${TRAEFIK_APP_HOST:-}`.

**Zbývá na serveru:**  
Ověřit/aktualizovat produkční `.env` a spustit `docker compose up -d --build`. Checklist viz spec.

---

### 2026-05-06 — Security fix: auth guard pro protected routes ✅ KOMPLETNÍ

**Branch:** `feat/registration-flow` (commit e141ef5)

**Bug:** `domains.global.ts` obsahoval `if (!appHost) return` na řádku 4, což způsobilo že celá auth ochrana byla podmíněna nastavením `NUXT_PUBLIC_APP_HOST`. V dev a single-domain deploymentu middleware odpadl hned, takže `/app/**`, `/coach/**` a `/dashboard` byly dostupné bez přihlášení.

**Fix:**
- Nový `frontend/middleware/auth.global.ts` — funguje nezávisle na multi-domain konfiguraci, vždy ověří session přes `/auth/me/` a redirectuje na login pokud user není přihlášen
- `domains.global.ts` nyní obsahuje jen redirect přihlášeného uživatele z public domain na app domain (odstraněn "app domain → login" redirect, ten přebírá auth.global.ts)
- `vitest.config.ts` rozšířen o `define: { "import.meta.client": "true", "import.meta.server": "false" }` pro testování middlewarů
- `vitest.setup.ts` rozšířen o globální stuby `navigateTo`, `defineNuxtRouteMiddleware`, `useRuntimeConfig`
- 9 nových testů v `frontend/middleware/auth.test.ts`, celkem 129 testů zelených

---

### 2026-05-04 — Registration Flow Redesign ✅ KOMPLETNÍ (feat/registration-flow)

**Spec:** `docs/superpowers/specs/2026-05-04-registration-flow-redesign.md`
**Plán:** `docs/superpowers/plans/2026-05-04-registration-flow-redesign.md`

**Co bylo implementováno:**
- `Profile.terms_accepted_at` pole + `needs_profile_setup` @property (migrace 0018)
- `GoogleProfileCompletionMiddleware` přepsán — redirect na `/accounts/profile-setup/`
- `auth_signup`: validace `terms_accepted`, ukládá `terms_accepted_at`
- `auth_me`: přidáno `first_name`, `last_name`, `needs_profile_setup` do response
- `_default_route_for_user`: redirect na `/accounts/profile-setup/` pro Google uživatele bez dokončeného onboardingu
- `POST /api/v1/auth/profile-setup/`: nový endpoint pro Google onboarding (role + terms + jméno)
- Frontend: `AuthMeResponse` rozšířeno o `first_name`, `last_name`, `needs_profile_setup`; `SignupPayload` + `terms_accepted`; `profileSetup()` API util
- Nuxt middleware `profile-setup.global.ts` — guard přesměrovávající Google uživatele bez onboardingu
- Signup formulář: terms+privacy checkbox, disabled submit bez souhlasu
- Nová stránka `/accounts/profile-setup/` — auth shell, jméno/role/terms, pre-filled z Google účtu
- Email šablony: tmavý design (`#09090b` + lime header) + `@media (prefers-color-scheme: light)` fallback
- Testy: 29 backend testů, 120 frontend testů — vše zelené

**Bugfixy (2026-05-05):**
- `AuthPreviewShell.vue`: změněn `flex-direction: column` + `margin-block: auto` na `.auth-shell__card` — formulář signup přestal být ořezán `overflow: hidden` shellu
- `AuthPreviewShell.vue`: `overflow: hidden` → `overflow-x: hidden; overflow-y: auto` — obranné scrollování kdyby grid row nevyrostl správně
- `[...slug].vue`: `filter(Boolean)` na slug segmentech — trailing slash v URL dával `"signup/"` místo `"signup"`, screenMap nenašel klíč a fallbackoval na `"login"` → signup formulář se vůbec nezobrazoval

---

### 2026-05-04 — Migrace Celery + Redis → django-q2 ✅ KOMPLETNÍ

**Spec:** `docs/superpowers/specs/2026-05-04-django-q2-migration-design.md`
**Plán:** `docs/superpowers/plans/2026-05-04-django-q2-migration.md`

**Motivace:** Celery + Redis byl přehnaně složitý pro jediný user-triggered task (Garmin sync). Django-q2 používá PostgreSQL jako broker — žádná nová infrastruktura.

**Co bylo uděláno:**
- Odstraněny balíčky: `celery[redis]`, `django-celery-beat`, `django-celery-results`, `redis`
- Přidán `django-q2==1.10.0`, aplikovány DB migrace (19 django_q tabulek)
- `backend/config/celery.py` smazán, `config/__init__.py` vyprázdněn
- `Q_CLUSTER` konfigurace v `settings.py` (`orm: "default"`, `workers: 1`, `timeout: 300`, `max_attempts: 1`)
- Nový management command `reset_stale_import_jobs` — cleanup RUNNING ImportJobů při startu workeru (nastavuje `status=ERROR`, `finished_at=now()`)
- `dashboard/services/tasks.py`: `@shared_task` + `.delay()` → `async_task(_execute_garmin_sync_job, import_job_id)`
- `test_celery_tasks.py` smazán, nahrazen `test_garmin_tasks.py` (5 testů, TDD)
- docker-compose: odstraněny `redis`, `celery-worker`, `celery-beat` services; přidán `qcluster` service (depends_on: db + web; spouští reset_stale_import_jobs před qcluster)
- `.env.example` vyčištěn od REDIS_* proměnných

**Stav po migraci:** 111 testů zelených, 1 skipped. Django check: 0 issues.

---

### 2026-04-18 — Nuxt migrace + infrastrukturní základ

**Větev:** `feat/nuxt-migration`
**Spec:** `docs/superpowers/specs/2026-04-18-nuxt-migration-design.md`
**Plán:** `docs/superpowers/plans/2026-04-18-nuxt-migration.md`

**Cíl:** Nahradit Vite SPA + Django templates jedním Nuxt 3 stackem, přejít na moderní tooling a přidat async task queue.

#### Co je součástí plánu

| Oblast | Technologie | Stav |
|--------|------------|------|
| Python package manager | uv (nahrazuje pip) | ✅ hotovo |
| Node package manager | pnpm (nahrazuje npm) | ✅ hotovo |
| Task queue + broker | Celery + Redis | ✅ hotovo |
| Frontend framework | Nuxt 3 (nahrazuje Vite SPA + Django templates) | ✅ hotovo (about.vue je placeholder) |

#### Fáze

- **Fáze 0a** — uv: `pyproject.toml`, aktualizace Dockerfile
- **Fáze 0b** — pnpm: nahradit npm, přechod `pnpm-lock.yaml`
- **Fáze 1** — Redis + Celery: Docker service, Celery worker + beat, Garmin sync jako async task
- **Fáze 2** — Nuxt setup, migrace komponent, veřejné stránky (SSR), error stránka, help modál
- **Fáze 3** — Cleanup Django templates + Nginx routing
- **Fáze 4** — QA

#### Blokující chybějící věci (původní motivace)
- Veřejné stránky (home, about, terms, privacy) — jen Django templates, bez Vue ekvivalentu
- Error stránky (404, 500) — jen Django templates
- Help modál (km pravidla) — jen Django template
- Garmin sync je synchronní (blokuje request) — Celery to opraví

**Implementační plány (bite-sized TDD):**
- `docs/superpowers/plans/2026-04-18-infrastructure.md` — uv, pnpm, Redis, Celery (9 tasků)
- `docs/superpowers/plans/2026-04-18-nuxt-migration-impl.md` — Nuxt migrace (12 tasků)

**Status (ověřeno 2026-04-24):** ✅ Kompletně hotovo. Backend: 125 passed, 1 skipped. Frontend: 96 passed (14 files). Django check: 0 issues.

#### Hotovo ve Fázi 0
- **Task 1 (uv)** — `backend/pyproject.toml` s 21 závislostmi (Django, Celery, Garmin, FIT, Postgres, gunicorn, whitenoise); `backend/uv.lock` vygenerován; `requirements.txt` smazán
- **Task 2 (Dockerfile uv)** — `Dockerfile` aktualizován: `pip install uv && uv sync --frozen --no-dev`
- **Task 3 (pnpm)** — `frontend/pnpm-lock.yaml` vygenerován; `frontend/.npmrc` (`shamefully-hoist=true`); `package-lock.json` smazán; docker-compose aktualizován

#### Hotovo v Fázi 1
- **Task 4** — Redis service v `docker-compose.yml` + `docker-compose.prod.yml` (volume `endurobuddy_redis`, `web` závisí na `redis`)
- **Task 5** — `backend/config/celery.py`, `backend/config/__init__.py`, Celery konfigurace v `settings.py`, `django_celery_beat` + `django_celery_results` v `INSTALLED_APPS`, migrace aplikovány
- **Task 6** — `celery-worker` + `celery-beat` services v `docker-compose.yml`
- **Task 7 (infra)** — `backend/dashboard/tests/test_celery_tasks.py` — 3 testy pro Celery task dispatch (TDD failing test před implementací)
- **Task 8 (infra)** — `backend/dashboard/services/tasks.py` — `ThreadPoolExecutor` nahrazen `@shared_task execute_garmin_sync_job`; `enqueue_garmin_sync_job` volá `.delay()`; `_execute_garmin_sync_job` čistá testovatelná funkce

#### Hotovo ve Fázi 2
- **Task 1 (nuxt)** — Nuxt 3 inicializace v `frontend/`:
  - `frontend/nuxt.config.ts` — SSR pro `/`, `/about`, `/terms`, `/privacy`; SPA pro `/app/**`, `/coach/**`, `/accounts/**`; @pinia/nuxt + @nuxtjs/i18n moduly; Vite proxy pro Django API
  - `frontend/app.vue` — minimální wrapper s `<NuxtLayout><NuxtPage />`
  - `frontend/pages/index.vue` — placeholder index stránka
  - `frontend/i18n/locales/cs.json` + `en.json` — prázdné locale soubory (i18n v9 je hledá v `i18n/locales/`)
  - `frontend/assets/design-tokens.css` + `fonts.css` — kopie z `src/assets/` pro Nuxt CSS pipeline
  - `frontend/vite.config.ts` → `vite.config.ts.bak` — přejmenováno (Nuxt nepodporuje standalone vite.config)
  - `package.json` aktualizován: nuxt, @pinia/nuxt, @nuxtjs/i18n, axios, vue, vue-router
  - Všech 93 testů zelených, Nuxt dev server startuje na `:3000`
- **Task 2 (nuxt)** — Migrace `src/` do Nuxt struktury:
  - `frontend/components/` — přesunuto z `src/components/`
  - `frontend/stores/` — 8 Pinia stores (auth, coach, legend, notifications, toasts, training)
  - `frontend/composables/` — useGarminImport, useInlineEditor, useTrainingParser
  - `frontend/assets/` — design-tokens.css, fonts.css
  - `frontend/i18n/` — locale soubory cs.json + en.json (přesunuto z `src/locales/`)
  - `frontend/plugins/i18n-sync.client.ts` — synchronizace jazyka s Django session
  - Starý `frontend/src/` adresář **zatím nebyl smazán** (viz "Zbývá")
- **Task 3 (nuxt)** — `$fetch` API klient:
  - `frontend/utils/apiFetch.ts` — wrapper s CSRF tokenem, credentials, X-Requested-With
  - `frontend/utils/api/` — 8 modulů: auth, coach, imports, invites, legend, notifications, profile, training
- **Task 4 (nuxt)** — Náhrada vlastního `useI18n` za `@nuxtjs/i18n`:
  - `frontend/plugins/i18n-sync.client.ts` — watch na locale, POST `/i18n/set_language/`
  - Importy `useI18n` z vlastního composable odstraněny; `@nuxtjs/i18n` auto-importuje
- **Task 5 (nuxt)** — `app.vue` a layouts:
  - `frontend/app.vue` — `<NuxtLayout><NuxtPage />`
  - `frontend/layouts/default.vue` — AppShell s variant="athlete"|"coach" dle URL
  - `frontend/layouts/public.vue` — topbar (logo, nav), footer (logo, nav, language switcher), copyright rok
  - `frontend/layouts/auth.vue` — centrovaný auth wrapper
- **Task 6 (nuxt)** — Pages pro přihlášenou část:
  - `frontend/pages/app/dashboard.vue` → AthleteView
  - `frontend/pages/app/index.vue` → redirect na /app/dashboard
  - `frontend/pages/app/profile/complete.vue` → CompleteProfileView
  - `frontend/pages/coach/plans.vue` → CoachView
  - `frontend/pages/coach/index.vue` → redirect na /coach/plans
  - `frontend/pages/coach/invite/[token].vue` → InviteView
  - `frontend/pages/accounts/[...slug].vue` → AuthFlowView (slug → screenMap)
- **Task 7 (nuxt)** — SSR veřejné stránky:
  - `frontend/pages/index.vue` — kompletní landing page (Hero, Features, How It Works, Audience, CTA, fade-up animace)
  - `frontend/pages/terms.vue` — kompletní Terms of Use (en/cs)
  - `frontend/pages/privacy.vue` — kompletní Privacy Policy (en/cs)
  - `frontend/pages/about.vue` — **PLACEHOLDER** ("Soon") — viz "Zbývá"
  - CSS přesunuto: `frontend/assets/css/public-base.css`, `public-home.css`, `public-about.css`, `public-legal.css`
- **Task 8 (nuxt)** — Error stránka a PlannedKmRulesModal (2026-04-19):
  - `frontend/error.vue` — Nuxt error page (statusCode 404/403/generic, i18n, design tokeny)
  - `frontend/components/training/PlannedKmRulesModal.vue` — modal s pravidly zápisu tréninku (Teleport to body, isOpen prop, close emit)
  - `frontend/components/training/PlannedRow.vue` — integrován help button `?` vedle labelu Title, modal mountován na konci template
  - `frontend/i18n/locales/cs.json` + `en.json` — přidány klíče `error.*` a `kmRules.*`
  - `frontend/components/training/PlannedKmRulesModal.test.ts` — 3 testy zelené (TDD: failing test commitnut před implementací)
  - Celkem 189 testů zelených
- **Task 9 (nuxt)** — Backend `GET /api/v1/site-config/` endpoint:
  - `backend/api/views/config.py` — vrací `{"registration_enabled": true/false}` dle `settings.REGISTRATION_ENABLED`
  - URL registrována v `backend/api/urls.py`
  - Testy: `backend/api/tests/test_site_config.py` zelené
  - **Poznámka:** `frontend/pages/index.vue` má `registrationEnabled` zatím hardcoded na `true` — viz "Zbývá"
- **Task 10 (nuxt)** — Docker: Nuxt jako standalone service + Nginx (2026-04-19):
  - `frontend/Dockerfile` — multi-stage build (builder → runtime), pnpm, `.output/server/index.mjs`
  - `nginx/nginx.conf` — upstream django + nuxt, routing: `/api/`, `/admin/`, `/static/`, `/i18n/`, `/accounts/google/` → Django; `/` → Nuxt; WebSocket upgrade header; přidány `X-Forwarded-Proto` + chybějící `X-Forwarded-For` do všech Django locations
  - `nginx/Dockerfile` — nginx:1.25-alpine s kopií nginx.conf
  - `docker-compose.yml` — přidán `nuxt` service (port 3000, depends_on web); odstraněn starý `frontend` service (pnpm dev na 5173)
  - `docker-compose.prod.yml` — `web` Traefik rule zúžen na path-prefix pro Django routes (priority 20); přidán `nuxt` service s catch-all Traefik rule (priority 10)
  - `frontend/.dockerignore` — vyloučeny node_modules, .nuxt, .output, .env atd.
  - `docker compose config --quiet` prošel bez chyb (dev i prod)
- **Task 11 (nuxt)** — Cleanup Django templates a HTML views (2026-04-19):
  - Odstraněny HTML-renderující views: `dashboard/views_home.py::home()`, `dashboard/views_coach.py::coach_training_plans()`, `dashboard/views_invites.py::accept_training_group_invite()`
  - Odstraněny URL patterny: `app/` (dashboard_home), `coach/plans/` (coach_training_plans), `coach/invite/<token>/` (training_group_invite_accept)
  - `config/urls.py` — přidán `account_complete_profile` URL (→ nuxt_redirect), import `nuxt_redirect` z `config.views_nuxt`
  - `accounts/views.py` — nahrazen import `config.views_spa` (smazaný) za `config.views_nuxt.nuxt_redirect`; fallback redirecty z `dashboard_home` na `/app/`
  - `dashboard/views_profile.py` — fallback redirect z `dashboard_home` na `/app/`
  - `templates/includes/_top_nav.html` — nahrazeny `{% url 'public_home' %}`, `{% url 'dashboard_home' %}`, `{% url 'coach_training_plans' %}` přímými URL; odstraněny tlačítka legend/import (jsou v Nuxt SPA)
  - Testy: odstraněny testy HTML views (`_fit_import_rendering_cases.py` vyřazen z test_fit_import.py, `_coach_training_page_cases.py` vyřazen z test_coach_training_plans.py); opraveny testy v `accounts/tests.py`, `test_profile_manage.py`, `test_spa_api.py`, `_coach_training_planned_cases.py`, `_coach_training_completed_cases.py`, `_fit_import_flow_cases.py`, `_fit_import_garmin_cases.py`
  - Django check: 0 issues; 141 testů zelených (1 skipped)
- **Task 11 residual fix** — Odstranění mrtvého kódu po cleanup (2026-04-19):
  - `dashboard/handlers/home_actions.py` — nahrazeny 4x `redirect("dashboard_home")` za `redirect("/app/dashboard")`
  - `dashboard/views_invites.py` — odstraněna celá funkce `accept_training_group_invite()` (URL byla smazána v Task 11, view bylo nedosažitelné); soubor zredukován na prázdný stub
  - `backend/templates/dashboard/accept_training_group_invite.html` — odstraněn (`git rm`)
  - `dashboard/tests/_fit_import_rendering_cases.py` — odstraněn (`git rm`; obsahoval reference na `dashboard_home`)
  - `dashboard/tests/_coach_training_page_cases.py` — odstraněn (`git rm`; obsahoval reference na `dashboard_home` a `training_group_invite_accept`)
  - Django check: 0 issues; 141 testů zelených (1 skipped)
- **Routing fix** — `/accounts/` nyní obsluhuje Nuxt (2026-04-19):
  - Kořenová příčina: Vite proxy přeposílal `/accounts/*` na Django; Django `nuxt_redirect` přesměrovával zpět na `localhost:3000` (hardcoded) → nekonečná smyčka
  - `frontend/nuxt.config.ts` — proxy `/accounts` nahrazen `/accounts/google` (jen OAuth)
  - `nginx/nginx.conf` — blok `location /accounts/` změněn na `location /accounts/google/`; ostatní `/accounts/*` padají na catch-all `/` → Nuxt
  - `docker-compose.prod.yml` — Traefik pravidla pro `web` zúžena z `PathPrefix('/accounts/')` na `PathPrefix('/accounts/google/')`
  - Výsledek: uživatelsky viditelné stránky účtu (login, signup...) obsluhuje Nuxt, OAuth callback (`/accounts/google/`) jde na Django

#### Dokončeno (2026-04-24)

- **`frontend/pages/about.vue`** — kompletní stránka (intro, story, mission, founder) portovaná dle CSS v `public-about.css`; i18n klíče přidány do cs.json + en.json
- **`frontend/pages/index.vue` — `registrationEnabled`** — nahrazeno `useFetch('/api/v1/site-config/')` + `computed`; již není hardcoded
- **`frontend/src/` smazán** — starý Vite SPA adresář odstraněn via `git rm`; `vitest.config.ts` alias `@/` opraven na `./`; `nuxt.config.ts` alias `@/` opraven na `./`; `vitest.setup.ts` stub i18n načítá skutečné překlady z `cs.json` s interpolací params; všechny `@/api/` importy v 13 komponentách nahrazeny `~/utils/api/`; dotčené testy aktualizovány (import paths + literal key expectations); 14 test files, 96 testů zelených; Nuxt dev server startuje bez chyb
- **`README.md` přepsán** — kompletní rewrite reflektující aktuální stack (Nuxt 3 + Django API + Celery + Redis + uv + pnpm)

---

### 2026-04-18 — Dashboard: editace completed trainingu + Garmin modal

**Soubory:** `frontend/src/components/training/WeekCard.vue`, `frontend/src/views/dashboard/AthleteView.vue`

**Co chybí:**

1. **Editace completed trainingu** — inline editace v WeekCard funguje jen pokud completed řádek *už existuje*. Pokud má den planned training ale žádný completed záznam, pole km/čas/HR nejsou klikatelná.

2. **Garmin Import Modal** — `GarminImportModal.vue` existuje (connect účtu, range sync, FIT upload), ale není přístupný z `AthleteView` — chybí tlačítko a mount komponenty.

**Plán WeekCard.vue:**
- Přidat `canEditCompletedGlobal` computed (čte `trainingStore.dashboard?.flags.can_edit_completed`)
- Přepsat `canEditCompleted(slot)` — vrátit `true` i když completed neexistuje, ale planned ano
- V `openEdit()`: nastavit `completedId = planned?.id` když žádný completed záznam neexistuje (backend `PATCH /training/completed/{planned_id}/` vytváří záznam pokud neexistuje)
- V `saveRow()`: po úspěšném vytvoření nového záznamu provést silent reload (`trainingStore.loadDashboard(..., { silent: true })`)

**Plán AthleteView.vue:**
- Importovat `GarminImportModal` a `useAuthStore`
- Přidat tlačítko "Import" (viditelné jen když `garmin_connect_enabled`) nad `MonthSummaryBar`
- Mountovat `<GarminImportModal>` na konec šablony
- i18n klíč `imports.open` už existuje — žádný nový klíč není potřeba

**Status:** ✅ Implementováno a mergnuto do main (2026-04-18)

---

### 2026-04-18 — Analýza: stav migrace Django templates → Vue SPA

Kompletní průzkum repozitáře na větvi `main`.

#### Portováno do Vue (templates lze postupně mazat)
| Oblast | Django template | Vue komponenta |
|---|---|---|
| Auth stránky | `account/*.html`, `socialaccount/*.html` | `AuthFlowView.vue` |
| Athlete dashboard | `dashboard/dashboard.html` + partialy | `AthleteView.vue`, `WeekCard.vue` atd. |
| Coach dashboard | `dashboard/coach_training_plans.html` | `CoachView.vue` |
| Pozvánka | `dashboard/accept_training_group_invite.html` | `InviteView.vue` |
| Doplnění profilu | `account/complete_profile.html` | `CompleteProfileView.vue` |
| Profil modal | `includes/_profile_modal.html` | `ProfileSettingsModal.vue` |
| Notifikace | `includes/_notifications_dropdown.html` | `NotificationBell.vue` |
| Top nav | `includes/_top_nav.html` | `TopNav.vue` |
| Garmin import modal | `dashboard/_import_modal.html` | `GarminImportModal.vue` |
| Legend modál | `dashboard/_legend_modals.html` | `LegendModal.vue` |
| Coach sidebar | `dashboard/_coach_sidebar.html` | `CoachSidebar.vue` |
| Coach manage modal | `dashboard/_coach_manage_modal.html` | `AthleteManageModal.vue` |

#### BLOKUJÍCÍ — chybí ve Vue (templates zatím nelze mazat)
1. **Veřejné stránky** — `public/home.html`, `public/about.html`, `public/terms.html`, `public/privacy.html` — celý veřejný web stále běží na Django templates.
2. **Help modál (km pravidla)** — `dashboard/_planned_km_rules_modal.html` — Vue má live parser preview, ale chybí standalone modál s vysvětlivkami.
3. **Error stránky** — `400.html`, `403.html`, `404.html`, `500.html` — jen Django templates.

#### Co má Vue navíc (není v Django templates)
- Live training parser preview v `PlannedRow.vue`
- FIT file upload v `GarminImportModal.vue`
- Job polling pro Garmin sync
- Language switcher přímo v `ProfileSettingsModal.vue`
- Skeleton loading states (`WeekCardSkeleton.vue`)
- Auth Preview sandbox (`/auth-preview/`)

#### URL routing — poznámka
V `config/urls.py` jsou SPA routes `/app/*` definovány **před** `include("dashboard.urls")`, takže legacy Django dashboard na `/app/` je v produkci překrytý SPA a nedostupný. Django route pro dashboard existuje v kódu, ale není dosažitelná.

**Status:** Analýza dokončena, implementace migrace veřejných stránek do Vue zatím neplánována.

---

### 2026-04-25/26 — WeekCard: split-zone editing + layout redesign ✅ KOMPLETNÍ

**Spec:** `docs/superpowers/specs/2026-04-25-weekcard-zone-editing.md`
**Plán:** `docs/superpowers/plans/2026-04-25-weekcard-zone-editing.md`

**Co bylo implementováno:**
- `WeekCard.vue`: planned (3/5) a completed (2/5) zóna se vzájemně vylučují při editování
- Kliknutím na planned zónu se otevřou jen inputy pro trénink/poznámky (modré podbarvení `rgba(56,189,248,.07)`)
- Kliknutím na completed zónu se otevřou jen inputy pro km/čas/HR (lime podbarvení `rgba(200,255,0,.07)`)
- Neaktivní zóna se ztmaví (opacity 0.45) a zablokuje klikání (`pointer-events: none`)
- Přepnutí zóny uloží dirty data fire-and-forget a okamžitě otevře novou zónu
- Summary row zobrazuje `planned_total_km_text` (plánované km) v planned sekci modrou mono barvou
- Mobilní layout: planned nahoře (plná šířka), completed jako kompaktní řádek pod ním
- Nový test soubor: `WeekCard.test.ts` (5 testů — 4 pro mutual exclusion, 1 pro summary)
- Celkem: 101 testů zelených (15 souborů), TypeScript: 0 chyb

---

### 2026-04-30 — WeekCard: editing UX + keyboard navigation ✅ KOMPLETNÍ

**Spec:** `docs/superpowers/specs/2026-04-30-weekcard-editing-ux.md`
**Plán:** `docs/superpowers/plans/2026-04-30-weekcard-editing-ux.md`

- `autoSave` ponechá edit otevřený po debounce uložení; `closeAndSave` zavírá při focusout
- `closeAfterSave` flag zajistí zavření i když focusout přijde během in-flight API callu
- Zone flash: zelená animace na buňkách aktivní zóny při úspěchu, červená při chybě
- Planned zóna animace končí na transparent (ne lime), aby nepřepisovala modré editační pozadí
- Klávesnicová navigace: Tab/Shift+Tab (pole+řádky), Enter/Shift+Enter (sloupec), Arrow keys
- Cross-week: WeekCard emituje `navigate-out-next/prev`, AthleteView + CoachView volají `focusCell`
- `defineExpose({ focusCell })` umožňuje parent komponentám zaměřit konkrétní pole v libovolném týdnu
- Celkem: 15 testů v `WeekCard.test.ts`, všechny zelené

---

### 2026-04-26 — Django templates: pouze admin + email ✅ KOMPLETNÍ

**Cíl:** Django renderuje HTML pouze pro `/admin/`. Vše ostatní obsluhuje Nuxt.

**Co bylo uděláno:**

1. **Smazány mrtvé dashboard/includes templates** — 19 souborů (dashboard/*, includes/*, _language_switcher.html)
2. **Error views přepsány bez templates** — `config/error_views.py` nyní:
   - `/api/*` requesty → JSON `{"error": "...", "status": N}`
   - Browserové requesty → self-contained inline HTML (design tokens, bez Bootstrapu, bez template souboru)
   - Smazány: `400.html`, `403.html`, `404.html`, `500.html`, `base.html`, `errors/_status_card.html`, `debug/error_preview.html`
   - Smazán: `test_dashboard_frontend_regressions.py` (testoval smazané templates)
3. **Smazán mrtvý `complete_profile` Django HTML view** — `accounts/views.py:complete_profile()` odstraněn, profil completion jde přes JSON API `/api/v1/profile/complete/` + Nuxt `CompleteProfileView.vue`
4. **`spa_account_*` POST handlery převedeny na `nuxt_redirect`** — Nuxt používá `/api/v1/auth/*` (JSON), allauth HTML POST path je dead code. Logout POST zachován (allauth session teardown).
5. **Smazány allauth HTML templates** — `account/*.html` (kromě `email/`) + `socialaccount/*.html`

**Zbývající templates (legitimní):**
- `templates/account/email/*.html` — transakční emaily (odesílání, ne web stránky)
- Django admin templates (poskytuje Django framework)

**Stav po dokončení:** 125 testů zelených (1 skipped), Django check: 0 issues.

---

### 2026-04-26 — Multi-domain architektura ✅ KOMPLETNÍ

**Spec:** `docs/superpowers/specs/2026-04-26-multi-domain.md`  
**Plán:** `docs/superpowers/plans/2026-04-26-multi-domain.md`  
**Status:** Implementováno a pushnuté na main

**Cíl:** Rozdělit aplikaci na `endurobuddy.cz` (veřejná část) a `app.endurobuddy.cz` (přihlášená část). `www.endurobuddy.cz` → 301 redirect.

**Klíčová rozhodnutí:**
- Jedna Nuxt instance obsluhuje obě domény (ne dva kontejnery)
- Session/CSRF cookies nastaveny s `domain=.endurobuddy.cz` (sdílené pro subdomény)
- Backend vrátí absolutní URL po přihlášení pokud je `DJANGO_APP_HOST` nastaven
- Dev workflow (dev.sh + nativní) se nemění — všechny nové proměnné mají prázdné výchozí hodnoty
- Oba docker-compose soubory jsou živé: `docker-compose.yml` = dev Docker stack, `docker-compose.prod.yml` = produkce s Traefik

**Hotovo (6 tasků):**
1. ✅ `backend/config/settings.py` — `SESSION_COOKIE_DOMAIN`, `CSRF_COOKIE_DOMAIN`, `APP_HOST`, dynamický `LOGIN_REDIRECT_URL` (commit: 8cef3aa)
2. ✅ `backend/api/views/auth.py` + `profile.py` — helper `_app_url()`, absolutní URL v `_default_route_for_user`, `auth_me`, `_default_app_route_for_role` (commit: 26461bc)
3. ✅ `frontend/nuxt.config.ts` + `frontend/middleware/domains.global.ts` — runtimeConfig `appHost`, cross-domain redirect middleware (commit: b0b925f)
4. ✅ `docker-compose.prod.yml` — Traefik routery pro `app.endurobuddy.cz` (Django + Nuxt) + `www` redirect middleware (commit: fef351c)
5. ✅ `nginx/nginx.conf` — `www` redirect server block (commit: dd3075f)
6. ✅ `.env.example` — nové proměnné: `TRAEFIK_APP_HOST`, `SESSION_COOKIE_DOMAIN`, `CSRF_COOKIE_DOMAIN`, `DJANGO_APP_HOST`, aktualizované `DJANGO_ALLOWED_HOSTS` + CORS/CSRF origins (commit: f3021db)

**Pro nasazení nastavit v `.env`:** `TRAEFIK_APP_HOST`, `SESSION_COOKIE_DOMAIN=.endurobuddy.cz`, `CSRF_COOKIE_DOMAIN=.endurobuddy.cz`, `DJANGO_APP_HOST=app.endurobuddy.cz`, `NUXT_PUBLIC_APP_HOST` (automaticky z `TRAEFIK_APP_HOST` přes docker-compose).
