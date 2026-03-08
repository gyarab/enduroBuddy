from accounts.models import CoachAthlete, CoachJoinRequest, Role
from django.conf import settings


def role_flags(request):
    user = getattr(request, "user", None)
    is_coach = False
    pending_coach_requests = []
    approved_coach_links = []
    if user and user.is_authenticated:
        profile = getattr(user, "profile", None)
        is_coach = bool(profile and profile.role == Role.COACH)
        pending_coach_requests = list(
            CoachJoinRequest.objects.select_related("coach")
            .filter(athlete=user, status=CoachJoinRequest.Status.PENDING)
            .order_by("-created_at")
        )
        approved_coach_links = list(
            CoachAthlete.objects.select_related("coach")
            .filter(athlete=user)
            .order_by("coach__username", "coach__id")
        )
    return {
        "is_coach": is_coach,
        "profile_pending_coach_requests": pending_coach_requests,
        "profile_approved_coach_links": approved_coach_links,
        "dashboard_asset_version": str(getattr(settings, "DASHBOARD_ASSET_VERSION", "50")),
    }
