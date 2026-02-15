from allauth.account.views import LoginView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie


@method_decorator(ensure_csrf_cookie, name="dispatch")
class EnduroLoginView(LoginView):
    """Ensure CSRF cookie is always present on GET /accounts/login/."""
