#!/usr/bin/env python3
"""数据底座校验 CLI（对应 check-blindbox 技能）。

校验 data/ 下种子数据的完整性并输出报告：
- tags_500.json：总数=500、去重、各维度 count 与实一致；
- spots_seed.json：blind_name 规范、无 full_name 泄露、标签类型合法；
- routes_seed.json：spot 引用有效、天数/类型规则、日程条数一致；
- evolution_metrics.json：覆盖全部 ID、严格无溯源结构。

退出码：0 = 全部通过；1 = 存在校验失败项。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.blind_masker import contains_full_name, validate_blind_name  # noqa: E402
from core.loaders import (  # noqa: E402
    load_evolution_metrics,
    load_json,
    load_routes,
    load_spots,
    load_tags_vocabulary,
)


def main() -> int:
    failures: list = []
    ok: list = []

    def check(cond: bool, label: str):
        (ok if cond else failures).append(label)

    tags_doc = load_json("tags_500.json")
    vocab = load_tags_vocabulary()
    spots = load_spots()
    routes = load_routes()
    metrics = load_evolution_metrics()

    # 标签
    check(tags_doc["total_count"] == 500, "标签总数 == 500")
    check(len(vocab) == 500, "标签扁平化 == 500")
    check(len(set(vocab)) == 500, "标签无重复")
    for c in tags_doc["categories"]:
        check(len(c["tags"]) == c["count"], f"维度 {c['category_id']} count 一致")

    # 景点
    for s in spots:
        okk, errs = validate_blind_name(s["full_name"], s["blind_name"])
        check(okk, f"{s['spot_id']} blind_name 合规 {errs if errs else ''}")
        check(not contains_full_name(s["description"], s["full_name"]),
              f"{s['spot_id']} description 无全称泄露")
        check(not contains_full_name(s["summary_100w"], s["full_name"]),
              f"{s['spot_id']} summary 无全称泄露")
        check(all(t["type"] in ("strong", "weak") for t in s["tags"]),
              f"{s['spot_id']} 标签类型合法")
        check(all(t["name"] in vocab for t in s["tags"]),
              f"{s['spot_id']} 标签均在 500 词汇库中")

    # 路线
    spot_ids = {s["spot_id"] for s in spots}
    for r in routes:
        check(r["route_type"] in ("single_spot", "multi_spot"), f"{r['route_id']} 类型合法")
        check(1 <= r["duration_days"] <= 7, f"{r['route_id']} 天数在 1~7")
        check(all(sid in spot_ids for sid in r["spot_ids"]), f"{r['route_id']} 景点引用有效")
        check(len(r["daily_schedule"]) == r["duration_days"], f"{r['route_id']} 日程条数一致")

    # 进化变量
    check(set(metrics["spots_metrics"].keys()) == spot_ids, "spots_metrics 覆盖全部景点")
    check(set(metrics["routes_metrics"].keys()) == {r["route_id"] for r in routes},
          "routes_metrics 覆盖全部路线")

    print(f"校验通过 {len(ok)} 项")
    if failures:
        print(f"\n校验失败 {len(failures)} 项：")
        for f in failures:
            print(f"  ✗ {f}")
        return 1
    print("  ✓ 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
