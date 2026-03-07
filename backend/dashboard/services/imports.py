from __future__ import annotations

from datetime import date, timedelta
import hashlib
from io import BytesIO

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import GarminConnection, GarminSyncAudit
from accounts.services.garmin_secret_store import decrypt_tokenstore, encrypt_tokenstore
from activities.models import Activity, ActivityImportLedger
from activities.services.garmin_importer import GarminImportError, connect_garmin_account, download_garmin_fit_payloads
from activities.services.fit_importer import import_fit_into_activity
from activities.services.fit_parser import parse_fit_file
from training.models import CompletedTraining, PlannedTraining

from .month_cards import resolve_week_for_day


GARMIN_RANGE_OPTIONS = {"today", "yesterday", "this_week", "last_week", "last_30_days", "all"}


def _enable_two_phase_for_day(day_items: list[PlannedTraining]) -> None:
    updates = []
    for item in day_items:
        if not item.is_two_phase_day:
            item.is_two_phase_day = True
            updates.append(item)
    if updates:
        PlannedTraining.objects.bulk_update(updates, ["is_two_phase_day"])


def _resolve_planned_training(user, run_day: date, fallback_title: str) -> PlannedTraining:
    week_obj = resolve_week_for_day(user, run_day)
    day_qs = PlannedTraining.objects.filter(week=week_obj, date=run_day).order_by("order_in_day", "id")
    day_items = list(day_qs)

    available = day_qs.filter(activity__isnull=True).first()
    if available:
        if len(day_items) >= 2:
            _enable_two_phase_for_day(day_items)
        return available

    max_order = day_items[-1].order_in_day if day_items else 0
    created = PlannedTraining.objects.create(
        week=week_obj,
        date=run_day,
        day_label=run_day.strftime("%a"),
        title=fallback_title or "Imported activity",
        order_in_day=max_order + 1,
        is_two_phase_day=len(day_items) >= 1,
    )
    if len(day_items) == 1:
        first = day_items[0]
        if not first.is_two_phase_day:
            first.is_two_phase_day = True
            first.save(update_fields=["is_two_phase_day"])
    return created


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
                activity = Activity.objects.create(
                    athlete=user,
                    planned_training=planned,
                    started_at=started_at,
                    title=fallback_title,
                )

            outcome = import_fit_into_activity(
                activity=activity,
                fileobj=BytesIO(fit_bytes),
                original_name=original_name or "",
                checksum_sha256=checksum,
                create_activity_file_row=True,
                parsed_result=parsed,
            )
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


def import_fit_for_user(user, uploaded_file) -> bool:
    fit_bytes = uploaded_file.read()
    return import_fit_bytes_for_user(
        user=user,
        fit_bytes=fit_bytes,
        original_name=getattr(uploaded_file, "name", "") or "",
    )


def _resolve_garmin_range(window: str) -> tuple[date | None, date | None]:
    today = timezone.localdate()
    if window == "today":
        return today, today
    if window == "yesterday":
        d = today - timedelta(days=1)
        return d, d
    if window == "this_week":
        monday = today - timedelta(days=today.weekday())
        return monday, today
    if window == "last_week":
        this_monday = today - timedelta(days=today.weekday())
        return this_monday - timedelta(days=7), this_monday - timedelta(days=1)
    if window == "last_30_days":
        return today - timedelta(days=29), today
    return None, None


def audit_garmin(
    *,
    user,
    action: str,
    status: str,
    connection: GarminConnection | None = None,
    window: str = "",
    imported_count: int = 0,
    skipped_count: int = 0,
    message: str = "",
) -> None:
    GarminSyncAudit.objects.create(
        user=user,
        connection=connection,
        action=action,
        status=status,
        window=window,
        imported_count=imported_count,
        skipped_count=skipped_count,
        message=message[:255],
    )


def connect_garmin_for_user(user, *, email: str, password: str) -> GarminConnection:
    bundle = connect_garmin_account(email=email, password=password)
    encrypted = encrypt_tokenstore(bundle.tokenstore)
    connection, _ = GarminConnection.objects.update_or_create(
        user=user,
        defaults={
            "garmin_email": email,
            "garmin_display_name": bundle.display_name or bundle.full_name or "",
            "encrypted_tokenstore": encrypted,
            "kms_key_id": settings.GARMIN_KMS_KEY_ID,
            "is_active": True,
            "revoked_at": None,
        },
    )
    return connection


def revoke_garmin_for_user(user) -> bool:
    connection = GarminConnection.objects.filter(user=user, is_active=True).first()
    if not connection:
        return False
    connection.is_active = False
    connection.encrypted_tokenstore = ""
    connection.revoked_at = timezone.now()
    connection.save(update_fields=["is_active", "encrypted_tokenstore", "revoked_at", "updated_at"])
    return True


def sync_garmin_for_user(user, *, window: str) -> tuple[int, int, GarminConnection]:
    connection = GarminConnection.objects.filter(user=user, is_active=True).first()
    if connection is None:
        raise GarminImportError("Garmin account is not connected.")

    from_day, to_day = _resolve_garmin_range(window)
    tokenstore = decrypt_tokenstore(connection.encrypted_tokenstore)
    result = download_garmin_fit_payloads(
        tokenstore=tokenstore,
        limit=int(settings.GARMIN_SYNC_LIMIT),
        from_day=from_day,
        to_day=to_day,
    )

    imported = 0
    skipped = 0
    for payload in result.payloads:
        did_import = import_fit_bytes_for_user(
            user=user,
            fit_bytes=payload.fit_bytes,
            original_name=payload.original_name,
        )
        if did_import:
            imported += 1
        else:
            skipped += 1

    connection.encrypted_tokenstore = encrypt_tokenstore(result.refreshed_tokenstore)
    connection.last_sync_at = timezone.now()
    connection.revoked_at = None
    connection.save(update_fields=["encrypted_tokenstore", "last_sync_at", "revoked_at", "updated_at"])
    return imported, skipped, connection
