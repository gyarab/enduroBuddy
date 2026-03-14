from __future__ import annotations

from ._coach_training_base import CoachTrainingPlansBase
from ._coach_training_completed_cases import CoachTrainingCompletedCases
from ._coach_training_page_cases import CoachTrainingPageCases
from ._coach_training_planned_cases import CoachTrainingPlannedCases


class CoachTrainingPlansTests(
    CoachTrainingPageCases,
    CoachTrainingPlannedCases,
    CoachTrainingCompletedCases,
    CoachTrainingPlansBase,
):
    pass
