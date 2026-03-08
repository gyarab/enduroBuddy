from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable
import logging

from django.conf import settings
from django.utils import timezone

from .imports import import_fit_for_user, sync_garmin_for_user


_executor = ThreadPoolExecutor(max_workers=2)
logger = logging.getLogger(__name__)


def _mode() -> str:
    return str(getattr(settings, "IMPORT_TASK_MODE", "inline") or "inline").lower()


def _run_or_enqueue(func: Callable[..., Any], *args, **kwargs):
    if _mode() == "async":
        _executor.submit(func, *args, **kwargs)
        return None
    return func(*args, **kwargs)


def run_fit_import(user, uploaded_file):
    return _run_or_enqueue(import_fit_for_user, user, uploaded_file)


def run_garmin_sync(user, *, window: str):
    return _run_or_enqueue(sync_garmin_for_user, user, window=window)


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


def enqueue_garmin_sync_job(import_job_id: int) -> None:
    _executor.submit(_execute_garmin_sync_job, import_job_id)
