import random
import unittest

from core.haversine import haversine_distance
from core.loaders import load_routes, spots_by_id
from core.recommendation import filter_by_distance, first_stop_distance, recommend

ORIGIN = {"lat": 22.5431, "lng": 114.0579}  # 深圳


class TestRecommendation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spots = spots_by_id()
        cls.routes = load_routes()

    def test_first_stop_distance_reasonable(self):
        # 稻城亚丁到深圳约 1500km，柳州约 500km
        d_dc = haversine_distance(ORIGIN["lat"], ORIGIN["lng"], 28.4124, 100.2078)
        self.assertGreater(d_dc, 1000)
        d_lz = haversine_distance(ORIGIN["lat"], ORIGIN["lng"], 24.2386, 109.2847)
        self.assertLess(d_lz, 1000)

    def test_filter_by_distance(self):
        within = filter_by_distance(self.routes, self.spots, ORIGIN, 1000)
        self.assertGreater(len(within), 0)
        for r in within:
            self.assertLessEqual(first_stop_distance(r, self.spots, ORIGIN), 1000)

    def test_recommend_returns_three_with_first_featured(self):
        recs = recommend(self.routes, self.spots, ORIGIN, matched_tags=["嗦粉"], apply_random=False)
        self.assertEqual(len(recs), 3)
        self.assertTrue(recs[0]["is_featured"])
        self.assertFalse(recs[1]["is_featured"])
        self.assertFalse(recs[2]["is_featured"])

    def test_recommend_tag_match_ranked_top(self):
        # 强标签“嗦粉”只存在于含 SP002 的路线，确定性排序下第一条必含 SP002
        recs = recommend(self.routes, self.spots, ORIGIN, matched_tags=["嗦粉"], apply_random=False)
        self.assertIn("SP002", set(recs[0]["spot_ids"]))

    def test_recommend_random_mode_still_three(self):
        recs = recommend(
            self.routes, self.spots, ORIGIN,
            matched_tags=[], specificity=0.0, rng=random.Random(7),
        )
        self.assertEqual(len(recs), 3)

    def test_recommend_respects_duration_preference(self):
        # 明确 1 天 → 首条应为 1 日路线（确定性）
        recs = recommend(
            self.routes, self.spots, ORIGIN,
            matched_tags=[], duration_days=1, apply_random=False,
        )
        self.assertEqual(recs[0]["duration_days"], 1)


if __name__ == "__main__":
    unittest.main()
