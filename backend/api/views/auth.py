from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.conf import settings

from accounts.models import CoachAthlete, Role


def _full_name(user) -> str:
    full_name = user.get_full_name().strip()
    if full_name:
        return full_name
    return user.username or user.email or ""


def _initials(full_name: str, email: str) -> str:
    name_parts = [part for part in full_name.split() if part]
    if len(name_parts) >= 2:
        return f"{name_parts[0][0]}{name_parts[1][0]}".upper()
    if len(name_parts) == 1:
        return name_parts[0][:2].upper()
    return (email[:2] or "EB").upper()


@login_required
def auth_me(request):
    user = request.user
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", Role.ATHLETE)
    full_name = _full_name(user)
    default_app_route = "/coach/plans" if role == Role.COACH else "/app/dashboard"
    coached_athlete_count = 0
    garmin_connection = None
    try:
        garmin_connection = user.garmin_connection
    except ObjectDoesNotExist:
        garmin_connection = None
    if role == Role.COACH:
        coached_athlete_count = CoachAthlete.objects.filter(
            coach=user,
            hidden_from_plans=False,
        ).count()

    payload = {
        "id": user.id,
        "full_name": full_name,
        "email": user.email,
        "role": role,
        "initials": _initials(full_name, user.email or ""),
        "capabilities": {
            "can_view_coach": role == Role.COACH,
            "can_view_athlete": True,
            "can_complete_profile": bool(profile and not profile.google_profile_completed),
            "has_garmin_connection": bool(garmin_connection and garmin_connection.is_active),
            "garmin_connect_enabled": bool(getattr(settings, "GARMIN_CONNECT_ENABLED", False)),
            "garmin_sync_enabled": bool(getattr(settings, "GARMIN_SYNC_ENABLED", False)),
            "coached_athlete_count": coached_athlete_count,
        },
        "default_app_route": default_app_route,
    }
    return JsonResponse(payload)
