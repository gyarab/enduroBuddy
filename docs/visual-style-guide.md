# EnduroBuddy Visual Style Guide

## Koncept: Neon Lab × Swiss Precision

EnduroBuddy má působit jako designérský precision instrument s momenty elektrické intenzity. Ne fitness app, ne analytics dashboard — moderní training workspace s nezaměnitelnou identitou.

**Swiss Precision** — matematický spacing, obsesivní čitelnost, grid disciplína, vzduch i v dark mode.

**Neon Lab** — elektrické akcenty použité chirurgicky, bold typografická škála, kreativní energie v detailech.

### Co vědomě neděláme

- Fitness-marketing vizuál, agresivní gradienty, sport piktogramy
- Přeplněný analytický cockpit (intervals.icu style)
- Sportovní sociální síť (Strava style)
- Utilitární systémový vzhled (Garmin Connect style)

EnduroBuddy je **čistý tréninkový workspace** s edge a personalitou.

---

## Logo — Velocity Bars

Tři vertikální obdélníky rostoucí výšky, zkosené -9° doprava. Gradientní opacity zleva (0.38 → 0.68 → 1.0) vytváří hloubku bez dalších barev.

Reprezentuje:
- **Stupňující se intenzitu** — tréninkové zóny 1–3
- **Progres a sílu** — klíčové hodnoty endurance tréninku
- **Data a precision** — tři diskrétní hodnoty jako vizualizace

### Geometrie (viewBox 48×48)

| Bar | x  | y  | width | height | rx  | opacity | transform |
|-----|----|----|-------|--------|-----|---------|-----------|
| 1   | 6  | 33 | 9     | 10     | 2.5 | 0.38    | skewX(-9) |
| 2   | 19 | 25 | 9     | 18     | 2.5 | 0.68    | skewX(-9) |
| 3   | 32 | 14 | 9     | 29     | 2.5 | 1.0     | skewX(-9) |

Glow: `feGaussianBlur stdDeviation="2.2"` + feMerge overlay. Vypnout pod 20px a na světlém pozadí.

### Varianty

| Soubor | Použití |
|--------|---------|
| `eb-mark.svg` | Favicon, app ikona, malé kontexty |
| `eb-logo-full.svg` | Mark + "EnduroBuddy" wordmark |
| `eb-logo-compact.svg` | Mark + "EB" monogram |
<<<<<<< HEAD
| `eb-wordmark.svg` | Pouze wordmark (Syne 700) |
=======
| `eb-wordmark.svg` | Pouze wordmark (Space Grotesk 700) |
>>>>>>> vue-frontend-codex
| `eb-social-dark.svg` | IG/X avatar, tmavé pozadí |
| `eb-social-lime.svg` | IG/X avatar, lime pozadí |
| `eb-social-dark-rounded.svg` | IG rounded corners |
| `eb-social-github.svg` | GitHub circle-safe |
| `eb-social-banner.svg` | OG / Twitter card (1200×630) |

Všechny v `backend/static/brand/`.

### Pravidla

- Mark je lime na tmavém, dark na lime/světlém — bez glow na světlém
<<<<<<< HEAD
- Wordmark vždy v Syne 700
=======
- Wordmark vždy v Space Grotesk 700
>>>>>>> vue-frontend-codex
- Minimální velikost marku: 16px (bez glow efektu)
- Kolem marku safe zone = šířka jednoho baru (~⅕ celkové šířky)

---

## Barevný systém

### Pozadí a povrchy

```
Token               Hex         Použití
─────────────────────────────────────────────────
--eb-bg             #09090b     Pozadí stránky (true dark, bez barevného nádechu)
--eb-bg-elevated    #111113     Nav, sidebar, elevated plochy
--eb-surface        #18181b     Karty, panely, modaly
--eb-surface-hover  #27272a     Hover state
```

### Bordery

```
--eb-border         #27272a     Primární bordery
--eb-border-soft    #1f1f23     Subtilní bordery, dividery
```

### Text

```
--eb-text           #fafafa     Primární text
--eb-text-secondary #a1a1aa     Sekundární text, popisy
--eb-text-muted     #71717a     Meta text, placeholder
```

### Akcenty

```
--eb-lime           #c8ff00     Primární CTA, done, coach, klíčové highlights
--eb-lime-hover     #d4ff33     Hover lime
--eb-lime-muted     rgba(200,255,0,.12)   Lime pozadí
--eb-lime-border    rgba(200,255,0,.20)   Lime border (active pills, hover btn)
--eb-blue           #38bdf8     Info, planned, athlete, sekundární akce
--eb-blue-muted     rgba(56,189,248,.12)  Blue pozadí
--eb-blue-border    rgba(56,189,248,.20)  Blue border
```

### Status

```
--eb-danger         #f43f5e     Chyba, missed, smazání
--eb-warning        #f59e0b     Pending, varování
```

### Role

```
--eb-coach          #c8ff00     Coach badge a UI akcenty
--eb-athlete        #38bdf8     Athlete badge a UI akcenty
```

### Poměr barev

- 80 % neutrální tmavé povrchy
- 12 % bordery, stíny, struktura
- 8 % akcenty a stavové barvy

### Kontrast

- Lime `#c8ff00` na `#09090b` = 15.2:1 (AAA)
- Text `#fafafa` na `#18181b` = 14.8:1 (AAA)
- Muted `#71717a` na `#09090b` = 4.6:1 (AA)

---

## Typografie

### Font stack

```css
<<<<<<< HEAD
--eb-font-display: "Syne", system-ui, sans-serif;
=======
--eb-font-display: "Space Grotesk", system-ui, sans-serif;
>>>>>>> vue-frontend-codex
--eb-font-body:    "Inter", "Segoe UI Variable Text", system-ui, sans-serif;
--eb-font-mono:    "JetBrains Mono", "Cascadia Code", monospace;
```

<<<<<<< HEAD
**Syne** — Geometrický display font s charakterem. Headlines, brand, hero, section titles.
=======
**Space Grotesk** — Technický display font s precision-nástroj charakterem. Headlines, brand, hero, section titles. Nahradil Syne pro čistší výsledek v tmavém UI.
>>>>>>> vue-frontend-codex

**Inter** — Precision UI font. Body text, formuláře, tabulky, labely, navigace.

**JetBrains Mono** — Numerická data: pace, distance, HR, timestamps.

### Typografická hierarchie

```
<<<<<<< HEAD
Level           Size                        Font            Weight   Tracking
─────────────────────────────────────────────────────────────────────────────
Display         clamp(3rem, 8vw, 6rem)      Syne            800      -0.04em
H1              clamp(2rem, 5vw, 3.5rem)    Syne            700      -0.03em
H2              clamp(1.5rem, 3vw, 2rem)    Syne            700      -0.02em
H3              1.125rem                    Inter           600      -0.01em
Body            0.9375rem (15px)            Inter           400      0
Small           0.8125rem (13px)            Inter           500      0.01em
Label           0.75rem (12px)              Inter           600      0.06em
Mono Data       0.875rem (14px)             JetBrains       500      0
=======
Level           Size                           Font             Weight   Tracking
──────────────────────────────────────────────────────────────────────────────────
Display         clamp(2.5rem, 6vw, 4.5rem)     Space Grotesk    700      -0.05em
H1              clamp(1.75rem, 4vw, 2.75rem)   Space Grotesk    700      -0.04em
H2              clamp(1.25rem, 2.5vw, 1.75rem) Space Grotesk    600      -0.025em
H3              1.0625rem (17px)               Space Grotesk    500      -0.01em
Body            0.9375rem (15px)               Inter            400      0
Small           0.8125rem (13px)               Inter            500      0.01em
Label           0.6875rem (11px)               Inter            600      0.07em
Mono Data       0.875rem (14px)                JetBrains Mono   500      -0.02em
>>>>>>> vue-frontend-codex
```

### Pravidla

<<<<<<< HEAD
- Syne NIKDY pod 18px
- Inter pro veškerý funkční UI text
- JetBrains Mono pro: pace (4:52), distance (12.3 km), HR (142 bpm), timestamps
- Labely jsou Inter uppercase s wide tracking — nikdy Syne
- Line-height: 0.9-1.0 pro display, 1.3 pro headings, 1.6 pro body
=======
- Space Grotesk pro Display, H1, H2, H3 — celá heading hierarchie z jednoho fontu
- Inter pro veškerý funkční UI text (Body, Small, Label, tlačítka, formuláře)
- JetBrains Mono pro: pace (4:52), distance (12.3 km), HR (142 bpm), timestamps
- Labely jsou Inter uppercase s wide tracking — nikdy Space Grotesk
- Line-height: 0.95 pro display, 1.05–1.3 pro headings, 1.6 pro body
>>>>>>> vue-frontend-codex

---

## Spacing & Grid

### Base unit: 4px

```
--eb-space-1:   4px     --eb-space-8:   32px
--eb-space-2:   8px     --eb-space-10:  40px
--eb-space-3:   12px    --eb-space-12:  48px
--eb-space-4:   16px    --eb-space-16:  64px
--eb-space-5:   20px    --eb-space-20:  80px
--eb-space-6:   24px
```

### Layout

- Max content width: 1280px
- Dashboard: fluid 100%
- Card padding: 24px (desktop), 16px (mobile)
- Section gap: 48-64px (desktop), 32px (mobile)

### Border radius

```
--eb-radius-sm:    6px     Inputy, malé elementy
--eb-radius-md:    10px    Karty, dropdowny
--eb-radius-lg:    16px    Modaly, panely
--eb-radius-xl:    24px    Hero bloky
--eb-radius-full:  9999px  Pills, badges
```

---

## Stíny

```
--eb-shadow-sm:   0 1px 2px rgba(0,0,0,.3)
--eb-shadow-md:   0 4px 16px rgba(0,0,0,.4)
--eb-shadow-lg:   0 12px 40px rgba(0,0,0,.5)
--eb-shadow-xl:   0 24px 64px rgba(0,0,0,.6)
--eb-glow-lime:   0 0 20px rgba(200,255,0,.15)
--eb-glow-blue:   0 0 20px rgba(56,189,248,.15)
```

---

## Komponenty

### Tlačítka

| Varianta   | Background          | Border              | Text    | Použití |
|-----------|--------------------|--------------------|---------|---------|
| Primary   | --eb-lime          | transparent         | #09090b | Single CTA per surface |
| Secondary | transparent        | --eb-border         | --eb-text | Sekundární akce |
| Ghost     | transparent        | transparent         | --eb-text-secondary | Terciární, nav |
| Danger    | rgba(244,63,94,.12)| rgba(244,63,94,.25) | #fda4af | Destruktivní akce |

- Výška: 40px default, 32px small, 48px large
- Font: Inter 600, 13px, letter-spacing 0.02em
- Radius: --eb-radius-sm (6px)
- Hover: translateY(-1px) + glow pro primary
- Pill varianta: radius-full

### Formuláře

- Výška: 40px
- Background: --eb-bg
- Border: 1px solid --eb-border
- Radius: --eb-radius-sm
- Focus: border lime + box-shadow glow-lime
- Placeholder: --eb-text-muted

### Karty

- Background: --eb-surface
- Border: 1px solid --eb-border-soft
- Radius: --eb-radius-md (10px)
- Padding: 24px
- Hover (interaktivní): border brightens, translateY(-2px)

### Badges

| Varianta | Text        | Background          | Border |
|----------|------------|--------------------|----|
| Done     | --eb-lime  | --eb-lime-muted    | rgba lime 20% |
| Planned  | --eb-blue  | --eb-blue-muted    | rgba blue 20% |
| Missed   | #fda4af    | rgba(244,63,94,.1) | rgba red 20% |
| Pending  | #fcd34d    | rgba(245,158,11,.1)| rgba yellow 20% |
| Coach    | --eb-lime  | --eb-lime-muted    | rgba lime 20% |
| Athlete  | --eb-blue  | --eb-blue-muted    | rgba blue 20% |

- Výška: 22px, pill shape
- Font: Inter 600, 11px, uppercase, tracking 0.04em

### Tabulky

- Header: Inter 600, 11px, uppercase, tracking 0.08em, --eb-text-muted
- Cell: 14px, --eb-text
- Row border: 1px --eb-border-soft
- Hover: background --eb-surface-hover
- Numerické buňky: JetBrains Mono

### Navigace

- Topbar: --eb-bg-elevated, 1px border-bottom, backdrop-filter blur(12px)
- Nav links: Inter 600, 12px, uppercase, tracking 0.06em
- Active: --eb-lime
- Hover: --eb-text + subtle bg

### Modaly

- Overlay: rgba(0,0,0,.6) + backdrop-blur(4px)
- Surface: --eb-surface, radius-lg, shadow-xl
- Header/footer s border

---

## Motion

### Principy

- Pohyb slouží orientaci, ne dekoraci
- Žádný bounce, elastic nebo energy flash
- ease-out pro vstup, ease-in-out pro změny stavu

### Timing

```
Micro interakce:  120ms   (hover, focus)
Standard:         180ms   (dropdown, toggle)
Entrance:         300ms   (modal, card appear)
Page transition:  500ms   (scroll reveal, route change)
```

### Scroll reveal

- opacity 0→1, translateY(16px→0)
- 500ms ease-out
- Stagger: +80ms per element

### prefers-reduced-motion

Vždy respektovat. Při reduced-motion vypnout všechny animace.

---

## Přístupnost

- Kontrast: WCAG AA minimum (4.5:1 body, 3:1 large text)
- Focus ring: 2px lime outline + 2px offset, vždy viditelný
- Hit area: minimum 40×40px
- Status nikdy jen barvou — vždy s textem nebo ikonou

---

## CSS architektura — public sekce

Tokeny a sdílené styly žijí v `public-base.css`; page-specific styly v samostatných souborech.

| Soubor | Obsah |
|--------|-------|
| `backend/static/css/public-base.css` | `:root` tokeny, body reset, `.eb-public-shell`, `.eb-topbar`, `.eb-footer` |
| `backend/static/css/public-home.css` | Landing page — `--lp-*` aliasy + všechny sekce (`lp-` prefix) |
| `backend/static/css/public-about.css` | About page — 4 sekce (`eb-about-*` prefix) |
| `backend/static/css/public-legal.css` | Privacy + Terms (`eb-legal-*` prefix) |

### Shell a topbar

- `.eb-public-shell` — `min(1280px, calc(100% - 48px))`, `margin-inline: auto`
- `.eb-topbar` — sticky, `rgba(17,17,19,.92)`, `backdrop-filter: blur(12px)`
- `.eb-topbar-inner` — `position: relative`; nav je `position: absolute; left: 50%; transform: translateX(-50%)`
- Logo: `eb-logo-full.svg` na desktopu, `eb-logo-compact.svg` pod 768px
- Nav skryt na mobilech pod 768px (hamburger menu zatím není)

### Bloky k přepsání v page templates

```django
{% block page_styles %}   {# <link> na page CSS #}
{% block topbar_links %}  {# vlastní nav linky (home page overriduje na anchory) #}
{% block topbar_actions %} {# login btn nebo lime CTA #}
{% block content %}       {# main obsah stránky #}
{% block footer %}        {# footer (standardní, přepisovat jen výjimečně) #}
```

---

## HTML showcase

Soubor `docs/visual-style-preview.html` obsahuje živé ukázky:

- Logo (Signal Stack) ve všech variantách + social media avatary
- Kompletní paleta (12 swatches)
- Typografická škála (9 úrovní)
- Topbar simulace
- Tlačítka (5 variant × 3 velikosti)
- Badges a labely
- Formulářové prvky
- Metrické karty
- Tabulka s mono daty
- Hero section simulace s dashboard mockupem
- Feature cards (3×2 grid)
- Steps + role cards
- Modal + toast notifikace
- Skeleton loading
- CTA block
- Spacing/radius reference
- Motion pravidla
