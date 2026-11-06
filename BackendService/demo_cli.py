#!/usr/bin/env python3
"""端到端演示：对话收敛 → 推荐 → 盲盒脱敏 → 明文解锁。

仅依赖标准库，可直接运行：
    python3 BackendService/demo_cli.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.dialogue import DialogueStateMachine  # noqa: E402
from core.loaders import load_routes, load_spots, load_tags_vocabulary  # noqa: E402
from core.recommendation import recommend  # noqa: E402


def main() -> None:
    vocab = load_tags_vocabulary()
    spots = {s["spot_id"]: s for s in load_spots()}
    routes = load_routes()

    origin = {"lat": 22.5431, "lng": 114.0579}  # 深圳

    sm = DialogueStateMachine(vocab)
    print("🎁 盲盒旅行AI 对话引擎演示（出发地：深圳）\n")

    for text in ["想吃辣，去嗦粉，玩两天"]:
        result = sm.process(text)
        print(f"👤 用户：{text}")
        print(f"🤖 引擎：{result.message}  (轮次 {result.turn_count}, kind={result.kind})\n")

    intent = sm.intent
    recs = recommend(
        routes, spots, origin,
        matched_tags=intent.matched_tags,
        duration_days=intent.duration_days,
        max_distance_km=intent.max_distance_km,
        apply_random=False,
    )

    print("── 盲盒态（脱敏）推荐卡片 ──")
    for i, r in enumerate(recs, start=1):
        tag = "⭐ 重点推荐" if r["is_featured"] else f"  推荐 {i}"
        print(f"[{tag}] {r['blind_route_title']}  ·  {r['duration_days']}天 · 🎫 选定行程后揭晓")

    print("\n── 选定第 1 条 → 生成计划行程单 → 明文解锁 ──")
    first = recs[0]
    print(f"路线名：{first['full_route_title']}")
    for sid in first["spot_ids"]:
        s = spots[sid]
        print(f"  · {s['full_name']}（门票 ¥{s['adult_ticket_price']}）")


if __name__ == "__main__":
    main()
