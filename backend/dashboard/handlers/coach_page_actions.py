from __future__ import annotations

from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from accounts.models import CoachAthlete, CoachJoinRequest, TrainingGroupAthlete
from dashboard.services.month_cards import (
    add_next_month_for_athlete,
    display_name,
)
from dashboard.texts import CoachText

def handle_coach_preselection_post(request, *, groups, selected_group):
    action = request.POST.get("action")
    if action in {"approve_join_request", "reject_join_request"}:
        join_request_id_raw = request.POST.get("join_request_id")
        if not join_request_id_raw or not join_request_id_raw.isdigit():
            messages.error(request, CoachText.INVALID_REQUEST)
            return redirect("coach_training_plans")

        join_request = (
            CoachJoinRequest.objects.select_related("athlete")
            .filter(id=int(join_request_id_raw), coach=request.user, status=CoachJoinRequest.Status.PENDING)
            .first()
        )
        if join_request is None:
            messages.error(request, CoachText.REQUEST_NOT_FOUND)
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
            messages.success(request, CoachText.REQUEST_APPROVED)
        else:
            join_request.status = CoachJoinRequest.Status.REJECTED
            join_request.decided_at = timezone.now()
            join_request.save(update_fields=["status", "decided_at"])
            messages.info(request, CoachText.REQUEST_REJECTED)
        return redirect("coach_training_plans")

    if action in {"hide_athlete", "show_athlete"}:
        return _handle_visibility_toggle(request, action=action)

    if action == "remove_athlete":
        athlete_id_raw = request.POST.get("athlete_id")
        confirm_name = (request.POST.get("confirm_name") or "").strip()
        if not athlete_id_raw or not athlete_id_raw.isdigit():
            messages.error(request, CoachText.INVALID_ATHLETE)
            return redirect("coach_training_plans")

        athlete_id = int(athlete_id_raw)
        if athlete_id == request.user.id:
            messages.error(request, CoachText.CANNOT_REMOVE_OWN_PLAN)
            return redirect("coach_training_plans")

        link = CoachAthlete.objects.select_related("athlete").filter(coach=request.user, athlete_id=athlete_id).first()
        if link is None:
            messages.error(request, CoachText.ATHLETE_NOT_FOUND)
            return redirect("coach_training_plans")

        expected_name = display_name(link.athlete).strip()
        if confirm_name != expected_name:
            messages.error(request, CoachText.CONFIRM_NAME_MISMATCH)
            return redirect("coach_training_plans")

        TrainingGroupAthlete.objects.filter(group__coach=request.user, athlete_id=athlete_id).delete()
        link.delete()
        CoachJoinRequest.objects.filter(
            coach=request.user,
            athlete_id=athlete_id,
            status=CoachJoinRequest.Status.PENDING,
        ).update(
            status=CoachJoinRequest.Status.REJECTED,
            decided_at=timezone.now(),
        )
        messages.success(request, CoachText.ATHLETE_REMOVED)
        return redirect("coach_training_plans")

    return None


def handle_coach_month_actions(request, *, athletes):
    action = request.POST.get("action")
    if action == "add_next_month_selected":
        athlete_raw = request.POST.get("athlete_id")
        target_athlete = None
        if athlete_raw and athlete_raw.isdigit():
            athlete_id = int(athlete_raw)
            target_athlete = next((athlete for athlete in athletes if athlete.id == athlete_id), None)
        if target_athlete is None:
            messages.error(request, CoachText.INVALID_ATHLETE_SELECTION)
            return redirect("coach_training_plans")

        month_created, weeks_created, days_created = add_next_month_for_athlete(athlete=target_athlete)
        if month_created:
            messages.success(request, CoachText.month_created(weeks_created=weeks_created, days_created=days_created))
        else:
            messages.info(request, CoachText.month_extended(weeks_created=weeks_created, days_created=days_created))
        return redirect(f"{reverse('coach_training_plans')}?athlete={target_athlete.id}")
    return None


def _handle_visibility_toggle(request, *, action: str):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    athlete_id_raw = request.POST.get("athlete_id")
    if not athlete_id_raw or not athlete_id_raw.isdigit():
        return _coach_toggle_error(request, is_ajax, CoachText.INVALID_ATHLETE, 400)

    athlete_id = int(athlete_id_raw)
    if athlete_id == request.user.id:
        return _coach_toggle_error(request, is_ajax, CoachText.CANNOT_HIDE_OWN_PLAN, 400)

    link = CoachAthlete.objects.filter(coach=request.user, athlete_id=athlete_id).first()
    if link is None:
        return _coach_toggle_error(request, is_ajax, CoachText.ATHLETE_NOT_FOUND, 404)

    link.hidden_from_plans = action == "hide_athlete"
    link.save(update_fields=["hidden_from_plans"])
    if is_ajax:
        return JsonResponse({"ok": True, "hidden": link.hidden_from_plans, "athlete_id": athlete_id})

    messages.success(request, CoachText.SETTINGS_SAVED)
    return redirect("coach_training_plans")


def _coach_toggle_error(request, is_ajax: bool, text: str, status: int):
    if is_ajax:
        return JsonResponse({"ok": False, "error": text}, status=status)
    messages.error(request, text)
    return redirect("coach_training_plans")
