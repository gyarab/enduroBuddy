# Debug Spec: Production Routing + Auth Bugs

**Datum:** 2026-05-06  
**Branch:** `feat/registration-flow` (auth fix) + `main` (docker fix)  
**Priorita:** Kritická — produkce není funkční

---

## Souhrn problémů

Tři souběžné bugy — sdílí jeden root cause cluster (chybějící konfigurace v `docker-compose.yml`):

1. `app.endurobuddy.cz/dashboard` → **404** (Traefik nezná tuto doménu)
2. `endurobuddy.cz/admin/` → **400/404** (ALLOWED_HOSTS pravděpodobně neobsahuje doménu)
3. Dashboard zobrazuje **"EnduroBuddy User"** místo jména (chybí `NUXT_PUBLIC_APP_HOST` v nuxt environment)

---

## Bug 1 — `app.endurobuddy.cz` → 404

### Root cause (potvrzeno)

`docker-compose.yml` nginx service má Traefik label pouze pro hlavní doménu:

```yaml
- "traefik.http.routers.endurobuddy.rule=Host(`endurobuddy.cz`)"
```

Pro `app.endurobuddy.cz` žádný router není. Traefik vrátí 404 přímo — požadavek se nikdy nedostane k nginx ani k Nuxt/Django.

Historický kontext: původně bylo v `docker-compose.prod.yml` (smazán při sloučení do jednoho souboru), ale Traefik routery pro `app.*` se do `docker-compose.yml` nedostaly.

### Potřebný fix

Přidat do nginx service v `docker-compose.yml` Traefik router pro `app.endurobuddy.cz`:

```yaml
# App subdoména — přes nginx stejný stack
- "traefik.http.routers.endurobuddy-app.rule=Host(`app.endurobuddy.cz`)"
- "traefik.http.routers.endurobuddy-app.entrypoints=websecure"
- "traefik.http.routers.endurobuddy-app.tls.certresolver=letsencrypt"
- "traefik.http.services.endurobuddy-app.loadbalancer.server.port=80"
```

Nginx `default_server` blok (`server_name _`) zachytí requesty z obou domén a správně routuje `/api/`, `/admin/`, `/accounts/google/` → Django; `/` → Nuxt.

---

## Bug 2 — `endurobuddy.cz/admin/` → 400/404

### Root cause (pravděpodobný, nutná verifikace na serveru)

nginx.conf i urls.py jsou správné (`path("admin/", admin.site.urls)` na řádku 28). Nginx routuje `/admin/` → Django správně.

Nejpravděpodobnější příčina: **`DJANGO_ALLOWED_HOSTS` neobsahuje `endurobuddy.cz`** v produkčním `.env`. Django vrátí `400 Bad Request` (SuspiciousOperation: DisallowedHost), který se může projevit jako chybová stránka s kódem 400 nebo jako prázdná odpověď — uživatel ji vnímá jako "404".

Druhá možná příčina: nginx container nebyl rebuild po změně konfigurace.

### Verifikace na serveru

```bash
# Zkontrolovat ALLOWED_HOSTS v .env
grep DJANGO_ALLOWED_HOSTS .env

# Zkontrolovat logy Django
docker compose logs web --tail=50 | grep -i "disallowed\|allowed host\|400"

# Zkontrolovat nginx logy
docker compose logs nginx --tail=20
```

### Potřebný fix

Zajistit, aby `DJANGO_ALLOWED_HOSTS` v produkčním `.env` obsahoval obě domény:

```
DJANGO_ALLOWED_HOSTS=endurobuddy.cz,app.endurobuddy.cz,localhost
```

Také `DJANGO_CSRF_TRUSTED_ORIGINS` musí obsahovat obě HTTPS origins pro POST requesty.

---

## Bug 3 — "EnduroBuddy User" místo jména uživatele

### Root cause (potvrzeno)

`docker-compose.yml` nuxt service nemá `NUXT_PUBLIC_APP_HOST`:

```yaml
nuxt:
  environment:
    NUXT_PUBLIC_API_BASE: /api/v1
    # NUXT_PUBLIC_APP_HOST chybí!
```

Řetězec selhání:
1. `NUXT_PUBLIC_APP_HOST` = `""` → `appHost = ""`
2. `domains.global.ts` line 4: `if (!appHost) return` → okamžitý exit
3. Auth check (authenticate user nebo redirect) se nikdy nespustí
4. `authStore.user` zůstane `null` (store není inicializován)
5. `ProfileDropdown`: `authStore.user?.full_name || "EnduroBuddy User"` → `"EnduroBuddy User"`

Vedlejší efekt: přihlášený uživatel na `endurobuddy.cz` (public domain) není přesměrován na `app.endurobuddy.cz` po přihlášení.

**Poznámka:** Nový `auth.global.ts` middleware (z `feat/registration-flow`) opravuje auth ochranu pro dev a single-domain deployment bez závislosti na `appHost`. Ale cross-domain redirect po přihlášení (`endurobuddy.cz` → `app.endurobuddy.cz`) stále závisí na `NUXT_PUBLIC_APP_HOST`.

### Potřebný fix

Přidat `NUXT_PUBLIC_APP_HOST` do nuxt service v `docker-compose.yml`:

```yaml
nuxt:
  environment:
    NUXT_PUBLIC_API_BASE: /api/v1
    NUXT_PUBLIC_APP_HOST: ${TRAEFIK_APP_HOST:-}
```

`.env.example` již obsahuje `TRAEFIK_APP_HOST=app.endurobuddy.cz` — stačí ho přeposlat jako `NUXT_PUBLIC_APP_HOST`.

---

## Implementační plán

Viz `docs/superpowers/plans/2026-05-06-production-routing-auth-bugs.md`

### Shrnutí kroků

1. **`docker-compose.yml`** — přidat Traefik router labels pro `app.endurobuddy.cz` do nginx service
2. **`docker-compose.yml`** — přidat `NUXT_PUBLIC_APP_HOST: ${TRAEFIK_APP_HOST:-}` do nuxt environment
3. **`.env.example`** — zkontrolovat a doplnit `DJANGO_ALLOWED_HOSTS` příklad s oběma doménami
4. **Server** — ověřit/aktualizovat `DJANGO_ALLOWED_HOSTS` v produkčním `.env`
5. **`feat/registration-flow` → `main`** — merge `auth.global.ts` middleware fixu

---

## Rizika a edge cases

- Traefik při přidání nového routeru potřebuje reload (automatický při `docker compose up -d`)
- `app.endurobuddy.cz` TLS certifikát — Traefik ho vystaví automaticky přes letsencrypt při prvním routování (může trvat ~1 min)
- `DJANGO_ALLOWED_HOSTS` musí obsahovat `app.endurobuddy.cz` pro Django API calls z `app.*` subdomény (Host header je `app.endurobuddy.cz`)
- `CSRF_TRUSTED_ORIGINS` musí obsahovat `https://app.endurobuddy.cz` pro POST requesty

---

## Soubory ke změně

| Soubor | Změna |
|--------|-------|
| `docker-compose.yml` | Traefik router pro `app.endurobuddy.cz` + `NUXT_PUBLIC_APP_HOST` |
| `.env.example` | Doplnit `DJANGO_ALLOWED_HOSTS` s oběma doménami |
| Produkční `.env` (server) | Aktualizovat `DJANGO_ALLOWED_HOSTS` |
