from accounts.models import Role
from django.conf import settings


def role_flags(request):
    user = getattr(request, "user", None)
    is_coach = False
    if user and user.is_authenticated:
        profile = getattr(user, "profile", None)
        is_coach = bool(profile and profile.role == Role.COACH)
    return {
        "is_coach": is_coach,
        "dashboard_asset_version": str(getattr(settings, "DASHBOARD_ASSET_VERSION", "50")),
    }
