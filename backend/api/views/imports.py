from __future__ import annotations

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from accounts.models import GarminConnection, GarminSyncAudit, ImportJob
from accounts.services.garmin_secret_store import GarminSecretStoreError
from activities.services.garmin_importer import GarminImportError
from dashboard.api import json_error
from dashboard.services.imports import (
    GARMIN_RANGE_OPTIONS,
    audit_garmin,
    connect_garmin_for_user,
    revoke_garmin_for_user,
)
from dashboard.services.tasks import enqueue_garmin_sync_job, run_fit_import
from dashboard.texts import ApiText, HomeText
from dashboard.views_home import _job_progress_percent, _job_status_label, _serialize_import_job


def _parse_json_body(request):
  try:
    return json.loads(request.body.decode("utf-8")), None
  except (UnicodeDecodeError, json.JSONDecodeError):
    return None, json_error(ApiText.INVALID_JSON_BODY, status=400)


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


def _serialize_connection(user) -> dict[str, object]:
  connection = GarminConnection.objects.filter(user=user, is_active=True).first()
  return {
    "connected": bool(connection),
    "display_name": (
      connection.garmin_display_name
      or connection.garmin_email
      or ""
    ) if connection else "",
  }


@login_required
@require_POST
def garmin_connect(request):
  if not settings.GARMIN_CONNECT_ENABLED:
    return json_error(ApiText.GARMIN_CONNECT_DISABLED, status=503)

  payload, error = _parse_json_body(request)
  if error:
    return error

  email = str((payload or {}).get("email") or "").strip()
  password = str((payload or {}).get("password") or "").strip()
  if not email or not password:
    return JsonResponse({"ok": False, "error": HomeText.GARMIN_EMAIL_PASSWORD_REQUIRED}, status=400)

  try:
    connection = connect_garmin_for_user(request.user, email=email, password=password)
    audit_garmin(
      user=request.user,
      connection=connection,
      action=GarminSyncAudit.Action.CONNECT,
      status=GarminSyncAudit.Status.SUCCESS,
      message="Garmin account connected.",
    )
    return JsonResponse(
      {
        "ok": True,
        "message": HomeText.GARMIN_ACCOUNT_CONNECTED,
        "connection": _serialize_connection(request.user),
      }
    )
  except (GarminImportError, GarminSecretStoreError) as exc:
    audit_garmin(
      user=request.user,
      action=GarminSyncAudit.Action.CONNECT,
      status=GarminSyncAudit.Status.ERROR,
      message=str(exc),
    )
    return JsonResponse({"ok": False, "error": HomeText.garmin_connect_failed(exc)}, status=400)
  except Exception:
    audit_garmin(
      user=request.user,
      action=GarminSyncAudit.Action.CONNECT,
      status=GarminSyncAudit.Status.ERROR,
      message="Unexpected Garmin connect error.",
    )
    return JsonResponse({"ok": False, "error": HomeText.GARMIN_CONNECT_FAILED}, status=500)


@login_required
@require_POST
def garmin_revoke(request):
  revoked = revoke_garmin_for_user(request.user)
  audit_garmin(
    user=request.user,
    action=GarminSyncAudit.Action.REVOKE,
    status=GarminSyncAudit.Status.SUCCESS if revoked else GarminSyncAudit.Status.ERROR,
    message="Garmin account disconnected." if revoked else "No active Garmin connection.",
  )
  return JsonResponse(
    {
      "ok": True,
      "message": HomeText.GARMIN_ACCOUNT_DISCONNECTED if revoked else HomeText.GARMIN_ACCOUNT_NOT_CONNECTED,
      "connection": _serialize_connection(request.user),
    }
  )


@login_required
@require_POST
def garmin_sync_start(request):
  if not settings.GARMIN_SYNC_ENABLED:
    return json_error(ApiText.GARMIN_SYNC_DISABLED, status=503)

  payload, error = _parse_json_body(request)
  if error:
    return error

  selected_range = str((payload or {}).get("range") or "last_30_days")
  if selected_range not in GARMIN_RANGE_OPTIONS:
    selected_range = "last_30_days"
  if not GarminConnection.objects.filter(user=request.user, is_active=True).exists():
    return json_error(ApiText.GARMIN_NOT_CONNECTED, status=400)

  try:
    job, is_new_job = _queue_garmin_sync_job_for_user(user=request.user, selected_range=selected_range)
  except Exception:
    return json_error(ApiText.GARMIN_SYNC_START_FAILED, status=500)

  return JsonResponse(
    {
      "ok": True,
      "job": {
        "id": job.id,
        "status": job.status,
        "status_label": _job_status_label(job.status),
        "progress_percent": _job_progress_percent(job),
        "message": job.message,
        "done": job.status in {ImportJob.Status.SUCCESS, ImportJob.Status.ERROR},
      },
      "already_running": not is_new_job,
      "message": HomeText.GARMIN_SYNC_ALREADY_RUNNING if not is_new_job else HomeText.GARMIN_SYNC_QUEUED,
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
@require_POST
def fit_upload(request):
  uploaded_file = request.FILES.get("fit_file")
  if not uploaded_file:
    return JsonResponse({"ok": False, "error": HomeText.FIT_FILE_REQUIRED}, status=400)

  try:
    imported = run_fit_import(request.user, uploaded_file)
  except Exception as exc:
    if settings.DEBUG:
      return JsonResponse({"ok": False, "error": HomeText.fit_import_failed(exc)}, status=400)
    return JsonResponse({"ok": False, "error": HomeText.FIT_IMPORT_FAILED}, status=500)

  if imported is None:
    return JsonResponse({"ok": True, "queued": True, "message": HomeText.FIT_IMPORT_QUEUED})
  if imported:
    return JsonResponse({"ok": True, "queued": False, "imported": True, "message": HomeText.FIT_FILE_IMPORTED})
  return JsonResponse({"ok": True, "queued": False, "imported": False, "message": HomeText.FIT_FILE_ALREADY_IMPORTED})
