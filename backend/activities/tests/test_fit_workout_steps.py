from __future__ import annotations

from django.test import SimpleTestCase

from activities.services.fit_parser import _derive_intervals_from_workout_steps


class FitWorkoutStepDerivationTests(SimpleTestCase):
    def test_derives_distance_based_intervals_from_samples(self):
        samples = []
        t_s = 0
        distance_m = 0

        def add_segment(seconds: int, meters: int, hr: int):
            nonlocal t_s, distance_m, samples
            step_distance = meters / seconds
            for _ in range(seconds):
                t_s += 1
                distance_m += step_distance
                samples.append({"t_s": t_s, "distance_m": int(round(distance_m)), "hr": hr})

        add_segment(180, 1000, 178)
        add_segment(60, 300, 150)
        add_segment(175, 1000, 180)
        add_segment(55, 300, 148)

        steps = [
            {"distance_m": 1000, "time_s": None, "intensity": "active"},
            {"distance_m": 300, "time_s": None, "intensity": "rest"},
            {"distance_m": 1000, "time_s": None, "intensity": "active"},
            {"distance_m": 300, "time_s": None, "intensity": "rest"},
        ]

        intervals = _derive_intervals_from_workout_steps(samples, steps)

        self.assertEqual(len(intervals), 4)
        self.assertEqual([it["note"] for it in intervals], ["WORK", "REST", "WORK", "REST"])
        self.assertTrue(950 <= intervals[0]["distance_m"] <= 1050)
        self.assertTrue(250 <= intervals[1]["distance_m"] <= 350)
        self.assertTrue(170 <= intervals[0]["duration_s"] <= 190)
        self.assertTrue(50 <= intervals[1]["duration_s"] <= 70)

    def test_derives_time_based_intervals_from_samples(self):
        samples = []
        for t_s in range(0, 241):
            samples.append(
                {
                    "t_s": t_s,
                    "distance_m": int(round(t_s * 3.5)),
                    "hr": 160 if t_s < 120 else 140,
                }
            )

        steps = [
            {"distance_m": None, "time_s": 120, "intensity": "active"},
            {"distance_m": None, "time_s": 60, "intensity": "rest"},
            {"distance_m": None, "time_s": 60, "intensity": "active"},
        ]

        intervals = _derive_intervals_from_workout_steps(samples, steps)

        self.assertEqual(len(intervals), 3)
        self.assertEqual([it["duration_s"] for it in intervals], [120, 60, 60])
        self.assertEqual([it["note"] for it in intervals], ["WORK", "REST", "WORK"])
