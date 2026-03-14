from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from io import BytesIO

from django.conf import settings
from django.utils import timezone

from accounts.models import GarminConnection, GarminSyncAudit
from accounts.services.garmin_secret_store import decrypt_tokenstore, encrypt_tokenstore
from activities.services.garmin_importer import GarminImportError, connect_garmin_account, download_garmin_fit_payloads
from activities.services.fit_parser import parse_fit_file

from .imports_fit import import_fit_bytes_for_user, import_fit_bytes_into_planned_for_user
from .imports_matching import _parse_payload_metadata_for_user, _resolve_planned_training, _select_payloads_for_import


GARMIN_RANGE_OPTIONS = {"today", "yesterday", "this_week", "last_week", "last_30_days", "all"}


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


def audit_garmin(*, user, action: str, status: str, connection: GarminConnection | None = None, window: str = "", imported_count: int = 0, skipped_count: int = 0, message: str = "") -> None:
    GarminSyncAudit.objects.create(user=user, connection=connection, action=action, status=status, window=window, imported_count=imported_count, skipped_count=skipped_count, message=message[:255])


def connect_garmin_for_user(user, *, email: str, password: str) -> GarminConnection:
    bundle = connect_garmin_account(email=email, password=password)
    encrypted = encrypt_tokenstore(bundle.tokenstore)
    connection, _ = GarminConnection.objects.update_or_create(
        user=user,
        defaults={"garmin_email": email, "garmin_display_name": bundle.display_name or bundle.full_name or "", "encrypted_tokenstore": encrypted, "kms_key_id": settings.GARMIN_KMS_KEY_ID, "is_active": True, "revoked_at": None},
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


def sync_garmin_for_user(user, *, window: str, progress_callback=None) -> tuple[int, int, GarminConnection]:
    connection = GarminConnection.objects.filter(user=user, is_active=True).first()
    if connection is None:
        raise GarminImportError("Garmin account is not connected.")
    from_day, to_day = _resolve_garmin_range(window)
    tokenstore = decrypt_tokenstore(connection.encrypted_tokenstore)
    result = download_garmin_fit_payloads(tokenstore=tokenstore, limit=int(settings.GARMIN_SYNC_LIMIT), from_day=from_day, to_day=to_day)
    if callable(progress_callback):
        progress_callback(stage="downloading_done", total=0, processed=0, imported=0, skipped=0)
    selected_payloads = _select_payloads_for_import(user=user, payloads=result.payloads)
    total_payloads = len(selected_payloads)
    if callable(progress_callback):
        progress_callback(stage="importing", total=total_payloads, processed=0, imported=0, skipped=0)
    imported = 0
    skipped = 0
    for index, payload in enumerate(selected_payloads, start=1):
        did_import = import_fit_bytes_for_user(user=user, fit_bytes=payload.fit_bytes, original_name=payload.original_name)
        if did_import:
            imported += 1
        else:
            skipped += 1
        if callable(progress_callback):
            progress_callback(stage="importing", total=total_payloads, processed=index, imported=imported, skipped=skipped)
    connection.encrypted_tokenstore = encrypt_tokenstore(result.refreshed_tokenstore)
    connection.last_sync_at = timezone.now()
    connection.revoked_at = None
    connection.save(update_fields=["encrypted_tokenstore", "last_sync_at", "revoked_at", "updated_at"])
    return imported, skipped, connection


def sync_garmin_week_for_user(user, *, week_start: date) -> tuple[int, int, GarminConnection]:
    connection = GarminConnection.objects.filter(user=user, is_active=True).first()
    if connection is None:
        raise GarminImportError("Garmin account is not connected.")
    week_start = week_start - timedelta(days=week_start.weekday())
    week_end = week_start + timedelta(days=6)
    tokenstore = decrypt_tokenstore(connection.encrypted_tokenstore)
    result = download_garmin_fit_payloads(tokenstore=tokenstore, limit=int(settings.GARMIN_SYNC_LIMIT), from_day=week_start, to_day=week_end)
    selected_payloads = _select_payloads_for_import(user=user, payloads=result.payloads)
    payloads_by_day: dict[date, list] = defaultdict(list)
    for payload in selected_payloads:
        run_day = _parse_payload_metadata_for_user(fit_bytes=payload.fit_bytes)["run_day"]
        payloads_by_day[run_day].append(payload)
    replaced = 0
    untouched = 0
    from training.models import PlannedTraining
    for run_day in sorted(payloads_by_day.keys()):
        payloads_for_day = payloads_by_day[run_day]
        day_items = list(
            PlannedTraining.objects.filter(week__training_month__athlete=user, date=run_day)
            .select_related("activity")
            .order_by("order_in_day", "id")
        )
        if not day_items:
            fallback_title = ""
            first_payload = payloads_for_day[0] if payloads_for_day else None
            if first_payload is not None:
                parsed = parse_fit_file(BytesIO(first_payload.fit_bytes))
                fallback_title = (parsed.summary or {}).get("title") or ""
            day_items = [_resolve_planned_training(user, run_day, fallback_title)]
        for payload, planned in zip(payloads_for_day, day_items):
            import_fit_bytes_into_planned_for_user(user=user, planned=planned, fit_bytes=payload.fit_bytes, original_name=payload.original_name)
            replaced += 1
        if len(payloads_for_day) < len(day_items):
            untouched += len(day_items) - len(payloads_for_day)
    connection.encrypted_tokenstore = encrypt_tokenstore(result.refreshed_tokenstore)
    connection.last_sync_at = timezone.now()
    connection.revoked_at = None
    connection.save(update_fields=["encrypted_tokenstore", "last_sync_at", "revoked_at", "updated_at"])
    return replaced, untouched, connection
