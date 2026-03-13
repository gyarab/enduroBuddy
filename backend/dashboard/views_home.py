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

from accounts.models import CoachAthlete, CoachJoinRequest, GarminConnection, GarminSyncAudit, ImportJob
from accounts.services.garmin_secret_store import GarminSecretStoreError
from activities.models import Activity, ActivityImportLedger
from activities.services.garmin_importer import GarminImportError
from dashboard.services.imports import (
    GARMIN_RANGE_OPTIONS,
    audit_garmin,
    connect_garmin_for_user,
    revoke_garmin_for_user,
    sync_garmin_week_for_user,
)
from dashboard.services.month_cards import add_next_month_for_athlete, build_month_cards_for_athlete, is_coach, resolve_week_for_day
from dashboard.services.tasks import enqueue_garmin_sync_job, run_fit_import, run_garmin_sync
from training.models import CompletedTraining, PlannedTraining, TrainingWeek
from .views_shared import _resolve_coach_from_code, maybe_add_test_notifications, sanitize_legend_state

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
        message="Synchronizace Garmin čeká na spuštění.",
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
    if not settings.DEBUG:
        return None
    if "remove_week_completed" not in request.GET:
        return None

    if not _is_admin_like(request.user):
        messages.error(request, "remove_week_completed je povoleny jen pro uzivatele admin.")
        return redirect("dashboard_home")

    parsed = _parse_remove_week_completed_token(request.GET.get("remove_week_completed") or "")
    if parsed is None:
        messages.error(request, "Pouzij remove_week_completed=3/1 nebo remove_week_completed=2026/3/1.")
        return redirect("dashboard_home")

    year, month, week_index = parsed
    User = get_user_model()
    admin_user = User.objects.filter(username="admin").first()
    if admin_user is None:
        messages.error(request, "Uzivatel admin nebyl nalezen.")
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
        messages.error(request, f"Tyden {week_index} v {month}/{year} nebyl nalezen.")
        return redirect("dashboard_home")

    planned_ids = list(
        PlannedTraining.objects.filter(
            week=week,
        ).values_list("id", flat=True)
    )
    deleted_completed_count = CompletedTraining.objects.filter(planned_id__in=planned_ids).count()
    deleted_activity_count = Activity.objects.filter(
        athlete=admin_user,
        planned_training_id__in=planned_ids,
    ).count()
    CompletedTraining.objects.filter(planned_id__in=planned_ids).delete()
    Activity.objects.filter(
        athlete=admin_user,
        planned_training_id__in=planned_ids,
    ).delete()

    messages.success(
        request,
        (
            f"Vymazano Splneno pro admin {month}/{year}, tyden {week_index}: "
            f"completed {deleted_completed_count}, activity {deleted_activity_count}."
        ),
    )
    return redirect("dashboard_home")


def _maybe_run_test_garmin_cleanup(request):
    if not settings.DEBUG:
        return None
    if "test_garmin_import" not in request.GET:
        return None
    flag = (request.GET.get("test_garmin_import") or "").strip().lower()
    if flag and flag not in {"1", "true", "yes", "on"}:
        return None

    if not _is_admin_like(request.user):
        messages.error(request, "test_garmin_import je povoleny jen pro uzivatele admin.")
        return redirect("dashboard_home")

    User = get_user_model()
    admin_user = User.objects.filter(username="admin").first()
    if admin_user is None:
        messages.error(request, "Uzivatel admin nebyl nalezen.")
        return redirect("dashboard_home")

    target_year = date.today().year
    from_day = date(target_year, 3, 2)
    to_day = date(target_year, 3, 8)

    planned_ids_qs = PlannedTraining.objects.filter(
        week__training_month__athlete=admin_user,
        date__range=(from_day, to_day),
    ).values_list("id", flat=True)
    planned_ids = list(planned_ids_qs)

    deleted_activity_count = Activity.objects.filter(
        athlete=admin_user,
        planned_training_id__in=planned_ids,
    ).delete()[0]
    deleted_activity_count += Activity.objects.filter(
        athlete=admin_user,
        started_at__date__range=(from_day, to_day),
    ).delete()[0]

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
        (
            f"Test cleanup hotov ({from_day:%d.%m.%Y} - {to_day:%d.%m.%Y}): "
            f"planned/completed {deleted_planned_count}, activity {deleted_activity_count}, ledger {deleted_ledger_count}. "
            f"Tyden znovu vytvoren (index {recreated_week.week_index}, dnu {len(recreated_days)})."
        ),
    )
    return redirect("dashboard_home")


@login_required
def home(request):
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "request_coach_by_code":
            coach_code = (request.POST.get("coach_code") or "").strip().upper()
            coach_user = _resolve_coach_from_code(coach_code)
            if coach_user is None:
                messages.error(request, "Kod trenera nebyl nalezen.")
                return redirect("dashboard_home")
            if coach_user.id == request.user.id:
                messages.error(request, "Nemuzes zadat vlastni kod trenera.")
                return redirect("dashboard_home")
            if CoachAthlete.objects.filter(coach=coach_user, athlete=request.user).exists():
                messages.info(request, "Uz jsi u tohoto trenera prirazeny.")
                return redirect("dashboard_home")
            already_pending = CoachJoinRequest.objects.filter(
                coach=coach_user,
                athlete=request.user,
                status=CoachJoinRequest.Status.PENDING,
            ).exists()
            if already_pending:
                messages.info(request, "Pozadavek uz ceka na schvaleni.")
                return redirect("dashboard_home")
            CoachJoinRequest.objects.create(
                coach=coach_user,
                athlete=request.user,
                status=CoachJoinRequest.Status.PENDING,
            )
            messages.success(request, "Pozadavek byl odeslan trenerovi ke schvaleni.")
            return redirect("dashboard_home")

        if action == "add_next_month_self":
            month_created, weeks_created, days_created = add_next_month_for_athlete(athlete=request.user)
            if month_created:
                messages.success(request, f"Pridán nový mesíc: týdny {weeks_created}, dny {days_created}.")
            else:
                messages.info(request, f"Mesíc už existoval, doplneno: týdny {weeks_created}, dny {days_created}.")
            return redirect("dashboard_home")

        source = request.POST.get("import_source", "fit_upload")

        if source == "garmin_connect":
            email = (request.POST.get("garmin_email") or "").strip()
            password = (request.POST.get("garmin_password") or "").strip()
            if not email or not password:
                messages.error(request, "Enter Garmin email and password.")
                return redirect("dashboard_home")
            try:
                connection = connect_garmin_for_user(request.user, email=email, password=password)
                audit_garmin(
                    user=request.user,
                    connection=connection,
                    action=GarminSyncAudit.Action.CONNECT,
                    status=GarminSyncAudit.Status.SUCCESS,
                    message="Garmin account connected.",
                )
                messages.success(request, "Garmin account connected.")
            except (GarminImportError, GarminSecretStoreError) as exc:
                audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.CONNECT,
                    status=GarminSyncAudit.Status.ERROR,
                    message=str(exc),
                )
                messages.error(request, f"Garmin connect failed: {exc}")
            except Exception:
                logger.exception("Garmin connect failed for user_id=%s", request.user.id)
                audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.CONNECT,
                    status=GarminSyncAudit.Status.ERROR,
                    message="Unexpected Garmin connect error.",
                )
                messages.error(request, "Garmin connect failed.")
            return redirect("dashboard_home")

        if source == "garmin_revoke":
            revoked = revoke_garmin_for_user(request.user)
            audit_garmin(
                user=request.user,
                action=GarminSyncAudit.Action.REVOKE,
                status=GarminSyncAudit.Status.SUCCESS if revoked else GarminSyncAudit.Status.ERROR,
                message="Garmin account disconnected." if revoked else "No active Garmin connection.",
            )
            if revoked:
                messages.success(request, "Garmin account disconnected.")
            else:
                messages.info(request, "Garmin account is not connected.")
            return redirect("dashboard_home")

        if source == "garmin_sync":
            selected_range = request.POST.get("garmin_range", "last_30_days")
            if selected_range not in GARMIN_RANGE_OPTIONS:
                selected_range = "last_30_days"
            try:
                is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
                if is_ajax:
                    _, is_new_job = _queue_garmin_sync_job_for_user(user=request.user, selected_range=selected_range)
                    if is_new_job:
                        messages.success(request, "Garmin sync queued.")
                    else:
                        messages.info(request, "Garmin sync už běží.")
                else:
                    sync_result = run_garmin_sync(request.user, window=selected_range)
                    if sync_result is None:
                        messages.success(request, "Garmin sync queued.")
                    else:
                        imported, skipped, connection = sync_result
                        audit_garmin(
                            user=request.user,
                            connection=connection,
                            action=GarminSyncAudit.Action.SYNC,
                            status=GarminSyncAudit.Status.SUCCESS,
                            window=selected_range,
                            imported_count=imported,
                            skipped_count=skipped,
                            message="Garmin sync finished.",
                        )
                        messages.success(request, f"Garmin sync finished. Imported: {imported}, skipped duplicates: {skipped}.")
            except (GarminImportError, GarminSecretStoreError) as exc:
                audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.SYNC,
                    status=GarminSyncAudit.Status.ERROR,
                    window=selected_range,
                    message=str(exc),
                )
                messages.error(request, f"Garmin sync failed: {exc}")
            except Exception:
                logger.exception("Garmin sync failed for user_id=%s", request.user.id)
                audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.SYNC,
                    status=GarminSyncAudit.Status.ERROR,
                    window=selected_range,
                    message="Unexpected Garmin sync error.",
                )
                messages.error(request, "Garmin sync failed.")
            return redirect("dashboard_home")

        uploaded_file = request.FILES.get("fit_file")
        if not uploaded_file:
            messages.error(request, "Please select a FIT file.")
            return redirect("dashboard_home")
        try:
            imported = run_fit_import(request.user, uploaded_file)
            if imported is None:
                messages.success(request, "FIT import queued.")
            elif imported:
                messages.success(request, "FIT file imported.")
            else:
                messages.info(request, "This FIT file is already imported.")
        except Exception as exc:
            logger.exception("FIT import failed for user_id=%s file=%s", request.user.id, getattr(uploaded_file, "name", ""))
            if settings.DEBUG:
                messages.error(request, f"FIT import failed: {exc}")
            else:
                messages.error(request, "FIT import failed.")
        return redirect("dashboard_home")

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
        },
    )


@login_required
def athlete_update_legend_state(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

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
        return JsonResponse({"ok": False, "error": "Garmin účet není připojen."}, status=400)

    try:
        job, is_new_job = _queue_garmin_sync_job_for_user(user=request.user, selected_range=selected_range)
    except Exception:
        logger.exception("Failed to queue Garmin sync for user_id=%s", request.user.id)
        return JsonResponse({"ok": False, "error": "Synchronizaci se nepodařilo spustit."}, status=500)

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
        return JsonResponse({"ok": False, "error": "Neplatny zacatek tydne."}, status=400)

    if not GarminConnection.objects.filter(user=request.user, is_active=True).exists():
        return JsonResponse({"ok": False, "error": "Garmin ucet neni pripojen."}, status=400)

    normalized_week_start = week_start - timedelta(days=week_start.weekday())
    if normalized_week_start > timezone.localdate():
        return JsonResponse({"ok": False, "error": "Garmin import tydne je dostupny az od zacatku tydne."}, status=400)
    window_label = f"week:{normalized_week_start.isoformat()}"
    try:
        replaced, untouched, connection = sync_garmin_week_for_user(
            request.user,
            week_start=normalized_week_start,
        )
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
        return JsonResponse({"ok": False, "error": f"Garmin sync failed: {exc}"}, status=400)
    except Exception:
        logger.exception("Garmin week sync failed for user_id=%s week_start=%s", request.user.id, normalized_week_start)
        audit_garmin(
            user=request.user,
            action=GarminSyncAudit.Action.SYNC,
            status=GarminSyncAudit.Status.ERROR,
            window=window_label,
            message="Unexpected Garmin week sync error.",
        )
        return JsonResponse({"ok": False, "error": "Garmin sync failed."}, status=500)

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
            "message": f"Garmin tyden synchronizovan. Prepsano: {replaced}, ponechano: {untouched}.",
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
        return JsonResponse({"ok": False, "error": "Job nenalezen."}, status=404)

    return JsonResponse(
        {
            "ok": True,
            "job": _serialize_import_job(job),
        }
    )
