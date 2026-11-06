"""GitHub 进化变量同步（Python 版，供后端/离线脚本批量合并推送使用）。

对应交底书 §3.6：将匿名增量（plan_mark_count / review_count）原子化合并进
`data/evolution_metrics.json` 并推送至 GitHub 仓库。

严格零溯源：本模块不读取、不写入任何用户身份字段。

用法：
    python3 -m core.evolution_sync \
        --repo SpaceSQ/BlindBoxTravelAI \
        --path data/evolution_metrics.json \
        --deltas '{"spot": {"SP001": [1, 0]}}' \
        --token "$GITHUB_TOKEN"
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

API = "https://api.github.com"

# 增量格式：{ "spot"|"route": { "<id>": [plan_increment, review_increment] } }
Deltas = Dict[str, Dict[str, List[int]]]


def _metrics_path(repo: str, path: str) -> str:
    return f"/repos/{repo}/contents/{path}"


def _auth_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _http(method: str, url: str, token: str, body: Any = None) -> Tuple[int, Any]:
    import urllib.request

    req = urllib.request.Request(url, method=method, headers=_auth_headers(token))
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def fetch_state(repo: str, path: str, token: str) -> Tuple[str, Dict[str, Any]]:
    """GET 远端文件，返回 (sha, metrics)。"""
    status, payload = _http("GET", API + _metrics_path(repo, path), token)
    if status != 200:
        raise RuntimeError(f"GET failed: {status} {payload}")
    sha = payload["sha"]
    content = base64.b64decode(payload["content"].replace("\n", "")).decode("utf-8")
    return sha, json.loads(content)


def apply_deltas(metrics: Dict[str, Any], deltas: Deltas) -> Dict[str, Any]:
    """将增量合并进 metrics（就地修改并返回）。"""
    for scope, entries in deltas.items():
        bucket = metrics.get(f"{scope}s_metrics", {})  # spot -> spots_metrics
        for key, (plan_inc, review_inc) in entries.items():
            stats = bucket.setdefault(key, {"plan_mark_count": 0, "review_count": 0})
            stats["plan_mark_count"] += plan_inc
            stats["review_count"] += review_inc
        metrics[f"{scope}s_metrics"] = bucket
    metrics["last_updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return metrics


def push_state(repo: str, path: str, token: str, sha: str, metrics: Dict[str, Any], branch: str = "main") -> str:
    """PUT 覆盖远端文件，返回新 sha。"""
    content = base64.b64encode(json.dumps(metrics, ensure_ascii=False).encode("utf-8")).decode("ascii")
    body = {
        "message": "chore(evolution): anonymous metric increment",
        "content": content,
        "sha": sha,
        "branch": branch,
    }
    status, payload = _http("PUT", API + _metrics_path(repo, path), token, body)
    if status not in (200, 201):
        raise RuntimeError(f"PUT failed: {status} {payload}")
    return payload["content"]["sha"]


def sync(repo: str, path: str, token: str, deltas: Deltas, branch: str = "main") -> str:
    """原子同步：GET → 合并 → PUT。返回提交后新 sha。"""
    sha, metrics = fetch_state(repo, path, token)
    merged = apply_deltas(metrics, deltas)
    return push_state(repo, path, token, sha, merged, branch)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="盲盒旅行AI 进化变量 GitHub 同步")
    parser.add_argument("--repo", default="SpaceSQ/BlindBoxTravelAI")
    parser.add_argument("--path", default="data/evolution_metrics.json")
    parser.add_argument("--deltas", required=True, help='JSON 增量，如 \'{"spot": {"SP001": [1, 0]}}\'')
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--branch", default="main")
    args = parser.parse_args(argv)

    if not args.token:
        print("错误：未配置 GITHUB_TOKEN。请设置环境变量或 --token。", file=sys.stderr)
        return 1

    deltas = json.loads(args.deltas)
    try:
        new_sha = sync(args.repo, args.path, args.token, deltas, args.branch)
        print(f"同步成功，新 sha={new_sha}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"同步失败：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
