# Grid Nav — Unified Mouse + Keyboard + Visual Redesign

**Datum:** 2026-05-10  
**Větev:** `feat/dashboard-grid-nav`  
**Status:** Schváleno, čeká na implementaci

---

## Problém

Keyboard navigace (`useGridNav` composable) a myšová interakce (`openEdit()` v WeekCard) jsou dvě oddělené systémy. Kliknutí na buňku nepohybuje kurzorem v `useGridNav` — po kliknutí + ESC kurzor neví kde je, šipky začínají od poslední pozice klávesnice, nikoli od kliknuté buňky.

Vizuálně kurzor používá lime outline pro všechny buňky bez ohledu na zónu, což odporuje existujícímu design systému kde modrá = planned a lime = completed.

---

## Schválený design

### 1. Propojení myši a klávesnice

Při každém volání `openEdit()` (ať klikem nebo klávesnicí) WeekCard emituje nový event `cursor-set` s payload `{ dayIdx: number, fieldIdx: number }`.

Parent (AthleteView, CoachView) naslouchá a synchronizuje:
```
cursor.value = { weekIdx: idx, dayIdx, fieldIdx }
```

Výsledek:
- Klik na buňku → kurzor se přesune tam
- Po kliknutí + ESC kurzor zůstane na té buňce
- Šipky potom pokračují od správné pozice

### 2. Zone-aware nav kurzor

Aktuální `wt__cell--nav-selected` (lime pro vše) se nahradí dvěma třídami:

| Třída | Buňky | Styl |
|-------|-------|------|
| `wt__cell--nav-selected-p` | type, title, notes (fi 0–2) | `outline: 2px solid #38bdf8` + `background: rgba(56,189,248,.08)` |
| `wt__cell--nav-selected-c` | km, min, details, avgHr, maxHr (fi 3–7) | `outline: 2px solid #c8ff00` + `background: rgba(200,255,0,.08)` |

### 3. Pill-hugging kurzor pro Type column (fi = 0)

Type buňka (fi = 0) **nepřijme** outline na celou buňku — kurzor se zobrazí přímo na pill/dot elementu uvnitř:

- **RUN pill se kurzorem:** `border: 1.5px solid #38bdf8` + `background: rgba(56,189,248,.12)` + `box-shadow: 0 0 0 2px rgba(56,189,248,.15)`
- **WKT pill se kurzorem:** `border: 1.5px solid #c8ff00` + `background: rgba(200,255,0,.10)` + `box-shadow: 0 0 0 2px rgba(200,255,0,.12)`
- **Prázdná tečka se kurzorem:** border solid modrý + background + glow (stejný jako RUN)

CSS třída na pill/dot: `wt__type-pill--cursor` / `wt__type-dot--cursor`  
CSS třída na cell kontejneru fi=0: `wt__cell--nav-selected-p` ale s `outline: none` a `background: transparent` (child pill handles it).

### 4. Ghost hover — cell-level (ne zone-level)

Aktuální zone-level hover (osvítí celou skupinu buněk najednou) se změní na cell-level hover:

```css
/* Planned buňka */
.wt__row:not(.wt__row--editing-planned):not(.wt__row--editing-completed)
  .wt__cell-p:hover {
  outline: 1px solid rgba(56,189,248,.38);
  background: rgba(56,189,248,.05);
}

/* Completed buňka */
.wt__row:not(.wt__row--editing-planned):not(.wt__row--editing-completed)
  .wt__cell-c:hover {
  outline: 1px solid rgba(200,255,0,.38);
  background: rgba(200,255,0,.05);
}
```

Type buňka hover: outline: none na buňku, hover efekt jen na pill/dot uvnitř.

### 5. Zone-aware save flash (varianta B)

Aktuální flash (`cell-flash-ok`: lime pro vše) se nahradí zone-aware flashem:

**Planned buňky (fi 0–2):**
```css
@keyframes cell-flash-ok-planned {
  0%   { background: rgba(56,189,248,.22); }
  60%  { background: rgba(56,189,248,.08); }
  100% { background: transparent; }
}
```

**Completed buňky (fi 3–7):**
```css
@keyframes cell-flash-ok-completed {
  0%   { background: rgba(200,255,0,.22); }
  60%  { background: rgba(200,255,0,.10); }
  100% { background: rgba(200,255,0,.05); }
}
```

CSS třídy: `.wt__cell--flash-ok-p` a `.wt__cell--flash-ok-c` (nahrazují existující `.wt__cell--flash-ok`).

### 6. Konzistentní výška prázdných buněk

Prázdné buňky byly vizuálně nižší než plné → ghost hover/cursor byl malý a nepřirozený.

Fix:
```css
.wt__cell-p,
.wt__cell-c {
  min-height: 1.75rem;
  display: flex;
  align-items: center;
}
```

A pro numeric value spany:
```css
.wt__num-val {
  display: block;
  min-height: 1.1em;
  line-height: 1.4;
}
```

### 7. Inline row expansion — celý řádek se otevře najednou

**Trigger:** klik kdekoliv na řádek nebo Enter z nav kurzoru.

**Chování:**
- Všechna planned pole (title + notes) se otevřou najednou jako textarea
- Každá textarea se auto-resize na plný obsah s zalomením řádků (žádné `white-space: nowrap`)
- Fokus jde na buňku, na kterou uživatel klikl (nebo na title při Enter z nav)
- Completed buňky zůstanou dimmed + neaktivní (stejné jako dnes při editaci)
- Border-left modrý + planned zone tint zůstávají

**Zavření:**
- Esc, Tab z posledního pole, nebo klik mimo řádek → uloží všechna pole najednou a zavře

**Nav span v closed stavu:** text oříznut s `…` (beze změny)

**CSS:** `.wt__row--open` třída na řádku spustí přepnutí nav spanů → textarea

**Týká se pouze planned zóny.** Completed zóna (km, čas, HR) se otevírá samostatně jako dnes — klik na completed buňku otevře completed editaci (oddělená zóna).

---

## Dopad na soubory

| Soubor | Změna |
|--------|-------|
| `frontend/components/training/WeekCard.vue` | emit `cursor-set`, zone-aware CSS třídy, pill cursor, hover cell-level, flash zone-aware, min-height fix, inline row expansion |
| `frontend/composables/useGridNav.ts` | beze změny |
| `frontend/components/views/dashboard/AthleteView.vue` | naslouchání `cursor-set` → `cursor.value` sync |
| `frontend/components/views/dashboard/CoachView.vue` | totéž jako AthleteView |

---

## Co se nemění

- Keyboard chování (šipky, Enter, Esc, printable → replace) zůstává beze změny
- Existující zone-based editing tint (modrá pro planned, lime pro completed) zůstává
- Border-left při editaci zůstává
- `useGridNav` composable API zůstává beze změny
- Testy: `focusCellByIdx`, `toggleTypeByDayIdx`, `exit-edit` logika beze změny

---

## Testovací scénáře

1. Klik na buňku → `cursor-set` event → cursor na správné pozici → šipky fungují od tam
2. Klik + ESC → kurzor viditelný na kliknuté buňce
3. Šipka ← na Type column → pill dostane border+glow, ne outline na buňce
4. Hover na prázdnou buňku → stejně velký ghost jako na plnou
5. Enter na planned buňce → modrý flash při uložení (ne lime)
6. Enter na completed buňce → lime flash při uložení
7. Klik na planned buňku → celý řádek se otevře, title + notes jako textarea, fokus na kliknutou buňku
8. Otevřený řádek s dlouhým textem → obě textarea se auto-roztáhnou na plný obsah
9. Esc nebo klik mimo → uloží obě pole a zavře
