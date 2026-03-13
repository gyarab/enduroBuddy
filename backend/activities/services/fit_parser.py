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
    intensity = str(it.get("intensity") or "").lower()
    if intensity in {"rest", "recovery"}:
        return False
    if intensity in {"active", "interval", "work"}:
        return True

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


def _avg_hr_from_samples(samples: list[dict[str, Any]]) -> Optional[int]:
    hrs = [int(s["hr"]) for s in samples if s.get("hr") is not None]
    if not hrs:
        return None
    return int(round(sum(hrs) / len(hrs)))


def _max_hr_from_samples(samples: list[dict[str, Any]]) -> Optional[int]:
    hrs = [int(s["hr"]) for s in samples if s.get("hr") is not None]
    return max(hrs) if hrs else None


def _message_to_row(msg) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for field in getattr(msg, "fields", []):
        if field.name:
            row[field.name] = field.value
    return row


def _extract_workout_steps(fit) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for msg in fit.get_messages("workout_step"):
        row = _message_to_row(msg)
        duration_type = str(row.get("duration_type") or "")
        if duration_type.startswith("repeat_until"):
            continue

        distance_m = row.get("duration_distance")
        if distance_m is not None:
            distance_m = int(round(float(distance_m)))

        time_s = row.get("duration_time")
        if time_s is not None:
            time_s = int(round(float(time_s)))

        if not distance_m and not time_s:
            continue

        steps.append(
            {
                "message_index": row.get("message_index"),
                "step_name": row.get("wkt_step_name") or row.get("notes") or "",
                "duration_type": duration_type,
                "distance_m": distance_m,
                "time_s": time_s,
                "intensity": str(row.get("intensity") or ""),
            }
        )
    return steps


def _step_note(step: dict[str, Any]) -> str:
    intensity = str(step.get("intensity") or "").lower()
    if intensity in {"rest", "recovery", "warmup", "cooldown"}:
        return "REST"
    return "WORK"


def _find_segment_end_index(
    samples: list[dict[str, Any]],
    start_index: int,
    *,
    target_distance_m: Optional[int] = None,
    target_time_s: Optional[int] = None,
) -> Optional[int]:
    start = samples[start_index]
    best_index: Optional[int] = None
    best_diff: Optional[float] = None

    for idx in range(start_index + 1, len(samples)):
        current = samples[idx]
        delta_t = int(current["t_s"]) - int(start["t_s"])
        if target_distance_m is not None and current.get("distance_m") is not None and start.get("distance_m") is not None:
            delta_d = int(current["distance_m"]) - int(start["distance_m"])
            diff = abs(delta_d - int(target_distance_m))
            if best_diff is None or diff < best_diff:
                best_index = idx
                best_diff = diff
            if delta_d >= int(target_distance_m):
                break
        elif target_time_s is not None:
            diff = abs(delta_t - int(target_time_s))
            if best_diff is None or diff < best_diff:
                best_index = idx
                best_diff = diff
            if delta_t >= int(target_time_s):
                break

    return best_index


def _interval_from_sample_slice(samples: list[dict[str, Any]], start_index: int, end_index: int, *, note: str) -> Optional[dict[str, Any]]:
    if end_index <= start_index:
        return None

    start = samples[start_index]
    end = samples[end_index]
    duration_s = int(end["t_s"]) - int(start["t_s"])
    if duration_s <= 0:
        return None

    distance_m = None
    if start.get("distance_m") is not None and end.get("distance_m") is not None:
        distance_m = int(end["distance_m"]) - int(start["distance_m"])

    avg_pace_s_per_km = None
    if distance_m and distance_m > 0:
        avg_pace_s_per_km = int(round(float(duration_s) / (float(distance_m) / 1000.0)))

    window = samples[start_index : end_index + 1]
    return {
        "duration_s": duration_s,
        "distance_m": distance_m,
        "avg_hr": _avg_hr_from_samples(window),
        "max_hr": _max_hr_from_samples(window),
        "avg_pace_s_per_km": avg_pace_s_per_km,
        "note": note,
    }


def _derive_intervals_from_workout_steps(samples: list[dict[str, Any]], steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(samples) < 2 or not steps:
        return []

    intervals: list[dict[str, Any]] = []
    cursor = 0

    for step in steps:
        end_index = _find_segment_end_index(
            samples,
            cursor,
            target_distance_m=step.get("distance_m"),
            target_time_s=step.get("time_s"),
        )
        if end_index is None:
            break

        interval = _interval_from_sample_slice(samples, cursor, end_index, note=_step_note(step))
        if interval is None:
            break

        intervals.append(interval)
        cursor = end_index
        if cursor >= len(samples) - 1:
            break

    return intervals if len(intervals) >= 2 else []


def _detect_workout_type(*, has_workout_steps: bool, laps: list[dict[str, Any]], is_auto_km_laps: bool) -> str:
    if has_workout_steps:
        return "WORKOUT"

    if not laps:
        return "RUN"

    if is_auto_km_laps:
        return "RUN"

    intensity_labels = [str(it.get("intensity") or "").lower() for it in laps]
    has_active_rest_pattern = any(label == "active" for label in intensity_labels) and any(label == "rest" for label in intensity_labels)
    manual_lap_count = sum(1 for it in laps if str(it.get("lap_trigger") or "").lower() == "manual")
    if has_active_rest_pattern and manual_lap_count >= 4:
        return "WORKOUT"

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
    workout_steps = _extract_workout_steps(fit)
    has_workout_steps = bool(workout_steps)

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
                "intensity": _val(lap, "intensity"),
                "lap_trigger": _val(lap, "lap_trigger"),
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

    derived_step_intervals = _derive_intervals_from_workout_steps(samples, workout_steps) if has_workout_steps else []
    if derived_step_intervals:
        laps = derived_step_intervals

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
