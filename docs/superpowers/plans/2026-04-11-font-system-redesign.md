# Font System Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nahradit Syne za Space Grotesk jako display font a aktualizovat typografickou škálu ve všech CSS souborech, šablonách a dokumentačních preview souborech.

**Architecture:** Změna je čistě CSS/font — žádná logika. Token `--eb-font-display` se mění z `"Syne"` na `"Space Grotesk"` na všech místech kde je definován. Google Fonts URL se aktualizují pro načítání Space Grotesk místo Syne. Inline typografické hodnoty v preview souborech se aktualizují dle nové škály.

**Tech Stack:** CSS custom properties, Google Fonts, Django templates, Vue 3 + Vite, Vitest

---

## Soubory k úpravě

| Soubor | Typ změny |
|--------|-----------|
| `frontend/src/assets/fonts.css` | Swap Syne → Space Grotesk v Google Fonts URL |
| `frontend/src/assets/design-tokens.css` | Swap `"Syne"` → `"Space Grotesk"` v `--eb-font-display` |
| `backend/static/css/public-base.css` | Swap `'Syne'` → `'Space Grotesk'` v `--eb-font-display` |
| `backend/static/css/public-home.css` | Swap `"Syne"` → `"Space Grotesk"` v `--lp-font-display` |
| `backend/templates/public/base_public.html` | Swap Syne → Space Grotesk v `<link>` tagu |
| `docs/visual-style-guide.md` | Aktualizace font stack sekce, typografické škály, logo pravidel |
| `docs/visual-style-preview.html` | Swap font URL, CSS token, typography sekce (labely + inline hodnoty) |
| `docs/app-dashboard-preview.html` | Swap font URL, CSS token |

---

## Task 1: Vue SPA — fonts.css + design-tokens.css

**Files:**
- Modify: `frontend/src/assets/fonts.css:1`
- Modify: `frontend/src/assets/design-tokens.css:29`

- [ ] **Step 1: Aktualizuj fonts.css**

Nahraď obsah souboru `frontend/src/assets/fonts.css`:

```css
@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap");
```

- [ ] **Step 2: Aktualizuj design-tokens.css**

V souboru `frontend/src/assets/design-tokens.css` na řádku 29 nahraď:

```css
  --eb-font-display: "Syne", system-ui, sans-serif;
```

za:

```css
  --eb-font-display: "Space Grotesk", system-ui, sans-serif;
```

- [ ] **Step 3: Ověř že testy prochází**

```bash
cd frontend && npm test
```

Očekáváno: všechny testy zelené (font změna nemá vliv na logiku)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/assets/fonts.css frontend/src/assets/design-tokens.css
git commit -m "feat(typography): swap Syne → Space Grotesk in Vue SPA font tokens"
```

---

## Task 2: Backend CSS + Django šablona

**Files:**
- Modify: `backend/static/css/public-base.css:26`
- Modify: `backend/static/css/public-home.css:13`
- Modify: `backend/templates/public/base_public.html:17`

- [ ] **Step 1: Aktualizuj public-base.css**

V souboru `backend/static/css/public-base.css` na řádku 26 nahraď:

```css
  --eb-font-display: 'Syne', system-ui, sans-serif;
```

za:

```css
  --eb-font-display: 'Space Grotesk', system-ui, sans-serif;
```

- [ ] **Step 2: Aktualizuj public-home.css**

V souboru `backend/static/css/public-home.css` na řádku 13 nahraď v inline CSS bloku hodnotu `--lp-font-display`. Najdi část:

```css
--lp-font-display:"Syne",system-ui,sans-serif;
```

a nahraď:

```css
--lp-font-display:"Space Grotesk",system-ui,sans-serif;
```

- [ ] **Step 3: Aktualizuj Google Fonts link v base_public.html**

V souboru `backend/templates/public/base_public.html` na řádku 17 nahraď celý `<link>` tag:

```html
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
```

za:

```html
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

- [ ] **Step 4: Commit**

```bash
git add backend/static/css/public-base.css backend/static/css/public-home.css backend/templates/public/base_public.html
git commit -m "feat(typography): swap Syne → Space Grotesk in backend CSS and template"
```

---

## Task 3: visual-style-guide.md — aktualizace font dokumentace

**Files:**
- Modify: `docs/visual-style-guide.md` (řádky 48, 60, 139–170)

- [ ] **Step 1: Aktualizuj font stack sekci (řádky 138–147)**

Nahraď blok:

```markdown
```css
--eb-font-display: "Syne", system-ui, sans-serif;
--eb-font-body:    "Inter", "Segoe UI Variable Text", system-ui, sans-serif;
--eb-font-mono:    "JetBrains Mono", "Cascadia Code", monospace;
```

**Syne** — Geometrický display font s charakterem. Headlines, brand, hero, section titles.

**Inter** — Precision UI font. Body text, formuláře, tabulky, labely, navigace.

**JetBrains Mono** — Numerická data: pace, distance, HR, timestamps.
```

za:

```markdown
```css
--eb-font-display: "Space Grotesk", system-ui, sans-serif;
--eb-font-body:    "Inter", "Segoe UI Variable Text", system-ui, sans-serif;
--eb-font-mono:    "JetBrains Mono", "Cascadia Code", monospace;
```

**Space Grotesk** — Technický display font s precision-nástroj charakterem. Headlines, brand, hero, section titles. Nahradil Syne pro čistší výsledek v tmavém UI.

**Inter** — Precision UI font. Body text, formuláře, tabulky, labely, navigace.

**JetBrains Mono** — Numerická data: pace, distance, HR, timestamps.
```

- [ ] **Step 2: Aktualizuj typografickou hierarchii (řádky 153–170)**

Nahraď celou tabulku a pravidla:

```markdown
```
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
```

### Pravidla

- Syne NIKDY pod 18px
- Inter pro veškerý funkční UI text
- JetBrains Mono pro: pace (4:52), distance (12.3 km), HR (142 bpm), timestamps
- Labely jsou Inter uppercase s wide tracking — nikdy Syne
- Line-height: 0.9-1.0 pro display, 1.3 pro headings, 1.6 pro body
```

za:

```markdown
```
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
```

### Pravidla

- Space Grotesk pro Display, H1, H2, H3 — celá heading hierarchie z jednoho fontu
- Inter pro veškerý funkční UI text (Body, Small, Label, tlačítka, formuláře)
- JetBrains Mono pro: pace (4:52), distance (12.3 km), HR (142 bpm), timestamps
- Labely jsou Inter uppercase s wide tracking — nikdy Space Grotesk
- Line-height: 0.95 pro display, 1.05–1.3 pro headings, 1.6 pro body
```

- [ ] **Step 3: Aktualizuj zmínky o logo wordmarku (řádky 48, 60)**

Řádek 48 — nahraď:
```
| `eb-wordmark.svg` | Pouze wordmark (Syne 700) |
```
za:
```
| `eb-wordmark.svg` | Pouze wordmark (Space Grotesk 700) |
```

Řádek 60 — nahraď:
```
- Wordmark vždy v Syne 700
```
za:
```
- Wordmark vždy v Space Grotesk 700
```

- [ ] **Step 4: Commit**

```bash
git add docs/visual-style-guide.md
git commit -m "docs(typography): update visual-style-guide for Space Grotesk font system"
```

---

## Task 4: visual-style-preview.html

**Files:**
- Modify: `docs/visual-style-preview.html` (řádky 9, 48, 774, 964–982, 993)

- [ ] **Step 1: Swap Google Fonts URL (řádek 9)**

Nahraď:
```html
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Syne:wght@700;800&display=swap" rel="stylesheet">
```
za:
```html
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

- [ ] **Step 2: Swap CSS token (řádek 48)**

Nahraď:
```css
      --eb-font-display:  "Syne", system-ui, sans-serif;
```
za:
```css
      --eb-font-display:  "Space Grotesk", system-ui, sans-serif;
```

- [ ] **Step 3: Aktualizuj meta tag (řádek 774)**

Nahraď:
```html
        <span class="ds-meta-tag">Syne + Inter + JetBrains Mono</span>
```
za:
```html
        <span class="ds-meta-tag">Space Grotesk + Inter + JetBrains Mono</span>
```

- [ ] **Step 4: Aktualizuj typography sekci (řádky 964–1003)**

Nahraď celý blok od `<div class="ds-section-note">Syne display` po `</div>` uzavírající `ds-panel` s type-row položkami:

```html
        <div class="ds-section-note">Space Grotesk display &middot; Inter body &middot; JetBrains Mono data</div>
      </div>
      <div class="ds-panel">
        <div class="type-row">
          <div class="type-meta">Display / SG 700</div>
          <div class="type-sample" style="font-family:var(--eb-font-display);font-size:clamp(2.5rem,6vw,4.5rem);font-weight:700;line-height:.95;letter-spacing:-.05em;">Training <span style="color:var(--eb-lime);">Control</span></div>
        </div>
        <div class="type-row">
          <div class="type-meta">H1 / SG 700</div>
          <div class="type-sample" style="font-family:var(--eb-font-display);font-size:clamp(1.75rem,4vw,2.75rem);font-weight:700;line-height:1.05;letter-spacing:-.04em;">Vše co trenér potřebuje</div>
        </div>
        <div class="type-row">
          <div class="type-meta">H2 / SG 600</div>
          <div class="type-sample" style="font-family:var(--eb-font-display);font-size:clamp(1.25rem,2.5vw,1.75rem);font-weight:600;line-height:1.15;letter-spacing:-.025em;">Měsíční plánování</div>
        </div>
        <div class="type-row">
          <div class="type-meta">H3 / SG 500</div>
          <div class="type-sample" style="font-family:var(--eb-font-display);font-size:1.0625rem;font-weight:500;line-height:1.3;letter-spacing:-.01em;color:var(--eb-text-secondary);">Týdenní přehled tréninků</div>
        </div>
        <div class="type-row">
          <div class="type-meta">Body / Inter 400</div>
          <div class="type-sample" style="font-size:15px;color:var(--eb-text-secondary);line-height:1.6;">EnduroBuddy spojuje měsíční tréninkové plány, splněné aktivity a spolupráci trenéra se sportovcem do jednoho moderního rozhraní. Připrav plán, sleduj realitu.</div>
        </div>
        <div class="type-row">
          <div class="type-meta">Small / Inter 500</div>
          <div class="type-sample" style="font-size:13px;font-weight:500;letter-spacing:.01em;color:var(--eb-text-secondary);">Posledních 6 km v maratonském tempu. Rozloženo do 4 intervalů.</div>
        </div>
        <div class="type-row">
          <div class="type-meta">Label / Inter 600 UC</div>
          <div class="type-sample" style="font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--eb-text-muted);">Týdenní objem &middot; Akutní zátěž &middot; Recovery index</div>
        </div>
        <div class="type-row">
          <div class="type-meta">Mono / JetBrains 500</div>
          <div class="type-sample" style="font-family:var(--eb-font-mono);font-size:14px;font-weight:500;letter-spacing:-.02em;">4:52 /km &middot; 12.3 km &middot; 142 bpm &middot; 1h 18m</div>
        </div>
        <div class="type-row">
          <div class="type-meta">Mono Large / JetBrains 500</div>
          <div class="type-sample" style="font-family:var(--eb-font-mono);font-size:2.2rem;font-weight:500;letter-spacing:-.03em;line-height:1;color:var(--eb-lime);">82 km</div>
        </div>
      </div>
```

- [ ] **Step 5: Otevři soubor v prohlížeči a vizuálně ověř typography sekci**

Otevři `docs/visual-style-preview.html` v prohlížeči. Zkontroluj:
- Typography sekce zobrazuje Space Grotesk (ne Syne) pro Display–H3
- H3 má viditelně jiný font než Body (Space Grotesk 500 vs Inter)
- Hodnoty letter-spacingu jsou těsnější než dříve

- [ ] **Step 6: Commit**

```bash
git add docs/visual-style-preview.html
git commit -m "docs(typography): update visual-style-preview for Space Grotesk font system"
```

---

## Task 5: app-dashboard-preview.html

**Files:**
- Modify: `docs/app-dashboard-preview.html` (řádky 9, 37)

- [ ] **Step 1: Swap Google Fonts URL (řádek 9)**

Nahraď:
```html
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```
za:
```html
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

- [ ] **Step 2: Swap CSS token (řádek 37)**

Nahraď:
```css
      --eb-font-display: 'Syne', system-ui, sans-serif;
```
za:
```css
      --eb-font-display: 'Space Grotesk', system-ui, sans-serif;
```

- [ ] **Step 3: Otevři soubor v prohlížeči a vizuálně ověř**

Otevři `docs/app-dashboard-preview.html` v prohlížeči. Zkontroluj že headlingy v dashboardu zobrazují Space Grotesk.

- [ ] **Step 4: Commit**

```bash
git add docs/app-dashboard-preview.html
git commit -m "docs(typography): update app-dashboard-preview for Space Grotesk font system"
```

---

## Task 6: Závěrečná verifikace

- [ ] **Step 1: Ověř že žádný soubor stále neobsahuje "Syne"**

```bash
grep -rn "Syne" frontend/src/ backend/static/css/ backend/templates/ docs/visual-style-guide.md docs/visual-style-preview.html docs/app-dashboard-preview.html
```

Očekáváno: žádný výstup (prázdný výsledek)

- [ ] **Step 2: Spusť frontend testy**

```bash
cd frontend && npm test
```

Očekáváno: všechny testy zelené

- [ ] **Step 3: Zkontroluj Vite build**

```bash
cd frontend && npm run build
```

Očekáváno: build proběhne bez chyb

- [ ] **Step 4: Finální commit pokud vše prošlo**

```bash
git add .
git status  # ověř že nejsou nezapomenuté soubory
```

Pokud je vše commitnuto, žádný commit není potřeba. Pokud zbývají neuložené změny, commitni je.
