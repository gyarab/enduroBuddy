from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fitparse import FitFile


@dataclass
class FitParseResult:
    summary: dict[str, Any]
    intervals: list[dict[str, Any]]


def _val(msg, field: str):
    try:
        return msg.get_value(field)
    except Exception:
        return None


def _secs(v):
    if v is None:
        return None
    try:
        # timedelta
        return int(v.total_seconds())
    except Exception:
        try:
            return int(v)
        except Exception:
            return None


def _pace_s_per_km(time_s: int | None, dist_m: int | None, avg_speed_mps: float | None):
    # pace v sekundách na km
    if avg_speed_mps and float(avg_speed_mps) > 0:
        return int(round(1000.0 / float(avg_speed_mps)))
    if time_s is not None and dist_m and float(dist_m) > 0:
        return int(round(float(time_s) / (float(dist_m) / 1000.0)))
    return None


def _detect_workout_type(laps: list[dict[str, Any]], has_workout_steps: bool) -> str:
    """
    Heuristika:
    - workout_step => WORKOUT
    - jinak posuzuj laps (už očištěné od mikro-lapů)
    """
    if has_workout_steps:
        return "WORKOUT"

    if len(laps) < 2:
        return "RUN"

    # vezmi distance/pace
    dists = [it.get("distance_m") for it in laps if it.get("distance_m") is not None]
    paces = [it.get("avg_pace_s_per_km") for it in laps if it.get("avg_pace_s_per_km") is not None]

    if not dists:
        return "RUN"

    # pokud jsou lapy převážně ~1 km (autolap), typicky to je RUN
    one_k = sum(1 for d in dists if 900 <= d <= 1100)
    is_mostly_1k = one_k >= int(0.6 * len(dists))

    # variabilita pace: velké rozdíly => intervaly
    if paces:
        avg_p = sum(paces) / len(paces)
        max_dev = max(abs(p - avg_p) for p in paces)
        high_variability = (avg_p > 0) and ((max_dev / avg_p) >= 0.15)  # 15%
    else:
        high_variability = False

    # mix distancí (1km + 500m + 300m...) často workout
    rounded = [int(round(d / 50.0) * 50) for d in dists]  # zaokrouhli na 50m
    distinct_dist = len(set(rounded))
    has_mixed_distances = distinct_dist >= 3  # benevolentnější

    # rozhodnutí
    if is_mostly_1k and not high_variability and not has_mixed_distances:
        return "RUN"

    # workout, pokud se pace výrazně mění nebo jsou různé délky úseků
    if high_variability or has_mixed_distances:
        return "WORKOUT"

    # fallback: pokud je hodně lapů, ale bez jasných znaků intervalů, ber jako RUN
    return "RUN"


def parse_fit_file(path: str) -> FitParseResult:
    fit = FitFile(path)
    fit.parse()

    # --- session summary ---
    sport = None
    started_at = None
    total_time_s = None
    total_dist_m = None
    avg_hr = None
    avg_speed = None  # m/s

    for msg in fit.get_messages("session"):
        sport = _val(msg, "sport")
        started_at = _val(msg, "start_time")
        total_time_s = _secs(_val(msg, "total_timer_time"))
        total_dist_m = _val(msg, "total_distance")
        avg_hr = _val(msg, "avg_heart_rate")
        avg_speed = _val(msg, "avg_speed")
        break

    # --- structured workouts ---
    has_workout_steps = False
    for _ in fit.get_messages("workout_step"):
        has_workout_steps = True
        break

    # --- laps (intervals) ---
    raw_laps: list[dict[str, Any]] = []
    for lap in fit.get_messages("lap"):
        lap_time = _secs(_val(lap, "total_timer_time"))
        lap_dist = _val(lap, "total_distance")
        lap_avg_hr = _val(lap, "avg_heart_rate")
        lap_avg_speed = _val(lap, "avg_speed")

        if lap_time is None and lap_dist is None:
            continue

        dist_m = int(lap_dist) if lap_dist is not None else None
        pace = _pace_s_per_km(lap_time, dist_m, lap_avg_speed)

        raw_laps.append(
            {
                "duration_s": lap_time,
                "distance_m": dist_m,
                "avg_hr": int(lap_avg_hr) if lap_avg_hr is not None else None,
                "avg_pace_s_per_km": pace,
                "note": "",
            }
        )

    # ODFILTROVÁNÍ “mikro-lapů” (typicky poslední 1s / pár metrů)
    # - workouty (500m, 1km) zůstanou
    # - bordel lapy zmizí
    laps: list[dict[str, Any]] = []
    for it in raw_laps:
        d = it.get("distance_m")
        t = it.get("duration_s")

        # když nevíme distance, necháme (může to být relevantní lap)
        if d is None:
            laps.append(it)
            continue

        if d < 200:
            continue
        if t is not None and t < 30:
            continue

        laps.append(it)

    # fallback: když laps nejsou (nebo jsme je moc ořezali), zkus 1km splits z recordů
    intervals = laps
    if not intervals:
        records = []
        for rec in fit.get_messages("record"):
            t = _val(rec, "timestamp")
            d = _val(rec, "distance")  # m kumulativně
            hr = _val(rec, "heart_rate")
            if t is None or d is None:
                continue
            records.append((t, float(d), int(hr) if hr is not None else None))

        if records:
            km = 1
            start_i = 0
            while True:
                target = km * 1000.0
                end_i = None
                for i in range(start_i, len(records)):
                    if records[i][1] >= target:
                        end_i = i
                        break
                if end_i is None:
                    break

                t0, d0, _ = records[start_i]
                t1, d1, _ = records[end_i]
                dur = _secs(t1 - t0) if hasattr(t1, "__sub__") else None
                dist = d1 - d0
                if dist <= 0:
                    start_i = end_i
                    km += 1
                    continue

                pace = int(round(dur / (dist / 1000.0))) if dur is not None else None
                hrs = [h for (_, _, h) in records[start_i:end_i + 1] if h is not None]
                ahr = int(round(sum(hrs) / len(hrs))) if hrs else None

                intervals.append(
                    {
                        "duration_s": dur,
                        "distance_m": int(round(dist)),
                        "avg_hr": ahr,
                        "avg_pace_s_per_km": pace,
                        "note": f"{km} km",
                    }
                )

                start_i = end_i
                km += 1

    workout_type = _detect_workout_type(intervals, has_workout_steps)

    avg_pace_s_per_km = _pace_s_per_km(
        total_time_s,
        int(total_dist_m) if total_dist_m is not None else None,
        avg_speed,
    )

    summary = {
        "started_at": started_at if isinstance(started_at, datetime) else None,
        "title": None,
        "sport": str(sport) if sport is not None else None,
        "workout_type": workout_type,  # "RUN" | "WORKOUT"
        "duration_s": int(total_time_s) if total_time_s is not None else None,
        "distance_m": int(total_dist_m) if total_dist_m is not None else None,
        "avg_hr": int(avg_hr) if avg_hr is not None else None,
        "avg_pace_s_per_km": avg_pace_s_per_km,
    }

    return FitParseResult(summary=summary, intervals=intervals)
