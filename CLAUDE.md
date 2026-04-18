# EnduroBuddy — Project Context for Claude

## Pravidla pro Clauda

1. **Při každé implementované změně nebo vytvoření plánu aktualizuj sekci "Aktivní plány a změny" v tomto CLAUDE.md** — napiš co bylo uděláno nebo co se plánuje, aby byl kontext viditelný napříč sezeními.

2. **Spec ukládej do `docs/superpowers/specs/YYYY-MM-DD-<tema>.md`** — design rozhodnutí, motivace, chování funkce.

3. **Implementační plán ukládej do `docs/superpowers/plans/YYYY-MM-DD-<tema>.md`** — konkrétní kroky, soubory, kód.

4. **Před implementací prohledej historii v `docs/superpowers/`** — tam jsou předchozí specs a plány, které mohou obsahovat relevantní kontext, rozhodnutí nebo hotové části.

5. **Commity bez Co-Authored-By** — autor je vždy jen uživatel, nikdy nepřidávej `Co-Authored-By: Claude` do commit message.

---

## Co je EnduroBuddy

Django webová aplikace pro plánování vytrvalostního tréninku. Propojuje trenéra a sportovce: trenér připravuje měsíční plány, sportovec zapisuje splněné tréninky a importuje aktivity z Garmin Connect nebo FIT souborů.

**Stack:** Python 3.12, Django 5.2, PostgreSQL, Vue 3 + TypeScript + Vite (SPA pro přihlášenou část), vlastní CSS bez frameworků, Docker Compose.

**Jazyky UI:** Česky + anglicky (django i18n, language switcher).

---

## Role uživatelů

- **Coach** — připravuje plány, spravuje sportovce a skupiny, sleduje plnění
- **Athlete** — vidí plán, zapisuje splněné tréninky, importuje aktivity

---

## Klíčové URL

| URL | Popis |
|-----|-------|
| `/` | Veřejná landing page (Django template) |
| `/app/*` | Athlete SPA (Vue Router — `AthleteView`) |
| `/coach/*` | Coach SPA (Vue Router — `CoachView`) |
| `/api/v1/` | DRF API (session auth, CSRF) |
| `/accounts/` | Autentizace (django-allauth) |
| `/admin/` | Django admin |

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
  main.ts              # app init, importuje design-tokens.css + fonts.css
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
  assets/              # design-tokens.css, fonts.css
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
- Display: **Syne** 700–800 (headlines, brand, hero)
- Body/UI: **Inter** 400–600 (vše funkční)
- Data/Mono: **JetBrains Mono** 500 (pace, distance, HR, timestamps)

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

## Aktivní plány a změny

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
