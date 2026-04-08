"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import EnduroLoginView, complete_profile
from config import error_views
from config.views_public import public_about, public_home, public_privacy, public_terms
from config.views_spa import spa_entry

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/v1/", include("api.urls")),
    path("accounts/login/", EnduroLoginView.as_view(), name="account_login"),
    path("accounts/complete-profile/", complete_profile, name="account_complete_profile"),
    path("accounts/", include("allauth.urls")),
    path("__debug/ui/errors/", error_views.error_preview_index, name="error_preview_index"),
    path("__debug/ui/errors/<int:status_code>/", error_views.error_preview_status, name="error_preview_status"),
    path("", public_home, name="public_home"),
    path("about/", public_about, name="public_about"),
    path("terms/", public_terms, name="public_terms"),
    path("privacy/", public_privacy, name="public_privacy"),
    path("app/", spa_entry, name="spa_app_root"),
    re_path(r"^app/(?P<path>.*)$", spa_entry, name="spa_app"),
    path("coach/", spa_entry, name="spa_coach_root"),
    re_path(r"^coach/(?P<path>.*)$", spa_entry, name="spa_coach"),
    path("", include("dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = "config.error_views.bad_request"
handler403 = "config.error_views.permission_denied"
handler404 = "config.error_views.page_not_found"
handler500 = "config.error_views.server_error"

