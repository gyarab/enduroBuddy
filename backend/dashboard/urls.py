from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="dashboard_home"),
    path("coach/plans/", views.coach_training_plans, name="coach_training_plans"),
    path("coach/invite/<str:token>/", views.accept_training_group_invite, name="training_group_invite_accept"),
]
