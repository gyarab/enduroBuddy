from __future__ import annotations

import hashlib
from io import BytesIO

from django.db import IntegrityError, transaction
from django.utils import timezone

from activities.models import Activity, ActivityFile, ActivityImportLedger
from activities.services.fit_importer import import_fit_into_activity
from activities.services.fit_parser import parse_fit_file
from activities.services.planned_interval_reconstructor import reconstruct_intervals_from_plan
from training.models import CompletedTraining, PlannedTraining

from .imports_matching import _resolve_planned_training


def import_fit_bytes_for_user(*, user, fit_bytes: bytes, original_name: str) -> bool:
    checksum = hashlib.sha256(fit_bytes).hexdigest()
    parsed = parse_fit_file(BytesIO(fit_bytes))
    started_at = parsed.summary.get("started_at") if parsed.summary else None
    if started_at is None:
        started_at = timezone.now()
    elif timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at, timezone.get_current_timezone())
    run_day = timezone.localtime(started_at).date() if timezone.is_aware(started_at) else started_at.date()
    fallback_title = (parsed.summary or {}).get("title") or "Imported activity"
    try:
        with transaction.atomic():
            ActivityImportLedger.objects.create(athlete=user, checksum_sha256=checksum)
            planned = _resolve_planned_training(user, run_day, fallback_title)
            activity = getattr(planned, "activity", None)
            if activity is None:
                activity = Activity.objects.create(athlete=user, planned_training=planned, started_at=started_at, title=fallback_title)
            parsed = reconstruct_intervals_from_plan(title=planned.title or "", parsed_result=parsed)
            outcome = import_fit_into_activity(activity=activity, fileobj=BytesIO(fit_bytes), original_name=original_name or "", checksum_sha256=checksum, create_activity_file_row=True, parsed_result=parsed)
            outcome.activity.refresh_from_db()
            completed, _ = CompletedTraining.objects.get_or_create(planned=planned)
            completed.activity = outcome.activity
            completed.time_seconds = outcome.activity.duration_s
            completed.distance_m = outcome.activity.distance_m
            completed.avg_hr = outcome.activity.avg_hr
            completed.save()
    except IntegrityError:
        return False
    return True


def import_fit_bytes_into_planned_for_user(*, user, planned: PlannedTraining, fit_bytes: bytes, original_name: str) -> Activity:
    checksum = hashlib.sha256(fit_bytes).hexdigest()
    parsed = parse_fit_file(BytesIO(fit_bytes))
    started_at = parsed.summary.get("started_at") if parsed.summary else None
    if started_at is None:
        started_at = timezone.now()
    elif timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at, timezone.get_current_timezone())
    fallback_title = (parsed.summary or {}).get("title") or planned.title or "Imported activity"
    with transaction.atomic():
        ActivityImportLedger.objects.get_or_create(athlete=user, checksum_sha256=checksum)
        activity = getattr(planned, "activity", None)
        if activity is None:
            activity = Activity.objects.create(athlete=user, planned_training=planned, started_at=started_at, title=fallback_title)
        parsed = reconstruct_intervals_from_plan(title=planned.title or "", parsed_result=parsed)
        create_activity_file_row = not ActivityFile.objects.filter(activity=activity, checksum_sha256=checksum).exists()
        outcome = import_fit_into_activity(activity=activity, fileobj=BytesIO(fit_bytes), original_name=original_name or "", checksum_sha256=checksum, create_activity_file_row=create_activity_file_row, parsed_result=parsed, force_reimport=True)
        outcome.activity.refresh_from_db()
        completed, _ = CompletedTraining.objects.get_or_create(planned=planned)
        completed.activity = outcome.activity
        completed.time_seconds = outcome.activity.duration_s
        completed.distance_m = outcome.activity.distance_m
        completed.avg_hr = outcome.activity.avg_hr
        completed.note = ""
        completed.feel = ""
        completed.save(update_fields=["activity", "time_seconds", "distance_m", "avg_hr", "note", "feel"])
    return outcome.activity


def import_fit_for_user(user, uploaded_file) -> bool:
    fit_bytes = uploaded_file.read()
    return import_fit_bytes_for_user(user=user, fit_bytes=fit_bytes, original_name=getattr(uploaded_file, "name", "") or "")
