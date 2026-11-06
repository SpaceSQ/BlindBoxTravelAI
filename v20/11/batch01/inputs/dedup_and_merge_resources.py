#!/usr/bin/env python3
"""
盲盒旅行AI (BlindBoxTravelAI) - 两级旅游资源库（市级 cities.json + 县级 areas.json）排除重复与合并总装引擎
用法:
  python3 scripts/dedup_and_merge_resources.py \
      --cities-file data/市级_cities.json \
      --areas-file data/县级_areas.json \
      --output-spots data/national_spots_master.json \
      --output-routes data/national_routes_master.json
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

GENERIC_SUFFIXES = [
    "国家级旅游度假区", "国家风景名胜区", "风景名胜区", "国家森林公园", "国家地质公园",
    "国家湿地公园", "森林公园", "湿地公园", "地质公园", "考古遗址公园", "遗址公园",
    "文化旅游区", "生态旅游区", "旅游度假区", "旅游景区", "风景区", "景区", "景点", "公园"
]

ROUTE_KEYWORDS = {"观光路线", "自驾路线", "徒步路线", "穿越路线", "探险路线"}


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lng / 2) ** 2)
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def normalize_stem(name: str, city_name: str = "", area_name: str = "") -> str:
    s = re.sub(r"\s+", "", name or "")
    for prefix in (city_name, area_name, city_name.rstrip("市州盟地区"), area_name.rstrip("县区市旗")):
        if prefix and len(prefix) >= 2 and s.startswith(prefix) and len(s) > len(prefix) + 1:
            s = s[len(prefix):]
    for suffix in GENERIC_SUFFIXES:
        if s.endswith(suffix) and len(s) > len(suffix) + 1:
            s = s[:-len(suffix)]
            break
    return s


def generate_blind_name(full_name: str) -> str:
    """严格保留2个汉字，其余字符一对一替换为*，保持长度完全一致。"""
    chars = list(full_name)
    n = len(chars)
    if n <= 2:
        return chars[0] + ("*" * (n - 1)) if n == 2 else "*"
    # 使用确定性哈希挑选2个非相邻或具代表性的位置保留
    digest = hashlib.md5(full_name.encode("utf-8")).digest()
    idx1 = digest[0] % max(1, n // 2)
    idx2 = (n // 2) + (digest[1] % (n - n // 2))
    if idx2 == idx1:
        idx2 = (idx1 + 1) % n
    keep = {idx1, idx2}
    return "".join(ch if i in keep else "*" for i, ch in enumerate(chars))


def sanitize_blind_text(text: str, full_name: str, stem: str) -> str:
    if not text:
        return ""
    res = text.replace(full_name, "这处秘境目的地")
    if stem and len(stem) >= 2:
        res = res.replace(stem, "该核心景区")
    return res


def merge_two_records(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    """合并市级与县级命中同一实体的记录，属性互补。"""
    merged = dict(primary)
    # 行政区划取最细粒度（优先保留县级 area_code / area_name / township_name）
    for k in ("area_code", "area_name", "township_name"):
        if not merged.get(k) and secondary.get(k):
            merged[k] = secondary[k]

    # 合并搜索关键词来源与搜索层级
    kw1 = set(merged.get("matched_search_keywords", [merged.get("matched_search_keyword")] if merged.get("matched_search_keyword") else []))
    kw2 = set(secondary.get("matched_search_keywords", [secondary.get("matched_search_keyword")] if secondary.get("matched_search_keyword") else []))
    merged["matched_search_keywords"] = sorted(x for x in (kw1 | kw2) if x)

    tiers = set(merged.get("search_tiers", [merged.get("search_tier")] if merged.get("search_tier") else []))
    tiers |= set(secondary.get("search_tiers", [secondary.get("search_tier")] if secondary.get("search_tier") else []))
    merged["search_tiers"] = sorted(x for x in tiers if x)

    # 合并 500 核心旅游标签（保持 strong 在前，weak 在后，去重）
    tag_map: Dict[str, str] = {}
    for t in (merged.get("tags") or []) + (secondary.get("tags") or []):
        t_name = t.get("name")
        t_type = t.get("type", "weak")
        if not t_name:
            continue
        if t_name not in tag_map or t_type == "strong":
            tag_map[t_name] = t_type
    strong_tags = [{"name": k, "type": "strong"} for k, v in tag_map.items() if v == "strong"]
    weak_tags = [{"name": k, "type": "weak"} for k, v in tag_map.items() if v != "strong"]
    merged["tags"] = strong_tags[:4] + weak_tags[:6]

    # 择优补齐坐标、门票、图片、简介与攻略
    if (not merged.get("location") or not merged["location"].get("lat")) and secondary.get("location"):
        merged["location"] = secondary["location"]
    for field in ("adult_ticket_price", "image_url", "source_url", "events_and_discounts", "ai_strategy", "tag_interpretation"):
        if merged.get(field) is None and secondary.get(field) is not None:
            merged[field] = secondary[field]
    if len(secondary.get("description") or "") > len(merged.get("description") or ""):
        merged["description"] = secondary["description"]
    if len(secondary.get("summary_100w") or "") > len(merged.get("summary_100w") or ""):
        merged["summary_100w"] = secondary["summary_100w"]

    return merged


def deduplicate_and_merge(city_records: List[Dict[str, Any]], area_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    spot_index: Dict[str, Dict[str, Any]] = {}
    route_index: Dict[str, Dict[str, Any]] = {}
    duplicate_count = 0

    all_incoming = [
        ({**r, "search_tier": r.get("search_tier", "city_level")}) for r in city_records
    ] + [
        ({**r, "search_tier": r.get("search_tier", "county_level")}) for r in area_records
    ]

    for rec in all_incoming:
        full_name = (rec.get("full_name") or "").strip()
        if len(full_name) < 2:
            continue
        city_code = str(rec.get("city_code") or rec.get("cityCode") or "")[:4]
        city_name = rec.get("city_name") or ""
        area_name = rec.get("area_name") or ""
        stem = normalize_stem(full_name, city_name, area_name)
        dedup_key = f"{city_code}::{stem}"

        kw = rec.get("matched_search_keyword") or ""
        is_route = rec.get("entity_type") == "route" or kw in ROUTE_KEYWORDS or full_name.endswith(("路线", "游线", "环线", "穿越线", "徒步线"))

        target_pool = route_index if is_route else spot_index
        if dedup_key in target_pool:
            target_pool[dedup_key] = merge_two_records(target_pool[dedup_key], rec)
            duplicate_count += 1
        else:
            # 进一步检查同城球面距离 < 150m 的近邻同名景点
            matched_geo_key = None
            loc = rec.get("location") or {}
            if not is_route and loc.get("lat") and loc.get("lng"):
                for k, existing in target_pool.items():
                    if not k.startswith(f"{city_code}::"):
                        continue
                    eloc = existing.get("location") or {}
                    if eloc.get("lat") and eloc.get("lng"):
                        dist = haversine_km(float(loc["lat"]), float(loc["lng"]), float(eloc["lat"]), float(eloc["lng"]))
                        if dist < 0.15 and (stem in existing["full_name"] or existing["full_name"] in full_name):
                            matched_geo_key = k
                            break
            if matched_geo_key:
                target_pool[matched_geo_key] = merge_two_records(target_pool[matched_geo_key], rec)
                duplicate_count += 1
            else:
                rec["blind_name"] = generate_blind_name(full_name)
                rec["description"] = sanitize_blind_text(rec.get("description", ""), full_name, stem)
                rec["summary_100w"] = sanitize_blind_text(rec.get("summary_100w", ""), full_name, stem)
                rec["evolution_stats"] = {"plan_mark_count": 0, "review_count": 0}
                target_pool[dedup_key] = rec

    final_spots = []
    for idx, (_, sp) in enumerate(sorted(spot_index.items()), start=1):
        sp["spot_id"] = sp.get("spot_id") or f"SP{idx:07d}"
        final_spots.append(sp)

    final_routes = []
    for idx, (_, rt) in enumerate(sorted(route_index.items()), start=1):
        rt["route_id"] = rt.get("route_id") or f"RT{idx:07d}"
        final_routes.append(rt)

    stats = {
        "input_city_records": len(city_records),
        "input_area_records": len(area_records),
        "total_input_records": len(all_incoming),
        "duplicates_merged": duplicate_count,
        "final_unique_spots": len(final_spots),
        "final_unique_routes": len(final_routes)
    }
    return final_spots, final_routes, stats


def main():
    parser = argparse.ArgumentParser(description="Deduplicate and merge city-level and county-level travel resource libraries.")
    parser.add_argument("--cities-file", default="data/市级_cities.json", help="Path to city-level resource JSON")
    parser.add_argument("--areas-file", default="data/县级_areas.json", help="Path to county-level resource JSON")
    parser.add_argument("--output-spots", default="data/national_spots_master.json", help="Output merged spots JSON")
    parser.add_argument("--output-routes", default="data/national_routes_master.json", help="Output merged routes JSON")
    args = parser.parse_args()

    cities_path = Path(args.cities_file)
    areas_path = Path(args.areas_file)

    city_records = json.loads(cities_path.read_text(encoding="utf-8")) if cities_path.exists() else []
    area_records = json.loads(areas_path.read_text(encoding="utf-8")) if areas_path.exists() else []

    spots, routes, stats = deduplicate_and_merge(city_records, area_records)

    Path(args.output_spots).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_spots).write_text(json.dumps(spots, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.output_routes).write_text(json.dumps(routes, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
