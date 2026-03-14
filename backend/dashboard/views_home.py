from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from dashboard.api import json_error
from accounts.models import CoachAthlete, CoachJoinRequest, GarminConnection, GarminSyncAudit, ImportJob
from accounts.services.garmin_secret_store import GarminSecretStoreError
from activities.models import Activity, ActivityImportLedger
from activities.services.garmin_importer import GarminImportError
from dashboard.services.imports import GARMIN_RANGE_OPTIONS, audit_garmin, sync_garmin_week_for_user
from dashboard.services.month_cards import build_month_cards_for_athlete, is_coach, resolve_week_for_day
from dashboard.services.tasks import enqueue_garmin_sync_job
from dashboard.texts import ApiText, DashboardText
from training.models import CompletedTraining, PlannedTraining, TrainingWeek

from .handlers.home_actions import handle_home_post
from .views_shared import maybe_add_test_notifications, sanitize_legend_state

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


def _is_admin_like(user) -> bool:
    return (
        user.username.lower() == "admin"
        or bool(getattr(user, "is_superuser", False))
        or bool(getattr(user, "is_staff", False))
    )


def _parse_remove_week_completed_token(raw_value: str) -> tuple[int, int, int] | None:
    raw = (raw_value or "").strip()
    if not raw:
        return None
    parts = [part.strip() for part in raw.split("/") if part.strip()]
    if len(parts) == 2 and all(part.isdigit() for part in parts):
        month, week_index = (int(parts[0]), int(parts[1]))
        return 2026, month, week_index
    if len(parts) == 3 and all(part.isdigit() for part in parts):
        year, month, week_index = (int(parts[0]), int(parts[1]), int(parts[2]))
        return year, month, week_index
    return None


def _maybe_remove_admin_week_completed(request):
    if not settings.DEBUG or "remove_week_completed" not in request.GET:
        return None
    if not _is_admin_like(request.user):
        messages.error(request, DashboardText.ADMIN_ONLY_REMOVE_WEEK)
        return redirect("dashboard_home")

    parsed = _parse_remove_week_completed_token(request.GET.get("remove_week_completed") or "")
    if parsed is None:
        messages.error(request, DashboardText.REMOVE_WEEK_USAGE)
        return redirect("dashboard_home")

    year, month, week_index = parsed
    admin_user = get_user_model().objects.filter(username="admin").first()
    if admin_user is None:
        messages.error(request, DashboardText.ADMIN_USER_NOT_FOUND)
        return redirect("dashboard_home")

    week = (
        TrainingWeek.objects.filter(
            training_month__athlete=admin_user,
            training_month__year=year,
            training_month__month=month,
            week_index=week_index,
        )
        .order_by("id")
        .first()
    )
    if week is None:
        messages.error(request, DashboardText.week_not_found(year=year, month=month, week_index=week_index))
        return redirect("dashboard_home")

    planned_ids = list(PlannedTraining.objects.filter(week=week).values_list("id", flat=True))
    deleted_completed_count = CompletedTraining.objects.filter(planned_id__in=planned_ids).count()
    deleted_activity_count = Activity.objects.filter(athlete=admin_user, planned_training_id__in=planned_ids).count()
    CompletedTraining.objects.filter(planned_id__in=planned_ids).delete()
    Activity.objects.filter(athlete=admin_user, planned_training_id__in=planned_ids).delete()
    messages.success(
        request,
        DashboardText.removed_admin_week(
            year=year,
            month=month,
            week_index=week_index,
            completed_count=deleted_completed_count,
            activity_count=deleted_activity_count,
        ),
    )
    return redirect("dashboard_home")


def _maybe_run_test_garmin_cleanup(request):
    if not settings.DEBUG or "test_garmin_import" not in request.GET:
        return None
    flag = (request.GET.get("test_garmin_import") or "").strip().lower()
    if flag and flag not in {"1", "true", "yes", "on"}:
        return None
    if not _is_admin_like(request.user):
        messages.error(request, DashboardText.ADMIN_ONLY_TEST_IMPORT)
        return redirect("dashboard_home")

    admin_user = get_user_model().objects.filter(username="admin").first()
    if admin_user is None:
        messages.error(request, DashboardText.ADMIN_USER_NOT_FOUND)
        return redirect("dashboard_home")

    target_year = date.today().year
    from_day = date(target_year, 3, 2)
    to_day = date(target_year, 3, 8)
    planned_ids = list(
        PlannedTraining.objects.filter(
            week__training_month__athlete=admin_user,
            date__range=(from_day, to_day),
        ).values_list("id", flat=True)
    )
    deleted_activity_count = Activity.objects.filter(athlete=admin_user, planned_training_id__in=planned_ids).delete()[0]
    deleted_activity_count += Activity.objects.filter(athlete=admin_user, started_at__date__range=(from_day, to_day)).delete()[0]
    deleted_planned_count = PlannedTraining.objects.filter(id__in=planned_ids).delete()[0]
    deleted_ledger_count = ActivityImportLedger.objects.filter(athlete=admin_user).delete()[0]

    recreated_week = resolve_week_for_day(admin_user, from_day)
    day_labels = ["Po", "Ut", "St", "Ct", "Pa", "So", "Ne"]
    existing_days = set(
        PlannedTraining.objects.filter(
            week=recreated_week,
            date__range=(from_day, to_day),
            order_in_day=1,
        ).values_list("date", flat=True)
    )
    recreated_days = []
    for offset, day_label in enumerate(day_labels):
        run_day = from_day + timedelta(days=offset)
        if run_day in existing_days:
            continue
        recreated_days.append(
            PlannedTraining(
                week=recreated_week,
                date=run_day,
                order_in_day=1,
                day_label=day_label,
                title="",
                notes="",
            )
        )
    if recreated_days:
        PlannedTraining.objects.bulk_create(recreated_days, batch_size=50)

    messages.success(
        request,
        DashboardText.test_cleanup_done(
            from_day=from_day,
            to_day=to_day,
            deleted_planned_count=deleted_planned_count,
            deleted_activity_count=deleted_activity_count,
            deleted_ledger_count=deleted_ledger_count,
            recreated_week_index=recreated_week.week_index,
            recreated_days_count=len(recreated_days),
        ),
    )
    return redirect("dashboard_home")


@login_required
def home(request):
    if request.method == "POST":
        return handle_home_post(
            request,
            logger=logger,
            queue_garmin_sync_job_for_user=_queue_garmin_sync_job_for_user,
        )

    cleanup_response = _maybe_run_test_garmin_cleanup(request)
    if cleanup_response is not None:
        return cleanup_response
    remove_completed_response = _maybe_remove_admin_week_completed(request)
    if remove_completed_response is not None:
        return remove_completed_response

    month_cards = build_month_cards_for_athlete(athlete=request.user, language_code=request.LANGUAGE_CODE)
    garmin_connection = GarminConnection.objects.filter(user=request.user, is_active=True).first()
    pending_coach_requests = list(
        CoachJoinRequest.objects.select_related("coach")
        .filter(athlete=request.user, status=CoachJoinRequest.Status.PENDING)
        .order_by("-created_at")
    )
    approved_coach_links = list(
        CoachAthlete.objects.select_related("coach")
        .filter(athlete=request.user)
        .order_by("coach__username", "coach__id")
    )
    maybe_add_test_notifications(request)
    return render(
        request,
        "dashboard/dashboard.html",
        {
            "month_cards": month_cards,
            "month_state_key": request.user.id,
            "garmin_connection": garmin_connection,
            "is_coach": is_coach(request.user),
            "plan_editable": True,
            "plan_update_url": reverse("athlete_update_planned_training"),
            "add_phase_url": reverse("athlete_add_second_phase_training"),
            "remove_phase_url": reverse("athlete_remove_second_phase_training"),
            "completed_editable": True,
            "completed_lock_linked_activity": False,
            "completed_update_url": reverse("athlete_update_completed_training"),
            "garmin_week_sync_enabled": True,
            "garmin_week_sync_url": reverse("garmin_sync_week"),
            "garmin_week_sync_connected": bool(garmin_connection),
            "add_month_enabled": True,
            "add_month_action": "add_next_month_self",
            "add_month_athlete_id": None,
            "pending_coach_requests": pending_coach_requests,
            "approved_coach_links": approved_coach_links,
            "legend_state_json": json.dumps(sanitize_legend_state(getattr(request.user.profile, "legend_state", {}))),
            "legend_editable": True,
            "legend_update_url": reverse("athlete_update_legend_state"),
            "show_garmin_match_debug": settings.DEBUG and _is_admin_like(request.user),
        },
    )


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
