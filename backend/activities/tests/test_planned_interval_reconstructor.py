from __future__ import annotations

from django.test import SimpleTestCase

from activities.services.fit_parser import FitParseResult
from activities.services.planned_interval_reconstructor import reconstruct_intervals_from_plan


class PlannedIntervalReconstructorTests(SimpleTestCase):
    def test_keeps_existing_structured_work_and_rest_intervals(self):
        parsed = FitParseResult(
            summary={"workout_type": "WORKOUT", "duration_s": 1393, "distance_m": 3942},
            intervals=[
                {"duration_s": 57, "distance_m": 303, "note": "WORK"},
                {"duration_s": 60, "distance_m": 90, "note": "REST"},
                {"duration_s": 56, "distance_m": 307, "note": "WORK"},
                {"duration_s": 59, "distance_m": 88, "note": "REST"},
                {"duration_s": 56, "distance_m": 308, "note": "WORK"},
                {"duration_s": 59, "distance_m": 82, "note": "REST"},
                {"duration_s": 55, "distance_m": 306, "note": "WORK"},
                {"duration_s": 62, "distance_m": 89, "note": "REST"},
                {"duration_s": 55, "distance_m": 309, "note": "WORK"},
                {"duration_s": 330, "distance_m": 134, "note": "REST"},
                {"duration_s": 54, "distance_m": 307, "note": "WORK"},
                {"duration_s": 62, "distance_m": 94, "note": "REST"},
                {"duration_s": 55, "distance_m": 304, "note": "WORK"},
                {"duration_s": 63, "distance_m": 99, "note": "REST"},
                {"duration_s": 54, "distance_m": 304, "note": "WORK"},
                {"duration_s": 63, "distance_m": 93, "note": "REST"},
                {"duration_s": 55, "distance_m": 307, "note": "WORK"},
                {"duration_s": 68, "distance_m": 92, "note": "REST"},
                {"duration_s": 55, "distance_m": 307, "note": "WORK"},
            ],
            samples=[{"t_s": 0, "distance_m": 0, "hr": 120}, {"t_s": 100, "distance_m": 500, "hr": 170}],
        )
        out = reconstruct_intervals_from_plan(
            title="3R 2x5x300m, p= 60s, po sérii 5´, tempo 1500m  2-3V",
            parsed_result=parsed,
        )
        self.assertEqual(out.intervals, parsed.intervals)

    def test_reconstructs_equal_repeats_from_total_duration_when_samples_not_segmentable(self):
        parsed = FitParseResult(
            summary={"workout_type": "WORKOUT", "duration_s": 1393, "distance_m": 3942},
            intervals=[
                {"duration_s": 283, "distance_m": 1000, "note": "WORK"},
                {"duration_s": 280, "distance_m": 1000, "note": "WORK"},
            ],
            samples=[],
        )
        out = reconstruct_intervals_from_plan(
            title="3R 2x5x300m, p= 60s, po sérii 5´, tempo 1500m  2-3V",
            parsed_result=parsed,
        )
        self.assertEqual(len(out.intervals), 19)
        work = [it for it in out.intervals if it["note"] == "WORK"]
        rest = [it for it in out.intervals if it["note"] == "REST"]
        self.assertEqual(len(work), 10)
        self.assertEqual(len(rest), 9)
        self.assertTrue(all(it["distance_m"] == 300 for it in work))
        self.assertEqual(rest[0]["duration_s"], 60)
        self.assertEqual(rest[4]["duration_s"], 300)

    def test_leaves_result_unchanged_when_no_rest_hints(self):
        parsed = FitParseResult(
            summary={"workout_type": "WORKOUT"},
            intervals=[{"duration_s": 100, "distance_m": 500, "note": "WORK"}],
            samples=[{"t_s": 0, "distance_m": 0, "hr": 120}, {"t_s": 100, "distance_m": 500, "hr": 170}],
        )
        out = reconstruct_intervals_from_plan(
            title="2R 10x400m ANP 2V",
            parsed_result=parsed,
        )
        self.assertEqual(out.intervals, parsed.intervals)
