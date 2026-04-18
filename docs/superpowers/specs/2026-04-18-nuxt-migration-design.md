# Nuxt Migration Design — Eliminace Django templates

**Datum:** 2026-04-18
**Větev:** `feat/nuxt-migration`
**Cíl:** Nahradit veškeré Django HTML templates Vue/Nuxt komponenty a přejít na architektuру Nuxt (Node.js) + Django (čisté REST API).

---

## Kontext a motivace

Projekt aktuálně provozuje dvě paralelní frontendové vrstvy:
- **Vite + Vue 3 SPA** — přihlášená část (`/app/*`, `/coach/*`)
- **Django templates** — veřejné stránky (`/`, `/about/`, `/terms/`, `/privacy/`), error stránky, legacy dashboard

Cílem je eliminovat Django templates úplně a provozovat jediný frontendový stack. Veřejné stránky vyžadují SSR kvůli SEO, proto volíme Nuxt.js s hybrid renderingem.

---

## Architektura

### Nové rozdělení zodpovědností

| Vrstva | Technologie | Port | Zodpovídá za |
|---|---|---|---|
| Frontend | Nuxt 3 (Node.js) | 3000 | Veškeré HTML stránky — SSR i SPA |
| Backend | Django + DRF | 8000 | REST API (`/api/v1/*`) + Django admin |
| Proxy | Nginx | 80/443 | Routing mezi Nuxt a Django |

### Nginx routing pravidla
```
/api/*      → Django :8000
/admin/*    → Django :8000
/static/*   → Django static files
vše ostatní → Nuxt :3000
```

### Nuxt hybrid rendering (routeRules)
```js
routeRules: {
  '/':          { ssr: true },   // SEO — server-side rendering
  '/about':     { ssr: true },
  '/terms':     { ssr: true },
  '/privacy':   { ssr: true },
  '/app/**':    { ssr: false },  // SPA — přihlášená athlete část
  '/coach/**':  { ssr: false },  // SPA — přihlášená coach část
  '/accounts/**': { ssr: false } // SPA — auth flow (allauth)
}
```

---

## Co se mění

### Nahrazuje se (Django → Nuxt)

| Django template | Nuxt ekvivalent |
|---|---|
| `templates/public/home.html` | `pages/index.vue` (SSR) |
| `templates/public/about.html` | `pages/about.vue` (SSR) |
| `templates/public/terms.html` | `pages/terms.vue` (SSR) |
| `templates/public/privacy.html` | `pages/privacy.vue` (SSR) |
| `templates/public/base_public.html` | `layouts/public.vue` |
| `templates/spa.html` | Nuxt entry (zabudovaný) |
| `templates/dashboard/*.html` | Existující Vue komponenty |
| Error stránky (400/403/404/500) | `error.vue` v Nuxt |
| `dashboard/_planned_km_rules_modal.html` | Nová `PlannedKmRulesModal.vue` komponenta |

### Frontend — migrace Vite → Nuxt

Stávající `frontend/` (Vite + Vue 3) se přepíše na Nuxt 3. Všechny existující komponenty, stores, composables a API klient se migrují. Změny jsou minimální — Nuxt je kompatibilní s Vue 3 ekosystémem.

Klíčové změny:
- `router/index.ts` → `pages/` adresář (Nuxt file-based routing)
- `main.ts` → `plugins/` + `app.vue`
- `axios` klient → `$fetch` / `useFetch` (Nuxt built-in)
- `vue-i18n` nebo vlastní `useI18n` → `@nuxtjs/i18n`
- Pinia stores → beze změny (Nuxt podporuje Pinia nativně přes `@pinia/nuxt`)

### Backend — Django zůstává jen jako API

Odstraní se:
- Views servující HTML (`dashboard/views.py` — SPA entry, public views)
- URL patterns pro HTML stránky
- Všechny templates (kromě `admin/`)
- CSS soubory pro veřejné stránky (`static/css/public-*.css`)

Zůstane:
- `api/` — veškeré DRF endpointy beze změny
- `admin/` — Django admin
- Allauth backend (zpracování POST požadavků pro auth)
- Celý datový model (modely, migrace)

### Docker Compose — přidá se Nuxt service

```yaml
nuxt:
  build: ./frontend
  ports:
    - "3000:3000"
  environment:
    - NUXT_PUBLIC_API_BASE=/api/v1
  depends_on:
    - backend
```

Nginx service dostane nová routing pravidla.

---

## Nové stránky (Nuxt SSR)

### Landing page (`pages/index.vue`)
Přepis `public/home.html` do Vue. Zachovává stávající design (design tokeny, sekce Hero/Features/Steps/Audience/CTA). Obsah je bilingvní přes `@nuxtjs/i18n`.

### About (`pages/about.vue`)
Přepis `public/about.html`.

### Terms a Privacy (`pages/terms.vue`, `pages/privacy.vue`)
Přepis právních stránek.

### Layout (`layouts/public.vue`)
Ekvivalent `base_public.html` — topbar, footer, language switcher. Sdílený pro všechny veřejné stránky.

### Error stránka (`error.vue`)
Unifikovaná error stránka pro 404, 500 a ostatní chyby. Zobrazuje kód chyby a odkaz zpět.

### Help modál — km pravidla
Nová komponenta `PlannedKmRulesModal.vue` — standalone modál s pravidly zápisu tréninkové notace. Integrovat do `PlannedRow.vue` jako help ikonka.

---

## Git workflow pro tuto migraci

```
main (produkce)
  ├── backup/pre-nuxt-20260418   ← snapshot stavu před migrací, NEMĚNIT
  └── feat/nuxt-migration        ← veškerá práce probíhá zde
        ↓ (po dokončení)
      merge → main
```

- Veškerá implementace probíhá na větvi `feat/nuxt-migration`
- Větev `backup/pre-nuxt-20260418` slouží jako záchranná síť — odráží stav `main` před migrací
- Po dokončení a otestování se `feat/nuxt-migration` mergne do `main`

---

## Pořadí implementace (fáze)

1. **Nuxt setup** — inicializace Nuxt 3 projektu, konfigurace hybrid renderingu, Docker service
2. **Migrace existujících Vue komponent** — přesun stores, composables, components, API klienta
3. **Veřejné stránky** — landing, about, terms, privacy + public layout
4. **Error stránky** — `error.vue`
5. **Help modál** — `PlannedKmRulesModal.vue`
6. **Cleanup Django** — odstranění templates, public views, URL patterns
7. **Nginx update** — nová routing pravidla
8. **Testování a QA** — ověřit SSR, SEO meta tagy, SPA navigaci, auth flow

---

## Úspěšný výsledek

- Django neobsluhuje žádné HTML stránky (kromě `/admin/`)
- Veřejné stránky mají plné SSR — `curl endurobuddy.com/` vrátí kompletní HTML
- Přihlášená část funguje jako SPA (žádná regrese)
- Auth flow (allauth) funguje beze změny
- Jeden frontendový stack, žádné Django templates
