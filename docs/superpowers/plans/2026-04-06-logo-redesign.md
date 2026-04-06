# Logo Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nahradit stávající ECG pulse logo za nový Velocity Bars mark a aktualizovat celý logo systém (9 SVG souborů + visual-style-guide.md).

**Architecture:** Každý SVG soubor se přepisuje samostatně. Všechny soubory sdílejí stejnou základní geometrii marku (3 obdélníky, skewX -9°, gradientní opacity). Testy jsou vizuální — každý soubor se ověří otevřením v prohlížeči. Žádné změny v kódu aplikace, jen `backend/static/brand/` + docs.

**Tech Stack:** SVG, Syne font (Google Fonts — použit v `<text>` elementu), žádné závislosti.

---

## Geometrie marku — reference

Všechny varianty sdílejí tuto základní definici (viewBox 48×48):

| Bar | x  | y  | width | height | rx  | opacity | transform  |
|-----|----|----|-------|--------|-----|---------|------------|
| 1   | 6  | 33 | 9     | 10     | 2.5 | 0.38    | skewX(-9)  |
| 2   | 19 | 25 | 9     | 18     | 2.5 | 0.68    | skewX(-9)  |
| 3   | 32 | 14 | 9     | 29     | 2.5 | 1.0     | skewX(-9)  |

Glow filter (pro tmavé pozadí, ≥ 20px):
```xml
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="blur"/>
  <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
```

---

## Task 1: eb-mark.svg

**Files:**
- Modify: `backend/static/brand/eb-mark.svg`

- [ ] **Přepsat soubor**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" fill="none">
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <g filter="url(#glow)">
    <rect x="6"  y="33" width="9" height="10" rx="2.5" fill="#c8ff00" opacity="0.38" transform="skewX(-9)"/>
    <rect x="19" y="25" width="9" height="18" rx="2.5" fill="#c8ff00" opacity="0.68" transform="skewX(-9)"/>
    <rect x="32" y="14" width="9" height="29" rx="2.5" fill="#c8ff00"               transform="skewX(-9)"/>
  </g>
</svg>
```

- [ ] **Vizuálně ověřit** — otevřít soubor v prohlížeči, zkontrolovat:
  - Tři sloupy rostoucí výšky, zkosené doprava
  - Lime barva, gradientní opacity (nejlevější nejslaběji)
  - Glow efekt je viditelný

- [ ] **Commit**

```bash
git add backend/static/brand/eb-mark.svg
git commit -m "feat: redesign eb-mark.svg with Velocity Bars"
```

---

## Task 2: eb-logo-full.svg

**Files:**
- Modify: `backend/static/brand/eb-logo-full.svg`

Soubor obsahuje mark + wordmark "EnduroBuddy". ViewBox zachováváme `320×64` (stejný jako originál — templates používají `height="28"` a aspect ratio se zachová). Mark je posunut o 8px dolů pro vertikální centrování v 64px výšce.

- [ ] **Přepsat soubor**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 64" fill="none">
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <!-- Mark — posunut translate(0,8) pro centrování v 64px výšce -->
  <g transform="translate(0, 8)" filter="url(#glow)">
    <rect x="6"  y="33" width="9" height="10" rx="2.5" fill="#c8ff00" opacity="0.38" transform="skewX(-9)"/>
    <rect x="19" y="25" width="9" height="18" rx="2.5" fill="#c8ff00" opacity="0.68" transform="skewX(-9)"/>
    <rect x="32" y="14" width="9" height="29" rx="2.5" fill="#c8ff00"               transform="skewX(-9)"/>
  </g>
  <!-- Wordmark — Syne 700 -->
  <text x="62" y="42" font-family="Syne, system-ui, sans-serif" font-weight="700" font-size="26" fill="#fafafa" letter-spacing="-0.5">EnduroBuddy</text>
</svg>
```

- [ ] **Vizuálně ověřit** — otevřít v prohlížeči, zkontrolovat:
  - Mark vlevo, wordmark vpravo, vertikálně zarovnány
  - Font "Syne" se načítá (pokud není dostupný offline, může fallback na system-ui)
  - Poměr mark : text je vizuálně vyvážený

- [ ] **Commit**

```bash
git add backend/static/brand/eb-logo-full.svg
git commit -m "feat: redesign eb-logo-full.svg with Velocity Bars"
```

---

## Task 3: eb-logo-compact.svg

**Files:**
- Modify: `backend/static/brand/eb-logo-compact.svg`

Mark + monogram "EB" (Syne 800, větší weight pro kompaktní variantu). ViewBox `140×64`.

- [ ] **Přepsat soubor**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 64" fill="none">
  <defs>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <g transform="translate(0, 8)" filter="url(#glow)">
    <rect x="6"  y="33" width="9" height="10" rx="2.5" fill="#c8ff00" opacity="0.38" transform="skewX(-9)"/>
    <rect x="19" y="25" width="9" height="18" rx="2.5" fill="#c8ff00" opacity="0.68" transform="skewX(-9)"/>
    <rect x="32" y="14" width="9" height="29" rx="2.5" fill="#c8ff00"               transform="skewX(-9)"/>
  </g>
  <text x="62" y="42" font-family="Syne, system-ui, sans-serif" font-weight="800" font-size="30" fill="#fafafa" letter-spacing="-1.5">EB</text>
</svg>
```

- [ ] **Vizuálně ověřit** — mark vlevo, "EB" vpravo, vertikálně zarovnány

- [ ] **Commit**

```bash
git add backend/static/brand/eb-logo-compact.svg
git commit -m "feat: redesign eb-logo-compact.svg with Velocity Bars"
```

---

## Task 4: eb-wordmark.svg

**Files:**
- Modify: `backend/static/brand/eb-wordmark.svg`

Pouze wordmark, žádný mark.

- [ ] **Přepsat soubor**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 48" fill="none">
  <text x="0" y="36" font-family="Syne, system-ui, sans-serif" font-weight="700" font-size="26" fill="#fafafa" letter-spacing="-0.5">EnduroBuddy</text>
</svg>
```

- [ ] **Vizuálně ověřit** — wordmark je čitelný, font je Syne (nebo system fallback)

- [ ] **Commit**

```bash
git add backend/static/brand/eb-wordmark.svg
git commit -m "feat: update eb-wordmark.svg (Syne 700)"
```

---

## Task 5: eb-social-dark.svg a eb-social-lime.svg

**Files:**
- Modify: `backend/static/brand/eb-social-dark.svg`
- Modify: `backend/static/brand/eb-social-lime.svg`

Čtvercové formáty 400×400 pro sociální sítě. Mark je scalovaný 4× (48px → 192px) a centrovaný. Filter stdDeviation se škáluje stejným faktorem (2.2 × 4 ≈ 8).

- [ ] **Přepsat eb-social-dark.svg**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" fill="none">
  <rect width="400" height="400" fill="#09090b"/>
  <defs>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <!-- Mark scale(4), translate tak aby byl vizuálně centrovaný -->
  <g transform="translate(104, 104) scale(4)" filter="url(#glow)">
    <rect x="6"  y="33" width="9" height="10" rx="2.5" fill="#c8ff00" opacity="0.38" transform="skewX(-9)"/>
    <rect x="19" y="25" width="9" height="18" rx="2.5" fill="#c8ff00" opacity="0.68" transform="skewX(-9)"/>
    <rect x="32" y="14" width="9" height="29" rx="2.5" fill="#c8ff00"               transform="skewX(-9)"/>
  </g>
</svg>
```

- [ ] **Přepsat eb-social-lime.svg** (inverzní barvy, bez glow)

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" fill="none">
  <rect width="400" height="400" fill="#c8ff00"/>
  <g transform="translate(104, 104) scale(4)">
    <rect x="6"  y="33" width="9" height="10" rx="2.5" fill="#09090b" opacity="0.38" transform="skewX(-9)"/>
    <rect x="19" y="25" width="9" height="18" rx="2.5" fill="#09090b" opacity="0.68" transform="skewX(-9)"/>
    <rect x="32" y="14" width="9" height="29" rx="2.5" fill="#09090b"               transform="skewX(-9)"/>
  </g>
</svg>
```

- [ ] **Vizuálně ověřit oba soubory** — mark je centrovaný ve čtverci, barvy správné

- [ ] **Commit**

```bash
git add backend/static/brand/eb-social-dark.svg backend/static/brand/eb-social-lime.svg
git commit -m "feat: redesign eb-social-dark.svg and eb-social-lime.svg"
```

---

## Task 6: eb-social-dark-rounded.svg a eb-social-github.svg

**Files:**
- Modify: `backend/static/brand/eb-social-dark-rounded.svg`
- Modify: `backend/static/brand/eb-social-github.svg`

Varianty pro Instagram (rounded corners) a GitHub (kruhový clip-path).

- [ ] **Přepsat eb-social-dark-rounded.svg** (tmavé pozadí, rx="80" pro zaoblené rohy)

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" fill="none">
  <rect width="400" height="400" rx="80" fill="#09090b"/>
  <defs>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <g transform="translate(104, 104) scale(4)" filter="url(#glow)">
    <rect x="6"  y="33" width="9" height="10" rx="2.5" fill="#c8ff00" opacity="0.38" transform="skewX(-9)"/>
    <rect x="19" y="25" width="9" height="18" rx="2.5" fill="#c8ff00" opacity="0.68" transform="skewX(-9)"/>
    <rect x="32" y="14" width="9" height="29" rx="2.5" fill="#c8ff00"               transform="skewX(-9)"/>
  </g>
</svg>
```

- [ ] **Přepsat eb-social-github.svg** (kruhový clip pro GitHub avatar)

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" fill="none">
  <defs>
    <clipPath id="circle-clip">
      <circle cx="200" cy="200" r="200"/>
    </clipPath>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="400" height="400" fill="#09090b" clip-path="url(#circle-clip)"/>
  <g transform="translate(104, 104) scale(4)" filter="url(#glow)" clip-path="url(#circle-clip)">
    <rect x="6"  y="33" width="9" height="10" rx="2.5" fill="#c8ff00" opacity="0.38" transform="skewX(-9)"/>
    <rect x="19" y="25" width="9" height="18" rx="2.5" fill="#c8ff00" opacity="0.68" transform="skewX(-9)"/>
    <rect x="32" y="14" width="9" height="29" rx="2.5" fill="#c8ff00"               transform="skewX(-9)"/>
  </g>
</svg>
```

- [ ] **Vizuálně ověřit** — rounded: rohy zaoblené; github: kruhový tvar s mark uvnitř

- [ ] **Commit**

```bash
git add backend/static/brand/eb-social-dark-rounded.svg backend/static/brand/eb-social-github.svg
git commit -m "feat: redesign eb-social-dark-rounded.svg and eb-social-github.svg"
```

---

## Task 7: eb-social-banner.svg

**Files:**
- Modify: `backend/static/brand/eb-social-banner.svg`

OG/Twitter card formát 1200×630. Mark (scale 2.5) vlevo od středu + wordmark vpravo — celá kompozice horizontálně centrovaná.

Mark scale(2.5) = 120px tall. Vertikální střed: (630-120)/2 = 255. Horizontální: celá logo skupina (~520px wide) centrovaná, start na (1200-520)/2 = 340.

- [ ] **Přepsat eb-social-banner.svg**

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" fill="none">
  <rect width="1200" height="630" fill="#09090b"/>
  <defs>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <!-- Mark scale(2.5), centrovaný vertikálně v 630px: (630/2)-(48*2.5/2)=255 -->
  <g transform="translate(340, 255) scale(2.5)" filter="url(#glow)">
    <rect x="6"  y="33" width="9" height="10" rx="2.5" fill="#c8ff00" opacity="0.38" transform="skewX(-9)"/>
    <rect x="19" y="25" width="9" height="18" rx="2.5" fill="#c8ff00" opacity="0.68" transform="skewX(-9)"/>
    <rect x="32" y="14" width="9" height="29" rx="2.5" fill="#c8ff00"               transform="skewX(-9)"/>
  </g>
  <!-- Wordmark — x=468 (340 + 48*2.5 + 28 gap) -->
  <text x="468" y="334" font-family="Syne, system-ui, sans-serif" font-weight="700" font-size="64" fill="#fafafa" letter-spacing="-2">EnduroBuddy</text>
</svg>
```

- [ ] **Vizuálně ověřit** — otevřít v prohlížeči a zkontrolovat horizontální/vertikální centrování, proporce mark vs wordmark

- [ ] **Commit**

```bash
git add backend/static/brand/eb-social-banner.svg
git commit -m "feat: redesign eb-social-banner.svg (1200×630)"
```

---

## Task 8: Aktualizovat visual-style-guide.md

**Files:**
- Modify: `docs/visual-style-guide.md` — sekce `## Logo — Stride Mark` (řádky ~22–53)

Přejmenovat koncept z "Stride Mark" na "Velocity Bars" a doplnit technické specifikace geometrie.

- [ ] **Nahradit celou sekci `## Logo`** v souboru `docs/visual-style-guide.md`:

Najít blok začínající `## Logo — Stride Mark` a nahradit ho tímto:

```markdown
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
| `eb-wordmark.svg` | Pouze wordmark (Syne 700) |
| `eb-social-dark.svg` | IG/X avatar, tmavé pozadí |
| `eb-social-lime.svg` | IG/X avatar, lime pozadí |
| `eb-social-dark-rounded.svg` | IG rounded corners |
| `eb-social-github.svg` | GitHub circle-safe |
| `eb-social-banner.svg` | OG / Twitter card (1200×630) |

Všechny v `backend/static/brand/`.

### Pravidla

- Mark je lime na tmavém, dark na lime/světlém — bez glow na světlém
- Wordmark vždy v Syne 700
- Minimální velikost marku: 16px (bez glow efektu)
- Kolem marku safe zone = šířka jednoho baru (~⅕ celkové šířky)
```

- [ ] **Commit**

```bash
git add docs/visual-style-guide.md
git commit -m "docs: update visual-style-guide.md — Velocity Bars logo spec"
```

---

## Checklist po dokončení

- [ ] Všech 9 SVG souborů otevřít v prohlížeči a vizuálně zkontrolovat
- [ ] Ověřit logo v navbar aplikace: spustit `cd backend && python manage.py runserver` a otevřít `/`
- [ ] Favicon: `eb-mark.svg` funguje jako favicon v `<link rel="icon">` tagu (zkontrolovat v `base_public.html`)
