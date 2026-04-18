# Implementační plán — Nuxt migrace + infrastrukturní základ

**Datum:** 2026-04-18  
**Větev:** `feat/nuxt-migration`  
**Spec:** `docs/superpowers/specs/2026-04-18-nuxt-migration-design.md`

---

## Přehled změn

Tento plán zahrnuje tři přidané oblasti nad rámec čisté Nuxt migrace:

| Oblast | Technologie | Co nahrazuje / přidává |
|--------|------------|------------------------|
| Python package manager | **uv** | pip + virtualenv |
| Node package manager | **pnpm** | npm |
| Task queue + broker | **Celery + Redis** | synchronní Garmin sync (neexistuje jako async) |
| Frontend framework | **Nuxt 3** | Vite SPA + Django templates |

---

## Proč uv, pnpm, Celery, Redis

### uv — Python package manager
**K čemu slouží:** Nahrazuje pip a virtualenv. Instaluje balíčky 10–100× rychleji díky Rust implementaci a paralelním stahováním. Generuje `uv.lock` pro 100% reproducibilní prostředí.

**Alternativy:**
- *poetry* — populární, ale pomalý a komplexní (vlastní resolver, jiný formát)
- *pdm* — moderní, méně rozšířený
- *pip* (aktuální) — pomalý, žádný lock file

**Závěr:** uv je v roce 2025/2026 průmyslový standard pro nové Python projekty. Drop-in náhrada, nulové riziko.

**V kontextu EnduroBuddy:** Rychlejší `docker build`, reproducibilní CI/CD, `pyproject.toml` jako single source of truth pro závislosti.

---

### pnpm — Node package manager
**K čemu slouží:** Nahrazuje npm. Ukládá balíčky v globálním content-addressable store a linkuje je — node_modules je 3–5× menší, instalace 2× rychlejší. Nativní podpora workspaces (pro Nuxt layers nebo budoucí monorepo).

**Alternativy:**
- *npm* (aktuální) — pomalý, velký node_modules, žádné workspaces
- *yarn berry* — komplexní, PnP mode je nestabilní
- *bun* — nejrychlejší, ale runtime nestabilní pro produkci v 2026

**Závěr:** pnpm je správná volba pro Nuxt projekty. Nuxt UI docs i Nuxt vlastní starter používají pnpm.

**V kontextu EnduroBuddy:** Základ pro případné Nuxt layers (sdílené komponenty). Bez Turborepo — to přijde až kdyby vznikl druhý package.

---

### Celery — task queue
**K čemu slouží:** Asynchronní zpracování úloh mimo HTTP request-response cyklus. Worker procesy beží vedle Django a zpracovávají úlohy z fronty.

**Proč to EnduroBuddy potřebuje:**
1. **Garmin sync** — volání Garmin Connect API trvá sekundy až desítky sekund. Dnes buď blokuje request, nebo není implementováno. Správně: uživatel klikne "Sync", Django vytvoří Celery task a okamžitě vrátí `202 Accepted`. Frontend polluje `/api/v1/imports/status/{job_id}/`.
2. **FIT file parsing** — CPU-intenzivní, nesmí blokovat web worker.
3. **Garmin periodic polling** — Celery Beat spouští sync každých N minut pro aktivní propojení.
4. **Emaily** — transakční emaily (potvrzení, pozvánky) asynchronně.

**Alternativy:**
- *Django Q2* — jednodušší, broker je DB (žádný Redis), ale neškáluje. Vhodné pro < 100 úloh/den. EnduroBuddy bude mít Garmin sync pro každého sportovce denně → Redis je správný.
- *Dramatiq + Redis* — moderní, čistší API než Celery, žádné pickle. Ale menší ekosystém, méně dokumentace.
- *Huey* — lehký, Redis nebo SQLite. Chybí Celery Beat ekvivalent ve stejné kvalitě.
- *RQ (Redis Queue)* — jednoduchý, ale Celery Beat (periodické úlohy) chybí.

**Závěr:** Celery + Redis je de-facto standard. Nejlepší dokumentace, největší ekosystém, Celery Beat pro Garmin polling.

---

### Redis — message broker + cache
**K čemu slouží:** Dvě role najednou:
1. **Celery broker** — fronta úloh (Celery posílá a přijímá zprávy přes Redis)
2. **Django cache** — session cache, rate limiting (django-axes), případně API response cache

**Alternativy pro broker:**
- *RabbitMQ* — robustnější messaging, ale komplexní provoz, overkill pro tento projekt
- *PostgreSQL jako broker* — Django Q2 přístup, neškáluje
- *Amazon SQS / upoutaný Redis* — cloud-only, ne pro fázi 1

**Závěr:** Redis v jedné instanci jako broker + cache je standardní jednoduchý setup. Fáze 1 na Proxmox: Redis kontejner. Fáze 2 na Hetzner: stejný kontejner nebo Hetzner Managed Redis.

---

## Fáze implementace

### Fáze 0: Tooling (nezávislé, bez rizika)

#### 0a — Migrace na uv

**Soubory k vytvoření/změně:**
- Vytvořit `backend/pyproject.toml` — deklarace závislostí (nahrazuje `requirements.txt`)
- Smazat `requirements.txt` (pokud existuje — v backendu momentálně není, generuje se z installed_apps)
- Aktualizovat `Dockerfile` — nahradit `pip install` za `uv sync`
- Aktualizovat `docker-compose.yml` — build context

**Postup:**
```bash
cd backend
uv init --no-workspace  # vytvoří pyproject.toml
uv add django djangorestframework django-allauth django-cors-headers whitenoise fitparse psycopg[binary]
uv add --dev pytest-django factory-boy ruff mypy django-stubs
```

**Dockerfile změna:**
```dockerfile
# Před:
RUN pip install -r requirements.txt

# Po:
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
```

**Best practice:** `uv sync --frozen` v CI/prod (respektuje lock file), `uv sync` v dev (aktualizuje).

---

#### 0b — Migrace na pnpm

**Soubory k vytvoření/změně:**
- Smazat `frontend/package-lock.json`
- Vytvořit `frontend/.npmrc` s `shamefully-hoist=true` (pro Nuxt kompatibilitu)
- Aktualizovat `docker-compose.yml` — nahradit `npm ci` za `pnpm install --frozen-lockfile`

**Postup:**
```bash
cd frontend
npm install -g pnpm
pnpm import  # konvertuje package-lock.json → pnpm-lock.yaml
rm package-lock.json
```

**Nuxt starter počítá s pnpm** — `nuxi init` defaultně generuje `pnpm-lock.yaml`.

---

### Fáze 1: Redis + Celery infrastruktura

#### 1a — Redis service

**Soubor:** `docker-compose.yml`

```yaml
redis:
  image: redis:7-alpine
  container_name: endurobuddy-redis
  restart: unless-stopped
  ports:
    - "6379:6379"
  volumes:
    - endurobuddy_redis:/var/lib/redis/data
  networks:
    - backend
  command: redis-server --appendonly yes  # persistence

volumes:
  endurobuddy_redis:  # přidat
```

**Best practice:** `appendonly yes` zapíná AOF persistence — při restartu se fronta neztratí.

---

#### 1b — Celery worker + beat

**Nové soubory:**
- `backend/config/celery.py` — Celery app instance
- `backend/config/__init__.py` — auto-discover (import celery app)
- `backend/dashboard/tasks.py` — Garmin sync task
- `backend/activities/tasks.py` — FIT parsing task

**`backend/config/celery.py`:**
```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("endurobuddy")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

**`backend/config/__init__.py`:**
```python
from .celery import app as celery_app
__all__ = ("celery_app",)
```

**`backend/config/settings.py` — přidat:**
```python
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
```

**`docker-compose.yml` — přidat:**
```yaml
celery-worker:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: endurobuddy-celery-worker
  restart: unless-stopped
  command: celery -A config worker -l info
  depends_on:
    - db
    - redis
  env_file:
    - .env
  volumes:
    - ./backend:/app/backend
  networks:
    - backend

celery-beat:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: endurobuddy-celery-beat
  restart: unless-stopped
  command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
  depends_on:
    - db
    - redis
  env_file:
    - .env
  volumes:
    - ./backend:/app/backend
  networks:
    - backend
```

**Závislosti k přidání:**
```
celery[redis]
django-celery-beat   # Beat scheduler v DB (admin-konfigurovatelný)
django-celery-results  # výsledky tasků v DB (pro polling stavu)
```

**`INSTALLED_APPS` — přidat:**
```python
"django_celery_beat",
"django_celery_results",
```

---

#### 1c — Garmin sync task (první reálný task)

**`backend/activities/tasks.py`:**
```python
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def sync_garmin_activities(self, athlete_id: int, date_from: str, date_to: str):
    """Asynchronní Garmin sync — voláno z GarminImportModal."""
    ...
```

**API endpoint — změna chování:**
```
POST /api/v1/imports/garmin/sync/
→ dříve: synchronní, blokuje
→ po:    vytvoří task, vrátí {"job_id": "...", "status": "pending"}

GET /api/v1/imports/garmin/status/{job_id}/
→ vrátí stav tasku (pending/progress/success/failure)
```

Frontend `useGarminImport.ts` už polling implementuje — backend se přizpůsobí.

---

### Fáze 2: Nuxt setup

*(Viz spec `2026-04-18-nuxt-migration-design.md` — sekce "Pořadí implementace")*

**2a — Inicializace Nuxt 3 projektu**

```bash
cd frontend
pnpm dlx nuxi@latest init .  # inicializace do stávajícího adresáře
```

Konfigurace `nuxt.config.ts`:
```typescript
export default defineNuxtConfig({
  modules: [
    '@pinia/nuxt',
    '@nuxtjs/i18n',
  ],
  routeRules: {
    '/': { ssr: true },
    '/about': { ssr: true },
    '/terms': { ssr: true },
    '/privacy': { ssr: true },
    '/app/**': { ssr: false },
    '/coach/**': { ssr: false },
    '/accounts/**': { ssr: false },
  },
  runtimeConfig: {
    public: {
      apiBase: '/api/v1',
    },
  },
})
```

**2b — Migrace existujících Vue komponent**

Přesunout z `src/` do Nuxt struktury:
- `src/components/` → `components/`
- `src/stores/` → `stores/`
- `src/composables/` → `composables/`
- `src/assets/` → `assets/`
- `src/locales/` → `i18n/locales/`
- `src/router/index.ts` → `pages/` (file-based routing)

Klíčové změny:
- `axios` klient (`src/api/client.ts`) → `$fetch` wrapper v `utils/api.ts`
- `useI18n.ts` (vlastní) → `@nuxtjs/i18n`
- `App.vue` + `main.ts` → `app.vue` + `plugins/`

**2c — Veřejné stránky (SSR)**

Nové soubory:
- `layouts/public.vue` — topbar, footer (z `base_public.html`)
- `pages/index.vue` — landing page (z `public/home.html`)
- `pages/about.vue` — (z `public/about.html`)
- `pages/terms.vue` — (z `public/terms.html`)
- `pages/privacy.vue` — (z `public/privacy.html`)

Design tokeny (`assets/css/design-tokens.css`) zůstávají beze změny.

**2d — Error stránka**

Nový soubor `error.vue` — zobrazí kód chyby, zprávu a odkaz zpět.

**2e — Help modál (km pravidla)**

Nová komponenta `components/training/PlannedKmRulesModal.vue`.  
Integrovat do `components/training/PlannedRow.vue` jako help ikona.

**2f — Docker Compose — Nuxt service**

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
```

**Dockerfile pro Nuxt:**
```dockerfile
FROM node:20-alpine
RUN npm install -g pnpm
WORKDIR /app
COPY pnpm-lock.yaml package.json ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build
CMD ["node", ".output/server/index.mjs"]
```

---

### Fáze 3: Cleanup Django + Nginx

**3a — Odstranění Django templates a views**

Smazat:
- `backend/templates/public/` — celý adresář
- `backend/static/css/public-*.css`
- Views v `dashboard/views.py` obsluhující `/`, `/about/`, `/terms/`, `/privacy/`
- Odpovídající URL patterns v `config/urls.py`

Ponechat:
- `backend/templates/admin/` — Django admin
- `backend/templates/spa.html` — dokud Nuxt plně nepřevezme (dočasně)

**3b — Nginx routing**

Nahradit aktuální serving (whitenoise + Django) Nginxem:
```nginx
location /api/ { proxy_pass http://django:8000; }
location /admin/ { proxy_pass http://django:8000; }
location /static/ { proxy_pass http://django:8000; }
location / { proxy_pass http://nuxt:3000; }
```

---

### Fáze 4: Testování a QA

- `curl https://endurobuddy.local/` → kompletní HTML s meta tagy (SSR ověření)
- Přihlášení, dashboard, Garmin import → bez regresí
- Garmin sync → task se vytvoří, status endpoint polluje správně
- `npm test` / `pnpm test` → zelené
- `python manage.py check` → bez chyb

---

## Závislosti (přehled)

### Backend (přidat do pyproject.toml)
```
celery[redis]>=5.3
django-celery-beat>=2.7
django-celery-results>=2.5
redis>=5.0
```

### Frontend (přidat do package.json přes pnpm)
```
nuxt ^3.11
@pinia/nuxt ^0.9
@nuxtjs/i18n ^9
```

---

## Pořadí fází (timeline)

```
Fáze 0a (uv)        ──── nezávislé, kdykoli
Fáze 0b (pnpm)      ──── nezávislé, nutné před Nuxt setupem
Fáze 1 (Redis/Celery) ── nezávislé na Nuxt, doporučeno před fází 2
Fáze 2 (Nuxt)       ──── závisí na 0b
Fáze 3 (Cleanup)    ──── závisí na kompletní fázi 2
Fáze 4 (QA)         ──── závisí na fázi 3
```
