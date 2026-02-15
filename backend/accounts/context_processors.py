from accounts.models import Role


def role_flags(request):
    user = getattr(request, "user", None)
    is_coach = False
    if user and user.is_authenticated:
        profile = getattr(user, "profile", None)
        is_coach = bool(profile and profile.role == Role.COACH)
    return {"is_coach": is_coach}
