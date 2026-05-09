# Spec: Dashboard Grid Navigation — Google Sheets mode

**Datum:** 2026-05-09  
**Větev:** `feat/dashboard-grid-nav`

---

## Motivace

Dashboard WeekCard má klávesovou navigaci uvnitř editačního módu, ale chybí navigační vrstva nad ním. Uživatel musí kliknout na buňku aby ji aktivoval. Cílem je přidat Google Sheets-style two-layer navigation: navigační mód (šipky pohybují kurzorem, bez psaní) a editační mód (psaní do buňky).

---

## Dva módy

### Navigační mód (výchozí)

- Jedna buňka je vizuálně označena (`outline: 2px solid var(--eb-lime)`)
- Šipky pohybují kurzorem po buňkách, nic se nepíše
- Žádný `<input>` nemá browser focus — focus drží wrapping div WeekCard nebo AthleteView
- Aktivace edit módu: Enter (zachová obsah) nebo psaní znaku (nahradí obsah)

### Editační mód

- Aktivní `<input>` nebo `<textarea>` má browser focus
- Šipky ← → pohybují kurzorem v textu (nativní)
- Šipky ↑ ↓ jsou zablokované (`preventDefault`) — nezpůsobí pohyb mezi řádky
- ESC uloží a vrátí do navigačního módu
- Enter v `<input>` uloží a vrátí do navigačního módu (kurzor zůstane)
- Enter v `<textarea>` vloží nový řádek (nativní chování)
- Tab uloží a přesune kurzor o pole doprava v navigačním módu

---

## Navigovatelná pole

8 polí per řádek (den), indexovaná 0–7:

| fieldIdx | pole | typ | editační mód |
|---|---|---|---|
| 0 | `type` | pill RUN/WORKOUT | toggle — bez editačního módu |
| 1 | `title` | textarea | text, auto-grow |
| 2 | `notes` | input | text |
| 3 | `km` | input | číslo |
| 4 | `minutes` | input | číslo |
| 5 | `details` | input | text |
| 6 | `avgHr` | input | číslo |
| 7 | `maxHr` | input | číslo |

Sloupce `date` a `dayLabel` jsou read-only, klávesová navigace je přeskočí.

---

## Mapování kláves

### Navigační mód (window-level keydown handler)

| Klávesa | Akce |
|---|---|
| `↑` | dayIdx−1, stejný fieldIdx. Pokud dayIdx=0 → cross-week prev (Sunday prev. týdne) |
| `↓` | dayIdx+1, stejný fieldIdx. Pokud dayIdx=6 → cross-week next (Monday next. týdne) |
| `←` | fieldIdx−1. Pokud fieldIdx=0 → zůstane |
| `→` | fieldIdx+1. Pokud fieldIdx=7 → zůstane |
| `Tab` | fieldIdx+1 (jako →) |
| `Shift+Tab` | fieldIdx−1 (jako ←) |
| `Enter` | enter edit mode, zachová obsah, kurzor na konec |
| `Space` na type pill (fieldIdx=0) | okamžitě toggle RUN↔WORKOUT, žádný edit mode |
| `Enter` na type pill (fieldIdx=0) | okamžitě toggle RUN↔WORKOUT, žádný edit mode |
| tisknutelný znak (A–Z, 0–9, `-`, `.` apod.) | enter edit mode s `replaceContent = key`, obsah nahrazen |
| `Backspace` / `Delete` | enter edit mode s `replaceContent = ''`, obsah vymazán |
| `Escape` | zruší označení (cursor → null), handler zůstane aktivní |

Všechny nav klávesy volají `preventDefault()` aby nebyl scrollován viewport.

### Editační mód (handler na konkrétním input/textarea)

| Klávesa | Akce |
|---|---|
| `←` `→` | nativní pohyb v textu |
| `↑` `↓` | `preventDefault`, nic nedělá |
| `Escape` | uloží (fire-and-forget), exitEdit, WeekCard emituje `exit-edit` |
| `Enter` v `<input>` | uloží, exitEdit, kurzor zůstane na stejné buňce |
| `Enter` v `<textarea>` | nativní newline |
| `Tab` | uloží, exitEdit, navigační mód fieldIdx+1 |
| `Shift+Tab` | uloží, exitEdit, navigační mód fieldIdx−1 |

---

## Architektura: `useGridNav` composable

**Soubor:** `frontend/composables/useGridNav.ts`

```typescript
interface GridCursor {
  weekIdx: number
  dayIdx: number   // 0 = pondělí, 6 = neděle
  fieldIdx: number // 0–7
}

export const GRID_FIELDS = ['type', 'title', 'notes', 'km', 'minutes', 'details', 'avgHr', 'maxHr'] as const
```

**Exportované hodnoty:**

- `cursor: Ref<GridCursor | null>` — aktuálně označená buňka; null = nic označeno
- `editMode: Ref<boolean>` — jsme v editačním módu?
- `initCursor(weeks: Week[])` — nastaví kurzor na pondělí týdne s dnešním datem (fieldIdx=0); pokud dnešní datum není v žádném týdnu, použije první týden
- `moveCursor(dir: 'up'|'down'|'left'|'right', weekCount: number): 'out-prev'|'out-next'|undefined` — pohyb kurzoru; vrátí signal pro cross-week navigaci pokud dojdeme na kraj
- `enterEdit(replaceContent?: string)` — nastaví editMode=true; pokud replaceContent je string, buňka dostane tento obsah
- `exitEdit()` — nastaví editMode=false; kurzor zůstane
- `attachKeyHandler()` / `detachKeyHandler()` — připojí/odpojí window keydown listener; volá AthleteView/CoachView v onMounted/onUnmounted

**Composable je instanciovaný zvlášť** v AthleteView a CoachView — nesdílí stav.

---

## Změny AthleteView / CoachView

- Volají `useGridNav()`
- V `onMounted`: `initCursor(weeks)` + `attachKeyHandler()`
- V `onUnmounted`: `detachKeyHandler()`
- Předají WeekCard prop: `:active-cursor="cursorForWeek(idx)"` kde `cursorForWeek(idx)` vrátí `{ dayIdx, fieldIdx }` pokud `cursor.weekIdx === idx`, jinak `null`
- Poslouchají `@navigate-out-next` / `@navigate-out-prev` — stávající logika zachována, navíc aktualizují `cursor.weekIdx`
- Poslouchají nový event `@exit-edit` z WeekCard → zavolají `exitEdit()`

---

## Změny WeekCard

### Nový prop
```typescript
activeCursor: { dayIdx: number; fieldIdx: number } | null  // default: null
```

### Vizuální označení nav kurzoru
Buňka odpovídající `activeCursor.dayIdx` + `activeCursor.fieldIdx` dostane CSS třídu `.wt__cell--nav-selected`:
```css
.wt__cell--nav-selected {
  outline: 2px solid var(--eb-lime);
  outline-offset: -1px;
  background: rgba(200, 255, 0, 0.06);
}
```
Nav výběr a editační zvýraznění zón (modré/lime pozadí) jsou oddělené třídy — mohou koexistovat.

### Odebrání `handleKeyNav()`
Stávající funkce `handleKeyNav()` na inputech bude odstraněna. Nahradí ji:
- Jednodušší `handleInputKeydown(e, field, date)` — řeší pouze editační mód (ESC, Enter, Tab, blokuje ↑↓)
- Křížová navigace zůstane jako `emit('navigate-out-next/prev')` ale iniciuje ji `useGridNav` v parentu

### Nový event
```typescript
emit('exit-edit')  // WeekCard emituje při ESC v editačním módu
```

### `focusCell()` zůstane
Stávající expose API zůstane pro cross-week navigaci.

### Auto-focus div pro nav mód
WeekCard dostane `tabindex="0"` na wrapping elementu aby mohl browser focus přijmout při kliknutí mimo inputy (nutné pro správné chycení keydown na window).

---

## Dynamická výška řádků

- `<textarea>` pro `title` a `notes`: `rows="1"`, `resize: none`, `overflow: hidden`
- Při každém `input` eventu na textarea: `el.style.height = 'auto'; el.style.height = el.scrollHeight + 'px'`
- Max výška: `120px` — nad tím `overflow-y: auto` (scrollovatelná textarea)
- Všechny `<input>` (km, min, hr, details) jsou jednořádkové, nerostou
- Řádky (dny) nemají fixní výšku — `align-items: start` místo `center` na grid kontejneru

---

## Jeden scrollbar

- WeekCard kontejner: `overflow: visible` — žádné per-week scrollbary
- Horizontální scroll (pokud tabulka přeteče viewport): jeden `overflow-x: auto` na `.wt` wrapperu (celá tabulka sdílí jeden horizontal scrollbar)
- Vertikální scroll: `<body>` / root layout, jeden scrollbar pro celou stránku

---

## Save feedback — flash pozadí buňky

Po úspěšném uložení:
```css
@keyframes cell-flash-ok {
  0%   { background: rgba(200, 255, 0, 0.2); }
  100% { background: transparent; }
}
.wt__cell--flash-ok { animation: cell-flash-ok 0.8s ease-out forwards; }
```

Po chybě uložení:
```css
@keyframes cell-flash-err {
  0%   { background: rgba(244, 63, 94, 0.2); }
  100% { background: transparent; }
}
.wt__cell--flash-err { animation: cell-flash-err 0.8s ease-out forwards; }
```

Flash se aplikuje na konkrétní buňku (ne celý řádek). Existující row-level flash třídy (`.wt__row--flash-planned-ok` atd.) budou odstraněny a nahrazeny cell-level třídami.

---

## Auto-focus při otevření dashboardu

1. `initCursor(weeks)` v `onMounted` AthleteView/CoachView
2. Najde `weekIdx` týdne který obsahuje dnešní datum
3. Pokud nenajde (zobrazený měsíc není aktuální), použije `weekIdx = 0`
4. Nastaví `cursor = { weekIdx, dayIdx: 0, fieldIdx: 0 }` (pondělí, type pill)
5. Při změně měsíce (přepnutí na jiný měsíc) se cursor resetuje na `weekIdx=0, dayIdx=0, fieldIdx=0`

---

## Testování

- `useGridNav.test.ts` — unit testy composablu: pohyb kurzoru, cross-week signály, enter/exit edit, initCursor
- `WeekCard.test.ts` — existující testy rozšíří o: nav-selected CSS třída dle activeCursor prop, exit-edit event při ESC
- Manuální test: otevřít dashboard, ověřit auto-focus, projít týden šipkami, vstoupit do editace Enter, napsat text, ESC, ověřit uložení + flash
