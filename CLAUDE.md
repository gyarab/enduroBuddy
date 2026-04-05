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

## Vizuální design systém

Dokumentace: `docs/visual-style-guide.md`
HTML showcase (app shell): `docs/visual-style-preview.html`
HTML showcase (dashboard): `docs/dashboard-visual-style-preview.html`

**Paleta (app):**
- Pozadí: `#101714` (Ink 950)
- Akcent: `#61c48f` (klidná zelená)
- Display font: Space Grotesk (pro nadpisy a logo)
- UI font: IBM Plex Sans

**Paleta (landing page — odlišná od app):**
- Pozadí: `#0a0d0f` (hlubší tmavá)
- Akcent 1: `#e8f04a` (neon žlutá — pouze CTA a 1 em v hero)
- Akcent 2: `#3dffa0` (neon zelená — done stavy)
- Display font: League Gothic uppercase
- UI font: IBM Plex Sans

---

## Landing page

Soubor: `backend/templates/public/home.html` (extends `public/base_public.html`)

Sekce: Hero (dashboard mockup) → Features (6 karet) → Jak to funguje (3 kroky) → Pro koho (Coach + Athlete) → CTA

Cílí primárně na **trenéry**. Design přístup: "Coach Command Center".

Spec: `docs/superpowers/specs/2026-04-05-landing-page-design.md`

---

## Důležitá pravidla

- **Nezasahuj do aplikačního kódu** pokud user explicitně nepožádá — dashboard, auth, modely, views jsou stabilní
- Styly landing page jdou do `{% block page_styles %}` jako inline `<style>` tag (existující pattern)
- Bilingualita: všechny texty v templates musí mít CS i EN variantu přes `{% if CURRENT_LANGUAGE == "en" %}`
- Fonty jsou načteny v `base_public.html` — nepřidávat duplikáty
- Bootstrap 5 je k dispozici, ale UI se staví přes vlastní CSS třídy s `eb-` prefixem

---

## Demo

```bash
cd backend
python manage.py seed_coach_demo
# coach_demo@endurobuddy.local / demo12345
```
