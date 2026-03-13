from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import hashlib
from io import BytesIO
from itertools import combinations, permutations
import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import GarminConnection, GarminSyncAudit
from accounts.services.garmin_secret_store import decrypt_tokenstore, encrypt_tokenstore
from activities.models import Activity, ActivityFile, ActivityImportLedger
from activities.services.garmin_importer import GarminImportError, connect_garmin_account, download_garmin_fit_payloads
from activities.services.fit_importer import import_fit_into_activity
from activities.services.fit_parser import parse_fit_file
from activities.services.planned_interval_reconstructor import reconstruct_intervals_from_plan
from training.models import CompletedTraining, PlannedTraining

from .month_cards import resolve_week_for_day
from .planned_interval_formatter import parse_planned_interval_blocks
from .planned_km import estimate_running_km_from_title


GARMIN_RANGE_OPTIONS = {"today", "yesterday", "this_week", "last_week", "last_30_days", "all"}
logger = logging.getLogger(__name__)


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
        session_type=PlannedTraining.SessionType.RUN,
        order_in_day=max_order + 1,
        is_two_phase_day=len(day_items) >= 1,
    )
    if len(day_items) == 1:
        first = day_items[0]
        if not first.is_two_phase_day:
            first.is_two_phase_day = True
            first.save(update_fields=["is_two_phase_day"])
    return created


def _parse_payload_metadata_for_user(*, fit_bytes: bytes) -> dict[str, object]:
    parsed = parse_fit_file(BytesIO(fit_bytes))
    started_at = parsed.summary.get("started_at") if parsed.summary else None
    if started_at is None:
        started_at = timezone.now()
    elif timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at, timezone.get_current_timezone())

    run_day = timezone.localtime(started_at).date() if timezone.is_aware(started_at) else started_at.date()
    summary = parsed.summary or {}
    workout_type = summary.get("workout_type") or Activity.WorkoutType.UNKNOWN
    distance_m = int(summary.get("distance_m") or 0)
    duration_s = int(summary.get("duration_s") or 0)
    intervals = list(parsed.intervals or [])
    work_interval_count = sum(1 for it in intervals if (it.get("note") or "").upper() == "WORK")
    rest_interval_count = sum(1 for it in intervals if (it.get("note") or "").upper() == "REST")
    return {
        "run_day": run_day,
        "workout_type": workout_type,
        "distance_m": distance_m,
        "duration_s": duration_s,
        "interval_count": len(intervals),
        "work_interval_count": work_interval_count,
        "rest_interval_count": rest_interval_count,
    }


def _is_explicit_two_phase_day(*, user, run_day: date) -> bool:
    day_items = list(
        PlannedTraining.objects.filter(
            week__training_month__athlete=user,
            date=run_day,
        )
        .only("id", "is_two_phase_day")
        .order_by("order_in_day", "id")
    )
    if len(day_items) >= 2:
        return True
    return any(item.is_two_phase_day for item in day_items)


def _planned_items_for_day(*, user, run_day: date) -> list[PlannedTraining]:
    return list(
        PlannedTraining.objects.filter(
            week__training_month__athlete=user,
            date=run_day,
        )
        .only("id", "title", "notes", "session_type", "order_in_day", "is_two_phase_day")
        .order_by("order_in_day", "id")
    )


def _planned_day_selection_context(*, user, run_day: date) -> dict[str, object]:
    day_items = _planned_items_for_day(user=user, run_day=run_day)
    if not day_items:
        return {
            "has_plan": False,
            "expected_session_type": Activity.WorkoutType.UNKNOWN,
            "expected_work_count": 0,
            "planned_distance_m": 0,
        }

    joined_title = " | ".join(item.title for item in day_items if item.title)
    joined_notes = " | ".join(item.notes for item in day_items if item.notes)
    interval_blocks = parse_planned_interval_blocks(joined_title)
    expected_work_count = sum(len(series) for block in interval_blocks for series in block.series)
    planned_distance_km = estimate_running_km_from_title(joined_title)
    expected_session_type = (
        Activity.WorkoutType.WORKOUT
        if any((item.session_type or PlannedTraining.SessionType.RUN) == PlannedTraining.SessionType.WORKOUT for item in day_items)
        or expected_work_count > 0
        else Activity.WorkoutType.RUN
    )

    return {
        "has_plan": True,
        "expected_session_type": expected_session_type,
        "expected_work_count": expected_work_count,
        "planned_distance_m": int(round(float(planned_distance_km) * 1000.0)) if planned_distance_km is not None else 0,
        "title": joined_title,
        "notes": joined_notes,
    }


def _planned_item_selection_context(item: PlannedTraining) -> dict[str, object]:
    title = item.title or ""
    interval_blocks = parse_planned_interval_blocks(title)
    expected_work_count = sum(len(series) for block in interval_blocks for series in block.series)
    planned_distance_km = estimate_running_km_from_title(title)
    expected_session_type = (
        Activity.WorkoutType.WORKOUT
        if (item.session_type or PlannedTraining.SessionType.RUN) == PlannedTraining.SessionType.WORKOUT
        or expected_work_count > 0
        else Activity.WorkoutType.RUN
    )
    return {
        "has_plan": bool(title.strip() or (item.notes or "").strip()),
        "expected_session_type": expected_session_type,
        "expected_work_count": expected_work_count,
        "planned_distance_m": int(round(float(planned_distance_km) * 1000.0)) if planned_distance_km is not None else 0,
        "title": title,
        "notes": item.notes or "",
        "planned_id": item.id,
        "order_in_day": item.order_in_day,
    }


def _distance_delta_score(*, planned_distance_m: int, actual_distance_m: int) -> int:
    if planned_distance_m <= 0 or actual_distance_m <= 0:
        return 0
    return -abs(int(actual_distance_m) - int(planned_distance_m))


def _selection_score_for_day(*, row: dict[str, object], plan_ctx: dict[str, object]) -> tuple:
    workout_type = row["workout_type"]
    distance_m = int(row["distance_m"])
    duration_s = int(row["duration_s"])
    work_interval_count = int(row.get("work_interval_count") or 0)
    rest_interval_count = int(row.get("rest_interval_count") or 0)
    interval_count = int(row.get("interval_count") or 0)

    expected_session_type = plan_ctx.get("expected_session_type")
    expected_work_count = int(plan_ctx.get("expected_work_count") or 0)
    planned_distance_m = int(plan_ctx.get("planned_distance_m") or 0)

    if expected_session_type == Activity.WorkoutType.WORKOUT:
        work_count_delta = -abs(work_interval_count - expected_work_count) if expected_work_count > 0 else work_interval_count
        has_rest_structure = 1 if rest_interval_count > 0 else 0
        return (
            1 if workout_type == Activity.WorkoutType.WORKOUT else 0,
            1 if expected_work_count > 0 and work_interval_count > 0 else 0,
            work_count_delta,
            has_rest_structure,
            rest_interval_count,
            interval_count,
            _distance_delta_score(planned_distance_m=planned_distance_m, actual_distance_m=distance_m),
            duration_s,
            distance_m,
        )

    return (
        1 if workout_type == Activity.WorkoutType.RUN else 0,
        _distance_delta_score(planned_distance_m=planned_distance_m, actual_distance_m=distance_m),
        distance_m,
        duration_s,
        -(1 if workout_type == Activity.WorkoutType.WORKOUT else 0),
        -work_interval_count,
        -rest_interval_count,
        -interval_count,
    )


def _score_debug_payload(row: dict[str, object]) -> dict[str, object]:
    payload = row.get("payload")
    return {
        "activity_id": getattr(payload, "activity_id", ""),
        "workout_type": row.get("workout_type"),
        "distance_m": int(row.get("distance_m") or 0),
        "duration_s": int(row.get("duration_s") or 0),
        "interval_count": int(row.get("interval_count") or 0),
        "work_interval_count": int(row.get("work_interval_count") or 0),
        "rest_interval_count": int(row.get("rest_interval_count") or 0),
    }


def _log_single_day_match(*, run_day: date, plan_ctx: dict[str, object], candidates: list[dict[str, object]], chosen: dict[str, object]) -> None:
    logger.debug(
        "Garmin match day=%s mode=single expected_session=%s expected_work=%s planned_distance_m=%s chosen=%s candidates=%s",
        run_day,
        plan_ctx.get("expected_session_type"),
        int(plan_ctx.get("expected_work_count") or 0),
        int(plan_ctx.get("planned_distance_m") or 0),
        {
            **_score_debug_payload(chosen),
            "score": _selection_score_for_day(row=chosen, plan_ctx=plan_ctx),
        },
        [
            {
                **_score_debug_payload(row),
                "score": _selection_score_for_day(row=row, plan_ctx=plan_ctx),
            }
            for row in candidates
        ],
    )


def _log_multi_day_match(*, run_day: date, planned_items: list[PlannedTraining], chosen_rows: list[dict[str, object]]) -> None:
    assignment = []
    for planned, row in zip(planned_items, chosen_rows):
        plan_ctx = _planned_item_selection_context(planned)
        assignment.append(
            {
                "planned_id": planned.id,
                "planned_title": planned.title,
                "expected_session_type": plan_ctx.get("expected_session_type"),
                "expected_work_count": int(plan_ctx.get("expected_work_count") or 0),
                "chosen": {
                    **_score_debug_payload(row),
                    "score": _selection_score_for_day(row=row, plan_ctx=plan_ctx),
                },
            }
        )
    logger.debug("Garmin match day=%s mode=multi assignments=%s", run_day, assignment)


def _match_payloads_to_planned_items(*, day_items: list[PlannedTraining], payload_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    if not day_items or not payload_rows:
        return []

    item_contexts = [_planned_item_selection_context(item) for item in day_items]
    pair_count = min(len(item_contexts), len(payload_rows))
    best_assignment: tuple[tuple, list[dict[str, object]]] | None = None

    payload_indexes = range(len(payload_rows))
    item_indexes = range(len(item_contexts))
    for chosen_payload_indexes in combinations(payload_indexes, pair_count):
        chosen_rows = [payload_rows[idx] for idx in chosen_payload_indexes]
        for permuted_rows in permutations(chosen_rows, pair_count):
            scored_pairs: list[tuple[tuple, int, dict[str, object], dict[str, object]]] = []
            for item_idx, row in zip(item_indexes, permuted_rows):
                plan_ctx = item_contexts[item_idx]
                score = _selection_score_for_day(row=row, plan_ctx=plan_ctx)
                scored_pairs.append((score, item_idx, row, plan_ctx))

            assignment_score = tuple(score for score, _, _, _ in scored_pairs)
            if best_assignment is None or assignment_score > best_assignment[0]:
                best_assignment = (assignment_score, [row for _, _, row, _ in scored_pairs])

    return best_assignment[1] if best_assignment is not None else []


def _select_payloads_for_import(*, user, payloads):
    if not payloads:
        return []

    prepared = []
    for payload in payloads:
        metadata = _parse_payload_metadata_for_user(fit_bytes=payload.fit_bytes)
        prepared.append(
            {
                "payload": payload,
                **metadata,
            }
        )

    by_day = defaultdict(list)
    for row in prepared:
        by_day[row["run_day"]].append(row)

    selected = []
    for run_day, day_items in by_day.items():
        planned_items = _planned_items_for_day(user=user, run_day=run_day)
        if len(planned_items) >= 2 or any(item.is_two_phase_day for item in planned_items):
            matched = _match_payloads_to_planned_items(day_items=planned_items, payload_rows=day_items)
            if matched:
                _log_multi_day_match(run_day=run_day, planned_items=planned_items, chosen_rows=matched)
                selected.extend(matched)
                continue
            logger.debug(
                "Garmin match day=%s mode=multi fallback=all_payloads planned_ids=%s candidate_ids=%s",
                run_day,
                [item.id for item in planned_items],
                [getattr(row.get('payload'), 'activity_id', '') for row in day_items],
            )
            selected.extend(day_items)
            continue

        plan_ctx = _planned_day_selection_context(user=user, run_day=run_day)
        best = max(day_items, key=lambda row: _selection_score_for_day(row=row, plan_ctx=plan_ctx))
        _log_single_day_match(run_day=run_day, plan_ctx=plan_ctx, candidates=day_items, chosen=best)
        selected.append(best)

    selected.sort(
        key=lambda row: (
            row["run_day"],
            1 if row["workout_type"] == Activity.WorkoutType.WORKOUT else 0,
            row["distance_m"],
            row["duration_s"],
        )
    )
    return [row["payload"] for row in selected]


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

            parsed = reconstruct_intervals_from_plan(title=planned.title or "", parsed_result=parsed)

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
            activity = Activity.objects.create(
                athlete=user,
                planned_training=planned,
                started_at=started_at,
                title=fallback_title,
            )

        parsed = reconstruct_intervals_from_plan(title=planned.title or "", parsed_result=parsed)
        create_activity_file_row = not ActivityFile.objects.filter(
            activity=activity,
            checksum_sha256=checksum,
        ).exists()
        outcome = import_fit_into_activity(
            activity=activity,
            fileobj=BytesIO(fit_bytes),
            original_name=original_name or "",
            checksum_sha256=checksum,
            create_activity_file_row=create_activity_file_row,
            parsed_result=parsed,
            force_reimport=True,
        )
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


def sync_garmin_for_user(user, *, window: str, progress_callback=None) -> tuple[int, int, GarminConnection]:
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
    if callable(progress_callback):
        progress_callback(
            stage="downloading_done",
            total=0,
            processed=0,
            imported=0,
            skipped=0,
        )

    selected_payloads = _select_payloads_for_import(user=user, payloads=result.payloads)
    total_payloads = len(selected_payloads)
    if callable(progress_callback):
        progress_callback(
            stage="importing",
            total=total_payloads,
            processed=0,
            imported=0,
            skipped=0,
        )

    imported = 0
    skipped = 0
    for index, payload in enumerate(selected_payloads, start=1):
        did_import = import_fit_bytes_for_user(
            user=user,
            fit_bytes=payload.fit_bytes,
            original_name=payload.original_name,
        )
        if did_import:
            imported += 1
        else:
            skipped += 1
        if callable(progress_callback):
            progress_callback(
                stage="importing",
                total=total_payloads,
                processed=index,
                imported=imported,
                skipped=skipped,
            )

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
    result = download_garmin_fit_payloads(
        tokenstore=tokenstore,
        limit=int(settings.GARMIN_SYNC_LIMIT),
        from_day=week_start,
        to_day=week_end,
    )
    selected_payloads = _select_payloads_for_import(user=user, payloads=result.payloads)

    payloads_by_day: dict[date, list] = defaultdict(list)
    for payload in selected_payloads:
        run_day = _parse_payload_metadata_for_user(fit_bytes=payload.fit_bytes)["run_day"]
        payloads_by_day[run_day].append(payload)

    replaced = 0
    untouched = 0
    for run_day in sorted(payloads_by_day.keys()):
        payloads_for_day = payloads_by_day[run_day]
        day_items = list(
            PlannedTraining.objects.filter(
                week__training_month__athlete=user,
                date=run_day,
            )
            .select_related("activity")
            .order_by("order_in_day", "id")
        )

        if not day_items:
            fallback_title = ""
            first_payload = payloads_for_day[0] if payloads_for_day else None
            if first_payload is not None:
                parsed = parse_fit_file(BytesIO(first_payload.fit_bytes))
                fallback_title = (parsed.summary or {}).get("title") or ""
            created = _resolve_planned_training(user, run_day, fallback_title)
            day_items = [created]

        for payload, planned in zip(payloads_for_day, day_items):
            import_fit_bytes_into_planned_for_user(
                user=user,
                planned=planned,
                fit_bytes=payload.fit_bytes,
                original_name=payload.original_name,
            )
            replaced += 1

        if len(payloads_for_day) < len(day_items):
            untouched += len(day_items) - len(payloads_for_day)

    connection.encrypted_tokenstore = encrypt_tokenstore(result.refreshed_tokenstore)
    connection.last_sync_at = timezone.now()
    connection.revoked_at = None
    connection.save(update_fields=["encrypted_tokenstore", "last_sync_at", "revoked_at", "updated_at"])
    return replaced, untouched, connection
