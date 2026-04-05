# Landing Page Design — EnduroBuddy

**Date:** 2026-04-05
**Approach:** Coach Command Center
**Status:** Approved

---

## Summary

Modern, professional landing page for EnduroBuddy targeting coaches as the primary audience. Medium length — hero + features + how it works + roles + CTA. High-energy tech aesthetic (neon yellow/green on deep dark background), with restrained accent usage. Does not touch the existing application code.

---

## Goals

- Present the product to undecided users (primarily coaches)
- Provide a clear path to registration
- Communicate the coach-athlete collaboration value proposition
- Reflect the existing visual language established in home.html and visual-style-guide.md

---

## Visual Language

### Palette (landing page specific)

```
Background:   #0a0d0f  (deep dark base)
Surface:      #13181b  (cards, panels)
Surface-2:    #181d21  (hover state)
Border:       rgba(255,255,255,.07)
Accent 1:     #e8f04a  (neon yellow — primary CTA, 1-2 hero em words only)
Accent 2:     #3dffa0  (neon green — done states, athlete badges)
Text:         #f0f2f0
Muted:        #9aab9e / #6b7a72
```

**Usage rule:** Accent yellow is used sparingly — primary CTA button and at most one `<em>` in the hero H1. Never used for decorative purposes.

### Typography

- **Hero H1:** `League Gothic`, uppercase, `clamp(2.8rem, 8vw, 5.6rem)`, tight letter-spacing (−0.05em)
- **Labels / pills / badges:** `Barlow Semi Condensed`, uppercase, 700 weight
- **Body / UI text:** `IBM Plex Sans`, 400–600 weight
- **Section titles:** `League Gothic` or `Barlow Semi Condensed` uppercase

### Shape & Texture

- Border radius: 18px for panels and cards
- Borders: thin, low-contrast (rgba white 7%)
- Shadows: deep (0 40px 80px rgba(0,0,0,.45))
- Background texture: SVG noise overlay at 35% opacity (already in home.html)
- Animations: `lpFloatIn` on hero elements (staggered), `lpFloat` on floating card

---

## Page Structure

### Topbar (sticky, blur backdrop)

- Logo left (`biglogo.png`)
- Nav links: Funkce | Jak funguje | Pro koho | O aplikaci
- Right: "Začít zdarma" CTA (yellow), CZ/EN language switcher
- Background: `rgba(10,13,15,.84)` + `backdrop-filter: blur(18px)`

---

### Section 1 — Hero (`#hero`)

Two-column grid (1fr / 0.92fr), full viewport height on desktop.

**Left column:**
- Eyebrow pill: pulsing dot + "Vytrvalostní trénink" / "Endurance training platform"
- H1 with `<em>` on key word (yellow): *"Měj plán, realitu i sportovce **pod kontrolou.**"*
- Subtitle (max 36rem): EnduroBuddy spojuje měsíční tréninkové plány, splněné aktivity a spolupráci trenéra se sportovcem do jednoho moderního rozhraní.
- Actions: primary CTA "Vyzkoušet zdarma" + text link "Jak to funguje →"
- Pills row: "Měsíční plánování" · "Plán vs realita" · "Trenér + sportovec"

**Right column:**
- Dashboard mockup panel (window chrome: red/yellow/green dots)
- Panel label: "endurobuddy.app – Tréninkový plán"
- 7-day week grid: mix of `done` (green border), `plan` (yellow border), `rest` days
- Activity feed below grid: 2 activity rows with icon, name, meta (distance, pace, time), badge
- Floating stats card (absolute positioned, animated float): volume metric

---

### Section 2 — Features (`#features`)

Label: "→ FUNKCE" in accent yellow
Section title: "Vše co trenér potřebuje" (League Gothic uppercase)
Lead text: 1 sentence

**3×2 card grid:**

| # | Icon | Title | Copy |
|---|------|-------|------|
| 1 | 📅 | Měsíční plánování | Připrav plán pro každého sportovce na celý měsíc dopředu. |
| 2 | ✓ | Plán vs. realita | Porovnej co bylo naplánováno s tím, co sportovec skutečně absolvoval. |
| 3 | ⚡ | Garmin Connect | Synchronizuj aktivity přímo z Garmin účtu sportovce automaticky. |
| 4 | 📁 | FIT import | Importuj soubory z libovolného GPS zařízení. |
| 5 | 👥 | Tréninkové skupiny | Organizuj sportovce do skupin a sdílej plány hromadně. |
| 6 | 👁 | Coach přehled | Sleduj všechny svěřence na jednom místě, filtruj a porovnávej. |

Cards: hover lifts 3px, border brightens, background shifts to surface-2.

---

### Section 3 — How it works (`#how`)

Two-column grid (1fr / 1fr), aligned center.

**Left column — numbered steps:**
1. Připrav měsíční plán — Vytvoř tréninkový plán pro sportovce nebo skupinu. Definuj typ, objem a intenzitu každého tréninku.
2. Sdílej se sportovci — Sportovci vidí svůj plán okamžitě. Připojí se přes coach join code nebo skupinovou pozvánku.
3. Sleduj plnění — Sportovci zapisují splněné tréninky a importují aktivity z Garminu nebo FIT souborů. Vidíš vše v reálném čase.

**Right column:** Dashboard panel mockup showing activity log / completed training feed.

---

### Section 4 — Pro koho (`#audience`)

Label + section title: "Pro trenéry i sportovce"
Two-column card layout.

**Coach card** (yellow badge):
- Badge: "Coach"
- Heading: "Pro trenéry"
- List (→ prefix): Připravuje měsíční plány / Spravuje více sportovců / Organizuje skupiny / Sleduje plnění v přehledu / Exportuje a analyzuje data

**Athlete card** (green badge):
- Badge: "Athlete"
- Heading: "Pro sportovce"
- List (→ prefix): Vidí svůj plán den po dni / Zapisuje splněné tréninky / Importuje aktivity z Garminu / Páruje plánované vs. skutečné / Sdílí výsledky s trenérem

---

### Section 5 — CTA

Centered block, radial gradient backdrop (yellow glow at top center).
- H2: "Začni plánovat lépe ještě dnes" (League Gothic)
- Subtitle: "Registrace je zdarma. Žádná kreditní karta."
- Button: "Začít zdarma →" (primary yellow CTA)

---

### Footer

Keep existing footer unchanged.

---

## Responsiveness

| Breakpoint | Change |
|-----------|--------|
| < 1200px | Hero and How-it-works go single column |
| < 992px | Hero min-height auto, reduced padding |
| < 768px | Feature grid single column, week grid 4 cols, floating card goes static |
| < 576px | Reduced section padding, week grid 2 cols |

---

## Animations

- Hero left column: `lpFloatIn` 0.8s delay 0.08s
- Hero right column: `lpFloatIn` 0.85s delay 0.2s
- Feature/section cards: `fade-up` IntersectionObserver on scroll
- Eyebrow dot: `lpPulse` 2s infinite
- Floating stats card: `lpFloat` 4s infinite
- Duration: 140–220ms for interactions, 600ms for scroll reveals

---

## Out of Scope

- Touch the existing application code (dashboard, auth, etc.)
- Testimonials / social proof section
- FAQ section
- Pricing section
- SEO meta tags beyond existing base template

---

## Implementation Notes

- Lives in `backend/templates/public/home.html` (extends `public/base_public.html`)
- Bilingual (CS/EN) via Django i18n — all strings need both language variants
- Styles go in `{% block page_styles %}` as `<style>` tag (existing pattern)
- No new static files needed — all fonts already loaded in base_public.html
- The visual style preview update (`docs/visual-style-preview.html`) should reflect the final landing page design language
