from __future__ import annotations

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.models import CoachAthlete, CoachJoinRequest, GarminConnection, GarminSyncAudit
from accounts.services.garmin_secret_store import GarminSecretStoreError
from activities.services.garmin_importer import GarminImportError
from dashboard.services.imports import GARMIN_RANGE_OPTIONS, audit_garmin, connect_garmin_for_user, revoke_garmin_for_user
from dashboard.services.month_cards import add_next_month_for_athlete, build_month_cards_for_athlete, is_coach
from dashboard.services.tasks import run_fit_import, run_garmin_sync
from .views_shared import _resolve_coach_from_code

logger = logging.getLogger(__name__)

@login_required
def home(request):
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "request_coach_by_code":
            coach_code = (request.POST.get("coach_code") or "").strip().upper()
            coach_user = _resolve_coach_from_code(coach_code)
            if coach_user is None:
                messages.error(request, "Kod trenera nebyl nalezen.")
                return redirect("dashboard_home")
            if coach_user.id == request.user.id:
                messages.error(request, "Nemuzes zadat vlastni kod trenera.")
                return redirect("dashboard_home")
            if CoachAthlete.objects.filter(coach=coach_user, athlete=request.user).exists():
                messages.info(request, "Uz jsi u tohoto trenera prirazeny.")
                return redirect("dashboard_home")
            already_pending = CoachJoinRequest.objects.filter(
                coach=coach_user,
                athlete=request.user,
                status=CoachJoinRequest.Status.PENDING,
            ).exists()
            if already_pending:
                messages.info(request, "Pozadavek uz ceka na schvaleni.")
                return redirect("dashboard_home")
            CoachJoinRequest.objects.create(
                coach=coach_user,
                athlete=request.user,
                status=CoachJoinRequest.Status.PENDING,
            )
            messages.success(request, "Pozadavek byl odeslan trenerovi ke schvaleni.")
            return redirect("dashboard_home")

        if action == "add_next_month_self":
            month_created, weeks_created, days_created = add_next_month_for_athlete(athlete=request.user)
            if month_created:
                messages.success(request, f"Pridán nový mesíc: týdny {weeks_created}, dny {days_created}.")
            else:
                messages.info(request, f"Mesíc už existoval, doplneno: týdny {weeks_created}, dny {days_created}.")
            return redirect("dashboard_home")

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
    pending_coach_requests = list(
        CoachJoinRequest.objects.select_related("coach")
        .filter(athlete=request.user, status=CoachJoinRequest.Status.PENDING)
        .order_by("-created_at")
    )
    approved_coach_links = list(
        CoachAthlete.objects.select_related("coach")
        .filter(athlete=request.user)
        .order_by("coach__username", "coach__id")
    )
    return render(
        request,
        "dashboard/dashboard.html",
        {
            "month_cards": month_cards,
            "month_state_key": request.user.id,
            "garmin_connection": garmin_connection,
            "is_coach": is_coach(request.user),
            "plan_editable": True,
            "plan_update_url": reverse("athlete_update_planned_training"),
            "completed_editable": True,
            "completed_update_url": reverse("athlete_update_completed_training"),
            "add_month_enabled": True,
            "add_month_action": "add_next_month_self",
            "add_month_athlete_id": None,
            "pending_coach_requests": pending_coach_requests,
            "approved_coach_links": approved_coach_links,
        },
    )


