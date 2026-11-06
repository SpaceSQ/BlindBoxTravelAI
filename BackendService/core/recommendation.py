"""推荐引擎：距离筛选 + 综合打分 + 动态随机 + 前 3 条（首条重点推荐）。

流程（PRD §2.1 Step 1~4）：
1. 距离筛选：多景点路线以首站景点距离满足用户所选阈值为准（交底书 §3.2.3）；
2. 综合打分 = w_tag·TagMatch + w_season·SeasonFit + w_pop·Popularity + 天数软加分；
3. 叠加与具体度成反比的随机扰动 ε_random；
4. 取前 3 条，第 1 条 is_featured=true；若距离内候选不足 3 条，自动放宽距离补齐。
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional

from core import tag_matcher as tm
from core.haversine import haversine_distance

W_TAG = 1.0
W_SEASON = 0.6
W_POP = 0.4
W_DURATION = 0.3

DEFAULT_MAX_DISTANCE_KM = 6000
DISTANCE_OPTIONS_KM = [500, 1000, 2000, 3000, 4000, 5000, 6000]


def first_stop_distance(route: dict, spots_by_id: Dict[str, dict], origin: dict) -> float:
    """路线首站景点到出发地的距离（公里）。"""
    first = spots_by_id[route["spot_ids"][0]]
    return haversine_distance(
        origin["lat"], origin["lng"],
        first["location"]["lat"], first["location"]["lng"],
    )


def filter_by_distance(
    routes: List[dict],
    spots_by_id: Dict[str, dict],
    origin: dict,
    max_km: float,
) -> List[dict]:
    """返回首站距离 ≤ max_km 的路线（保持原顺序）。"""
    return [
        r for r in routes
        if first_stop_distance(r, spots_by_id, origin) <= max_km
    ]


def base_score(
    route: dict,
    spots_by_id: Dict[str, dict],
    matched_tags: List[str],
    month: int,
    duration_days: Optional[int],
) -> float:
    """确定性综合打分（不含随机扰动）。"""
    tag_match = tm.compute_tag_match(route, spots_by_id, matched_tags)
    season_fit = tm.compute_season_fit(route, spots_by_id, month)
    popularity = tm.compute_popularity(route.get("evolution_stats", {}))

    duration_bonus = 0.0
    if duration_days is not None:
        diff = abs(route.get("duration_days", 0) - duration_days)
        duration_bonus = max(0.0, 1.0 - 0.5 * diff)

    return (
        W_TAG * tag_match
        + W_SEASON * season_fit
        + W_POP * popularity
        + W_DURATION * duration_bonus
    )


def recommend(
    routes: List[dict],
    spots_by_id: Dict[str, dict],
    origin: dict,
    matched_tags: Optional[List[str]] = None,
    max_distance_km: Optional[int] = None,
    duration_days: Optional[int] = None,
    month: Optional[int] = None,
    specificity: float = 0.5,
    rng: Optional[random.Random] = None,
    apply_random: bool = True,
) -> List[dict]:
    """生成最多 3 条推荐（首条 is_featured），距离内候选不足时放宽距离补齐。

    apply_random=False 时关闭随机扰动，便于确定性测试。
    """
    matched_tags = matched_tags or []
    rng = rng or random.Random()
    month = month or 6
    max_dist = max_distance_km if max_distance_km is not None else DEFAULT_MAX_DISTANCE_KM

    in_range: List[dict] = []
    out_of_range: List[dict] = []
    for route in routes:
        if first_stop_distance(route, spots_by_id, origin) <= max_dist:
            in_range.append(route)
        else:
            out_of_range.append(route)

    def scored(items: List[dict]) -> List[tuple]:
        rows = []
        for route in items:
            base = base_score(route, spots_by_id, matched_tags, month, duration_days)
            eps = 0.0
            if apply_random:
                eps = tm.temperature_for_specificity(specificity) * rng.uniform(-1.0, 1.0)
            rows.append((base + eps, route))
        rows.sort(key=lambda x: x[0], reverse=True)
        return rows

    top: List[dict] = [route for _, route in scored(in_range)[:3]]

    if len(top) < 3:
        for _, route in scored(out_of_range):
            if len(top) >= 3:
                break
            top.append(route)

    result: List[dict] = []
    for i, route in enumerate(top):
        r = dict(route)
        r["is_featured"] = (i == 0)
        result.append(r)
    return result
