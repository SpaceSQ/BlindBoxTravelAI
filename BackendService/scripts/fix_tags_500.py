#!/usr/bin/env python3
"""一次性数据迁移：将 data/tags_500.json 修正为真正的 500 个去重标签。

背景（Milestone 1 数据校验发现）：
- 原文件声明 total_count=500，实际仅 475 个（去重后 471，含 4 个跨类重复）；
- 有 11 个已被 spots_seed.json 使用的景点标签不在词汇库中。

本脚本执行（幂等、可复现）：
1. 去除 4 个跨类重复标签（保留语义更贴近的类）：
    赶海/溯溪 → experience_gameplay，探险 → experience_gameplay，穷游 → scale_audience；
2. 补入 11 个已在种子景点中使用的标签；
3. 补入 18 个通用旅游标签，使去重总数精确达到 500；
4. 重算各维度 count 与 total_count。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TAGS_PATH = REPO_ROOT / "data" / "tags_500.json"

# 跨类重复：{类别: [需从该类移除的标签]}
REMOVE = {
    "weather_environment": ["赶海", "溯溪"],
    "emotion_mood": ["探险"],
    "experience_gameplay": ["穷游"],
}

# 补入标签：{类别: [标签...]}（11 个景点在用标签 + 18 个通用标签）
ADD = {
    "emotion_mood": ["眼睛在天堂", "蓝色星球", "异星感", "荒凉"],
    "weather_environment": ["缺氧", "梅雨季", "回南天"],
    "terrain_landscape": ["海蚀崖", "沙丘", "风蚀地貌", "红土地"],
    "food_taste": ["臭味相投", "火锅", "肠粉", "糖水", "生腌", "锅包肉"],
    "culture_history": ["簪花围", "渔村", "伟人足迹", "蚵壳厝", "傩戏"],
    "experience_gameplay": ["宇航员", "散步", "城市漫步", "夜爬"],
    "scale_audience": ["反向旅游", "错峰游", "慢旅行"],
}


def main() -> int:
    data = json.loads(TAGS_PATH.read_text(encoding="utf-8"))
    known_categories = {c["category_id"] for c in data["categories"]}

    for cat_id, tags in REMOVE.items():
        if cat_id not in known_categories:
            print(f"[skip] 未知类别 {cat_id}")
            continue
        print(f"[dedupe] {cat_id} 移除重复: {tags}")

    for category in data["categories"]:
        cid = category["category_id"]
        # 1) 去重（保持顺序，移除 REMOVE 指定标签）
        original = category["tags"]
        remove = set(REMOVE.get(cid, []))
        deduped: list = []
        seen = set()
        for t in original:
            if t in remove:
                continue
            if t in seen:
                continue
            deduped.append(t)
            seen.add(t)
        category["tags"] = deduped

        # 2) 补入 ADD 标签（去重追加）
        added = []
        for t in ADD.get(cid, []):
            if t not in seen:
                category["tags"].append(t)
                seen.add(t)
                added.append(t)
        if added:
            print(f"[add] {cid} +{len(added)}: {added}")

        # 3) 重算 count
        category["count"] = len(category["tags"])

    # 4) 重算 total_count
    total = sum(len(c["tags"]) for c in data["categories"])
    data["total_count"] = total

    TAGS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n[done] total_count={total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
