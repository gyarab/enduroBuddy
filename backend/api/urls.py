from django.urls import path

from .views.auth import auth_me
from .views.coach import coach_dashboard, coach_update_athlete_focus
from .views.dashboard import athlete_dashboard
from .views.imports import fit_upload, garmin_connect, garmin_revoke, garmin_sync_start, import_job_status
from .views.notifications import list_notifications, mark_notifications_read_view
from .views.training import second_phase_training, update_completed_training, update_planned_training

urlpatterns = [
    path("auth/me/", auth_me, name="api_auth_me"),
    path("dashboard/", athlete_dashboard, name="api_dashboard"),
    path("coach/dashboard/", coach_dashboard, name="api_coach_dashboard"),
    path("coach/athlete-focus/", coach_update_athlete_focus, name="api_coach_athlete_focus"),
    path("imports/garmin/connect/", garmin_connect, name="api_imports_garmin_connect"),
    path("imports/garmin/revoke/", garmin_revoke, name="api_imports_garmin_revoke"),
    path("imports/garmin/start/", garmin_sync_start, name="api_imports_garmin_start"),
    path("imports/jobs/<int:job_id>/status/", import_job_status, name="api_imports_job_status"),
    path("imports/fit/", fit_upload, name="api_imports_fit"),
    path("notifications/", list_notifications, name="api_notifications"),
    path("notifications/mark-read/", mark_notifications_read_view, name="api_notifications_mark_read"),
    path("training/planned/<int:planned_id>/", update_planned_training, name="api_training_planned_update"),
    path("training/planned/<int:planned_id>/second-phase/", second_phase_training, name="api_training_planned_second_phase"),
    path("training/completed/<int:planned_id>/", update_completed_training, name="api_training_completed_update"),
]
