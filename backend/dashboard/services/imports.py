from __future__ import annotations

from collections import defaultdict
from datetime import date
import logging

from activities.models import Activity
from activities.services.garmin_importer import connect_garmin_account, download_garmin_fit_payloads

from .imports_fit import import_fit_bytes_for_user, import_fit_bytes_into_planned_for_user, import_fit_for_user
from .imports_garmin import GARMIN_RANGE_OPTIONS, _resolve_garmin_range, audit_garmin, revoke_garmin_for_user
from .imports_matching import (
    _log_multi_day_match,
    _log_single_day_match,
    _match_payloads_to_planned_items,
    _parse_payload_metadata_for_user,
    _planned_day_selection_context,
    _planned_items_for_day,
    _resolve_planned_training,
    _selection_score_for_day,
)
from .imports_garmin import connect_garmin_for_user as _connect_garmin_for_user_impl
from .imports_garmin import sync_garmin_for_user as _sync_garmin_for_user_impl
from .imports_garmin import sync_garmin_week_for_user as _sync_garmin_week_for_user_impl


logger = logging.getLogger(__name__)

__all__ = [
    "GARMIN_RANGE_OPTIONS",
    "audit_garmin",
    "connect_garmin_for_user",
    "import_fit_bytes_for_user",
    "import_fit_bytes_into_planned_for_user",
    "import_fit_for_user",
    "revoke_garmin_for_user",
    "sync_garmin_for_user",
    "sync_garmin_week_for_user",
    "connect_garmin_account",
    "download_garmin_fit_payloads",
    "_parse_payload_metadata_for_user",
    "_resolve_planned_training",
    "_select_payloads_for_import",
]


def _select_payloads_for_import(*, user, payloads):
    if not payloads:
        return []
    prepared = []
    for payload in payloads:
        prepared.append({"payload": payload, **_parse_payload_metadata_for_user(fit_bytes=payload.fit_bytes)})
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
                logger.debug(
                    "Garmin match day=%s mode=multi chosen_ids=%s",
                    run_day,
                    [getattr(row.get("payload"), "activity_id", "") for row in matched],
                )
                selected.extend(matched)
                continue
            selected.extend(day_items)
            continue
        plan_ctx = _planned_day_selection_context(user=user, run_day=run_day)
        best = max(day_items, key=lambda row: _selection_score_for_day(row=row, plan_ctx=plan_ctx))
        _log_single_day_match(run_day=run_day, plan_ctx=plan_ctx, candidates=day_items, chosen=best)
        logger.debug(
            "Garmin match day=%s mode=single chosen_id=%s candidate_ids=%s",
            run_day,
            getattr(best.get("payload"), "activity_id", ""),
            [getattr(row.get("payload"), "activity_id", "") for row in day_items],
        )
        selected.append(best)
    selected.sort(key=lambda row: (row["run_day"], 1 if row["workout_type"] == Activity.WorkoutType.WORKOUT else 0, row["distance_m"], row["duration_s"]))
    return [row["payload"] for row in selected]


def connect_garmin_for_user(user, *, email: str, password: str):
    from . import imports_garmin as garmin_module

    original_connect = garmin_module.connect_garmin_account
    try:
        garmin_module.connect_garmin_account = connect_garmin_account
        return _connect_garmin_for_user_impl(user, email=email, password=password)
    finally:
        garmin_module.connect_garmin_account = original_connect


def sync_garmin_for_user(user, *, window: str, progress_callback=None):
    from . import imports_garmin as garmin_module

    original_download = garmin_module.download_garmin_fit_payloads
    try:
        garmin_module.download_garmin_fit_payloads = download_garmin_fit_payloads
        return _sync_garmin_for_user_impl(user, window=window, progress_callback=progress_callback)
    finally:
        garmin_module.download_garmin_fit_payloads = original_download


def sync_garmin_week_for_user(user, *, week_start: date):
    from . import imports_garmin as garmin_module

    original_download = garmin_module.download_garmin_fit_payloads
    try:
        garmin_module.download_garmin_fit_payloads = download_garmin_fit_payloads
        return _sync_garmin_week_for_user_impl(user, week_start=week_start)
    finally:
        garmin_module.download_garmin_fit_payloads = original_download
