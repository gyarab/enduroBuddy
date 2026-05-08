# Favicon + dynamické titulky stránek — implementační plán

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Přidat SVG favicon a dynamické titulky záložek prohlížeče podle aktuální stránky a jazyka aplikace.

**Architecture:** Favicon přidán do `nuxt.config.ts` app.head.link. Globální `titleTemplate` nastavena v nuxt.config.ts. Každá stránka volá `useHead` s computed i18n titulem. Auth slug stránka mapuje screen → i18n klíč.

**Tech Stack:** Nuxt 3, @nuxtjs/i18n (auto-importuje `useI18n`), `useHead` (Nuxt auto-import)

---

## Task 0: Vytvoření feature větve

- [ ] **Krok 1: Vytvořit větev a pushnout na remote**

  ```bash
  git checkout -b feat/favicon-page-titles
  git push -u origin feat/favicon-page-titles
  ```

---

## Soubory

| Soubor | Změna |
|---|---|
| `frontend/nuxt.config.ts` | + favicon do `app.head.link`, + `titleTemplate` a fallback `title` do `app.head` |
| `frontend/i18n/locales/cs.json` | + sekce `"page"` s i18n klíči |
| `frontend/i18n/locales/en.json` | + sekce `"page"` s i18n klíči |
| `frontend/pages/index.vue` | + `useHead({ titleTemplate: 'EnduroBuddy' })` |
| `frontend/pages/about.vue` | + `useHead({ title: computed(() => t('page.about')) })` |
| `frontend/pages/terms.vue` | + `useHead({ title: computed(() => t('page.terms')) })` |
| `frontend/pages/privacy.vue` | + `useHead({ title: computed(() => t('page.privacy')) })` |
| `frontend/pages/dashboard.vue` | + `useI18n` + `useHead` s `page.dashboard` |
| `frontend/pages/app/profile/complete.vue` | + `useI18n` + `useHead` s `page.completeProfile` |
| `frontend/pages/coach/plans.vue` | + `useI18n` + `useHead` s `page.coachPlans` |
| `frontend/pages/coach/invite/[token].vue` | + `useI18n` + `useHead` s `page.invite` |
| `frontend/pages/accounts/profile-setup.vue` | + `useI18n` + `useHead` s `page.profileSetup` |
| `frontend/pages/accounts/[...slug].vue` | + `useI18n` + `useHead` s computed mapou screen → i18n klíč |

---

## Task 1: nuxt.config.ts — favicon + titleTemplate

**Files:**
- Modify: `frontend/nuxt.config.ts`

- [ ] **Krok 1: Přidat favicon a titleTemplate do nuxt.config.ts**

  Uprav sekci `app` v `frontend/nuxt.config.ts`. Přidej `titleTemplate`, fallback `title` a favicon jako první položku v `link` poli:

  ```typescript
  app: {
    head: {
      titleTemplate: '%s | EnduroBuddy',
      title: 'EnduroBuddy',
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/brand/eb-mark.svg' },
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Nunito:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap&subset=latin,latin-ext",
        },
      ],
    },
  },
  ```

- [ ] **Krok 2: Ověřit TypeScript a testy**

  ```bash
  cd frontend && npm test
  ```
  Očekávaný výsledek: všechny testy zelené (počet se nemění).

- [ ] **Krok 3: Commit**

  ```bash
  git add frontend/nuxt.config.ts
  git commit -m "feat: add SVG favicon and global titleTemplate to nuxt.config"
  ```

---

## Task 2: I18n klíče pro titulky stránek

**Files:**
- Modify: `frontend/i18n/locales/cs.json`
- Modify: `frontend/i18n/locales/en.json`

- [ ] **Krok 1: Přidat sekci `page` do cs.json**

  Na konec `frontend/i18n/locales/cs.json` (před uzavírací `}`) přidej:

  ```json
  "page": {
    "about": "O aplikaci",
    "terms": "Podmínky použití",
    "privacy": "Ochrana soukromí",
    "dashboard": "Přehled tréninku",
    "completeProfile": "Dokončení profilu",
    "coachPlans": "Plány tréninků",
    "invite": "Pozvánka",
    "profileSetup": "Nastavení profilu",
    "login": "Přihlášení",
    "signup": "Registrace",
    "passwordReset": "Zapomenuté heslo"
  }
  ```

- [ ] **Krok 2: Přidat sekci `page` do en.json**

  Na konec `frontend/i18n/locales/en.json` (před uzavírací `}`) přidej:

  ```json
  "page": {
    "about": "About",
    "terms": "Terms of Use",
    "privacy": "Privacy Policy",
    "dashboard": "Training Dashboard",
    "completeProfile": "Complete Profile",
    "coachPlans": "Training Plans",
    "invite": "Invitation",
    "profileSetup": "Profile Setup",
    "login": "Log in",
    "signup": "Sign up",
    "passwordReset": "Forgot Password"
  }
  ```

- [ ] **Krok 3: Ověřit testy**

  ```bash
  cd frontend && npm test
  ```
  Očekávaný výsledek: všechny testy zelené.

- [ ] **Krok 4: Commit**

  ```bash
  git add frontend/i18n/locales/cs.json frontend/i18n/locales/en.json
  git commit -m "feat: add page.* i18n keys for page titles (cs + en)"
  ```

---

## Task 3: Titulky veřejných stránek (index, about, terms, privacy)

**Files:**
- Modify: `frontend/pages/index.vue`
- Modify: `frontend/pages/about.vue`
- Modify: `frontend/pages/terms.vue`
- Modify: `frontend/pages/privacy.vue`

`useHead` a `useI18n` jsou v Nuxt 3 auto-importovány — žádné explicitní `import` není potřeba.

- [ ] **Krok 1: index.vue — titulek bez suffixu**

  Landing page má být jen `"EnduroBuddy"` (bez ` | EnduroBuddy`). Přepiš globální `titleTemplate` pro tuto stránku.

  Do `<script setup lang="ts">` v `frontend/pages/index.vue` přidej na konec bloku (před `</script>`):

  ```typescript
  useHead({ titleTemplate: 'EnduroBuddy' })
  ```

- [ ] **Krok 2: about.vue**

  Do `<script setup lang="ts">` v `frontend/pages/about.vue` přidej na konec bloku (za existující `const { t } = useI18n()`):

  ```typescript
  useHead({ title: computed(() => t('page.about')) })
  ```

  Pokud `useI18n()` v souboru ještě není, přidej ho:
  ```typescript
  const { t } = useI18n()
  useHead({ title: computed(() => t('page.about')) })
  ```

- [ ] **Krok 3: terms.vue**

  Do `<script setup lang="ts">` v `frontend/pages/terms.vue` přidej:

  ```typescript
  const { t } = useI18n()
  useHead({ title: computed(() => t('page.terms')) })
  ```

  Pokud `useI18n()` již existuje, přidej jen `useHead` řádek.

- [ ] **Krok 4: privacy.vue**

  Do `<script setup lang="ts">` v `frontend/pages/privacy.vue` přidej:

  ```typescript
  const { t } = useI18n()
  useHead({ title: computed(() => t('page.privacy')) })
  ```

  Pokud `useI18n()` již existuje, přidej jen `useHead` řádek.

- [ ] **Krok 5: Ověřit testy**

  ```bash
  cd frontend && npm test
  ```
  Očekávaný výsledek: všechny testy zelené.

- [ ] **Krok 6: Commit**

  ```bash
  git add frontend/pages/index.vue frontend/pages/about.vue frontend/pages/terms.vue frontend/pages/privacy.vue
  git commit -m "feat: add page titles to public pages (index, about, terms, privacy)"
  ```

---

## Task 4: Titulky aplikačních stránek (dashboard, profile, coach)

**Files:**
- Modify: `frontend/pages/dashboard.vue`
- Modify: `frontend/pages/app/profile/complete.vue`
- Modify: `frontend/pages/coach/plans.vue`
- Modify: `frontend/pages/coach/invite/[token].vue`
- Modify: `frontend/pages/accounts/profile-setup.vue`

Tyto stránky jsou minimální (jen delegují na komponentu) a zatím nepoužívají `useI18n`. Přidej `useI18n` + `useHead` do každé.

- [ ] **Krok 1: dashboard.vue**

  Nahraď obsah `frontend/pages/dashboard.vue`:

  ```vue
  <template>
    <AthleteView />
  </template>

  <script setup lang="ts">
  definePageMeta({ layout: "default" })

  const { t } = useI18n()
  useHead({ title: computed(() => t('page.dashboard')) })
  </script>
  ```

- [ ] **Krok 2: app/profile/complete.vue**

  Nahraď obsah `frontend/pages/app/profile/complete.vue`:

  ```vue
  <template>
    <CompleteProfileView />
  </template>

  <script setup lang="ts">
  definePageMeta({ layout: "default" })

  const { t } = useI18n()
  useHead({ title: computed(() => t('page.completeProfile')) })
  </script>
  ```

- [ ] **Krok 3: coach/plans.vue**

  Nahraď obsah `frontend/pages/coach/plans.vue`:

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

- [ ] **Krok 4: coach/invite/[token].vue**

  Nahraď obsah `frontend/pages/coach/invite/[token].vue`:

  ```vue
  <template>
    <InviteView />
  </template>

  <script setup lang="ts">
  definePageMeta({ layout: "default" })

  const { t } = useI18n()
  useHead({ title: computed(() => t('page.invite')) })
  </script>
  ```

- [ ] **Krok 5: accounts/profile-setup.vue**

  Do `<script setup lang="ts">` v `frontend/pages/accounts/profile-setup.vue` přidej za `definePageMeta(...)`:

  ```typescript
  const { t } = useI18n()
  useHead({ title: computed(() => t('page.profileSetup')) })
  ```

- [ ] **Krok 6: Ověřit testy**

  ```bash
  cd frontend && npm test
  ```
  Očekávaný výsledek: všechny testy zelené.

- [ ] **Krok 7: Commit**

  ```bash
  git add frontend/pages/dashboard.vue frontend/pages/app/profile/complete.vue frontend/pages/coach/plans.vue frontend/pages/coach/invite/[token].vue frontend/pages/accounts/profile-setup.vue
  git commit -m "feat: add page titles to app pages (dashboard, coach, profile)"
  ```

---

## Task 5: Dynamický titulek pro auth slug stránku

**Files:**
- Modify: `frontend/pages/accounts/[...slug].vue`

Stránka `[...slug].vue` obsluhuje více auth obrazovek. Titulek se mění podle hodnoty `screen` computed. Pro neznámé screeny (fallback `"login"`) se zobrazí titulek přihlášení.

- [ ] **Krok 1: Přidat useI18n + useHead do [...]slug].vue**

  Do `<script setup lang="ts">` v `frontend/pages/accounts/[...slug].vue` přidej za `const screen = computed(...)`:

  ```typescript
  const { t } = useI18n()

  const screenTitleKeys: Partial<Record<string, string>> = {
    'login': 'page.login',
    'signup': 'page.signup',
    'password-reset': 'page.passwordReset',
  }

  useHead(computed(() => {
    const key = screenTitleKeys[screen.value]
    return key ? { title: t(key) } : { titleTemplate: 'EnduroBuddy' }
  }))
  ```

  Celý výsledný `<script setup>` blok bude vypadat takto:

  ```vue
  <script setup lang="ts">
  definePageMeta({ layout: "auth" })

  const route = useRoute()

  const slug = computed(() => {
    const parts = route.params.slug as string[]
    const filtered = Array.isArray(parts) ? parts.filter(Boolean) : [String(parts)].filter(Boolean)
    return filtered.join("/")
  })

  const screenMap: Record<string, string> = {
    "login": "login",
    "signup": "signup",
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

  const screen = computed(() => {
    const path = slug.value
    if (path.startsWith("confirm-email/") && path.length > "confirm-email/".length) {
      return "email-confirm-key"
    }
    if (path.startsWith("password/reset/key/") && path !== "password/reset/key/done") {
      return "password-reset-key"
    }
    return screenMap[path] ?? "login"
  })

  const { t } = useI18n()

  const screenTitleKeys: Partial<Record<string, string>> = {
    'login': 'page.login',
    'signup': 'page.signup',
    'password-reset': 'page.passwordReset',
  }

  useHead(computed(() => {
    const key = screenTitleKeys[screen.value]
    return key ? { title: t(key) } : { titleTemplate: 'EnduroBuddy' }
  }))
  </script>
  ```

- [ ] **Krok 2: Ověřit testy**

  ```bash
  cd frontend && npm test
  ```
  Očekávaný výsledek: všechny testy zelené.

- [ ] **Krok 3: Commit**

  ```bash
  git add frontend/pages/accounts/[...slug].vue
  git commit -m "feat: add dynamic page title to auth slug page based on screen"
  ```

---

## Task 6: Aktualizace CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Krok 1: Přidat záznam do sekce "Aktivní plány a změny" v CLAUDE.md**

  Přidej nový záznam na začátek sekce (za nadpis `## Aktivní plány a změny`):

  ```markdown
  ### 2026-05-08 — Favicon + dynamické titulky záložek ✅ KOMPLETNÍ

  **Spec:** `docs/superpowers/specs/2026-05-08-favicon-page-titles.md`
  **Plán:** `docs/superpowers/plans/2026-05-08-favicon-page-titles.md`

  - `nuxt.config.ts`: SVG favicon (`/brand/eb-mark.svg`), globální `titleTemplate: '%s | EnduroBuddy'`
  - `i18n/locales/cs.json` + `en.json`: přidána sekce `page.*` (11 klíčů)
  - Všechny stránky: `useHead` s `computed(() => t('page.xxx'))` — reaktivní na změnu jazyka
  - `index.vue`: `titleTemplate: 'EnduroBuddy'` (bez suffixu)
  - `accounts/[...slug].vue`: computed mapa screen → i18n klíč (login, signup, passwordReset)
  ```

- [ ] **Krok 2: Commit**

  ```bash
  git add CLAUDE.md
  git commit -m "docs: update CLAUDE.md with favicon and page titles implementation"
  ```
