# Migrace Celery + Redis → django-q2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nahradit Celery + Redis za django-q2 (PostgreSQL broker) a eliminovat Redis service, celery-worker a celery-beat z docker-compose.

**Architecture:** Django-q2 používá PostgreSQL jako broker — žádná nová infrastruktura. `qcluster` management command nahradí celery-worker jako Docker service. Celery-beat service zmizí úplně (no periodic tasks).

**Tech Stack:** django-q2, PostgreSQL (stávající DB), uv

---

## File Map

| Soubor | Akce |
|--------|------|
| `backend/pyproject.toml` | modify — swap Celery deps za django-q2 |
| `backend/config/settings.py` | modify — odebrat `CELERY_*`, přidat `Q_CLUSTER`, upravit `INSTALLED_APPS` |
| `backend/config/celery.py` | delete |
| `backend/config/__init__.py` | modify — odebrat import Celery app |
| `backend/dashboard/services/tasks.py` | modify — odebrat `@shared_task`, změnit enqueue na `async_task()` |
| `backend/dashboard/management/__init__.py` | create (prázdný) |
| `backend/dashboard/management/commands/__init__.py` | create (prázdný) |
| `backend/dashboard/management/commands/reset_stale_import_jobs.py` | create |
| `backend/dashboard/tests/test_celery_tasks.py` | delete |
| `backend/dashboard/tests/test_garmin_tasks.py` | create — přepsané testy pro django-q2 |
| `docker-compose.yml` | modify — odebrat redis/celery-worker/celery-beat, přidat qcluster |
| `docker-compose.prod.yml` | modify — stejné úpravy |

---

## Task 1: Závislosti + konfigurace

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/config/settings.py`
- Delete: `backend/config/celery.py`
- Modify: `backend/config/__init__.py`

- [ ] **Step 1: Aktualizuj pyproject.toml**

Nahraď čtyři Celery závislosti jednou django-q2:

```toml
# backend/pyproject.toml — sekce dependencies (celý blok závislostí)
dependencies = [
    "django==5.2.9",
    "django-allauth[socialaccount]==65.14.3",
    "django-cors-headers==4.7.0",
    "djangorestframework==3.16.0",
    "fitparse==1.2.0",
    "garminconnect==0.2.28",
    "gunicorn==23.0.0",
    "psycopg[binary]==3.3.2",
    "PyJWT==2.10.1",
    "requests==2.32.4",
    "whitenoise==6.9.0",
    "django-q2",
]
```

- [ ] **Step 2: Spusť uv sync**

```bash
cd backend
uv sync
```

Očekávané: `django-q2` nainstalováno, `celery`, `redis`, `django-celery-beat`, `django-celery-results` odebrány. Žádné chyby.

- [ ] **Step 3: Aktualizuj INSTALLED_APPS v settings.py**

V `backend/config/settings.py` nahraď řádky 90–91:

```python
    "django_celery_beat",
    "django_celery_results",
```

za:

```python
    "django_q",
```

- [ ] **Step 4: Odeber Celery konfiguraci a přidej Q_CLUSTER v settings.py**

V `backend/config/settings.py` nahraď blok na řádcích 269–276:

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

za:

```python
# Django Q2
Q_CLUSTER = {
    "name": "endurobuddy",
    "workers": 1,
    "timeout": 300,
    "retry": 0,
    "save_limit": 0,
    "orm": "default",
}
```

- [ ] **Step 5: Smaž config/celery.py**

```bash
git rm backend/config/celery.py
```

- [ ] **Step 6: Aktualizuj config/__init__.py**

Obsah `backend/config/__init__.py` nahraď prázdným souborem:

```python
```

(Soubor musí existovat, ale importovat Celery app již nesmí.)

- [ ] **Step 7: Ověř Django check**

```bash
cd backend
python manage.py check
```

Očekávané: `System check identified no issues (0 silenced).`

- [ ] **Step 8: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/config/settings.py backend/config/__init__.py
git commit -m "chore: swap Celery + Redis za django-q2"
```

---

## Task 2: DB migrace pro django_q

**Files:**
- Nové migrační soubory vytvoří `python manage.py migrate` automaticky z django_q balíčku.

- [ ] **Step 1: Spusť migrace**

```bash
cd backend
python manage.py migrate
```

Očekávané: uvidíš řádky jako:
```
  Applying django_q.0001_initial... OK
  Applying django_q.0002_...      OK
```

- [ ] **Step 2: Ověř Django check**

```bash
python manage.py check
```

Očekávané: `System check identified no issues (0 silenced).`

Django_q migrace jsou součástí balíčku — žádné soubory se nepřidají do gitu. Commit není potřeba.

---

## Task 3: Management command reset_stale_import_jobs (TDD)

**Files:**
- Create: `backend/dashboard/management/__init__.py`
- Create: `backend/dashboard/management/commands/__init__.py`
- Create: `backend/dashboard/management/commands/reset_stale_import_jobs.py`
- Create: `backend/dashboard/tests/test_garmin_tasks.py`

- [ ] **Step 1: Vytvoř adresářovou strukturu**

```bash
mkdir -p backend/dashboard/management/commands
touch backend/dashboard/management/__init__.py
touch backend/dashboard/management/commands/__init__.py
```

- [ ] **Step 2: Napiš failing test**

Vytvoř `backend/dashboard/tests/test_garmin_tasks.py`:

```python
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from accounts.models import ImportJob


@pytest.fixture
def garmin_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="tester@example.com",
        email="tester@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def import_job(garmin_user):
    return ImportJob.objects.create(
        user=garmin_user,
        kind=ImportJob.Kind.GARMIN_SYNC,
        status=ImportJob.Status.QUEUED,
        window="last_7_days",
        message="Waiting.",
    )


def test_reset_stale_import_jobs_marks_running_as_error(garmin_user):
    """reset_stale_import_jobs musí přepsat RUNNING joby na ERROR."""
    from django.core.management import call_command

    job = ImportJob.objects.create(
        user=garmin_user,
        kind=ImportJob.Kind.GARMIN_SYNC,
        status=ImportJob.Status.RUNNING,
        window="last_7_days",
        message="Running.",
    )
    call_command("reset_stale_import_jobs")
    job.refresh_from_db()
    assert job.status == ImportJob.Status.ERROR
    assert job.message == "Worker restarted"


def test_reset_stale_import_jobs_ignores_non_running(garmin_user):
    """reset_stale_import_jobs nesmí měnit joby mimo stav RUNNING."""
    from django.core.management import call_command

    job = ImportJob.objects.create(
        user=garmin_user,
        kind=ImportJob.Kind.GARMIN_SYNC,
        status=ImportJob.Status.QUEUED,
        window="last_7_days",
        message="Waiting.",
    )
    call_command("reset_stale_import_jobs")
    job.refresh_from_db()
    assert job.status == ImportJob.Status.QUEUED


def test_execute_garmin_sync_job_marks_success(import_job):
    """Job musí skončit SUCCESS po úspěšném sync."""
    from dashboard.services.tasks import _execute_garmin_sync_job

    with patch("dashboard.services.tasks.sync_garmin_for_user") as mock_sync, \
         patch("dashboard.services.imports.audit_garmin"):
        mock_sync.return_value = (5, 2, MagicMock())
        _execute_garmin_sync_job(import_job.id)

    import_job.refresh_from_db()
    assert import_job.status == ImportJob.Status.SUCCESS
    assert import_job.imported_count == 5
    assert import_job.skipped_count == 2


@pytest.mark.django_db
def test_execute_garmin_sync_job_nonexistent_id():
    """Task s neexistujícím job ID musí tiše skončit bez výjimky."""
    from dashboard.services.tasks import _execute_garmin_sync_job
    _execute_garmin_sync_job(999999)


def test_enqueue_garmin_sync_job_calls_async_task(import_job):
    """enqueue_garmin_sync_job musí volat async_task s _execute_garmin_sync_job."""
    from dashboard.services.tasks import enqueue_garmin_sync_job, _execute_garmin_sync_job

    with patch("dashboard.services.tasks.async_task") as mock_async_task:
        enqueue_garmin_sync_job(import_job.id)
        mock_async_task.assert_called_once_with(_execute_garmin_sync_job, import_job.id)
```

- [ ] **Step 3: Spusť testy — ověř že failují správně**

```bash
cd backend
python -m pytest dashboard/tests/test_garmin_tasks.py -v
```

Očekávané: `test_reset_stale_import_jobs_*` failují s `CommandError` nebo `ModuleNotFoundError` (command neexistuje). `test_enqueue_garmin_sync_job_calls_async_task` failuje protože `async_task` v tasks.py neexistuje.

- [ ] **Step 4: Implementuj management command**

Vytvoř `backend/dashboard/management/commands/reset_stale_import_jobs.py`:

```python
from django.core.management.base import BaseCommand

from accounts.models import ImportJob


class Command(BaseCommand):
    help = "Přepíše ImportJoby ve stavu RUNNING na ERROR (cleanup po restartu workeru)."

    def handle(self, *args, **options):
        updated = ImportJob.objects.filter(
            status=ImportJob.Status.RUNNING,
        ).update(
            status=ImportJob.Status.ERROR,
            message="Worker restarted",
        )
        self.stdout.write(f"Reset {updated} stale import job(s).")
```

- [ ] **Step 5: Spusť testy pro management command — ověř že prochází**

```bash
cd backend
python -m pytest dashboard/tests/test_garmin_tasks.py::test_reset_stale_import_jobs_marks_running_as_error dashboard/tests/test_garmin_tasks.py::test_reset_stale_import_jobs_ignores_non_running -v
```

Očekávané: oba testy PASS.

- [ ] **Step 6: Commit management command**

```bash
git add backend/dashboard/management/ backend/dashboard/tests/test_garmin_tasks.py
git commit -m "feat: management command reset_stale_import_jobs + testy"
```

---

## Task 4: Migrace tasks.py na django-q2 API (TDD)

**Files:**
- Modify: `backend/dashboard/services/tasks.py`
- Delete: `backend/dashboard/tests/test_celery_tasks.py`

- [ ] **Step 1: Spusť enqueue test — ověř že failuje**

```bash
cd backend
python -m pytest dashboard/tests/test_garmin_tasks.py::test_enqueue_garmin_sync_job_calls_async_task -v
```

Očekávané: FAIL — `async_task` není importován v `tasks.py`, mock na `dashboard.services.tasks.async_task` selže.

- [ ] **Step 2: Aktualizuj tasks.py**

Celý obsah `backend/dashboard/services/tasks.py` nahraď:

```python
from __future__ import annotations

import logging

from django_q.tasks import async_task
from django.utils import timezone

from .imports import import_fit_for_user, sync_garmin_for_user

logger = logging.getLogger(__name__)


def run_fit_import(user, uploaded_file):
    """FIT import — synchronní (soubory jsou malé)."""
    return import_fit_for_user(user, uploaded_file)


def run_garmin_sync(user, *, window: str):
    """Garmin sync — synchronní (legacy non-AJAX fallback)."""
    return sync_garmin_for_user(user, window=window)


def enqueue_garmin_sync_job(import_job_id: int) -> None:
    """Odešle Garmin sync job do django-q2 fronty."""
    async_task(_execute_garmin_sync_job, import_job_id)


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

- [ ] **Step 3: Spusť všechny testy v novém souboru**

```bash
cd backend
python -m pytest dashboard/tests/test_garmin_tasks.py -v
```

Očekávané: 5 testů PASS.

- [ ] **Step 4: Smaž starý test soubor**

```bash
git rm backend/dashboard/tests/test_celery_tasks.py
```

- [ ] **Step 5: Spusť celou backend test suite**

```bash
cd backend
python -m pytest -x
```

Očekávané: všechny testy projdou, žádná Celery-related chyba.

- [ ] **Step 6: Commit**

```bash
git add backend/dashboard/services/tasks.py backend/dashboard/tests/test_garmin_tasks.py
git commit -m "feat: migruj Garmin task z Celery na django-q2"
```

---

## Task 5: Docker Compose cleanup

**Files:**
- Modify: `docker-compose.yml`
- Modify: `docker-compose.prod.yml`

- [ ] **Step 1: Aktualizuj docker-compose.yml**

Celý obsah `docker-compose.yml` nahraď:

```yaml
services:
  db:
    image: postgres:16
    container_name: endurobuddy-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: endurobuddy
      POSTGRES_USER: endurobuddy
      POSTGRES_PASSWORD: endurobuddy_password
    ports:
      - "5432:5432"
    volumes:
      - endurobuddy_pgdata:/var/lib/postgresql/data
    networks:
      - backend

  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: endurobuddy-web
    restart: unless-stopped
    depends_on:
      - db
    environment:
      POSTGRES_HOST: db
      DJANGO_DEBUG: "true"
    env_file:
      - .env
    ports:
      - "8000:8000"
    command: ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
    volumes:
      - ./backend:/app/backend
    networks:
      - backend

  qcluster:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: endurobuddy-qcluster
    restart: unless-stopped
    command: sh -c "cd /app/backend && python manage.py reset_stale_import_jobs && python manage.py qcluster"
    depends_on:
      - db
    env_file:
      - .env
    environment:
      POSTGRES_HOST: db
      DJANGO_DEBUG: "true"
    volumes:
      - ./backend:/app/backend
    networks:
      - backend

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

  nginx:
    build:
      context: ./nginx
    container_name: endurobuddy-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - web
      - nuxt
    networks:
      - backend

volumes:
  endurobuddy_pgdata:

networks:
  backend:
```

- [ ] **Step 2: Aktualizuj docker-compose.prod.yml**

V `docker-compose.prod.yml`:

1. Smaž celý `redis:` blok (řádky 15–24).
2. V `web:` sekci: odeber `- redis` z `depends_on` (pokud existuje).
3. Smaž celý `celery-worker:` blok (řádky 61–79).
4. Smaž celý `celery-beat:` blok (řádky 81–99).
5. Přidej `qcluster:` service za `web:` service:

```yaml
  qcluster:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: endurobuddy-qcluster
    restart: unless-stopped
    command: sh -c "cd /app/backend && python manage.py reset_stale_import_jobs && python manage.py qcluster"
    depends_on:
      - db
    env_file:
      - .env
    environment:
      POSTGRES_HOST: db
      POSTGRES_PORT: 5432
      DJANGO_DEBUG: "false"
      DJANGO_USE_HTTPS: "true"
    networks:
      - backend
```

6. V sekci `volumes:` smaž `endurobuddy_redis:`.

- [ ] **Step 3: Ověř validitu compose souborů**

```bash
docker compose config --quiet
docker compose -f docker-compose.prod.yml config --quiet
```

Očekávané: žádné chyby ani varování.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml docker-compose.prod.yml
git commit -m "chore: odeber Redis + Celery services, přidej qcluster"
```

---

## Finální ověření

- [ ] **Spusť celou backend test suite**

```bash
cd backend
python -m pytest -v
```

Očekávané: všechny testy zelené, žádný import Celery, žádný `redis` v chybách.

- [ ] **Ověř Django check**

```bash
cd backend
python manage.py check
```

Očekávané: `System check identified no issues (0 silenced).`
