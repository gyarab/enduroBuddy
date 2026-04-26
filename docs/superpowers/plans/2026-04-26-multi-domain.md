# Implementační plán: Multi-domain architektura

**Spec:** `docs/superpowers/specs/2026-04-26-multi-domain.md`  
**Datum:** 2026-04-26  
**Větev:** `main`

---

## Přehled změn

6 tasků, žádný není blokující pro druhý (lze dělat postupně).  
Dev workflow (`dev.sh` + nativní Django/Nuxt) se nemění — nové proměnné mají prázdné výchozí hodnoty.

---

## Task 1 — Django settings: cookie domain + APP_HOST

**Soubor:** `backend/config/settings.py`

Přidat za `SESSION_COOKIE_NAME` / `CSRF_COOKIE_NAME`:

```python
# Subdomain cookie sharing — empty string = same domain as request (dev default)
_cookie_domain = os.environ.get("SESSION_COOKIE_DOMAIN", "")
if _cookie_domain:
    SESSION_COOKIE_DOMAIN = _cookie_domain

_csrf_cookie_domain = os.environ.get("CSRF_COOKIE_DOMAIN", "")
if _csrf_cookie_domain:
    CSRF_COOKIE_DOMAIN = _csrf_cookie_domain

# App subdomain hostname (e.g. "app.endurobuddy.cz") — empty in dev
APP_HOST = os.environ.get("DJANGO_APP_HOST", "")
```

Aktualizovat `LOGIN_REDIRECT_URL`:

```python
_app_host = os.environ.get("DJANGO_APP_HOST", "")
LOGIN_REDIRECT_URL = f"https://{_app_host}/app/" if _app_host else "/app/"
```

**Poznámka:** Nepřiřazujeme `SESSION_COOKIE_DOMAIN = ""` — Django interní logika pak použije prázdný string jako doménu místo žádné, což je špatně. Proto podmíněné přiřazení jen pokud hodnota existuje.

---

## Task 2 — Django views: absolutní URL po přihlášení

**Soubory:** `backend/api/views/auth.py`, `backend/api/views/profile.py`

### auth.py

Přidat helper funkci po importech:

```python
def _app_url(path: str) -> str:
    """Returns absolute URL for the app domain if APP_HOST is configured."""
    app_host = getattr(settings, "APP_HOST", "")
    return f"https://{app_host}{path}" if app_host else path
```

Upravit `_default_route_for_user()`:

```python
def _default_route_for_user(user) -> str:
    # ... stávající logika pro has_incomplete_google_profile ...
    if has_incomplete_google_profile:
        return _app_url("/app/profile/complete")
    return _app_url("/coach/plans" if role == Role.COACH else "/app/dashboard")
```

Upravit `auth_me()` řádek 143:

```python
default_app_route = _app_url("/coach/plans" if role == Role.COACH else "/app/dashboard")
```

### profile.py

Přidat stejný helper (nebo importovat ze sdíleného místa — ale duplikace je OK pro dva soubory):

```python
def _app_url(path: str) -> str:
    from django.conf import settings
    app_host = getattr(settings, "APP_HOST", "")
    return f"https://{app_host}{path}" if app_host else path
```

Upravit `_default_app_route_for_role()`:

```python
def _default_app_route_for_role(role: str) -> str:
    path = "/coach/plans" if role == Role.COACH else "/app/dashboard"
    return _app_url(path)
```

**Dopad:** `ProfileSettingsModal.vue` zobrazuje `default_app_route` jako `<a :href="...">` — absolutní URL funguje beze změny.

---

## Task 3 — Nuxt: runtimeConfig + global middleware

### 3a) nuxt.config.ts

Do `runtimeConfig.public` přidat:

```ts
runtimeConfig: {
  public: {
    apiBase: "/api/v1",
    appHost: "",  // override via NUXT_PUBLIC_APP_HOST env var
  },
},
```

### 3b) frontend/middleware/domains.global.ts (nový soubor)

```ts
export default defineNuxtRouteMiddleware(async (to) => {
  const config = useRuntimeConfig()
  const appHost = config.public.appHost as string
  if (!appHost) return  // dev: no domain split

  const currentHost = import.meta.server
    ? (useRequestHeaders()["host"] ?? "").split(":")[0]
    : window.location.hostname

  const isAppDomain = currentHost === appHost
  const isPublicDomain = !isAppDomain

  const APP_PATHS = ["/app/", "/coach/"]
  const isAppPath = APP_PATHS.some((p) => to.path.startsWith(p))

  // Public domain + app path → přesměrovat na app doménu
  if (isPublicDomain && isAppPath) {
    return navigateTo(`https://${appHost}${to.fullPath}`, { external: true })
  }

  // Auth check: pouze client-side (vyhnout se SSR waterfall)
  if (import.meta.client) {
    const auth = useAuthStore()
    if (!auth.hasBootstrapped) {
      await auth.initialize()
    }

    // Veřejná doména + přihlášený + public stránka → přesměrovat na app
    const PUBLIC_PAGES = ["/", "/about", "/terms", "/privacy"]
    if (isPublicDomain && PUBLIC_PAGES.includes(to.path) && auth.isAuthenticated) {
      const target = auth.isCoach ? "/coach/plans" : "/app/dashboard"
      return navigateTo(`https://${appHost}${target}`, { external: true })
    }

    // App doména + nepřihlášený + app path → přesměrovat na login
    if (isAppDomain && isAppPath && !auth.isAuthenticated) {
      const publicHost = appHost.replace(/^app\./, "")
      return navigateTo(`https://${publicHost}/accounts/login/`, { external: true })
    }
  }
})
```

**Poznámky:**
- `import.meta.server` blok: pouze path-based redirect (bez API callu)
- `import.meta.client` blok: auth check s lazy bootstrap
- Derivace public hosta: `app.endurobuddy.cz` → `endurobuddy.cz` (strip `app.` prefix)
- Accounts stránky (`/accounts/*`) fungují na obou doménách — záměrně bez redirectu

---

## Task 4 — docker-compose.prod.yml: Traefik pro app. a www

### Nová env var

Do `.env.example` přidat: `TRAEFIK_APP_HOST=app.endurobuddy.cz`

### web service — přidat app subdoménu do Django route pravidel

Stávající `traefik.http.routers.endurobuddy.rule` rozšířit o `Host('${TRAEFIK_APP_HOST}')`:

```yaml
# HTTP routers (pro web service)
- "traefik.http.routers.endurobuddy-http.rule=\
    (Host(`${TRAEFIK_HOST}`) || Host(`${TRAEFIK_APP_HOST}`)) && \
    (PathPrefix(`/api/`) || PathPrefix(`/admin/`) || PathPrefix(`/static/`) || PathPrefix(`/i18n/`) || PathPrefix(`/accounts/google/`))"
- "traefik.http.routers.endurobuddy.rule=\
    (Host(`${TRAEFIK_HOST}`) || Host(`${TRAEFIK_APP_HOST}`)) && \
    (PathPrefix(`/api/`) || PathPrefix(`/admin/`) || PathPrefix(`/static/`) || PathPrefix(`/i18n/`) || PathPrefix(`/accounts/google/`))"
```

### nuxt service — přidat app subdoménu + www redirect

Rozšířit existující Nuxt routery o `app.` host:

```yaml
# HTTP routery pro Nuxt (catch-all pro obě domény)
- "traefik.http.routers.endurobuddy-nuxt-http.rule=Host(`${TRAEFIK_HOST}`) || Host(`${TRAEFIK_APP_HOST}`)"
- "traefik.http.routers.endurobuddy-nuxt.rule=Host(`${TRAEFIK_HOST}`) || Host(`${TRAEFIK_APP_HOST}`)"
```

### www redirect — nové routery v nuxt service

```yaml
# www redirect middleware
- "traefik.http.middlewares.endurobuddy-www-redirect.redirectregex.regex=^https?://www\\.${TRAEFIK_HOST}/(.*)"
- "traefik.http.middlewares.endurobuddy-www-redirect.redirectregex.replacement=https://${TRAEFIK_HOST}/$${1}"
- "traefik.http.middlewares.endurobuddy-www-redirect.redirectregex.permanent=true"

# www HTTP router (před https redirect)
- "traefik.http.routers.endurobuddy-www-http.rule=Host(`www.${TRAEFIK_HOST}`)"
- "traefik.http.routers.endurobuddy-www-http.entrypoints=web"
- "traefik.http.routers.endurobuddy-www-http.priority=30"
- "traefik.http.routers.endurobuddy-www-http.middlewares=endurobuddy-www-redirect"
- "traefik.http.routers.endurobuddy-www-http.service=endurobuddy-nuxt"

# www HTTPS router
- "traefik.http.routers.endurobuddy-www.rule=Host(`www.${TRAEFIK_HOST}`)"
- "traefik.http.routers.endurobuddy-www.entrypoints=websecure"
- "traefik.http.routers.endurobuddy-www.tls=true"
- "traefik.http.routers.endurobuddy-www.tls.certresolver=${TRAEFIK_CERTRESOLVER}"
- "traefik.http.routers.endurobuddy-www.priority=30"
- "traefik.http.routers.endurobuddy-www.middlewares=endurobuddy-www-redirect"
- "traefik.http.routers.endurobuddy-www.service=endurobuddy-nuxt"
```

**Poznámka k Traefiku a `$`:**  
V docker-compose YAML je `$` v Traefik regexech potřeba escapovat jako `$$`. Proto `$${1}` v replacement.

### nuxt service — přidat env proměnnou

```yaml
environment:
  NUXT_PUBLIC_API_BASE: /api/v1
  NUXT_PUBLIC_APP_HOST: ${TRAEFIK_APP_HOST}
```

---

## Task 5 — nginx/nginx.conf: www redirect (pro dev Docker stack)

Přidat před stávající `server` blok:

```nginx
# www → apex redirect (dev Docker / staging)
server {
    listen 80;
    server_name www.endurobuddy.cz www.localhost;
    return 301 $scheme://endurobuddy.cz$request_uri;
}
```

Stávající `server_name _;` zůstává jako catch-all pro všechny ostatní hostnames.

---

## Task 6 — .env.example: nové proměnné

Přidat za stávající `TRAEFIK_HOST` a `TRAEFIK_CERTRESOLVER`:

```env
TRAEFIK_APP_HOST=app.endurobuddy.cz

# Session a CSRF cookies platné pro všechny subdomény (leading dot je záměrný)
SESSION_COOKIE_DOMAIN=.endurobuddy.cz
CSRF_COOKIE_DOMAIN=.endurobuddy.cz

# App subdoména pro backend redirecty po přihlášení
DJANGO_APP_HOST=app.endurobuddy.cz

# Aktualizovat ALLOWED_HOSTS aby obsahoval obě domény
DJANGO_ALLOWED_HOSTS=endurobuddy.cz,app.endurobuddy.cz,www.endurobuddy.cz

# Aktualizovat CORS a CSRF trusted origins
DJANGO_CSRF_TRUSTED_ORIGINS=https://endurobuddy.cz,https://app.endurobuddy.cz,https://www.endurobuddy.cz
DJANGO_CORS_ALLOWED_ORIGINS=https://endurobuddy.cz,https://app.endurobuddy.cz
```

---

## Testovací checklist

- [ ] Dev (dev.sh): aplikace funguje beze změn na localhost, žádné redirecty
- [ ] Dev Docker: `docker compose up` startuje bez chyb, nginx reaguje na :80
- [ ] Backend unit testy: `python manage.py test` zelené
- [ ] Frontend testy: `pnpm test` zelené
- [ ] Prod: `www.endurobuddy.cz` → 301 na `https://endurobuddy.cz`
- [ ] Prod: nepřihlášený na `endurobuddy.cz` → landing page
- [ ] Prod: přihlášený sportovec na `endurobuddy.cz` → redirect na `app.endurobuddy.cz/app/dashboard`
- [ ] Prod: přihlášený trenér na `endurobuddy.cz` → redirect na `app.endurobuddy.cz/coach/plans`
- [ ] Prod: login emailem → po přihlášení redirect na `app.endurobuddy.cz/app/dashboard`
- [ ] Prod: login přes Google → po OAuth redirect na `app.endurobuddy.cz/app/`
- [ ] Prod: logout → přesměrování na `/accounts/login/`
- [ ] Prod: session cookie dostupná na obou doménách (devtools → Application → Cookies)
