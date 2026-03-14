from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from accounts.models import CoachAthlete, CoachJoinRequest, GarminSyncAudit
from accounts.services.notifications import notify_new_coach_join_request
from accounts.services.garmin_secret_store import GarminSecretStoreError
from activities.services.garmin_importer import GarminImportError
from dashboard.services.imports import (
    GARMIN_RANGE_OPTIONS,
    audit_garmin,
    connect_garmin_for_user,
    revoke_garmin_for_user,
)
from dashboard.services.month_cards import add_next_month_for_athlete
from dashboard.services.tasks import run_fit_import, run_garmin_sync
from dashboard.texts import HomeText

from ..views_shared import _resolve_coach_from_code


def handle_home_post(request, *, logger, queue_garmin_sync_job_for_user):
    action = request.POST.get("action", "")
    if action == "request_coach_by_code":
        coach_code = (request.POST.get("coach_code") or "").strip().upper()
        coach_user = _resolve_coach_from_code(coach_code)
        if coach_user is None:
            return _home_response(request, ok=False, message=HomeText.COACH_CODE_NOT_FOUND, tone="danger", status=400)
        if coach_user.id == request.user.id:
            return _home_response(request, ok=False, message=HomeText.OWN_COACH_CODE, tone="danger", status=400)
        if CoachAthlete.objects.filter(coach=coach_user, athlete=request.user).exists():
            return _home_response(request, ok=True, message=HomeText.ALREADY_ASSIGNED_TO_COACH, tone="info")

        already_pending = CoachJoinRequest.objects.filter(
            coach=coach_user,
            athlete=request.user,
            status=CoachJoinRequest.Status.PENDING,
        ).exists()
        if already_pending:
            return _home_response(request, ok=True, message=HomeText.JOIN_REQUEST_ALREADY_PENDING, tone="info")

        join_request = CoachJoinRequest.objects.create(
            coach=coach_user,
            athlete=request.user,
            status=CoachJoinRequest.Status.PENDING,
        )
        notify_new_coach_join_request(join_request=join_request)
        return _home_response(request, ok=True, message=HomeText.JOIN_REQUEST_SENT, tone="success")

    if action == "add_next_month_self":
        month_created, weeks_created, days_created = add_next_month_for_athlete(athlete=request.user)
        if month_created:
            messages.success(request, HomeText.month_created(weeks_created=weeks_created, days_created=days_created))
        else:
            messages.info(request, HomeText.month_extended(weeks_created=weeks_created, days_created=days_created))
        return redirect("dashboard_home")

    source = request.POST.get("import_source", "fit_upload")
    if source == "garmin_connect":
        return _handle_garmin_connect(request, logger=logger)
    if source == "garmin_revoke":
        return _handle_garmin_revoke(request)
    if source == "garmin_sync":
        return _handle_garmin_sync(request, logger=logger, queue_garmin_sync_job_for_user=queue_garmin_sync_job_for_user)
    return _handle_fit_import(request, logger=logger)


def _handle_garmin_connect(request, *, logger):
    email = (request.POST.get("garmin_email") or "").strip()
    password = (request.POST.get("garmin_password") or "").strip()
    if not email or not password:
        return _home_response(request, ok=False, message=HomeText.GARMIN_EMAIL_PASSWORD_REQUIRED, tone="danger", status=400)
    try:
        connection = connect_garmin_for_user(request.user, email=email, password=password)
        audit_garmin(
            user=request.user,
            connection=connection,
            action=GarminSyncAudit.Action.CONNECT,
            status=GarminSyncAudit.Status.SUCCESS,
            message="Garmin account connected.",
        )
        return _home_response(
            request,
            ok=True,
            message=HomeText.GARMIN_ACCOUNT_CONNECTED,
            tone="success",
            extra={"refresh_import_modal": True, "refresh_month_cards": True},
        )
    except (GarminImportError, GarminSecretStoreError) as exc:
        audit_garmin(
            user=request.user,
            action=GarminSyncAudit.Action.CONNECT,
            status=GarminSyncAudit.Status.ERROR,
            message=str(exc),
        )
        return _home_response(request, ok=False, message=HomeText.garmin_connect_failed(exc), tone="danger", status=400)
    except Exception:
        logger.exception("Garmin connect failed for user_id=%s", request.user.id)
        audit_garmin(
            user=request.user,
            action=GarminSyncAudit.Action.CONNECT,
            status=GarminSyncAudit.Status.ERROR,
            message="Unexpected Garmin connect error.",
        )
        return _home_response(request, ok=False, message=HomeText.GARMIN_CONNECT_FAILED, tone="danger", status=500)


def _handle_garmin_revoke(request):
    revoked = revoke_garmin_for_user(request.user)
    audit_garmin(
        user=request.user,
        action=GarminSyncAudit.Action.REVOKE,
        status=GarminSyncAudit.Status.SUCCESS if revoked else GarminSyncAudit.Status.ERROR,
        message="Garmin account disconnected." if revoked else "No active Garmin connection.",
    )
    if revoked:
        return _home_response(
            request,
            ok=True,
            message=HomeText.GARMIN_ACCOUNT_DISCONNECTED,
            tone="success",
            extra={"refresh_import_modal": True, "refresh_month_cards": True},
        )
    return _home_response(
        request,
        ok=True,
        message=HomeText.GARMIN_ACCOUNT_NOT_CONNECTED,
        tone="info",
        extra={"refresh_import_modal": True, "refresh_month_cards": True},
    )


def _handle_garmin_sync(request, *, logger, queue_garmin_sync_job_for_user):
    selected_range = request.POST.get("garmin_range", "last_30_days")
    if selected_range not in GARMIN_RANGE_OPTIONS:
        selected_range = "last_30_days"
    try:
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
        if is_ajax:
            _, is_new_job = queue_garmin_sync_job_for_user(user=request.user, selected_range=selected_range)
            if is_new_job:
                messages.success(request, HomeText.GARMIN_SYNC_QUEUED)
            else:
                messages.info(request, HomeText.GARMIN_SYNC_ALREADY_RUNNING)
        else:
            sync_result = run_garmin_sync(request.user, window=selected_range)
            if sync_result is None:
                messages.success(request, HomeText.GARMIN_SYNC_QUEUED)
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
                messages.success(request, HomeText.garmin_sync_finished(imported=imported, skipped=skipped))
    except (GarminImportError, GarminSecretStoreError) as exc:
        audit_garmin(
            user=request.user,
            action=GarminSyncAudit.Action.SYNC,
            status=GarminSyncAudit.Status.ERROR,
            window=selected_range,
            message=str(exc),
        )
        messages.error(request, HomeText.garmin_sync_failed(exc))
    except Exception:
        logger.exception("Garmin sync failed for user_id=%s", request.user.id)
        audit_garmin(
            user=request.user,
            action=GarminSyncAudit.Action.SYNC,
            status=GarminSyncAudit.Status.ERROR,
            window=selected_range,
            message="Unexpected Garmin sync error.",
        )
        messages.error(request, HomeText.GARMIN_SYNC_FAILED)
    return redirect("dashboard_home")


def _handle_fit_import(request, *, logger):
    uploaded_file = request.FILES.get("fit_file")
    if not uploaded_file:
        return _home_response(request, ok=False, message=HomeText.FIT_FILE_REQUIRED, tone="danger", status=400)
    try:
        imported = run_fit_import(request.user, uploaded_file)
        if imported is None:
            return _home_response(
                request,
                ok=True,
                message=HomeText.FIT_IMPORT_QUEUED,
                tone="success",
                extra={"refresh_import_modal": True, "refresh_month_cards": False},
            )
        elif imported:
            return _home_response(
                request,
                ok=True,
                message=HomeText.FIT_FILE_IMPORTED,
                tone="success",
                extra={"refresh_import_modal": True, "refresh_month_cards": True},
            )
        return _home_response(
            request,
            ok=True,
            message=HomeText.FIT_FILE_ALREADY_IMPORTED,
            tone="info",
            extra={"refresh_import_modal": True, "refresh_month_cards": False},
        )
    except Exception as exc:
        logger.exception("FIT import failed for user_id=%s file=%s", request.user.id, getattr(uploaded_file, "name", ""))
        if settings.DEBUG:
            return _home_response(request, ok=False, message=HomeText.fit_import_failed(exc), tone="danger", status=400)
        return _home_response(request, ok=False, message=HomeText.FIT_IMPORT_FAILED, tone="danger", status=500)


def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _home_response(request, *, ok: bool, message: str, tone: str, status: int = 200, extra: dict | None = None):
    if _is_ajax(request):
        payload = {"ok": ok, "message": message, "tone": tone}
        if extra:
            payload.update(extra)
        return JsonResponse(payload, status=status)

    level = {
        "success": "success",
        "danger": "error",
        "warning": "warning",
        "info": "info",
        "secondary": "info",
    }.get(tone, "info")
    getattr(messages, level)(request, message)
    return redirect("dashboard_home")
