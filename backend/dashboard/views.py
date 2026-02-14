from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render
from django.utils import timezone

from activities.models import Activity, ActivityInterval
from training.models import TrainingMonth, TrainingWeek, PlannedTraining


MONTHS_CS = {
    1: "Leden",
    2: "Únor",
    3: "Březen",
    4: "Duben",
    5: "Květen",
    6: "Červen",
    7: "Červenec",
    8: "Srpen",
    9: "Září",
    10: "Říjen",
    11: "Listopad",
    12: "Prosinec",
}


def _fmt_month_label(year: int, month: int) -> str:
    return f"{MONTHS_CS.get(month, str(month))} {year}"


def _fmt_km(distance_m: int | None) -> str:
    if not distance_m:
        return "—"
    return f"{(float(distance_m) / 1000.0):.2f}"


def _fmt_minutes(duration_s: int | None) -> str:
    if not duration_s:
        return "—"
    mins = int(round(int(duration_s) / 60.0))
    return str(mins)


def _fmt_pace_mmss(pace_s_per_km: int | None) -> str:
    if not pace_s_per_km:
        return "—"
    pace_s_per_km = int(pace_s_per_km)
    m = pace_s_per_km // 60
    s = pace_s_per_km % 60
    return f"{m}:{s:02d}"


def _fmt_interval_time(duration_s: int | None) -> str | None:
    if not duration_s:
        return None
    ds = int(duration_s)
    if ds < 60:
        return str(ds)
    m = ds // 60
    s = ds % 60
    return f"{m}:{s:02d}"


def _is_pause_interval(it: ActivityInterval) -> bool:
    # jednoduchá heuristika pauzy (ladíme podle tvých dat)
    if not it.duration_s:
        return True
    if it.duration_s < 25:
        return True
    if not it.distance_m:
        return True
    if it.distance_m < 120:
        return True
    return False


def _work_intervals(activity: Activity) -> list[ActivityInterval]:
    intervals = list(activity.intervals.all())
    return [it for it in intervals if not _is_pause_interval(it)]


def _weighted_avg_hr(intervals: list[ActivityInterval]) -> int | None:
    num = 0.0
    den = 0.0
    for it in intervals:
        if it.avg_hr is None or it.duration_s is None:
            continue
        w = float(it.duration_s)
        num += float(it.avg_hr) * w
        den += w
    if den <= 0:
        return None
    return int(round(num / den))


def _max_hr_from_activity(activity: Activity) -> int | None:
    if getattr(activity, "max_hr", None):
        return activity.max_hr
    vals = [it.max_hr for it in activity.intervals.all() if getattr(it, "max_hr", None)]
    return max(vals) if vals else None


@dataclass
class MonthCard:
    id: int
    label: str
    weeks: list[TrainingWeek]


@login_required
def home(request):
    user = request.user

    months_qs = (
        TrainingMonth.objects.filter(athlete=user)
        .prefetch_related(
            Prefetch(
                "weeks",
                queryset=TrainingWeek.objects.all().prefetch_related(
                    Prefetch(
                        "planned_trainings",
                        queryset=PlannedTraining.objects.select_related("activity").prefetch_related(
                            Prefetch("activity__intervals", queryset=ActivityInterval.objects.all().order_by("index"))
                        ),
                    )
                ),
            )
        )
        .order_by("year", "month")
    )

    month_cards: list[MonthCard] = []
    for m in months_qs:
        label = _fmt_month_label(m.year, m.month)
        month_cards.append(MonthCard(id=m.id, label=label, weeks=list(m.weeks.all())))

    # Completed rows + totals per week
    for m in month_cards:
        for w in m.weeks:
            # totals (jen completed aktivity)
            total_dist_m = 0
            total_dur_s = 0
            hrs_for_avg: list[int] = []
            max_hr_week: int | None = None

            for t in w.planned_trainings.all():
                a: Activity | None = getattr(t, "activity", None)
                if not a:
                    t.completed_row = None
                    continue

                workout_type = a.workout_type or "UNKNOWN"
                km = _fmt_km(a.distance_m)
                minutes = _fmt_minutes(a.duration_s)

                if a.distance_m:
                    total_dist_m += int(a.distance_m)
                if a.duration_s:
                    total_dur_s += int(a.duration_s)

                if workout_type == "RUN":
                    third = _fmt_pace_mmss(a.avg_pace_s_per_km)
                    avg_hr = a.avg_hr
                else:
                    work_its = _work_intervals(a)
                    parts = []
                    for it in work_its:
                        s = _fmt_interval_time(it.duration_s)
                        if s:
                            parts.append(s)
                    third = f"({', '.join(parts)})" if parts else "—"
                    avg_hr = _weighted_avg_hr(work_its)

                if avg_hr is not None:
                    hrs_for_avg.append(int(avg_hr))

                mx = _max_hr_from_activity(a)
                if mx is not None:
                    max_hr_week = mx if max_hr_week is None else max(max_hr_week, mx)

                t.completed_row = {
                    "type": workout_type,  # RUN / WORKOUT / UNKNOWN
                    "km": km,              # string "8.01"
                    "min": minutes,        # string "49"
                    "third": third,        # pace nebo "(intervaly...)"
                    "avg_hr": avg_hr,
                    "max_hr": mx,
                }

            # totals row for the week
            w.completed_total = {
                "km": _fmt_km(total_dist_m) if total_dist_m else "—",
                "min": _fmt_minutes(total_dur_s) if total_dur_s else "—",
                "avg_hr": int(round(sum(hrs_for_avg) / len(hrs_for_avg))) if hrs_for_avg else None,
                "max_hr": max_hr_week,
            }

    return render(
        request,
        "dashboard/dashboard.html",
        {"month_cards": month_cards},
    )
