from __future__ import annotations

from datetime import date, timedelta

from django.db.models import Prefetch
from django.utils import timezone

from accounts.models import Role
from activities.models import Activity, ActivityInterval
from training.models import PlannedTraining, TrainingMonth, TrainingWeek

from .month_cards_rows import activity_local_day, build_completed_rows_for_week, build_planned_rows_for_week, planned_week_km_label, sum_week_total
from .month_cards_shared import CZ_MONTHS, EN_MONTHS


def week_index_in_month(day_value: date) -> int:
    first_day = day_value.replace(day=1)
    shift = (7 - first_day.weekday()) % 7
    first_monday = first_day + timedelta(days=shift)
    return ((day_value - first_monday).days // 7) + 1


def week_start_monday(day_value: date) -> date:
    return day_value - timedelta(days=day_value.weekday())


def week_start_for_month_index(*, year: int, month: int, week_index: int) -> date:
    first_monday = first_monday_in_month(year, month)
    return first_monday + timedelta(days=max(0, int(week_index) - 1) * 7)


def resolve_week_for_day(user, run_day: date) -> TrainingWeek:
    week_start = week_start_monday(run_day)
    month_obj, _ = TrainingMonth.objects.get_or_create(athlete=user, year=week_start.year, month=week_start.month)
    planned_on_day = (
        PlannedTraining.objects.filter(week__training_month=month_obj, date=run_day)
        .select_related("week")
        .order_by("week__week_index", "order_in_day", "id")
        .first()
    )
    if planned_on_day:
        return planned_on_day.week
    week_index = week_index_in_month(week_start)
    week_obj, _ = TrainingWeek.objects.get_or_create(training_month=month_obj, week_index=week_index)
    return week_obj


def build_month_cards_for_athlete(*, athlete, language_code: str) -> list[dict]:
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
                                .prefetch_related(Prefetch("activity__intervals", queryset=ActivityInterval.objects.order_by("index")))
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
    today = timezone.localdate()
    week_ranges: list[tuple[int, date, date]] = []
    for month in months_qs:
        weeks_out = []
        for week in list(month.weeks.all()):
            planned_items = list(week.planned_trainings.all())
            week.week_start = week_start_for_month_index(year=month.year, month=month.month, week_index=week.week_index)
            week.week_end = week.week_start + timedelta(days=6)
            week_ranges.append((week.id, week.week_start, week.week_end))
            week.has_started = week.week_start <= today
            weeks_out.append((week, planned_items))
        month_cards.append({"id": month.id, "label": f"{month_dict.get(month.month, str(month.month))} {month.year}", "weeks": weeks_out})

    unplanned_by_week_id: dict[int, list[Activity]] = {}
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
                    unplanned_by_week_id.setdefault(week_id, []).append(activity)
                    break

    for month_card in month_cards:
        resolved_weeks = []
        for week_obj, planned_items in month_card["weeks"]:
            week_obj.planned_rows = build_planned_rows_for_week(planned_items, language_code=language_code)
            week_obj.planned_total_km_text = planned_week_km_label(planned_items, language_code)
            week_obj.completed_rows = build_completed_rows_for_week(planned_items, extra_activities=unplanned_by_week_id.get(week_obj.id, []))
            week_obj.completed_total = sum_week_total(week_obj.completed_rows)
            resolved_weeks.append(week_obj)
        month_card["weeks"] = resolved_weeks
    return month_cards


def first_monday_in_month(year: int, month: int) -> date:
    first_day = date(year, month, 1)
    shift = (7 - first_day.weekday()) % 7
    return first_day + timedelta(days=shift)


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    out_year = total // 12
    out_month = (total % 12) + 1
    return out_year, out_month


def ensure_month_for_athlete(*, athlete, year: int, month: int) -> tuple[bool, int, int]:
    month_obj, month_created = TrainingMonth.objects.get_or_create(athlete=athlete, year=year, month=month)
    day_labels = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]
    monday = first_monday_in_month(year, month)
    week_starts: list[tuple[int, date]] = []
    week_index = 1
    while monday.month == month:
        week_starts.append((week_index, monday))
        monday += timedelta(days=7)
        week_index += 1
    existing_weeks = {week.week_index: week for week in TrainingWeek.objects.filter(training_month=month_obj, week_index__in=[idx for idx, _ in week_starts])}
    new_weeks = [TrainingWeek(training_month=month_obj, week_index=idx) for idx, _ in week_starts if idx not in existing_weeks]
    if new_weeks:
        TrainingWeek.objects.bulk_create(new_weeks, batch_size=50)
    weeks_by_index = {week.week_index: week for week in TrainingWeek.objects.filter(training_month=month_obj, week_index__in=[idx for idx, _ in week_starts])}
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
            if (idx, run_day) in existing_days:
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


def add_next_month_for_athlete(*, athlete) -> tuple[bool, int, int, int, int]:
    latest = TrainingMonth.objects.filter(athlete=athlete).order_by("-year", "-month").first()
    if latest is None:
        start = timezone.localdate().replace(day=1)
        target_year, target_month = start.year, start.month
    else:
        target_year, target_month = shift_month(latest.year, latest.month, 1)
    month_created, weeks_created, days_created = ensure_month_for_athlete(athlete=athlete, year=target_year, month=target_month)
    return month_created, weeks_created, days_created, target_year, target_month


def fill_gaps_and_add_next_month_for_athlete(*, athlete) -> tuple[int, int, int]:
    months = list(
        TrainingMonth.objects.filter(athlete=athlete)
        .order_by("year", "month")
        .values_list("year", "month")
    )
    if not months:
        month_created, weeks_created, days_created, _, _ = add_next_month_for_athlete(athlete=athlete)
        return (1 if month_created else 0), weeks_created, days_created

    created_months = 0
    created_weeks = 0
    created_days = 0
    start_year, start_month = months[0]
    end_year, end_month = months[-1]
    existing_months = {(int(year), int(month)) for year, month in months}

    current_year, current_month = start_year, start_month
    while (current_year, current_month) != (end_year, end_month):
        if (current_year, current_month) not in existing_months:
            month_created, weeks_created, days_created = ensure_month_for_athlete(
                athlete=athlete,
                year=current_year,
                month=current_month,
            )
            if month_created:
                created_months += 1
            created_weeks += weeks_created
            created_days += days_created
        current_year, current_month = shift_month(current_year, current_month, 1)

    month_created, weeks_created, days_created, _, _ = add_next_month_for_athlete(athlete=athlete)
    if month_created:
        created_months += 1
    created_weeks += weeks_created
    created_days += days_created
    return created_months, created_weeks, created_days


def is_coach(user) -> bool:
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == Role.COACH)


def display_name(user) -> str:
    if user.first_name or user.last_name:
        return f"{user.first_name} {user.last_name}".strip()
    return user.username
