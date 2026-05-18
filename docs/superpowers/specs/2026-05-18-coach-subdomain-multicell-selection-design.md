# Spec: Coach Subdomain + Multi-cell Selection + Keyboard Nav Bug Fix

**Datum:** 2026-05-18  
**Větev:** `feat/coach-subdomain-multicell`

---

## Přehled

Tři nezávislé funkční oblasti:

1. **Bug fix** — klávesová navigace dashboardu se deaktivuje pokud je otevřen side panel nebo modal
2. **Coach subdoména** — coach dashboard přesunout na `coach.endurobuddy.cz/plans`
3. **Multi-cell selection** — výběr více buněk v gridu (Shift+šipky, myš), mazání, kopírování a vkládání

---

## 1. Bug fix: klávesová navigace v panelech

### Problém

`handleKeyDown` v `CoachView.vue` a `AthleteView.vue` zpracovává šipkové klávesy i když je otevřen `ManagePanel`, `LegendPanel` nebo `GarminImportModal`. Uživatel nemůže ovládat input v panelu šipkami — dashboard je zachytí dříve.

### Fix

Na začátek `handleKeyDown` v obou view přidat guard podle otevřených panelů:

**`CoachView.vue`:**
```typescript
function handleKeyDown(e: KeyboardEvent) {
  if (isManageOpen.value || isLegendOpen.value) return
  // ... stávající logika
}
```

**`AthleteView.vue`:**
```typescript
function handleKeyDown(e: KeyboardEvent) {
  if (isGarminOpen.value || isLegendOpen.value) return
  // ... stávající logika
}
```

Pravidlo: pokud je otevřen jakýkoliv panel nebo modal, `handleKeyDown` se vrátí hned. Nativní fokus inputu pak funguje bez rušení.

---

## 2. Coach subdoména (`coach.endurobuddy.cz/plans`)

### Cíl

Coach dashboard se přesune z `app.endurobuddy.cz/coach/plans` na `coach.endurobuddy.cz/plans`. Čistá URL, oddělená subdoména od athlete části.

### Frontend

#### Nová page

`frontend/pages/plans.vue` — renderuje `<CoachView />`, layout `default`, identický `useHead` jako `/coach/plans`:

```vue
<template>
  <CoachView />
</template>

<script setup lang="ts">
definePageMeta({ layout: "default" })
const { t } = useI18n()
useHead({ title: computed(() => t('page.coachPlans')) })
</script>
```

#### `nuxt.config.ts`

- `runtimeConfig.public.coachHost: ""` přibude vedle `appHost`
- `routeRules`: přidat `"/plans": { ssr: false }`
- `nuxt` service v docker-compose dostane `NUXT_PUBLIC_COACH_HOST: ${TRAEFIK_COACH_HOST:-}`

#### `middleware/domains.global.ts`

Rozšíření na tři domény. Logika redirect pravidel:

| Aktuální doména | Cesta | Akce |
|---|---|---|
| `appHost` | `/coach/**` nebo `/plans` | → `https://coachHost/plans` |
| `coachHost` | `/app/**`, `/dashboard` | → `https://appHost${path}` |
| `coachHost` | public paths (`/`, `/about`, atd.) | → `https://publicHost${path}` |
| public domain | `/coach/**`, `/plans` | → `https://coachHost/plans` |
| public domain | `/app/**`, `/dashboard` | → `https://appHost${path}` (stávající) |

`publicHost` = `appHost.replace(/^app\./, '')` (stávající odvozování).

#### `middleware/auth.global.ts`

Přidat `/plans` do seznamu chráněných cest (vyžadují přihlášení).

### Backend

#### `settings.py`

```python
COACH_HOST = env("DJANGO_COACH_HOST", default="")
```

Přidat `coach.endurobuddy.cz` do `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` (podmíněně pokud `COACH_HOST` nastaven).

#### `api/views/auth.py`

Helper `_app_url()` a `_default_route_for_user()` — coach uživatelé dostávají absolutní URL na coach subdoménu:

```python
def _coach_url(path: str) -> str:
    coach_host = settings.COACH_HOST
    if coach_host:
        return f"https://{coach_host}{path}"
    return path

# V _default_route_for_user pro coach roli:
return _coach_url("/plans")
```

#### `.env.example`

```
DJANGO_COACH_HOST=coach.endurobuddy.cz
TRAEFIK_COACH_HOST=coach.endurobuddy.cz
```

### Infra

#### `docker-compose.yml`

Nový Traefik router `endurobuddy-coach` pro `coach.endurobuddy.cz` (HTTPS, stejný nginx service):

```yaml
- "traefik.http.routers.endurobuddy-coach.rule=Host(`coach.endurobuddy.cz`)"
- "traefik.http.routers.endurobuddy-coach.entrypoints=websecure"
- "traefik.http.routers.endurobuddy-coach.tls.certresolver=letsencrypt"
- "traefik.http.routers.endurobuddy-coach.service=endurobuddy-nginx"
```

`nuxt` service dostane `NUXT_PUBLIC_COACH_HOST: ${TRAEFIK_COACH_HOST:-}`.

### Redirecty

- `app.endurobuddy.cz/coach/plans` → `coach.endurobuddy.cz/plans` (přes middleware)
- Stará page `frontend/pages/coach/plans.vue` zůstane pro dev prostředí kde `coachHost` není nastaven (graceful degradation)

---

## 3. Multi-cell selection

### Datový model

Rozšíření `useGridNav` composable:

```typescript
// Přibude ke stávajícímu cursor, editMode, pendingReplace
const anchor: Ref<GridCursor | null> = ref(null)
const clipboard: Ref<string[][] | null> = ref(null)

// Normalized selection rectangle
const selection = computed(() => {
  if (!cursor.value || !anchor.value) return null
  const cLin = toLinear(cursor.value.weekIdx, cursor.value.dayIdx)
  const aLin = toLinear(anchor.value.weekIdx, anchor.value.dayIdx)
  return {
    minLin: Math.min(cLin, aLin),
    maxLin: Math.max(cLin, aLin),
    minF: Math.min(cursor.value.fieldIdx, anchor.value.fieldIdx),
    maxF: Math.max(cursor.value.fieldIdx, anchor.value.fieldIdx),
  }
})
```

`toLinear(weekIdx, dayIdx)` = `weekIdx * 7 + dayIdx` — globální lineární index napříč týdny.  
`fromLinear(lin)` = `{ weekIdx: Math.floor(lin / 7), dayIdx: lin % 7 }` — inverzní funkce.

### Klávesové zkratky

| Klávesa | Chování |
|---|---|
| `Shift+šipka` | Nastaví anchor na cursor (pokud není), pohne cursorem |
| `šipka` (bez Shift) | Vymaže anchor, pohne cursorem |
| `Ctrl+C` | Zkopíruje selection do clipboard (2D string array) |
| `Ctrl+V` | Vloží clipboard od cursor pozice (relativně) |
| `Delete` / `Backspace` | Vymaže hodnoty buněk ve selection (prázdný string), zachová anchor/cursor |
| `Esc` | Vymaže anchor i cursor |

`fieldIdx 0` (typ) je z výběru vyloučen — selection začíná od `fieldIdx 1`. Shift+šipka doleva se zastaví na `fieldIdx 1`.

### Myš

- `mousedown` na buňce (fi ≥ 1) → anchor = cursor = daná buňka
- `mouseover` při držení tlačítka → pohybuje cursorem (live drag selection)
- `mouseup` → pokud anchor === cursor (žádný pohyb), zruší anchor (= single-cell nav bez selection highlight)
- `Shift+klik` → zachová anchor, pohne cursorem na kliknutou buňku

### Copy / Paste

**Copy:**
```typescript
// clipboard[dayOffset][fieldOffset]
clipboard.value = []
for (let lin = sel.minLin; lin <= sel.maxLin; lin++) {
  const { weekIdx, dayIdx } = fromLinear(lin)
  const row = []
  for (let fi = sel.minF; fi <= sel.maxF; fi++) {
    row.push(getFieldValue(weekIdx, dayIdx, fi))  // aktuální hodnota z store
  }
  clipboard.value.push(row)
}
```

**Paste (relativní):**
```typescript
const startLin = toLinear(cursor.weekIdx, cursor.dayIdx)
clipboard.value.forEach((row, rowOff) => {
  const targetLin = startLin + rowOff
  if (targetLin >= totalDays) return
  const { weekIdx, dayIdx } = fromLinear(targetLin)
  row.forEach((val, colOff) => {
    const fi = cursor.fieldIdx + colOff
    if (fi > 7) return
    saveField(weekIdx, dayIdx, fi, val)  // existující save API call, silent
  })
})
```

Paste volá existující save API endpointy (planned/completed patch) tiše — bez loading state, bez reload. Chyby se ignorují (best-effort).

### Vizuální feedback

- Vybrané buňky dostanou CSS třídu `.wt__cell--selected`: `background: rgba(56,189,248,.16); border: 2px solid rgba(56,189,248,.35)`
- Anchor buňka dostane `.wt__cell--selected.wt__cell--selection-anchor`: `border-color: #38bdf8` (plná)
- Žádné animace po copy/delete/paste — data se tiše změní

### WeekCard integrace

WeekCard dostane nový prop:

```typescript
interface SelectionRange {
  minLin: number
  maxLin: number
  minF: number
  maxF: number
}

defineProps<{
  // ... stávající props
  selectionRange: SelectionRange | null
  weekLinearOffset: number  // weekIdx * 7 — pro přepočet globální → lokální
}>()
```

Buňka je ve výběru pokud:
```typescript
function isCellSelected(dayIdx: number, fieldIdx: number): boolean {
  if (!props.selectionRange || fieldIdx < 1) return false
  const lin = props.weekLinearOffset + dayIdx
  return lin >= props.selectionRange.minLin &&
         lin <= props.selectionRange.maxLin &&
         fieldIdx >= props.selectionRange.minF &&
         fieldIdx <= props.selectionRange.maxF
}
```

WeekCard emituje nové eventy pro myš:
```typescript
emit('cell-mousedown', { dayIdx, fieldIdx, shiftKey })
emit('cell-mouseover', { dayIdx, fieldIdx })
```

View (CoachView/AthleteView) naslouchá těmto eventům a aktualizuje anchor/cursor v `useGridNav`.

### `handleKeyDown` rozšíření

V obou view se stávající `handleKeyDown` rozšíří:

```typescript
// Shift+Arrow → selection
if (e.shiftKey && ['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)) {
  e.preventDefault()
  if (!gridNav.anchor.value) gridNav.setAnchor({ ...cursor.value })
  const dir = e.key.replace('Arrow','').toLowerCase()
  gridNav.moveCursor(dir, weekCount, { shiftLock: true })
  return
}

// Ctrl+C
if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
  e.preventDefault()
  gridNav.copySelection(/* getValue callback */)
  return
}

// Ctrl+V
if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
  e.preventDefault()
  gridNav.pasteSelection(/* setValue callback */)
  return
}
```

`moveCursor` dostane volitelný flag `shiftLock: true` který zabrání pohybu doleva na `fieldIdx < 1`.

---

## Testování

### Bug fix
- Test: ManagePanel open → stisknout šipku → cursor se nepohne
- Test: ManagePanel closed → stisknout šipku → cursor se pohne

### Coach subdoména
- Test middleware: `domains.global` — coach path na app doméně → redirect na coach doménu
- Test backend: `auth_me` vrátí správnou redirect URL pro coach roli

### Multi-cell selection
- Test: Shift+šipka nastaví anchor, pohne cursor, selection je normalizovaný obdélník
- Test: šipka bez Shift vymaže anchor
- Test: copy → clipboard obsahuje správné hodnoty (2D array)
- Test: paste → hodnoty vloženy relativně od cursor pozice
- Test: delete → hodnoty buněk jsou prázdné
- Test: cross-week selection → `toLinear/fromLinear` správně přechází mezi týdny
- Test: myš drag → selection se rozrůstá při mouseover
- Test: Shift+klik → selection se rozšíří
- Test: mouseup bez pohybu → anchor se zruší (single cell)

---

## Co se NEMĚNÍ

- `frontend/pages/coach/plans.vue` zůstane — pro dev bez `coachHost` funguje jako dřív
- Editace buněk (Enter, psaní) funguje identicky — selection se při vstupu do edit módu vymaže
- `fieldIdx 0` (typ) zůstává mimo selection, ovládá se jen Enter/Space
