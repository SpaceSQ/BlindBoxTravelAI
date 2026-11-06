import math
import unittest

from core.tag_matcher import (
    compute_popularity,
    compute_season_fit,
    compute_tag_match,
    season_for_month,
    tag_weight,
    temperature_for_specificity,
)

SPOTS = {
    "A": {"tags": [{"name": "雪山", "type": "strong"}, {"name": "赏秋", "type": "weak"}]},
    "B": {"tags": [{"name": "嗦粉", "type": "strong"}]},
}


def route(spots):
    return {"spot_ids": spots}


class TestTagMatcher(unittest.TestCase):
    def test_weights(self):
        self.assertEqual(tag_weight("strong"), 3.0)
        self.assertEqual(tag_weight("weak"), 1.0)

    def test_tag_match(self):
        self.assertEqual(compute_tag_match(route(["A"]), SPOTS, ["雪山"]), 3.0)
        self.assertEqual(compute_tag_match(route(["A"]), SPOTS, ["赏秋"]), 1.0)
        self.assertEqual(compute_tag_match(route(["A"]), SPOTS, ["雪山", "赏秋"]), 4.0)
        self.assertEqual(compute_tag_match(route(["A"]), SPOTS, ["嗦粉"]), 0.0)
        # 多景点路线：标签汇总，同名取 strong
        self.assertEqual(compute_tag_match(route(["A", "B"]), SPOTS, ["雪山", "嗦粉"]), 6.0)

    def test_season_fit(self):
        # 秋季标签命中秋季 → 1.0
        self.assertEqual(compute_season_fit(route(["A"]), SPOTS, 10), 1.0)
        # 秋季标签在冬季 → 0.2
        self.assertEqual(compute_season_fit(route(["A"]), SPOTS, 1), 0.2)
        # 无季节标签 → 0.5
        self.assertEqual(compute_season_fit(route(["B"]), SPOTS, 10), 0.5)

    def test_popularity(self):
        self.assertEqual(compute_popularity({"plan_mark_count": 0, "review_count": 0}), 0.0)
        self.assertAlmostEqual(
            compute_popularity({"plan_mark_count": 0, "review_count": 1}), math.log(3)
        )

    def test_temperature_bounds(self):
        self.assertAlmostEqual(temperature_for_specificity(0.0), 0.85)
        self.assertAlmostEqual(temperature_for_specificity(1.0), 0.15)
        self.assertLess(temperature_for_specificity(0.9), temperature_for_specificity(0.1))

    def test_season_for_month(self):
        self.assertEqual(season_for_month(4), "春")
        self.assertEqual(season_for_month(7), "夏")
        self.assertEqual(season_for_month(10), "秋")
        self.assertEqual(season_for_month(12), "冬")


if __name__ == "__main__":
    unittest.main()
