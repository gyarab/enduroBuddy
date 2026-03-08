from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import re
import unicodedata


_NUM = r"\d+(?:[.,]\d+)?"
_MUL = r"[xX]"

_MULT_RANGE_PAREN_RE = re.compile(rf"(?P<m1>{_NUM})\s*-\s*(?P<m2>{_NUM})\s*{_MUL}\s*\((?P<body>[^)]*)\)", re.IGNORECASE)
_MULT_PAREN_WITH_TAIL_SERIES_RE = re.compile(
    rf"(?P<m>{_NUM})\s*{_MUL}\s*\((?P<body>[^)]*)\)\s*(?:mk|mch)?\s*(?P<tail>\d{{3,4}}(?:\s*-\s*\d{{3,4}})+)m\b",
    re.IGNORECASE,
)
_MULT_SINGLE_PAREN_RE = re.compile(rf"(?P<m>{_NUM})\s*{_MUL}\s*\((?P<body>[^)]*)\)", re.IGNORECASE)
_MULT_CHAIN_DIST_RANGE_RE = re.compile(
    rf"(?P<a1>{_NUM})\s*-\s*(?P<a2>{_NUM})\s*{_MUL}\s*(?P<b>{_NUM})\s*{_MUL}\s*(?P<d>{_NUM})\s*(?P<u>km|m)\b",
    re.IGNORECASE,
)
_MULT_CHAIN_DIST_SINGLE_RE = re.compile(
    rf"(?P<a>{_NUM})\s*{_MUL}\s*(?P<b>{_NUM})\s*{_MUL}\s*(?P<d>{_NUM})\s*(?P<u>km|m)\b",
    re.IGNORECASE,
)
_MULT_DIST_RANGE_RE = re.compile(rf"(?P<m1>{_NUM})\s*-\s*(?P<m2>{_NUM})\s*{_MUL}\s*(?P<d>{_NUM})\s*(?P<u>km|m)\b", re.IGNORECASE)
_MULT_DIST_SINGLE_RE = re.compile(rf"(?P<m>{_NUM})\s*{_MUL}\s*(?P<d>{_NUM})\s*(?P<u>km|m)\b", re.IGNORECASE)
_RV_RANGE_KM_RE = re.compile(rf"(?<!\w)(?P<a>{_NUM})\s*-\s*(?P<b>{_NUM})\s*(?P<t>[RV])(?=$|[\s,;+()/-])", re.IGNORECASE)
_RV_KM_RE = re.compile(rf"(?<!\w)(?P<v>{_NUM})\s*(?P<t>[RV])(?=$|[\s,;+()/-])", re.IGNORECASE)
_RANGE_UNIT_RE = re.compile(rf"(?P<a>{_NUM})\s*-\s*(?P<b>{_NUM})\s*(?P<u>km|m)\b", re.IGNORECASE)
_SINGLE_UNIT_RE = re.compile(rf"(?P<v>{_NUM})\s*(?P<u>km|m)\b", re.IGNORECASE)
_BARE_M_SERIES_RE = re.compile(r"\b(?P<body>\d{3,4}(?:\s*-\s*\d{3,4}){1,})\b")
_BARE_M_TOKEN_RE = re.compile(r"(?<!\d)(?P<v>\d{3,4})(?!\d)")
_PAUSE_MIN_RE = re.compile(r"\bp\s*=\s*(?P<min>\d+(?:[.,]\d+)?)\s*[''´’]", re.IGNORECASE)
_KLUS_MIN_RE = re.compile(r"(?:(?P<after>po\s*serii)\s*)?(?P<min>\d+(?:[.,]\d+)?)\s*(?:min|m(?:in)?)\s*klus", re.IGNORECASE)

_RUN_HINT_RE = re.compile(r"\b(km|m|klus|fartlek|tempo|kopec|beh|run|interval|rovinky)\b", re.IGNORECASE)

_WALK_KEYWORDS = ("chuze", "mch", "walk", "walking", "hike")
_LONG_RUN_HINTS = ("delsi klus", "dlouhy klus", "long run")
_BY_FEEL_HINTS = ("na pocit", "by feel")

_MAX_KM_TOKEN = Decimal("60")
_MIN_M_TOKEN = Decimal("100")
_MAX_M_TOKEN = Decimal("5000")
_MAX_RV_TOKEN = Decimal("30")


@dataclass
class PlannedKmEstimate:
    total_km: Decimal
    confidence: str
    warnings: list[str]


@dataclass
class _ParseContext:
    warnings: set[str]

    def warn(self, code: str) -> None:
        self.warnings.add(code)


def _to_decimal(raw: str | None) -> Decimal | None:
    if raw is None:
        return None
    try:
        return Decimal(str(raw).replace(",", "."))
    except Exception:
        return None


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _is_walk_context(text: str, start: int, end: int) -> bool:
    # Treat as walking only when the walk marker is directly tied to this distance token.
    # Example walk distance: "200m MCH" or "MCH 200m"
    # Example not-walk (running distance with walk recovery): "6x100m s MCH"
    normalized = _strip_accents(text).lower()
    left = max(0, start - 24)
    right = min(len(normalized), end + 24)
    around = normalized[left:right]
    rel_start = start - left
    rel_end = end - left
    before = around[:rel_start]
    after = around[rel_end:]

    marker_pattern = r"(?:mch|chuze|walk|walking|hike)"
    if re.search(rf"\b{marker_pattern}\s*$", before):
        return True
    if re.search(rf"^\s*{marker_pattern}\b", after):
        return True
    return False


def _is_tempo_context(text: str, start: int) -> bool:
    normalized = _strip_accents(text).lower()
    left = max(0, start - 20)
    before = normalized[left:start]
    return re.search(r"(?:tempo|tempu)\s*$", before) is not None


def _to_km(value: Decimal, unit: str, ctx: _ParseContext) -> Decimal:
    if unit.lower() == "km":
        if value > _MAX_KM_TOKEN:
            ctx.warn("dropped_large_km_token")
            return Decimal("0")
        return value
    if value < _MIN_M_TOKEN or value > _MAX_M_TOKEN:
        ctx.warn("dropped_invalid_m_token")
        return Decimal("0")
    return value / Decimal("1000")


def _tail_series_km(raw: str, ctx: _ParseContext) -> Decimal:
    values = []
    for part in re.split(r"\s*-\s*", raw):
        parsed = _to_decimal(part)
        if parsed is None:
            return Decimal("0")
        values.append(parsed)
    if not values:
        return Decimal("0")
    if any(v < _MIN_M_TOKEN or v > _MAX_M_TOKEN for v in values):
        ctx.warn("dropped_invalid_m_token")
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal("1000")


def _bare_m_tokens_km(raw: str, ctx: _ParseContext) -> Decimal:
    total = Decimal("0")
    for match in _BARE_M_TOKEN_RE.finditer(raw):
        value = _to_decimal(match.group("v"))
        if value is None:
            continue
        if value < _MIN_M_TOKEN or value > _MAX_M_TOKEN:
            continue
        total += value / Decimal("1000")
    return total


def _estimate_pause_minutes_km(raw_text: str, ctx: _ParseContext) -> Decimal:
    # Static pauses like "P=90s" or "P=1,5'" do not add running distance.
    return Decimal("0")


def _outer_series_multiplier(raw_text: str) -> Decimal:
    match = re.search(r"\b(?P<n>\d+(?:[.,]\d+)?)\s*[xX]\s*\d", raw_text)
    if not match:
        return Decimal("1")
    value = _to_decimal(match.group("n"))
    if value is None or value <= 0 or value > 10:
        return Decimal("1")
    return value


def _estimate_klus_minutes_km(raw_text: str, ctx: _ParseContext) -> Decimal:
    total = Decimal("0")
    normalized = _strip_accents(raw_text).lower()
    series_mult = _outer_series_multiplier(normalized)
    for match in _KLUS_MIN_RE.finditer(normalized):
        mins = _to_decimal(match.group("min"))
        if mins is None or mins <= 0:
            continue
        mult = series_mult if match.group("after") else Decimal("1")
        total += mins * Decimal("0.25") * mult
    if total > 0:
        ctx.warn("klus_minutes_estimate_used")
    return total


def _consume_pattern(
    mutable: str,
    pattern: re.Pattern,
    handler,
) -> tuple[Decimal, str]:
    total = Decimal("0")
    pieces: list[str] = []
    last_end = 0
    for match in pattern.finditer(mutable):
        total += handler(match, mutable)
        pieces.append(mutable[last_end:match.start()])
        pieces.append(" " * (match.end() - match.start()))
        last_end = match.end()
    pieces.append(mutable[last_end:])
    return total, "".join(pieces)


def _estimate_segment_km(text: str, ctx: _ParseContext) -> Decimal:
    if not text:
        return Decimal("0")

    total = Decimal("0")
    mutable = text

    def add(pattern: re.Pattern, handler) -> None:
        nonlocal total, mutable
        inc, next_mutable = _consume_pattern(mutable, pattern, handler)
        total += inc
        mutable = next_mutable

    # Phase 1: parenthesized intervals and nested structures
    def handle_mult_range_paren(match: re.Match, src: str) -> Decimal:
        m1 = _to_decimal(match.group("m1"))
        m2 = _to_decimal(match.group("m2"))
        if m1 is None or m2 is None or m1 < 0 or m2 < 0:
            return Decimal("0")
        mult = max(m1, m2)
        body = match.group("body")
        body_km = _estimate_segment_km(body, ctx)
        if body_km == 0:
            body_km = _bare_m_tokens_km(body, ctx)
        return mult * body_km

    def handle_mult_paren_with_tail(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        m = _to_decimal(match.group("m"))
        if m is None or m < 0:
            return Decimal("0")
        body_km = _estimate_segment_km(match.group("body"), ctx)
        tail_km = _tail_series_km(match.group("tail"), ctx)
        return m * (body_km + tail_km)

    def handle_mult_single_paren(match: re.Match, src: str) -> Decimal:
        m = _to_decimal(match.group("m"))
        if m is None or m < 0:
            return Decimal("0")
        body = match.group("body")
        body_km = _estimate_segment_km(body, ctx)
        if body_km == 0:
            body_km = _bare_m_tokens_km(body, ctx)
        return m * body_km

    add(_MULT_RANGE_PAREN_RE, handle_mult_range_paren)
    add(_MULT_PAREN_WITH_TAIL_SERIES_RE, handle_mult_paren_with_tail)
    add(_MULT_SINGLE_PAREN_RE, handle_mult_single_paren)

    # Phase 2: multiplicative distance expressions
    def handle_mult_chain_range(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        a1 = _to_decimal(match.group("a1"))
        a2 = _to_decimal(match.group("a2"))
        b = _to_decimal(match.group("b"))
        d = _to_decimal(match.group("d"))
        if None in {a1, a2, b, d}:
            return Decimal("0")
        if a1 < 0 or a2 < 0 or b < 0 or d < 0:
            return Decimal("0")
        return max(a1, a2) * b * _to_km(d, match.group("u"), ctx)

    def handle_mult_chain_single(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        a = _to_decimal(match.group("a"))
        b = _to_decimal(match.group("b"))
        d = _to_decimal(match.group("d"))
        if None in {a, b, d}:
            return Decimal("0")
        if a < 0 or b < 0 or d < 0:
            return Decimal("0")
        return a * b * _to_km(d, match.group("u"), ctx)

    def handle_mult_dist_range(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        m1 = _to_decimal(match.group("m1"))
        m2 = _to_decimal(match.group("m2"))
        d = _to_decimal(match.group("d"))
        if m1 is None or m2 is None or d is None or m1 < 0 or m2 < 0 or d < 0:
            return Decimal("0")
        return max(m1, m2) * _to_km(d, match.group("u"), ctx)

    def handle_mult_dist_single(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        m = _to_decimal(match.group("m"))
        d = _to_decimal(match.group("d"))
        if m is None or d is None or m < 0 or d < 0:
            return Decimal("0")
        return m * _to_km(d, match.group("u"), ctx)

    add(_MULT_CHAIN_DIST_RANGE_RE, handle_mult_chain_range)
    add(_MULT_CHAIN_DIST_SINGLE_RE, handle_mult_chain_single)
    add(_MULT_DIST_RANGE_RE, handle_mult_dist_range)
    add(_MULT_DIST_SINGLE_RE, handle_mult_dist_single)

    # Phase 3: generic distance tokens
    def handle_rv_range(match: re.Match, src: str) -> Decimal:
        a = _to_decimal(match.group("a"))
        b = _to_decimal(match.group("b"))
        if a is None or b is None or a < 0 or b < 0:
            return Decimal("0")
        if a > _MAX_RV_TOKEN or b > _MAX_RV_TOKEN:
            return Decimal("0")
        return max(a, b)

    def handle_rv(match: re.Match, src: str) -> Decimal:
        value = _to_decimal(match.group("v"))
        if value is None or value < 0:
            return Decimal("0")
        if value > _MAX_RV_TOKEN:
            return Decimal("0")
        return value

    def handle_range_unit(match: re.Match, src: str) -> Decimal:
        if match.group("u").lower() == "m" and _is_tempo_context(src, match.start()):
            return Decimal("0")
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        a = _to_decimal(match.group("a"))
        b = _to_decimal(match.group("b"))
        if a is None or b is None or a < 0 or b < 0:
            return Decimal("0")
        return _to_km(max(a, b), match.group("u"), ctx)

    def handle_single_unit(match: re.Match, src: str) -> Decimal:
        if match.group("u").lower() == "m" and _is_tempo_context(src, match.start()):
            return Decimal("0")
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        value = _to_decimal(match.group("v"))
        if value is None or value < 0:
            return Decimal("0")
        return _to_km(value, match.group("u"), ctx)

    def handle_bare_series(match: re.Match, src: str) -> Decimal:
        if _is_tempo_context(src, match.start()):
            return Decimal("0")
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        return _tail_series_km(match.group("body"), ctx)

    add(_RV_RANGE_KM_RE, handle_rv_range)
    add(_RV_KM_RE, handle_rv)
    add(_RANGE_UNIT_RE, handle_range_unit)
    add(_SINGLE_UNIT_RE, handle_single_unit)
    add(_BARE_M_SERIES_RE, handle_bare_series)

    total += _estimate_pause_minutes_km(text, ctx)
    total += _estimate_klus_minutes_km(text, ctx)
    if total == 0:
        normalized = _strip_accents(text).lower()
        if ("klus" in normalized and "na pocit" in normalized and "del" in normalized) or (
            any(h in normalized for h in _LONG_RUN_HINTS) and any(h in normalized for h in _BY_FEEL_HINTS)
        ):
            ctx.warn("long_run_by_feel_heuristic_used")
            return Decimal("15.0")
    return total


def estimate_running_km_details(text: str | None) -> PlannedKmEstimate:
    raw = text or ""
    ctx = _ParseContext(warnings=set())
    total = _estimate_segment_km(raw, ctx).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if total > 0 and not ctx.warnings:
        confidence = "high"
    elif total > 0:
        confidence = "medium"
    else:
        confidence = "low"
        if _RUN_HINT_RE.search(raw):
            ctx.warn("run_hint_but_no_distance")

    return PlannedKmEstimate(total_km=total, confidence=confidence, warnings=sorted(ctx.warnings))


def estimate_running_km_from_text(text: str | None) -> Decimal:
    return estimate_running_km_details(text).total_km


def estimate_running_km_from_title(title: str | None) -> Decimal | None:
    total = estimate_running_km_from_text(title)
    return total if total > 0 else None


def format_week_km_label(total_km: Decimal | float | None, language_code: str) -> str:
    value = Decimal(str(total_km or 0)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if language_code.startswith("cs"):
        return f"{str(value).replace('.', ',')} km/t\u00fdden"
    return f"{value} km/week"
