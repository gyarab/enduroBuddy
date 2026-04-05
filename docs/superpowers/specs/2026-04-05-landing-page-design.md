# EnduroBuddy — Complete Design Language

**Date:** 2026-04-05
**Concept:** Neon Lab × Swiss Precision
**Status:** In progress

---

## Design Philosophy

EnduroBuddy's visual identity lives at the intersection of two worlds:

**Swiss Precision** — Mathematical spacing, obsessive readability, grid discipline, generous whitespace even in dark mode. Every element earns its place. Data is sovereign.

**Neon Lab** — Electric accent colors used surgically, bold typographic scale as a design element, creative energy in the details. The brand has edge and personality.

The result: a tool that feels like a designer's precision instrument with moments of electric intensity. Not a fitness app. Not an analytics dashboard. A **modern training workspace** with unmistakable identity.

---

## Logo

### Concept: "Stride Mark"

The logomark is three horizontal bars of increasing length, slightly tilted forward (≈ 6° lean). They represent:
- Forward momentum (the tilt)
- Training progression (increasing size)
- Data visualization (bar chart)
- The letter "E" abstracted

Combined with a clean **Syne** wordmark. The mark uses the electric lime accent on dark, or dark on light backgrounds.

### Variants
- **Full logo** — mark + "EnduroBuddy" wordmark
- **Compact logo** — mark + "EB" monogram
- **Mark only** — the stride mark standalone (for favicons, app icons)
- **Wordmark only** — "EnduroBuddy" in Syne 700

### Logo files
- `backend/static/brand/eb-logo-full.svg`
- `backend/static/brand/eb-logo-compact.svg`
- `backend/static/brand/eb-mark.svg`
- `backend/static/brand/eb-wordmark.svg`

---

## Color System

### Philosophy
Near-black base with zero color cast. Accents used like a scalpel — precisely, sparingly, with maximum impact. Two accent colors create a visual hierarchy: lime for action, blue for information.

### Core Palette

```
Token               Hex         Usage
─────────────────────────────────────────────────────
--eb-bg             #09090b     Page background (true dark, colorless)
--eb-bg-elevated    #111113     Elevated background, nav, sidebar
--eb-surface        #18181b     Cards, panels, modals
--eb-surface-hover  #27272a     Hover state for surfaces
--eb-border         #27272a     Primary borders
--eb-border-soft    #1f1f23     Subtle borders, dividers
--eb-text           #fafafa     Primary text
--eb-text-secondary #a1a1aa     Secondary text, descriptions
--eb-text-muted     #71717a     Muted text, placeholders, meta
```

### Accent Colors

```
Token               Hex         Usage
─────────────────────────────────────────────────────
--eb-lime           #c8ff00     Primary CTA, active states, key highlights
--eb-lime-hover     #d4ff33     Hover state for lime
--eb-lime-muted     rgba(200,255,0,.12)   Lime backgrounds
--eb-blue           #38bdf8     Info states, secondary actions, links
--eb-blue-muted     rgba(56,189,248,.12)  Blue backgrounds
```

### Status Colors

```
Token               Hex         Usage
─────────────────────────────────────────────────────
--eb-done           #c8ff00     Completed / success (lime)
--eb-planned        #38bdf8     Planned / scheduled (blue)
--eb-missed         #f43f5e     Missed / error / danger
--eb-pending        #f59e0b     Pending / warning
--eb-rest           #71717a     Rest day / inactive
```

### Role Colors

```
Token               Hex         Usage
─────────────────────────────────────────────────────
--eb-coach          #c8ff00     Coach badge, coach UI accents
--eb-athlete        #38bdf8     Athlete badge, athlete UI accents
```

### Ratio
- 80% neutral dark surfaces
- 12% borders, shadows, structure
- 8% accent and status colors

---

## Typography

### Font Stack

```
--eb-font-display:  "Syne", system-ui, sans-serif
--eb-font-body:     "Inter", "Segoe UI Variable Text", system-ui, sans-serif
--eb-font-mono:     "JetBrains Mono", "Cascadia Code", monospace
```

**Syne** — Geometric display font with character. Used for headlines, brand, hero text, section titles. Bold, distinctive letterforms bridge creativity (Neon Lab) with geometric roots (Swiss).

**Inter** — The ultimate precision UI font. Peak readability at all sizes. Used for body text, forms, tables, labels, navigation — everything that needs to be scanned quickly.

**JetBrains Mono** — For numeric data, pace values, distances, code-like elements. Tabular figures, clean ligatures.

### Type Scale

```
Level               Size                    Font        Weight  Tracking
───────────────────────────────────────────────────────────────────────
Display             clamp(3rem, 8vw, 6rem)  Syne        800     -0.04em
H1                  clamp(2rem, 5vw, 3.5rem) Syne       700     -0.03em
H2                  clamp(1.5rem, 3vw, 2rem) Syne       700     -0.02em
H3                  1.125rem                Inter       600     -0.01em
Body                0.9375rem (15px)        Inter       400     0
Small               0.8125rem (13px)        Inter       500     0.01em
Label               0.75rem (12px)          Inter       600     0.06em
Mono Data           0.875rem (14px)         JetBrains   500     0
```

### Rules
- Syne is NEVER used below 18px
- Inter handles all functional UI text
- JetBrains Mono for: pace (4:52), distance (12.3 km), HR (142 bpm), timestamps
- Labels are Inter uppercase with wide tracking — never Syne
- Line-height: 1.0 for display, 1.3 for headings, 1.6 for body

---

## Spacing & Grid

### Base Unit: 4px

```
--eb-space-1:   4px
--eb-space-2:   8px
--eb-space-3:   12px
--eb-space-4:   16px
--eb-space-5:   20px
--eb-space-6:   24px
--eb-space-8:   32px
--eb-space-10:  40px
--eb-space-12:  48px
--eb-space-16:  64px
--eb-space-20:  80px
```

### Layout Widths
- Max content width: 1280px
- Dashboard max: 100% (fluid)
- Card padding: 24px (desktop), 16px (mobile)
- Section gap: 48px (desktop), 32px (mobile)

### Border Radius

```
--eb-radius-sm:    6px    (inputs, small elements)
--eb-radius-md:    10px   (cards, dropdowns)
--eb-radius-lg:    16px   (modals, panels)
--eb-radius-xl:    24px   (hero blocks)
--eb-radius-full:  9999px (pills, badges)
```

---

## Shadows

```
--eb-shadow-sm:   0 1px 2px rgba(0,0,0,.3)
--eb-shadow-md:   0 4px 16px rgba(0,0,0,.4)
--eb-shadow-lg:   0 12px 40px rgba(0,0,0,.5)
--eb-shadow-xl:   0 24px 64px rgba(0,0,0,.6)
--eb-glow-lime:   0 0 20px rgba(200,255,0,.15)
--eb-glow-blue:   0 0 20px rgba(56,189,248,.15)
```

---

## Components

### Buttons

| Variant     | Background               | Border                     | Text Color | Usage |
|------------|--------------------------|----------------------------|------------|-------|
| Primary    | --eb-lime                | transparent                | #09090b    | Single dominant CTA per surface |
| Secondary  | transparent              | --eb-border                | --eb-text  | Secondary actions |
| Ghost      | transparent              | transparent                | --eb-text-secondary | Tertiary, nav |
| Danger     | rgba(244,63,94,.12)      | rgba(244,63,94,.25)        | #fda4af    | Destructive actions |

- Height: 40px default, 32px small, 48px large
- Font: Inter 600, 13px, uppercase, tracking 0.04em
- Radius: --eb-radius-sm (6px)
- Hover: translateY(-1px) + subtle glow for primary
- Pill variant: radius-full

### Form Controls
- Height: 40px
- Background: --eb-surface
- Border: 1px solid --eb-border
- Radius: --eb-radius-sm
- Focus: border-color lime + box-shadow glow-lime
- Placeholder: --eb-text-muted

### Cards
- Background: --eb-surface
- Border: 1px solid --eb-border-soft
- Radius: --eb-radius-md
- Padding: 24px
- Hover (if interactive): border-color brightens, subtle translateY(-2px)

### Badges

| Variant  | Text Color | Background             | Border |
|----------|-----------|------------------------|--------|
| Done     | --eb-lime | --eb-lime-muted        | rgba lime 20% |
| Planned  | --eb-blue | --eb-blue-muted        | rgba blue 20% |
| Missed   | #fda4af   | rgba(244,63,94,.1)     | rgba red 20% |
| Pending  | #fcd34d   | rgba(245,158,11,.1)    | rgba yellow 20% |
| Coach    | --eb-lime | --eb-lime-muted        | rgba lime 20% |
| Athlete  | --eb-blue | --eb-blue-muted        | rgba blue 20% |

- Height: 24px
- Font: Inter 600, 11px, uppercase, tracking 0.06em
- Radius: full (pill)

### Tables
- Header: Inter 600, 11px, uppercase, tracking 0.08em, --eb-text-muted
- Cell: 14px, --eb-text
- Row border: 1px --eb-border-soft
- Hover: background --eb-surface-hover
- Numeric cells: JetBrains Mono

### Navigation
- Topbar: --eb-bg-elevated + 1px border-bottom + backdrop-filter blur(12px)
- Nav links: Inter 600, 12px, uppercase, tracking 0.06em
- Active: --eb-lime text
- Hover: --eb-text + subtle bg

### Modals
- Overlay: rgba(0,0,0,.6) + backdrop-blur(4px)
- Surface: --eb-surface, radius-lg, shadow-xl
- Header: border-bottom, padding 20px 24px
- Footer: border-top, padding 16px 24px, flex end

---

## Motion

### Principles
- Motion serves orientation, not decoration
- No bounce, no elastic, no energy flash
- Everything ease-out for entry, ease-in-out for state changes

### Timing
```
Micro interactions:  120ms (hover, focus)
Standard:            180ms (dropdowns, toggles)
Entrance:            300ms (modal open, card appear)
Page transition:     500ms (route changes, scroll reveals)
```

### Scroll Reveal
- opacity 0→1, translateY(16px→0)
- 500ms ease-out
- Stagger: +80ms per element

### Hover
- Buttons: translateY(-1px), 120ms
- Cards: translateY(-2px) + border brighten, 180ms
- Nav links: color shift, 120ms

---

## Landing Page Structure

### Topbar (sticky)
Logo left · Nav center · CTA right · blur backdrop

### Hero
Two-column. Left: eyebrow pill + H1 (Syne 800, one word in lime) + subtitle + CTA + pills row. Right: dashboard mockup panel.

### Features (#features)
Section label + H2. 3×2 card grid: icon + title + one-liner.

### How it works (#how)
3 numbered steps left + visual panel right.

### Roles (#audience)
Two cards: Coach (lime badge) + Athlete (blue badge) with bullet lists.

### CTA
Centered block, lime glow, H2 + subtitle + button.

### Footer
Brand + links + language switcher.

---

## Accessibility

- Contrast: all text meets WCAG AA (4.5:1 body, 3:1 large)
- Lime #c8ff00 on #09090b = 15.2:1 ratio (AAA)
- Focus rings always visible (2px lime outline + 2px offset)
- Hit areas minimum 40×40px
- Status never indicated by color alone
- Reduced motion: respect prefers-reduced-motion

---

## Implementation Notes

- CSS custom properties on :root
- Dark mode only for v1 (light mode later)
- Fonts loaded via Google Fonts: Syne (700, 800), Inter (400, 500, 600), JetBrains Mono (500)
- No external icon library — inline SVG
- Landing page: inline styles in page_styles block
- App: shared CSS file (base.css refactor)
