from __future__ import annotations

from datetime import date
from typing import Any, Optional

from django.utils import timezone

from activities.models import Activity
from training.models import CompletedTraining, PlannedTraining

from .month_cards_shared import activity_segment, garmin_match_debug_text, normalize_plan_text, plan_indicates_workout, planned_day_key, planned_km_hint_payload
from .planned_interval_formatter import format_planned_interval_string
from .planned_km import estimate_running_km_from_title, format_week_km_label


def build_planned_rows_for_week(planned_items: list[PlannedTraining], *, language_code: str) -> list[dict[str, Any]]:
    grouped: dict[Any, list[PlannedTraining]] = {}
    for item in planned_items:
        grouped.setdefault(planned_day_key(item), []).append(item)

    def sort_key(key):
        kind, value = key
        return (0, value) if kind == "dated" else (1, value)

    rows: list[dict[str, Any]] = []
    for key in sorted(grouped.keys(), key=sort_key):
        items = sorted(grouped[key], key=lambda x: (x.order_in_day, x.id))
        is_two_phase = any(x.is_two_phase_day for x in items)

        def planned_row_from(subitems: list[PlannedTraining], *, show_date: bool) -> dict[str, Any]:
            if not subitems:
                row = {
                    "planned_id": None,
                    "item_count": 0,
                    "date": items[0].date if show_date else None,
                    "day_label": items[0].day_label if show_date else "",
                    "title": "-",
                    "title_raw": "",
                    "session_type": PlannedTraining.SessionType.RUN,
                    "notes": "",
                    "notes_raw": "",
                    "order_in_day": 1,
                    "is_second_phase": False,
                    "is_two_phase_day": False,
                }
                row.update(planned_km_hint_payload(title_text="", language_code=language_code))
                return row
            first = subitems[0]
            titles = [x.title for x in subitems if x.title]
            notes = [x.notes for x in subitems if x.notes]
            joined_titles = " | ".join(titles) if titles else ""
            joined_notes = " | ".join(notes) if notes else ""
            effective_session_type = PlannedTraining.SessionType.WORKOUT if any((x.session_type or PlannedTraining.SessionType.RUN) == PlannedTraining.SessionType.WORKOUT for x in subitems) else PlannedTraining.SessionType.RUN
            row = {
                "planned_id": first.id,
                "item_count": len(subitems),
                "date": first.date if show_date else None,
                "day_label": first.day_label if show_date else "",
                "title": joined_titles if joined_titles else "-",
                "title_raw": joined_titles,
                "session_type": effective_session_type,
                "notes": joined_notes,
                "notes_raw": joined_notes,
                "order_in_day": int(first.order_in_day or 1),
                "is_second_phase": int(first.order_in_day or 1) > 1,
                "is_two_phase_day": any(x.is_two_phase_day for x in subitems),
            }
            row.update(planned_km_hint_payload(title_text=joined_titles, language_code=language_code))
            return row

        if is_two_phase:
            rows.append(planned_row_from(items[:1], show_date=True))
            rows.append(planned_row_from(items[1:], show_date=False))
        else:
            rows.append(planned_row_from(items, show_date=True))
    return rows


def activity_local_day(activity: Activity) -> date | None:
    if activity.started_at is None:
        return None
    if timezone.is_naive(activity.started_at):
        return activity.started_at.date()
    return timezone.localtime(activity.started_at).date()


def build_completed_row_from_activities(activities: list[Activity], *, show_intervals: bool, planned_titles_by_activity_id: Optional[dict[int, str]] = None, planned_session_types_by_activity_id: Optional[dict[int, str]] = None) -> dict[str, Any]:
    activities = sorted(activities, key=lambda a: (a.started_at is None, a.started_at))
    total_distance_m = sum(int(a.distance_m or 0) for a in activities)
    total_duration_s = sum(int(a.duration_s or 0) for a in activities)
    hr_num = 0
    hr_den = 0
    max_hr = None
    third_parts: list[str] = []
    debug_parts: list[str] = []
    for activity in activities:
        dur = int(activity.duration_s or 0)
        if activity.avg_hr is not None and dur > 0:
            hr_num += int(activity.avg_hr) * dur
            hr_den += dur
        if activity.max_hr is not None:
            max_hr = max(max_hr or 0, int(activity.max_hr))
        seg = activity_segment(activity, show_intervals=show_intervals, planned_title=(planned_titles_by_activity_id or {}).get(activity.id, ""))
        if seg != "-":
            third_parts.append(seg)
        debug_parts.append(garmin_match_debug_text(activity, planned_title=(planned_titles_by_activity_id or {}).get(activity.id, ""), session_type=(planned_session_types_by_activity_id or {}).get(activity.id, "")))
    duration_min = int(round(total_duration_s / 60.0)) if total_duration_s > 0 else 0
    avg_hr = int(round(hr_num / hr_den)) if hr_den > 0 else None
    return {"km": f"{total_distance_m / 1000.0:.2f}" if total_distance_m > 0 else "", "min": str(duration_min) if duration_min > 0 else "", "third": " | ".join(third_parts) if third_parts else "", "match_debug": " | ".join(part for part in debug_parts if part), "avg_hr": avg_hr, "max_hr": max_hr, "_distance_m": total_distance_m, "_duration_min": duration_min}


def build_completed_row_for_unplanned_activity(activity: Activity) -> dict[str, Any]:
    show_intervals = any((it.distance_m or 0) > 0 or (it.duration_s or 0) > 0 for it in activity.intervals.all())
    if not show_intervals:
        show_intervals = (activity.workout_type or "") == Activity.WorkoutType.WORKOUT
    row = build_completed_row_from_activities([activity], show_intervals=show_intervals)
    descriptor_parts = []
    if activity.title:
        descriptor_parts.append(activity.title)
    if row["third"]:
        descriptor_parts.append(row["third"])
    row["third"] = " | ".join(descriptor_parts) if descriptor_parts else ""
    row["planned_id"] = None
    row["item_count"] = 1
    row["has_linked_activity"] = True
    return row


def build_completed_rows_for_week(planned_items: list[PlannedTraining], *, extra_activities: list[Activity] | None = None) -> list[dict[str, Any]]:
    grouped: dict[Any, list[PlannedTraining]] = {}
    for item in planned_items:
        grouped.setdefault(("dated", item.date) if item.date is not None else ("undated", item.id), []).append(item)
    extra_by_day: dict[date, list[Activity]] = {}
    for activity in extra_activities or []:
        activity_day = activity_local_day(activity)
        if activity_day is not None:
            extra_by_day.setdefault(activity_day, []).append(activity)

    def items_have_linked_activity(subitems: list[PlannedTraining]) -> bool:
        for item in subitems:
            if getattr(item, "activity", None) is not None:
                return True
            completed = getattr(item, "completed", None)
            if completed is not None and getattr(completed, "activity_id", None):
                return True
        return False

    def apply_manual_overrides(row: dict[str, Any], completed: CompletedTraining | None) -> None:
        if completed is None:
            return
        if completed.distance_m is not None:
            distance_m = int(completed.distance_m)
            row["_distance_m"] = distance_m
            row["km"] = f"{distance_m / 1000.0:.2f}" if distance_m > 0 else ""
        if completed.time_seconds is not None:
            duration_min = int(round(int(completed.time_seconds) / 60.0))
            row["_duration_min"] = duration_min
            row["min"] = str(duration_min) if duration_min > 0 else ""
        if completed.avg_hr is not None:
            row["avg_hr"] = int(completed.avg_hr)
        if completed.note:
            row["third"] = completed.note
        if completed.feel and completed.feel.strip().isdigit():
            row["max_hr"] = int(completed.feel.strip())

    def show_intervals_for(subitems: list[PlannedTraining], sub_activities: list[Activity]) -> bool:
        if any((x.session_type or PlannedTraining.SessionType.RUN) == PlannedTraining.SessionType.WORKOUT for x in subitems):
            return True
        if subitems and all((x.session_type or PlannedTraining.SessionType.RUN) == PlannedTraining.SessionType.RUN for x in subitems):
            return False
        title = " ".join((x.title or "") for x in subitems)
        notes = " ".join((x.notes or "") for x in subitems)
        if plan_indicates_workout(title=title, notes=notes):
            return True
        if normalize_plan_text(f"{title} {notes}"):
            return False
        has_work_intervals = any(format_planned_interval_string("", list(a.intervals.all())) != "-" for a in sub_activities)
        if has_work_intervals:
            return True
        return any((a.workout_type or "") == "WORKOUT" for a in sub_activities)

    rows: list[dict[str, Any]] = []
    all_keys = set(grouped.keys()) | {("dated", activity_day) for activity_day in extra_by_day.keys()}
    for key in sorted(all_keys, key=lambda x: (x[0] == "undated", x[1])):
        items = sorted(grouped.get(key, []), key=lambda x: (x.order_in_day, x.id))
        is_two_phase = any(x.is_two_phase_day for x in items)
        if items and is_two_phase:
            phase_1_items = items[:1]
            phase_2_items = items[1:]
            phase_1_activities = [x.activity for x in phase_1_items if getattr(x, "activity", None)]
            phase_2_activities = [x.activity for x in phase_2_items if getattr(x, "activity", None)]
            phase_1_titles = {x.activity.id: x.title or "" for x in phase_1_items if getattr(x, "activity", None)}
            phase_2_titles = {x.activity.id: x.title or "" for x in phase_2_items if getattr(x, "activity", None)}
            phase_1_session_types = {x.activity.id: (x.session_type or PlannedTraining.SessionType.RUN) for x in phase_1_items if getattr(x, "activity", None)}
            phase_2_session_types = {x.activity.id: (x.session_type or PlannedTraining.SessionType.RUN) for x in phase_2_items if getattr(x, "activity", None)}
            phase_1_row = build_completed_row_from_activities(phase_1_activities, show_intervals=show_intervals_for(phase_1_items, phase_1_activities), planned_titles_by_activity_id=phase_1_titles, planned_session_types_by_activity_id=phase_1_session_types)
            phase_1_row["planned_id"] = phase_1_items[0].id if phase_1_items else None
            phase_1_row["item_count"] = len(phase_1_items)
            phase_1_row["has_linked_activity"] = items_have_linked_activity(phase_1_items)
            if len(phase_1_items) == 1:
                apply_manual_overrides(phase_1_row, getattr(phase_1_items[0], "completed", None))
            rows.append(phase_1_row)
            phase_2_row = build_completed_row_from_activities(phase_2_activities, show_intervals=show_intervals_for(phase_2_items, phase_2_activities), planned_titles_by_activity_id=phase_2_titles, planned_session_types_by_activity_id=phase_2_session_types)
            phase_2_row["planned_id"] = phase_2_items[0].id if phase_2_items else None
            phase_2_row["item_count"] = len(phase_2_items)
            phase_2_row["has_linked_activity"] = items_have_linked_activity(phase_2_items)
            if len(phase_2_items) == 1:
                apply_manual_overrides(phase_2_row, getattr(phase_2_items[0], "completed", None))
            day_distance_m = int(phase_1_row.get("_distance_m") or 0) + int(phase_2_row.get("_distance_m") or 0)
            day_duration_min = int(phase_1_row.get("_duration_min") or 0) + int(phase_2_row.get("_duration_min") or 0)
            phase_2_row["km"] = f"{day_distance_m / 1000.0:.2f}" if day_distance_m > 0 else ""
            phase_2_row["min"] = str(day_duration_min) if day_duration_min > 0 else ""
            rows.append(phase_2_row)
        elif items:
            day_activities = [x.activity for x in items if getattr(x, "activity", None)]
            planned_titles = {x.activity.id: x.title or "" for x in items if getattr(x, "activity", None)}
            planned_session_types = {x.activity.id: (x.session_type or PlannedTraining.SessionType.RUN) for x in items if getattr(x, "activity", None)}
            row = build_completed_row_from_activities(day_activities, show_intervals=show_intervals_for(items, day_activities), planned_titles_by_activity_id=planned_titles, planned_session_types_by_activity_id=planned_session_types)
            row["planned_id"] = items[0].id if items else None
            row["item_count"] = len(items)
            row["has_linked_activity"] = items_have_linked_activity(items)
            if len(items) == 1:
                apply_manual_overrides(row, getattr(items[0], "completed", None))
            rows.append(row)
        if key[0] == "dated":
            for activity in sorted(extra_by_day.get(key[1], []), key=lambda a: (a.started_at is None, a.started_at, a.id)):
                rows.append(build_completed_row_for_unplanned_activity(activity))
    return rows


def sum_week_total(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_distance_m = 0
    min_sum = 0
    hr_num = 0
    hr_den = 0
    max_hr = None
    for row in rows:
        distance_m = int(row.get("_distance_m") or 0)
        minutes = int(row.get("_duration_min") or 0)
        total_distance_m += distance_m
        min_sum += minutes
        if row.get("avg_hr") is not None and minutes > 0:
            hr_num += int(row["avg_hr"]) * minutes
            hr_den += minutes
        if row.get("max_hr") is not None:
            max_hr = max(max_hr or 0, int(row["max_hr"]))
    avg_hr = int(round(hr_num / hr_den)) if hr_den > 0 else None
    return {"km": f"{total_distance_m / 1000.0:.2f}" if total_distance_m > 0 else "-", "time": str(min_sum) if min_sum > 0 else "-", "avg_hr": avg_hr, "max_hr": max_hr}


def sum_planned_week_km(planned_items: list[PlannedTraining]) -> float:
    total = 0.0
    for planned in planned_items:
        extracted = estimate_running_km_from_title(planned.title)
        if extracted is not None:
            total += float(extracted)
    return total


def planned_week_km_label(planned_items: list[PlannedTraining], language_code: str) -> str:
    return format_week_km_label(sum_planned_week_km(planned_items), language_code)
