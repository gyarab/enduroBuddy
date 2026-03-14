from __future__ import annotations

from decimal import Decimal
import re
from typing import Any, Optional

from activities.models import Activity, ActivityInterval
from training.models import PlannedTraining

from .planned_interval_formatter import format_planned_interval_string
from .planned_km import estimate_running_km_details


CZ_MONTHS = {1: "Leden", 2: "Únor", 3: "Březen", 4: "Duben", 5: "Květen", 6: "Červen", 7: "Červenec", 8: "Srpen", 9: "Září", 10: "Říjen", 11: "Listopad", 12: "Prosinec"}
EN_MONTHS = {1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"}

_RUN_FINISHER_RE = re.compile(r"(?P<hint>\d+(?:\s*-\s*\d+)?\s*x\s*\d+(?:[.,]\d+)?\s*m\b[^|+]*)", re.IGNORECASE)


def fmt_mmss(seconds: Optional[int]) -> str:
    if seconds is None:
        return "-"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def work_intervals(intervals: list[ActivityInterval]) -> list[ActivityInterval]:
    return [it for it in intervals if (it.distance_m or 0) >= 200 and (it.duration_s or 0) >= 30]


def fmt_intervals(intervals: list[ActivityInterval]) -> str:
    work = work_intervals(intervals)
    if not work:
        return "-"
    out = []
    for it in work:
        d = it.duration_s or 0
        out.append(str(d) if d < 60 else fmt_mmss(d))
    return "(" + ", ".join(out) + ")"


def extract_run_finisher_hint(title: str) -> str:
    raw = (title or "").strip()
    if not raw:
        return ""
    for match in _RUN_FINISHER_RE.finditer(raw):
        hint = " ".join((match.group("hint") or "").split())
        lowered = hint.lower()
        if any(keyword in lowered for keyword in ("rovinky", "kopec", "kopce", "mch", "stride", "strides")):
            return hint
    return ""


def normalize_plan_text(text: str) -> str:
    return (text or "").strip().lower()


def plan_indicates_workout(*, title: str, notes: str) -> bool:
    text = f"{normalize_plan_text(title)} {normalize_plan_text(notes)}".strip()
    if not text:
        return False
    workout_keywords = ("workout", "tempo", "fartlek", "anp", "lt", "interv", "rovinky", "sbc", "mk", "mch", "p=", "zavod", "závod", "kopec", "kopce", "fini", "interval")
    if any(k in text for k in workout_keywords):
        return True
    pattern_hits = (
        re.search(r"\b\d+\s*x\s*\d+", text),
        re.search(r"\b\d+\s*x\s*\(", text),
        re.search(r"\b\d+\s*-\s*\d+\b", text),
        re.search(r"\btempo\s*\d", text),
    )
    return any(pattern_hits)


def activity_segment(a: Activity, *, show_intervals: bool, planned_title: str = "") -> str:
    intervals = list(a.intervals.all())
    intervals_text = format_planned_interval_string(planned_title, intervals)
    if intervals_text == "-":
        intervals_text = fmt_intervals(intervals)
    pace = fmt_mmss(a.avg_pace_s_per_km)
    pace_text = "-" if pace == "-" else f"{pace}/km"
    finisher_hint = extract_run_finisher_hint(planned_title)
    if not show_intervals:
        if pace_text != "-" and finisher_hint:
            return f"{pace_text} + {finisher_hint}"
        return pace_text
    if intervals_text != "-" and pace_text != "-":
        return f"{intervals_text}, {pace_text}"
    if intervals_text != "-":
        return intervals_text
    if pace_text != "-":
        return pace_text
    return "-"


def garmin_match_debug_text(a: Activity, *, planned_title: str = "", session_type: str = "") -> str:
    intervals = list(a.intervals.all())
    work_count = sum(1 for it in intervals if (it.note or "").upper() == "WORK")
    rest_count = sum(1 for it in intervals if (it.note or "").upper() == "REST")
    distance_km = f"{(int(a.distance_m or 0) / 1000.0):.2f}" if a.distance_m else "-"
    expected = "WORKOUT" if plan_indicates_workout(title=planned_title, notes="") or session_type == PlannedTraining.SessionType.WORKOUT else "RUN"
    return f"Garmin match: expected {expected}, got {(a.workout_type or '-')} | W {work_count} / R {rest_count} | {distance_km} km"


def planned_day_key(t: PlannedTraining):
    if t.date is None:
        return ("undated", t.id)
    return ("dated", t.date)


def extract_warning_fragment(title_text: str, warning_code: str) -> str:
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
        m = re.search(r"(p\s*=\s*\d+(?:[.,]\d+)?\s*['Â´’]|po\s*s[ée]rii\s*\d+(?:[.,]\d+)?\s*(?:min|m(?:in)?))", raw, re.IGNORECASE)
        return m.group(0) if m else ""
    if warning_code == "klus_minutes_estimate_used":
        m = re.search(r"(?:(?:po\s*s[ée]rii)\s*)?\d+(?:[.,]\d+)?\s*(?:min|m(?:in)?)\s*klus", raw, re.IGNORECASE)
        return m.group(0) if m else ""
    if warning_code == "long_run_by_feel_heuristic_used":
        m = re.search(r"(na pocit|by feel)", raw, re.IGNORECASE)
        return m.group(0) if m else ""
    return ""


def planned_km_hint_payload(*, title_text: str, language_code: str) -> dict[str, Any]:
    normalized_title = (title_text or "").strip()
    if not normalized_title:
        return {"planned_km_value": 0.0, "planned_km_confidence": "low", "planned_km_badge": "", "planned_km_text": "", "planned_km_warning": "", "planned_km_detail": "", "planned_km_line_km": "", "planned_km_line_reason": "", "planned_km_line_where": "", "planned_km_show": False}
    if normalized_title.lower() in {"volno", "rest", "rest day"}:
        return {"planned_km_value": 0.0, "planned_km_confidence": "high", "planned_km_badge": "OK", "planned_km_text": "≈ 0,0 km", "planned_km_warning": "", "planned_km_detail": "Volno: 0 km je v pořádku.", "planned_km_line_km": "≈ 0,0 km", "planned_km_line_reason": "V pořádku (volno).", "planned_km_line_where": "", "planned_km_show": True}
    details = estimate_running_km_details(title_text)
    km_str = str(details.total_km.quantize(Decimal("0.1")))
    if language_code.startswith("cs"):
        km_str = km_str.replace(".", ",")
    warning_map = {
        "run_hint_but_no_distance": "Nejasný zápis: chybí konkrétní vzdálenost (např. 8 km, 6x300m, 2R/2V).",
        "long_run_by_feel_heuristic_used": "Použit odhad pro běh na pocit.",
        "klus_minutes_estimate_used": "Do součtu je započítán odhad z času klusu (min klus).",
        "pause_minutes_estimate_used": "Do součtu je započítán odhad z pauz.",
        "dropped_large_km_token": "Část zápisu ignorována (podezřele vysoké km).",
        "dropped_invalid_m_token": "Část zápisu ignorována (neplatné metry).",
    }
    warning_text = warning_map.get(details.warnings[0], "") if details.warnings else ""
    line_km = f"≈ {km_str} km"
    line_reason = "V pořádku."
    line_where = ""
    detail_text = line_km
    if warning_text:
        fragment = extract_warning_fragment(normalized_title, details.warnings[0])
        if fragment:
            detail_text = f'{detail_text} - {warning_text} Problem je v: "{fragment}".'
            line_reason = warning_text
            line_where = fragment
        else:
            detail_text = f"{detail_text} - {warning_text}"
            line_reason = warning_text
    elif details.confidence != "high":
        detail_text = f"{detail_text} - Nejasný zápis, doplň konkrétní vzdálenosti (km/m, opakování, R/V)."
        line_reason = "Nejasný zápis, doplň konkrétní vzdálenosti."
    badge_map = {"high": "OK", "medium": "~", "low": "!"}
    return {
        "planned_km_value": float(details.total_km),
        "planned_km_confidence": details.confidence,
        "planned_km_badge": badge_map.get(details.confidence, "?"),
        "planned_km_text": f"≈ {km_str} km",
        "planned_km_warning": warning_text,
        "planned_km_detail": detail_text,
        "planned_km_line_km": line_km,
        "planned_km_line_reason": line_reason,
        "planned_km_line_where": line_where,
        "planned_km_show": True,
    }
