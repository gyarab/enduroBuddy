# Coach Subdomain + Multi-cell Selection + Keyboard Nav Fix — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix keyboard nav stealing focus from panels, add `coach.endurobuddy.cz/plans` subdomain, and implement Shift+arrow / mouse multi-cell selection with Ctrl+C/V and Delete in the training grid.

**Architecture:** Three independent areas on one branch `feat/coach-subdomain-multicell`. Bug fix is a 2-line guard. Coach subdomain extends the existing 2-domain middleware to 3. Multi-cell selection extends `useGridNav` with `anchor`/`clipboard` state; WeekCard gains selection CSS and mouse events; views wire keyboard + mouse handlers.

**Tech Stack:** Vue 3 + Nuxt 3, TypeScript, Python/Django, Docker Compose + Traefik, Vitest

---

## Files overview

| File | Change |
|---|---|
| `frontend/components/views/dashboard/CoachView.vue` | Add panel guard; add Shift+Arrow, Ctrl+C/V, mouse handlers |
| `frontend/components/views/dashboard/AthleteView.vue` | Same as CoachView |
| `frontend/composables/useGridNav.ts` | Add anchor, selection computed, clipboard, 5 new functions |
| `frontend/components/training/WeekCard.vue` | selectionRange prop, isCellSelected, mousedown/mouseover emits, silentWriteField |
| `frontend/components/training/WeekCard.test.ts` | Tests for selection + silentWriteField |
| `frontend/pages/plans.vue` | New page — renders CoachView |
| `frontend/nuxt.config.ts` | coachHost runtimeConfig, /plans routeRule |
| `frontend/middleware/domains.global.ts` | 3-domain routing logic |
| `frontend/middleware/domains.test.ts` | New tests for coach domain routing |
| `frontend/middleware/auth.global.ts` | Add /plans to PROTECTED_PATHS |
| `backend/config/settings.py` | COACH_HOST env var |
| `backend/api/views/auth.py` | _coach_url() helper, update _default_route_for_user + auth_me + auth_profile_setup |
| `backend/.env.example` | DJANGO_COACH_HOST + TRAEFIK_COACH_HOST |
| `docker-compose.yml` | Traefik router for coach.endurobuddy.cz |

---

## Task 1: Bug fix — keyboard nav guard in open panels

**Files:**
- Modify: `frontend/components/views/dashboard/CoachView.vue:45`
- Modify: `frontend/components/views/dashboard/AthleteView.vue:40`

- [ ] **Step 1: Add guard to CoachView.vue handleKeyDown**

In `CoachView.vue`, the function `handleKeyDown` starts at line 45. Add the guard as the first two lines of the function body:

```typescript
function handleKeyDown(e: KeyboardEvent) {
  if (isManageOpen.value || isLegendOpen.value) return   // ← ADD THIS LINE
  const active = document.activeElement
  const inInput = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement
  // ... rest unchanged
```

- [ ] **Step 2: Add guard to AthleteView.vue handleKeyDown**

In `AthleteView.vue`, `handleKeyDown` starts at line 40. `legendStore.isPanelOpen` controls the legend panel:

```typescript
function handleKeyDown(e: KeyboardEvent) {
  if (legendStore.isPanelOpen) return   // ← ADD THIS LINE
  const active = document.activeElement
  const inInput = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement
  // ... rest unchanged
```

- [ ] **Step 3: Run tests to confirm nothing broke**

```bash
cd frontend && pnpm test --run
```

Expected: all existing tests pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/components/views/dashboard/CoachView.vue frontend/components/views/dashboard/AthleteView.vue
git commit -m "fix: disable grid keyboard nav when side panel is open"
```

---

## Task 2: Backend — coach host + auth redirect

**Files:**
- Modify: `backend/config/settings.py`
- Modify: `backend/api/views/auth.py`
- Modify: `backend/.env.example`

- [ ] **Step 1: Add COACH_HOST to settings.py**

Find the block where `APP_HOST` is defined (search for `APP_HOST`). Add immediately after it:

```python
APP_HOST = os.environ.get("DJANGO_APP_HOST", "")
COACH_HOST = os.environ.get("DJANGO_COACH_HOST", "")
```

- [ ] **Step 2: Update auth.py — add _coach_url and update redirect functions**

In `backend/api/views/auth.py`, after the existing `_app_url` function (line 36), add:

```python
def _coach_url(path: str) -> str:
    coach_host = getattr(settings, "COACH_HOST", "")
    return f"https://{coach_host}{path}" if coach_host else path
```

Update `_default_route_for_user` (currently line 69):

```python
def _default_route_for_user(user) -> str:
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", Role.ATHLETE)
    if profile and profile.needs_profile_setup:
        return _app_url("/accounts/profile-setup/")
    if role == Role.COACH:
        return _coach_url("/plans")
    return _app_url("/app/dashboard")
```

Update `auth_me` — find the line `default_app_route = _app_url("/coach/plans" if role == Role.COACH else "/app/dashboard")` (currently line 142) and replace:

```python
    default_app_route = _coach_url("/plans") if role == Role.COACH else _app_url("/app/dashboard")
```

Update `auth_profile_setup` — find `redirect_to = _app_url("/coach/plans" if role == Role.COACH else "/app/dashboard")` (currently line 748) and replace:

```python
    redirect_to = _coach_url("/plans") if role == Role.COACH else _app_url("/app/dashboard")
```

- [ ] **Step 3: Update .env.example**

Add after the existing `DJANGO_APP_HOST=app.endurobuddy.cz` line:

```
DJANGO_COACH_HOST=coach.endurobuddy.cz
TRAEFIK_COACH_HOST=coach.endurobuddy.cz
```

- [ ] **Step 4: Run backend tests**

```bash
cd backend && python manage.py test api.tests --verbosity=2
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/config/settings.py backend/api/views/auth.py backend/.env.example
git commit -m "feat: add COACH_HOST setting and coach redirect URL in auth views"
```

---

## Task 3: Frontend — /plans page + nuxt.config

**Files:**
- Create: `frontend/pages/plans.vue`
- Modify: `frontend/nuxt.config.ts`

- [ ] **Step 1: Create frontend/pages/plans.vue**

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

- [ ] **Step 2: Update nuxt.config.ts**

Add `coachHost` to runtimeConfig and `/plans` to routeRules.

In `runtimeConfig.public`, add `coachHost: ""` after `appHost: ""`:

```typescript
runtimeConfig: {
  public: {
    apiBase: "/api/v1",
    appHost: "",
    coachHost: "",   // ← ADD
  },
},
```

In `routeRules`, add `/plans`:

```typescript
routeRules: {
  "/": { ssr: true },
  "/about": { ssr: true },
  "/terms": { ssr: true },
  "/privacy": { ssr: true },
  "/dashboard": { ssr: false },
  "/app/**": { ssr: false },
  "/coach/**": { ssr: false },
  "/accounts/**": { ssr: false },
  "/plans": { ssr: false },   // ← ADD
},
```

- [ ] **Step 3: Add NUXT_PUBLIC_COACH_HOST to docker-compose.yml nuxt service**

In `docker-compose.yml`, inside the `nuxt:` service `environment:` block, add:

```yaml
      NUXT_PUBLIC_COACH_HOST: ${TRAEFIK_COACH_HOST:-}
```

- [ ] **Step 4: Run tests**

```bash
cd frontend && pnpm test --run
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/pages/plans.vue frontend/nuxt.config.ts docker-compose.yml
git commit -m "feat: add /plans page and coachHost runtime config"
```

---

## Task 4: Frontend — domains middleware (3 domains) + auth guard

**Files:**
- Modify: `frontend/middleware/domains.global.ts`
- Modify: `frontend/middleware/auth.global.ts`
- Modify: `frontend/middleware/domains.test.ts`

- [ ] **Step 1: Write new failing tests for coach domain routing**

Add to `frontend/middleware/domains.test.ts` (append before the closing `}`):

```typescript
describe("coach domain routing", () => {
  const COACH_HOST = "coach.endurobuddy.cz"

  beforeEach(() => {
    vi.clearAllMocks()
    mockAppHost = "app.endurobuddy.cz"
    vi.stubGlobal("useRuntimeConfig", () => ({
      public: { appHost: mockAppHost, coachHost: COACH_HOST }
    }))
  })

  it("redirects app domain + /coach/plans to coach domain /plans", async () => {
    setHostname("app.endurobuddy.cz")
    await domainsMiddleware(route("/coach/plans"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://coach.endurobuddy.cz/plans",
      { external: true },
    )
  })

  it("redirects app domain + /plans to coach domain /plans", async () => {
    setHostname("app.endurobuddy.cz")
    await domainsMiddleware(route("/plans"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://coach.endurobuddy.cz/plans",
      { external: true },
    )
  })

  it("redirects public domain + /plans to coach domain", async () => {
    setHostname("endurobuddy.cz")
    await domainsMiddleware(route("/plans"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://coach.endurobuddy.cz/plans",
      { external: true },
    )
  })

  it("redirects coach domain + public path to public domain", async () => {
    setHostname("coach.endurobuddy.cz")
    await domainsMiddleware(route("/"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://endurobuddy.cz/",
      { external: true },
    )
  })

  it("redirects coach domain + /app/dashboard to app domain", async () => {
    setHostname("coach.endurobuddy.cz")
    await domainsMiddleware(route("/app/dashboard"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://app.endurobuddy.cz/app/dashboard",
      { external: true },
    )
  })

  it("does NOT redirect coach domain + /plans", async () => {
    setHostname("coach.endurobuddy.cz")
    await domainsMiddleware(route("/plans"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd frontend && pnpm test --run middleware/domains
```

Expected: 6 new tests FAIL.

- [ ] **Step 3: Rewrite domains.global.ts to support 3 domains**

Replace the entire content of `frontend/middleware/domains.global.ts`:

```typescript
export default defineNuxtRouteMiddleware((to) => {
  const config = useRuntimeConfig()
  const appHost = config.public.appHost as string
  const coachHost = config.public.coachHost as string
  if (!appHost && !coachHost) return

  const currentHost = import.meta.server
    ? (useRequestHeaders()["host"] ?? "").split(":")[0]
    : window.location.hostname

  const isAppDomain = !!appHost && currentHost === appHost
  const isCoachDomain = !!coachHost && currentHost === coachHost
  const isPublicDomain = !isAppDomain && !isCoachDomain

  const COACH_PATHS = ["/coach/", "/plans"]
  const ATHLETE_PATHS = ["/app/", "/dashboard"]
  const isCoachPath = COACH_PATHS.some((p) => to.path === p || to.path.startsWith(p))
  const isAthletePath = ATHLETE_PATHS.some((p) => to.path === p || to.path.startsWith(p))
  const isAppPath = isCoachPath || isAthletePath

  // ── Coach domain ──────────────────────────────────────────────
  if (isCoachDomain) {
    if (isAthletePath && appHost)
      return navigateTo(`https://${appHost}${to.fullPath}`, { external: true })
    if (!isAppPath && appHost) {
      const publicHost = appHost.replace(/^app\./, "")
      return navigateTo(`https://${publicHost}${to.fullPath}`, { external: true })
    }
    return
  }

  // ── App domain ────────────────────────────────────────────────
  if (isAppDomain) {
    if (isCoachPath && coachHost)
      return navigateTo(`https://${coachHost}/plans`, { external: true })
    if (!isAppPath) {
      const publicHost = appHost.replace(/^app\./, "")
      return navigateTo(`https://${publicHost}${to.fullPath}`, { external: true })
    }
    return
  }

  // ── Public domain ─────────────────────────────────────────────
  if (isCoachPath && coachHost)
    return navigateTo(`https://${coachHost}/plans`, { external: true })
  if (isAthletePath && appHost)
    return navigateTo(`https://${appHost}${to.fullPath}`, { external: true })
})
```

- [ ] **Step 4: Update auth.global.ts — add /plans to protected paths**

In `frontend/middleware/auth.global.ts`, update `PROTECTED_PATHS`:

```typescript
const PROTECTED_PATHS = ["/app/", "/coach/", "/dashboard", "/plans"]
```

Also update the login redirect to use the public domain (not just appHost → publicHost) when coachHost is the current domain — but since auth.global only redirects to login and the login page is on the public domain, derive publicHost from appHost as before. The existing logic already handles this correctly since it checks `appHost` and derives `publicHost`. No change needed for the redirect itself.

- [ ] **Step 5: Run tests to confirm all pass**

```bash
cd frontend && pnpm test --run
```

Expected: all tests pass including the 6 new ones.

- [ ] **Step 6: Commit**

```bash
git add frontend/middleware/domains.global.ts frontend/middleware/domains.test.ts frontend/middleware/auth.global.ts
git commit -m "feat: extend domains middleware for coach.endurobuddy.cz subdomain"
```

---

## Task 5: Infra — Traefik router for coach subdomain

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add coach Traefik router labels to nginx service**

In `docker-compose.yml`, in the `nginx:` service `labels:` block, after the `endurobuddy-app` router lines, add:

```yaml
      # HTTPS — coach subdoména
      - "traefik.http.routers.endurobuddy-coach.rule=Host(`coach.endurobuddy.cz`)"
      - "traefik.http.routers.endurobuddy-coach.entrypoints=websecure"
      - "traefik.http.routers.endurobuddy-coach.tls.certresolver=letsencrypt"
      - "traefik.http.routers.endurobuddy-coach.service=endurobuddy-nginx"
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add Traefik router for coach.endurobuddy.cz"
```

---

## Task 6: Extend useGridNav — anchor + selection + clipboard

**Files:**
- Modify: `frontend/composables/useGridNav.ts`

- [ ] **Step 1: Write failing tests for new useGridNav functionality**

Create `frontend/composables/useGridNav.test.ts`:

```typescript
import { describe, expect, it, beforeEach } from "vitest"
import { useGridNav } from "./useGridNav"

describe("useGridNav — selection", () => {
  it("setAnchor stores anchor at given position", () => {
    const nav = useGridNav()
    nav.cursor.value = { weekIdx: 0, dayIdx: 1, fieldIdx: 2 }
    nav.setAnchor({ weekIdx: 0, dayIdx: 1, fieldIdx: 2 })
    expect(nav.anchor.value).toEqual({ weekIdx: 0, dayIdx: 1, fieldIdx: 2 })
  })

  it("clearAnchor sets anchor to null", () => {
    const nav = useGridNav()
    nav.anchor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    nav.clearAnchor()
    expect(nav.anchor.value).toBeNull()
  })

  it("selection is null when no anchor", () => {
    const nav = useGridNav()
    nav.cursor.value = { weekIdx: 0, dayIdx: 2, fieldIdx: 3 }
    expect(nav.selection.value).toBeNull()
  })

  it("selection normalizes anchor+cursor rectangle", () => {
    const nav = useGridNav()
    nav.anchor.value = { weekIdx: 0, dayIdx: 4, fieldIdx: 5 }
    nav.cursor.value  = { weekIdx: 0, dayIdx: 1, fieldIdx: 2 }
    const sel = nav.selection.value!
    expect(sel.minLin).toBe(1)   // dayIdx 1
    expect(sel.maxLin).toBe(4)   // dayIdx 4
    expect(sel.minF).toBe(2)
    expect(sel.maxF).toBe(5)
  })

  it("selection spans across weeks with toLinear", () => {
    const nav = useGridNav()
    nav.anchor.value = { weekIdx: 0, dayIdx: 6, fieldIdx: 1 }  // linear 6
    nav.cursor.value  = { weekIdx: 1, dayIdx: 1, fieldIdx: 3 }  // linear 8
    const sel = nav.selection.value!
    expect(sel.minLin).toBe(6)
    expect(sel.maxLin).toBe(8)
  })

  it("copySelection fills clipboard from getValue callback", () => {
    const nav = useGridNav()
    nav.anchor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    nav.cursor.value  = { weekIdx: 0, dayIdx: 1, fieldIdx: 2 }
    const values: Record<string, string> = {
      "0-0-1": "Run", "0-0-2": "easy", "0-1-1": "Bike", "0-1-2": "hills",
    }
    nav.copySelection((wi, di, fi) => values[`${wi}-${di}-${fi}`] ?? "")
    expect(nav.clipboard.value).toEqual([["Run", "easy"], ["Bike", "hills"]])
  })

  it("deleteSelection calls setValue with empty string for each cell", () => {
    const nav = useGridNav()
    nav.anchor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    nav.cursor.value  = { weekIdx: 0, dayIdx: 0, fieldIdx: 2 }
    const calls: Array<[number, number, number, string]> = []
    nav.deleteSelection((wi, di, fi, val) => calls.push([wi, di, fi, val]), 4)
    expect(calls).toEqual([[0, 0, 1, ""], [0, 0, 2, ""]])
  })

  it("pasteSelection pastes clipboard relative to cursor", () => {
    const nav = useGridNav()
    nav.clipboard.value = [["A", "B"], ["C", "D"]]
    nav.cursor.value = { weekIdx: 0, dayIdx: 2, fieldIdx: 3 }
    const calls: Array<[number, number, number, string]> = []
    nav.pasteSelection((wi, di, fi, val) => calls.push([wi, di, fi, val]), 4)
    // cursor at linear 2, startF 3
    // row 0: linear 2 → week 0 day 2, fi 3 → "A", fi 4 → "B"
    // row 1: linear 3 → week 0 day 3, fi 3 → "C", fi 4 → "D"
    expect(calls).toEqual([
      [0, 2, 3, "A"], [0, 2, 4, "B"],
      [0, 3, 3, "C"], [0, 3, 4, "D"],
    ])
  })
})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd frontend && pnpm test --run composables/useGridNav
```

Expected: 8 new tests FAIL (setAnchor not defined etc.).

- [ ] **Step 3: Implement extensions in useGridNav.ts**

Replace the entire `useGridNav.ts` with:

```typescript
import { ref, computed, type Ref } from 'vue'

export const GRID_FIELDS = [
  'type', 'title', 'notes', 'km', 'minutes', 'details', 'avgHr', 'maxHr',
] as const

export type GridField = (typeof GRID_FIELDS)[number]

export interface GridCursor {
  weekIdx: number
  dayIdx: number   // 0 = pondělí, 6 = neděle
  fieldIdx: number // 0–7
}

export interface SelectionRange {
  minLin: number
  maxLin: number
  minF: number
  maxF: number
}

function toLinear(weekIdx: number, dayIdx: number): number {
  return weekIdx * 7 + dayIdx
}

function fromLinear(lin: number): { weekIdx: number; dayIdx: number } {
  return { weekIdx: Math.floor(lin / 7), dayIdx: lin % 7 }
}

export function useGridNav() {
  const cursor: Ref<GridCursor | null> = ref(null)
  const lastCursor: Ref<GridCursor | null> = ref(null)
  const editMode = ref(false)
  const pendingReplace: Ref<string | undefined> = ref(undefined)
  const anchor: Ref<GridCursor | null> = ref(null)
  const clipboard: Ref<string[][] | null> = ref(null)

  const selection = computed<SelectionRange | null>(() => {
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

  function clearCursor(): void {
    if (cursor.value) lastCursor.value = { ...cursor.value }
    cursor.value = null
    anchor.value = null
  }

  function setAnchor(pos: GridCursor): void {
    anchor.value = { ...pos }
  }

  function clearAnchor(): void {
    anchor.value = null
  }

  function moveCursor(
    dir: 'up' | 'down' | 'left' | 'right',
    weekCount: number,
  ): void {
    if (!cursor.value) {
      cursor.value = lastCursor.value
        ? { ...lastCursor.value }
        : { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
      return
    }
    const c = cursor.value

    if (dir === 'left') {
      cursor.value = { ...c, fieldIdx: Math.max(0, c.fieldIdx - 1) }
      return
    }
    if (dir === 'right') {
      cursor.value = { ...c, fieldIdx: Math.min(7, c.fieldIdx + 1) }
      return
    }
    if (dir === 'up') {
      if (c.dayIdx > 0) {
        cursor.value = { ...c, dayIdx: c.dayIdx - 1 }
      } else if (c.weekIdx > 0) {
        cursor.value = { ...c, weekIdx: c.weekIdx - 1, dayIdx: 6 }
      }
      return
    }
    if (dir === 'down') {
      if (c.dayIdx < 6) {
        cursor.value = { ...c, dayIdx: c.dayIdx + 1 }
      } else if (c.weekIdx < weekCount - 1) {
        cursor.value = { ...c, weekIdx: c.weekIdx + 1, dayIdx: 0 }
      }
    }
  }

  function enterEdit(replaceContent?: string): void {
    editMode.value = true
    pendingReplace.value = replaceContent
  }

  function exitEdit(): void {
    editMode.value = false
    pendingReplace.value = undefined
  }

  function initCursor(weeks: Array<{ week_start: string; week_end: string }>): void {
    if (!weeks.length) return
    cursor.value = { weekIdx: 0, dayIdx: 0, fieldIdx: 1 }
    anchor.value = null
  }

  function _getActiveRange(): SelectionRange | null {
    if (selection.value) return selection.value
    if (cursor.value) {
      const lin = toLinear(cursor.value.weekIdx, cursor.value.dayIdx)
      return { minLin: lin, maxLin: lin, minF: cursor.value.fieldIdx, maxF: cursor.value.fieldIdx }
    }
    return null
  }

  function copySelection(
    getValue: (weekIdx: number, dayIdx: number, fieldIdx: number) => string
  ): void {
    const range = _getActiveRange()
    if (!range) return
    clipboard.value = []
    for (let lin = range.minLin; lin <= range.maxLin; lin++) {
      const { weekIdx, dayIdx } = fromLinear(lin)
      const row: string[] = []
      for (let fi = range.minF; fi <= range.maxF; fi++) {
        row.push(getValue(weekIdx, dayIdx, fi))
      }
      clipboard.value.push(row)
    }
  }

  function deleteSelection(
    setValue: (weekIdx: number, dayIdx: number, fieldIdx: number, val: string) => void,
    totalWeeks: number,
  ): void {
    const range = _getActiveRange()
    if (!range) return
    const maxLin = totalWeeks * 7 - 1
    for (let lin = range.minLin; lin <= Math.min(range.maxLin, maxLin); lin++) {
      const { weekIdx, dayIdx } = fromLinear(lin)
      for (let fi = range.minF; fi <= range.maxF; fi++) {
        setValue(weekIdx, dayIdx, fi, '')
      }
    }
  }

  function pasteSelection(
    setValue: (weekIdx: number, dayIdx: number, fieldIdx: number, val: string) => void,
    totalWeeks: number,
  ): void {
    if (!clipboard.value || !cursor.value) return
    const startLin = toLinear(cursor.value.weekIdx, cursor.value.dayIdx)
    const startF = cursor.value.fieldIdx
    const maxLin = totalWeeks * 7 - 1
    clipboard.value.forEach((row, rowOff) => {
      const targetLin = startLin + rowOff
      if (targetLin > maxLin) return
      const { weekIdx, dayIdx } = fromLinear(targetLin)
      row.forEach((val, colOff) => {
        const fi = startF + colOff
        if (fi > 7) return
        setValue(weekIdx, dayIdx, fi, val)
      })
    })
  }

  return {
    cursor, lastCursor, editMode, pendingReplace,
    anchor, clipboard, selection,
    moveCursor, clearCursor, enterEdit, exitEdit, initCursor,
    setAnchor, clearAnchor,
    copySelection, deleteSelection, pasteSelection,
  }
}
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
cd frontend && pnpm test --run composables/useGridNav
```

Expected: all 8 new tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/composables/useGridNav.ts frontend/composables/useGridNav.test.ts
git commit -m "feat: extend useGridNav with anchor, selection, clipboard"
```

---

## Task 7: WeekCard — selection prop + CSS + mouse emits + silentWriteField

**Files:**
- Modify: `frontend/components/training/WeekCard.vue`
- Modify: `frontend/components/training/WeekCard.test.ts`

- [ ] **Step 1: Write failing tests**

Add to `frontend/components/training/WeekCard.test.ts`:

```typescript
describe("selection highlighting", () => {
  it("adds wt__cell--selected class when cell is in selectionRange", async () => {
    const wrapper = mountWeekCard()
    await wrapper.setProps({
      selectionRange: { minLin: 0, maxLin: 0, minF: 3, maxF: 4 },
      weekLinearOffset: 0,
    })
    // dayIdx 0, fieldIdx 3 (km) should be selected
    const cell = wrapper.find('[data-testid="sel-cell-0-3"]')
    expect(cell.classes()).toContain('wt__cell--selected')
  })

  it("does NOT add wt__cell--selected to type cell (fieldIdx 0)", async () => {
    const wrapper = mountWeekCard()
    await wrapper.setProps({
      selectionRange: { minLin: 0, maxLin: 0, minF: 0, maxF: 2 },
      weekLinearOffset: 0,
    })
    const typeCell = wrapper.find('[data-testid="nav-cell-type-2026-05-01"]')
    expect(typeCell.classes()).not.toContain('wt__cell--selected')
  })

  it("emits cell-mousedown on mousedown on selectable cell", async () => {
    const wrapper = mountWeekCard()
    const cell = wrapper.find('[data-testid="sel-cell-0-1"]')
    await cell.trigger('mousedown')
    expect(wrapper.emitted('cell-mousedown')).toBeTruthy()
    expect(wrapper.emitted('cell-mousedown')![0]).toEqual([{ dayIdx: 0, fieldIdx: 1, shiftKey: false }])
  })
})

describe("silentWriteField", () => {
  it("opens edit and sets field value for completed field", async () => {
    const wrapper = mountWeekCard(buildWeekWithCompleted())
    const component = wrapper.vm as any
    component.silentWriteField(0, 3, '15.5')  // dayIdx 0, fieldIdx 3 (km)
    await nextTick()
    const edit = component.editingRows.get('2026-05-01')
    expect(edit?.km).toBe('15.5')
    expect(edit?.closeAfterSave).toBe(true)
  })
})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd frontend && pnpm test --run WeekCard
```

Expected: new tests FAIL.

- [ ] **Step 3: Add selectionRange + weekLinearOffset props to WeekCard**

In `WeekCard.vue` script, update `defineProps`:

```typescript
import type { SelectionRange } from '~/composables/useGridNav'

const props = defineProps<{
  week: DashboardWeek;
  editorContext?: "athlete" | "coach";
  activeCursor?: { dayIdx: number; fieldIdx: number } | null;
  selectionRange?: SelectionRange | null;
  weekLinearOffset?: number;
}>()
```

Add `isCellSelected` helper after the existing `isNavSelected` function (search for `isNavSelected`):

```typescript
function isCellSelected(dayIdx: number, fieldIdx: number): boolean {
  if (!props.selectionRange || fieldIdx < 1) return false
  const lin = (props.weekLinearOffset ?? 0) + dayIdx
  return (
    lin >= props.selectionRange.minLin &&
    lin <= props.selectionRange.maxLin &&
    fieldIdx >= props.selectionRange.minF &&
    fieldIdx <= props.selectionRange.maxF
  )
}
```

- [ ] **Step 4: Add selection CSS class to cells in template**

For every data cell div (title, notes, km, minutes, details, avgHr, maxHr cells) in the template, add `isCellSelected(dayIdx, fieldIdx)` to its `:class` binding and a `data-testid` for the selection test.

Find the title cell div (around line 654). It already has `navSelectedClass(slot.date, 1)` in its `:class`. The `daySlots` loop index provides `dayIdx`. Change the loop header to include the index:

```html
<template v-for="(slot, dayIdx) in daySlots" :key="slot.date">
```

(The existing loop is `v-for="slot in daySlots"` — add `, dayIdx`.)

Then for each data cell, add to its `:class` array `{ 'wt__cell--selected': isCellSelected(dayIdx, fi) }` and `data-testid` for selection. For example, the title cell (fi=1):

```html
<div
  class="wt__cell wt__cell--title wt__cell-p"
  :data-testid="`cell-title-${slot.date}`"
  :data-sel-testid="`sel-cell-${dayIdx}-1`"
  :class="[
    navSelectedClass(slot.date, 1),
    { 'wt__cell--selected': isCellSelected(dayIdx, 1) },
    { 'wt__cell--flash-err': flashingCellsErr.has(`${slot.date}:1`) },
  ]"
  @mousedown.prevent="emit('cell-mousedown', { dayIdx, fieldIdx: 1, shiftKey: $event.shiftKey })"
  @mouseover="emit('cell-mouseover', { dayIdx, fieldIdx: 1 })"
  @click.stop="openEdit(slot, 'title', 'planned')"
>
```

Apply the same pattern to all 7 data cells (fieldIdx 1–7). Use the correct `fi` value for each.

For `data-testid` on cells used in the selection tests, use `:data-testid="\`sel-cell-${dayIdx}-${fi}\`"` (adjust per cell).

- [ ] **Step 5: Add selection CSS to WeekCard scoped styles**

In `<style scoped>`, add:

```css
.wt__cell--selected {
  background: rgba(56, 189, 248, .16);
  border: 2px solid rgba(56, 189, 248, .35);
}
```

- [ ] **Step 6: Add cell-mousedown + cell-mouseover to emits**

In `defineEmits`, add:

```typescript
"cell-mousedown": [payload: { dayIdx: number; fieldIdx: number; shiftKey: boolean }]
"cell-mouseover": [payload: { dayIdx: number; fieldIdx: number }]
```

- [ ] **Step 7: Add silentWriteField to defineExpose**

In `defineExpose({ ... })`, add:

```typescript
silentWriteField(dayIdx: number, fieldIdx: number, value: string) {
  if (fieldIdx === 0) return
  const field = FIELD_BY_IDX[fieldIdx]
  if (!field) return
  const zone: "planned" | "completed" = fieldIdx <= 2 ? 'planned' : 'completed'
  const slot = daySlots.value[dayIdx]
  if (!slot) return
  openEdit(slot, field, zone)
  const edit = editingRows.get(slot.date)
  if (!edit) return
  if (field === 'title')        edit.title   = value
  else if (field === 'notes')   edit.notes   = value
  else if (field === 'km')      edit.km      = value
  else if (field === 'minutes') edit.minutes = value
  else if (field === 'details') edit.details = value
  else if (field === 'avgHr')   edit.avgHr   = value
  else if (field === 'maxHr')   edit.maxHr   = value
  edit.isDirty = true
  edit.closeAfterSave = true
  if (edit.debounceTimer) {
    clearTimeout(edit.debounceTimer)
    edit.debounceTimer = null
  }
  void autoSave(slot, edit)
},
```

- [ ] **Step 8: Run tests**

```bash
cd frontend && pnpm test --run WeekCard
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```bash
git add frontend/components/training/WeekCard.vue frontend/components/training/WeekCard.test.ts
git commit -m "feat: add selection range, mouse events, and silentWriteField to WeekCard"
```

---

## Task 8: CoachView — Shift+Arrow, Ctrl+C/V, mouse selection

**Files:**
- Modify: `frontend/components/views/dashboard/CoachView.vue`

- [ ] **Step 1: Destructure new gridNav values**

Update the destructuring from `useGridNav()` at line 31:

```typescript
const gridNav = useGridNav()
const { cursor, editMode, anchor, selection } = gridNav
```

- [ ] **Step 2: Add isDragging ref and getFieldValue helper**

After the `weekCardRefs` declaration, add:

```typescript
const isDragging = ref(false)

function getFieldValue(weekIdx: number, dayIdx: number, fieldIdx: number): string {
  const week = coachStore.weeks[weekIdx]
  if (!week) return ''
  const base = new Date(week.week_start)
  base.setDate(base.getDate() + dayIdx)
  const dateStr = base.toISOString().split('T')[0]
  const FIELD_MAP = ['', 'title', 'notes', 'km', 'minutes', 'details', 'avgHr', 'maxHr']
  const field = FIELD_MAP[fieldIdx]
  if (!field) return ''
  const planned = week.planned_rows.find(r => r.date === dateStr && !r.is_second_phase)
  const completed = week.completed_rows.find(r => r.date === dateStr)
  if (field === 'title') return planned?.title === '-' ? '' : (planned?.title ?? '')
  if (field === 'notes') return planned?.notes ?? ''
  if (field === 'km')      return completed?.completed_metrics?.km ?? ''
  if (field === 'minutes') return completed?.completed_metrics?.minutes ?? ''
  if (field === 'details') return completed?.completed_metrics?.details ?? ''
  if (field === 'avgHr')   return completed?.completed_metrics?.avg_hr?.toString() ?? ''
  if (field === 'maxHr')   return completed?.completed_metrics?.max_hr?.toString() ?? ''
  return ''
}

function setFieldValue(weekIdx: number, dayIdx: number, fieldIdx: number, val: string): void {
  weekCardRefs[weekIdx]?.silentWriteField(dayIdx, fieldIdx, val)
}
```

- [ ] **Step 3: Update handleKeyDown — add Shift+Arrow and Ctrl+C/V**

Replace the entire `handleKeyDown` function with:

```typescript
function handleKeyDown(e: KeyboardEvent) {
  if (isManageOpen.value || isLegendOpen.value) return
  const active = document.activeElement
  const inInput = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement
  if (editMode.value && !inInput) gridNav.exitEdit()
  if (editMode.value) return

  const weekCount = coachStore.weeks.length

  // Shift+Arrow — extend selection
  if (e.shiftKey && ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    if (cursor.value && !anchor.value) gridNav.setAnchor({ ...cursor.value })
    const dir = e.key.replace('Arrow', '').toLowerCase() as 'up' | 'down' | 'left' | 'right'
    gridNav.moveCursor(dir, weekCount)
    // Clamp left boundary to fieldIdx 1
    if (cursor.value && cursor.value.fieldIdx < 1) cursor.value = { ...cursor.value, fieldIdx: 1 }
    return
  }

  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    gridNav.clearAnchor()
    const dir = e.key.replace('Arrow', '').toLowerCase() as 'up' | 'down' | 'left' | 'right'
    gridNav.moveCursor(dir, weekCount)
    return
  }

  if (e.key === 'Tab') {
    e.preventDefault()
    gridNav.clearAnchor()
    gridNav.moveCursor(e.shiftKey ? 'left' : 'right', weekCount)
    return
  }

  // Ctrl+C — copy
  if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
    e.preventDefault()
    gridNav.copySelection(getFieldValue)
    return
  }

  // Ctrl+V — paste
  if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
    e.preventDefault()
    gridNav.pasteSelection(setFieldValue, weekCount)
    return
  }

  if (!cursor.value) return
  const { weekIdx, dayIdx, fieldIdx } = cursor.value

  if (e.key === 'Enter' || (e.key === ' ' && fieldIdx === 0)) {
    e.preventDefault()
    gridNav.clearAnchor()
    if (fieldIdx === 0) {
      weekCardRefs[weekIdx]?.toggleTypeByDayIdx(dayIdx)
    } else {
      openCellByIdx(weekIdx, dayIdx, fieldIdx)
    }
    return
  }

  if ((e.key === 'Backspace' || e.key === 'Delete') && fieldIdx !== 0) {
    e.preventDefault()
    if (anchor.value) {
      // Multi-cell delete
      gridNav.deleteSelection(setFieldValue, weekCount)
    } else {
      openCellByIdx(weekIdx, dayIdx, fieldIdx, '')
    }
    return
  }

  if (e.key === 'Escape') {
    e.preventDefault()
    if (anchor.value) {
      gridNav.clearAnchor()
    } else {
      gridNav.clearCursor()
    }
    return
  }

  if (PRINTABLE.test(e.key) && !e.ctrlKey && !e.metaKey && fieldIdx !== 0) {
    e.preventDefault()
    gridNav.clearAnchor()
    openCellByIdx(weekIdx, dayIdx, fieldIdx, e.key)
  }
}
```

- [ ] **Step 4: Add mouse event handlers**

After `handleKeyDown`, add:

```typescript
function handleCellMouseDown(weekIdx: number, payload: { dayIdx: number; fieldIdx: number; shiftKey: boolean }) {
  if (payload.shiftKey && cursor.value) {
    if (!anchor.value) gridNav.setAnchor({ ...cursor.value })
  } else {
    gridNav.setAnchor({ weekIdx, dayIdx: payload.dayIdx, fieldIdx: payload.fieldIdx })
  }
  cursor.value = { weekIdx, dayIdx: payload.dayIdx, fieldIdx: payload.fieldIdx }
  isDragging.value = true
}

function handleCellMouseOver(weekIdx: number, payload: { dayIdx: number; fieldIdx: number }) {
  if (!isDragging.value) return
  cursor.value = { weekIdx, dayIdx: payload.dayIdx, fieldIdx: payload.fieldIdx }
}

function handleWindowMouseUp() {
  if (!isDragging.value) return
  isDragging.value = false
  // If anchor === cursor (single click, no drag), collapse to nav cursor
  if (
    anchor.value && cursor.value &&
    anchor.value.weekIdx === cursor.value.weekIdx &&
    anchor.value.dayIdx === cursor.value.dayIdx &&
    anchor.value.fieldIdx === cursor.value.fieldIdx
  ) {
    gridNav.clearAnchor()
  }
}
```

- [ ] **Step 5: Register mouseup listener in onMounted/onUnmounted**

In `onMounted`, add:
```typescript
window.addEventListener('mouseup', handleWindowMouseUp)
```

In `onUnmounted`, add:
```typescript
window.removeEventListener('mouseup', handleWindowMouseUp)
```

- [ ] **Step 6: Add selectionRange + weekLinearOffset props and new emits to WeekCard in template**

In the `<template>` section, update the `WeekCard` v-for loop to pass new props and listen to new events:

```html
<WeekCard
  v-for="(week, idx) in coachStore.weeks"
  :key="week.id"
  :ref="(el) => { if (el) weekCardRefs[idx] = el as InstanceType<typeof WeekCard> }"
  :week="week"
  editor-context="coach"
  :active-cursor="cursorForWeek(idx)"
  :selection-range="selection"
  :week-linear-offset="idx * 7"
  @navigate-out-next="(p) => handleNavOut('next', idx, p)"
  @navigate-out-prev="(p) => handleNavOut('prev', idx, p)"
  @exit-edit="handleExitEdit"
  @exit-edit-move="(dir) => handleExitEditMove(dir)"
  @cursor-set="(p) => handleCursorSet(idx, p)"
  @cell-mousedown="(p) => handleCellMouseDown(idx, p)"
  @cell-mouseover="(p) => handleCellMouseOver(idx, p)"
/>
```

- [ ] **Step 7: Run tests**

```bash
cd frontend && pnpm test --run
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add frontend/components/views/dashboard/CoachView.vue
git commit -m "feat: add multi-cell selection keyboard + mouse to CoachView"
```

---

## Task 9: AthleteView — same selection wiring

**Files:**
- Modify: `frontend/components/views/dashboard/AthleteView.vue`

- [ ] **Step 1: Destructure new gridNav values**

Update the destructuring from `useGridNav()` at line 25:

```typescript
const gridNav = useGridNav()
const { cursor, editMode, anchor, selection } = gridNav
```

- [ ] **Step 2: Add isDragging + getFieldValue + setFieldValue**

After `weekCardRefs`, add (same helpers as CoachView but using `trainingStore`):

```typescript
const isDragging = ref(false)

function getFieldValue(weekIdx: number, dayIdx: number, fieldIdx: number): string {
  const week = trainingStore.weeks[weekIdx]
  if (!week) return ''
  const base = new Date(week.week_start)
  base.setDate(base.getDate() + dayIdx)
  const dateStr = base.toISOString().split('T')[0]
  const FIELD_MAP = ['', 'title', 'notes', 'km', 'minutes', 'details', 'avgHr', 'maxHr']
  const field = FIELD_MAP[fieldIdx]
  if (!field) return ''
  const planned = week.planned_rows.find(r => r.date === dateStr && !r.is_second_phase)
  const completed = week.completed_rows.find(r => r.date === dateStr)
  if (field === 'title') return planned?.title === '-' ? '' : (planned?.title ?? '')
  if (field === 'notes') return planned?.notes ?? ''
  if (field === 'km')      return completed?.completed_metrics?.km ?? ''
  if (field === 'minutes') return completed?.completed_metrics?.minutes ?? ''
  if (field === 'details') return completed?.completed_metrics?.details ?? ''
  if (field === 'avgHr')   return completed?.completed_metrics?.avg_hr?.toString() ?? ''
  if (field === 'maxHr')   return completed?.completed_metrics?.max_hr?.toString() ?? ''
  return ''
}

function setFieldValue(weekIdx: number, dayIdx: number, fieldIdx: number, val: string): void {
  weekCardRefs[weekIdx]?.silentWriteField(dayIdx, fieldIdx, val)
}
```

- [ ] **Step 3: Replace handleKeyDown** (same logic as CoachView Task 8 Step 3, but use `trainingStore.weeks.length` for `weekCount` and `legendStore.isPanelOpen` as the guard):

```typescript
function handleKeyDown(e: KeyboardEvent) {
  if (legendStore.isPanelOpen) return
  const active = document.activeElement
  const inInput = active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement
  if (editMode.value && !inInput) gridNav.exitEdit()
  if (editMode.value) return

  const weekCount = trainingStore.weeks.length

  if (e.shiftKey && ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    if (cursor.value && !anchor.value) gridNav.setAnchor({ ...cursor.value })
    const dir = e.key.replace('Arrow', '').toLowerCase() as 'up' | 'down' | 'left' | 'right'
    gridNav.moveCursor(dir, weekCount)
    if (cursor.value && cursor.value.fieldIdx < 1) cursor.value = { ...cursor.value, fieldIdx: 1 }
    return
  }

  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    gridNav.clearAnchor()
    const dir = e.key.replace('Arrow', '').toLowerCase() as 'up' | 'down' | 'left' | 'right'
    gridNav.moveCursor(dir, weekCount)
    return
  }

  if (e.key === 'Tab') {
    e.preventDefault()
    gridNav.clearAnchor()
    gridNav.moveCursor(e.shiftKey ? 'left' : 'right', weekCount)
    return
  }

  if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
    e.preventDefault()
    gridNav.copySelection(getFieldValue)
    return
  }

  if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
    e.preventDefault()
    gridNav.pasteSelection(setFieldValue, weekCount)
    return
  }

  if (!cursor.value) return
  const { weekIdx, dayIdx, fieldIdx } = cursor.value

  if (e.key === 'Enter' || (e.key === ' ' && fieldIdx === 0)) {
    e.preventDefault()
    gridNav.clearAnchor()
    if (fieldIdx === 0) {
      weekCardRefs[weekIdx]?.toggleTypeByDayIdx(dayIdx)
    } else {
      openCellByIdx(weekIdx, dayIdx, fieldIdx)
    }
    return
  }

  if ((e.key === 'Backspace' || e.key === 'Delete') && fieldIdx !== 0) {
    e.preventDefault()
    if (anchor.value) {
      gridNav.deleteSelection(setFieldValue, weekCount)
    } else {
      openCellByIdx(weekIdx, dayIdx, fieldIdx, '')
    }
    return
  }

  if (e.key === 'Escape') {
    e.preventDefault()
    if (anchor.value) {
      gridNav.clearAnchor()
    } else {
      gridNav.clearCursor()
    }
    return
  }

  if (PRINTABLE.test(e.key) && !e.ctrlKey && !e.metaKey && fieldIdx !== 0) {
    e.preventDefault()
    gridNav.clearAnchor()
    openCellByIdx(weekIdx, dayIdx, fieldIdx, e.key)
  }
}
```

- [ ] **Step 4: Add mouse handlers (same as CoachView Task 8 Step 4)**

Add `handleCellMouseDown`, `handleCellMouseOver`, `handleWindowMouseUp` with the same implementation but the function bodies are identical (they use `cursor.value`, `anchor.value`, `isDragging.value` — all from the local scope).

- [ ] **Step 5: Register mouseup in onMounted/onUnmounted** (same as CoachView)

- [ ] **Step 6: Update WeekCard usage in template**

Find the `WeekCard` component in `AthleteView.vue` template and add:

```html
  :selection-range="selection"
  :week-linear-offset="idx * 7"
  @cell-mousedown="(p) => handleCellMouseDown(idx, p)"
  @cell-mouseover="(p) => handleCellMouseOver(idx, p)"
```

- [ ] **Step 7: Run all tests**

```bash
cd frontend && pnpm test --run
```

Expected: all tests pass. If TypeScript errors, fix them.

```bash
cd frontend && pnpm exec vue-tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/components/views/dashboard/AthleteView.vue
git commit -m "feat: add multi-cell selection keyboard + mouse to AthleteView"
```

---

## Task 10: Final QA + push

- [ ] **Step 1: Run full test suite**

```bash
cd frontend && pnpm test --run
```

Expected: all tests pass (≥162 tests).

```bash
cd backend && python manage.py test --verbosity=1
```

Expected: all tests pass.

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && pnpm exec vue-tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 3: Django check**

```bash
cd backend && python manage.py check
```

Expected: System check identified no issues.

- [ ] **Step 4: Update CLAUDE.md**

In `CLAUDE.md`, under "Aktivní plány a změny", add entry:

```markdown
### 2026-05-18 — Coach subdomain + multi-cell selection + keyboard nav fix 🔄 IN PROGRESS

**Spec:** `docs/superpowers/specs/2026-05-18-coach-subdomain-multicell-selection-design.md`
**Plán:** `docs/superpowers/plans/2026-05-18-coach-subdomain-multicell-selection.md`
**Větev:** `feat/coach-subdomain-multicell`

- Task 1: keyboard nav guard in panels
- Task 2: backend COACH_HOST + auth redirect
- Task 3: /plans page + nuxt.config coachHost
- Task 4: domains middleware 3 domains + tests
- Task 5: Traefik router for coach subdomain
- Task 6: useGridNav anchor/selection/clipboard
- Task 7: WeekCard selectionRange + mouse emits + silentWriteField
- Task 8: CoachView multi-cell keyboard + mouse
- Task 9: AthleteView multi-cell keyboard + mouse
```

- [ ] **Step 5: Push branch**

```bash
git push -u origin feat/coach-subdomain-multicell
```
