from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render


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
