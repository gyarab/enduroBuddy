from __future__ import annotations

import json
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import AppNotification, CoachAthlete, CoachJoinRequest, Role, TrainingGroup, TrainingGroupAthlete, TrainingGroupInvite
from activities.models import Activity
from dashboard.views import _resolve_week_for_day
from training.models import CompletedTraining, PlannedTraining, TrainingMonth, TrainingWeek


class CoachTrainingPlansBase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.coach = User.objects.create_user(username="coach", password="coach")
        self.athlete = User.objects.create_user(username="athlete", password="athlete")
        self.athlete2 = User.objects.create_user(username="athlete2", password="athlete2")
        self.other_coach = User.objects.create_user(username="coach2", password="coach2")

        self.coach.profile.role = Role.COACH
        self.coach.profile.save(update_fields=["role"])

        self.other_coach.profile.role = Role.COACH
        self.other_coach.profile.save(update_fields=["role"])

        self.group = TrainingGroup.objects.create(coach=self.coach, name="Skupina A")
        TrainingGroupAthlete.objects.create(group=self.group, athlete=self.athlete)

        self.other_group = TrainingGroup.objects.create(coach=self.other_coach, name="Cizi skupina")
        TrainingGroupAthlete.objects.create(group=self.other_group, athlete=self.athlete)

        week = _resolve_week_for_day(self.athlete, date(2026, 3, 5))
        PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 5),
            day_label="Thu",
            title="Easy run",
            order_in_day=1,
        )
