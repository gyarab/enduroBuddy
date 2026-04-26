# Spec: Multi-domain architektura (endurobuddy.cz + app.endurobuddy.cz)

**Datum:** 2026-04-26  
**Status:** Připraveno k implementaci

---

## Cíl

Rozdělit aplikaci na dvě domény:

| Doména | Obsah |
|--------|-------|
| `endurobuddy.cz` | Veřejné stránky (/, /about, /terms, /privacy) + auth flow (/accounts/*) |
| `app.endurobuddy.cz` | Přihlášená část: /app/dashboard (sportovec), /coach/plans (trenér) |
| `www.endurobuddy.cz` | 301 redirect na `endurobuddy.cz` |

Přihlášený uživatel na `endurobuddy.cz` je automaticky přesměrován na `app.endurobuddy.cz/app/dashboard` nebo `app.endurobuddy.cz/coach/plans`.

---

## Motivace

- Jasná URL sémantika: veřejný web vs. aplikace
- SEO: `endurobuddy.cz` je čistá landing page bez app route noise
- Budoucí základ pro potenciální multi-tenant nebo white-label přístup

---

## Architektura

### Jeden Nuxt server, dvě domény

Jedna Nuxt instance obsluhuje obě domény. Nuxt dostane `NUXT_PUBLIC_APP_HOST=app.endurobuddy.cz` a v global middleware rozlišuje, na které doméně běží.

Alternativa (dva Nuxt kontejnery) zamítnuta — zbytečná složitost a spotřeba paměti.

### API na obou doménách

Nginx/Traefik routuje `/api/`, `/admin/`, `/static/`, `/i18n/`, `/accounts/google/` na Django **z obou domén**. Nuxt volá `/api/v1` relativně — funguje z obou.

### Sdílené session cookies

Django session a CSRF cookie musí být nastaveny s `domain=.endurobuddy.cz` (leading dot = platí pro všechny subdomény). Bez toho by uživatel přihlášený na `endurobuddy.cz` neměl session na `app.endurobuddy.cz`.

### Redirect po přihlášení

Po úspěšném přihlášení `_default_route_for_user()` v backendu vrátí absolutní URL (např. `https://app.endurobuddy.cz/app/dashboard`) pokud je nastaven `DJANGO_APP_HOST`. `AuthFlowView.vue` používá `window.location.href`, takže cross-domain redirect funguje bez změn.

Pro Google OAuth: `LOGIN_REDIRECT_URL` se dynamicky nastaví na `https://app.endurobuddy.cz/app/` pokud je `DJANGO_APP_HOST` nastaven.

---

## Dev vs. Prod

### Dev (dev.sh + nativní Django/Nuxt)

- `NUXT_PUBLIC_APP_HOST` není nastaven → middleware je no-op
- Vše běží na `localhost:8000` (Django) + `localhost:3000` (Nuxt)
- Žádné cross-domain redirecty, žádné cookie domain
- Chování v deva = stejné jako dnes

### Dev Docker (docker-compose.yml)

- Nginx obsluhuje `localhost:80` s catch-all server blokem
- Přidán `www` redirect server block (pro testování s hosts file)
- Nuxt kontejner dostane `NUXT_PUBLIC_APP_HOST` pokud chceme testovat domény lokálně

### Prod (docker-compose.prod.yml + Traefik)

- `TRAEFIK_HOST=endurobuddy.cz`, `TRAEFIK_APP_HOST=app.endurobuddy.cz`
- Traefik routery pro obě domény (Django backend routes + Nuxt catch-all)
- Traefik middleware pro `www` → 301 redirect
- `.env` obsahuje `SESSION_COOKIE_DOMAIN=.endurobuddy.cz`, `CSRF_COOKIE_DOMAIN=.endurobuddy.cz`, `DJANGO_APP_HOST=app.endurobuddy.cz`

---

## Bezpečnostní poznámky

- `SESSION_COOKIE_DOMAIN=.endurobuddy.cz` rozšiřuje scope cookies — riziko je minimální (obě domény pod naší kontrolou), ale je potřeba dát pozor při přidávání dalších subdomén v budoucnu
- `CSRF_COOKIE_DOMAIN` musí být nastaveno shodně, jinak CSRF validace selže pro cross-subdomain requesty
- `DJANGO_CSRF_TRUSTED_ORIGINS` musí obsahovat obě domény: `https://endurobuddy.cz,https://app.endurobuddy.cz`
- `DJANGO_ALLOWED_HOSTS` musí obsahovat obě domény

---

## Dotčené soubory

### Backend
- `backend/config/settings.py` — cookie domain, APP_HOST, LOGIN_REDIRECT_URL
- `backend/api/views/auth.py` — `_default_route_for_user()` absolute URL
- `backend/api/views/profile.py` — `_default_app_route_for_role()` absolute URL
- `.env.example` — nové proměnné

### Frontend
- `frontend/nuxt.config.ts` — `appHost` v runtimeConfig
- `frontend/middleware/domains.global.ts` — nový soubor, cross-domain redirect logika

### Infrastructure
- `docker-compose.prod.yml` — Traefik routery pro `app.` + `www` redirect
- `docker-compose.yml` — `www` redirect server block v nginx konfiguraci (volitelné)
- `nginx/nginx.conf` — `www` redirect server block

---

## Scénáře chování

| Uživatel | Stav | Cíl | Výsledek |
|----------|------|-----|---------|
| Nepřihlášený | — | `endurobuddy.cz` | Zobrazí landing page |
| Nepřihlášený | — | `app.endurobuddy.cz/app/dashboard` | Nuxt middleware: redirect na `endurobuddy.cz/accounts/login/` |
| Přihlášený sportovec | — | `endurobuddy.cz` | Nuxt middleware: redirect na `app.endurobuddy.cz/app/dashboard` |
| Přihlášený trenér | — | `endurobuddy.cz` | Nuxt middleware: redirect na `app.endurobuddy.cz/coach/plans` |
| Kdokoli | — | `www.endurobuddy.cz` | Traefik: 301 → `endurobuddy.cz` |
| Login (email) | úspěch | — | Backend vrátí `https://app.endurobuddy.cz/app/dashboard`, `window.location.href` naviguje |
| Login (Google OAuth) | úspěch | — | Django `LOGIN_REDIRECT_URL` = `https://app.endurobuddy.cz/app/`, Traefik → Nuxt → `/app/dashboard` |
