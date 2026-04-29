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

### Konfigurace

```bash
cp .env.example .env
```

Vyplň povinné hodnoty — ostatní mají rozumné výchozí hodnoty pro dev:

| Proměnná | Dev | Produkce |
|----------|-----|---------|
| `DJANGO_SECRET_KEY` | libovolný řetězec | dlouhý náhodný klíč |
| `POSTGRES_*` | `endurobuddy` / `endurobuddy_password` | produkční DB credentials |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` (native) nebo `redis://redis:6379/0` (Docker) | s heslem |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | seznam domén |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `http://localhost:3000,http://localhost:8000` | https:// domény |
| `DJANGO_CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | https:// domény |
| `GARMIN_CONNECT_ENABLED` | `false` | `true` (vyžaduje KMS klíč) |
| `GOOGLE_CLIENT_ID/SECRET` | prázdné (OAuth disabled) | Google Console credentials |
| `TRAEFIK_*` | není potřeba | pro produkční Traefik routing |
| `SESSION/CSRF_COOKIE_DOMAIN` | není potřeba | `.endurobuddy.cz` pro subdomény |
| `DJANGO_APP_HOST` | není potřeba | `app.endurobuddy.cz` |

Kompletní šablona se všemi proměnnými je v [.env.example](.env.example).

---

### Dev workflow (doporučeno)

Pro rychlý iterativní vývoj spusť databázi a Redis přes Docker, Django a Nuxt lokálně.

**1. Spusť závislosti**

```bash
docker compose up db redis -d
```

**2. Backend**

```bash
cd backend
uv sync
source ../.venv/Scripts/activate  # Windows: ..\.venv\Scripts\activate
python manage.py migrate
python manage.py runserver
```

**3. Frontend**

```bash
cd frontend
pnpm install
pnpm dev
```

Nuxt běží na `http://localhost:3000`, Django na `http://localhost:8000`. Nuxt automaticky proxuje `/api/*` na Django.

---

### Subdoménové testování

Ve výchozím stavu aplikace běží na `localhost` bez subdoménové logiky (`NUXT_PUBLIC_APP_HOST` je prázdný → middleware se nespustí).

Pro testování přesměrování mezi `endurobuddy.local` a `app.endurobuddy.local`:

**1. Přidej záznamy do hosts souboru** (otevři Notepad jako správce → `C:\Windows\System32\drivers\etc\hosts`):

```
127.0.0.1 endurobuddy.local
127.0.0.1 app.endurobuddy.local
```

**2. Uprav `.env`:**

```env
DJANGO_APP_HOST=app.endurobuddy.local
SESSION_COOKIE_DOMAIN=.endurobuddy.local
CSRF_COOKIE_DOMAIN=.endurobuddy.local
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,endurobuddy.local,app.endurobuddy.local
DJANGO_CSRF_TRUSTED_ORIGINS=http://endurobuddy.local:3000,http://app.endurobuddy.local:3000,http://endurobuddy.local:8000,http://app.endurobuddy.local:8000
DJANGO_CORS_ALLOWED_ORIGINS=http://endurobuddy.local:3000,http://app.endurobuddy.local:3000
```

**3. Přidej `frontend/.env`** (čte ho Nuxt dev server, není v gitu):

```bash
echo "NUXT_PUBLIC_APP_HOST=app.endurobuddy.local" > frontend/.env
```

Pak: `http://endurobuddy.local:3000` → veřejná část, `http://app.endurobuddy.local:3000` → přihlášená část.

> **Poznámka:** Cross-domain redirecty v middleware používají `https://`, takže na HTTP localhost selžou. Přímá navigace na správnou URL funguje normálně.

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
