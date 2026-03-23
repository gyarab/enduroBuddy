from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import reverse
from urllib.parse import urlencode

from allauth.socialaccount.models import SocialAccount


def _client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


class GoogleOAuthRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in settings.GOOGLE_AUTH_RATE_LIMIT_PATHS:
            ip = _client_ip(request)
            cache_key = f"google_oauth_rl:{ip}:{request.path}"
            window = settings.GOOGLE_AUTH_RATE_LIMIT_WINDOW_SECONDS
            limit = settings.GOOGLE_AUTH_RATE_LIMIT_MAX_REQUESTS

            if cache.add(cache_key, 1, timeout=window):
                count = 1
            else:
                try:
                    count = cache.incr(cache_key)
                except ValueError:
                    cache.set(cache_key, 1, timeout=window)
                    count = 1

            if count > limit:
                return render(request, "account/ratelimit.html", status=429)

        return self.get_response(request)


class GoogleProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.complete_profile_path = reverse("account_complete_profile")
        self.logout_path = reverse("account_logout")

    def __call__(self, request):
        if self._should_redirect(request):
            next_url = request.get_full_path()
            return redirect(f"{self.complete_profile_path}?{urlencode({'next': next_url})}")
        return self.get_response(request)

    def _should_redirect(self, request) -> bool:
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return False
        if request.path in {self.complete_profile_path, self.logout_path}:
            return False
        if request.path.startswith("/admin/"):
            return False
        if not SocialAccount.objects.filter(user=user, provider="google").exists():
            return False
        profile = user.profile
        return not bool(
            getattr(profile, "google_profile_completed", False)
            and getattr(profile, "google_role_confirmed", False)
        )
