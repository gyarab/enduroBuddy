from __future__ import annotations

import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import CoachAthlete, CoachJoinRequest, Role, TrainingGroup, TrainingGroupAthlete
from dashboard.services.month_cards import add_next_month_for_athlete, build_month_cards_for_athlete, display_name, is_coach
from dashboard.services.planned_km import estimate_running_km_from_title
from training.models import PlannedTraining
from .views_shared import (
    _coach_can_access_athlete,
    _create_second_phase_for_planned,
    _remove_second_phase_for_planned,
    _create_training_group_invite,
    _get_cached_coach_accessible_ids,
    maybe_add_test_notifications,
    _update_completed_training_for_planned,
    sanitize_legend_state,
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
    missing_athletes = []
    for athlete_id, athlete in athlete_by_id.items():
        if athlete_id in coach_links:
            continue
        missing_athletes.append((athlete_id, athlete))

    if missing_athletes:
        new_links = []
        for _, athlete in missing_athletes:
            current_max_order += 1
            new_links.append(
                CoachAthlete(
                    coach=request.user,
                    athlete=athlete,
                    sort_order=current_max_order,
                )
            )
        CoachAthlete.objects.bulk_create(new_links, batch_size=200)
        for link in CoachAthlete.objects.select_related("athlete").filter(
            coach=request.user,
            athlete_id__in=[athlete_id for athlete_id, _ in missing_athletes],
        ):
            coach_links[link.athlete_id] = link

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
            messages.error(request, "Neplatný výber atleta.")
            return redirect("coach_training_plans")

        month_created, weeks_created, days_created = add_next_month_for_athlete(athlete=target_athlete)
        if month_created:
            messages.success(request, f"Pridán nový mesíc: týdny {weeks_created}, dny {days_created}.")
        else:
            messages.info(request, f"Mesíc už existoval, doplneno: týdny {weeks_created}, dny {days_created}.")
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
    legend_editable = bool(selected_athlete_is_self)
    selected_athlete_legend_state_json = json.dumps({})
    if selected_athlete is not None:
        month_cards = build_month_cards_for_athlete(athlete=selected_athlete, language_code=request.LANGUAGE_CODE)
        selected_link = coach_links.get(selected_athlete.id) if not selected_athlete_is_self else None
        if selected_link is not None:
            selected_athlete_focus = (selected_link.focus or "")[:sidebar_focus_limit]
        selected_profile = getattr(selected_athlete, "profile", None)
        selected_athlete_legend_state_json = json.dumps(
            sanitize_legend_state(getattr(selected_profile, "legend_state", {}))
        )

    maybe_add_test_notifications(request)
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
            "selected_athlete_legend_state_json": selected_athlete_legend_state_json,
            "legend_editable": legend_editable,
            "legend_update_url": reverse("athlete_update_legend_state") if legend_editable else "",
            "month_cards": month_cards,
            "plan_editable": True,
            "plan_update_url": reverse("coach_update_planned_training"),
            "add_phase_url": reverse("coach_add_second_phase_training"),
            "remove_phase_url": reverse("coach_remove_second_phase_training"),
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
    if field not in {"title", "notes", "session_type"}:
        return JsonResponse({"ok": False, "error": "Invalid field."}, status=400)
    if not isinstance(value, str):
        return JsonResponse({"ok": False, "error": "Invalid value."}, status=400)
    if field == "session_type" and value not in {
        PlannedTraining.SessionType.RUN,
        PlannedTraining.SessionType.WORKOUT,
    }:
        return JsonResponse({"ok": False, "error": "Invalid session_type value."}, status=400)

    planned = (
        PlannedTraining.objects.select_related("week__training_month")
        .filter(id=planned_id)
        .first()
    )
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)

    athlete_id = planned.week.training_month.athlete_id
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(
        coach_user=request.user,
        athlete_id=athlete_id,
        accessible_ids=accessible_ids,
    ):
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    setattr(planned, field, value)
    update_fields = [field]
    if field == "title":
        estimated = estimate_running_km_from_title(value)
        if estimated is not None:
            estimated = min(estimated, _MAX_PLANNED_DISTANCE_KM)
        planned.planned_distance_km = estimated
        update_fields.append("planned_distance_km")
    planned.save(update_fields=update_fields)
    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": value})



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
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(
        coach_user=request.user,
        athlete_id=athlete_id,
        accessible_ids=accessible_ids,
    ):
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    try:
        normalized = _update_completed_training_for_planned(planned=planned, field=field, value=value)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": normalized})


@login_required
@require_POST
def coach_add_second_phase_training(request):
    if not is_coach(request.user):
        return JsonResponse({"ok": False, "error": "Coach access only."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)

    planned = (
        PlannedTraining.objects.select_related("week__training_month")
        .filter(id=planned_id)
        .first()
    )
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)

    athlete_id = planned.week.training_month.athlete_id
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(
        coach_user=request.user,
        athlete_id=athlete_id,
        accessible_ids=accessible_ids,
    ):
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    try:
        created = _create_second_phase_for_planned(planned=planned)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "planned_id": planned.id,
            "second_phase_planned_id": created.id,
        }
    )


@login_required
@require_POST
def coach_remove_second_phase_training(request):
    if not is_coach(request.user):
        return JsonResponse({"ok": False, "error": "Coach access only."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON body."}, status=400)

    planned_id = payload.get("planned_id")
    if not isinstance(planned_id, int):
        return JsonResponse({"ok": False, "error": "Invalid planned_id."}, status=400)

    planned = (
        PlannedTraining.objects.select_related("week__training_month")
        .filter(id=planned_id)
        .first()
    )
    if planned is None:
        return JsonResponse({"ok": False, "error": "Planned training not found."}, status=404)

    athlete_id = planned.week.training_month.athlete_id
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(
        coach_user=request.user,
        athlete_id=athlete_id,
        accessible_ids=accessible_ids,
    ):
        return JsonResponse({"ok": False, "error": "Forbidden for this athlete."}, status=403)

    try:
        removed_planned_id = _remove_second_phase_for_planned(planned=planned)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "planned_id": planned.id,
            "removed_planned_id": removed_planned_id,
        }
    )



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

    links = {}
    for link in CoachAthlete.objects.filter(coach=request.user, athlete_id__in=athlete_ids):
        link._original_sort_order = link.sort_order
        links[link.athlete_id] = link
    if len(links) != len(athlete_ids):
        return JsonResponse({"ok": False, "error": "One or more athletes are not linked to this coach."}, status=403)

    for index, athlete_id in enumerate(athlete_ids, start=1):
        links[athlete_id].sort_order = index

    changed_links = [link for link in links.values() if link.sort_order != getattr(link, "_original_sort_order", link.sort_order)]
    if not changed_links:
        return JsonResponse({"ok": True})

    CoachAthlete.objects.bulk_update(changed_links, ["sort_order"])
    return JsonResponse({"ok": True})


_MAX_PLANNED_DISTANCE_KM = Decimal("999.99")
