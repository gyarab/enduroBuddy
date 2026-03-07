from dashboard.services.month_cards import resolve_week_for_day as _resolve_week_for_day
from accounts.models import CoachAthlete
from training.models import CompletedTraining

from .views_athlete_api import (
    athlete_add_second_phase_training,
    athlete_remove_second_phase_training,
    athlete_update_completed_training,
    athlete_update_planned_training,
)
from .views_coach import (
    coach_add_second_phase_training,
    coach_remove_second_phase_training,
    coach_reorder_athletes,
    coach_training_plans,
    coach_update_athlete_focus,
    coach_update_completed_training,
    coach_update_planned_training,
)
from .views_home import home
from .views_invites import accept_training_group_invite
