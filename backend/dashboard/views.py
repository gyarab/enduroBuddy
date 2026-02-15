from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.models import (
    CoachAthlete,
    GarminConnection,
    GarminSyncAudit,
    TrainingGroup,
    TrainingGroupAthlete,
    TrainingGroupInvite,
)
from accounts.services.garmin_secret_store import GarminSecretStoreError
from activities.services.garmin_importer import GarminImportError
from dashboard.services.imports import (
    GARMIN_RANGE_OPTIONS,
    audit_garmin,
    connect_garmin_for_user,
    revoke_garmin_for_user,
)
from dashboard.services.month_cards import (
    add_next_month_for_athlete,
    build_month_cards_for_athlete,
    display_name,
    is_coach,
    resolve_week_for_day,
)
from dashboard.services.tasks import run_fit_import, run_garmin_sync


logger = logging.getLogger(__name__)

# Backward-compatibility for tests importing this helper from dashboard.views.
_resolve_week_for_day = resolve_week_for_day


def _create_training_group_invite(*, group: TrainingGroup, created_by, invited_email: str = "") -> TrainingGroupInvite:
    token = secrets.token_urlsafe(32)
    return TrainingGroupInvite.objects.create(
        group=group,
        created_by=created_by,
        token=token,
        invited_email=invited_email.strip(),
        expires_at=timezone.now() + timedelta(days=7),
    )


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
                connection = connect_garmin_for_user(request.user, email=email, password=password)
                audit_garmin(
                    user=request.user,
                    connection=connection,
                    action=GarminSyncAudit.Action.CONNECT,
                    status=GarminSyncAudit.Status.SUCCESS,
                    message="Garmin account connected.",
                )
                messages.success(request, "Garmin account connected.")
            except (GarminImportError, GarminSecretStoreError) as exc:
                audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.CONNECT,
                    status=GarminSyncAudit.Status.ERROR,
                    message=str(exc),
                )
                messages.error(request, f"Garmin connect failed: {exc}")
            except Exception:
                logger.exception("Garmin connect failed for user_id=%s", request.user.id)
                audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.CONNECT,
                    status=GarminSyncAudit.Status.ERROR,
                    message="Unexpected Garmin connect error.",
                )
                messages.error(request, "Garmin connect failed.")
            return redirect("dashboard_home")

        if source == "garmin_revoke":
            revoked = revoke_garmin_for_user(request.user)
            audit_garmin(
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
                sync_result = run_garmin_sync(request.user, window=selected_range)
                if sync_result is None:
                    messages.success(request, "Garmin sync queued.")
                else:
                    imported, skipped, connection = sync_result
                    audit_garmin(
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
                audit_garmin(
                    user=request.user,
                    action=GarminSyncAudit.Action.SYNC,
                    status=GarminSyncAudit.Status.ERROR,
                    window=selected_range,
                    message=str(exc),
                )
                messages.error(request, f"Garmin sync failed: {exc}")
            except Exception:
                logger.exception("Garmin sync failed for user_id=%s", request.user.id)
                audit_garmin(
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
            imported = run_fit_import(request.user, uploaded_file)
            if imported is None:
                messages.success(request, "FIT import queued.")
            elif imported:
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

    month_cards = build_month_cards_for_athlete(athlete=request.user, language_code=request.LANGUAGE_CODE)
    garmin_connection = GarminConnection.objects.filter(user=request.user, is_active=True).first()
    return render(
        request,
        "dashboard/dashboard.html",
        {
            "month_cards": month_cards,
            "garmin_connection": garmin_connection,
            "is_coach": is_coach(request.user),
        },
    )


@login_required
def coach_training_plans(request):
    if not is_coach(request.user):
        messages.error(request, "Coach access only.")
        return redirect("dashboard_home")

    groups = list(
        TrainingGroup.objects.filter(coach=request.user)
        .prefetch_related("memberships__athlete")
        .order_by("name", "id")
    )
    if not groups:
        groups = [
            TrainingGroup.objects.create(
                coach=request.user,
                name="Moji sv\u011b\u0159enci",
                description="V\u00fdchoz\u00ed skupina pro pozv\u00e1nky.",
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
        messages.success(request, "Pozv\u00e1nka byla vytvo\u0159ena.")
        return redirect("coach_training_plans")

    athletes = [link.athlete for link in request.user.coached_athletes.select_related("athlete").order_by("athlete__username")]
    athlete_ids = {a.id for a in athletes}
    for member in selected_group.memberships.select_related("athlete").all():
        if member.athlete_id not in athlete_ids:
            athletes.append(member.athlete)
            athlete_ids.add(member.athlete_id)

    active_invites = list(selected_group.invites.filter(used_at__isnull=True, expires_at__gt=timezone.now()).order_by("-created_at"))

    if request.method == "POST" and request.POST.get("action") == "bulk_add_next_month":
        created_months = 0
        created_weeks = 0
        created_days = 0
        for athlete in athletes:
            month_created, weeks_created, days_created = add_next_month_for_athlete(athlete=athlete)
            if month_created:
                created_months += 1
            created_weeks += weeks_created
            created_days += days_created

        messages.success(request, f"Hromadn\u011b vytvo\u0159eno: m\u011bs\u00edce {created_months}, t\u00fddny {created_weeks}, dny {created_days}.")
        return redirect("coach_training_plans")

    athlete_raw = request.GET.get("athlete")
    if athlete_raw and athlete_raw.isdigit():
        selected_athlete = next((a for a in athletes if a.id == int(athlete_raw)), None)
    if selected_athlete is None and athletes:
        selected_athlete = athletes[0]

    month_cards = []
    if selected_athlete is not None:
        month_cards = build_month_cards_for_athlete(athlete=selected_athlete, language_code=request.LANGUAGE_CODE)

    return render(
        request,
        "dashboard/coach_training_plans.html",
        {
            "is_coach": True,
            "selected_group": selected_group,
            "athletes": athletes,
            "active_invites": active_invites,
            "selected_athlete": selected_athlete,
            "selected_athlete_name": display_name(selected_athlete) if selected_athlete else "",
            "month_cards": month_cards,
        },
    )


@login_required
def accept_training_group_invite(request, token: str):
    invite = (
        TrainingGroupInvite.objects.select_related("group", "group__coach", "used_by")
        .filter(token=token)
        .first()
    )
    if invite is None:
        messages.error(request, "Pozv\u00e1nka neexistuje.")
        return redirect("dashboard_home")

    is_expired = invite.expires_at <= timezone.now()
    is_used = invite.used_at is not None

    if request.method == "POST":
        if is_used:
            messages.error(request, "Pozv\u00e1nka u\u017e byla pou\u017eita.")
            return redirect("dashboard_home")
        if is_expired:
            messages.error(request, "Pozv\u00e1nka u\u017e vypr\u0161ela.")
            return redirect("dashboard_home")
        if request.user.id == invite.group.coach_id:
            messages.error(request, "Tren\u00e9r nem\u016f\u017ee p\u0159ijmout vlastn\u00ed pozv\u00e1nku.")
            return redirect("dashboard_home")

        TrainingGroupAthlete.objects.get_or_create(group=invite.group, athlete=request.user)
        CoachAthlete.objects.get_or_create(coach=invite.group.coach, athlete=request.user)
        invite.used_at = timezone.now()
        invite.used_by = request.user
        invite.save(update_fields=["used_at", "used_by"])
        messages.success(request, "Byl/a jsi p\u0159id\u00e1n/a do tr\u00e9ninkov\u00e9 skupiny.")
        return redirect("dashboard_home")

    return render(
        request,
        "dashboard/accept_training_group_invite.html",
        {
            "invite": invite,
            "is_expired": is_expired,
            "is_used": is_used,
            "is_coach": is_coach(request.user),
        },
    )
