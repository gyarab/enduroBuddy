from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, BinaryIO, Optional, Union

from fitparse import FitFile

SourceType = Union[str, BinaryIO]


@dataclass
class FitParseResult:
    summary: dict[str, Any]
    intervals: list[dict[str, Any]]
    samples: list[dict[str, Any]]


def _val(msg, field: str):
    try:
        return msg.get_value(field)
    except Exception:
        return None


def _secs(v) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v.total_seconds())  # timedelta
    except Exception:
        try:
            return int(v)
        except Exception:
            return None


def _sport_to_model(sport) -> Optional[str]:
    if sport is None:
        return None
    s = str(sport).lower()
    if "run" in s:
        return "RUN"
    if "bike" in s or "cycling" in s:
        return "BIKE"
    if "swim" in s:
        return "SWIM"
    return "OTHER"


def _is_work_interval(it: dict[str, Any]) -> bool:
    dur = it.get("duration_s") or 0
    dist = it.get("distance_m") or 0
    pace = it.get("avg_pace_s_per_km")

    if dur <= 0:
        return False

    # pauzy bývají krátké / minimální distance
    if dist and dist < 200:
        return False

    # bez pace se bojíme rozhodnout → pauza
    if pace is None:
        return False

    # příliš pomalé = pauza (7:00/km)
    if pace > 420:
        return False

    return True


def _detect_workout_type(*, has_workout_steps: bool, laps: list[dict[str, Any]], is_auto_km_laps: bool) -> str:
    if has_workout_steps:
        return "WORKOUT"

    if not laps:
        return "RUN"

    if is_auto_km_laps:
        return "RUN"

    work_laps = [it for it in laps if _is_work_interval(it)]
    if len(work_laps) < 2:
        return "RUN"

    dists = [int(it["distance_m"]) for it in work_laps if it.get("distance_m") is not None]
    if len(dists) < 2:
        return "RUN"

    mn, mx = min(dists), max(dists)
    # workout expected when there is clear lap distance structure variability
    if mx - mn >= 250:
        return "WORKOUT"

    return "RUN"


def parse_fit_file(source: SourceType) -> FitParseResult:
    fit = FitFile(source)
    fit.parse()

    # --- session summary ---
    sport = None
    sub_sport = None
    started_at = None
    total_time_s = None
    total_dist_m = None
    avg_hr_session = None
    avg_speed = None  # m/s

    for msg in fit.get_messages("session"):
        sport = _val(msg, "sport")
        sub_sport = _val(msg, "sub_sport")
        started_at = _val(msg, "start_time")
        total_time_s = _secs(_val(msg, "total_timer_time"))
        total_dist_m = _val(msg, "total_distance")
        avg_hr_session = _val(msg, "avg_heart_rate")
        avg_speed = _val(msg, "avg_speed")
        break

    # --- structured workout steps ---
    has_workout_steps = False
    for _ in fit.get_messages("workout_step"):
        has_workout_steps = True
        break

    # --- laps -> intervals ---
    laps: list[dict[str, Any]] = []
    for lap in fit.get_messages("lap"):
        lap_time = _secs(_val(lap, "total_timer_time"))
        lap_dist = _val(lap, "total_distance")
        lap_avg_hr = _val(lap, "avg_heart_rate")
        lap_max_hr = _val(lap, "max_heart_rate")
        lap_avg_speed = _val(lap, "avg_speed")

        if lap_time is None and lap_dist is None:
            continue

        pace_s_per_km = None
        if lap_avg_speed and float(lap_avg_speed) > 0:
            pace_s_per_km = int(round(1000.0 / float(lap_avg_speed)))
        elif lap_time is not None and lap_dist and float(lap_dist) > 0:
            pace_s_per_km = int(round(float(lap_time) / (float(lap_dist) / 1000.0)))

        laps.append(
            {
                "duration_s": lap_time,
                "distance_m": int(lap_dist) if lap_dist is not None else None,
                "avg_hr": int(lap_avg_hr) if lap_avg_hr is not None else None,
                "max_hr": int(lap_max_hr) if lap_max_hr is not None else None,
                "avg_pace_s_per_km": pace_s_per_km,
                "note": "",
            }
        )

    # --- samples from records (bez GPS) ---
    samples: list[dict[str, Any]] = []
    start_ts: Optional[datetime] = None

    for rec in fit.get_messages("record"):
        ts = _val(rec, "timestamp")
        if not ts:
            continue
        if start_ts is None:
            start_ts = ts

        t_s = int((ts - start_ts).total_seconds())

        dist = _val(rec, "distance")
        hr = _val(rec, "heart_rate")

        speed = _val(rec, "enhanced_speed") or _val(rec, "speed")
        alt = _val(rec, "enhanced_altitude") or _val(rec, "altitude")

        cadence = _val(rec, "cadence")
        power = _val(rec, "power")

        samples.append(
            {
                "t_s": t_s,
                "distance_m": int(dist) if dist is not None else None,
                "hr": int(hr) if hr is not None else None,
                "speed_m_s": float(speed) if speed is not None else None,
                "cadence": int(cadence) if cadence is not None else None,
                "power": int(power) if power is not None else None,
                "altitude_m": float(alt) if alt is not None else None,
            }
        )

    # --- max_hr from samples ---
    max_hr = None
    hrs = [s["hr"] for s in samples if s.get("hr") is not None]
    if hrs:
        max_hr = max(hrs)

    # --- auto-km-laps (easy run) ---
    is_auto_km_laps = False
    if len(laps) >= 6:
        dists = [x.get("distance_m") for x in laps if x.get("distance_m")]
        if dists:
            near_1k = sum(1 for d in dists if 950 <= int(d) <= 1050)
            if near_1k / max(len(dists), 1) >= 0.8:
                is_auto_km_laps = True

    workout_type = _detect_workout_type(
        has_workout_steps=has_workout_steps,
        laps=laps,
        is_auto_km_laps=is_auto_km_laps,
    )

    # --- label WORK/REST + work_avg_hr ---
    work_avg_hr = None
    if workout_type == "WORKOUT" and laps:
        num = 0
        den = 0
        for it in laps:
            is_work = _is_work_interval(it)
            it["note"] = "WORK" if is_work else "REST"

            hr = it.get("avg_hr")
            dur = it.get("duration_s") or 0
            if is_work and hr is not None and dur > 0:
                num += int(hr) * int(dur)
                den += int(dur)

        if den > 0:
            work_avg_hr = int(round(num / den))
    else:
        for it in laps:
            it["note"] = ""

    # --- pace summary ---
    avg_pace_s_per_km = None
    if avg_speed and float(avg_speed) > 0:
        avg_pace_s_per_km = int(round(1000.0 / float(avg_speed)))
    elif total_time_s is not None and total_dist_m and float(total_dist_m) > 0:
        avg_pace_s_per_km = int(round(float(total_time_s) / (float(total_dist_m) / 1000.0)))

    summary = {
        "started_at": started_at if isinstance(started_at, datetime) else None,
        "title": None,
        "sport": _sport_to_model(sport),
        "workout_type": workout_type,
        "duration_s": int(total_time_s) if total_time_s is not None else None,
        "distance_m": int(total_dist_m) if total_dist_m is not None else None,
        "avg_hr": int(avg_hr_session) if avg_hr_session is not None else None,
        "work_avg_hr": work_avg_hr,
        "max_hr": int(max_hr) if max_hr is not None else None,
        "avg_pace_s_per_km": avg_pace_s_per_km,
        "sub_sport": str(sub_sport) if sub_sport is not None else None,
    }

    return FitParseResult(summary=summary, intervals=laps, samples=samples)
