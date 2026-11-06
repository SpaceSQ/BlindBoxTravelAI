import unittest

from core.blind_masker import (
    contains_full_name,
    mask_full_name,
    sanitize_text,
    validate_blind_name,
)

SEED_CASES = [
    ("甘孜稻城亚丁风景区", "**稻**丁***"),
    ("柳州螺蛳粉小镇", "*州**粉**"),
    ("泉州蟳埔村", "泉***村"),
    ("乌兰察布火山地质公园", "**察**山****"),
    ("长沙橘子洲头", "*沙**洲*"),
]


class TestBlindMasker(unittest.TestCase):
    def test_seed_blind_names_valid(self):
        for full, blind in SEED_CASES:
            ok, errs = validate_blind_name(full, blind)
            self.assertTrue(ok, f"{full} -> {blind}: {errs}")

    def test_mask_preserves_length_and_two_hanzi(self):
        for full in ["甘孜稻城亚丁风景区", "泉州蟳埔村", "乌兰察布火山地质公园"]:
            blind = mask_full_name(full)
            ok, errs = validate_blind_name(full, blind)
            self.assertTrue(ok, errs)
            self.assertEqual(len(blind), len(full))

    def test_mask_with_explicit_indices(self):
        self.assertEqual(
            mask_full_name("甘孜稻城亚丁风景区", keep_indices=[2, 5]), "**稻**丁***"
        )
        self.assertEqual(mask_full_name("泉州蟳埔村", keep_indices=[0, 4]), "泉***村")

    def test_validate_rejects_bad(self):
        # 保留 6 个汉字
        ok, _ = validate_blind_name("长沙橘子洲头", "长沙橘子洲头")
        self.assertFalse(ok)
        # 长度不一致
        ok, _ = validate_blind_name("长沙橘子洲头", "*沙*")
        self.assertFalse(ok)
        # 保留字与原文不符
        ok, _ = validate_blind_name("长沙橘子洲头", "泉***村")
        self.assertFalse(ok)

    def test_contains_full_name(self):
        self.assertTrue(contains_full_name("去甘孜稻城亚丁风景区玩", "甘孜稻城亚丁风景区"))
        self.assertFalse(contains_full_name("去这座秘境玩", "甘孜稻城亚丁风景区"))

    def test_sanitize_replaces_full_name(self):
        text = "这里是甘孜稻城亚丁风景区，欢迎你来。"
        cleaned = sanitize_text(text, ["甘孜稻城亚丁风景区"])
        self.assertNotIn("甘孜稻城亚丁风景区", cleaned)
        self.assertIn("这座秘境", cleaned)


if __name__ == "__main__":
    unittest.main()
