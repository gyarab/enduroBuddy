from __future__ import annotations

from calendar import monthrange
from datetime import date
from datetime import timedelta
import hashlib
from io import BytesIO
import logging
import secrets
from typing import Any, Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.urls import reverse
from django.shortcuts import redirect, render
from django.conf import settings
from django.utils import timezone

from accounts.models import (
    CoachAthlete,
    GarminConnection,
    GarminSyncAudit,
    Role,
    TrainingGroup,
    TrainingGroupAthlete,
    TrainingGroupInvite,
)
from accounts.services.garmin_secret_store import decrypt_tokenstore, encrypt_tokenstore, GarminSecretStoreError
from activities.models import Activity, ActivityFile, ActivityInterval
from activities.services.garmin_importer import GarminImportError, connect_garmin_account, download_garmin_fit_payloads
from activities.services.fit_importer import import_fit_into_activity
from activities.services.fit_parser import parse_fit_file
from training.models import CompletedTraining, PlannedTraining, TrainingMonth, TrainingWeek


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
logger = logging.getLogger(__name__)
GARMIN_RANGE_OPTIONS = {"today", "yesterday", "this_week", "last_week", "last_30_days", "all"}


def _fmt_mmss(seconds: Optional[int]) -> str:
    if seconds is None:
        return "-"
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def _fmt_minutes(duration_s: Optional[int]) -> str:
    if duration_s is None:
        return "-"
    mins = int(round(duration_s / 60.0))
    return str(mins)


def _fmt_km(distance_m: Optional[int]) -> str:
    if not distance_m:
        return "-"
    return f"{distance_m / 1000.0:.2f}"


def _work_intervals(intervals: list[ActivityInterval]) -> list[ActivityInterval]:
    return [
        it for it in intervals
        if (it.distance_m or 0) >= 200 and (it.duration_s or 0) >= 30
    ]


def _fmt_intervals(intervals: list[ActivityInterval]) -> str:
    work = _work_intervals(intervals)
    if not work:
        return "-"

    out = []
    for it in work:
        d = it.duration_s or 0
        if d < 60:
            out.append(str(d))
        else:
            out.append(_fmt_mmss(d))
    return "(" + ", ".join(out) + ")"


def _weighted_avg_hr(intervals: list[ActivityInterval]) -> Optional[int]:
    work = [it for it in _work_intervals(intervals) if it.avg_hr is not None]
    if not work:
        return None

    total_w = 0
    total = 0
    for it in work:
        w = int(it.duration_s or 0)
        if w <= 0:
            continue
        total_w += w
        total += int(it.avg_hr) * w

    if total_w <= 0:
        return None
    return int(round(total / total_w))


def _activity_to_completed_row(a: Activity) -> dict[str, Any]:
    intervals = list(a.intervals.all().order_by("index"))

    workout_type = a.workout_type or "RUN"
    km = _fmt_km(a.distance_m)
    minutes = _fmt_minutes(a.duration_s)
    max_hr = a.max_hr

    if workout_type == "WORKOUT":
        third = _fmt_intervals(intervals)
        avg_hr = _weighted_avg_hr(intervals)
    else:
        third = _fmt_mmss(a.avg_pace_s_per_km)
        avg_hr = a.avg_hr

    return {
        "workout_type": workout_type,
        "km": km,
        "min": minutes,
        "third": third,
        "avg_hr": avg_hr,
        "max_hr": max_hr,
    }


def _activity_segment(a: Activity) -> str:
    intervals = list(a.intervals.all().order_by("index"))
    if (a.workout_type or "RUN") == "WORKOUT":
        return _fmt_intervals(intervals)

    pace = _fmt_mmss(a.avg_pace_s_per_km)
    if pace == "-":
        return "-"
    return f"{pace}/km"


def _activity_day_key(planned: PlannedTraining, activity: Activity) -> Optional[date]:
    if planned.date is not None:
        return planned.date
    if activity.started_at is None:
        return None
    if timezone.is_aware(activity.started_at):
        return timezone.localtime(activity.started_at).date()
    return activity.started_at.date()


def _planned_day_key(t: PlannedTraining):
    if t.date is None:
        return ("undated", t.id)
    return ("dated", t.date)


def _build_planned_rows_for_week(planned_items: list[PlannedTraining]) -> list[dict[str, Any]]:
    grouped: dict[Any, list[PlannedTraining]] = {}
    for t in planned_items:
        grouped.setdefault(_planned_day_key(t), []).append(t)

    def sort_key(k):
        kind, value = k
        if kind == "dated":
            return (0, value)
        return (1, value)

    rows: list[dict[str, Any]] = []
    for key in sorted(grouped.keys(), key=sort_key):
        items = sorted(grouped[key], key=lambda x: (x.order_in_day, x.id))
        is_two_phase = any(x.is_two_phase_day for x in items)

        def planned_row_from(subitems: list[PlannedTraining], *, show_date: bool) -> dict[str, Any]:
            if not subitems:
                return {
                    "date": items[0].date if show_date else None,
                    "day_label": items[0].day_label if show_date else "",
                    "title": "-",
                    "notes": "",
                }
            first = subitems[0]
            titles = [x.title for x in subitems if x.title]
            notes = [x.notes for x in subitems if x.notes]
            return {
                "date": first.date if show_date else None,
                "day_label": first.day_label if show_date else "",
                "title": " | ".join(titles) if titles else "-",
                "notes": " | ".join(notes) if notes else "",
            }

        if is_two_phase:
            rows.append(planned_row_from(items[:1], show_date=True))
            rows.append(planned_row_from(items[1:], show_date=False))
        else:
            rows.append(planned_row_from(items, show_date=True))
    return rows


def _build_completed_row_from_activities(activities: list[Activity]) -> dict[str, Any]:
    activities = sorted(
        activities,
        key=lambda a: (a.started_at is None, a.started_at),
    )

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

        seg = _activity_segment(a)
        if seg != "-":
            third_parts.append(seg)

    km = f"{total_distance_m / 1000.0:.2f}" if total_distance_m > 0 else "-"
    minutes = str(int(round(total_duration_s / 60.0))) if total_duration_s > 0 else "-"
    avg_hr = int(round(hr_num / hr_den)) if hr_den > 0 else None

    return {
        "km": km,
        "min": minutes,
        "third": " | ".join(third_parts) if third_parts else "-",
        "avg_hr": avg_hr,
        "max_hr": max_hr,
    }


def _build_completed_rows_for_week(planned_items: list[PlannedTraining]) -> list[dict[str, Any]]:
    grouped: dict[Any, list[PlannedTraining]] = {}
    for t in planned_items:
        key = ("dated", t.date) if t.date is not None else ("undated", t.id)
        grouped.setdefault(key, []).append(t)

    rows: list[dict[str, Any]] = []
    for key in sorted(grouped.keys(), key=lambda x: (x[0] == "undated", x[1])):
        items = sorted(grouped[key], key=lambda x: (x.order_in_day, x.id))
        is_two_phase = any(x.is_two_phase_day for x in items)

        if is_two_phase:
            phase_1_activities = [x.activity for x in items[:1] if getattr(x, "activity", None)]
            phase_2_activities = [x.activity for x in items[1:] if getattr(x, "activity", None)]
            rows.append(_build_completed_row_from_activities(phase_1_activities))
            rows.append(_build_completed_row_from_activities(phase_2_activities))
        else:
            day_activities = [x.activity for x in items if getattr(x, "activity", None)]
            rows.append(_build_completed_row_from_activities(day_activities))

    return rows


def _sum_week_total(rows: list[dict[str, Any]]) -> dict[str, Any]:
    km_sum = 0.0
    min_sum = 0
    hr_num = 0
    hr_den = 0
    max_hr = None

    for r in rows:
        try:
            km_sum += float(r["km"])
        except Exception:
            pass

        try:
            m = int(r["min"])
            min_sum += m
        except Exception:
            m = 0

        if r.get("avg_hr") is not None and m > 0:
            hr_num += int(r["avg_hr"]) * m
            hr_den += m

        if r.get("max_hr") is not None:
            max_hr = max(max_hr or 0, int(r["max_hr"]))

    avg_hr = int(round(hr_num / hr_den)) if hr_den > 0 else None

    return {
        "km": f"{km_sum:.2f}" if km_sum > 0 else "-",
        "time": str(min_sum) if min_sum > 0 else "-",
        "avg_hr": avg_hr,
        "max_hr": max_hr,
    }


def _week_index_in_month(d: date) -> int:
    first_day = d.replace(day=1)
    shift = (7 - first_day.weekday()) % 7  # Monday=0
    first_monday = first_day + timedelta(days=shift)
    return ((d - first_monday).days // 7) + 1


def _week_start_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _resolve_week_for_day(user, run_day: date) -> TrainingWeek:
    week_start = _week_start_monday(run_day)
    month_obj, _ = TrainingMonth.objects.get_or_create(
        athlete=user,
        year=week_start.year,
        month=week_start.month,
    )

    planned_on_day = (
        PlannedTraining.objects
        .filter(week__training_month=month_obj, date=run_day)
        .select_related("week")
        .order_by("week__week_index", "order_in_day", "id")
        .first()
    )
    if planned_on_day:
        return planned_on_day.week

    week_index = _week_index_in_month(week_start)
    week_obj, _ = TrainingWeek.objects.get_or_create(
        training_month=month_obj,
        week_index=week_index,
    )
    return week_obj


def _resolve_planned_training(user, run_day: date, fallback_title: str) -> PlannedTraining:
    week_obj = _resolve_week_for_day(user, run_day)
    day_qs = (
        PlannedTraining.objects
        .filter(week=week_obj, date=run_day)
        .order_by("order_in_day", "id")
    )

    available = day_qs.filter(activity__isnull=True).first()
    if available:
        return available

    max_order = day_qs.order_by("-order_in_day").values_list("order_in_day", flat=True).first() or 0
    return PlannedTraining.objects.create(
        week=week_obj,
        date=run_day,
        day_label=run_day.strftime("%a"),
        title=fallback_title or "Imported activity",
        order_in_day=max_order + 1,
    )


def _import_fit_bytes_for_user(*, user, fit_bytes: bytes, original_name: str) -> bool:
    checksum = hashlib.sha256(fit_bytes).hexdigest()
    if ActivityFile.objects.filter(activity__athlete=user, checksum_sha256=checksum).exists():
        return False

    parsed = parse_fit_file(BytesIO(fit_bytes))

    started_at = parsed.summary.get("started_at") if parsed.summary else None
    if started_at is None:
        started_at = timezone.now()
    elif timezone.is_naive(started_at):
        started_at = timezone.make_aware(started_at, timezone.get_current_timezone())

    run_day = timezone.localtime(started_at).date() if timezone.is_aware(started_at) else started_at.date()
    fallback_title = (parsed.summary or {}).get("title") or "Imported activity"

    planned = _resolve_planned_training(user, run_day, fallback_title)
    activity = getattr(planned, "activity", None)
    if activity is None:
        activity = Activity.objects.create(
            athlete=user,
            planned_training=planned,
            started_at=started_at,
            title=fallback_title,
        )

    outcome = import_fit_into_activity(
        activity=activity,
        fileobj=BytesIO(fit_bytes),
        original_name=original_name or "",
        checksum_sha256=checksum,
        create_activity_file_row=True,
    )
    outcome.activity.refresh_from_db()

    completed, _ = CompletedTraining.objects.get_or_create(planned=planned)
    completed.activity = outcome.activity
    completed.time_seconds = outcome.activity.duration_s
    completed.distance_m = outcome.activity.distance_m
    completed.avg_hr = outcome.activity.avg_hr
    completed.save()
    return True


def _import_fit_for_user(user, uploaded_file) -> bool:
    fit_bytes = uploaded_file.read()
    return _import_fit_bytes_for_user(
        user=user,
        fit_bytes=fit_bytes,
        original_name=getattr(uploaded_file, "name", "") or "",
    )


def _resolve_garmin_range(window: str) -> tuple[date | None, date | None]:
    today = timezone.localdate()
    if window == "today":
        return today, today
    if window == "yesterday":
        d = today - timedelta(days=1)
        return d, d
    if window == "this_week":
        monday = today - timedelta(days=today.weekday())
        return monday, today
    if window == "last_week":
        this_monday = today - timedelta(days=today.weekday())
        return this_monday - timedelta(days=7), this_monday - timedelta(days=1)
    if window == "last_30_days":
        return today - timedelta(days=29), today
    return None, None


def _audit_garmin(
    *,
    user,
    action: str,
    status: str,
    connection: GarminConnection | None = None,
    window: str = "",
    imported_count: int = 0,
    skipped_count: int = 0,
    message: str = "",
) -> None:
    GarminSyncAudit.objects.create(
        user=user,
        connection=connection,
        action=action,
        status=status,
        window=window,
        imported_count=imported_count,
        skipped_count=skipped_count,
        message=message[:255],
    )


def _connect_garmin_for_user(user, *, email: str, password: str) -> GarminConnection:
    bundle = connect_garmin_account(email=email, password=password)
    encrypted = encrypt_tokenstore(bundle.tokenstore)
    connection, _ = GarminConnection.objects.update_or_create(
        user=user,
        defaults={
            "garmin_email": email,
            "garmin_display_name": bundle.display_name or bundle.full_name or "",
            "encrypted_tokenstore": encrypted,
            "kms_key_id": settings.GARMIN_KMS_KEY_ID,
            "is_active": True,
            "revoked_at": None,
        },
    )
    return connection


def _revoke_garmin_for_user(user) -> bool:
    connection = GarminConnection.objects.filter(user=user, is_active=True).first()
    if not connection:
        return False
    connection.is_active = False
    connection.encrypted_tokenstore = ""
    connection.revoked_at = timezone.now()
    connection.save(update_fields=["is_active", "encrypted_tokenstore", "revoked_at", "updated_at"])
    return True


def _sync_garmin_for_user(user, *, window: str) -> tuple[int, int, GarminConnection]:
    connection = GarminConnection.objects.filter(user=user, is_active=True).first()
    if connection is None:
        raise GarminImportError("Garmin account is not connected.")

    from_day, to_day = _resolve_garmin_range(window)
    tokenstore = decrypt_tokenstore(connection.encrypted_tokenstore)
    result = download_garmin_fit_payloads(
        tokenstore=tokenstore,
        limit=int(settings.GARMIN_SYNC_LIMIT),
        from_day=from_day,
        to_day=to_day,
    )

    imported = 0
    skipped = 0
    for payload in result.payloads:
        did_import = _import_fit_bytes_for_user(
            user=user,
            fit_bytes=payload.fit_bytes,
            original_name=payload.original_name,
        )
        if did_import:
            imported += 1
        else:
            skipped += 1

    connection.encrypted_tokenstore = encrypt_tokenstore(result.refreshed_tokenstore)
    connection.last_sync_at = timezone.now()
    connection.revoked_at = None
    connection.save(update_fields=["encrypted_tokenstore", "last_sync_at", "revoked_at", "updated_at"])
    return imported, skipped, connection


def _is_coach(user) -> bool:
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == Role.COACH)


def _display_name(user) -> str:
    if user.first_name or user.last_name:
        return f"{user.first_name} {user.last_name}".strip()
    return user.username


def _create_training_group_invite(*, group: TrainingGroup, created_by, invited_email: str = "") -> TrainingGroupInvite:
    # 32 bytes URL-safe token; collisions are practically negligible.
    token = secrets.token_urlsafe(32)
    return TrainingGroupInvite.objects.create(
        group=group,
        created_by=created_by,
        token=token,
        invited_email=invited_email.strip(),
        expires_at=timezone.now() + timedelta(days=7),
    )


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    total = year * 12 + (month - 1) + delta
    out_year = total // 12
    out_month = (total % 12) + 1
    return out_year, out_month


def _build_month_cards_for_athlete(*, athlete, language_code: str) -> list[dict[str, Any]]:
    months_qs = (
        TrainingMonth.objects
        .filter(athlete=athlete)
        .prefetch_related(
            Prefetch(
                "weeks",
                queryset=(
                    TrainingWeek.objects
                    .all()
                    .prefetch_related(
                        Prefetch(
                            "planned_trainings",
                            queryset=(
                                PlannedTraining.objects
                                .select_related("activity")
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
            w.planned_rows = _build_planned_rows_for_week(planned_items)
            w.completed_rows = _build_completed_rows_for_week(planned_items)
            w.completed_total = _sum_week_total(w.completed_rows)
            weeks_out.append(w)

        month_cards.append(
            {
                "id": m.id,
                "label": f"{month_dict.get(m.month, str(m.month))} {m.year}",
                "weeks": weeks_out,
            }
        )
    return month_cards


def _first_monday_in_month(year: int, month: int) -> date:
    first_day = date(year, month, 1)
    shift = (7 - first_day.weekday()) % 7
    return first_day + timedelta(days=shift)


def _add_next_month_for_athlete(*, athlete) -> tuple[bool, int, int]:
    latest = (
        TrainingMonth.objects
        .filter(athlete=athlete)
        .order_by("-year", "-month")
        .first()
    )

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

    day_labels = ["Po", "Út", "St", "Čt", "Pá", "So", "Ne"]
    weeks_created = 0
    days_created = 0

    monday = _first_monday_in_month(target_year, target_month)
    week_index = 1
    while monday.month == target_month:
        week_obj, week_was_created = TrainingWeek.objects.get_or_create(
            training_month=month_obj,
            week_index=week_index,
        )
        if week_was_created:
            weeks_created += 1

        for offset, day_label in enumerate(day_labels):
            run_day = monday + timedelta(days=offset)
            _, created = PlannedTraining.objects.get_or_create(
                week=week_obj,
                date=run_day,
                order_in_day=1,
                defaults={
                    "day_label": day_label,
                    "title": "",
                    "notes": "",
                },
            )
            if created:
                days_created += 1

        monday += timedelta(days=7)
        week_index += 1

    return month_created, weeks_created, days_created


@login_required
def home(request):
    if request.method == "POST":
        source = request.POST.get("import_source", "fit_upload")

        if source == "garmin_connect":
            email = (request.POST.get("garmin_email") or "").strip()
            password = (request.POST.get("garmin_password") or "").strip()
            if not email or not password:
                messages.error(request, "Enter Garmin email and password.")
                return redirect("dashboard_home")
            try:
                connection = _connect_garmin_for_user(request.user, email=email, password=password)
                _audit_garmin(
                    user=request.user,
                    connection=connection,
                    action=GarminSyncAudit.Action.CONNECT,
                    status=GarminSyncAudit.Status.SUCCESS,
                    message="Garmin account connected.",
                )
                messages.success(request, "Garmin account connected.")
            except (GarminImportError, GarminSecretStoreError) as exc:
                _audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.CONNECT,
                    status=GarminSyncAudit.Status.ERROR,
                    message=str(exc),
                )
                messages.error(request, f"Garmin connect failed: {exc}")
            except Exception:
                logger.exception("Garmin connect failed for user_id=%s", request.user.id)
                _audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.CONNECT,
                    status=GarminSyncAudit.Status.ERROR,
                    message="Unexpected Garmin connect error.",
                )
                messages.error(request, "Garmin connect failed.")
            return redirect("dashboard_home")

        if source == "garmin_revoke":
            revoked = _revoke_garmin_for_user(request.user)
            _audit_garmin(
                user=request.user,
                action=GarminSyncAudit.Action.REVOKE,
                status=GarminSyncAudit.Status.SUCCESS if revoked else GarminSyncAudit.Status.ERROR,
                message="Garmin account disconnected." if revoked else "No active Garmin connection.",
            )
            if revoked:
                messages.success(request, "Garmin account disconnected.")
            else:
                messages.info(request, "Garmin account is not connected.")
            return redirect("dashboard_home")

        if source == "garmin_sync":
            selected_range = request.POST.get("garmin_range", "last_30_days")
            if selected_range not in GARMIN_RANGE_OPTIONS:
                selected_range = "last_30_days"
            try:
                imported, skipped, connection = _sync_garmin_for_user(request.user, window=selected_range)
                _audit_garmin(
                    user=request.user,
                    connection=connection,
                    action=GarminSyncAudit.Action.SYNC,
                    status=GarminSyncAudit.Status.SUCCESS,
                    window=selected_range,
                    imported_count=imported,
                    skipped_count=skipped,
                    message="Garmin sync finished.",
                )
                messages.success(request, f"Garmin sync finished. Imported: {imported}, skipped duplicates: {skipped}.")
            except (GarminImportError, GarminSecretStoreError) as exc:
                _audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.SYNC,
                    status=GarminSyncAudit.Status.ERROR,
                    window=selected_range,
                    message=str(exc),
                )
                messages.error(request, f"Garmin sync failed: {exc}")
            except Exception:
                logger.exception("Garmin sync failed for user_id=%s", request.user.id)
                _audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.SYNC,
                    status=GarminSyncAudit.Status.ERROR,
                    window=selected_range,
                    message="Unexpected Garmin sync error.",
                )
                messages.error(request, "Garmin sync failed.")
            return redirect("dashboard_home")

        uploaded_file = request.FILES.get("fit_file")
        if not uploaded_file:
            messages.error(request, "Please select a FIT file.")
            return redirect("dashboard_home")
        try:
            imported = _import_fit_for_user(request.user, uploaded_file)
            if imported:
                messages.success(request, "FIT file imported.")
            else:
                messages.info(request, "This FIT file is already imported.")
        except Exception as exc:
            logger.exception("FIT import failed for user_id=%s file=%s", request.user.id, getattr(uploaded_file, "name", ""))
            if settings.DEBUG:
                messages.error(request, f"FIT import failed: {exc}")
            else:
                messages.error(request, "FIT import failed.")
        return redirect("dashboard_home")

    month_cards = _build_month_cards_for_athlete(athlete=request.user, language_code=request.LANGUAGE_CODE)
    garmin_connection = GarminConnection.objects.filter(user=request.user, is_active=True).first()
    return render(
        request,
        "dashboard/dashboard.html",
        {
            "month_cards": month_cards,
            "garmin_connection": garmin_connection,
            "is_coach": _is_coach(request.user),
        },
    )


@login_required
def coach_training_plans(request):
    if not _is_coach(request.user):
        messages.error(request, "Coach access only.")
        return redirect("dashboard_home")

    groups = list(
        TrainingGroup.objects
        .filter(coach=request.user)
        .prefetch_related("memberships__athlete")
        .order_by("name", "id")
    )
    if not groups:
        groups = [
            TrainingGroup.objects.create(
                coach=request.user,
                name="Moji svěřenci",
                description="Výchozí skupina pro pozvánky.",
            )
        ]

    selected_group = groups[0]
    selected_athlete = None

    if request.method == "POST" and request.POST.get("action") == "create_invite":
        invited_email = (request.POST.get("invited_email") or "").strip()
        _create_training_group_invite(
            group=selected_group,
            created_by=request.user,
            invited_email=invited_email,
        )
        messages.success(request, "Pozvánka byla vytvořena.")
        return redirect("coach_training_plans")

    athletes = [link.athlete for link in request.user.coachded_athletes.select_related("athlete").order_by("athlete__username")]
    athlete_ids = {a.id for a in athletes}
    for member in selected_group.memberships.select_related("athlete").all():
        if member.athlete_id not in athlete_ids:
            athletes.append(member.athlete)
            athlete_ids.add(member.athlete_id)

    active_invites = list(
        selected_group.invites
        .filter(used_at__isnull=True, expires_at__gt=timezone.now())
        .order_by("-created_at")
    )

    if request.method == "POST" and request.POST.get("action") == "bulk_add_next_month":
        created_months = 0
        created_weeks = 0
        created_days = 0
        for athlete in athletes:
            month_created, weeks_created, days_created = _add_next_month_for_athlete(athlete=athlete)
            if month_created:
                created_months += 1
            created_weeks += weeks_created
            created_days += days_created

        messages.success(request, f"Hromadně vytvořeno: měsíce {created_months}, týdny {created_weeks}, dny {created_days}.")
        return redirect("coach_training_plans")

    athlete_raw = request.GET.get("athlete")
    if athlete_raw and athlete_raw.isdigit():
        selected_athlete = next((a for a in athletes if a.id == int(athlete_raw)), None)
    if selected_athlete is None and athletes:
        selected_athlete = athletes[0]

    month_cards = []
    if selected_athlete is not None:
        month_cards = _build_month_cards_for_athlete(athlete=selected_athlete, language_code=request.LANGUAGE_CODE)

    return render(
        request,
        "dashboard/coach_training_plans.html",
        {
            "is_coach": True,
            "selected_group": selected_group,
            "athletes": athletes,
            "active_invites": active_invites,
            "selected_athlete": selected_athlete,
            "selected_athlete_name": _display_name(selected_athlete) if selected_athlete else "",
            "month_cards": month_cards,
        },
    )

@login_required
def accept_training_group_invite(request, token: str):
    invite = (
        TrainingGroupInvite.objects
        .select_related("group", "group__coach", "used_by")
        .filter(token=token)
        .first()
    )
    if invite is None:
        messages.error(request, "Pozvánka neexistuje.")
        return redirect("dashboard_home")

    is_expired = invite.expires_at <= timezone.now()
    is_used = invite.used_at is not None

    if request.method == "POST":
        if is_used:
            messages.error(request, "Pozvánka už byla použita.")
            return redirect("dashboard_home")
        if is_expired:
            messages.error(request, "Pozvánka už vypršela.")
            return redirect("dashboard_home")
        if request.user.id == invite.group.coach_id:
            messages.error(request, "Trenér nemůže přijmout vlastní pozvánku.")
            return redirect("dashboard_home")

        TrainingGroupAthlete.objects.get_or_create(group=invite.group, athlete=request.user)
        CoachAthlete.objects.get_or_create(coach=invite.group.coach, athlete=request.user)
        invite.used_at = timezone.now()
        invite.used_by = request.user
        invite.save(update_fields=["used_at", "used_by"])
        messages.success(request, "Byl/a jsi přidán/a do tréninkové skupiny.")
        return redirect("dashboard_home")

    return render(
        request,
        "dashboard/accept_training_group_invite.html",
        {
            "invite": invite,
            "is_expired": is_expired,
            "is_used": is_used,
            "is_coach": _is_coach(request.user),
        },
    )


