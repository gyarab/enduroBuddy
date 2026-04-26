"""
Nuxt entry point view.

In the Nuxt migration architecture, the Nuxt server handles all HTML rendering.
Django handles only: /api/v1/, /admin/, /accounts/ (POST form submissions), /i18n/.

For GET requests to /accounts/* that land on Django (via Nuxt dev proxy or direct),
this view redirects to the Nuxt frontend so client-side routing can take over.
"""
from django.conf import settings
from django.http import HttpResponseRedirect


def nuxt_redirect(request, path: str = "") -> HttpResponseRedirect:
    """Redirect GET requests to the Nuxt frontend server.

    In production, Nginx routes these requests to Nuxt directly.
    In development, the Nuxt Vite proxy forwards /accounts/* to Django;
    we redirect back to the Nuxt dev server so the SPA can render.
    """
    nuxt_dev_url = getattr(settings, "NUXT_DEV_SERVER_URL", "http://localhost:3000")
    original_path = request.get_full_path()

    if settings.DEBUG:
        return HttpResponseRedirect(f"{nuxt_dev_url}{original_path}")

    # In production this should not be reached (Nginx handles routing),
    # but fall back to redirecting to the root.
    return HttpResponseRedirect("/")
