"""强弱标签匹配、进化变量加权、季节适配与动态随机温度（PRD §2.1 Step 3）。

综合评分公式：
    Score = w_tag · TagMatch(strong=3.0, weak=1.0)
          + w_season · SeasonFit
          + w_pop · log(1 + plan + 2·review)
          + ε_random

其中 ε_random 与用户输入具体度 (specificity) 成反比：输入越宽泛温度越高（≤0.85），
越具体温度越低（≥0.15）。
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, Sequence, Set

STRONG_WEIGHT = 3.0
WEAK_WEIGHT = 1.0

# 季节标签亲和表（轻量启发式，M1 阶段占位，后续可替换为真实气象数据）
_SEASON_TAGS: Dict[str, Set[str]] = {
    "春": {"踏青", "赏梅", "樱花季", "花海", "梯田放水"},
    "夏": {"避暑", "溯溪", "漂流", "戏水", "看海", "赶海", "溶洞避暑"},
    "秋": {"赏秋", "红叶", "银杏黄了", "观潮", "赏月"},
    "冬": {"看雪", "滑雪", "雾凇", "冰雕", "温泉", "暖冬", "避寒", "冰天雪地", "玩雪"},
}


def season_for_month(month: int) -> str:
    """将月份映射到季节（北半球）：3~5 春、6~8 夏、9~11 秋、12~2 冬。"""
    if 3 <= month <= 5:
        return "春"
    if 6 <= month <= 8:
        return "夏"
    if 9 <= month <= 11:
        return "秋"
    return "冬"


def tag_weight(tag_type: str) -> float:
    return STRONG_WEIGHT if tag_type == "strong" else WEAK_WEIGHT


def collect_route_tags(route: dict, spots_by_id: Dict[str, dict]) -> Dict[str, str]:
    """汇总路线所有景点的标签，返回 {标签名: 类型}；同名标签取更高级别（strong 优先）。"""
    tags: Dict[str, str] = {}
    for sid in route.get("spot_ids", []):
        spot = spots_by_id.get(sid)
        if not spot:
            continue
        for t in spot.get("tags", []):
            name = t.get("name")
            typ = t.get("type", "weak")
            if name is None:
                continue
            if name not in tags or typ == "strong":
                tags[name] = typ
    return tags


def compute_tag_match(route: dict, spots_by_id: Dict[str, dict], matched_tags: Iterable[str]) -> float:
    """计算路线与用户意图标签的重合度：strong=3.0、weak=1.0 的加权和。"""
    tags = collect_route_tags(route, spots_by_id)
    score = 0.0
    for mt in matched_tags:
        if mt in tags:
            score += tag_weight(tags[mt])
    return score


def compute_season_fit(route: dict, spots_by_id: Dict[str, dict], month: int) -> float:
    """季节适配度：命中本季标签 1.0、无季节标签 0.5、命中他季标签 0.2。"""
    season = season_for_month(month)
    tags = set(collect_route_tags(route, spots_by_id).keys())
    if tags & _SEASON_TAGS[season]:
        return 1.0
    all_season: Set[str] = set().union(*_SEASON_TAGS.values())
    if tags & all_season:
        return 0.2
    return 0.5


def compute_popularity(evolution_stats: dict) -> float:
    """进化变量热度：log(1 + plan + 2·review)。"""
    plan = evolution_stats.get("plan_mark_count", 0)
    review = evolution_stats.get("review_count", 0)
    return math.log1p(plan + 2 * review)


def temperature_for_specificity(specificity: float) -> float:
    """随机温度系数：specificity 0→0.85，1→0.15，线性插值。"""
    s = max(0.0, min(1.0, specificity))
    return 0.85 - 0.7 * s
