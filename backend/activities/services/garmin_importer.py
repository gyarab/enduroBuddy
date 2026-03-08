from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
import zipfile


class GarminImportError(Exception):
    pass


@dataclass(frozen=True)
class GarminFitPayload:
    activity_id: str
    original_name: str
    fit_bytes: bytes


@dataclass(frozen=True)
class GarminConnectionBundle:
    tokenstore: str
    display_name: str
    full_name: str


@dataclass(frozen=True)
class GarminDownloadResult:
    payloads: list[GarminFitPayload]
    refreshed_tokenstore: str


def _new_client(
    *,
    email: str | None = None,
    password: str | None = None,
    return_on_mfa: bool = False,
):
    try:
        from garminconnect import Garmin
    except Exception as exc:
        raise GarminImportError("Python package 'garminconnect' is not installed.") from exc
    return Garmin(email=email, password=password, return_on_mfa=return_on_mfa)


def _extract_fit_bytes(payload: bytes) -> bytes:
    if payload.startswith(b"PK"):
        with zipfile.ZipFile(BytesIO(payload)) as zf:
            for name in zf.namelist():
                if name.lower().endswith(".fit"):
                    return zf.read(name)
        raise GarminImportError("Downloaded archive does not contain any .fit file.")
    return payload


def _iter_activity_rows(activities_result) -> list[dict]:
    if isinstance(activities_result, list):
        rows = activities_result
    elif isinstance(activities_result, dict):
        rows = activities_result.get("activities") or []
    else:
        rows = []
    return [row for row in rows if isinstance(row, dict)]


def _parse_activity_day(row: dict) -> date | None:
    raw = row.get("startTimeLocal") or row.get("startTimeGMT") or row.get("startTime")
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw.date()
    if isinstance(raw, str):
        text = raw.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(text[:19], fmt).date()
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            return None
    return None


def _row_is_in_range(row: dict, *, from_day: date | None, to_day: date | None) -> bool:
    if from_day is None and to_day is None:
        return True
    day = _parse_activity_day(row)
    if day is None:
        return False
    if from_day and day < from_day:
        return False
    if to_day and day > to_day:
        return False
    return True


def connect_garmin_account(*, email: str, password: str) -> GarminConnectionBundle:
    if not email or not password:
        raise GarminImportError("Missing Garmin email or password.")

    client = _new_client(email=email, password=password, return_on_mfa=True)
    try:
        login_status, _ = client.login()
    except Exception as exc:
        raise GarminImportError(f"Garmin login failed: {exc}") from exc

    if login_status == "needs_mfa":
        raise GarminImportError(
            "Garmin account requires MFA verification, which is not supported in this flow yet."
        )

    tokenstore = client.garth.dumps()
    if not tokenstore:
        raise GarminImportError("Garmin login succeeded but token store is empty.")

    return GarminConnectionBundle(
        tokenstore=tokenstore,
        display_name=getattr(client, "display_name", "") or "",
        full_name=getattr(client, "full_name", "") or "",
    )


def download_garmin_fit_payloads(
    *,
    tokenstore: str,
    limit: int,
    from_day: date | None = None,
    to_day: date | None = None,
) -> GarminDownloadResult:
    if not tokenstore:
        raise GarminImportError("Missing Garmin token store.")
    if limit <= 0:
        raise GarminImportError("Garmin sync limit must be a positive number.")

    client = _new_client()
    try:
        client.login(tokenstore=tokenstore)
    except Exception as exc:
        raise GarminImportError(f"Garmin token login failed: {exc}") from exc

    page_size = min(50, limit)
    offset = 0
    matched_ids: list[str] = []
    stop_due_to_range = False

    while len(matched_ids) < limit:
        rows = _iter_activity_rows(client.get_activities(offset, page_size))
        if not rows:
            break

        for row in rows:
            activity_id = row.get("activityId")
            if activity_id is None:
                continue

            if not _row_is_in_range(row, from_day=from_day, to_day=to_day):
                if from_day is not None:
                    day = _parse_activity_day(row)
                    if day is not None and day < from_day:
                        stop_due_to_range = True
                        break
                continue

            matched_ids.append(str(activity_id))
            if len(matched_ids) >= limit:
                break

        if stop_due_to_range:
            break
        offset += len(rows)

    payloads: list[GarminFitPayload] = []
    for activity_id in matched_ids:
        raw = client.download_activity(
            activity_id,
            dl_fmt=client.ActivityDownloadFormat.ORIGINAL,
        )
        payloads.append(
            GarminFitPayload(
                activity_id=activity_id,
                original_name=f"garmin_{activity_id}.fit",
                fit_bytes=_extract_fit_bytes(raw),
            )
        )

    return GarminDownloadResult(
        payloads=payloads,
        refreshed_tokenstore=client.garth.dumps(),
    )
