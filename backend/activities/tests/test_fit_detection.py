from __future__ import annotations

from pathlib import Path
from unittest import skip

from django.test import SimpleTestCase

from activities.services.fit_parser import _detect_workout_type, parse_fit_file


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "fit"


class FitWorkoutTypeDetectionTests(SimpleTestCase):
    def test_easy_run_detected_as_run(self):
        path = FIXTURES_DIR / "Z3.fit"
        res = parse_fit_file(str(path))

        self.assertIn("workout_type", res.summary)
        self.assertEqual(res.summary["workout_type"], "RUN")

    def test_interval_workout_detected_as_workout(self):
        path = FIXTURES_DIR / "2x1km, 4x500m.fit"
        res = parse_fit_file(str(path))

        self.assertIn("workout_type", res.summary)
        self.assertEqual(res.summary["workout_type"], "WORKOUT")

        # bonus: workout by měl mít intervaly / splits
        self.assertTrue(len(res.intervals) >= 4)

        # bonus: pace by měl být vyplněný aspoň u části intervalů
        paces = [it.get("avg_pace_s_per_km") for it in res.intervals if it.get("avg_pace_s_per_km") is not None]
        self.assertTrue(len(paces) >= 4)

    def test_workout_type_heuristic_does_not_mark_warmup_as_workout(self):
        laps = [
            {"duration_s": 600, "distance_m": 1950, "avg_pace_s_per_km": 308},
            {"duration_s": 620, "distance_m": 2005, "avg_pace_s_per_km": 309},
            {"duration_s": 605, "distance_m": 1980, "avg_pace_s_per_km": 305},
        ]
        t = _detect_workout_type(has_workout_steps=False, laps=laps, is_auto_km_laps=False)
        self.assertEqual(t, "RUN")

    def test_workout_type_heuristic_marks_varied_work_laps_as_workout(self):
        laps = [
            {"duration_s": 220, "distance_m": 1000, "avg_pace_s_per_km": 220},
            {"duration_s": 180, "distance_m": 500, "avg_pace_s_per_km": 360},
            {"duration_s": 220, "distance_m": 1000, "avg_pace_s_per_km": 220},
            {"duration_s": 180, "distance_m": 500, "avg_pace_s_per_km": 360},
        ]
        t = _detect_workout_type(has_workout_steps=False, laps=laps, is_auto_km_laps=False)
        self.assertEqual(t, "WORKOUT")

    def test_workout_type_heuristic_marks_manual_active_rest_laps_as_workout(self):
        laps = [
            {"duration_s": 57, "distance_m": 303, "avg_pace_s_per_km": 188, "intensity": "active", "lap_trigger": "manual"},
            {"duration_s": 60, "distance_m": 90, "avg_pace_s_per_km": 662, "intensity": "rest", "lap_trigger": "manual"},
            {"duration_s": 56, "distance_m": 307, "avg_pace_s_per_km": 182, "intensity": "active", "lap_trigger": "manual"},
            {"duration_s": 59, "distance_m": 88, "avg_pace_s_per_km": 665, "intensity": "rest", "lap_trigger": "manual"},
        ]
        t = _detect_workout_type(has_workout_steps=False, laps=laps, is_auto_km_laps=False)
        self.assertEqual(t, "WORKOUT")

    @skip("debug only")
    def test_debug_z3_print_laps(self):
        path = FIXTURES_DIR / "Z3.fit"
        res = parse_fit_file(str(path))

        print("\nZ3 workout_type:", res.summary.get("workout_type"))
        print("Z3 avg_pace:", res.summary.get("avg_pace_s_per_km"))

        # vypiš prvních 25 intervalů (laps)
        for i, it in enumerate(res.intervals[:25], start=1):
            print(
                i,
                "dur", it.get("duration_s"),
                "dist", it.get("distance_m"),
                "pace", it.get("avg_pace_s_per_km"),
                "note", it.get("note"),
            )
