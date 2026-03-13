from __future__ import annotations

from types import SimpleNamespace

from django.test import SimpleTestCase

from dashboard.services.planned_interval_formatter import (
    format_planned_interval_string,
    parse_planned_interval_blocks,
    parse_planned_interval_structure,
)


def _interval(*, distance_m: int, duration_s: int, pace: int, note: str = "WORK"):
    return SimpleNamespace(
        distance_m=distance_m,
        duration_s=duration_s,
        avg_pace_s_per_km=pace,
        note=note,
    )


class PlannedIntervalFormatterTests(SimpleTestCase):
    def test_parse_parenthesized_repeat_structure(self):
        parsed = parse_planned_interval_structure("2R 4x(1200 - 400), p=1,5' po 1200 a 3' po sérii 2V")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.series, [[1200, 400], [1200, 400], [1200, 400], [1200, 400]])

    def test_parse_nested_repeat_structure(self):
        parsed = parse_planned_interval_structure("3R 2x5x300m, p=60s, po sérii 5' 2V")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.series, [[300, 300, 300, 300, 300], [300, 300, 300, 300, 300]])

    def test_parse_linear_chain_structure(self):
        parsed = parse_planned_interval_structure("2R 3km - 2km - 1 km (tempo ANP - 10K - 5K) 2V")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.series, [[3000, 2000, 1000]])

    def test_parse_multiple_blocks_split_by_plus(self):
        parsed = parse_planned_interval_blocks("2R 4x1km v tempu závodu + 5x400m mírně svižněji, P=90s 2V")
        self.assertEqual([item.series for item in parsed], [[[1000, 1000, 1000, 1000]], [[400, 400, 400, 400, 400]]])

    def test_parse_multiple_blocks_with_unitless_meter_repeats(self):
        parsed = parse_planned_interval_blocks("2R 10x400m ANP, P=40s + 6x400 v tempu 5K, P=50s + 4x300m v tempu 1500m, P=1´ 2V")
        self.assertEqual(
            [item.series for item in parsed],
            [
                [[400, 400, 400, 400, 400, 400, 400, 400, 400, 400]],
                [[400, 400, 400, 400, 400, 400]],
                [[300, 300, 300, 300]],
            ],
        )

    def test_parse_steady_distance_block_with_workout_hint(self):
        parsed = parse_planned_interval_blocks("2R 4km tempový běh v tempu 10km +2x5x150m kopec, 150m MK 2V")
        self.assertEqual([item.series for item in parsed], [[[4000]], [[150, 150, 150, 150, 150], [150, 150, 150, 150, 150]]])

    def test_formats_repeated_parenthesized_workout_by_series(self):
        intervals = [
            _interval(distance_m=1203, duration_s=251, pace=209),
            _interval(distance_m=60, duration_s=90, pace=1500, note="REST"),
            _interval(distance_m=402, duration_s=80, pace=199),
            _interval(distance_m=55, duration_s=180, pace=1800, note="REST"),
            _interval(distance_m=1198, duration_s=249, pace=208),
            _interval(distance_m=401, duration_s=79, pace=197),
            _interval(distance_m=1204, duration_s=252, pace=210),
            _interval(distance_m=398, duration_s=80, pace=201),
            _interval(distance_m=1201, duration_s=250, pace=208),
            _interval(distance_m=400, duration_s=81, pace=202),
        ]
        out = format_planned_interval_string("2R 4x(1200 - 400), p=1,5´ po 1200 a 3´ po sérii, tempo 10K - 3K 2V", intervals)
        self.assertEqual(out, "(4:11, 1:20) (4:09, 1:19) (4:12, 1:20) (4:10, 1:21)")

    def test_formats_linear_chain_and_filters_slow_mislabeled_recovery_chunks(self):
        intervals = [
            _interval(distance_m=1000, duration_s=237, pace=237),
            _interval(distance_m=1000, duration_s=238, pace=238),
            _interval(distance_m=1000, duration_s=242, pace=242),
            _interval(distance_m=557, duration_s=183, pace=328),
            _interval(distance_m=1000, duration_s=224, pace=224),
            _interval(distance_m=1000, duration_s=226, pace=226),
            _interval(distance_m=454, duration_s=150, pace=330),
            _interval(distance_m=1000, duration_s=212, pace=212),
        ]
        out = format_planned_interval_string("2R 3km - 2km - 1 km (tempo ANP - 10K - 5k), p=3´/2,5´MK 2V", intervals)
        self.assertEqual(out, "(11:57, 7:30, 3:32)")

    def test_formats_nested_repeat_linear_by_series(self):
        intervals = [
            _interval(distance_m=300, duration_s=57, pace=190),
            _interval(distance_m=300, duration_s=56, pace=187),
            _interval(distance_m=300, duration_s=56, pace=187),
            _interval(distance_m=300, duration_s=55, pace=184),
            _interval(distance_m=300, duration_s=55, pace=184),
            _interval(distance_m=300, duration_s=54, pace=180),
            _interval(distance_m=300, duration_s=55, pace=184),
            _interval(distance_m=300, duration_s=54, pace=180),
            _interval(distance_m=300, duration_s=55, pace=184),
            _interval(distance_m=300, duration_s=55, pace=184),
        ]
        out = format_planned_interval_string("3R 2x5x300m, p= 60s, po sérii 5´, tempo 1500m 2-3V", intervals)
        self.assertEqual(out, "(57, 56, 56, 55, 55) (54, 55, 54, 55, 55)")

    def test_formats_multiple_blocks_split_by_plus(self):
        intervals = [
            _interval(distance_m=1000, duration_s=231, pace=231),
            _interval(distance_m=1000, duration_s=233, pace=233),
            _interval(distance_m=1000, duration_s=234, pace=234),
            _interval(distance_m=1000, duration_s=232, pace=232),
            _interval(distance_m=400, duration_s=76, pace=190),
            _interval(distance_m=400, duration_s=75, pace=188),
            _interval(distance_m=400, duration_s=74, pace=185),
            _interval(distance_m=400, duration_s=73, pace=182),
            _interval(distance_m=400, duration_s=72, pace=180),
        ]
        out = format_planned_interval_string(
            "2R 4x1km v tempu závodu + 5x400m mírně svižněji, P= 2´po 1km a 90s po 400 2V",
            intervals,
        )
        self.assertEqual(out, "(3:51, 3:53, 3:54, 3:52) + (1:16, 1:15, 1:14, 1:13, 1:12)")

    def test_formats_steady_block_followed_by_nested_repeat(self):
        intervals = [
            _interval(distance_m=2000, duration_s=470, pace=235),
            _interval(distance_m=2000, duration_s=468, pace=234),
            _interval(distance_m=150, duration_s=26, pace=173),
            _interval(distance_m=150, duration_s=25, pace=167),
            _interval(distance_m=150, duration_s=25, pace=167),
            _interval(distance_m=150, duration_s=24, pace=160),
            _interval(distance_m=150, duration_s=25, pace=167),
            _interval(distance_m=150, duration_s=26, pace=173),
            _interval(distance_m=150, duration_s=25, pace=167),
            _interval(distance_m=150, duration_s=25, pace=167),
            _interval(distance_m=150, duration_s=24, pace=160),
            _interval(distance_m=150, duration_s=24, pace=160),
        ]
        out = format_planned_interval_string(
            "2R 4km tempový běh v tempu 10km +2x5x150m kopec, 150m MK 2V",
            intervals,
        )
        self.assertEqual(out, "(15:38) + (26, 25, 25, 24, 25) (26, 25, 25, 24, 24)")

    def test_formats_three_blocks_with_middle_unitless_repeat(self):
        intervals = [
            *[_interval(distance_m=400, duration_s=94 + (i % 2), pace=236 + (i % 2)) for i in range(10)],
            *[_interval(distance_m=400, duration_s=88 + (i % 2), pace=221 + (i % 2)) for i in range(6)],
            *[_interval(distance_m=300, duration_s=56 - (i % 2), pace=186 - (i % 2)) for i in range(4)],
        ]
        out = format_planned_interval_string(
            "2R 10x400m ANP, P=40s + 6x400 v tempu 5K, P=50s + 4x300m v tempu 1500m, P=1´ 2V",
            intervals,
        )
        self.assertEqual(
            out,
            "(1:34, 1:35, 1:34, 1:35, 1:34, 1:35, 1:34, 1:35, 1:34, 1:35) + (1:28, 1:29, 1:28, 1:29, 1:28, 1:29) + (56, 55, 56, 55)",
        )
