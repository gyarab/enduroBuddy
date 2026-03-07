from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="dashboard_home"),
    path("plans/update/", views.athlete_update_planned_training, name="athlete_update_planned_training"),
    path("plans/completed/update/", views.athlete_update_completed_training, name="athlete_update_completed_training"),
    path("coach/plans/", views.coach_training_plans, name="coach_training_plans"),
    path("coach/plans/update/", views.coach_update_planned_training, name="coach_update_planned_training"),
    path("coach/plans/completed/update/", views.coach_update_completed_training, name="coach_update_completed_training"),
    path("coach/plans/athlete-focus/", views.coach_update_athlete_focus, name="coach_update_athlete_focus"),
    path("coach/plans/reorder-athletes/", views.coach_reorder_athletes, name="coach_reorder_athletes"),
    path("coach/invite/<str:token>/", views.accept_training_group_invite, name="training_group_invite_accept"),
]
