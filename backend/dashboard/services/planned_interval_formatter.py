from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional

from activities.models import ActivityInterval


def _fmt_mmss(seconds: Optional[int]) -> str:
    if seconds is None:
        return "-"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def _fmt_seconds(seconds: Optional[int]) -> str:
    if seconds is None:
        return "-"
    return str(int(seconds)) if int(seconds) < 60 else _fmt_mmss(seconds)


@dataclass(frozen=True)
class ParsedIntervalStructure:
    series: list[list[int]]


_WARMUP_COOLDOWN_RE = re.compile(r"\b\d+(?:-\d+)?\s*[RV]\b", re.IGNORECASE)
_OUTER_REPEAT_RE = re.compile(r"(?P<count>\d+(?:-\d+)?)\s*x\s*\((?P<body>[^()]*)\)", re.IGNORECASE)
_NESTED_REPEAT_RE = re.compile(
    r"(?P<outer>\d+(?:-\d+)?)\s*x\s*(?P<inner>\d+(?:-\d+)?)\s*x\s*(?P<segment>\d+(?:[.,]\d+)?\s*(?:km|m)?)",
    re.IGNORECASE,
)
_REPEAT_SIMPLE_RE = re.compile(r"(?P<count>\d+(?:-\d+)?)\s*x\s*(?P<segment>\d+(?:[.,]\d+)?\s*(?:km|m)?)", re.IGNORECASE)
_CHAIN_RE = re.compile(r"(?P<chain>(?:\d+(?:[.,]\d+)?\s*(?:km|m)?\s*-\s*)+\d+(?:[.,]\d+)?\s*(?:km|m)?)", re.IGNORECASE)
_DISTANCE_TOKEN_RE = re.compile(r"(?P<value>\d+(?:[.,]\d+)?)(?P<unit>\s*(?:km|m))?$", re.IGNORECASE)
_STEADY_DISTANCE_RE = re.compile(r"(?P<segment>\d+(?:[.,]\d+)?\s*km)\b", re.IGNORECASE)


def _upper_bound_int(raw: str) -> int:
    raw = (raw or "").strip()
    if "-" in raw:
        raw = raw.split("-")[-1]
    return int(float(raw.replace(",", ".")))


def _normalize_text(title: str) -> str:
    cleaned = (title or "").replace("–", "-").replace("—", "-")
    cleaned = cleaned.replace("×", "x")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = _WARMUP_COOLDOWN_RE.sub(" ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _infer_default_unit(tokens: list[str]) -> str:
    lowered = [t.lower() for t in tokens]
    if any("km" in t for t in lowered):
        return "km"
    if any("m" in t for t in lowered):
        return "m"
    numeric_values = []
    for token in lowered:
        m = _DISTANCE_TOKEN_RE.match(token.strip())
        if not m:
            continue
        try:
            numeric_values.append(float(m.group("value").replace(",", ".")))
        except Exception:
            continue
    if any(v >= 100 for v in numeric_values):
        return "m"
    return "km"


def _parse_distance_token(token: str, *, default_unit: Optional[str] = None) -> Optional[int]:
    m = _DISTANCE_TOKEN_RE.match((token or "").strip())
    if not m:
        return None
    try:
        value = float(m.group("value").replace(",", "."))
    except Exception:
        return None
    unit = (m.group("unit") or "").strip().lower() or (default_unit or "")
    if unit == "km":
        return int(round(value * 1000))
    if unit == "m":
        return int(round(value))
    if value >= 100:
        return int(round(value))
    return int(round(value * 1000))


def _parse_chain(chain: str) -> Optional[list[int]]:
    tokens = [part.strip() for part in re.split(r"\s*-\s*", chain or "") if part.strip()]
    if len(tokens) < 2:
        return None
    default_unit = _infer_default_unit(tokens)
    parsed = [_parse_distance_token(token, default_unit=default_unit) for token in tokens]
    if any(v is None for v in parsed):
        return None
    return [int(v) for v in parsed if v is not None]


def _split_top_level_plus(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")" and depth > 0:
            depth -= 1
        if ch == "+" and depth == 0:
            part = "".join(current).strip(" ,/")
            if part:
                parts.append(part)
            current = []
            continue
        current.append(ch)
    tail = "".join(current).strip(" ,/")
    if tail:
        parts.append(tail)
    return parts or [text]


def _parse_single_structure(text: str) -> Optional[ParsedIntervalStructure]:
    if not text:
        return None

    m = _OUTER_REPEAT_RE.search(text)
    if m:
        series_count = _upper_bound_int(m.group("count"))
        chain = _parse_chain(m.group("body"))
        if chain:
            return ParsedIntervalStructure(series=[list(chain) for _ in range(series_count)])

    m = _NESTED_REPEAT_RE.search(text)
    if m:
        outer = _upper_bound_int(m.group("outer"))
        inner = _upper_bound_int(m.group("inner"))
        segment = _parse_distance_token(m.group("segment"))
        if segment:
            return ParsedIntervalStructure(series=[[segment] * inner for _ in range(outer)])

    m = _REPEAT_SIMPLE_RE.search(text)
    if m:
        count = _upper_bound_int(m.group("count"))
        segment = _parse_distance_token(m.group("segment"))
        if segment:
            return ParsedIntervalStructure(series=[[segment] * count])

    m = _CHAIN_RE.search(text)
    if m:
        chain = _parse_chain(m.group("chain"))
        if chain:
            return ParsedIntervalStructure(series=[chain])

    lowered = text.lower()
    steady_hints = ("temp", "tempo", "anp", "lt", "prah", "závod", "zavod", "race", "fartlek")
    m = _STEADY_DISTANCE_RE.search(text)
    if m and any(hint in lowered for hint in steady_hints):
        segment = _parse_distance_token(m.group("segment"))
        if segment:
            return ParsedIntervalStructure(series=[[segment]])

    return None


def parse_planned_interval_structure(title: str) -> Optional[ParsedIntervalStructure]:
    text = _normalize_text(title)
    return _parse_single_structure(text)


def parse_planned_interval_blocks(title: str) -> list[ParsedIntervalStructure]:
    text = _normalize_text(title)
    if not text:
        return []

    blocks: list[ParsedIntervalStructure] = []
    for part in _split_top_level_plus(text):
        parsed = _parse_single_structure(part)
        if parsed is not None:
            blocks.append(parsed)

    if blocks:
        return blocks

    single = _parse_single_structure(text)
    return [single] if single is not None else []


def _fallback_work_intervals(intervals: list[ActivityInterval]) -> list[ActivityInterval]:
    return [it for it in intervals if (it.distance_m or 0) >= 200 and (it.duration_s or 0) >= 30]


def _planned_work_intervals(intervals: list[ActivityInterval]) -> list[ActivityInterval]:
    labeled = [it for it in intervals if (it.note or "").strip().upper() == "WORK"]
    if len(labeled) < 2:
        return _fallback_work_intervals(intervals)

    paced = [int(it.avg_pace_s_per_km) for it in labeled if it.avg_pace_s_per_km is not None]
    if not paced:
        return labeled

    fastest = min(paced)
    # Garmin sometimes mislabels slow recovery chunks as WORK; trim obvious outliers.
    threshold = fastest + 90
    filtered = [it for it in labeled if it.avg_pace_s_per_km is not None and int(it.avg_pace_s_per_km) <= threshold]
    return filtered if len(filtered) >= 2 else labeled


def _distance_tolerance_m(target_m: int) -> int:
    return max(80, min(250, int(round(target_m * 0.2))))


def _match_series(series: list[list[int]], work_intervals: list[ActivityInterval], *, start_index: int = 0) -> Optional[tuple[list[list[int]], int]]:
    out: list[list[int]] = []
    cursor = start_index

    for series_targets in series:
        formatted_series: list[int] = []
        for target in series_targets:
            if cursor >= len(work_intervals):
                return None

            best: Optional[tuple[int, int, int]] = None
            distance_sum = 0
            duration_sum = 0
            tolerance = _distance_tolerance_m(target)

            for idx in range(cursor, min(len(work_intervals), cursor + 3)):
                it = work_intervals[idx]
                if it.distance_m is None or it.duration_s is None:
                    return None
                distance_sum += int(it.distance_m)
                duration_sum += int(it.duration_s)

                diff = abs(distance_sum - target)
                if diff <= tolerance:
                    candidate = (idx + 1, duration_sum, diff)
                    if best is None or candidate[2] < best[2]:
                        best = candidate
                if distance_sum > target + tolerance:
                    break

            if best is None:
                return None

            cursor = best[0]
            formatted_series.append(best[1])

        out.append(formatted_series)

    return out, cursor


def format_planned_interval_string(title: str, intervals: list[ActivityInterval]) -> str:
    structures = parse_planned_interval_blocks(title)
    if not structures:
        return "-"

    work_intervals = _planned_work_intervals(intervals)
    if not work_intervals:
        return "-"

    cursor = 0
    rendered_blocks: list[str] = []
    for structure in structures:
        matched = _match_series(structure.series, work_intervals, start_index=cursor)
        if matched is None:
            if rendered_blocks:
                break
            return "-"
        block_series, cursor = matched

        chunks = []
        for series in block_series:
            chunks.append("(" + ", ".join(_fmt_seconds(seconds) for seconds in series) + ")")
        if chunks:
            rendered_blocks.append(" ".join(chunks))

    return " + ".join(rendered_blocks) if rendered_blocks else "-"
