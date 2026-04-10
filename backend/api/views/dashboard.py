from __future__ import annotations

from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.http import JsonResponse
from django.utils import timezone

from accounts.models import Role
from activities.models import Activity, ActivityInterval
from dashboard.services.month_cards_calendar import week_start_for_month_index
from dashboard.services.month_cards_rows import (
    activity_local_day,
    build_completed_rows_for_week,
    build_planned_rows_for_week,
    planned_week_km_label,
    sum_week_total,
)
from dashboard.services.month_cards_shared import CZ_MONTHS, EN_MONTHS
from training.models import PlannedTraining, TrainingMonth, TrainingWeek


def _parse_month_query(raw_value: str | None) -> tuple[int, int] | None:
    raw = (raw_value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.strptime(raw, "%Y-%m")
    except ValueError:
        return None
    return parsed.year, parsed.month


def _month_label(year: int, month: int, language_code: str) -> str:
    month_dict = CZ_MONTHS if language_code.startswith("cs") else EN_MONTHS
    return f"{month_dict.get(month, str(month))} {year}"


def _is_substantive_planned_row(row: dict) -> bool:
    return bool(
        (row.get("title_raw") or "").strip()
        or (row.get("notes_raw") or "").strip()
        or float(row.get("planned_km_value") or 0) > 0
    )


def _is_substantive_completed_row(row: dict) -> bool:
    return bool(
        (row.get("km") or "").strip()
        or (row.get("min") or "").strip()
        or (row.get("third") or "").strip()
        or row.get("avg_hr") is not None
        or row.get("max_hr") is not None
        or row.get("has_linked_activity")
    )


def _serialize_planned_row(row: dict) -> dict:
    status = "rest" if not _is_substantive_planned_row(row) else "planned"
    is_second_phase = bool(row.get("is_second_phase"))
    is_two_phase_day = bool(row.get("is_two_phase_day"))
    has_date = bool(row.get("date"))
    return {
        "id": row.get("planned_id"),
        "kind": "planned",
        "status": status,
        "date": row.get("date").isoformat() if row.get("date") else None,
        "day_label": row.get("day_label") or "",
        "title": row.get("title") or "-",
        "notes": row.get("notes") or "",
        "session_type": row.get("session_type") or PlannedTraining.SessionType.RUN,
        "planned_metrics": {
            "planned_km_value": row.get("planned_km_value") or 0,
            "planned_km_text": row.get("planned_km_text") or "",
            "planned_km_confidence": row.get("planned_km_confidence") or "low",
            "planned_km_show": bool(row.get("planned_km_show")),
            "planned_km_line_km": row.get("planned_km_line_km") or "",
            "planned_km_line_reason": row.get("planned_km_line_reason") or "",
            "planned_km_line_where": row.get("planned_km_line_where") or "",
        },
        "completed_metrics": None,
        "editable": bool(row.get("planned_id")),
        "is_second_phase": is_second_phase,
        "can_add_second_phase": bool(row.get("planned_id")) and has_date and not is_two_phase_day and not is_second_phase,
        "can_remove_second_phase": bool(row.get("planned_id")) and is_second_phase,
    }


def _serialize_completed_row(row: dict) -> dict:
    status = "done" if _is_substantive_completed_row(row) else "missed"
    return {
        "id": row.get("planned_id"),
        "kind": "completed",
        "status": status,
        "date": None,
        "day_label": "",
        "title": "",
        "notes": row.get("third") or "",
        "session_type": PlannedTraining.SessionType.RUN,
        "planned_metrics": None,
        "completed_metrics": {
            "km": row.get("km") or "",
            "minutes": row.get("min") or "",
            "details": row.get("third") or "",
            "avg_hr": row.get("avg_hr"),
            "max_hr": row.get("max_hr"),
        },
        "editable": bool(row.get("planned_id")),
        "has_linked_activity": bool(row.get("has_linked_activity")),
    }


def _build_month_summary(weeks_payload: list[dict]) -> dict:
    planned_sessions = 0
    completed_sessions = 0
    planned_km = 0.0
    completed_km = 0.0
    completed_minutes = 0

    for week in weeks_payload:
        for planned_row in week["planned_rows"]:
            if _is_substantive_planned_row(planned_row):
                planned_sessions += 1
                planned_km += float(planned_row.get("planned_km_value") or 0)
        for completed_row in week["completed_rows"]:
            if _is_substantive_completed_row(completed_row):
                completed_sessions += 1
        completed_total = week["completed_total"]
        try:
            completed_km += float((completed_total.get("km") or "0").replace(",", "."))
        except ValueError:
            completed_km += 0.0
        try:
            completed_minutes += int(completed_total.get("time") or 0)
        except ValueError:
            completed_minutes += 0

    completion_rate = round((completed_sessions / planned_sessions) * 100) if planned_sessions else 0
    return {
        "planned_sessions": planned_sessions,
        "completed_sessions": completed_sessions,
        "planned_km": round(planned_km, 1),
        "completed_km": round(completed_km, 1),
        "completed_minutes": completed_minutes,
        "completion_rate": completion_rate,
    }


def build_dashboard_payload_for_athlete(
    *,
    athlete,
    language_code: str,
    month_query: str | None = None,
    flags: dict | None = None,
):
    month_qs = (
        TrainingMonth.objects.filter(athlete=athlete)
        .prefetch_related(
            Prefetch(
                "weeks",
                queryset=(
                    TrainingWeek.objects.all()
                    .prefetch_related(
                        Prefetch(
                            "planned_trainings",
                            queryset=(
                                PlannedTraining.objects.select_related("activity", "completed")
                                .prefetch_related(
                                    Prefetch("activity__intervals", queryset=ActivityInterval.objects.order_by("index"))
                                )
                                .order_by("date", "id")
                            ),
                        )
                    )
                    .order_by("week_index", "id")
                ),
            )
        )
        .order_by("-year", "-month")
    )
    months = list(month_qs)
    selected_token = _parse_month_query(month_query)

    selected_month = None
    if selected_token is not None:
        selected_month = next(
            (month for month in months if month.year == selected_token[0] and month.month == selected_token[1]),
            None,
        )
    if selected_month is None and months:
        selected_month = months[0]

    default_flags = {
        "is_coach": False,
        "can_edit_planned": True,
        "can_edit_completed": True,
    }
    effective_flags = {
        **default_flags,
        **(flags or {}),
    }

    if selected_month is None:
        return {
            "selected_month": None,
            "navigation": {"previous": None, "next": None, "available": []},
            "summary": {
                "planned_sessions": 0,
                "completed_sessions": 0,
                "planned_km": 0,
                "completed_km": 0,
                "completed_minutes": 0,
                "completion_rate": 0,
            },
            "weeks": [],
            "flags": effective_flags,
        }

    available = [
        {
            "id": month.id,
            "value": f"{month.year:04d}-{month.month:02d}",
            "label": _month_label(month.year, month.month, language_code),
        }
        for month in months
    ]
    selected_index = next(index for index, month in enumerate(months) if month.id == selected_month.id)
    previous_month = months[selected_index + 1] if selected_index + 1 < len(months) else None
    next_month = months[selected_index - 1] if selected_index - 1 >= 0 else None

    today = timezone.localdate()
    week_ranges: list[tuple[int, object, object]] = []
    week_entries: list[dict] = []
    weeks_payload: list[dict] = []
    for week in list(selected_month.weeks.all()):
        planned_items = list(week.planned_trainings.all())
        week_start = week_start_for_month_index(
            year=selected_month.year,
            month=selected_month.month,
            week_index=week.week_index,
        )
        week_end = week_start + timedelta(days=6)
        week_ranges.append((week.id, week_start, week_end))
        week_entries.append(
            {
                "week": week,
                "planned_items": planned_items,
                "week_start": week_start,
                "week_end": week_end,
                "has_started": week_start <= today,
            }
        )

    extra_by_week_id: dict[int, list[Activity]] = {}
    if week_ranges:
        min_day = min(start for _, start, _ in week_ranges)
        max_day = max(end for _, _, end in week_ranges)
        unplanned_activities = list(
            Activity.objects.filter(
                athlete=athlete,
                planned_training__isnull=True,
                started_at__isnull=False,
                started_at__date__range=(min_day, max_day),
            )
            .prefetch_related(Prefetch("intervals", queryset=ActivityInterval.objects.order_by("index")))
            .order_by("started_at", "id")
        )
        for activity in unplanned_activities:
            activity_day = activity_local_day(activity)
            if activity_day is None:
                continue
            for week_id, week_start, week_end in week_ranges:
                if week_start <= activity_day <= week_end:
                    extra_by_week_id.setdefault(week_id, []).append(activity)
                    break

    for week_entry in week_entries:
        week = week_entry["week"]
        planned_items = week_entry["planned_items"]
        planned_rows = build_planned_rows_for_week(planned_items, language_code=language_code)
        completed_rows = build_completed_rows_for_week(
            planned_items,
            extra_activities=extra_by_week_id.get(week.id, []),
        )
        weeks_payload.append(
            {
                "id": week.id,
                "week_index": week.week_index,
                "week_start": week_entry["week_start"].isoformat(),
                "week_end": week_entry["week_end"].isoformat(),
                "has_started": week_entry["has_started"],
                "planned_total_km_text": planned_week_km_label(planned_items, language_code),
                "completed_total": sum_week_total(completed_rows),
                "planned_rows": planned_rows,
                "completed_rows": completed_rows,
            }
        )

    summary = _build_month_summary(weeks_payload)
    serialized_weeks = [
        {
            "id": week["id"],
            "week_index": week["week_index"],
            "week_start": week["week_start"],
            "week_end": week["week_end"],
            "has_started": week["has_started"],
            "planned_total_km_text": week["planned_total_km_text"],
            "completed_total": week["completed_total"],
            "planned_rows": [
                {
                    **_serialize_planned_row(row),
                    "editable": bool(effective_flags.get("can_edit_planned")) and bool(row.get("planned_id")),
                }
                for row in week["planned_rows"]
            ],
            "completed_rows": [
                {
                    **_serialize_completed_row(row),
                    "editable": bool(effective_flags.get("can_edit_completed")) and bool(row.get("planned_id")),
                }
                for row in week["completed_rows"]
            ],
        }
        for week in weeks_payload
    ]

    return {
        "selected_month": {
            "id": selected_month.id,
            "value": f"{selected_month.year:04d}-{selected_month.month:02d}",
            "label": _month_label(selected_month.year, selected_month.month, language_code),
            "year": selected_month.year,
            "month": selected_month.month,
        },
        "navigation": {
            "previous": (
                {
                    "value": f"{previous_month.year:04d}-{previous_month.month:02d}",
                    "label": _month_label(previous_month.year, previous_month.month, language_code),
                }
                if previous_month
                else None
            ),
            "next": (
                {
                    "value": f"{next_month.year:04d}-{next_month.month:02d}",
                    "label": _month_label(next_month.year, next_month.month, language_code),
                }
                if next_month
                else None
            ),
            "available": available,
        },
        "summary": summary,
        "weeks": serialized_weeks,
        "flags": effective_flags,
    }


@login_required
def athlete_dashboard(request):
    language_code = getattr(request, "LANGUAGE_CODE", "cs")
    response = build_dashboard_payload_for_athlete(
        athlete=request.user,
        language_code=language_code,
        month_query=request.GET.get("month"),
        flags={
            "is_coach": getattr(getattr(request.user, "profile", None), "role", Role.ATHLETE) == Role.COACH,
            "can_edit_planned": True,
            "can_edit_completed": True,
        },
    )
    return JsonResponse(response)
