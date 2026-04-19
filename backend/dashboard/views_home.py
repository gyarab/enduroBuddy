from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q
from django.utils import timezone

from dashboard.api import json_error
from accounts.models import AppNotification, GarminConnection, GarminSyncAudit, ImportJob
from accounts.services.notifications import mark_notifications_read, serialize_notification
from accounts.services.garmin_secret_store import GarminSecretStoreError
from activities.services.garmin_importer import GarminImportError
from dashboard.services.imports import GARMIN_RANGE_OPTIONS, audit_garmin, sync_garmin_week_for_user
from dashboard.services.tasks import enqueue_garmin_sync_job
from dashboard.texts import ApiText, DashboardText
from .views_shared import sanitize_legend_state

logger = logging.getLogger(__name__)


def _job_status_label(status: str) -> str:
    return {
        ImportJob.Status.QUEUED: "Queued",
        ImportJob.Status.RUNNING: "Running",
        ImportJob.Status.SUCCESS: "Done",
        ImportJob.Status.ERROR: "Error",
    }.get(status, status or "Unknown")


def _job_progress_percent(job: ImportJob) -> int:
    if job.status == ImportJob.Status.SUCCESS:
        return 100
    if job.status == ImportJob.Status.ERROR:
        return min(99, max(0, int((job.processed_count / max(1, job.total_count)) * 100))) if job.total_count else 0
    if job.status == ImportJob.Status.QUEUED:
        return 0
    if job.total_count > 0:
        return min(99, max(0, int((job.processed_count / job.total_count) * 100)))
    return 10 if (job.started_at or job.status == ImportJob.Status.RUNNING) else 0


def _serialize_import_job(job: ImportJob) -> dict:
    done = job.status in {ImportJob.Status.SUCCESS, ImportJob.Status.ERROR}
    return {
        "id": job.id,
        "status": job.status,
        "status_label": _job_status_label(job.status),
        "progress_percent": _job_progress_percent(job),
        "window": job.window,
        "message": job.message,
        "total_count": job.total_count,
        "processed_count": job.processed_count,
        "imported_count": job.imported_count,
        "skipped_count": job.skipped_count,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "done": done,
    }


def _queue_garmin_sync_job_for_user(*, user, selected_range: str) -> tuple[ImportJob, bool]:
    existing_job = (
        ImportJob.objects.filter(
            user=user,
            kind=ImportJob.Kind.GARMIN_SYNC,
            status__in=[ImportJob.Status.QUEUED, ImportJob.Status.RUNNING],
        )
        .order_by("-id")
        .first()
    )
    if existing_job:
        return existing_job, False

    job = ImportJob.objects.create(
        user=user,
        kind=ImportJob.Kind.GARMIN_SYNC,
        status=ImportJob.Status.QUEUED,
        window=selected_range,
        message="Synchronizace Garmin ceka na spusteni.",
    )
    enqueue_garmin_sync_job(job.id)
    return job, True


@login_required
def athlete_update_legend_state(request):
    if request.method != "POST":
        return json_error(ApiText.METHOD_NOT_ALLOWED, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    next_state = sanitize_legend_state(payload.get("state"))
    profile = request.user.profile
    profile.legend_state = next_state
    profile.save(update_fields=["legend_state"])
    return JsonResponse({"ok": True, "state": next_state})


@login_required
@require_POST
def garmin_sync_start(request):
    if not settings.GARMIN_SYNC_ENABLED:
        return json_error(ApiText.GARMIN_SYNC_DISABLED, status=503)
    selected_range = request.POST.get("garmin_range", "last_30_days")
    if selected_range not in GARMIN_RANGE_OPTIONS:
        selected_range = "last_30_days"
    if not GarminConnection.objects.filter(user=request.user, is_active=True).exists():
        return json_error(ApiText.GARMIN_NOT_CONNECTED, status=400)

    try:
        job, is_new_job = _queue_garmin_sync_job_for_user(user=request.user, selected_range=selected_range)
    except Exception:
        logger.exception("Failed to queue Garmin sync for user_id=%s", request.user.id)
        return json_error(ApiText.GARMIN_SYNC_START_FAILED, status=500)

    return JsonResponse(
        {
            "ok": True,
            "job_id": job.id,
            "status": job.status,
            "status_label": _job_status_label(job.status),
            "progress_percent": _job_progress_percent(job),
            "already_running": not is_new_job,
            "message": job.message,
        }
    )


@login_required
@require_POST
def garmin_sync_week(request):
    if not settings.GARMIN_SYNC_ENABLED:
        return json_error(ApiText.GARMIN_SYNC_DISABLED, status=503)
    raw_week_start = (request.POST.get("week_start") or "").strip()
    try:
        week_start = date.fromisoformat(raw_week_start)
    except ValueError:
        return json_error(ApiText.INVALID_WEEK_START, status=400)
    if not GarminConnection.objects.filter(user=request.user, is_active=True).exists():
        return json_error(ApiText.GARMIN_NOT_CONNECTED, status=400)

    normalized_week_start = week_start - timedelta(days=week_start.weekday())
    if normalized_week_start > timezone.localdate():
        return json_error(ApiText.GARMIN_WEEK_UNAVAILABLE, status=400)

    window_label = f"week:{normalized_week_start.isoformat()}"
    try:
        replaced, untouched, connection = sync_garmin_week_for_user(request.user, week_start=normalized_week_start)
        audit_garmin(
            user=request.user,
            connection=connection,
            action=GarminSyncAudit.Action.SYNC,
            status=GarminSyncAudit.Status.SUCCESS,
            window=window_label,
            imported_count=replaced,
            skipped_count=untouched,
            message="Garmin week sync finished.",
        )
    except (GarminImportError, GarminSecretStoreError) as exc:
        audit_garmin(
            user=request.user,
            action=GarminSyncAudit.Action.SYNC,
            status=GarminSyncAudit.Status.ERROR,
            window=window_label,
            message=str(exc),
        )
        return json_error(f"{ApiText.GARMIN_SYNC_FAILED}: {exc}", status=400)
    except Exception:
        logger.exception("Garmin week sync failed for user_id=%s week_start=%s", request.user.id, normalized_week_start)
        audit_garmin(
            user=request.user,
            action=GarminSyncAudit.Action.SYNC,
            status=GarminSyncAudit.Status.ERROR,
            window=window_label,
            message="Unexpected Garmin week sync error.",
        )
        return json_error(ApiText.GARMIN_SYNC_FAILED, status=500)

    return JsonResponse(
        {
            "ok": True,
            "status": "SUCCESS",
            "status_label": "Done",
            "progress_percent": 100,
            "week_start": normalized_week_start.isoformat(),
            "replaced_count": replaced,
            "untouched_count": untouched,
            "imported_count": replaced,
            "skipped_count": untouched,
            "message": DashboardText.garmin_week_synced(replaced=replaced, untouched=untouched),
        }
    )


@login_required
@require_GET
def import_job_status(request, job_id: int):
    job = (
        ImportJob.objects.filter(
            id=job_id,
            user=request.user,
            kind=ImportJob.Kind.GARMIN_SYNC,
        )
        .order_by("-id")
        .first()
    )
    if job is None:
        return json_error(ApiText.JOB_NOT_FOUND, status=404)

    return JsonResponse({"ok": True, "job": _serialize_import_job(job)})


@login_required
@require_GET
def notification_poll(request):
    notifications_qs = AppNotification.objects.filter(recipient=request.user, read_at__isnull=True)
    notifications_qs = notifications_qs.exclude(
        Q(dedupe_key__startswith="test-live-") | Q(text__startswith="Test live:")
    )
    notifications = list(
        notifications_qs.select_related("actor").order_by("-created_at", "-id")[:20]
    )
    return JsonResponse(
        {
            "ok": True,
            "notifications": [serialize_notification(notification) for notification in notifications],
        }
    )


@login_required
@require_POST
def notification_mark_read(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    notification_ids = payload.get("notification_ids")
    if not isinstance(notification_ids, list):
        return json_error("notification_ids must be a list.", status=400)

    marked_count = mark_notifications_read(recipient=request.user, notification_ids=notification_ids)
    return JsonResponse({"ok": True, "marked_count": marked_count})
