# Implementační plán: Production Routing + Auth Bugs

**Datum:** 2026-05-06  
**Spec:** `docs/superpowers/specs/2026-05-06-production-routing-auth-bugs.md`

---

## Task 1 — docker-compose.yml: Traefik router pro app.endurobuddy.cz

**Soubor:** `docker-compose.yml`

Přidat do nginx service labels:

```yaml
# App subdoména — stejný nginx stack, jiná doména
- "traefik.http.routers.endurobuddy-app.rule=Host(`app.endurobuddy.cz`)"
- "traefik.http.routers.endurobuddy-app.entrypoints=websecure"
- "traefik.http.routers.endurobuddy-app.tls.certresolver=letsencrypt"
- "traefik.http.services.endurobuddy-app.loadbalancer.server.port=80"
```

Nginx `default_server` blok zachytí requesty obou domén a routuje správně.

**Verifikace:** `docker compose config --quiet` bez chyb; po nasazení `curl -I https://app.endurobuddy.cz/` vrátí 200/30x místo 404.

---

## Task 2 — docker-compose.yml: NUXT_PUBLIC_APP_HOST do nuxt environment

**Soubor:** `docker-compose.yml`

```yaml
nuxt:
  environment:
    NUXT_PUBLIC_API_BASE: /api/v1
    NUXT_PUBLIC_APP_HOST: ${TRAEFIK_APP_HOST:-}
```

`TRAEFIK_APP_HOST` již existuje v `.env.example` a produkčním `.env`. Hodnota `:-` zajistí prázdný string v dev (kde proměnná není nastavena).

**Verifikace:** Dashboard na `app.endurobuddy.cz` zobrazí správné jméno uživatele; `endurobuddy.cz` přesměruje přihlášeného uživatele na `app.endurobuddy.cz`.

---

## Task 3 — .env.example: doplnit DJANGO_ALLOWED_HOSTS

**Soubor:** `.env.example`

Zkontrolovat a aktualizovat příklad hodnoty:

```
DJANGO_ALLOWED_HOSTS=endurobuddy.cz,app.endurobuddy.cz,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://endurobuddy.cz,https://app.endurobuddy.cz
```

Oba řetězce jsou čárkou oddělené. Django settings.py je správně parsuje.

---

## Task 4 — Commit + push

Commitovat Tasks 1–3 jako jeden commit, pushnout na `feat/registration-flow`.

---

## Task 5 — Instrukce pro update produkčního .env na serveru

**Není kód — je to checklist pro server deployment:**

Ověřit v `/path/to/.env` na serveru:

```
DJANGO_ALLOWED_HOSTS=endurobuddy.cz,app.endurobuddy.cz,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://endurobuddy.cz,https://app.endurobuddy.cz
TRAEFIK_APP_HOST=app.endurobuddy.cz
SESSION_COOKIE_DOMAIN=.endurobuddy.cz
CSRF_COOKIE_DOMAIN=.endurobuddy.cz
DJANGO_APP_HOST=app.endurobuddy.cz
```

Po aktualizaci `.env`:
```bash
docker compose up -d --build
```

---

## Pořadí implementace

```
Task 1 (docker router) → Task 2 (nuxt env) → Task 3 (.env.example) → Task 4 (commit)
```

Tasks 1–3 lze dělat paralelně (všechny jsou v různých souborech bez závislostí).
