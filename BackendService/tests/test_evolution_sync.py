import unittest

from core.evolution_sync import apply_deltas


class TestEvolutionSync(unittest.TestCase):
    def test_apply_deltas_accumulates(self):
        metrics = {"last_updated": "2026-01-01T00:00:00Z", "spots_metrics": {}, "routes_metrics": {}}
        deltas = {
            "spot": {"SP001": [1, 0], "SP002": [0, 1]},
            "route": {"RT001": [1, 1]},
        }
        out = apply_deltas(metrics, deltas)
        self.assertEqual(out["spots_metrics"]["SP001"]["plan_mark_count"], 1)
        self.assertEqual(out["spots_metrics"]["SP001"]["review_count"], 0)
        self.assertEqual(out["spots_metrics"]["SP002"]["review_count"], 1)
        self.assertEqual(out["routes_metrics"]["RT001"]["plan_mark_count"], 1)
        self.assertEqual(out["routes_metrics"]["RT001"]["review_count"], 1)
        self.assertNotEqual(out["last_updated"], "2026-01-01T00:00:00Z")

    def test_apply_deltas_reuses_existing_counts(self):
        metrics = {
            "last_updated": "",
            "spots_metrics": {"SP001": {"plan_mark_count": 5, "review_count": 3}},
            "routes_metrics": {},
        }
        out = apply_deltas(metrics, {"spot": {"SP001": [1, 1]}})
        self.assertEqual(out["spots_metrics"]["SP001"]["plan_mark_count"], 6)
        self.assertEqual(out["spots_metrics"]["SP001"]["review_count"], 4)


if __name__ == "__main__":
    unittest.main()
