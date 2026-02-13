from __future__ import annotations

from pathlib import Path
from unittest import skip

from django.test import SimpleTestCase

from activities.services.fit_parser import parse_fit_file


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
