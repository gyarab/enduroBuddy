from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import re
import unicodedata


_NUM = r"\d+(?:[.,]\d+)?"
_MUL = r"[x×]"
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
_RANGE_UNIT_RE = re.compile(rf"(?P<a>{_NUM})\s*-\s*(?P<b>{_NUM})\s*(?P<u>km|m)\b", re.IGNORECASE)
_SINGLE_UNIT_RE = re.compile(rf"(?P<v>{_NUM})\s*(?P<u>km|m)\b", re.IGNORECASE)
_BARE_M_SERIES_RE = re.compile(r"\b(?P<body>\d{3,4}(?:\s*-\s*\d{3,4}){1,})\b")
_BARE_M_TOKEN_RE = re.compile(r"(?<!\d)(?P<v>\d{3,4})(?!\d)")
_RV_KM_RE = re.compile(rf"(?<!\w)(?P<v>{_NUM})\s*(?P<t>[RV])(?=$|[\s,;+()/-])")
_PAUSE_MIN_RE = re.compile(r"(?:\bp\s*=\s*|\bpo\s*serii\s*)(?P<min>\d+(?:[.,]\d+)?)\s*['´’]", re.IGNORECASE)

_WALK_KEYWORDS = ("chuze", "mch", "walk", "walking", "hike")
_LONG_RUN_HINTS = ("delsi klus", "dlouhy klus", "long run")
_BY_FEEL_HINTS = ("na pocit", "by feel")


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
    separators = "+,;/|"
    seg_left = start
    while seg_left > 0 and text[seg_left - 1] not in separators:
        seg_left -= 1
    seg_right = end
    while seg_right < len(text) and text[seg_right] not in separators:
        seg_right += 1

    segment = _strip_accents(text[seg_left:seg_right]).lower()
    rel_start = start - seg_left
    rel_end = end - seg_left

    for keyword in _WALK_KEYWORDS:
        pos = segment.find(keyword)
        while pos != -1:
            if pos < rel_start:
                distance = rel_start - (pos + len(keyword))
            elif pos > rel_end:
                distance = pos - rel_end
            else:
                distance = 0
            if distance <= 3:
                return True
            pos = segment.find(keyword, pos + 1)
    return False


def _to_km(value: Decimal, unit: str) -> Decimal:
    if unit.lower() == "km":
        if value > Decimal("60"):
            return Decimal("0")
        return value
    if value < Decimal("100") or value > Decimal("5000"):
        return Decimal("0")
    return value / Decimal("1000")


def _tail_series_km(raw: str) -> Decimal:
    values = []
    for part in re.split(r"\s*-\s*", raw):
        parsed = _to_decimal(part)
        if parsed is None:
            return Decimal("0")
        values.append(parsed)
    if not values or any(v < 100 or v > 5000 for v in values):
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal("1000")


def _bare_m_tokens_km(raw: str) -> Decimal:
    total = Decimal("0")
    for match in _BARE_M_TOKEN_RE.finditer(raw):
        value = _to_decimal(match.group("v"))
        if value is None:
            continue
        if value < 100 or value > 5000:
            continue
        total += value / Decimal("1000")
    return total


def _estimate_pause_minutes_km(raw_text: str) -> Decimal:
    total = Decimal("0")
    for match in _PAUSE_MIN_RE.finditer(raw_text):
        mins = _to_decimal(match.group("min"))
        if mins is None or mins < 0:
            continue
        total += mins * Decimal("0.15")
    return total


def _estimate_segment_km(text: str) -> Decimal:
    if not text:
        return Decimal("0")

    total = Decimal("0")
    mutable = text
    pause_km = _estimate_pause_minutes_km(text)

    def _consume(pattern: re.Pattern, handler) -> None:
        nonlocal mutable, total
        pieces: list[str] = []
        last_end = 0
        for match in pattern.finditer(mutable):
            total += handler(match, mutable)
            pieces.append(mutable[last_end:match.start()])
            pieces.append(" " * (match.end() - match.start()))
            last_end = match.end()
        pieces.append(mutable[last_end:])
        mutable = "".join(pieces)

    def _handle_mult_range_paren(match: re.Match, src: str) -> Decimal:
        m1 = _to_decimal(match.group("m1"))
        m2 = _to_decimal(match.group("m2"))
        if m1 is None or m2 is None or m1 < 0 or m2 < 0:
            return Decimal("0")
        mult = (m1 + m2) / Decimal("2")
        body = match.group("body")
        body_km = _estimate_segment_km(body)
        if body_km == 0:
            body_km = _bare_m_tokens_km(body)
        return mult * body_km

    def _handle_mult_paren_with_tail_series(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        m = _to_decimal(match.group("m"))
        if m is None or m < 0:
            return Decimal("0")
        body_km = _estimate_segment_km(match.group("body"))
        tail_km = _tail_series_km(match.group("tail"))
        return m * (body_km + tail_km)

    def _handle_mult_single_paren(match: re.Match, src: str) -> Decimal:
        m = _to_decimal(match.group("m"))
        if m is None or m < 0:
            return Decimal("0")
        body = match.group("body")
        body_km = _estimate_segment_km(body)
        if body_km == 0:
            body_km = _bare_m_tokens_km(body)
        return m * body_km

    def _handle_mult_chain_dist_range(match: re.Match, src: str) -> Decimal:
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
        return ((a1 + a2) / Decimal("2")) * b * _to_km(d, match.group("u"))

    def _handle_mult_chain_dist_single(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        a = _to_decimal(match.group("a"))
        b = _to_decimal(match.group("b"))
        d = _to_decimal(match.group("d"))
        if None in {a, b, d}:
            return Decimal("0")
        if a < 0 or b < 0 or d < 0:
            return Decimal("0")
        return a * b * _to_km(d, match.group("u"))

    def _handle_mult_dist_range(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        m1 = _to_decimal(match.group("m1"))
        m2 = _to_decimal(match.group("m2"))
        d = _to_decimal(match.group("d"))
        if m1 is None or m2 is None or d is None or m1 < 0 or m2 < 0 or d < 0:
            return Decimal("0")
        return ((m1 + m2) / Decimal("2")) * _to_km(d, match.group("u"))

    def _handle_mult_dist_single(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        m = _to_decimal(match.group("m"))
        d = _to_decimal(match.group("d"))
        if m is None or d is None or m < 0 or d < 0:
            return Decimal("0")
        return m * _to_km(d, match.group("u"))

    def _handle_rv_km(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        value = _to_decimal(match.group("v"))
        if value is None or value < 0:
            return Decimal("0")
        return value

    def _handle_range_unit(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        a = _to_decimal(match.group("a"))
        b = _to_decimal(match.group("b"))
        if a is None or b is None or a < 0 or b < 0:
            return Decimal("0")
        return _to_km((a + b) / Decimal("2"), match.group("u"))

    def _handle_single_unit(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        value = _to_decimal(match.group("v"))
        if value is None or value < 0:
            return Decimal("0")
        return _to_km(value, match.group("u"))

    def _handle_bare_m_series(match: re.Match, src: str) -> Decimal:
        if _is_walk_context(src, match.start(), match.end()):
            return Decimal("0")
        return _tail_series_km(match.group("body"))

    _consume(_MULT_RANGE_PAREN_RE, _handle_mult_range_paren)
    _consume(_MULT_PAREN_WITH_TAIL_SERIES_RE, _handle_mult_paren_with_tail_series)
    _consume(_MULT_SINGLE_PAREN_RE, _handle_mult_single_paren)
    _consume(_MULT_CHAIN_DIST_RANGE_RE, _handle_mult_chain_dist_range)
    _consume(_MULT_CHAIN_DIST_SINGLE_RE, _handle_mult_chain_dist_single)
    _consume(_MULT_DIST_RANGE_RE, _handle_mult_dist_range)
    _consume(_MULT_DIST_SINGLE_RE, _handle_mult_dist_single)
    _consume(_RV_KM_RE, _handle_rv_km)
    _consume(_RANGE_UNIT_RE, _handle_range_unit)
    _consume(_SINGLE_UNIT_RE, _handle_single_unit)
    _consume(_BARE_M_SERIES_RE, _handle_bare_m_series)

    total += pause_km
    if total == 0:
        normalized = _strip_accents(text).lower()
        if ("klus" in normalized and "na pocit" in normalized and "del" in normalized) or (
            any(h in normalized for h in _LONG_RUN_HINTS) and any(h in normalized for h in _BY_FEEL_HINTS)
        ):
            return Decimal("15.0")
    return total


def estimate_running_km_from_text(text: str | None) -> Decimal:
    return _estimate_segment_km(text or "").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def estimate_running_km_from_title(title: str | None) -> Decimal | None:
    total = estimate_running_km_from_text(title)
    return total if total > 0 else None


def format_week_km_label(total_km: Decimal | float | None, language_code: str) -> str:
    value = Decimal(str(total_km or 0)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if language_code.startswith("cs"):
        return f"{str(value).replace('.', ',')} km/t\u00fdden"
    return f"{value} km/week"
