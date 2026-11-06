"""数据底座完整性校验（对应 check-blindbox 技能）。"""
import json
import unittest

from core.blind_masker import contains_full_name, validate_blind_name
from core.loaders import (
    load_evolution_metrics,
    load_json,
    load_routes,
    load_spots,
    load_tags_vocabulary,
)


class TestSeedData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tags_doc = load_json("tags_500.json")
        cls.vocab = load_tags_vocabulary()
        cls.spots = load_spots()
        cls.routes = load_routes()
        cls.metrics = load_evolution_metrics()

    # ---- 标签库 ----
    def test_tags_are_exactly_500_unique(self):
        self.assertEqual(self.tags_doc["total_count"], 500)
        self.assertEqual(len(self.vocab), 500)
        self.assertEqual(len(set(self.vocab)), 500)

    def test_category_counts_match_actual(self):
        for c in self.tags_doc["categories"]:
            self.assertEqual(len(c["tags"]), c["count"], c["category_id"])

    def test_spot_tags_are_in_vocabulary(self):
        for s in self.spots:
            for t in s["tags"]:
                self.assertIn(t["name"], self.vocab, f"{s['spot_id']}:{t['name']}")

    # ---- 景点盲盒 ----
    def test_spot_blind_names_valid_and_no_leak(self):
        for s in self.spots:
            ok, errs = validate_blind_name(s["full_name"], s["blind_name"])
            self.assertTrue(ok, f"{s['spot_id']}: {errs}")
            self.assertFalse(
                contains_full_name(s["description"], s["full_name"]), s["spot_id"]
            )
            self.assertFalse(
                contains_full_name(s["summary_100w"], s["full_name"]), s["spot_id"]
            )

    def test_spot_tag_types_valid(self):
        for s in self.spots:
            for t in s["tags"]:
                self.assertIn(t["type"], ("strong", "weak"), s["spot_id"])
            self.assertTrue(2 <= len(s["tags"]) <= 9, s["spot_id"])
            self.assertGreaterEqual(s["adult_ticket_price"], 0)

    # ---- 路线库 ----
    def test_routes_reference_valid_spots_and_duration(self):
        spot_ids = {s["spot_id"] for s in self.spots}
        for r in self.routes:
            self.assertIn(r["route_type"], ("single_spot", "multi_spot"), r["route_id"])
            self.assertTrue(1 <= r["duration_days"] <= 7, r["route_id"])
            for sid in r["spot_ids"]:
                self.assertIn(sid, spot_ids, r["route_id"])
            if r["route_type"] == "single_spot":
                self.assertEqual(len(r["spot_ids"]), 1, r["route_id"])
                self.assertLessEqual(r["duration_days"], 2, r["route_id"])
            else:
                self.assertGreaterEqual(len(r["spot_ids"]), 2, r["route_id"])
                self.assertGreaterEqual(r["duration_days"], 2, r["route_id"])
            self.assertEqual(len(r["daily_schedule"]), r["duration_days"], r["route_id"])

    # ---- 进化变量 ----
    def test_evolution_metrics_covers_all_ids(self):
        spot_ids = {s["spot_id"] for s in self.spots}
        route_ids = {r["route_id"] for r in self.routes}
        self.assertEqual(set(self.metrics["spots_metrics"].keys()), spot_ids)
        self.assertEqual(set(self.metrics["routes_metrics"].keys()), route_ids)

    def test_evolution_metrics_zero_provenance(self):
        raw = json.dumps(self.metrics, ensure_ascii=False).lower()
        for forbidden in ("user_id", "nickname", "device_id", "uuid", "ip_address"):
            self.assertNotIn(forbidden, raw)


if __name__ == "__main__":
    unittest.main()
