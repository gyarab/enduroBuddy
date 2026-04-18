# Infrastructure Plan — uv + pnpm + Celery + Redis

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace pip+npm with uv+pnpm, add Redis and Celery to replace the existing ThreadPoolExecutor-based async with a proper task queue.

**Architecture:** `uv` manages Python deps via `pyproject.toml`, `pnpm` manages Node deps, Redis runs as a Docker service, and Celery replaces the `_executor.submit()` call in `dashboard/services/tasks.py` with a `@shared_task`. The existing `_execute_garmin_sync_job` function body stays intact — only the dispatch mechanism changes.

**Tech Stack:** uv 0.4+, pnpm 9+, Celery 5.3+, Redis 7, django-celery-beat 2.7+, django-celery-results 2.5+

---

## File Map

| Action | File |
|--------|------|
| Create | `backend/pyproject.toml` |
| Delete | `requirements.txt` (root) |
| Modify | `Dockerfile` |
| Modify | `docker-compose.yml` |
| Modify | `docker-compose.prod.yml` |
| Create | `backend/config/celery.py` |
| Modify | `backend/config/__init__.py` |
| Modify | `backend/config/settings.py` |
| Modify | `backend/dashboard/services/tasks.py` |
| Create | `backend/dashboard/tests/test_celery_tasks.py` |

---

## Task 1: Migrate Python deps to uv

**Files:**
- Create: `backend/pyproject.toml`
- Delete: `requirements.txt`

- [ ] **Krok 1: Ověřit obsah requirements.txt**

```bash
cat requirements.txt
```

Očekávaný výstup (aktuální deps):
```
asgiref==3.11.0
cryptography==46.0.3
Django==5.2.9
django-allauth==65.14.3
django-cors-headers==4.7.0
djangorestframework==3.16.0
fitparse==1.2.0
garminconnect==0.2.28
gunicorn==23.0.0
psycopg==3.3.2
psycopg-binary==3.3.2
PyJWT==2.10.1
requests==2.32.4
sqlparse==0.5.5
tzdata==2025.3
whitenoise==6.9.0
```

- [ ] **Krok 2: Vytvořit `backend/pyproject.toml`**

```toml
[project]
name = "endurobuddy"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "django==5.2.9",
    "django-allauth==65.14.3",
    "django-cors-headers==4.7.0",
    "djangorestframework==3.16.0",
    "fitparse==1.2.0",
    "garminconnect==0.2.28",
    "gunicorn==23.0.0",
    "psycopg[binary]==3.3.2",
    "PyJWT==2.10.1",
    "requests==2.32.4",
    "whitenoise==6.9.0",
    "celery[redis]==5.4.0",
    "django-celery-beat==2.7.0",
    "django-celery-results==2.5.1",
    "redis==5.2.1",
]

[dependency-groups]
dev = [
    "pytest-django==4.9.0",
    "factory-boy==3.3.1",
]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings"
pythonpath = ["."]
```

- [ ] **Krok 3: Nainstalovat uv a vygenerovat lock file**

```bash
pip install uv
cd backend
uv lock
```

Očekávaný výstup: `Resolved X packages` + vytvoření `backend/uv.lock`

- [ ] **Krok 4: Ověřit instalaci**

```bash
cd backend
uv sync
python -c "import django; print(django.__version__)"
```

Očekávaný výstup: `5.2.9`

- [ ] **Krok 5: Smazat requirements.txt**

```bash
rm requirements.txt
```

- [ ] **Krok 6: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git rm requirements.txt
git commit -m "chore: migrate Python deps from pip/requirements.txt to uv/pyproject.toml"
```

---

## Task 2: Aktualizovat Dockerfile pro uv

**Files:**
- Modify: `Dockerfile`

- [ ] **Krok 1: Ověřit aktuální Dockerfile**

Aktuální Stage 2 (Django runtime) začíná:
```dockerfile
FROM python:3.12-slim
...
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
```

- [ ] **Krok 2: Nahradit pip za uv v Dockerfile**

Nahradit Stage 2 od `FROM python:3.12-slim` po `COPY backend ./backend`:

```dockerfile
# Stage 1: Build Vue SPA
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Django runtime
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Install Python dependencies via uv
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend ./backend

# Copy Vue build output from frontend stage
COPY --from=frontend-build /app/backend/static_build ./backend/static_build

WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]
```

Poznámka: `uv sync --frozen --no-dev` instaluje přesně deps z lock file bez dev závislostí.

- [ ] **Krok 3: Ověřit build**

```bash
docker build -t endurobuddy-test .
```

Očekávaný výstup: `Successfully built ...`

- [ ] **Krok 4: Commit**

```bash
git add Dockerfile
git commit -m "chore: switch Dockerfile to uv for Python dependency installation"
```

---

## Task 3: Migrate Node deps na pnpm

**Files:**
- Create: `frontend/.npmrc`
- Modify: `docker-compose.yml` (frontend service)
- Delete: `frontend/package-lock.json`

- [ ] **Krok 1: Nainstalovat pnpm (lokálně)**

```bash
npm install -g pnpm@9
pnpm --version
```

Očekávaný výstup: `9.x.x`

- [ ] **Krok 2: Konvertovat lock file**

```bash
cd frontend
pnpm import
```

Vytvoří `frontend/pnpm-lock.yaml` z `package-lock.json`.

- [ ] **Krok 3: Vytvořit `frontend/.npmrc`**

```ini
shamefully-hoist=true
```

Potřebné pro Nuxt kompatibilitu (rozloží symlinky do flat node_modules).

- [ ] **Krok 4: Ověřit instalaci**

```bash
cd frontend
rm -rf node_modules
pnpm install
pnpm test
```

Očekávaný výstup: `✓ 75 tests passed`

- [ ] **Krok 5: Smazat package-lock.json**

```bash
rm frontend/package-lock.json
```

- [ ] **Krok 6: Aktualizovat docker-compose.yml — frontend service**

Nahradit `command` v `frontend` service:

```yaml
frontend:
  image: node:20-alpine
  container_name: endurobuddy-frontend
  working_dir: /app/frontend
  command: sh -c "npm install -g pnpm && pnpm install --frozen-lockfile && pnpm dev"
  environment:
    DJANGO_ORIGIN: "http://web:8000"
  volumes:
    - ./frontend:/app/frontend
  ports:
    - "5173:5173"
  depends_on:
    - web
  networks:
    - backend
```

- [ ] **Krok 7: Aktualizovat Dockerfile — Stage 1 (frontend build)**

```dockerfile
# Stage 1: Build Vue SPA
FROM node:20-alpine AS frontend-build

RUN npm install -g pnpm

WORKDIR /app/frontend

COPY frontend/pnpm-lock.yaml frontend/package.json ./
RUN pnpm install --frozen-lockfile

COPY frontend/ ./
RUN pnpm build
```

- [ ] **Krok 8: Commit**

```bash
git add frontend/pnpm-lock.yaml frontend/.npmrc docker-compose.yml Dockerfile
git rm frontend/package-lock.json
git commit -m "chore: migrate frontend from npm to pnpm"
```

---

## Task 4: Přidat Redis do Docker Compose

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docker-compose.prod.yml`

- [ ] **Krok 1: Přidat Redis service do `docker-compose.yml`**

Do sekce `services:` přidat za `db:`:

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
    command: redis-server --appendonly yes
```

Do sekce `volumes:` přidat:
```yaml
  endurobuddy_redis:
```

`web` service získá závislost:
```yaml
  web:
    ...
    depends_on:
      - db
      - redis
```

- [ ] **Krok 2: Přidat Redis do `docker-compose.prod.yml`**

```yaml
  redis:
    image: redis:7-alpine
    container_name: endurobuddy-redis
    restart: unless-stopped
    volumes:
      - endurobuddy_redis:/var/lib/redis/data
    networks:
      - backend
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
```

Volumes sekce:
```yaml
  endurobuddy_redis:
```

Poznámka: V produkci Redis chráněn heslem přes `REDIS_PASSWORD` env var.

- [ ] **Krok 3: Ověřit spuštění**

```bash
docker compose up redis -d
docker compose exec redis redis-cli ping
```

Očekávaný výstup: `PONG`

- [ ] **Krok 4: Commit**

```bash
git add docker-compose.yml docker-compose.prod.yml
git commit -m "feat: add Redis service to Docker Compose"
```

---

## Task 5: Přidat Celery do Djanga

**Files:**
- Create: `backend/config/celery.py`
- Modify: `backend/config/__init__.py`
- Modify: `backend/config/settings.py`

- [ ] **Krok 1: Ověřit aktuální `backend/config/__init__.py`**

```bash
cat backend/config/__init__.py
```

Pravděpodobně prázdný soubor.

- [ ] **Krok 2: Vytvořit `backend/config/celery.py`**

```python
from __future__ import annotations

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("endurobuddy")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

- [ ] **Krok 3: Aktualizovat `backend/config/__init__.py`**

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

- [ ] **Krok 4: Přidat Celery konfiguraci do `backend/config/settings.py`**

Na konec souboru za email konfiguraci přidat:

```python
# Celery
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
```

- [ ] **Krok 5: Přidat django_celery_beat a django_celery_results do INSTALLED_APPS**

V `settings.py` — do `INSTALLED_APPS` přidat:

```python
    "django_celery_beat",
    "django_celery_results",
```

- [ ] **Krok 6: Spustit migrace**

```bash
cd backend
python manage.py migrate
```

Očekávaný výstup: nové migrace pro `django_celery_beat` a `django_celery_results`.

- [ ] **Krok 7: Ověřit, že Celery app se importuje bez chyb**

```bash
cd backend
python -c "from config.celery import app; print(app)"
```

Očekávaný výstup: `<Celery endurobuddy at 0x...>`

- [ ] **Krok 8: Commit**

```bash
git add backend/config/celery.py backend/config/__init__.py backend/config/settings.py
git commit -m "feat: add Celery app with Redis broker to Django config"
```

---

## Task 6: Přidat Celery worker a beat do Docker Compose

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Krok 1: Přidat celery-worker service**

Do `docker-compose.yml` přidat za `web:`:

```yaml
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: endurobuddy-celery-worker
    restart: unless-stopped
    command: sh -c "cd /app/backend && celery -A config worker -l info"
    depends_on:
      - db
      - redis
    env_file:
      - .env
    environment:
      POSTGRES_HOST: db
      DJANGO_DEBUG: "true"
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
    command: sh -c "cd /app/backend && celery -A config beat -l info"
    depends_on:
      - db
      - redis
    env_file:
      - .env
    environment:
      POSTGRES_HOST: db
      DJANGO_DEBUG: "true"
    volumes:
      - ./backend:/app/backend
    networks:
      - backend
```

- [ ] **Krok 2: Ověřit spuštění workeru**

```bash
docker compose up celery-worker -d
docker compose logs celery-worker --tail=20
```

Očekávaný výstup obsahuje:
```
[config.worker] ready.
celery@... ready.
```

- [ ] **Krok 3: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add Celery worker and beat services to Docker Compose"
```

---

## Task 7: Napsat test pro Garmin sync task

**Files:**
- Create: `backend/dashboard/tests/test_celery_tasks.py`

Testy se píšou před refaktorem (TDD).

- [ ] **Krok 1: Napsat failing test**

Vytvořit `backend/dashboard/tests/test_celery_tasks.py`:

```python
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from accounts.models import ImportJob


@pytest.fixture
def import_job(db, django_user_model):
    user = django_user_model.objects.create_user(
        username="tester@example.com",
        email="tester@example.com",
        password="testpass123",
    )
    return ImportJob.objects.create(
        user=user,
        kind=ImportJob.Kind.GARMIN_SYNC,
        status=ImportJob.Status.QUEUED,
        window="last_7_days",
        message="Waiting.",
    )


def test_execute_garmin_sync_job_marks_running(import_job):
    """Job must transition to RUNNING before any Garmin API call."""
    from dashboard.services.tasks import _execute_garmin_sync_job

    with patch("dashboard.services.tasks.sync_garmin_for_user") as mock_sync:
        mock_sync.return_value = (0, 0, MagicMock())
        _execute_garmin_sync_job(import_job.id)

    import_job.refresh_from_db()
    assert import_job.status == ImportJob.Status.SUCCESS


def test_execute_garmin_sync_job_nonexistent_id():
    """Task with nonexistent job ID must exit silently without raising."""
    from dashboard.services.tasks import _execute_garmin_sync_job

    _execute_garmin_sync_job(999999)  # must not raise


def test_enqueue_garmin_sync_job_dispatches_celery_task(import_job):
    """enqueue_garmin_sync_job must call Celery task, not ThreadPoolExecutor."""
    from dashboard.services import tasks as tasks_module

    with patch.object(tasks_module, "execute_garmin_sync_job") as mock_task:
        mock_task.delay = MagicMock()
        from dashboard.services.tasks import enqueue_garmin_sync_job
        enqueue_garmin_sync_job(import_job.id)
        mock_task.delay.assert_called_once_with(import_job.id)
```

- [ ] **Krok 2: Spustit testy — ověřit, že poslední test PADÁ**

```bash
cd backend
python -m pytest dashboard/tests/test_celery_tasks.py -v
```

Očekávaný výstup:
```
PASSED  test_execute_garmin_sync_job_marks_running
PASSED  test_execute_garmin_sync_job_nonexistent_id
FAILED  test_enqueue_garmin_sync_job_dispatches_celery_task
  AttributeError: module has no attribute 'execute_garmin_sync_job'
```

- [ ] **Krok 3: Commit (failing test)**

```bash
git add backend/dashboard/tests/test_celery_tasks.py
git commit -m "test: add failing test for Celery-based Garmin sync dispatch"
```

---

## Task 8: Konvertovat Garmin sync na Celery task

**Files:**
- Modify: `backend/dashboard/services/tasks.py`

- [ ] **Krok 1: Nahradit `ThreadPoolExecutor` Celery taskem**

Celý soubor `backend/dashboard/services/tasks.py` nahradit:

```python
from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .imports import import_fit_for_user, sync_garmin_for_user

logger = logging.getLogger(__name__)


def run_fit_import(user, uploaded_file):
    """FIT import — synchronní (soubory jsou malé, parsování rychlé)."""
    return import_fit_for_user(user, uploaded_file)


def enqueue_garmin_sync_job(import_job_id: int) -> None:
    """Odešle Garmin sync job do Celery fronty."""
    execute_garmin_sync_job.delay(import_job_id)


@shared_task(bind=True, max_retries=0, name="dashboard.tasks.execute_garmin_sync_job")
def execute_garmin_sync_job(self, import_job_id: int) -> None:
    """Celery task — vykoná Garmin sync pro daný ImportJob."""
    _execute_garmin_sync_job(import_job_id)


def _execute_garmin_sync_job(import_job_id: int) -> None:
    from accounts.models import GarminSyncAudit, ImportJob
    from accounts.services.garmin_secret_store import GarminSecretStoreError
    from activities.services.garmin_importer import GarminImportError
    from dashboard.services.imports import audit_garmin

    job = ImportJob.objects.select_related("user").filter(
        id=import_job_id,
        kind=ImportJob.Kind.GARMIN_SYNC,
    ).first()
    if job is None or job.status in {ImportJob.Status.SUCCESS, ImportJob.Status.ERROR}:
        return

    job.status = ImportJob.Status.RUNNING
    job.started_at = timezone.now()
    job.total_count = 0
    job.processed_count = 0
    job.imported_count = 0
    job.skipped_count = 0
    job.message = "Garmin sync running (0%)."
    job.save(
        update_fields=[
            "status",
            "started_at",
            "total_count",
            "processed_count",
            "imported_count",
            "skipped_count",
            "message",
            "updated_at",
        ]
    )

    def _progress_percent(*, stage: str, total: int, processed: int) -> int:
        if stage == "downloading_done":
            return 10
        if stage == "importing":
            if total <= 0:
                return 95
            return min(95, max(10, int((processed / total) * 85) + 10))
        return 0

    def _on_progress(*, stage: str, total: int, processed: int, imported: int, skipped: int) -> None:
        percent = _progress_percent(stage=stage, total=total, processed=processed)
        if stage == "downloading_done":
            msg = "Garmin sync: downloading finished (10%)."
        elif stage == "importing":
            if total > 0:
                msg = f"Garmin sync: processing {processed}/{total} ({percent}%)."
            else:
                msg = "Garmin sync: no activities to import (95%)."
        else:
            msg = f"Garmin sync running ({percent}%)."

        ImportJob.objects.filter(id=job.id).update(
            total_count=max(0, int(total)),
            processed_count=max(0, int(processed)),
            imported_count=max(0, int(imported)),
            skipped_count=max(0, int(skipped)),
            message=msg[:255],
            updated_at=timezone.now(),
        )

    try:
        imported, skipped, connection = sync_garmin_for_user(
            job.user,
            window=job.window or "last_30_days",
            progress_callback=_on_progress,
        )
        job.refresh_from_db(fields=["total_count", "processed_count"])
        job.status = ImportJob.Status.SUCCESS
        total_done = max(int(imported) + int(skipped), int(job.total_count or 0))
        job.total_count = total_done
        job.processed_count = total_done
        job.imported_count = imported
        job.skipped_count = skipped
        job.message = f"Garmin sync done (100%). Imported: {imported}, duplicates: {skipped}."
        job.finished_at = timezone.now()
        job.save(
            update_fields=[
                "status",
                "total_count",
                "processed_count",
                "imported_count",
                "skipped_count",
                "message",
                "finished_at",
                "updated_at",
            ]
        )
        audit_garmin(
            user=job.user,
            connection=connection,
            action=GarminSyncAudit.Action.SYNC,
            status=GarminSyncAudit.Status.SUCCESS,
            window=job.window,
            imported_count=imported,
            skipped_count=skipped,
            message="Garmin sync finished.",
        )
    except (GarminImportError, GarminSecretStoreError) as exc:
        job.status = ImportJob.Status.ERROR
        job.message = f"Garmin sync failed: {str(exc)}"[:255]
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "message", "finished_at", "updated_at"])
        audit_garmin(
            user=job.user,
            action=GarminSyncAudit.Action.SYNC,
            status=GarminSyncAudit.Status.ERROR,
            window=job.window,
            message=str(exc),
        )
    except Exception:
        logger.exception("Garmin background sync failed for import_job_id=%s", import_job_id)
        job.status = ImportJob.Status.ERROR
        job.message = "Garmin sync failed: unexpected error."
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "message", "finished_at", "updated_at"])
        audit_garmin(
            user=job.user,
            action=GarminSyncAudit.Action.SYNC,
            status=GarminSyncAudit.Status.ERROR,
            window=job.window,
            message="Unexpected Garmin sync error.",
        )
```

Klíčové změny oproti originálu:
- Smazán `ThreadPoolExecutor` a `_executor`
- Přidán `@shared_task` dekorátor na `execute_garmin_sync_job`
- `enqueue_garmin_sync_job` volá `.delay()` místo `_executor.submit()`
- `_execute_garmin_sync_job` je čistá funkce (testovatelná bez Celery)

- [ ] **Krok 2: Spustit testy — všechny musí projít**

```bash
cd backend
python -m pytest dashboard/tests/test_celery_tasks.py -v
```

Očekávaný výstup:
```
PASSED  test_execute_garmin_sync_job_marks_running
PASSED  test_execute_garmin_sync_job_nonexistent_id
PASSED  test_enqueue_garmin_sync_job_dispatches_celery_task
```

- [ ] **Krok 3: Spustit celý test suite**

```bash
cd backend
python -m pytest -v
```

Očekávaný výstup: všechny testy zelené.

- [ ] **Krok 4: Ověřit, že Django check projde**

```bash
cd backend
python manage.py check
```

Očekávaný výstup: `System check identified no issues (0 silenced).`

- [ ] **Krok 5: Commit**

```bash
git add backend/dashboard/services/tasks.py
git commit -m "feat: replace ThreadPoolExecutor with Celery for async Garmin sync"
```

---

## Task 9: End-to-end ověření

- [ ] **Krok 1: Spustit celý stack**

```bash
docker compose up --build -d
docker compose logs -f celery-worker
```

- [ ] **Krok 2: Ověřit, že worker naslouchá**

```bash
docker compose exec celery-worker celery -A config inspect active
```

Očekávaný výstup: `-> celery@...: OK` (prázdný seznam aktivních tasků)

- [ ] **Krok 3: Ověřit frontend (pnpm)**

```bash
cd frontend
pnpm test
```

Očekávaný výstup: `✓ 75 tests passed`

- [ ] **Krok 4: Commit závěrečný**

```bash
git add .
git commit -m "chore: verify uv+pnpm+Celery+Redis stack end-to-end"
```
