# Spec: Migrace Celery + Redis → django-q2

**Datum:** 2026-05-04  
**Větev:** main  
**Stav:** schváleno, čeká na implementaci

---

## Kontext

EnduroBuddy provozuje Celery + Redis kvůli jedinému async tasku: spuštění Garmin Connect syncu na pozadí (`execute_garmin_sync_job`). Redis slouží pouze jako Celery broker a result backend — žádné jiné využití (sessions, caching, WebSocket channels). `django-celery-beat` je nainstalovaný, ale žádný periodický task není naplánovaný. `django-celery-results` ukládá výsledky do Redis, ale kód je nikdy nečte (progress sleduje `ImportJob` model v DB).

Cíl: nahradit Redis + Celery za `django-q2`, který používá PostgreSQL jako broker. Eliminovat Redis service, celery-worker a celery-beat z docker-compose.

---

## Architektura

```
Před:  web + redis + celery-worker + celery-beat
Po:    web + qcluster
```

`qcluster` je Django management command (`python manage.py qcluster`) spouštěný jako samostatný Docker service (stejný image jako `web`, žádný nový Dockerfile). PostgreSQL funguje jako task broker — žádná nová infrastruktura.

Periodický scheduler se **nenakonfiguruje** — všechny tasky jsou on-demand. Scheduler lze přidat kdykoliv v budoucnu úpravou `Q_CLUSTER` konfigurace bez změny infrastruktury.

---

## Konfigurace django-q2

```python
Q_CLUSTER = {
    "name": "endurobuddy",
    "workers": 1,           # jeden Garmin sync najednou stačí
    "timeout": 300,         # max 5 minut (stejný limit jako dnes)
    "retry": 0,             # žádné automatické retry (konzistentní s max_retries=0)
    "save_limit": 0,        # výsledky neukládat — progress sleduje ImportJob
    "orm": "default",       # PostgreSQL jako broker
}
```

`django_q` přidat do `INSTALLED_APPS`. Tabulky vytvoří migrace.

---

## Startup cleanup

Při restartu `qcluster` procesu mohou existovat `ImportJob` záznamy ve stavu `"running"` z přerušeného syncu. Tyto záznamy se přepíší na `"failed"` se zprávou `"Worker restarted"`.

Implementace jako management command `reset_stale_import_jobs`. Spouštění jako součást qcluster service command:

```
sh -c "python manage.py reset_stale_import_jobs && python manage.py qcluster"
```

Command je idempotentní. Spouští se jen při startu qcluster, ne při startu web service — nesnižuje to riziko interference s legitimně běžícím jobem při restartu web kontejneru.

---

## Změny kódu

| Soubor | Změna |
|--------|-------|
| `backend/pyproject.toml` | odebrat `celery[redis]`, `django-celery-beat`, `django-celery-results`, `redis`; přidat `django-q2` |
| `backend/config/settings.py` | odebrat `CELERY_*` blok; přidat `Q_CLUSTER` a `django_q` do `INSTALLED_APPS` |
| `backend/config/celery.py` | smazat |
| `backend/config/__init__.py` | odebrat import Celery app |
| `backend/dashboard/services/tasks.py` | odebrat `@shared_task` dekorátor (django-q2 nepotřebuje dekorátory); `enqueue_garmin_sync_job` volá `async_task(_execute_garmin_sync_job, import_job_id)` místo `.delay()` |
| `backend/dashboard/management/commands/reset_stale_import_jobs.py` | nový command — cleanup stale ImportJobů |
| `backend/dashboard/tests/test_celery_tasks.py` | přepsat pro django-q2 API (přejmenovat na `test_garmin_tasks.py`) |
| `docker-compose.yml` | odebrat `redis`, `celery-worker`, `celery-beat`; přidat `qcluster` service |
| `docker-compose.prod.yml` | stejné úpravy jako dev compose |

---

## Testování

Tři testy v `test_garmin_tasks.py`:

1. **Task execution** — volá `_execute_garmin_sync_job(import_job_id)` synchronně, ověří stav `ImportJob` po dokončení. Žádný mock brokeru.
2. **Enqueue** — mock `async_task`, ověří že `enqueue_garmin_sync_job()` ho volá s `_execute_garmin_sync_job` jako prvním argumentem a `import_job_id` jako druhým.
3. **Startup cleanup** — zavolá `reset_stale_import_jobs` command, ověří že `ImportJob` ve stavu `"running"` se přepíše na `"failed"`.

---

## Co se nemění

- `ImportJob` model a polling mechanismus — beze změny
- `run_fit_import()` a `run_garmin_sync()` synchronní funkce — beze změny
- API endpointy v `api/views/imports.py` — beze změny (volají `enqueue_garmin_sync_job()`)
- Frontend polling logika — beze změny

---

## Mimo scope

- Periodické tasky (noční sync, email digest) — přidají se samostatně až bude potřeba
- Změna `ImportJob` progress mechanismu
- Caching, sessions, WebSocket channels — Redis se pro tyto účely nepoužíval
