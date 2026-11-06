import unittest

from core.haversine import haversine_distance


class TestHaversine(unittest.TestCase):
    def test_same_point_is_zero(self):
        self.assertAlmostEqual(
            haversine_distance(39.9042, 116.4074, 39.9042, 116.4074), 0.0, places=6
        )

    def test_beijing_shanghai_distance(self):
        # 北京→上海 直线距离约 1067 km
        d = haversine_distance(39.9042, 116.4074, 31.2304, 121.4737)
        self.assertGreater(d, 1000)
        self.assertLess(d, 1200)
        self.assertAlmostEqual(d, 1067, delta=40)

    def test_symmetry(self):
        a = (28.4124, 100.2078)  # 稻城
        b = (41.523, 113.1118)   # 乌兰察布
        self.assertAlmostEqual(
            haversine_distance(*a, *b), haversine_distance(*b, *a), places=9
        )

    def test_short_distance_order(self):
        # 深圳→广州 远小于 深圳→北京
        sz = (22.5431, 114.0579)
        gz = (23.1291, 113.2644)
        bj = (39.9042, 116.4074)
        self.assertLess(
            haversine_distance(*sz, *gz), haversine_distance(*sz, *bj)
        )


if __name__ == "__main__":
    unittest.main()
