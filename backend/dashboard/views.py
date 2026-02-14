from __future__ import annotations

from typing import Any, Optional

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render

from training.models import TrainingMonth
from activities.models import ActivityInterval


CZ_MONTHS = {
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


def _fmt_mmss(seconds: Optional[int]) -> str:
    if seconds is None:
        return "—"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def _fmt_minutes(duration_s: Optional[int]) -> str:
    if duration_s is None:
        return "—"
    mins = int(round(duration_s / 60.0))
    return str(mins)


def _fmt_km(distance_m: Optional[int]) -> str:
    if not distance_m:
        return "—"
    return f"{distance_m / 1000.0:.2f}"


def _work_intervals(intervals: list[ActivityInterval]) -> list[ActivityInterval]:
    # heuristika "work" vs "rest"
    return [
        it for it in intervals
        if (it.distance_m or 0) >= 200 and (it.duration_s or 0) >= 30
    ]


def _fmt_intervals(intervals: list[ActivityInterval]) -> str:
    work = _work_intervals(intervals)
    if not work:
        return "—"

    out = []
    for it in work:
        d = it.duration_s or 0
        if d < 60:
            out.append(str(d))
        else:
            out.append(_fmt_mmss(d))
    return "(" + ", ".join(out) + ")"


def _weighted_avg_hr(intervals: list[ActivityInterval]) -> Optional[int]:
    work = [it for it in _work_intervals(intervals) if it.avg_hr is not None]
    if not work:
        return None

    total_w = 0
    total = 0
    for it in work:
        w = int(it.duration_s or 0)
        if w <= 0:
            continue
        total_w += w
        total += int(it.avg_hr) * w

    if total_w <= 0:
        return None
    return int(round(total / total_w))


def _activity_to_completed_row(a) -> dict[str, Any]:
    intervals = list(a.intervals.all().order_by("index"))

    workout_type = a.workout_type or "RUN"
    km = _fmt_km(a.distance_m)
    minutes = _fmt_minutes(a.duration_s)
    max_hr = a.max_hr

    if workout_type == "WORKOUT":
        third = _fmt_intervals(intervals)
        avg_hr = _weighted_avg_hr(intervals)
    else:
        third = _fmt_mmss(a.avg_pace_s_per_km)
        avg_hr = a.avg_hr

    return {
        "workout_type": workout_type,
        "km": km,
        "min": minutes,
        "third": third,
        "avg_hr": avg_hr,
        "max_hr": max_hr,
    }


def _sum_week_total(rows: list[dict[str, Any]]) -> dict[str, Any]:
    km_sum = 0.0
    min_sum = 0
    hr_num = 0
    hr_den = 0
    max_hr = None

    for r in rows:
        # km
        try:
            km_sum += float(r["km"])
        except Exception:
            pass

        # minutes
        try:
            m = int(r["min"])
            min_sum += m
        except Exception:
            m = 0

        # avg hr weighted by minutes
        if r.get("avg_hr") is not None and m > 0:
            hr_num += int(r["avg_hr"]) * m
            hr_den += m

        # max hr
        if r.get("max_hr") is not None:
            max_hr = max(max_hr or 0, int(r["max_hr"]))

    avg_hr = int(round(hr_num / hr_den)) if hr_den > 0 else None

    return {
        "km": f"{km_sum:.2f}" if km_sum > 0 else "—",
        "time": str(min_sum) if min_sum > 0 else "—",
        "avg_hr": avg_hr,
        "max_hr": max_hr,
    }


@login_required
def home(request):
    # ✅ Prefetch čistě přes stringy (bez .rel.model hacků)
    months_qs = (
        TrainingMonth.objects
        .filter(athlete=request.user)
        .prefetch_related(
            Prefetch(
                "weeks",
                queryset=(
                    TrainingMonth._meta.get_field("weeks").related_model.objects
                    .all()
                    .prefetch_related(
                        Prefetch(
                            "planned_trainings",
                            queryset=(
                                TrainingMonth._meta.get_field("weeks").related_model._meta.get_field("planned_trainings").related_model.objects
                                .select_related("activity")
                                .prefetch_related(
                                    Prefetch(
                                        "activity__intervals",
                                        queryset=ActivityInterval.objects.order_by("index"),
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
        .order_by("year", "month")
    )

    month_cards = []
    for m in months_qs:
        weeks_out = []
        for w in list(m.weeks.all()):
            completed_rows_for_total = []

            for t in list(w.planned_trainings.all()):
                # ⚠️ neukládat do FK fieldů, jen runtime atribut
                t.completed_row = None
                if getattr(t, "activity", None):
                    t.completed_row = _activity_to_completed_row(t.activity)
                    completed_rows_for_total.append(t.completed_row)

            w.completed_total = _sum_week_total(completed_rows_for_total)
            weeks_out.append(w)

        month_cards.append(
            {
                "id": m.id,
                "label": f"{CZ_MONTHS.get(m.month, str(m.month))} {m.year}",
                "weeks": weeks_out,
            }
        )

    return render(request, "dashboard/dashboard.html", {"month_cards": month_cards})
