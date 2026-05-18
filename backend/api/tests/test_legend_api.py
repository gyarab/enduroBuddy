from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import CoachAthlete

User = get_user_model()


class LegendAthleteIdTest(TestCase):
    def setUp(self):
        self.coach = User.objects.create_user(
            username="coach@test.com", password="pass", email="coach@test.com"
        )
        self.coach.profile.role = "COACH"
        self.coach.profile.save()
        self.athlete = User.objects.create_user(
            username="ath@test.com", password="pass", email="ath@test.com"
        )
        self.athlete.profile.legend_state = {"zones": {"1": {"from": "100", "to": "120"}}}
        self.athlete.profile.save()
        CoachAthlete.objects.create(coach=self.coach, athlete=self.athlete)

    def test_coach_can_get_athlete_legend(self):
        self.client.force_login(self.coach)
        resp = self.client.get(
            f"/api/v1/legend/?athlete_id={self.athlete.id}"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["state"]["zones"]["1"]["from"], "100")

    def test_athlete_cannot_get_others_legend(self):
        self.client.force_login(self.athlete)
        resp = self.client.get(
            f"/api/v1/legend/?athlete_id={self.coach.id}"
        )
        self.assertEqual(resp.status_code, 403)

    def test_invalid_athlete_id_returns_404(self):
        self.client.force_login(self.coach)
        resp = self.client.get("/api/v1/legend/?athlete_id=999999")
        self.assertEqual(resp.status_code, 404)

    def test_coach_cannot_get_unmanaged_athlete_legend(self):
        """A coach who does not manage an athlete must not be able to read their legend."""
        other_athlete = User.objects.create_user(
            username="other@test.com", password="pass", email="other@test.com"
        )
        other_athlete.profile.legend_state = {"zones": {"1": {"from": "140", "to": "160"}}}
        other_athlete.profile.save()
        # No CoachAthlete link between self.coach and other_athlete
        self.client.force_login(self.coach)
        resp = self.client.get(f"/api/v1/legend/?athlete_id={other_athlete.id}")
        self.assertEqual(resp.status_code, 404)
