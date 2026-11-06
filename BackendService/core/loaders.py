"""数据加载器：读取 data/ 目录下的种子数据并构建内存索引。

仓库结构约定（交底书 §一）：
    <repo_root>/data/{tags_500,spots_seed,routes_seed,evolution_metrics}.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def find_repo_root() -> Path:
    """向上查找包含 data/tags_500.json 的目录，作为仓库根目录。"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "data" / "tags_500.json").exists():
            return parent
    raise FileNotFoundError("无法定位仓库根目录（未找到 data/tags_500.json）")


REPO_ROOT = find_repo_root()
DATA_DIR = REPO_ROOT / "data"


def load_json(name: str) -> Any:
    """读取 data/ 目录下的 JSON 文件。"""
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def load_tags_vocabulary() -> List[str]:
    """将 tags_500.json 扁平化为 500 个标签字符串列表（供意图提取使用）。"""
    data = load_json("tags_500.json")
    tags: List[str] = []
    for category in data.get("categories", []):
        tags.extend(category.get("tags", []))
    return tags


def load_spots() -> List[Dict[str, Any]]:
    return load_json("spots_seed.json")


def load_routes() -> List[Dict[str, Any]]:
    return load_json("routes_seed.json")


def load_evolution_metrics() -> Dict[str, Any]:
    return load_json("evolution_metrics.json")


def spots_by_id() -> Dict[str, Dict[str, Any]]:
    """返回 {spot_id: spot} 索引。"""
    return {s["spot_id"]: s for s in load_spots()}


def routes_by_id() -> Dict[str, Dict[str, Any]]:
    """返回 {route_id: route} 索引。"""
    return {r["route_id"]: r for r in load_routes()}
