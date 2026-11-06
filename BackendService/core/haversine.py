"""Haversine 球面距离计算（交底书 §3.2）。

用于距离筛选器：计算用户当前/出发地坐标与景点坐标之间的大圆距离（公里），
支撑 500km ~ 6000km 的距离下拉筛选。
"""
from __future__ import annotations

import math
from typing import Mapping

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """返回两点间的球面距离（公里）。

    输入均为角度制（度）。公式：
        d = 2R · atan2(√a, √(1-a))
        a = sin²(Δlat/2) + cos(lat1)·cos(lat2)·sin²(Δlng/2)
    """
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    r_lat1 = math.radians(lat1)
    r_lat2 = math.radians(lat2)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(r_lat1) * math.cos(r_lat2) * math.sin(d_lng / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_KM * c


def distance_km_between(p1: Mapping[str, float], p2: Mapping[str, float]) -> float:
    """从 {lat, lng} 映射计算两点距离。"""
    return haversine_distance(p1["lat"], p1["lng"], p2["lat"], p2["lng"])
