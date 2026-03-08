from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import re
from typing import Any, Optional

from django.db.models import Prefetch
from django.utils import timezone

from accounts.models import Role
from activities.models import Activity, ActivityInterval
from training.models import CompletedTraining, PlannedTraining, TrainingMonth, TrainingWeek
from .planned_km import estimate_running_km_details, estimate_running_km_from_title, format_week_km_label


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


def _normalize_plan_text(text: str) -> str:
    return (text or "").strip().lower()


def _plan_indicates_workout(*, title: str, notes: str) -> bool:
    text = f"{_normalize_plan_text(title)} {_normalize_plan_text(notes)}".strip()
    if not text:
        return False

    workout_keywords = (
        "workout",
        "tempo",
        "fartlek",
        "anp",
        "lt",
        "interv",
        "rovinky",
        "sbc",
        "mk",
        "mch",
        "p=",
        "zavod",
        "závod",
        "kopec",
        "kopce",
        "fini",
        "interval",
    )
    if any(k in text for k in workout_keywords):
        return True

    pattern_hits = (
        re.search(r"\b\d+\s*x\s*\d+", text),
        re.search(r"\b\d+\s*x\s*\(", text),
        re.search(r"\b\d+\s*-\s*\d+\b", text),
        re.search(r"\btempo\s*\d", text),
    )
    return any(pattern_hits)


def _activity_segment(a: Activity, *, show_intervals: bool) -> str:
    intervals = list(a.intervals.all())
    intervals_text = _fmt_intervals(intervals)
    pace = _fmt_mmss(a.avg_pace_s_per_km)
    pace_text = "-" if pace == "-" else f"{pace}/km"

    if not show_intervals:
        return pace_text

    if intervals_text != "-" and pace_text != "-":
        return f"{intervals_text}, {pace_text}"
    if intervals_text != "-":
        return intervals_text
    if pace_text != "-":
        return pace_text
    return "-"


def _planned_day_key(t: PlannedTraining):
    if t.date is None:
        return ("undated", t.id)
    return ("dated", t.date)


def _extract_warning_fragment(title_text: str, warning_code: str) -> str:
    raw = title_text or ""
    if warning_code == "run_hint_but_no_distance":
        m = re.search(r"\b(klus|beh|běh|run|fartlek|tempo|kopec|kopce|interval)\b", raw, re.IGNORECASE)
        return m.group(0) if m else raw[:24].strip()
    if warning_code == "dropped_large_km_token":
        for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*km\b", raw, re.IGNORECASE):
            try:
                if float(m.group(1).replace(",", ".")) > 60:
                    return m.group(0)
            except Exception:
                continue
    if warning_code == "dropped_invalid_m_token":
        for m in re.finditer(r"(\d{2,5})\s*m\b", raw, re.IGNORECASE):
            try:
                value = int(m.group(1))
                if value < 100 or value > 5000:
                    return m.group(0)
            except Exception:
                continue
    if warning_code == "pause_minutes_estimate_used":
        m = re.search(r"(p\s*=\s*\d+(?:[.,]\d+)?\s*['´’]|po\s*s[ée]rii\s*\d+(?:[.,]\d+)?\s*(?:min|m(?:in)?))", raw, re.IGNORECASE)
        return m.group(0) if m else ""
    if warning_code == "klus_minutes_estimate_used":
        m = re.search(r"(?:(?:po\s*s[ée]rii)\s*)?\d+(?:[.,]\d+)?\s*(?:min|m(?:in)?)\s*klus", raw, re.IGNORECASE)
        return m.group(0) if m else ""
    if warning_code == "long_run_by_feel_heuristic_used":
        m = re.search(r"(na pocit|by feel)", raw, re.IGNORECASE)
        return m.group(0) if m else ""
    return ""


def _planned_km_hint_payload(*, title_text: str, language_code: str) -> dict[str, Any]:
    normalized_title = (title_text or "").strip()
    if not normalized_title:
        return {
            "planned_km_value": 0.0,
            "planned_km_confidence": "low",
            "planned_km_badge": "",
            "planned_km_text": "",
            "planned_km_warning": "",
            "planned_km_detail": "",
            "planned_km_line_km": "",
            "planned_km_line_reason": "",
            "planned_km_line_where": "",
            "planned_km_show": False,
        }
    lowered = normalized_title.lower()
    is_rest = lowered in {"volno", "rest", "rest day"}
    if is_rest:
        detail_text = "Volno: 0 km je v pořádku." if language_code.startswith("cs") else "Volno: 0 km je v pořádku."
        return {
            "planned_km_value": 0.0,
            "planned_km_confidence": "high",
            "planned_km_badge": "OK",
            "planned_km_text": "\u2248 0,0 km" if language_code.startswith("cs") else "\u2248 0,0 km",
            "planned_km_warning": "",
            "planned_km_detail": detail_text,
            "planned_km_line_km": "\u2248 0,0 km" if language_code.startswith("cs") else "\u2248 0,0 km",
            "planned_km_line_reason": "V pořádku (volno)." if language_code.startswith("cs") else "V pořádku (volno).",
            "planned_km_line_where": "",
            "planned_km_show": True,
        }
    details = estimate_running_km_details(title_text)
    km_one_decimal = details.total_km.quantize(Decimal("0.1"))
    km_str = str(km_one_decimal)
    if language_code.startswith("cs"):
        km_str = km_str.replace(".", ",")
    warning_map_cs = {
        "run_hint_but_no_distance": "Nejasný zápis: chybí konkrétní vzdálenost (např. 8 km, 6x300m, 2R/2V).",
        "long_run_by_feel_heuristic_used": "Použit odhad pro běh na pocit.",
        "klus_minutes_estimate_used": "Do součtu je započítán odhad z času klusu (min klus).",
        "pause_minutes_estimate_used": "Do součtu je započítán odhad z pauz.",
        "dropped_large_km_token": "Část zápisu ignorována (podezřele vysoké km).",
        "dropped_invalid_m_token": "Část zápisu ignorována (neplatné metry).",
    }
    warning_map_en = {
        "run_hint_but_no_distance": "Nejasný zápis: chybí konkrétní vzdálenost (např. 8 km, 6x300m, 2R/2V).",
        "long_run_by_feel_heuristic_used": "Použit odhad pro běh na pocit.",
        "klus_minutes_estimate_used": "Do součtu je započítán odhad z času klusu (min klus).",
        "pause_minutes_estimate_used": "Do součtu je započítán odhad z pauz.",
        "dropped_large_km_token": "Část zápisu ignorována (podezřele vysoké km).",
        "dropped_invalid_m_token": "Část zápisu ignorována (neplatné metry).",
    }
    warning_map = warning_map_cs if language_code.startswith("cs") else warning_map_cs
    warning_text = warning_map.get(details.warnings[0], "") if details.warnings else ""
    line_km = f"\u2248 {km_str} km"
    line_reason = "V pořádku." if language_code.startswith("cs") else "V pořádku."
    line_where = ""
    detail_text = line_km
    if warning_text:
        fragment = _extract_warning_fragment(normalized_title, details.warnings[0])
        if fragment:
            if language_code.startswith("cs"):
                detail_text = f'{detail_text} - {warning_text} Problem je v: "{fragment}".'
            else:
                detail_text = f'{detail_text} - {warning_text} Problem je v: "{fragment}".'
            line_reason = warning_text
            line_where = fragment
        else:
            detail_text = f"{detail_text} - {warning_text}"
            line_reason = warning_text
    elif details.confidence != "high":
        if language_code.startswith("cs"):
            detail_text = f"{detail_text} - Nejasný zápis, doplň konkrétní vzdálenosti (km/m, opakování, R/V)."
            line_reason = "Nejasný zápis, doplň konkrétní vzdálenosti."
        else:
            detail_text = f"{detail_text} - Nejasný zápis, doplň konkrétní vzdálenosti (km/m, opakování, R/V)."
            line_reason = "Nejasný zápis, doplň konkrétní vzdálenosti."
    badge_map = {"high": "OK", "medium": "~", "low": "!"}
    return {
        "planned_km_value": float(details.total_km),
        "planned_km_confidence": details.confidence,
        "planned_km_badge": badge_map.get(details.confidence, "?"),
        "planned_km_text": f"\u2248 {km_str} km",
        "planned_km_warning": warning_text,
        "planned_km_detail": detail_text,
        "planned_km_line_km": line_km,
        "planned_km_line_reason": line_reason,
        "planned_km_line_where": line_where,
        "planned_km_show": True,
    }


def _build_planned_rows_for_week(planned_items: list[PlannedTraining], *, language_code: str) -> list[dict[str, Any]]:
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
                    "session_type": PlannedTraining.SessionType.RUN,
                    "notes": "",
                    "notes_raw": "",
                    "planned_km_value": 0.0,
                    "planned_km_confidence": "low",
                    "planned_km_badge": "",
                    "planned_km_text": "",
                    "planned_km_warning": "",
                    "planned_km_detail": "",
                    "planned_km_line_km": "",
                    "planned_km_line_reason": "",
                    "planned_km_line_where": "",
                    "planned_km_show": False,
                }
            first = subitems[0]
            titles = [x.title for x in subitems if x.title]
            notes = [x.notes for x in subitems if x.notes]
            joined_titles = " | ".join(titles) if titles else ""
            joined_notes = " | ".join(notes) if notes else ""
            effective_session_type = (
                PlannedTraining.SessionType.WORKOUT
                if any((x.session_type or PlannedTraining.SessionType.RUN) == PlannedTraining.SessionType.WORKOUT for x in subitems)
                else PlannedTraining.SessionType.RUN
            )
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
            }
            row.update(_planned_km_hint_payload(title_text=joined_titles, language_code=language_code))
            return row

        if is_two_phase:
            rows.append(planned_row_from(items[:1], show_date=True))
            rows.append(planned_row_from(items[1:], show_date=False))
        else:
            rows.append(planned_row_from(items, show_date=True))
    return rows


def _build_completed_row_from_activities(activities: list[Activity], *, show_intervals: bool) -> dict[str, Any]:
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

        seg = _activity_segment(a, show_intervals=show_intervals)
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

        def _show_intervals_for(subitems: list[PlannedTraining], sub_activities: list[Activity]) -> bool:
            if any((x.session_type or PlannedTraining.SessionType.RUN) == PlannedTraining.SessionType.WORKOUT for x in subitems):
                return True
            if subitems and all((x.session_type or PlannedTraining.SessionType.RUN) == PlannedTraining.SessionType.RUN for x in subitems):
                return False

            title = " ".join((x.title or "") for x in subitems)
            notes = " ".join((x.notes or "") for x in subitems)
            normalized = _normalize_plan_text(f"{title} {notes}")
            has_plan_text = bool(normalized)
            if _plan_indicates_workout(title=title, notes=notes):
                return True
            if has_plan_text:
                return False
            has_work_intervals = any(_fmt_intervals(list(a.intervals.all())) != "-" for a in sub_activities)
            if has_work_intervals:
                return True
            return any((a.workout_type or "") == "WORKOUT" for a in sub_activities)

        if is_two_phase:
            phase_1_items = items[:1]
            phase_2_items = items[1:]

            phase_1_activities = [x.activity for x in phase_1_items if getattr(x, "activity", None)]
            phase_2_activities = [x.activity for x in phase_2_items if getattr(x, "activity", None)]

            phase_1_row = _build_completed_row_from_activities(
                phase_1_activities,
                show_intervals=_show_intervals_for(phase_1_items, phase_1_activities),
            )
            phase_1_row["planned_id"] = phase_1_items[0].id if phase_1_items else None
            phase_1_row["item_count"] = len(phase_1_items)
            if len(phase_1_items) == 1:
                _apply_manual_overrides(phase_1_row, getattr(phase_1_items[0], "completed", None))
            rows.append(phase_1_row)

            phase_2_row = _build_completed_row_from_activities(
                phase_2_activities,
                show_intervals=_show_intervals_for(phase_2_items, phase_2_activities),
            )
            phase_2_row["planned_id"] = phase_2_items[0].id if phase_2_items else None
            phase_2_row["item_count"] = len(phase_2_items)
            if len(phase_2_items) == 1:
                _apply_manual_overrides(phase_2_row, getattr(phase_2_items[0], "completed", None))

            # Keep week totals based on per-phase raw values, but display
            # km/min in phase 2 as cumulative day total (phase 1 + phase 2).
            day_distance_m = int(phase_1_row.get("_distance_m") or 0) + int(phase_2_row.get("_distance_m") or 0)
            day_duration_min = int(phase_1_row.get("_duration_min") or 0) + int(phase_2_row.get("_duration_min") or 0)
            phase_2_row["km"] = f"{day_distance_m / 1000.0:.2f}" if day_distance_m > 0 else "-"
            phase_2_row["min"] = str(day_duration_min) if day_duration_min > 0 else "-"
            rows.append(phase_2_row)
        else:
            day_activities = [x.activity for x in items if getattr(x, "activity", None)]
            row = _build_completed_row_from_activities(
                day_activities,
                show_intervals=_show_intervals_for(items, day_activities),
            )
            row["planned_id"] = items[0].id if items else None
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


def _sum_planned_week_km(planned_items: list[PlannedTraining]) -> float:
    total = 0.0
    for planned in planned_items:
        extracted = estimate_running_km_from_title(planned.title)
        if extracted is not None:
            total += float(extracted)
    return total


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
        .order_by("-year", "-month")
    )

    month_dict = CZ_MONTHS if language_code.startswith("cs") else EN_MONTHS
    month_cards = []
    for m in months_qs:
        weeks_out = []
        for w in list(m.weeks.all()):
            planned_items = list(w.planned_trainings.all())
            w.planned_rows = _build_planned_rows_for_week(planned_items, language_code=language_code)
            w.planned_total_km_text = format_week_km_label(_sum_planned_week_km(planned_items), language_code)
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
