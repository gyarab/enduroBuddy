from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import CoachAthlete, CoachJoinRequest, Role, TrainingGroup
from accounts.services.notifications import notify_athlete_plan_updated
from dashboard.api import json_error
from dashboard.handlers.coach_page_actions import handle_coach_month_actions, handle_coach_preselection_post
from dashboard.handlers.planned_training_api import (
    load_planned_training,
    parse_json_body,
    planned_athlete_id,
    save_planned_field,
    validate_completed_update_payload,
    validate_planned_id_payload,
    validate_planned_update_payload,
)
from dashboard.services.month_cards import build_month_cards_for_athlete, display_name, is_coach
from dashboard.texts import ApiText, CoachText

from .views_shared import (
    _coach_can_access_athlete,
    _create_second_phase_for_planned,
    _get_cached_coach_accessible_ids,
    _remove_second_phase_for_planned,
    _update_completed_training_for_planned,
    maybe_add_test_notifications,
    sanitize_legend_state,
)


@login_required
def coach_training_plans(request):
    if not is_coach(request.user):
        messages.error(request, ApiText.COACH_ACCESS_ONLY)
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
                name=CoachText.DEFAULT_GROUP_NAME,
                description=CoachText.DEFAULT_GROUP_DESCRIPTION,
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

    if request.method == "POST":
        post_response = handle_coach_preselection_post(request, groups=groups, selected_group=selected_group)
        if post_response is not None:
            return post_response

    coach_links = {
        link.athlete_id: link
        for link in request.user.coached_athletes.select_related("athlete").order_by("sort_order", "id")
    }
    athlete_by_id = {athlete_id: link.athlete for athlete_id, link in coach_links.items()}
    for member in selected_group.memberships.select_related("athlete").all():
        athlete_by_id.setdefault(member.athlete_id, member.athlete)

    current_max_order = max((link.sort_order for link in coach_links.values()), default=0)
    missing_athletes = [(athlete_id, athlete) for athlete_id, athlete in athlete_by_id.items() if athlete_id not in coach_links]
    if missing_athletes:
        new_links = []
        for _, athlete in missing_athletes:
            current_max_order += 1
            new_links.append(CoachAthlete(coach=request.user, athlete=athlete, sort_order=current_max_order))
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
    if request.method == "POST":
        post_response = handle_coach_month_actions(request, athletes=athletes)
        if post_response is not None:
            return post_response

    athlete_raw = request.GET.get("athlete")
    if athlete_raw and athlete_raw.isdigit():
        selected_athlete = next((athlete for athlete in athletes if athlete.id == int(athlete_raw)), None)
    if selected_athlete is None and athletes:
        selected_athlete = athletes[0]

    month_cards = []
    selected_athlete_focus = ""
    selected_athlete_is_self = bool(selected_athlete and selected_athlete.id == request.user.id)
    selected_athlete_is_managed = bool(selected_athlete and selected_athlete.id != request.user.id)
    legend_editable = bool(selected_athlete_is_self)
    selected_athlete_legend_state_json = json.dumps({})
    if selected_athlete is not None:
        month_cards = build_month_cards_for_athlete(athlete=selected_athlete, language_code=request.LANGUAGE_CODE)
        selected_link = coach_links.get(selected_athlete.id) if not selected_athlete_is_self else None
        if selected_link is not None:
            selected_athlete_focus = (selected_link.focus or "")[:sidebar_focus_limit]
        selected_profile = getattr(selected_athlete, "profile", None)
        selected_athlete_legend_state_json = json.dumps(sanitize_legend_state(getattr(selected_profile, "legend_state", {})))

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
            "completed_editable": False if selected_athlete_is_managed else bool(selected_athlete_is_self),
            "completed_lock_linked_activity": False,
            "completed_update_url": reverse("coach_update_completed_training") if selected_athlete_is_self else "",
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
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    payload, error = parse_json_body(request)
    if error:
        return error
    parsed_payload, error = validate_planned_update_payload(payload)
    if error:
        return error

    planned_id, field, value = parsed_payload
    planned, error = load_planned_training(planned_id)
    if error:
        return error

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    old_value = getattr(planned, field, "")
    save_planned_field(planned=planned, field=field, value=value)
    notify_athlete_plan_updated(
        planned=planned,
        actor=request.user,
        field=field,
        old_value=old_value,
        new_value=value,
    )
    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": value})


@login_required
@require_POST
def coach_update_completed_training(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    payload, error = parse_json_body(request)
    if error:
        return error
    parsed_payload, error = validate_completed_update_payload(payload)
    if error:
        return error

    planned_id, field, value = parsed_payload
    planned, error = load_planned_training(planned_id, include_activity=True)
    if error:
        return error

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)
    if athlete_id != request.user.id:
        return json_error(ApiText.COACH_CANNOT_EDIT_MANAGED_COMPLETED, status=403)

    try:
        normalized = _update_completed_training_for_planned(planned=planned, field=field, value=value)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "field": field, "value": normalized})


@login_required
@require_POST
def coach_add_second_phase_training(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    payload, error = parse_json_body(request)
    if error:
        return error
    planned_id, error = validate_planned_id_payload(payload)
    if error:
        return error

    planned, error = load_planned_training(planned_id)
    if error:
        return error

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    try:
        created = _create_second_phase_for_planned(planned=planned)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "second_phase_planned_id": created.id})


@login_required
@require_POST
def coach_remove_second_phase_training(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    payload, error = parse_json_body(request)
    if error:
        return error
    planned_id, error = validate_planned_id_payload(payload)
    if error:
        return error

    planned, error = load_planned_training(planned_id)
    if error:
        return error

    athlete_id = planned_athlete_id(planned)
    accessible_ids = _get_cached_coach_accessible_ids(request)
    if not _coach_can_access_athlete(coach_user=request.user, athlete_id=athlete_id, accessible_ids=accessible_ids):
        return json_error(ApiText.FORBIDDEN_FOR_ATHLETE, status=403)

    try:
        removed_planned_id = _remove_second_phase_for_planned(planned=planned)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "planned_id": planned.id, "removed_planned_id": removed_planned_id})


@login_required
@require_POST
def coach_update_athlete_focus(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    athlete_id = payload.get("athlete_id")
    focus = payload.get("focus", "")
    if not isinstance(athlete_id, int):
        return json_error(ApiText.INVALID_ATHLETE_ID, status=400)
    if not isinstance(focus, str):
        return json_error(ApiText.INVALID_FOCUS_VALUE, status=400)

    link = CoachAthlete.objects.filter(coach=request.user, athlete_id=athlete_id).first()
    if link is None:
        return json_error(ApiText.ATHLETE_LINK_NOT_FOUND, status=404)

    link.focus = focus.strip()[:10]
    link.save(update_fields=["focus"])
    return JsonResponse({"ok": True, "athlete_id": athlete_id, "focus": link.focus})


@login_required
@require_POST
def coach_reorder_athletes(request):
    if not is_coach(request.user):
        return json_error(ApiText.COACH_ACCESS_ONLY, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return json_error(ApiText.INVALID_JSON_BODY, status=400)

    athlete_ids = payload.get("athlete_ids")
    if not isinstance(athlete_ids, list) or not all(isinstance(x, int) for x in athlete_ids):
        return json_error(ApiText.ATHLETE_IDS_MUST_BE_INT_LIST, status=400)
    if len(set(athlete_ids)) != len(athlete_ids):
        return json_error(ApiText.DUPLICATE_ATHLETE_IDS, status=400)

    links = {}
    for link in CoachAthlete.objects.filter(coach=request.user, athlete_id__in=athlete_ids):
        link._original_sort_order = link.sort_order
        links[link.athlete_id] = link
    if len(links) != len(athlete_ids):
        return json_error(ApiText.UNLINKED_ATHLETE_IDS, status=403)

    for index, athlete_id in enumerate(athlete_ids, start=1):
        links[athlete_id].sort_order = index

    changed_links = [link for link in links.values() if link.sort_order != getattr(link, "_original_sort_order", link.sort_order)]
    if not changed_links:
        return JsonResponse({"ok": True})

    CoachAthlete.objects.bulk_update(changed_links, ["sort_order"])
    return JsonResponse({"ok": True})
