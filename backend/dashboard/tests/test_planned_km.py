from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from dashboard.services.month_cards import build_month_cards_for_athlete
from dashboard.services.planned_km import (
    estimate_running_km_details,
    estimate_running_km_from_text,
    estimate_running_km_from_title,
    format_week_km_label,
)
from dashboard.views import _resolve_week_for_day
from training.models import PlannedTraining


class PlannedKmServiceTests(TestCase):
    def test_estimate_running_km_from_title_supports_comma_and_dot(self):
        self.assertEqual(estimate_running_km_from_title("Volne 8,5 km"), Decimal("8.50"))
        self.assertEqual(estimate_running_km_from_title("Tempo 12.3 km"), Decimal("12.30"))
        self.assertIsNone(estimate_running_km_from_title("Bez vzdalenosti"))

    def test_estimate_running_km_handles_ranges_repetitions_and_walk_exclusion(self):
        self.assertEqual(estimate_running_km_from_text("6-8 km pruzkum oblasti"), Decimal("8.00"))
        self.assertEqual(estimate_running_km_from_text("2-3x(2km + 1km)"), Decimal("9.00"))
        self.assertEqual(estimate_running_km_from_text("2x(1000-800-600-400-200)"), Decimal("6.00"))
        self.assertEqual(estimate_running_km_from_text("3x5x150m"), Decimal("2.25"))
        self.assertEqual(estimate_running_km_from_text("2-3x6x100m"), Decimal("1.80"))
        self.assertEqual(estimate_running_km_from_text("2R 8 km fartlek ... 2V"), Decimal("12.00"))
        self.assertEqual(estimate_running_km_from_text("delsi klus na pocit"), Decimal("15.00"))
        row_est = float(estimate_running_km_from_text("2R 6-8x(400ANP - 400 v tempu 5K, 200MK) P=1' 2V"))
        self.assertGreaterEqual(row_est, 10.0)
        self.assertLessEqual(row_est, 13.5)
        self.assertEqual(
            estimate_running_km_from_text("6x50m prudsi kopec s MCH + 6x300m mirnejsi kopec s MK"),
            Decimal("1.80"),
        )
        self.assertEqual(
            estimate_running_km_from_text("2R mobilita, plyometrie, prudsi kopce 6-8x100m s mch 5V"),
            Decimal("7.80"),
        )
        self.assertEqual(
            estimate_running_km_from_text("3R 2x5x300m, p= 60s, po serii 5', tempo 1500m 2-3V"),
            Decimal("9.00"),
        )
        self.assertEqual(
            estimate_running_km_from_text("2R 3x5x150m (tempo 800-1500), p=150m MCH, po serii 8 min klus 2V"),
            Decimal("12.25"),
        )

    def test_estimate_running_km_does_not_create_huge_false_range_from_m_and_km_mix(self):
        row = "2R 500-500-1km-1km-500-500 po trave, p=90s po 500 a 2' po km 2-3V tempo cca 5-10km"
        self.assertLess(float(estimate_running_km_from_text(row)), 30.0)

    def test_estimate_running_km_details_reports_confidence_and_warnings(self):
        high = estimate_running_km_details("8 km klus")
        self.assertEqual(high.confidence, "high")
        self.assertEqual(high.total_km, Decimal("8.00"))
        self.assertEqual(high.warnings, [])

        medium = estimate_running_km_details("delsi klus na pocit")
        self.assertEqual(medium.confidence, "medium")
        self.assertIn("long_run_by_feel_heuristic_used", medium.warnings)

        low = estimate_running_km_details("rychly beh podle pocitu")
        self.assertEqual(low.confidence, "low")
        self.assertEqual(low.total_km, Decimal("0.00"))
        self.assertIn("run_hint_but_no_distance", low.warnings)

    def test_estimate_running_km_matches_realistic_week_pattern(self):
        rows = [
            "9 km klus",
            "2R 2-3x(2km v tempu 1/2m - 1km v tempu 10K), p= 3' po kazdem 2V",
            "10 km klus",
            "2R 8 km fartlek (30' svizne, 120' klus) 2V",
            "2R 2x(1000-800-600-400-200) MK 400-300-200-200m po serii 5', tempo 10k-5k-3k-1500, 2V",
            "delsi klus na pocit",
            "volno",
        ]
        total = sum(float(estimate_running_km_from_text(r)) for r in rows)
        self.assertGreaterEqual(total, 71.0)
        self.assertLessEqual(total, 74.5)

    def test_format_week_km_label_is_localized(self):
        self.assertEqual(format_week_km_label(60.25, "cs"), "60,3 km/týden")
        self.assertEqual(format_week_km_label(60.25, "en"), "60.3 km/week")

    def test_build_month_cards_contains_week_planned_total_text(self):
        user = get_user_model().objects.create_user(username="athlete-km", password="x")
        week = _resolve_week_for_day(user, date(2026, 3, 2))
        PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 2),
            day_label="Mon",
            title="Easy 10 km",
            order_in_day=1,
        )
        PlannedTraining.objects.create(
            week=week,
            date=date(2026, 3, 3),
            day_label="Tue",
            title="5,5 km intervals",
            planned_distance_km=Decimal("99.00"),
            order_in_day=1,
        )

        cards_cs = build_month_cards_for_athlete(athlete=user, language_code="cs")
        cards_en = build_month_cards_for_athlete(athlete=user, language_code="en")
        self.assertEqual(cards_cs[0]["weeks"][0].planned_total_km_text, "15,5 km/týden")
        self.assertEqual(cards_en[0]["weeks"][0].planned_total_km_text, "15.5 km/week")
