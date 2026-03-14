from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

from accounts.models import CoachAthlete, CoachJoinRequest, GarminSyncAudit
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
            messages.error(request, HomeText.COACH_CODE_NOT_FOUND)
            return redirect("dashboard_home")
        if coach_user.id == request.user.id:
            messages.error(request, HomeText.OWN_COACH_CODE)
            return redirect("dashboard_home")
        if CoachAthlete.objects.filter(coach=coach_user, athlete=request.user).exists():
            messages.info(request, HomeText.ALREADY_ASSIGNED_TO_COACH)
            return redirect("dashboard_home")

        already_pending = CoachJoinRequest.objects.filter(
            coach=coach_user,
            athlete=request.user,
            status=CoachJoinRequest.Status.PENDING,
        ).exists()
        if already_pending:
            messages.info(request, HomeText.JOIN_REQUEST_ALREADY_PENDING)
            return redirect("dashboard_home")

        CoachJoinRequest.objects.create(
            coach=coach_user,
            athlete=request.user,
            status=CoachJoinRequest.Status.PENDING,
        )
        messages.success(request, HomeText.JOIN_REQUEST_SENT)
        return redirect("dashboard_home")

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
        messages.error(request, HomeText.GARMIN_EMAIL_PASSWORD_REQUIRED)
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
        messages.success(request, HomeText.GARMIN_ACCOUNT_CONNECTED)
    except (GarminImportError, GarminSecretStoreError) as exc:
        audit_garmin(
            user=request.user,
            action=GarminSyncAudit.Action.CONNECT,
            status=GarminSyncAudit.Status.ERROR,
            message=str(exc),
        )
        messages.error(request, HomeText.garmin_connect_failed(exc))
    except Exception:
        logger.exception("Garmin connect failed for user_id=%s", request.user.id)
        audit_garmin(
            user=request.user,
            action=GarminSyncAudit.Action.CONNECT,
            status=GarminSyncAudit.Status.ERROR,
            message="Unexpected Garmin connect error.",
        )
        messages.error(request, HomeText.GARMIN_CONNECT_FAILED)
    return redirect("dashboard_home")


def _handle_garmin_revoke(request):
    revoked = revoke_garmin_for_user(request.user)
    audit_garmin(
        user=request.user,
        action=GarminSyncAudit.Action.REVOKE,
        status=GarminSyncAudit.Status.SUCCESS if revoked else GarminSyncAudit.Status.ERROR,
        message="Garmin account disconnected." if revoked else "No active Garmin connection.",
    )
    if revoked:
        messages.success(request, HomeText.GARMIN_ACCOUNT_DISCONNECTED)
    else:
        messages.info(request, HomeText.GARMIN_ACCOUNT_NOT_CONNECTED)
    return redirect("dashboard_home")


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
        messages.error(request, HomeText.FIT_FILE_REQUIRED)
        return redirect("dashboard_home")
    try:
        imported = run_fit_import(request.user, uploaded_file)
        if imported is None:
            messages.success(request, HomeText.FIT_IMPORT_QUEUED)
        elif imported:
            messages.success(request, HomeText.FIT_FILE_IMPORTED)
        else:
            messages.info(request, HomeText.FIT_FILE_ALREADY_IMPORTED)
    except Exception as exc:
        logger.exception("FIT import failed for user_id=%s file=%s", request.user.id, getattr(uploaded_file, "name", ""))
        if settings.DEBUG:
            messages.error(request, HomeText.fit_import_failed(exc))
        else:
            messages.error(request, HomeText.FIT_IMPORT_FAILED)
    return redirect("dashboard_home")
