# Favicon + dynamické titulky stránek

**Datum:** 2026-05-08  
**Větev:** `feat/favicon-page-titles`

## Cíl

Přidat favicon (ikona v záložce prohlížeče) a dynamické titulky záložek podle aktuální stránky a jazyka aplikace.

## Favicon

- Soubor: `frontend/public/brand/eb-mark.svg` (už existuje)
- Přidán do `nuxt.config.ts` → `app.head.link`:
  ```js
  { rel: 'icon', type: 'image/svg+xml', href: '/brand/eb-mark.svg' }
  ```
- SVG favicon nativně podporován všemi moderními prohlížeči, žádná konverze na `.ico` není potřeba.

## Dynamické titulky

### Globální šablona (`nuxt.config.ts`)

```js
app: {
  head: {
    titleTemplate: '%s | EnduroBuddy',
    title: 'EnduroBuddy',  // fallback
  }
}
```

### Přístup: per-page `useHead`

Každá stránka volá `useHead({ title: t('page.xxx') })`. Titulek sleduje aktuální jazyk aplikace přes `@nuxtjs/i18n` composable `useI18n`.

### I18n klíče

Přidány do `frontend/i18n/locales/cs.json` a `en.json` pod sekci `page`:

| Klíč | cs | en |
|---|---|---|
| `page.about` | O aplikaci | About |
| `page.terms` | Podmínky použití | Terms of Use |
| `page.privacy` | Ochrana soukromí | Privacy Policy |
| `page.dashboard` | Přehled tréninku | Training Dashboard |
| `page.completeProfile` | Dokončení profilu | Complete Profile |
| `page.coachPlans` | Plány tréninků | Training Plans |
| `page.invite` | Pozvánka | Invitation |
| `page.login` | Přihlášení | Log in |
| `page.signup` | Registrace | Sign up |
| `page.profileSetup` | Nastavení profilu | Profile Setup |

### Stránky a jejich titulky

| Soubor | Titulek |
|---|---|
| `pages/index.vue` | `"EnduroBuddy"` (přepisuje template, jen brand name) |
| `pages/about.vue` | `t('page.about')` |
| `pages/terms.vue` | `t('page.terms')` |
| `pages/privacy.vue` | `t('page.privacy')` |
| `pages/app/dashboard.vue` | `t('page.dashboard')` |
| `pages/app/profile/complete.vue` | `t('page.completeProfile')` |
| `pages/coach/plans.vue` | `t('page.coachPlans')` |
| `pages/coach/invite/[token].vue` | `t('page.invite')` |
| `pages/accounts/[...slug].vue` | Computed podle `screenMap` slugu — `login → page.login`, `signup → page.signup`, `profile-setup → page.profileSetup`, ostatní → fallback `"EnduroBuddy"` |

Redirect stránky (`app/index.vue`, `coach/index.vue`) nemají titulek — přesměrovávají okamžitě.

## Soubory ke změně

- `frontend/nuxt.config.ts` — favicon + titleTemplate
- `frontend/i18n/locales/cs.json` — přidat `page.*` klíče
- `frontend/i18n/locales/en.json` — přidat `page.*` klíče
- `frontend/pages/index.vue` — `useHead({ title: 'EnduroBuddy' })`
- `frontend/pages/about.vue` — `useHead`
- `frontend/pages/terms.vue` — `useHead`
- `frontend/pages/privacy.vue` — `useHead`
- `frontend/pages/app/dashboard.vue` — `useHead`
- `frontend/pages/app/profile/complete.vue` — `useHead`
- `frontend/pages/coach/plans.vue` — `useHead`
- `frontend/pages/coach/invite/[token].vue` — `useHead`
- `frontend/pages/accounts/[...slug].vue` — computed titulek podle slugu

## Testování

- `npm test` musí projít beze změn (useHead je deklarativní, nepotřebuje nové testy)
- Ruční kontrola: otevřít každou stránku a ověřit titulek záložky v cs i en
