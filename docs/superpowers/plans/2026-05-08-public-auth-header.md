# Public Auth-Aware Header Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the public layout header show "Dashboard →" for authenticated users and "Login →" for unauthenticated users, and remove the auto-redirect that sent authenticated users away from the landing page.

**Architecture:** Two file changes: (1) remove the authenticated-user auto-redirect block from `domains.global.ts` (lines 28–39); (2) add client-side auth check to `public.vue` layout to conditionally render the correct header button. New test files cover both changes using the existing middleware test pattern (vitest stubs) and the component test pattern (vue-test-utils).

**Tech Stack:** Vue 3, Nuxt 3, Pinia, Vue Test Utils, Vitest

---

### Task 1: Cleanup merged branches and create feature branch

**Files:**
- No file changes — git operations only

- [ ] **Step 1: Delete local merged branch**

```bash
git branch -d feat/registration-flow
```

Expected: `Deleted branch feat/registration-flow`

- [ ] **Step 2: Delete remote merged branches**

```bash
git push origin --delete feat/registration-flow
git push school --delete feat/registration-flow
```

Expected: each prints `- [deleted]   feat/registration-flow`

- [ ] **Step 3: Create and push feature branch**

```bash
git checkout -b feat/public-auth-header
git push -u origin feat/public-auth-header
```

Expected: `Branch 'feat/public-auth-header' set up to track remote branch 'origin/feat/public-auth-header'`

---

### Task 2: Remove auth redirect from domains.global.ts (TDD)

**Files:**
- Create: `frontend/middleware/domains.test.ts`
- Modify: `frontend/middleware/domains.global.ts`

- [ ] **Step 1: Write failing test**

Create `frontend/middleware/domains.test.ts`:

```ts
import { beforeEach, describe, expect, it, vi } from "vitest"

const mockInitialize = vi.fn()
let mockIsAuthenticated = false
let mockIsCoach = false
let mockHasBootstrapped = true
let mockAppHost = "app.endurobuddy.cz"

vi.mock("~/stores/auth", () => ({
  useAuthStore: vi.fn(() => ({
    hasBootstrapped: mockHasBootstrapped,
    isAuthenticated: mockIsAuthenticated,
    isCoach: mockIsCoach,
    initialize: mockInitialize,
  })),
}))

vi.stubGlobal("useRuntimeConfig", () => ({ public: { appHost: mockAppHost } }))
vi.stubGlobal("useRequestHeaders", () => ({ host: "endurobuddy.cz" }))

import domainsMiddleware from "./domains.global"

const mockNavigateTo = vi.mocked(navigateTo)

function setHostname(hostname: string) {
  Object.defineProperty(window, "location", {
    value: { hostname },
    configurable: true,
    writable: true,
  })
}

function route(path: string) {
  return { path, fullPath: path } as Parameters<typeof domainsMiddleware>[0]
}

describe("domains.global middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockIsAuthenticated = false
    mockIsCoach = false
    mockHasBootstrapped = true
    mockAppHost = "app.endurobuddy.cz"
    vi.stubGlobal("useRuntimeConfig", () => ({ public: { appHost: mockAppHost } }))
    setHostname("endurobuddy.cz")
  })

  it("returns early when appHost is not set", async () => {
    mockAppHost = ""
    vi.stubGlobal("useRuntimeConfig", () => ({ public: { appHost: "" } }))
    await domainsMiddleware(route("/"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it("redirects public domain + app path to app domain", async () => {
    setHostname("endurobuddy.cz")
    await domainsMiddleware(route("/dashboard"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://app.endurobuddy.cz/dashboard",
      { external: true },
    )
  })

  it("redirects app domain + public path to public domain", async () => {
    setHostname("app.endurobuddy.cz")
    await domainsMiddleware(route("/"), {} as any)
    expect(mockNavigateTo).toHaveBeenCalledWith(
      "https://endurobuddy.cz/",
      { external: true },
    )
  })

  it("does NOT redirect authenticated user from public domain landing page", async () => {
    mockIsAuthenticated = true
    setHostname("endurobuddy.cz")
    await domainsMiddleware(route("/"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })

  it("does NOT redirect unauthenticated user from public domain about page", async () => {
    mockIsAuthenticated = false
    setHostname("endurobuddy.cz")
    await domainsMiddleware(route("/about"), {} as any)
    expect(mockNavigateTo).not.toHaveBeenCalled()
  })
})
```

- [ ] **Step 2: Run tests to verify one fails**

From `frontend/`:
```bash
pnpm test middleware/domains
```

Expected: 4 pass, 1 fails — "does NOT redirect authenticated user from public domain landing page" fails because the current code calls `navigateTo("https://app.endurobuddy.cz/dashboard", { external: true })` for authenticated users.

- [ ] **Step 3: Replace domains.global.ts**

Replace the full content of `frontend/middleware/domains.global.ts` with:

```ts
export default defineNuxtRouteMiddleware((to) => {
  const config = useRuntimeConfig()
  const appHost = config.public.appHost as string
  if (!appHost) return

  const currentHost = import.meta.server
    ? (useRequestHeaders()["host"] ?? "").split(":")[0]
    : window.location.hostname

  const isAppDomain = currentHost === appHost
  const isPublicDomain = !isAppDomain

  const APP_PATHS = ["/dashboard", "/app/", "/coach/"]
  const isAppPath = APP_PATHS.some((p) => to.path.startsWith(p))

  // App domain + public path → redirect to public domain
  if (isAppDomain && !isAppPath) {
    const publicHost = appHost.replace(/^app\./, "")
    return navigateTo(`https://${publicHost}${to.fullPath}`, { external: true })
  }

  // Public domain + app path → redirect to app domain
  if (isPublicDomain && isAppPath) {
    return navigateTo(`https://${appHost}${to.fullPath}`, { external: true })
  }
})
```

- [ ] **Step 4: Run tests to verify all pass**

```bash
pnpm test middleware/domains
```

Expected: 5 pass, 0 fail

- [ ] **Step 5: Run full test suite**

```bash
pnpm test
```

Expected: all tests green (was passing before, no regressions)

- [ ] **Step 6: Commit**

```bash
git add frontend/middleware/domains.global.ts frontend/middleware/domains.test.ts
git commit -m "feat: remove auto-redirect of authenticated users from public pages"
```

---

### Task 3: Auth-aware header in public.vue (TDD)

**Files:**
- Create: `frontend/layouts/public.test.ts`
- Modify: `frontend/layouts/public.vue`
- Modify: `frontend/i18n/locales/cs.json`
- Modify: `frontend/i18n/locales/en.json`

- [ ] **Step 1: Write failing tests**

Create `frontend/layouts/public.test.ts`:

```ts
import { mount } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import { createRouter, createMemoryHistory } from "vue-router"
import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/components/ui/EbLogo.vue", () => ({ default: { template: "<span />" } }))

const mockInitialize = vi.fn()
const mockAuth = {
  hasBootstrapped: true,
  isAuthenticated: false,
  initialize: mockInitialize,
}

vi.mock("~/stores/auth", () => ({
  useAuthStore: vi.fn(() => mockAuth),
}))

import PublicLayout from "@/layouts/public.vue"

function makeRouter() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", component: { template: "<div/>" } },
      { path: "/dashboard", component: { template: "<div/>" } },
      { path: "/accounts/login/", component: { template: "<div/>" } },
    ],
  })
  router.push("/")
  return router
}

describe("public layout header", () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)
    vi.clearAllMocks()
    mockAuth.isAuthenticated = false
    mockAuth.hasBootstrapped = true
  })

  it("shows login link when unauthenticated", async () => {
    const router = makeRouter()
    await router.isReady()
    const wrapper = mount(PublicLayout, {
      global: { plugins: [router, pinia] },
    })
    expect(wrapper.find('a[href="/accounts/login/"]').exists()).toBe(true)
    expect(wrapper.find('a[href="/dashboard"]').exists()).toBe(false)
  })

  it("shows dashboard link when authenticated", async () => {
    mockAuth.isAuthenticated = true
    const router = makeRouter()
    await router.isReady()
    const wrapper = mount(PublicLayout, {
      global: { plugins: [router, pinia] },
    })
    expect(wrapper.find('a[href="/dashboard"]').exists()).toBe(true)
    expect(wrapper.find('a[href="/accounts/login/"]').exists()).toBe(false)
  })

  it("calls initialize() on mount when not yet bootstrapped", async () => {
    mockAuth.hasBootstrapped = false
    const router = makeRouter()
    await router.isReady()
    mount(PublicLayout, {
      global: { plugins: [router, pinia] },
    })
    expect(mockInitialize).toHaveBeenCalledOnce()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pnpm test layouts/public
```

Expected: 2–3 tests fail — "shows dashboard link when authenticated" fails because the current template always renders the login link. "calls initialize() on mount" fails because `onMounted` is not yet in public.vue.

- [ ] **Step 3: Add `nav.dashboard` i18n key to cs.json**

In `frontend/i18n/locales/cs.json`, add `"dashboard"` inside the `"nav"` object after the `"login"` key:

```json
"nav": {
  "home": "Domů",
  "features": "Funkce",
  "howItWorks": "Jak funguje",
  "about": "O aplikaci",
  "login": "Přihlášení",
  "dashboard": "Dashboard",
  ...
}
```

- [ ] **Step 4: Add `nav.dashboard` i18n key to en.json**

In `frontend/i18n/locales/en.json`, add `"dashboard"` inside the `"nav"` object after the `"login"` key:

```json
"nav": {
  "home": "Home",
  "features": "Features",
  "howItWorks": "How it works",
  "about": "About",
  "login": "Log in",
  "dashboard": "Dashboard",
  ...
}
```

- [ ] **Step 5: Update public.vue**

Replace the full content of `frontend/layouts/public.vue` with:

```vue
<template>
  <div class="eb-public-root">
    <header class="eb-topbar">
      <div class="eb-public-shell eb-topbar-inner">
        <NuxtLink to="/" class="eb-topbar-brand" aria-label="EnduroBuddy">
          <EbLogo size="lg" />
        </NuxtLink>

        <nav class="eb-topbar-nav" :aria-label="t('nav.mainNavLabel')">
          <slot name="nav">
            <NuxtLink to="/" class="eb-topbar-link">{{ t("nav.home") }}</NuxtLink>
            <NuxtLink to="/about" class="eb-topbar-link">{{ t("nav.about") }}</NuxtLink>
            <a href="/#features" class="eb-topbar-link">{{ t("nav.features") }}</a>
          </slot>
        </nav>

        <div class="eb-topbar-actions">
          <slot name="actions">
            <NuxtLink v-if="auth.isAuthenticated" to="/dashboard" class="eb-btn-nav">
              {{ t("nav.dashboard") }} →
            </NuxtLink>
            <NuxtLink v-else to="/accounts/login/" class="eb-btn-nav">
              {{ t("nav.login") }} →
            </NuxtLink>
          </slot>
        </div>
      </div>
    </header>

    <slot />

    <footer class="eb-footer">
      <div class="eb-public-shell">
        <div class="eb-footer-grid">
          <div class="eb-footer-brand">
            <EbLogo class="eb-footer-logo" size="lg" />
            <p class="eb-footer-tagline">{{ t("footer.tagline") }}</p>
          </div>

          <nav class="eb-footer-nav" :aria-label="t('nav.footerNavLabel')">
            <ul>
              <li><NuxtLink to="/">{{ t("nav.home") }}</NuxtLink></li>
              <li><NuxtLink to="/about">{{ t("nav.about") }}</NuxtLink></li>
              <li><NuxtLink to="/terms">{{ t("nav.terms") }}</NuxtLink></li>
              <li><NuxtLink to="/privacy">{{ t("nav.privacy") }}</NuxtLink></li>
            </ul>
          </nav>

          <div class="eb-footer-lang">
            <div class="eb-footer-lang-label">{{ t("footer.language") }}</div>
            <div class="eb-footer-lang-pills">
              <button
                class="eb-lang-pill"
                :class="{ 'is-active': locale === 'cs' }"
                @click="setLocale('cs')"
              >CZ</button>
              <button
                class="eb-lang-pill"
                :class="{ 'is-active': locale === 'en' }"
                @click="setLocale('en')"
              >EN</button>
            </div>
          </div>
        </div>

        <div class="eb-footer-copy">© {{ currentYear }} EnduroBuddy</div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue"
import { useAuthStore } from "~/stores/auth"

const { t, locale, setLocale } = useI18n()
const auth = useAuthStore()
const currentYear = new Date().getFullYear()

onMounted(async () => {
  if (!auth.hasBootstrapped) await auth.initialize()
})
</script>
```

- [ ] **Step 6: Run layout tests to verify they pass**

```bash
pnpm test layouts/public
```

Expected: 3 pass, 0 fail

- [ ] **Step 7: Run full test suite**

```bash
pnpm test
```

Expected: all tests green

- [ ] **Step 8: Commit**

```bash
git add frontend/layouts/public.vue frontend/layouts/public.test.ts frontend/i18n/locales/cs.json frontend/i18n/locales/en.json
git commit -m "feat: show dashboard button in public header when authenticated"
```

---

### Task 4: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add entry to "Aktivní plány a změny" section in CLAUDE.md**

Add the following block at the top of the "Aktivní plány a změny" section (before the 2026-05-06 entry):

```markdown
### 2026-05-08 — Public header: auth-aware CTA ✅ KOMPLETNÍ (feat/public-auth-header)

**Spec:** `docs/superpowers/specs/2026-05-08-public-auth-header.md`
**Plán:** `docs/superpowers/plans/2026-05-08-public-auth-header.md`

**Co bylo implementováno:**
- `domains.global.ts`: odstraněn blok který přesměrovával přihlášené uživatele z veřejných stránek na app doménu
- `public.vue`: přidán `useAuthStore()` + `onMounted` inicializace; header zobrazuje "Dashboard →" (`/dashboard`) pro přihlášené, "Login →" pro nepřihlášené
- i18n: přidán klíč `nav.dashboard` do cs.json + en.json
- Testy: `frontend/middleware/domains.test.ts` (5 testů), `frontend/layouts/public.test.ts` (3 testy)
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with public auth header changes"
```

- [ ] **Step 3: Push branch**

```bash
git push
```
