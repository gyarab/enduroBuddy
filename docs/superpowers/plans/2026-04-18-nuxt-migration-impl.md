# Nuxt Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nahradit Vite SPA + Django HTML templates jedním Nuxt 3 stackem se SSR pro veřejné stránky a SPA pro přihlášenou část.

**Architecture:** Nuxt 3 (Node.js :3000) sedí před Djangem (:8000). Nginx routuje `/api/*` a `/admin/*` → Django, vše ostatní → Nuxt. Existující Vue 3 komponenty jsou kompatibilní s Nuxt beze změn — stačí je přesunout. `axios` nahrazuje `$fetch` wrapper s CSRF hlavičkou. Vlastní `useI18n` nahrazuje `@nuxtjs/i18n` (potřeba pro SSR). Stránky vzniknou jako `pages/` soubory z existujícího `router/index.ts`.

**Tech Stack:** Nuxt 3.11+, @pinia/nuxt, @nuxtjs/i18n 9, Nginx 1.25, pnpm (předpoklad: Task 3 z infrastructure plánu hotov)

**Předpoklad:** Plán `2026-04-18-infrastructure.md` je hotov (pnpm nainstalováno).

---

## File Map

### Frontend — nové soubory

| Akce | Soubor |
|------|--------|
| Create | `frontend/nuxt.config.ts` |
| Create | `frontend/app.vue` |
| Create | `frontend/error.vue` |
| Create | `frontend/layouts/default.vue` |
| Create | `frontend/layouts/public.vue` |
| Create | `frontend/layouts/auth.vue` |
| Create | `frontend/pages/index.vue` |
| Create | `frontend/pages/about.vue` |
| Create | `frontend/pages/terms.vue` |
| Create | `frontend/pages/privacy.vue` |
| Create | `frontend/pages/app/dashboard.vue` |
| Create | `frontend/pages/app/profile/complete.vue` |
| Create | `frontend/pages/coach/plans.vue` |
| Create | `frontend/pages/accounts/[...slug].vue` |
| Create | `frontend/utils/api.ts` |
| Create | `frontend/plugins/pinia.ts` |
| Create | `frontend/components/training/PlannedKmRulesModal.vue` |
| Rename/Move | `frontend/src/` → `frontend/` (viz Task 2) |

### Frontend — smazané soubory

| Soubor |
|--------|
| `frontend/src/main.ts` |
| `frontend/src/App.vue` |
| `frontend/src/router/index.ts` |
| `frontend/src/composables/useI18n.ts` |
| `frontend/vite.config.ts` |

### Backend — smazané soubory (Task 10)

| Soubor |
|--------|
| `backend/templates/public/` (celý adresář) |
| `backend/templates/spa.html` |
| `backend/static/css/public-*.css` |
| Views a URL patterns pro HTML stránky |

### Infrastruktura

| Akce | Soubor |
|------|--------|
| Create | `frontend/Dockerfile` |
| Modify | `docker-compose.yml` |
| Create | `nginx/nginx.conf` |
| Create | `nginx/Dockerfile` |

---

## Task 1: Inicializace Nuxt 3

**Files:**
- Create: `frontend/nuxt.config.ts`
- Create: `frontend/package.json` (update)
- Modify: `frontend/.npmrc`

- [ ] **Krok 1: Zálohovat aktuální frontend**

```bash
cd frontend
git stash  # nebo pracuj na větvi feat/nuxt-migration
```

- [ ] **Krok 2: Přidat Nuxt do package.json**

Nahradit `frontend/package.json`:

```json
{
  "name": "endurobuddy-frontend",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "nuxt dev",
    "build": "nuxt build",
    "preview": "nuxt preview",
    "test": "vitest",
    "typecheck": "nuxt typecheck"
  },
  "dependencies": {
    "nuxt": "^3.11.0",
    "@pinia/nuxt": "^0.9.0",
    "@nuxtjs/i18n": "^9.0.0",
    "pinia": "^3.0.3"
  },
  "devDependencies": {
    "@nuxt/test-utils": "^3.13.0",
    "@vue/test-utils": "^2.4.6",
    "jsdom": "^26.1.0",
    "typescript": "^5.8.3",
    "vitest": "^3.1.2"
  }
}
```

- [ ] **Krok 3: Nainstalovat deps**

```bash
cd frontend
pnpm install
```

Očekávaný výstup: `Packages: +X added`

- [ ] **Krok 4: Vytvořit `frontend/nuxt.config.ts`**

```typescript
export default defineNuxtConfig({
  compatibilityDate: "2024-11-01",
  devtools: { enabled: true },

  modules: [
    "@pinia/nuxt",
    "@nuxtjs/i18n",
  ],

  routeRules: {
    "/": { ssr: true },
    "/about": { ssr: true },
    "/terms": { ssr: true },
    "/privacy": { ssr: true },
    "/app/**": { ssr: false },
    "/coach/**": { ssr: false },
    "/accounts/**": { ssr: false },
  },

  runtimeConfig: {
    public: {
      apiBase: "/api/v1",
    },
  },

  i18n: {
    locales: [
      { code: "cs", file: "cs.json" },
      { code: "en", file: "en.json" },
    ],
    defaultLocale: "cs",
    langDir: "i18n/",
    strategy: "no_prefix",
  },

  css: [
    "~/assets/design-tokens.css",
    "~/assets/fonts.css",
  ],

  vite: {
    server: {
      proxy: {
        "/api": "http://localhost:8000",
        "/admin": "http://localhost:8000",
        "/accounts": "http://localhost:8000",
        "/i18n": "http://localhost:8000",
        "/static": "http://localhost:8000",
      },
    },
  },
})
```

- [ ] **Krok 5: Ověřit, že Nuxt startuje**

```bash
cd frontend
pnpm dev
```

Očekávaný výstup: `Nuxt 3.x.x ready on http://localhost:3000`

- [ ] **Krok 6: Commit**

```bash
git add frontend/package.json frontend/nuxt.config.ts frontend/pnpm-lock.yaml
git commit -m "feat: add Nuxt 3 config and dependencies"
```

---

## Task 2: Přesunout src/ do Nuxt struktury

**Files:**
- Move: `frontend/src/components/` → `frontend/components/`
- Move: `frontend/src/stores/` → `frontend/stores/`
- Move: `frontend/src/composables/` (bez useI18n.ts) → `frontend/composables/`
- Move: `frontend/src/assets/` → `frontend/assets/`
- Move: `frontend/src/locales/` → `frontend/i18n/`
- Move: `frontend/src/utils/` → `frontend/utils/`

Nuxt automaticky auto-importuje soubory z `components/`, `composables/`, `utils/`, `stores/`.

- [ ] **Krok 1: Přesunout adresáře**

```bash
cd frontend
cp -r src/components .
cp -r src/stores .
cp -r src/assets .
cp -r src/utils .
mkdir -p composables
mkdir -p i18n

# Composables — bez useI18n.ts (nahrazuje @nuxtjs/i18n)
for f in src/composables/*.ts; do
  name=$(basename "$f")
  if [ "$name" != "useI18n.ts" ]; then
    cp "$f" composables/
  fi
done

# Locales → i18n/
cp src/locales/cs.json i18n/cs.json
cp src/locales/en.json i18n/en.json
```

- [ ] **Krok 2: Opravit importy v přesunutých souborech**

Nahradit `@/` importy ve všech přesunutých souborech. Nuxt auto-importuje z `composables/`, `utils/`, `stores/` — relative importy `~/` fungují pro vše ostatní.

```bash
# Příkaz nahradí @/ za ~/src/ → ~/  v composables, stores, components
find composables stores components utils -name "*.ts" -o -name "*.vue" | \
  xargs sed -i 's|from "@/composables/|from "~/composables/|g; s|from "@/stores/|from "~/stores/|g; s|from "@/api/|from "~/utils/api|g; s|from "@/locales/|from "~/i18n/|g; s|from "@/utils/|from "~/utils/|g; s|from "@/components/|from "~/components/|g'
```

Pozor: `@/api/` importy je potřeba nahradit ručně po vytvoření `utils/api.ts` v Task 3.

- [ ] **Krok 3: Smazat api/ adresář ze src (nahradí utils/api.ts)**

Stávající `src/api/*.ts` soubory jsou wrappers nad `axios`. V Task 3 vznikne nový `utils/api.ts` s `$fetch`. Soubory z `src/api/` poslouží jako reference — zkopírovat pro přehled, ale nepoužívat přímo.

```bash
cp -r src/api /tmp/endurobuddy-api-backup  # záloha pro referenci
```

- [ ] **Krok 4: Ověřit TypeScript**

```bash
cd frontend
pnpm typecheck 2>&1 | head -30
```

Chyby týkající se `useI18n` a importů jsou očekávané — řeší se v dalších taskech.

- [ ] **Krok 5: Commit**

```bash
git add components/ stores/ composables/ assets/ i18n/ utils/
git commit -m "feat: move Vue components and stores to Nuxt directory structure"
```

---

## Task 3: Vytvořit $fetch API klient

Nahrazuje `src/api/client.ts` (axios) + všechny `src/api/*.ts` wrappers.

**Files:**
- Create: `frontend/utils/api.ts`

- [ ] **Krok 1: Napsat test pro API util**

Vytvořit `frontend/utils/api.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest"

// Mock $fetch (není dostupný mimo Nuxt runtime)
vi.mock("#app", () => ({
  useRequestHeaders: () => ({}),
  useCookie: () => ({ value: "test-csrf-token" }),
}))

describe("apiFetch CSRF", () => {
  it("adds X-CSRFToken header from cookie", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({ ok: true })
    vi.stubGlobal("$fetch", fetchSpy)

    const { apiFetch } = await import("~/utils/api")
    await apiFetch("/test/")

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining("/test/"),
      expect.objectContaining({
        headers: expect.objectContaining({
          "X-CSRFToken": "test-csrf-token",
        }),
      })
    )
  })
})
```

- [ ] **Krok 2: Spustit test — ověřit FAIL**

```bash
cd frontend
pnpm test utils/api.test.ts
```

Očekávaný výstup: `FAIL — Cannot find module '~/utils/api'`

- [ ] **Krok 3: Vytvořit `frontend/utils/api.ts`**

```typescript
import { useCookie } from "#app"

export interface ApiOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE"
  body?: Record<string, unknown> | FormData
  params?: Record<string, string | number>
}

export async function apiFetch<T = unknown>(
  path: string,
  options: ApiOptions = {}
): Promise<T> {
  const csrfToken = useCookie("endurobuddy_csrftoken")

  return $fetch<T>(path, {
    baseURL: "/api/v1",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      ...(csrfToken.value ? { "X-CSRFToken": csrfToken.value } : {}),
    },
    method: options.method ?? "GET",
    ...(options.body ? { body: options.body } : {}),
    ...(options.params ? { params: options.params } : {}),
  })
}
```

- [ ] **Krok 4: Přesunout API wrappers**

Zkopírovat a upravit `src/api/*.ts` — nahradit `apiClient.get/post/patch/delete` za `apiFetch`:

Příklad `utils/api/training.ts` (ostatní soubory analogicky):

```typescript
import { apiFetch } from "~/utils/api"

export type DashboardData = {
  /* ... stávající typy z src/api/training.ts ... */
}

export const fetchDashboard = (year: number, month: number) =>
  apiFetch<DashboardData>(`/training/dashboard/`, { params: { year, month } })
```

Vytvořit soubory:
- `frontend/utils/api/auth.ts` (z `src/api/auth.ts`)
- `frontend/utils/api/training.ts` (z `src/api/training.ts`)
- `frontend/utils/api/coach.ts` (z `src/api/coach.ts`)
- `frontend/utils/api/imports.ts` (z `src/api/imports.ts`)
- `frontend/utils/api/invites.ts` (z `src/api/invites.ts`)
- `frontend/utils/api/notifications.ts` (z `src/api/notifications.ts`)
- `frontend/utils/api/profile.ts` (z `src/api/profile.ts`)
- `frontend/utils/api/legend.ts` (z `src/api/legend.ts`)

- [ ] **Krok 5: Aktualizovat importy v stores a composables**

```bash
find composables stores -name "*.ts" | xargs grep -l "@/api/" | while read f; do
  sed -i 's|from "@/api/|from "~/utils/api/|g' "$f"
done
```

- [ ] **Krok 6: Ověřit typecheck**

```bash
pnpm typecheck 2>&1 | grep -v "useI18n" | head -30
```

Cíl: žádné chyby kromě `useI18n` (řeší se v Task 4).

- [ ] **Krok 7: Commit**

```bash
git add utils/
git commit -m "feat: replace axios with \$fetch wrapper for Nuxt-compatible API calls"
```

---

## Task 4: Nahradit vlastní useI18n za @nuxtjs/i18n

**Files:**
- Modify: `frontend/composables/useGarminImport.ts`
- Modify: Všechny komponenty a stores používající `useI18n()`

- [ ] **Krok 1: Najít všechna použití**

```bash
cd frontend
grep -r "useI18n" --include="*.ts" --include="*.vue" -l
```

- [ ] **Krok 2: Strategie náhrady**

`@nuxtjs/i18n` auto-importuje `useI18n` z `vue-i18n` — stejné API: `const { t, locale } = useI18n()`.

`setLocale(lang)` se nahrazuje voláním `setLocale` z `@nuxtjs/i18n`:
```typescript
// Před:
import { useI18n } from "@/composables/useI18n"
const { t, setLocale } = useI18n()

// Po: (auto-importováno Nuxtem)
const { t, locale } = useI18n()
const { setLocale } = useI18n()
```

Synchronizace jazyka s Django session zůstává — přesunout logiku ze starého `useI18n.ts` do pluginu.

- [ ] **Krok 3: Vytvořit `frontend/plugins/i18n-sync.client.ts`**

```typescript
export default defineNuxtPlugin(() => {
  const { locale } = useI18n()

  async function syncWithDjango(lang: string) {
    const csrfToken = useCookie("endurobuddy_csrftoken")
    try {
      await $fetch("/i18n/set_language/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          ...(csrfToken.value ? { "X-CSRFToken": csrfToken.value } : {}),
        },
        body: `language=${lang}`,
      })
    } catch {
      // Non-critical — jazyk je přepnutý v Nuxtu
    }
  }

  watch(locale, (newLocale) => {
    void syncWithDjango(newLocale)
  })
})
```

- [ ] **Krok 4: Nahradit importy useI18n v komponentách**

Ve všech souborech kde je `import { useI18n } from "@/composables/useI18n"` nebo `import { useI18n } from "~/composables/useI18n"` — smazat import (Nuxt auto-importuje `useI18n` z `@nuxtjs/i18n`).

```bash
find composables stores components -name "*.ts" -o -name "*.vue" | \
  xargs sed -i '/from "~\/composables\/useI18n"/d; /from "@\/composables\/useI18n"/d'
```

- [ ] **Krok 5: Ověřit testy**

```bash
cd frontend
pnpm test
```

Cíl: testy pro `useGarminImport`, `useInlineEditor` atd. zelené.

- [ ] **Krok 6: Commit**

```bash
git add composables/ plugins/ components/ stores/
git commit -m "feat: replace custom useI18n with @nuxtjs/i18n auto-import"
```

---

## Task 5: Vytvořit app.vue a layouts

**Files:**
- Create: `frontend/app.vue`
- Create: `frontend/layouts/default.vue`
- Create: `frontend/layouts/public.vue`
- Create: `frontend/layouts/auth.vue`

- [ ] **Krok 1: Vytvořit `frontend/app.vue`**

```vue
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

- [ ] **Krok 2: Vytvořit `frontend/layouts/default.vue`**

Layout pro přihlášenou část (`/app/*`, `/coach/*`). Obsahuje `AppShell` z existující komponenty.

```vue
<template>
  <AppShell>
    <slot />
  </AppShell>
</template>
```

Ověřit, že `components/layout/AppShell.vue` existuje — pokud ne, přesunout z `src/`.

- [ ] **Krok 3: Vytvořit `frontend/layouts/public.vue`**

Ekvivalent `backend/templates/public/base_public.html`. Topbar + footer bez Bootstrapu.

```vue
<template>
  <div class="eb-public-root">
    <header class="eb-topbar">
      <div class="eb-public-shell eb-topbar-inner">
        <NuxtLink to="/" class="eb-topbar-brand" aria-label="EnduroBuddy">
          <img src="/brand/eb-logo-full.svg" alt="EnduroBuddy" class="eb-logo-full">
          <img src="/brand/eb-logo-compact.svg" alt="EB" class="eb-logo-compact">
        </NuxtLink>

        <nav class="eb-topbar-nav">
          <slot name="nav">
            <NuxtLink to="/#features">{{ t("nav.features") }}</NuxtLink>
            <NuxtLink to="/#how">{{ t("nav.howItWorks") }}</NuxtLink>
            <NuxtLink to="/about">{{ t("nav.about") }}</NuxtLink>
          </slot>
        </nav>

        <div class="eb-topbar-actions">
          <slot name="actions">
            <NuxtLink to="/accounts/login/" class="eb-btn-nav">
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
            <img src="/brand/eb-logo-full.svg" alt="EnduroBuddy" class="eb-footer-logo">
            <p class="eb-footer-tagline">{{ t("footer.tagline") }}</p>
          </div>
          <nav class="eb-footer-nav">
            <NuxtLink to="/">{{ t("nav.home") }}</NuxtLink>
            <NuxtLink to="/about">{{ t("nav.about") }}</NuxtLink>
            <NuxtLink to="/terms">{{ t("nav.terms") }}</NuxtLink>
            <NuxtLink to="/privacy">{{ t("nav.privacy") }}</NuxtLink>
          </nav>
          <div class="eb-footer-lang">
            <button @click="setLocale('cs')">Česky</button>
            <button @click="setLocale('en')">English</button>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n()
const { setLocale } = useI18n()
</script>
```

Přidat i18n klíče do `i18n/cs.json` a `i18n/en.json`:
```json
"nav": {
  "home": "Domů",
  "features": "Funkce",
  "howItWorks": "Jak funguje",
  "about": "O aplikaci",
  "login": "Přihlášení",
  "terms": "Podmínky",
  "privacy": "Ochrana dat"
},
"footer": {
  "tagline": "Tréninkový workspace pro trenéry a sportovce."
}
```

- [ ] **Krok 4: Vytvořit `frontend/layouts/auth.vue`**

Layout pro auth stránky (bez navigace, centrovaný formulář).

```vue
<template>
  <div class="eb-auth-root">
    <slot />
  </div>
</template>
```

- [ ] **Krok 5: Commit**

```bash
git add app.vue layouts/
git commit -m "feat: add Nuxt layouts (default, public, auth)"
```

---

## Task 6: Vytvořit pages pro přihlášenou část

**Files:**
- Create: `frontend/pages/app/dashboard.vue`
- Create: `frontend/pages/app/profile/complete.vue`
- Create: `frontend/pages/coach/plans.vue`
- Create: `frontend/pages/accounts/[...slug].vue`
- Create: `frontend/pages/app/index.vue` (redirect)
- Create: `frontend/pages/coach/index.vue` (redirect)

- [ ] **Krok 1: Vytvořit `frontend/pages/app/dashboard.vue`**

```vue
<template>
  <AthleteView />
</template>

<script setup lang="ts">
definePageMeta({ layout: "default" })
</script>
```

- [ ] **Krok 2: Vytvořit `frontend/pages/app/index.vue`**

```vue
<script setup lang="ts">
navigateTo("/app/dashboard", { replace: true })
</script>
```

- [ ] **Krok 3: Vytvořit `frontend/pages/app/profile/complete.vue`**

```vue
<template>
  <CompleteProfileView />
</template>

<script setup lang="ts">
definePageMeta({ layout: "default" })
</script>
```

- [ ] **Krok 4: Vytvořit `frontend/pages/coach/plans.vue`**

```vue
<template>
  <CoachView />
</template>

<script setup lang="ts">
definePageMeta({ layout: "default" })
</script>
```

- [ ] **Krok 5: Vytvořit `frontend/pages/coach/index.vue`**

```vue
<script setup lang="ts">
navigateTo("/coach/plans", { replace: true })
</script>
```

- [ ] **Krok 6: Vytvořit `frontend/pages/accounts/[...slug].vue`**

Auth flow — všechny `/accounts/*` URL obsluhy deleguje na `AuthFlowView`. Slug v URL určuje, jaká obrazovka se zobrazí.

```vue
<template>
  <AuthFlowView :auth-screen="screen" />
</template>

<script setup lang="ts">
definePageMeta({ layout: "auth" })

const route = useRoute()
const slug = route.params.slug as string[]
const path = slug.join("/")

const screenMap: Record<string, string> = {
  "login": "login",
  "signup": "signup",
  "logout": "logout",
  "password/reset": "password-reset",
  "password/reset/done": "password-reset-done",
  "confirm-email": "verification-sent",
  "inactive": "inactive",
  "email": "email-management",
  "password/change": "password-change",
  "password/set": "password-set",
  "password/reset/key/done": "password-reset-key-done",
  "social/login/error": "social-error",
  "social/login/cancelled": "social-cancelled",
  "social/connections": "connections",
  "reauthenticate": "reauthenticate",
}

const screen = computed(() => screenMap[path] ?? "login")
</script>
```

- [ ] **Krok 7: Commit**

```bash
git add pages/
git commit -m "feat: add Nuxt pages for authenticated routes (/app/*, /coach/*, /accounts/*)"
```

---

## Task 7: Vytvořit SSR veřejné stránky

**Files:**
- Create: `frontend/pages/index.vue`
- Create: `frontend/pages/about.vue`
- Create: `frontend/pages/terms.vue`
- Create: `frontend/pages/privacy.vue`
- Migrate CSS: `backend/static/css/public-home.css` → `frontend/assets/css/public-home.css`

- [ ] **Krok 1: Přesunout CSS pro veřejné stránky do assets**

```bash
mkdir -p frontend/assets/css
cp backend/static/css/public-base.css frontend/assets/css/public-base.css
cp backend/static/css/public-home.css frontend/assets/css/public-home.css
cp backend/static/css/public-about.css frontend/assets/css/public-about.css
cp backend/static/css/public-legal.css frontend/assets/css/public-legal.css
```

Přidat do `nuxt.config.ts`:
```typescript
css: [
  "~/assets/design-tokens.css",
  "~/assets/fonts.css",
  "~/assets/css/public-base.css",  // přidat
],
```

- [ ] **Krok 2: Vytvořit `frontend/pages/index.vue`**

Přepis `backend/templates/public/home.html` do Vue. HTML struktura se portuje 1:1, `{% if CURRENT_LANGUAGE == "en" %}..{% else %}..{% endif %}` se nahrazuje `t("klíč")`.

```vue
<template>
  <main class="lp-main">
    <!-- HERO -->
    <section class="lp-shell lp-hero">
      <div class="lp-hero-left">
        <div class="lp-eyebrow">
          <span class="lp-eyebrow-dot"></span>
          {{ t("landing.eyebrow") }}
        </div>
        <h1 class="lp-h1" v-html="t('landing.headline')"></h1>
        <p class="lp-subtitle">{{ t("landing.subtitle") }}</p>
        <div class="lp-actions">
          <NuxtLink
            v-if="registrationEnabled"
            class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill"
            to="/accounts/signup/"
          >{{ t("landing.ctaPrimary") }}</NuxtLink>
          <span v-else class="lp-btn lp-btn-primary lp-btn-lg lp-btn-pill eb-btn-disabled">
            {{ t("landing.ctaPrimary") }}
          </span>
          <a class="lp-btn lp-btn-ghost lp-btn-lg" href="#how">{{ t("landing.ctaSecondary") }}</a>
        </div>
        <div class="lp-pills">
          <span class="lp-pill">{{ t("landing.pill1") }}</span>
          <span class="lp-pill">{{ t("landing.pill2") }}</span>
          <span class="lp-pill">{{ t("landing.pill3") }}</span>
        </div>
      </div>

      <!-- Hero panel mockup — portovat HTML ze šablony 1:1 -->
      <div class="lp-hero-right">
        <!-- ... obsah z home.html sekce lp-panel ... -->
      </div>
    </section>

    <!-- FEATURES, HOW IT WORKS, AUDIENCE, CTA — portovat ze šablony -->
  </main>
</template>

<script setup lang="ts">
definePageMeta({ layout: "public" })

const { t } = useI18n()

// Načtení registration_enabled flagy z backend API
const { data: siteConfig } = await useFetch("/api/v1/site-config/", {
  default: () => ({ registration_enabled: false }),
})
const registrationEnabled = computed(() => siteConfig.value?.registration_enabled ?? false)

useSeoMeta({
  title: t("landing.seoTitle"),
  description: t("landing.seoDescription"),
})
</script>
```

Přidat i18n klíče do obou locale souborů pro všechny texty z `home.html`.

Poznámka: `registration_enabled` přijde z nového `GET /api/v1/site-config/` endpointu — viz Task 9.

- [ ] **Krok 3: Vytvořit `frontend/pages/about.vue`**

Stejný postup — portovat `backend/templates/public/about.html` do Vue komponent s `t()`.

```vue
<template>
  <main class="about-main">
    <!-- portovat sekce intro, story, mission, founder z about.html -->
  </main>
</template>

<script setup lang="ts">
definePageMeta({ layout: "public" })
const { t } = useI18n()
useSeoMeta({ title: t("about.seoTitle") })
</script>
```

- [ ] **Krok 4: Vytvořit `frontend/pages/terms.vue` a `privacy.vue`**

```vue
<!-- terms.vue -->
<template>
  <main class="legal-main">
    <div class="legal-card">
      <NuxtLink to="/" class="legal-back">← {{ t("legal.back") }}</NuxtLink>
      <h1>{{ t("legal.termsTitle") }}</h1>
      <!-- portovat obsah z terms.html -->
    </div>
  </main>
</template>

<script setup lang="ts">
definePageMeta({ layout: "public" })
const { t } = useI18n()
</script>
```

- [ ] **Krok 5: Ověřit SSR výstup**

```bash
cd frontend
pnpm build && pnpm preview
curl http://localhost:3000/ | grep "<title>"
```

Očekávaný výstup: `<title>EnduroBuddy | Moderní platforma...</title>` (kompletní HTML, ne prázdná stránka)

- [ ] **Krok 6: Commit**

```bash
git add pages/index.vue pages/about.vue pages/terms.vue pages/privacy.vue assets/css/
git commit -m "feat: add SSR public pages (landing, about, terms, privacy)"
```

---

## Task 8: Error stránka a PlannedKmRulesModal

**Files:**
- Create: `frontend/error.vue`
- Create: `frontend/components/training/PlannedKmRulesModal.vue`
- Modify: `frontend/components/training/PlannedRow.vue`

- [ ] **Krok 1: Vytvořit `frontend/error.vue`**

```vue
<template>
  <div class="eb-error-root">
    <div class="eb-error-card">
      <div class="eb-error-code">{{ error.statusCode }}</div>
      <h1 class="eb-error-title">{{ title }}</h1>
      <p class="eb-error-message">{{ error.message }}</p>
      <NuxtLink to="/" class="eb-btn eb-btn-primary">
        {{ t("error.goHome") }}
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { NuxtError } from "#app"

const props = defineProps<{ error: NuxtError }>()
const { t } = useI18n()

const title = computed(() => {
  if (props.error.statusCode === 404) return t("error.notFound")
  if (props.error.statusCode === 403) return t("error.forbidden")
  return t("error.generic")
})
</script>

<style scoped>
.eb-error-root {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--eb-bg);
}
.eb-error-card {
  text-align: center;
  padding: 3rem;
}
.eb-error-code {
  font-family: var(--eb-font-mono);
  font-size: 6rem;
  color: var(--eb-lime);
  line-height: 1;
}
.eb-error-title {
  font-family: var(--eb-font-display);
  font-size: 2rem;
  color: var(--eb-text);
  margin: 1rem 0 0.5rem;
}
.eb-error-message {
  color: var(--eb-text-muted);
  margin-bottom: 2rem;
}
</style>
```

Přidat i18n klíče: `error.notFound`, `error.forbidden`, `error.generic`, `error.goHome`.

- [ ] **Krok 2: Napsat test pro PlannedKmRulesModal**

Vytvořit `frontend/components/training/PlannedKmRulesModal.test.ts`:

```typescript
import { describe, it, expect } from "vitest"
import { mount } from "@vue/test-utils"
import PlannedKmRulesModal from "./PlannedKmRulesModal.vue"

describe("PlannedKmRulesModal", () => {
  it("is hidden when isOpen is false", () => {
    const wrapper = mount(PlannedKmRulesModal, {
      props: { isOpen: false },
    })
    expect(wrapper.find(".eb-modal-overlay").exists()).toBe(false)
  })

  it("shows content when isOpen is true", () => {
    const wrapper = mount(PlannedKmRulesModal, {
      props: { isOpen: true },
    })
    expect(wrapper.find(".eb-modal-overlay").exists()).toBe(true)
  })

  it("emits close event on overlay click", async () => {
    const wrapper = mount(PlannedKmRulesModal, {
      props: { isOpen: true },
    })
    await wrapper.find(".eb-modal-overlay").trigger("click")
    expect(wrapper.emitted("close")).toBeTruthy()
  })
})
```

- [ ] **Krok 3: Spustit test — ověřit FAIL**

```bash
pnpm test components/training/PlannedKmRulesModal.test.ts
```

- [ ] **Krok 4: Vytvořit `frontend/components/training/PlannedKmRulesModal.vue`**

```vue
<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="eb-modal-overlay"
      @click.self="$emit('close')"
    >
      <div class="eb-modal" role="dialog" aria-modal="true">
        <div class="eb-modal-header">
          <h2 class="eb-modal-title">{{ t("kmRules.title") }}</h2>
          <button class="eb-modal-close" @click="$emit('close')" aria-label="Zavřít">✕</button>
        </div>
        <div class="eb-modal-body km-rules-body">
          <section>
            <h3>{{ t("kmRules.basicTitle") }}</h3>
            <ul>
              <li><code>15</code> — {{ t("kmRules.basicKm") }}</li>
              <li><code>1:30</code> — {{ t("kmRules.basicTime") }}</li>
              <li><code>15 / 1:30</code> — {{ t("kmRules.basicBoth") }}</li>
            </ul>
          </section>
          <section>
            <h3>{{ t("kmRules.typeTitle") }}</h3>
            <ul>
              <li><code>15 Z</code> — {{ t("kmRules.typeZ") }}</li>
              <li><code>15 T</code> — {{ t("kmRules.typeT") }}</li>
              <li><code>15 TV</code> — {{ t("kmRules.typeTV") }}</li>
            </ul>
          </section>
          <section>
            <h3>{{ t("kmRules.intervalsTitle") }}</h3>
            <ul>
              <li><code>10 + 5×1 Z</code> — {{ t("kmRules.intervalsExample") }}</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{ isOpen: boolean }>()
defineEmits<{ close: [] }>()
const { t } = useI18n()
</script>

<style scoped>
.eb-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.eb-modal {
  background: var(--eb-surface);
  border: 1px solid var(--eb-border);
  border-radius: var(--eb-radius-lg);
  width: min(520px, 90vw);
  max-height: 80vh;
  overflow-y: auto;
}
.eb-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--eb-border);
}
.eb-modal-title {
  font-family: var(--eb-font-display);
  font-size: 1.125rem;
  color: var(--eb-text);
  margin: 0;
}
.eb-modal-close {
  background: none;
  border: none;
  color: var(--eb-text-muted);
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
}
.eb-modal-body { padding: 1.5rem; }
.km-rules-body section { margin-bottom: 1.5rem; }
.km-rules-body h3 { color: var(--eb-text); font-size: 0.875rem; font-weight: 600; margin-bottom: 0.5rem; }
.km-rules-body ul { list-style: none; padding: 0; margin: 0; }
.km-rules-body li { color: var(--eb-text-muted); font-size: 0.875rem; margin-bottom: 0.25rem; }
.km-rules-body code { font-family: var(--eb-font-mono); color: var(--eb-lime); }
</style>
```

- [ ] **Krok 5: Integrovat do PlannedRow.vue**

V `components/training/PlannedRow.vue` přidat help ikonu a modal:

```vue
<!-- Přidat do template vedle existujícího help tlačítka -->
<button class="planned-row-help" @click="showKmRules = true" title="Pravidla zápisu">?</button>
<PlannedKmRulesModal :is-open="showKmRules" @close="showKmRules = false" />
```

```typescript
// V <script setup>
const showKmRules = ref(false)
```

- [ ] **Krok 6: Spustit všechny testy**

```bash
pnpm test
```

Očekávaný výstup: všechny testy zelené.

- [ ] **Krok 7: Commit**

```bash
git add error.vue components/training/PlannedKmRulesModal.vue components/training/PlannedRow.vue
git commit -m "feat: add error page and PlannedKmRulesModal component"
```

---

## Task 9: Backend — přidat /api/v1/site-config/ endpoint

Potřebuje ho landing page pro `registration_enabled` flag.

**Files:**
- Modify: `backend/api/views/dashboard.py` nebo nový `backend/api/views/config.py`
- Modify: `backend/api/urls.py`

- [ ] **Krok 1: Vytvořit view**

Přidat do `backend/api/views/dashboard.py` (nebo nový soubor):

```python
from django.conf import settings
from django.http import JsonResponse


def site_config(request):
    return JsonResponse({
        "registration_enabled": bool(getattr(settings, "REGISTRATION_ENABLED", True)),
    })
```

- [ ] **Krok 2: Přidat URL**

V `backend/api/urls.py` přidat:

```python
path("site-config/", views.dashboard.site_config, name="site-config"),
```

- [ ] **Krok 3: Ověřit endpoint**

```bash
cd backend
python manage.py shell -c "
from django.test import RequestFactory
from api.views.dashboard import site_config
r = RequestFactory().get('/api/v1/site-config/')
resp = site_config(r)
print(resp.content)
"
```

Očekávaný výstup: `{"registration_enabled": true}`

- [ ] **Krok 4: Commit**

```bash
git add backend/api/views/ backend/api/urls.py
git commit -m "feat: add /api/v1/site-config/ endpoint for registration_enabled flag"
```

---

## Task 10: Docker — Nuxt jako samostatný service

**Files:**
- Create: `frontend/Dockerfile`
- Modify: `docker-compose.yml`
- Create: `nginx/nginx.conf`
- Create: `nginx/Dockerfile`

- [ ] **Krok 1: Vytvořit `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine AS builder

RUN npm install -g pnpm

WORKDIR /app

COPY pnpm-lock.yaml package.json .npmrc ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

FROM node:20-alpine AS runtime

WORKDIR /app

COPY --from=builder /app/.output ./.output

EXPOSE 3000

ENV NODE_ENV=production
ENV NITRO_HOST=0.0.0.0
ENV NITRO_PORT=3000

CMD ["node", ".output/server/index.mjs"]
```

- [ ] **Krok 2: Aktualizovat `docker-compose.yml`**

Přidat `nuxt` service a `nginx` service, odebrat starý `frontend` service:

```yaml
  nuxt:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: endurobuddy-nuxt
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      NUXT_PUBLIC_API_BASE: /api/v1
    depends_on:
      - web
    networks:
      - backend

  nginx:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: endurobuddy-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - web
      - nuxt
    networks:
      - backend
```

- [ ] **Krok 3: Vytvořit `nginx/nginx.conf`**

```nginx
upstream django {
    server web:8000;
}

upstream nuxt {
    server nuxt:3000;
}

server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location /api/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /admin/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        proxy_pass http://django;
    }

    location /i18n/ {
        proxy_pass http://django;
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://nuxt;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

- [ ] **Krok 4: Vytvořit `nginx/Dockerfile`**

```dockerfile
FROM nginx:1.25-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

- [ ] **Krok 5: Ověřit build**

```bash
docker compose build nuxt nginx
docker compose up -d
curl http://localhost/ | grep "<title>"
```

Očekávaný výstup: `<title>EnduroBuddy...`

- [ ] **Krok 6: Commit**

```bash
git add frontend/Dockerfile nginx/ docker-compose.yml
git commit -m "feat: add Nuxt and Nginx Docker services"
```

---

## Task 11: Cleanup Django templates

**Files:**
- Delete: `backend/templates/public/` (celý adresář)
- Delete: `backend/templates/spa.html`
- Delete: `backend/static/css/public-*.css`
- Modify: `backend/config/urls.py`
- Modify: `backend/dashboard/views_home.py` nebo ekvivalentní views

- [ ] **Krok 1: Ověřit, že Nuxt obsluhuje všechny URL**

```bash
curl http://localhost/ -I | grep "HTTP"        # → 200 od Nuxt
curl http://localhost/about -I | grep "HTTP"   # → 200 od Nuxt
curl http://localhost/api/v1/site-config/ -I   # → 200 od Django
```

- [ ] **Krok 2: Smazat public templates a CSS**

```bash
rm -rf backend/templates/public/
rm backend/templates/spa.html
rm backend/static/css/public-base.css
rm backend/static/css/public-home.css
rm backend/static/css/public-about.css
rm backend/static/css/public-legal.css
```

- [ ] **Krok 3: Odebrat URL patterns pro HTML views**

V `backend/config/urls.py` odebrat URL patterns pro:
- `public_home`, `public_about`, `public_terms`, `public_privacy`
- SPA entry point (URL pattern servující `spa.html`)

Zachovat:
- `/api/v1/` — DRF/vlastní API
- `/admin/` — Django admin
- `/accounts/` — allauth (zpracování POST)
- `/i18n/` — language switcher

- [ ] **Krok 4: Spustit Django check**

```bash
cd backend
python manage.py check
```

Očekávaný výstup: `System check identified no issues (0 silenced).`

- [ ] **Krok 5: Ověřit, že `/accounts/login/` POST stále funguje**

```bash
curl -c cookies.txt -b cookies.txt -X POST http://localhost/accounts/login/ \
  -H "X-CSRFToken: $(cat cookies.txt | grep csrf | awk '{print $7}')" \
  -d "login=test@example.com&password=wrong"
```

Očekávaný výstup: 302 redirect nebo 200 s error (allauth zpracoval request).

- [ ] **Krok 6: Commit**

```bash
git add backend/config/urls.py backend/
git rm -r backend/templates/public/ backend/templates/spa.html
git rm backend/static/css/public-*.css
git commit -m "feat: remove Django HTML templates and public views — Nuxt now handles all frontend"
```

---

## Task 12: QA a SSR ověření

- [ ] **Krok 1: Ověřit SSR meta tagy**

```bash
curl http://localhost/ | grep -E "<title>|<meta name"
```

Očekávaný výstup:
```html
<title>EnduroBuddy | Moderní platforma pro vytrvalostní trénink</title>
<meta name="description" content="...">
```

- [ ] **Krok 2: Ověřit SPA navigaci**

```bash
curl http://localhost/app/dashboard -I
```

Očekávaný výstup: `HTTP/1.1 200` (HTML stránka — SPA se hydratuje v prohlížeči)

- [ ] **Krok 3: Ověřit auth redirect**

```bash
curl http://localhost/accounts/login/ -I
```

Očekávaný výstup: `HTTP/1.1 200` (Nuxt servuje SPA, Vue Router renderuje AuthFlowView)

- [ ] **Krok 4: Spustit frontend testy**

```bash
cd frontend
pnpm test
```

Očekávaný výstup: všechny testy zelené.

- [ ] **Krok 5: Ověřit Django admin**

```bash
curl http://localhost/admin/ -I
```

Očekávaný výstup: `HTTP/1.1 302` (redirect na /admin/login/)

- [ ] **Krok 6: Závěrečný commit**

```bash
git add .
git commit -m "feat: Nuxt migration complete — SSR public pages, SPA authenticated routes, Django as API only"
```
