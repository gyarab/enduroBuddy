from __future__ import annotations

from dataclasses import replace
import re
from typing import Optional

from activities.services.fit_parser import FitParseResult


_OUTER_REPEAT_RE = re.compile(r"(?P<count>\d+(?:-\d+)?)\s*x\s*\((?P<body>[^()]*)\)", re.IGNORECASE)
_NESTED_REPEAT_RE = re.compile(
    r"(?P<outer>\d+(?:-\d+)?)\s*x\s*(?P<inner>\d+(?:-\d+)?)\s*x\s*(?P<segment>\d+(?:[.,]\d+)?\s*(?:km|m)?)",
    re.IGNORECASE,
)
_DISTANCE_TOKEN_RE = re.compile(r"(?P<value>\d+(?:[.,]\d+)?)(?P<unit>\s*(?:km|m))?$", re.IGNORECASE)
_PAUSE_RE = re.compile(r"\bp\s*=\s*(?P<values>[^,;]+)", re.IGNORECASE)
_POST_SERIES_RE = re.compile(r"po\s+s.{0,4}rii\s*(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>min|m(?:in)?|s|sec|sek|´|'|\?)", re.IGNORECASE)


def _upper_bound_int(raw: str) -> int:
    raw = (raw or "").strip()
    if "-" in raw:
        raw = raw.split("-")[-1]
    return int(float(raw.replace(",", ".")))


def _parse_distance_token(token: str, *, default_unit: Optional[str] = None) -> Optional[int]:
    m = _DISTANCE_TOKEN_RE.match((token or "").strip())
    if not m:
        return None
    value = float(m.group("value").replace(",", "."))
    unit = (m.group("unit") or "").strip().lower() or (default_unit or "")
    if unit == "km":
        return int(round(value * 1000))
    if unit == "m":
        return int(round(value))
    if value >= 100:
        return int(round(value))
    return int(round(value * 1000))


def _infer_default_unit(tokens: list[str]) -> str:
    lowered = [t.lower() for t in tokens]
    if any("km" in t for t in lowered):
        return "km"
    if any("m" in t for t in lowered):
        return "m"
    return "m"


def _parse_chain(chain: str) -> Optional[list[int]]:
    tokens = [part.strip() for part in re.split(r"\s*-\s*", chain or "") if part.strip()]
    if len(tokens) < 2:
        return None
    default_unit = _infer_default_unit(tokens)
    parsed = [_parse_distance_token(token, default_unit=default_unit) for token in tokens]
    if any(v is None for v in parsed):
        return None
    return [int(v) for v in parsed if v is not None]


def _parse_series_structure(title: str) -> Optional[list[list[int]]]:
    text = (title or "").replace("–", "-").replace("—", "-").replace("×", "x")
    text = re.sub(r"\b\d+(?:-\d+)?\s*[RV]\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()

    m = _OUTER_REPEAT_RE.search(text)
    if m:
        series_count = _upper_bound_int(m.group("count"))
        chain = _parse_chain(m.group("body"))
        if chain:
            return [list(chain) for _ in range(series_count)]

    m = _NESTED_REPEAT_RE.search(text)
    if m:
        outer = _upper_bound_int(m.group("outer"))
        inner = _upper_bound_int(m.group("inner"))
        segment = _parse_distance_token(m.group("segment"))
        if segment:
            return [[segment] * inner for _ in range(outer)]

    return None


def _parse_time_seconds(raw: str) -> Optional[int]:
    text = (raw or "").strip().lower()
    m = re.search(r"(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>min|m(?:in)?|s|sec|sek|´|'|\?)", text, re.IGNORECASE)
    if not m:
        return None
    value = float(m.group("value").replace(",", "."))
    unit = m.group("unit").lower()
    if unit in {"s", "sec", "sek"}:
        return int(round(value))
    return int(round(value * 60))


def _parse_rest_hints(title: str, series: list[list[int]]) -> tuple[Optional[int], Optional[int]]:
    text = title or ""
    rep_rest_s = None
    series_rest_s = None

    m = _PAUSE_RE.search(text)
    if m:
        values = [part.strip() for part in re.split(r"/", m.group("values")) if part.strip()]
        parsed = [_parse_time_seconds(v) for v in values]
        parsed = [v for v in parsed if v is not None]
        if parsed:
            rep_rest_s = parsed[0]
            if len(parsed) > 1:
                series_rest_s = parsed[1]

    m = _POST_SERIES_RE.search(text)
    if m:
        parsed = _parse_time_seconds(f"{m.group('value')} {m.group('unit')}")
        if parsed is not None:
            series_rest_s = parsed

    if len(series) == 1:
        series_rest_s = None

    return rep_rest_s, series_rest_s


def _find_index_for_distance(samples: list[dict], start_index: int, target_distance_m: int) -> Optional[int]:
    if start_index >= len(samples):
        return None
    start_distance = samples[start_index].get("distance_m")
    if start_distance is None:
        return None
    best = None
    best_diff = None
    for idx in range(start_index + 1, len(samples)):
        current_distance = samples[idx].get("distance_m")
        if current_distance is None:
            continue
        diff = abs((int(current_distance) - int(start_distance)) - int(target_distance_m))
        if best_diff is None or diff < best_diff:
            best = idx
            best_diff = diff
        if int(current_distance) - int(start_distance) >= int(target_distance_m):
            break
    return best


def _find_index_for_time(samples: list[dict], start_index: int, target_time_s: int) -> Optional[int]:
    if start_index >= len(samples):
        return None
    start_time = int(samples[start_index]["t_s"])
    best = None
    best_diff = None
    for idx in range(start_index + 1, len(samples)):
        diff = abs((int(samples[idx]["t_s"]) - start_time) - int(target_time_s))
        if best_diff is None or diff < best_diff:
            best = idx
            best_diff = diff
        if int(samples[idx]["t_s"]) - start_time >= int(target_time_s):
            break
    return best


def _build_interval(samples: list[dict], start_index: int, end_index: int, note: str) -> Optional[dict]:
    if end_index is None or end_index <= start_index:
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
    hrs = [int(s["hr"]) for s in samples[start_index : end_index + 1] if s.get("hr") is not None]
    return {
        "duration_s": duration_s,
        "distance_m": distance_m,
        "avg_hr": int(round(sum(hrs) / len(hrs))) if hrs else None,
        "max_hr": max(hrs) if hrs else None,
        "avg_pace_s_per_km": avg_pace_s_per_km,
        "note": note,
    }


def _all_equal_work_segments(series: list[list[int]]) -> bool:
    values = [seg for row in series for seg in row]
    return bool(values) and all(seg == values[0] for seg in values)


def _expected_rest_count(series: list[list[int]]) -> int:
    return sum(max(0, len(row) - 1) for row in series) + max(0, len(series) - 1)


def _has_structured_intervals(parsed_result: FitParseResult, *, series: list[list[int]]) -> bool:
    intervals = list(parsed_result.intervals or [])
    if not intervals:
        return False

    work_intervals = [it for it in intervals if (it.get("note") or "").upper() == "WORK"]
    rest_intervals = [it for it in intervals if (it.get("note") or "").upper() == "REST"]
    expected_work = sum(len(row) for row in series)
    expected_rest = _expected_rest_count(series)
    if len(work_intervals) != expected_work:
        return False
    if expected_rest > 0 and len(rest_intervals) < expected_rest:
        return False
    return True


def _reconstruct_equal_repeat_from_totals(
    *,
    series: list[list[int]],
    rep_rest_s: Optional[int],
    series_rest_s: Optional[int],
    parsed_result: FitParseResult,
) -> Optional[FitParseResult]:
    if not _all_equal_work_segments(series):
        return None

    summary = dict(parsed_result.summary or {})
    total_duration_s = int(summary.get("duration_s") or 0)
    total_distance_m = int(summary.get("distance_m") or 0)
    if total_duration_s <= 0:
        return None

    total_reps = sum(len(row) for row in series)
    total_short_rests = sum(max(0, len(row) - 1) for row in series)
    total_series_rests = max(0, len(series) - 1)
    estimated_rest_s = int(rep_rest_s or 0) * total_short_rests + int(series_rest_s or 0) * total_series_rests
    remaining_work_s = total_duration_s - estimated_rest_s
    if remaining_work_s <= 0 or total_reps <= 0:
        return None

    work_distance_m = sum(sum(row) for row in series)
    rest_distance_total = max(0, total_distance_m - work_distance_m)
    total_rest_count = total_short_rests + total_series_rests
    per_rest_distance = int(round(rest_distance_total / total_rest_count)) if total_rest_count > 0 else 0

    base_work = remaining_work_s // total_reps
    remainder = remaining_work_s % total_reps
    work_segment_m = series[0][0]

    intervals: list[dict] = []
    rep_index = 0
    for series_index, row in enumerate(series):
        for idx_in_row, _ in enumerate(row):
            duration_s = base_work + (1 if rep_index < remainder else 0)
            rep_index += 1
            intervals.append(
                {
                    "duration_s": duration_s,
                    "distance_m": work_segment_m,
                    "avg_hr": None,
                    "max_hr": None,
                    "avg_pace_s_per_km": int(round(float(duration_s) / (float(work_segment_m) / 1000.0))),
                    "note": "WORK",
                }
            )
            is_last_segment = idx_in_row == len(row) - 1
            is_last_series = series_index == len(series) - 1
            rest_seconds = None
            if not is_last_segment:
                rest_seconds = rep_rest_s
            elif not is_last_series:
                rest_seconds = series_rest_s
            if rest_seconds:
                intervals.append(
                    {
                        "duration_s": int(rest_seconds),
                        "distance_m": per_rest_distance if per_rest_distance > 0 else None,
                        "avg_hr": None,
                        "max_hr": None,
                        "avg_pace_s_per_km": None,
                        "note": "REST",
                    }
                )

    if len(intervals) < 3:
        return None

    summary["workout_type"] = "WORKOUT"
    summary["work_avg_hr"] = summary.get("work_avg_hr")
    return FitParseResult(summary=summary, intervals=intervals, samples=parsed_result.samples)


def reconstruct_intervals_from_plan(*, title: str, parsed_result: FitParseResult) -> FitParseResult:
    series = _parse_series_structure(title)
    if not series:
        return parsed_result

    if _has_structured_intervals(parsed_result, series=series):
        return parsed_result

    rep_rest_s, series_rest_s = _parse_rest_hints(title, series)
    if rep_rest_s is None and series_rest_s is None:
        return parsed_result

    if len(parsed_result.samples) < 2:
        fallback = _reconstruct_equal_repeat_from_totals(
            series=series,
            rep_rest_s=rep_rest_s,
            series_rest_s=series_rest_s,
            parsed_result=parsed_result,
        )
        return fallback or parsed_result

    samples = parsed_result.samples
    cursor = 0
    intervals: list[dict] = []
    fallback = lambda: _reconstruct_equal_repeat_from_totals(
        series=series,
        rep_rest_s=rep_rest_s,
        series_rest_s=series_rest_s,
        parsed_result=parsed_result,
    )

    for series_index, segments in enumerate(series):
        for segment_index, target_distance_m in enumerate(segments):
            end_index = _find_index_for_distance(samples, cursor, target_distance_m)
            interval = _build_interval(samples, cursor, end_index, "WORK")
            if interval is None:
                return fallback() or parsed_result
            intervals.append(interval)
            cursor = min(end_index + 1, len(samples) - 1)

            is_last_segment = segment_index == len(segments) - 1
            is_last_series = series_index == len(series) - 1
            rest_seconds = None
            if not is_last_segment:
                rest_seconds = rep_rest_s
            elif not is_last_series:
                rest_seconds = series_rest_s
            if rest_seconds:
                rest_end_index = _find_index_for_time(samples, cursor, rest_seconds)
                rest_interval = _build_interval(samples, cursor, rest_end_index, "REST")
                if rest_interval is None:
                    return fallback() or parsed_result
                intervals.append(rest_interval)
                cursor = min(rest_end_index + 1, len(samples) - 1)

    if len(intervals) < 3:
        return fallback() or parsed_result

    work_intervals = [it for it in intervals if it["note"] == "WORK"]
    if len(work_intervals) < sum(len(s) for s in series):
        return fallback() or parsed_result

    summary = dict(parsed_result.summary or {})
    summary["workout_type"] = "WORKOUT"
    work_hrs = [int(it["avg_hr"]) * int(it["duration_s"]) for it in work_intervals if it.get("avg_hr") is not None and it.get("duration_s")]
    work_den = sum(int(it["duration_s"]) for it in work_intervals if it.get("avg_hr") is not None and it.get("duration_s"))
    summary["work_avg_hr"] = int(round(sum(work_hrs) / work_den)) if work_den > 0 else summary.get("work_avg_hr")

    return FitParseResult(summary=summary, intervals=intervals, samples=parsed_result.samples)
