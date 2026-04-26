# EnduroBuddy

Tréninkový workspace pro vytrvalostní sporty. Propojuje trenéra a sportovce: trenér připravuje měsíční plány s týdenní strukturou, sportovec zapisuje splněné tréninky a importuje aktivity z Garmin Connect nebo FIT souborů.

## Stack

| Vrstva | Technologie |
|--------|-------------|
| Frontend | Nuxt 3 (SSR pro veřejné stránky, SPA pro přihlášenou část) |
| Backend | Django 5.2 + Django REST Framework |
| Databáze | PostgreSQL |
| Task queue | Celery + Redis (async Garmin sync, FIT parsing) |
| Auth | django-allauth (email + Google OAuth) |
| Python deps | uv + pyproject.toml |
| Node deps | pnpm |
| Kontejnerizace | Docker Compose + Nginx (reverse proxy) |

## Architektura

```
Nginx :80
├── /api/*        → Django :8000   (REST API)
├── /admin/*      → Django :8000   (Django admin)
├── /static/*     → Django :8000   (statické soubory)
├── /i18n/*       → Django :8000   (language switcher)
├── /accounts/google/* → Django :8000  (OAuth callback)
└── /*            → Nuxt :3000     (vše ostatní)
```

### Nuxt renderovací strategie

| URL | Režim |
|-----|-------|
| `/`, `/about`, `/terms`, `/privacy` | SSR (server-side rendering pro SEO) |
| `/app/**` | SPA (athlete dashboard) |
| `/coach/**` | SPA (coach workspace) |
| `/accounts/**` | SPA (allauth auth flow) |

### Struktura repozitáře

```
.
├── backend/                  # Django backend
│   ├── accounts/             # profily, role, Garmin připojení, ImportJob
│   ├── activities/           # import aktivit, FIT soubory, intervaly
│   ├── api/                  # DRF views + URL patterns
│   ├── config/               # settings, urls, celery, wsgi
│   ├── dashboard/            # servisní logika (handlers, Celery tasks)
│   ├── templates/            # Django admin šablony
│   └── training/             # plánované + splněné tréninky
├── frontend/                 # Nuxt 3 frontend
│   ├── assets/               # CSS design tokeny, fonty, public page CSS
│   ├── components/           # Vue komponenty (ui/, training/, coach/, layout/)
│   ├── composables/          # useGarminImport, useInlineEditor, useTrainingParser
│   ├── i18n/locales/         # cs.json + en.json
│   ├── layouts/              # default (AppShell), public (topbar+footer), auth
│   ├── pages/                # file-based routing (index, about, terms, privacy, app/*, coach/*, accounts/*)
│   ├── plugins/              # i18n-sync.client.ts (sync jazyka s Django)
│   ├── stores/               # Pinia stores (auth, training, coach, notifications…)
│   └── utils/                # apiFetch wrapper + api/ moduly
├── nginx/                    # Nginx konfigurace a Dockerfile
├── docs/                     # specs, implementační plány, visual style guide
├── docker-compose.yml        # lokální dev stack
├── docker-compose.prod.yml   # produkční stack (Traefik)
└── Dockerfile                # multi-stage build (Nuxt → Django)
```

## Role uživatelů

**Coach** — připravuje měsíční plány, spravuje sportovce a skupiny, sleduje plnění.  
**Athlete** — vidí plán, zapisuje splněné tréninky, importuje aktivity.

## Klíčové funkce

- Registrace, přihlášení, potvrzení e-mailu, reset hesla (django-allauth)
- Volitelný Google OAuth login
- Propojení trenér ↔ sportovec přes join code a join requesty
- Tréninkové skupiny a pozvánky přes token
- Měsíční plánovací dashboard s týdenní strukturou
- Inline editace plánovaných i splněných tréninků
- Import aktivit z FIT souborů
- Synchronizace s Garmin Connect (asynchronně přes Celery)
- Deduplikace importu podle kontrolního součtu
- Ukládání intervalů a vzorků pro analytiku
- Bilingvní UI (čeština + angličtina)
- Django admin pro správu dat

## Lokální vývoj

### Požadavky

- Docker a Docker Compose
- Node.js 20+ a pnpm (pro frontend dev server)
- Python 3.12+ a uv (pro backend mimo Docker)

### Rychlý start přes Docker

**1. Připrav konfiguraci**

```bash
cp .env.example .env
```

Do `.env` doplň minimálně:

```env
DJANGO_SECRET_KEY=replace-with-long-random-secret-key
POSTGRES_DB=endurobuddy
POSTGRES_USER=endurobuddy
POSTGRES_PASSWORD=endurobuddy_password
REDIS_URL=redis://redis:6379/0
```

**2. Spusť celý stack**

```bash
docker compose up --build
```

Spustí: PostgreSQL, Redis, Django (web), Celery worker, Celery beat, Nuxt, Nginx.

**3. Otevři v prohlížeči**

```
http://localhost/
```

---

### Dev workflow (doporučeno)

Pro rychlý iterativní vývoj spusť databázi a Redis přes Docker, Django a Nuxt lokálně.

**Backend:**

```bash
# Spusť závislosti
docker compose up db redis -d

# Aktivuj virtualenv s uv
cd backend
uv sync
source ../.venv/Scripts/activate  # Windows: ..\.venv\Scripts\activate

# Migrace
python manage.py migrate

# Django dev server
python manage.py runserver
```

**Frontend:**

```bash
cd frontend
pnpm install
pnpm dev
```

Nuxt dev server běží na `:3000`, proxuje `/api/*` na Django `:8000`.

---

### Proměnné prostředí

| Proměnná | Popis | Výchozí |
|----------|-------|---------|
| `DJANGO_SECRET_KEY` | Povinný klíč (bez něj aplikace nenaběhne) | — |
| `DJANGO_DEBUG` | Debug režim | `false` |
| `DJANGO_ALLOWED_HOSTS` | Povolené hosty | `localhost,127.0.0.1` |
| `POSTGRES_*` | Databázové připojení | — |
| `REDIS_URL` | Redis broker + cache | `redis://redis:6379/0` |
| `REGISTRATION_ENABLED` | Zapnutí registrace | `true` |
| `GARMIN_CONNECT_ENABLED` | Zobrazí/skryje Garmin napojení | `false` |
| `GARMIN_SYNC_ENABLED` | Povolí synchronizaci | `false` |
| `GARMIN_KMS_KEY_ID` | AWS KMS klíč pro šifrování tokenů | — |
| `GOOGLE_CLIENT_ID` | Google OAuth Client ID | — |
| `GOOGLE_CLIENT_SECRET` | Google OAuth Client Secret | — |

## Demo data

```bash
cd backend
python manage.py seed_coach_demo
# coach_demo@endurobuddy.local / demo12345
```

Vytvoří demo trenéra, tři sportovce, skupinu A-team a ukázkové měsíční plány.

## Testování

**Backend:**

```bash
cd backend
python -m pytest          # 125 testů
python manage.py check    # Django system check
```

**Frontend:**

```bash
cd frontend
pnpm test     # 95 testů (Vitest)
```

Pokrytí: FIT import flow, Garmin importer, Celery task dispatch, coach plánování, inline editace, bezpečnost profile/settings akcí.

## Vizuální identita

Design systém „Neon Lab × Swiss Precision" — kreativní energie s racionální čistotou.

| Token | Hodnota |
|-------|---------|
| Pozadí | `#09090b` |
| Surface | `#18181b` |
| Primární akcent | `#c8ff00` (electric lime) |
| Sekundární akcent | `#38bdf8` (crisp blue) |
| Display font | Syne 700–800 |
| Body font | Inter 400–600 |
| Mono font | JetBrains Mono 500 |

Detaily: [`docs/visual-style-guide.md`](docs/visual-style-guide.md)
