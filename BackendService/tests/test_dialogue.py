import unittest

from core.dialogue import DialogueStateMachine, extract_intent, hanzi_count, specificity_score

VOCAB = ["雪山", "滑雪", "重装徒步", "嗦粉", "辣", "治愈", "亲子", "情侣", "独自旅行", "赶海", "看海"]


class TestDialogue(unittest.TestCase):
    def test_hanzi_count(self):
        self.assertEqual(hanzi_count("看海"), 2)
        self.assertEqual(hanzi_count("啊"), 1)
        self.assertEqual(hanzi_count("Go!"), 0)

    def test_reject_under_two_hanzi(self):
        sm = DialogueStateMachine(VOCAB)
        r = sm.process("啊")
        self.assertEqual(r.kind, "reject")
        self.assertEqual(sm.turn_count, 0)  # 不计入有效轮次

    def test_casual_generate_turn1(self):
        sm = DialogueStateMachine(VOCAB)
        r = sm.process("随便推荐一个")
        self.assertEqual(r.kind, "generate")
        self.assertEqual(r.turn_count, 1)

    def test_specific_generate_turn1(self):
        sm = DialogueStateMachine(VOCAB)
        r = sm.process("想看雪山，想滑雪，3天，500公里内")
        self.assertEqual(r.kind, "generate")
        self.assertEqual(r.turn_count, 1)

    def test_follow_up_then_forced_generate_turn4(self):
        sm = DialogueStateMachine(VOCAB)
        inputs = ["想出去玩", "开心一点的", "风景好的", "就这些吧"]
        for i, text in enumerate(inputs, start=1):
            r = sm.process(text)
            if i < 4:
                self.assertEqual(r.kind, "follow_up", f"turn {i}")
                self.assertTrue(r.quick_options, f"turn {i} 应提供快捷选项")
            else:
                self.assertEqual(r.kind, "generate", f"turn {i}")
                self.assertTrue(r.forced, "第 4 轮必须强制收敛")
                self.assertEqual(r.turn_count, 4)

    def test_extract_intent_slots(self):
        it = extract_intent("想和闺蜜去赶海看海，玩两天，1000公里内", VOCAB)
        self.assertIn("赶海", it.matched_tags)
        self.assertIn("看海", it.matched_tags)
        self.assertEqual(it.duration_days, 2)
        self.assertEqual(it.max_distance_km, 1000)
        self.assertEqual(it.companion, "闺蜜")
        self.assertGreaterEqual(specificity_score(it), 0.75)

    def test_specificity_low_for_vague(self):
        it = extract_intent("想出去玩", VOCAB)
        self.assertEqual(it.matched_tags, [])
        self.assertLess(specificity_score(it), 0.75)


if __name__ == "__main__":
    unittest.main()
