"""对话状态机：≥2 汉字触发、1~4 轮强制收敛（交底书 §3.1 / PRD §2.1）。

核心约束：
- 输入包含 ≥2 个汉字才进入对话轮次，否则轻量提示；
- turn_count == 1 且（用户直接表达“随便/直接推荐” 或 SpecificityScore ≥ 0.75）→ 立即生成；
- 1 ≤ turn_count < 4 且 SpecificityScore < 0.75 → 生成 1 句追问 + 3~4 个快捷胶囊选项；
- turn_count == 4 → 硬性红线：禁止追问，强制生成 3 条盲盒订单。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

HANZI_RE = re.compile(r"[一-龥]")
MIN_HANZI = 2
SPECIFICITY_THRESHOLD = 0.75

# 快捷追问胶囊选项
QUICK_OPTIONS = {
    "duration": ["1天", "2天", "3天", "4天及以上"],
    "distance": ["500km内", "1000km内", "3000km内", "多远都行"],
    "companion": ["独自", "情侣", "闺蜜", "亲子"],
}

_CASUAL_TERMS = [
    "随便", "随缘", "直接推荐", "直接给我", "直接来", "推荐一个",
    "看着来", "周末去玩", "随便去玩", "随便推荐", "都行", "都可以",
]
_COMPANION_TERMS = [
    "亲子", "带娃", "情侣", "闺蜜", "兄弟", "姐妹", "独自", "一个人",
    "全家", "毕业旅行", "蜜月", "团建", "银发", "独行", "全家出游",
]

# 中文数字 → 天数
_CHINESE_NUM = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "半": 1}
_DURATION_RE = re.compile(r"(\d|[一二两三四五六七半])\s*[天日]")
_DISTANCE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:公里|km|千米)", re.IGNORECASE)


@dataclass
class Intent:
    """从自然语言中提取出的意图槽位。"""
    matched_tags: List[str] = field(default_factory=list)
    duration_days: Optional[int] = None
    max_distance_km: Optional[int] = None
    companion: Optional[str] = None
    casual: bool = False


@dataclass
class TurnResult:
    """状态机单轮处理结果。"""
    kind: str  # 'reject' | 'generate' | 'follow_up'
    message: str
    quick_options: List[str] = field(default_factory=list)
    forced: bool = False
    intent: Optional[Intent] = None
    turn_count: int = 0


def hanzi_count(text: str) -> int:
    return len(HANZI_RE.findall(text))


def extract_intent(text: str, vocab_tags: List[str]) -> Intent:
    """规则/词汇库驱动的意图槽位提取（M1 阶段用关键词匹配替代本地大模型）。"""
    intent = Intent()

    # 1. 标签映射：长标签优先，避免子串误匹配
    for tag in sorted(vocab_tags, key=len, reverse=True):
        if tag in text:
            intent.matched_tags.append(tag)

    # 2. “随便/直接推荐”等宽松信号
    for term in _CASUAL_TERMS:
        if term in text:
            intent.casual = True
            break

    # 3. 出行天数（1~7 天）
    m = _DURATION_RE.search(text)
    if m:
        tok = m.group(1)
        if tok.isdigit():
            days = int(tok)
        else:
            days = _CHINESE_NUM.get(tok)
        if days:
            intent.duration_days = max(1, min(7, days))

    # 4. 距离阈值（公里）
    m = _DISTANCE_RE.search(text)
    if m:
        intent.max_distance_km = int(float(m.group(1)))

    # 5. 同行人群
    for term in _COMPANION_TERMS:
        if term in text:
            intent.companion = term
            break

    return intent


def specificity_score(intent: Intent) -> float:
    """意图明确度（0.0 ~ 1.0）。"""
    s = 0.0
    ntags = len(set(intent.matched_tags))
    if ntags >= 1:
        s += 0.3
    if ntags >= 2:
        s += 0.2
    if intent.duration_days is not None:
        s += 0.25
    if intent.max_distance_km is not None:
        s += 0.25
    if intent.companion is not None:
        s += 0.15
    return min(1.0, s)


class DialogueStateMachine:
    """维护对话轮次并强制 1~4 轮收敛。"""

    def __init__(self, vocab_tags: List[str]):
        self.vocab_tags = vocab_tags
        self.turn_count = 0
        self.intent = Intent()

    def reset(self) -> None:
        self.turn_count = 0
        self.intent = Intent()

    def _merge(self, new: Intent) -> None:
        """跨轮合并意图：标签取并集，槽位仅在为空时填充。"""
        self.intent.casual = self.intent.casual or new.casual
        for t in new.matched_tags:
            if t not in self.intent.matched_tags:
                self.intent.matched_tags.append(t)
        if self.intent.duration_days is None:
            self.intent.duration_days = new.duration_days
        if self.intent.max_distance_km is None:
            self.intent.max_distance_km = new.max_distance_km
        if self.intent.companion is None:
            self.intent.companion = new.companion

    def _next_question(self) -> str:
        """按缺失优先级返回一句神秘感追问。"""
        if self.intent.duration_days is None:
            return "这趟盲盒想拆几天呀？（1~7 天都可以哦）"
        if self.intent.max_distance_km is None:
            return "想走多远去拆这份惊喜呢？"
        return "这次和谁一起出发呀？"

    def _next_options(self) -> List[str]:
        if self.intent.duration_days is None:
            return QUICK_OPTIONS["duration"]
        if self.intent.max_distance_km is None:
            return QUICK_OPTIONS["distance"]
        return QUICK_OPTIONS["companion"]

    def process(self, text: str) -> TurnResult:
        """处理一轮用户输入。"""
        if hanzi_count(text) < MIN_HANZI:
            return TurnResult(
                kind="reject",
                message="再多说两个字，让我捕捉你的旅行灵感~",
                turn_count=self.turn_count,
            )

        self.turn_count += 1
        self._merge(extract_intent(text, self.vocab_tags))

        # 第 1 轮：宽松信号或足够明确 → 直接出盒
        if self.turn_count == 1 and (self.intent.casual or specificity_score(self.intent) >= SPECIFICITY_THRESHOLD):
            return TurnResult(
                kind="generate",
                message="捕捉到你的旅行灵感了，这就为你拆出 3 份盲盒行程~",
                intent=self.intent,
                turn_count=self.turn_count,
            )

        # 硬性红线：第 4 轮强制收敛
        if self.turn_count >= 4:
            return TurnResult(
                kind="generate",
                forced=True,
                message="好的，就按现在这份心情，为你揭晓 3 份盲盒行程~",
                intent=self.intent,
                turn_count=self.turn_count,
            )

        return TurnResult(
            kind="follow_up",
            message=self._next_question(),
            quick_options=self._next_options(),
            intent=self.intent,
            turn_count=self.turn_count,
        )
