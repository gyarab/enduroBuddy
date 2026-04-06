# EnduroBuddy — Project Context for Claude

## Co je EnduroBuddy

Django webová aplikace pro plánování vytrvalostního tréninku. Propojuje trenéra a sportovce: trenér připravuje měsíční plány, sportovec zapisuje splněné tréninky a importuje aktivity z Garmin Connect nebo FIT souborů.

**Stack:** Python 3.12, Django 5.2, PostgreSQL, Bootstrap 5, server-rendered templates + vlastní JS/CSS, Docker Compose.

**Jazyky UI:** Česky + anglicky (django i18n, language switcher).

---

## Role uživatelů

- **Coach** — připravuje plány, spravuje sportovce a skupiny, sleduje plnění
- **Athlete** — vidí plán, zapisuje splněné tréninky, importuje aktivity

---

## Klíčové URL

| URL | Popis |
|-----|-------|
| `/` | Veřejná landing page |
| `/app/` | Dashboard sportovce |
| `/coach/plans/` | Dashboard trenéra |
| `/accounts/` | Autentizace (django-allauth) |
| `/admin/` | Django admin |

---

## Architektura

```
backend/
  accounts/    # profily, role, coach-athlete vazby, skupiny, Garmin připojení
  activities/  # import aktivit, FIT soubory, intervaly, vzorky
  dashboard/   # hlavní dashboard, coach rozhraní, servisní logika
  training/    # měsíce, týdny, plánované a dokončené tréninky
  templates/   # Django templates (server-rendered)
  static/      # CSS, JS, brand assets
```

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

Každá stránka načítá jen svůj CSS přes `{% block page_styles %}` s `<link>` tagem.

### Landing page

Soubor: `backend/templates/public/home.html` (extends `public/base_public.html`)

Sekce: Hero (dashboard mockup) → Features (6 karet) → Jak to funguje (3 kroky) → Pro koho (Coach + Athlete) → CTA

Cílí primárně na **trenéry**. Design přístup: "Coach Command Center".

Home page overriduje `{% block topbar_links %}` (přidává anchory #features, #how, #audience) a `{% block topbar_actions %}` (lime CTA "Začít zdarma" místo login tlačítka).

---

## Důležitá pravidla

- **Nezasahuj do aplikačního kódu** pokud user explicitně nepožádá — dashboard, auth, modely, views jsou stabilní
- Page-specific styly jdou do externího CSS souboru, načteného přes `{% block page_styles %}` — **ne inline `<style>` tag**
- Bilingualita: všechny texty v templates musí mít CS i EN variantu přes `{% if CURRENT_LANGUAGE == "en" %}`
- Fonty: Syne + Inter + JetBrains Mono — načítá `base_public.html`, v page templates se nepřidávají znovu
- Bootstrap 5 je k dispozici, ale UI se staví přes vlastní CSS třídy s `eb-` prefixem
- Prefix `eb-` pro sdílené CSS třídy; `lp-` pro landing-page-only třídy
- Každý template musí mít `{% load static %}` pokud používá `{% static %}`

---

## Demo

```bash
cd backend
python manage.py seed_coach_demo
# coach_demo@endurobuddy.local / demo12345
```
