# WeekCard — Split-zone editing & layout redesign

**Datum:** 2026-04-25
**Větev:** feat/nuxt-migration
**Soubory:** `frontend/components/training/WeekCard.vue` (jediný dotčený soubor)

---

## Kontext a motivace

WeekCard.vue zobrazuje týdenní přehled tréninku jako flat-grid tabulku. Kliknutím na jakékoliv pole se otevřou **všechna** vstupní pole najednou (planned i completed zároveň) — uživatel chce editovat buď plán, nebo splnění, ne oboje najednou.

Doplňující problémy:
- Vizuálně není jasné, kde začíná a kde končí planned vs completed část.
- Na mobilu tabulka přetéká a schází smysluplné přizpůsobení.
- Summary row neukazuje plánované kilometry.

---

## Design

### 1. Layout — proporce zón

Každý denní řádek je horizontálně rozdělen na dvě zóny:

| Zóna | Sloupce | Obsah | Poměr |
|------|---------|-------|-------|
| **Planned** | datum · den · typ · trénink · poznámky | plánovaný trénink | ~3/5 šířky |
| separator | — | 1px linka | — |
| **Completed** | km · čas · intervaly · ⌀HR · HR↑ | naměřené hodnoty | ~2/5 šířky |

Grid template (desktop):
```
44px 30px 42px minmax(11rem, 2.5fr) minmax(5rem, 1fr)
1px
60px 52px minmax(5rem, 1fr) 46px 46px
```

Barevné kódování zón:
- Planned hover/editing: `rgba(56,189,248, .05–.07)` (eb-blue — planned/athlete barva)
- Completed hover/editing: `rgba(200,255,0, .05–.07)` (eb-lime — done/completed barva)

### 2. Edit state — mutual exclusion

`editingRows` zůstane jako `Map<string, RowEdit>`. Do `RowEdit` se přidá:

```ts
activeZone: "planned" | "completed"
```

Pravidla přepínání:
- Klik na planned zónu → otevře se planned, `activeZone = "planned"`
- Klik na completed zónu → otevře se completed, `activeZone = "completed"`
- Klik na **jinou zónu** téhož dne:
  1. Přepne `activeZone` okamžitě (optimisticky)
  2. Pokud `isDirty` — spustí save na pozadí (fire-and-forget, stejně jako debounce save)
- V šabloně: planned inputy se renderují jen když `activeZone === "planned"`, completed inputy jen když `activeZone === "completed"`
- Druhá zóna se zobrazí greyed out (opacity .5, cursor: default) dokud je editování aktivní

### 3. Vizuální stavy zón

| Stav | Planned zóna | Completed zóna |
|------|-------------|----------------|
| Idle | hover → modrý tón, cursor pointer (pokud editable) | hover → lime tón, cursor pointer (pokud editable) |
| Editing planned | modrý tón + blue inputy (`rgba(56,189,248,.3)` border) | greyed out, cursor default |
| Editing completed | greyed out, cursor default | lime tón + lime inputy (`rgba(200,255,0,.3)` border) |
| Done (splněný den) | border-left: 2px lime | — |
| Missed | border-left: 2px danger | — |

### 4. Summary row

Stávající summary row zobrazuje jen completed součty. Nově:

```
[Týden celkem] [plán XX km]   |   [km splněno] [čas] [ ] [⌀HR] [ ]
  grid-col 1-3   grid-col 4-5  sep   grid-col 7   8         10
```

- Planned total: `week.planned_total_km_text` (pole již existuje v `DashboardWeek`)
- Barva: `var(--eb-blue)` (38bdf8), font-family mono, font-weight 600

### 5. Mobilní layout (breakpoint < 768px)

Každý den se zobrazí jako dva vertikálně vrstvené řádky:

```
┌─────────────────────────────────────┐
│ [Po 1.5] [RUN pill] Tempo 10km      │  ← planned row (plná šířka, klikatelná)
│   ✓ 10.2 km · 43:10 · ⌀152         │  ← completed sub-row (odsazení 1.5rem vlevo)
└─────────────────────────────────────┘
```

- Planned row: `border-left: 2px solid rgba(56,189,248,.35)` při editaci `rgba(56,189,248,.5)`
- Completed sub-row: bez border-left defaultně; při editaci `rgba(200,255,0,.5)`
- Prázdné completed: zobrazí "klikni pro zápis" hint
- Notes sloupec se na mobilu schová (dostupný jen přes editing)
- Summary row: `plán X km · splněno Y km`

### 6. Scope změn

**Dotčeno:** pouze `frontend/components/training/WeekCard.vue`

**Není potřeba měnit:**
- `PlannedRow.vue` — komponenta není ve WeekCard používána (WeekCard má vlastní inline logiku)
- `CompletedRow.vue`, `CompletedEditor.vue` — stejný důvod
- Stores, API, backend — žádné nové endpointy

### 7. Testy

WeekCard.vue nemá vlastní test soubor. Existující testy dotčeny:
- `frontend/components/training/PlannedRow.test.ts` — nedotčen
- `frontend/components/training/CompletedRow.test.ts` — nedotčen
- `npm test` musí projít bez chyb po implementaci

---

## Shrnutí změn v `RowEdit`

```ts
interface RowEdit {
  date: string
  activeZone: "planned" | "completed"   // NOVÉ
  // planned
  plannedId: number | null
  title: string
  notes: string
  sessionType: "RUN" | "WORKOUT"
  isCreating: boolean
  // completed
  completedId: number | null
  km: string
  minutes: string
  details: string
  avgHr: string
  maxHr: string
  // ui
  isSaving: boolean
  isDirty: boolean
  debounceTimer: ReturnType<typeof setTimeout> | null
  focusField: string
}
```

Signatura `openEdit` se rozšíří o zónový parametr:
```ts
function openEdit(slot: DaySlot, focusField: string, zone: "planned" | "completed")
```
