from django.urls import path

from .views.auth import auth_me
from .views.coach import (
    coach_athletes,
    coach_create_planned_training,
    coach_dashboard,
    coach_reorder_athletes,
    coach_second_phase_training,
    coach_toggle_athlete_visibility,
    coach_update_athlete_focus,
    coach_update_completed_training,
    coach_update_planned_training,
)
from .views.dashboard import athlete_dashboard
from .views.imports import fit_upload, garmin_connect, garmin_revoke, garmin_sync_start, import_job_status
from .views.notifications import list_notifications, mark_notifications_read_view
from .views.profile import profile_completion
from .views.training import create_planned_training, second_phase_training, update_completed_training, update_planned_training

urlpatterns = [
    path("auth/me/", auth_me, name="api_auth_me"),
    path("profile/complete/", profile_completion, name="api_profile_complete"),
    path("dashboard/", athlete_dashboard, name="api_dashboard"),
    path("coach/athletes/", coach_athletes, name="api_coach_athletes"),
    path("coach/dashboard/", coach_dashboard, name="api_coach_dashboard"),
    path("coach/training/planned/", coach_create_planned_training, name="api_coach_training_planned_create"),
    path("coach/training/planned/<int:planned_id>/", coach_update_planned_training, name="api_coach_training_planned_update"),
    path("coach/training/completed/<int:planned_id>/", coach_update_completed_training, name="api_coach_training_completed_update"),
    path(
        "coach/training/planned/<int:planned_id>/second-phase/",
        coach_second_phase_training,
        name="api_coach_training_planned_second_phase",
    ),
    path("coach/athlete-focus/", coach_update_athlete_focus, name="api_coach_athlete_focus"),
    path("coach/reorder-athletes/", coach_reorder_athletes, name="api_coach_reorder_athletes"),
    path("coach/athlete-visibility/", coach_toggle_athlete_visibility, name="api_coach_athlete_visibility"),
    path("imports/garmin/connect/", garmin_connect, name="api_imports_garmin_connect"),
    path("imports/garmin/revoke/", garmin_revoke, name="api_imports_garmin_revoke"),
    path("imports/garmin/start/", garmin_sync_start, name="api_imports_garmin_start"),
    path("imports/jobs/<int:job_id>/status/", import_job_status, name="api_imports_job_status"),
    path("imports/fit/", fit_upload, name="api_imports_fit"),
    path("notifications/", list_notifications, name="api_notifications"),
    path("notifications/mark-read/", mark_notifications_read_view, name="api_notifications_mark_read"),
    path("training/planned/", create_planned_training, name="api_training_planned_create"),
    path("training/planned/<int:planned_id>/", update_planned_training, name="api_training_planned_update"),
    path("training/planned/<int:planned_id>/second-phase/", second_phase_training, name="api_training_planned_second_phase"),
    path("training/completed/<int:planned_id>/", update_completed_training, name="api_training_completed_update"),
]
