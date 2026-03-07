from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

from django.db.models import Prefetch
from django.utils import timezone

from accounts.models import Role
from activities.models import Activity, ActivityInterval
from training.models import CompletedTraining, PlannedTraining, TrainingMonth, TrainingWeek


CZ_MONTHS = {
    1: "Leden",
    2: "\u00danor",
    3: "B\u0159ezen",
    4: "Duben",
    5: "Kv\u011bten",
    6: "\u010cerven",
    7: "\u010cervenec",
    8: "Srpen",
    9: "Z\u00e1\u0159\u00ed",
    10: "\u0158\u00edjen",
    11: "Listopad",
    12: "Prosinec",
}
EN_MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def _fmt_mmss(seconds: Optional[int]) -> str:
    if seconds is None:
        return "-"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def _work_intervals(intervals: list[ActivityInterval]) -> list[ActivityInterval]:
    return [it for it in intervals if (it.distance_m or 0) >= 200 and (it.duration_s or 0) >= 30]


def _fmt_intervals(intervals: list[ActivityInterval]) -> str:
    work = _work_intervals(intervals)
    if not work:
        return "-"

    out = []
    for it in work:
        d = it.duration_s or 0
        out.append(str(d) if d < 60 else _fmt_mmss(d))
    return "(" + ", ".join(out) + ")"


def _activity_segment(a: Activity) -> str:
    if (a.workout_type or "RUN") == "WORKOUT":
        intervals = list(a.intervals.all())
        return _fmt_intervals(intervals)

    pace = _fmt_mmss(a.avg_pace_s_per_km)
    if pace == "-":
        return "-"
    return f"{pace}/km"


def _planned_day_key(t: PlannedTraining):
    if t.date is None:
        return ("undated", t.id)
    return ("dated", t.date)


def _build_planned_rows_for_week(planned_items: list[PlannedTraining]) -> list[dict[str, Any]]:
    grouped: dict[Any, list[PlannedTraining]] = {}
    for t in planned_items:
        grouped.setdefault(_planned_day_key(t), []).append(t)

    def sort_key(k):
        kind, value = k
        return (0, value) if kind == "dated" else (1, value)

    rows: list[dict[str, Any]] = []
    for key in sorted(grouped.keys(), key=sort_key):
        items = sorted(grouped[key], key=lambda x: (x.order_in_day, x.id))
        is_two_phase = any(x.is_two_phase_day for x in items)

        def planned_row_from(subitems: list[PlannedTraining], *, show_date: bool) -> dict[str, Any]:
            if not subitems:
                return {
                    "planned_id": None,
                    "item_count": 0,
                    "date": items[0].date if show_date else None,
                    "day_label": items[0].day_label if show_date else "",
                    "title": "-",
                    "title_raw": "",
                    "notes": "",
                    "notes_raw": "",
                }
            first = subitems[0]
            titles = [x.title for x in subitems if x.title]
            notes = [x.notes for x in subitems if x.notes]
            joined_titles = " | ".join(titles) if titles else ""
            joined_notes = " | ".join(notes) if notes else ""
            return {
                "planned_id": first.id,
                "item_count": len(subitems),
                "date": first.date if show_date else None,
                "day_label": first.day_label if show_date else "",
                "title": joined_titles if joined_titles else "-",
                "title_raw": joined_titles,
                "notes": joined_notes,
                "notes_raw": joined_notes,
            }

        if is_two_phase:
            rows.append(planned_row_from(items[:1], show_date=True))
            rows.append(planned_row_from(items[1:], show_date=False))
        else:
            rows.append(planned_row_from(items, show_date=True))
    return rows


def _build_completed_row_from_activities(activities: list[Activity]) -> dict[str, Any]:
    activities = sorted(activities, key=lambda a: (a.started_at is None, a.started_at))
    total_distance_m = sum(int(a.distance_m or 0) for a in activities)
    total_duration_s = sum(int(a.duration_s or 0) for a in activities)

    hr_num = 0
    hr_den = 0
    max_hr = None
    third_parts: list[str] = []

    for a in activities:
        dur = int(a.duration_s or 0)
        if a.avg_hr is not None and dur > 0:
            hr_num += int(a.avg_hr) * dur
            hr_den += dur
        if a.max_hr is not None:
            max_hr = max(max_hr or 0, int(a.max_hr))

        seg = _activity_segment(a)
        if seg != "-":
            third_parts.append(seg)

    km = f"{total_distance_m / 1000.0:.2f}" if total_distance_m > 0 else "-"
    duration_min = int(round(total_duration_s / 60.0)) if total_duration_s > 0 else 0
    minutes = str(duration_min) if duration_min > 0 else "-"
    avg_hr = int(round(hr_num / hr_den)) if hr_den > 0 else None

    return {
        "km": km,
        "min": minutes,
        "third": " | ".join(third_parts) if third_parts else "-",
        "avg_hr": avg_hr,
        "max_hr": max_hr,
        "_distance_m": total_distance_m,
        "_duration_min": duration_min,
    }


def _build_completed_rows_for_week(planned_items: list[PlannedTraining]) -> list[dict[str, Any]]:
    grouped: dict[Any, list[PlannedTraining]] = {}
    for t in planned_items:
        key = ("dated", t.date) if t.date is not None else ("undated", t.id)
        grouped.setdefault(key, []).append(t)

    def _apply_manual_overrides(row: dict[str, Any], completed: CompletedTraining | None) -> None:
        if completed is None:
            return

        if completed.distance_m is not None:
            distance_m = int(completed.distance_m)
            row["_distance_m"] = distance_m
            row["km"] = f"{distance_m / 1000.0:.2f}" if distance_m > 0 else "-"

        if completed.time_seconds is not None:
            duration_min = int(round(int(completed.time_seconds) / 60.0))
            row["_duration_min"] = duration_min
            row["min"] = str(duration_min) if duration_min > 0 else "-"

        if completed.avg_hr is not None:
            row["avg_hr"] = int(completed.avg_hr)

        if completed.note:
            row["third"] = completed.note

        if completed.feel:
            feel = completed.feel.strip()
            if feel.isdigit():
                row["max_hr"] = int(feel)

    rows: list[dict[str, Any]] = []
    for key in sorted(grouped.keys(), key=lambda x: (x[0] == "undated", x[1])):
        items = sorted(grouped[key], key=lambda x: (x.order_in_day, x.id))
        is_two_phase = any(x.is_two_phase_day for x in items)

        if is_two_phase:
            phase_1_items = items[:1]
            phase_2_items = items[1:]

            phase_1_activities = [x.activity for x in phase_1_items if getattr(x, "activity", None)]
            phase_2_activities = [x.activity for x in phase_2_items if getattr(x, "activity", None)]

            phase_1_row = _build_completed_row_from_activities(phase_1_activities)
            phase_1_row["planned_id"] = phase_1_items[0].id if len(phase_1_items) == 1 else None
            phase_1_row["item_count"] = len(phase_1_items)
            if len(phase_1_items) == 1:
                _apply_manual_overrides(phase_1_row, getattr(phase_1_items[0], "completed", None))
            rows.append(phase_1_row)

            phase_2_row = _build_completed_row_from_activities(phase_2_activities)
            phase_2_row["planned_id"] = phase_2_items[0].id if len(phase_2_items) == 1 else None
            phase_2_row["item_count"] = len(phase_2_items)
            if len(phase_2_items) == 1:
                _apply_manual_overrides(phase_2_row, getattr(phase_2_items[0], "completed", None))
            rows.append(phase_2_row)
        else:
            day_activities = [x.activity for x in items if getattr(x, "activity", None)]
            row = _build_completed_row_from_activities(day_activities)
            row["planned_id"] = items[0].id if len(items) == 1 else None
            row["item_count"] = len(items)
            if len(items) == 1:
                _apply_manual_overrides(row, getattr(items[0], "completed", None))
            rows.append(row)

    return rows


def _sum_week_total(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_distance_m = 0
    min_sum = 0
    hr_num = 0
    hr_den = 0
    max_hr = None

    for r in rows:
        distance_m = int(r.get("_distance_m") or 0)
        m = int(r.get("_duration_min") or 0)
        total_distance_m += distance_m
        min_sum += m

        if r.get("avg_hr") is not None and m > 0:
            hr_num += int(r["avg_hr"]) * m
            hr_den += m

        if r.get("max_hr") is not None:
            max_hr = max(max_hr or 0, int(r["max_hr"]))

    avg_hr = int(round(hr_num / hr_den)) if hr_den > 0 else None
    return {
        "km": f"{total_distance_m / 1000.0:.2f}" if total_distance_m > 0 else "-",
        "time": str(min_sum) if min_sum > 0 else "-",
        "avg_hr": avg_hr,
        "max_hr": max_hr,
    }


def _week_index_in_month(d: date) -> int:
    first_day = d.replace(day=1)
    shift = (7 - first_day.weekday()) % 7
    first_monday = first_day + timedelta(days=shift)
    return ((d - first_monday).days // 7) + 1


def _week_start_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def resolve_week_for_day(user, run_day: date) -> TrainingWeek:
    week_start = _week_start_monday(run_day)
    month_obj, _ = TrainingMonth.objects.get_or_create(
        athlete=user,
        year=week_start.year,
        month=week_start.month,
    )

    planned_on_day = (
        PlannedTraining.objects.filter(week__training_month=month_obj, date=run_day)
        .select_related("week")
        .order_by("week__week_index", "order_in_day", "id")
        .first()
    )
    if planned_on_day:
        return planned_on_day.week

    week_index = _week_index_in_month(week_start)
    week_obj, _ = TrainingWeek.objects.get_or_create(training_month=month_obj, week_index=week_index)
    return week_obj


def build_month_cards_for_athlete(*, athlete, language_code: str) -> list[dict[str, Any]]:
    months_qs = (
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
                                    Prefetch(
                                        "activity__intervals",
                                        queryset=ActivityInterval.objects.filter(activity__workout_type="WORKOUT").order_by("index"),
                                    )
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

    month_dict = CZ_MONTHS if language_code.startswith("cs") else EN_MONTHS
    month_cards = []
    for m in months_qs:
        weeks_out = []
        for w in list(m.weeks.all()):
            planned_items = list(w.planned_trainings.all())
            w.planned_rows = _build_planned_rows_for_week(planned_items)
            w.completed_rows = _build_completed_rows_for_week(planned_items)
            w.completed_total = _sum_week_total(w.completed_rows)
            weeks_out.append(w)

        month_cards.append({"id": m.id, "label": f"{month_dict.get(m.month, str(m.month))} {m.year}", "weeks": weeks_out})
    return month_cards


def _first_monday_in_month(year: int, month: int) -> date:
    first_day = date(year, month, 1)
    shift = (7 - first_day.weekday()) % 7
    return first_day + timedelta(days=shift)


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    out_year = total // 12
    out_month = (total % 12) + 1
    return out_year, out_month


def add_next_month_for_athlete(*, athlete) -> tuple[bool, int, int]:
    latest = TrainingMonth.objects.filter(athlete=athlete).order_by("-year", "-month").first()

    if latest is None:
        start = timezone.localdate().replace(day=1)
        target_year, target_month = start.year, start.month
    else:
        target_year, target_month = _shift_month(latest.year, latest.month, 1)

    month_obj, month_created = TrainingMonth.objects.get_or_create(
        athlete=athlete,
        year=target_year,
        month=target_month,
    )

    day_labels = ["Po", "\u00dat", "St", "\u010ct", "P\u00e1", "So", "Ne"]

    monday = _first_monday_in_month(target_year, target_month)
    week_starts: list[tuple[int, date]] = []
    week_index = 1
    while monday.month == target_month:
        week_starts.append((week_index, monday))
        monday += timedelta(days=7)
        week_index += 1

    existing_weeks = {
        w.week_index: w
        for w in TrainingWeek.objects.filter(
            training_month=month_obj,
            week_index__in=[idx for idx, _ in week_starts],
        )
    }

    new_weeks = [
        TrainingWeek(training_month=month_obj, week_index=idx)
        for idx, _ in week_starts
        if idx not in existing_weeks
    ]
    if new_weeks:
        TrainingWeek.objects.bulk_create(new_weeks, batch_size=50)

    weeks_by_index = {
        w.week_index: w
        for w in TrainingWeek.objects.filter(
            training_month=month_obj,
            week_index__in=[idx for idx, _ in week_starts],
        )
    }

    existing_days = set(
        PlannedTraining.objects.filter(
            week__training_month=month_obj,
            week__week_index__in=[idx for idx, _ in week_starts],
            order_in_day=1,
            date__isnull=False,
        ).values_list("week__week_index", "date")
    )

    missing_days = []
    for idx, week_start in week_starts:
        for offset, day_label in enumerate(day_labels):
            run_day = week_start + timedelta(days=offset)
            day_key = (idx, run_day)
            if day_key in existing_days:
                continue
            missing_days.append(
                PlannedTraining(
                    week=weeks_by_index[idx],
                    date=run_day,
                    order_in_day=1,
                    day_label=day_label,
                    title="",
                    notes="",
                )
            )

    if missing_days:
        PlannedTraining.objects.bulk_create(missing_days, batch_size=200)

    return month_created, len(new_weeks), len(missing_days)


def is_coach(user) -> bool:
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == Role.COACH)


def display_name(user) -> str:
    if user.first_name or user.last_name:
        return f"{user.first_name} {user.last_name}".strip()
    return user.username
