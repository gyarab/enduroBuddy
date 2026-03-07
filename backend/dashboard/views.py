from __future__ import annotations

import json
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import (
    CoachAthlete,
    CoachJoinRequest,
    GarminConnection,
    GarminSyncAudit,
    Profile,
    Role,
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
from training.models import CompletedTraining, PlannedTraining


logger = logging.getLogger(__name__)

# Backward-compatibility for tests importing this helper from dashboard.views.
_resolve_week_for_day = resolve_week_for_day


def _coach_can_access_athlete(*, coach_user, athlete_id: int) -> bool:
    if coach_user.id == athlete_id:
        return True
    has_direct_link = CoachAthlete.objects.filter(coach=coach_user, athlete_id=athlete_id).exists()
    has_group_link = TrainingGroupAthlete.objects.filter(group__coach=coach_user, athlete_id=athlete_id).exists()
    return bool(has_direct_link or has_group_link)


def _parse_optional_int(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if raw in {"", "-"}:
            return None
        if raw.isdigit():
            return int(raw)
    raise ValueError("Invalid integer value.")


def _parse_optional_distance_m(value):
    if value is None:
        return None
    if isinstance(value, str):
        raw = value.strip().replace(",", ".")
        if raw in {"", "-"}:
            return None
        km = float(raw)
    elif isinstance(value, (int, float)):
        km = float(value)
    else:
        raise ValueError("Invalid km value.")
    if km < 0:
        raise ValueError("Invalid km value.")
    return int(round(km * 1000))


def _parse_optional_minutes_to_seconds(value):
    minutes = _parse_optional_int(value)
    if minutes is None:
        return None
    if minutes < 0:
        raise ValueError("Invalid minutes value.")
    return int(minutes) * 60


def _create_training_group_invite(*, group: TrainingGroup, created_by, invited_email: str = "") -> TrainingGroupInvite:
    token = secrets.token_urlsafe(32)
    return TrainingGroupInvite.objects.create(
        group=group,
        created_by=created_by,
        token=token,
        invited_email=invited_email.strip(),
        expires_at=timezone.now() + timedelta(days=7),
    )


def _resolve_coach_from_code(raw_code: str):
    normalized = (raw_code or "").strip().upper()
    if not normalized:
        return None
    profile = Profile.objects.select_related("user").filter(role=Role.COACH, coach_join_code=normalized).first()
    return profile.user if profile else None


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
                messages.success(request, f"Přidán nový měsíc: týdny {weeks_created}, dny {days_created}.")
            else:
                messages.info(request, f"Měsíc už existoval, doplněno: týdny {weeks_created}, dny {days_created}.")
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
    if request.user.profile.role == Role.COACH:
        request.user.profile.ensure_coach_join_code()
    sidebar_name_limit = 18
    sidebar_focus_limit = 10
    sidebar_summary_limit = sidebar_name_limit + 3 + sidebar_focus_limit
    empty_focus_label = ""

    if request.method == "POST" and request.POST.get("action") == "create_invite":
        invited_email = (request.POST.get("invited_email") or "").strip()
        _create_training_group_invite(
            group=selected_group,
            created_by=request.user,
            invited_email=invited_email,
        )
        messages.success(request, "Pozv\u00e1nka byla vytvo\u0159ena.")
        return redirect("coach_training_plans")

    if request.method == "POST" and request.POST.get("action") in {"approve_join_request", "reject_join_request"}:
        action = request.POST.get("action")
        join_request_id_raw = request.POST.get("join_request_id")
        if not join_request_id_raw or not join_request_id_raw.isdigit():
            messages.error(request, "Neplatny pozadavek.")
            return redirect("coach_training_plans")
        join_request = (
            CoachJoinRequest.objects.select_related("athlete")
            .filter(id=int(join_request_id_raw), coach=request.user, status=CoachJoinRequest.Status.PENDING)
            .first()
        )
        if join_request is None:
            messages.error(request, "Pozadavek nebyl nalezen nebo uz byl vyrizen.")
            return redirect("coach_training_plans")

        if action == "approve_join_request":
            default_group = groups[0]
            TrainingGroupAthlete.objects.get_or_create(group=default_group, athlete=join_request.athlete)
            max_order = CoachAthlete.objects.filter(coach=request.user).aggregate(max_order=models.Max("sort_order")).get("max_order") or 0
            CoachAthlete.objects.get_or_create(
                coach=request.user,
                athlete=join_request.athlete,
                defaults={"sort_order": int(max_order) + 1},
            )
            join_request.status = CoachJoinRequest.Status.APPROVED
            join_request.decided_at = timezone.now()
            join_request.save(update_fields=["status", "decided_at"])
            messages.success(request, "Zadost byla schvalena.")
        else:
            join_request.status = CoachJoinRequest.Status.REJECTED
            join_request.decided_at = timezone.now()
            join_request.save(update_fields=["status", "decided_at"])
            messages.info(request, "Zadost byla zamitnuta.")
        return redirect("coach_training_plans")

    if request.method == "POST" and request.POST.get("action") in {"hide_athlete", "show_athlete"}:
        action = request.POST.get("action")
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        athlete_id_raw = request.POST.get("athlete_id")
        if not athlete_id_raw or not athlete_id_raw.isdigit():
            if is_ajax:
                return JsonResponse({"ok": False, "error": "Neplatny atlet."}, status=400)
            messages.error(request, "Neplatny atlet.")
            return redirect("coach_training_plans")
        athlete_id = int(athlete_id_raw)
        if athlete_id == request.user.id:
            if is_ajax:
                return JsonResponse({"ok": False, "error": "Nelze skryt vlastni plan."}, status=400)
            messages.error(request, "Nelze skryt vlastni plan.")
            return redirect("coach_training_plans")
        link = CoachAthlete.objects.filter(coach=request.user, athlete_id=athlete_id).first()
        if link is None:
            if is_ajax:
                return JsonResponse({"ok": False, "error": "Atlet nebyl nalezen."}, status=404)
            messages.error(request, "Atlet nebyl nalezen.")
            return redirect("coach_training_plans")
        link.hidden_from_plans = action == "hide_athlete"
        link.save(update_fields=["hidden_from_plans"])
        if is_ajax:
            return JsonResponse({"ok": True, "hidden": link.hidden_from_plans, "athlete_id": athlete_id})
        messages.success(request, "Nastaveni bylo ulozeno.")
        return redirect("coach_training_plans")

    if request.method == "POST" and request.POST.get("action") == "remove_athlete":
        athlete_id_raw = request.POST.get("athlete_id")
        confirm_name = (request.POST.get("confirm_name") or "").strip()
        if not athlete_id_raw or not athlete_id_raw.isdigit():
            messages.error(request, "Neplatny atlet.")
            return redirect("coach_training_plans")
        athlete_id = int(athlete_id_raw)
        if athlete_id == request.user.id:
            messages.error(request, "Nelze odebrat vlastni plan.")
            return redirect("coach_training_plans")

        link = CoachAthlete.objects.select_related("athlete").filter(coach=request.user, athlete_id=athlete_id).first()
        if link is None:
            messages.error(request, "Atlet nebyl nalezen.")
            return redirect("coach_training_plans")
        expected_name = display_name(link.athlete).strip()
        if confirm_name != expected_name:
            messages.error(request, "Potvrzovaci jmeno nesouhlasi.")
            return redirect("coach_training_plans")

        TrainingGroupAthlete.objects.filter(group__coach=request.user, athlete_id=athlete_id).delete()
        link.delete()
        CoachJoinRequest.objects.filter(coach=request.user, athlete_id=athlete_id, status=CoachJoinRequest.Status.PENDING).update(
            status=CoachJoinRequest.Status.REJECTED,
            decided_at=timezone.now(),
        )
        messages.success(request, "Sverenec byl odebran.")
        return redirect("coach_training_plans")

    coach_links = {
        link.athlete_id: link
        for link in request.user.coached_athletes.select_related("athlete").order_by("sort_order", "id")
    }
    athlete_by_id = {athlete_id: link.athlete for athlete_id, link in coach_links.items()}

    for member in selected_group.memberships.select_related("athlete").all():
        athlete_by_id.setdefault(member.athlete_id, member.athlete)

    # Ensure every athlete in the sidebar has a coach-athlete link for persisted focus and ordering.
    current_max_order = max((link.sort_order for link in coach_links.values()), default=0)
    for athlete_id, athlete in athlete_by_id.items():
        if athlete_id in coach_links:
            continue
        current_max_order += 1
        link = CoachAthlete.objects.create(
            coach=request.user,
            athlete=athlete,
            sort_order=current_max_order,
        )
        coach_links[athlete_id] = link

    ordered_links = sorted(coach_links.values(), key=lambda link: (link.sort_order, link.id))
    visible_ordered_links = [link for link in ordered_links if not bool(getattr(link, "hidden_from_plans", False))]
    athletes = []
    managed_athletes = []

    request.user.coach_focus = ""
    request.user.is_self_plan = True
    request.user.display_name = display_name(request.user)
    request.user.display_name_short = request.user.display_name[:sidebar_name_limit]
    request.user.sidebar_empty_focus_label = empty_focus_label
    request.user.sidebar_summary = (
        f"{request.user.display_name_short} - {empty_focus_label}" if empty_focus_label else request.user.display_name_short
    )[:sidebar_summary_limit]
    athletes.append(request.user)

    for link in ordered_links:
        if link.athlete_id == request.user.id:
            continue
        athlete = athlete_by_id.get(link.athlete_id) or link.athlete
        athlete.display_name = display_name(athlete)
        athlete.display_name_short = athlete.display_name[:sidebar_name_limit]
        athlete.coach_focus = (link.focus or "")[:sidebar_focus_limit]
        athlete.is_self_plan = False
        athlete.sidebar_empty_focus_label = empty_focus_label
        athlete_focus_text = (athlete.coach_focus or empty_focus_label).strip()
        athlete.sidebar_summary = (
            f"{athlete.display_name_short} - {athlete_focus_text}" if athlete_focus_text else athlete.display_name_short
        )[:sidebar_summary_limit]
        athlete.is_hidden_from_plans = bool(getattr(link, "hidden_from_plans", False))
        managed_athletes.append(athlete)

    managed_by_id = {athlete.id: athlete for athlete in managed_athletes}
    for link in visible_ordered_links:
        if link.athlete_id == request.user.id:
            continue
        athlete = managed_by_id.get(link.athlete_id)
        if athlete is not None:
            athletes.append(athlete)

    active_invites = list(selected_group.invites.filter(used_at__isnull=True, expires_at__gt=timezone.now()).order_by("-created_at"))
    pending_join_requests = list(
        CoachJoinRequest.objects.select_related("athlete")
        .filter(coach=request.user, status=CoachJoinRequest.Status.PENDING)
        .order_by("-created_at")
    )

    if request.method == "POST" and request.POST.get("action") == "add_next_month_selected":
        athlete_raw = request.POST.get("athlete_id")
        target_athlete = None
        if athlete_raw and athlete_raw.isdigit():
            athlete_id = int(athlete_raw)
            target_athlete = next((a for a in athletes if a.id == athlete_id), None)
        if target_athlete is None:
            messages.error(request, "Neplatný výběr atleta.")
            return redirect("coach_training_plans")

        month_created, weeks_created, days_created = add_next_month_for_athlete(athlete=target_athlete)
        if month_created:
            messages.success(request, f"Přidán nový měsíc: týdny {weeks_created}, dny {days_created}.")
        else:
            messages.info(request, f"Měsíc už existoval, doplněno: týdny {weeks_created}, dny {days_created}.")
        return redirect(f"{reverse('coach_training_plans')}?athlete={target_athlete.id}")

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
    selected_athlete_focus = ""
    selected_athlete_is_self = bool(selected_athlete and selected_athlete.id == request.user.id)
    if selected_athlete is not None:
        month_cards = build_month_cards_for_athlete(athlete=selected_athlete, language_code=request.LANGUAGE_CODE)
        selected_link = coach_links.get(selected_athlete.id) if not selected_athlete_is_self else None
        if selected_link is not None:
            selected_athlete_focus = (selected_link.focus or "")[:sidebar_focus_limit]

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
            "selected_athlete_focus": selected_athlete_focus,
            "selected_athlete_is_self": selected_athlete_is_self,
            "month_cards": month_cards,
            "plan_editable": True,
            "plan_update_url": reverse("coach_update_planned_training"),
            "completed_editable": True,
            "completed_update_url": reverse("coach_update_completed_training"),
            "add_month_enabled": selected_athlete is not None,
            "add_month_action": "add_next_month_selected",
            "add_month_athlete_id": selected_athlete.id if selected_athlete else None,
            "coach_plan_update_url": reverse("coach_update_planned_training"),
            "coach_athlete_focus_update_url": reverse("coach_update_athlete_focus"),
            "coach_athlete_reorder_url": reverse("coach_reorder_athletes"),
            "coach_join_code": request.user.profile.coach_join_code or "",
            "pending_join_requests": pending_join_requests,
            "managed_athletes": managed_athletes,
        },
    )


@login_required
@require_POST
def coach_update_planned_training(request):
    if not is_coach(request.user):
        return JsonResponse({"ok": False, "error": "Coach access only."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    field = payload.get("field")
    value = payload.get("value", "")

    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)
    if field not in {"title", "notes"}:
        return JsonResponse({"ok": False, "error": "Invalid field."}, status=400)
    if not isinstance(value, str):
        return JsonResponse({"ok": False, "error": "Invalid value."}, status=400)

    planned = (
        PlannedTraining.objects.select_related("week__training_month")
        .filter(id=planned_id)
        .first()
    )
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)

    athlete_id = planned.week.training_month.athlete_id
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id):
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    setattr(planned, field, value)
    planned.save(update_fields=[field])
    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": value})


@login_required
@require_POST
def athlete_update_planned_training(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    field = payload.get("field")
    value = payload.get("value", "")

    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)
    if field not in {"title", "notes"}:
        return JsonResponse({"ok": False, "error": "Invalid field."}, status=400)
    if not isinstance(value, str):
        return JsonResponse({"ok": False, "error": "Invalid value."}, status=400)

    planned = (
        PlannedTraining.objects.select_related("week__training_month")
        .filter(id=planned_id)
        .first()
    )
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)

    if planned.week.training_month.athlete_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    setattr(planned, field, value)
    planned.save(update_fields=[field])
    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": value})


def _update_completed_training_for_planned(*, planned: PlannedTraining, field: str, value):
    completed, _ = CompletedTraining.objects.get_or_create(planned=planned)

    if field == "km":
        completed.distance_m = _parse_optional_distance_m(value)
        completed.save(update_fields=["distance_m"])
        return "-" if completed.distance_m is None else f"{completed.distance_m / 1000.0:.2f}"

    if field == "min":
        completed.time_seconds = _parse_optional_minutes_to_seconds(value)
        completed.save(update_fields=["time_seconds"])
        if completed.time_seconds is None:
            return "-"
        return str(int(round(completed.time_seconds / 60.0)))

    if field == "third":
        if not isinstance(value, str):
            raise ValueError("Invalid text value.")
        completed.note = value
        completed.save(update_fields=["note"])
        return value or "-"

    if field == "avg_hr":
        avg_hr = _parse_optional_int(value)
        if avg_hr is not None and avg_hr < 0:
            raise ValueError("Invalid avg_hr value.")
        completed.avg_hr = avg_hr
        completed.save(update_fields=["avg_hr"])
        return completed.avg_hr

    if field == "max_hr":
        max_hr = _parse_optional_int(value)
        if max_hr is not None and max_hr < 0:
            raise ValueError("Invalid max_hr value.")
        completed.feel = "" if max_hr is None else str(max_hr)
        completed.save(update_fields=["feel"])
        if getattr(planned, "activity", None):
            planned.activity.max_hr = max_hr
            planned.activity.save(update_fields=["max_hr"])
        return max_hr

    raise ValueError("Invalid field.")


@login_required
@require_POST
def coach_update_completed_training(request):
    if not is_coach(request.user):
        return JsonResponse({"ok": False, "error": "Coach access only."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    field = payload.get("field")
    value = payload.get("value", "")

    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)
    if field not in {"km", "min", "third", "avg_hr", "max_hr"}:
        return JsonResponse({"ok": False, "error": "Invalid field."}, status=400)

    planned = PlannedTraining.objects.select_related("week__training_month", "activity").filter(id=planned_id).first()
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)

    athlete_id = planned.week.training_month.athlete_id
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id):
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    try:
        normalized = _update_completed_training_for_planned(planned=planned, field=field, value=value)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": normalized})


@login_required
@require_POST
def athlete_update_completed_training(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    field = payload.get("field")
    value = payload.get("value", "")

    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)
    if field not in {"km", "min", "third", "avg_hr", "max_hr"}:
        return JsonResponse({"ok": False, "error": "Invalid field."}, status=400)

    planned = PlannedTraining.objects.select_related("week__training_month", "activity").filter(id=planned_id).first()
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)
    if planned.week.training_month.athlete_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    try:
        normalized = _update_completed_training_for_planned(planned=planned, field=field, value=value)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": normalized})


@login_required
@require_POST
def coach_update_athlete_focus(request):
    if not is_coach(request.user):
        return JsonResponse({"ok": False, "error": "Coach access only."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    athlete_id = payload.get("athlete_id")
    focus = payload.get("focus", "")

    if not isinstance(athlete_id, int):
        return JsonResponse({"ok": False, "error": "Invalid athlete_id."}, status=400)
    if not isinstance(focus, str):
        return JsonResponse({"ok": False, "error": "Invalid focus value."}, status=400)
    focus = focus.strip()[:10]

    link = CoachAthlete.objects.filter(coach=request.user, athlete_id=athlete_id).first()
    if link is None:
        return JsonResponse({"ok": False, "error": "Athlete link not found."}, status=404)

    link.focus = focus
    link.save(update_fields=["focus"])
    return JsonResponse({"ok": True, "athlete_id": athlete_id, "focus": link.focus})


@login_required
@require_POST
def coach_reorder_athletes(request):
    if not is_coach(request.user):
        return JsonResponse({"ok": False, "error": "Coach access only."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    athlete_ids = payload.get("athlete_ids")
    if not isinstance(athlete_ids, list) or not all(isinstance(x, int) for x in athlete_ids):
        return JsonResponse({"ok": False, "error": "athlete_ids must be a list of integers."}, status=400)
    if len(set(athlete_ids)) != len(athlete_ids):
        return JsonResponse({"ok": False, "error": "Duplicate athlete ids are not allowed."}, status=400)

    links = {
        link.athlete_id: link
        for link in CoachAthlete.objects.filter(coach=request.user, athlete_id__in=athlete_ids)
    }
    if len(links) != len(athlete_ids):
        return JsonResponse({"ok": False, "error": "One or more athletes are not linked to this coach."}, status=403)

    for index, athlete_id in enumerate(athlete_ids, start=1):
        links[athlete_id].sort_order = index

    CoachAthlete.objects.bulk_update(list(links.values()), ["sort_order"])
    return JsonResponse({"ok": True})


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
