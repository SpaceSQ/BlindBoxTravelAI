"""盲盒旅行AI 辅助推理 API（FastAPI 骨架，Milestone 2 完善）。

端点规划：
- GET  /health            健康检查
- POST /chat/turn         单轮对话：{session_id, text} → 状态机结果 + 推荐（第 1/4 轮时）
- GET  /routes/masked     盲盒态路线列表（脱敏标题）
- POST /spots/validate    Grok Bot 采集数据的盲盒脱敏入库校验

依赖：fastapi、uvicorn、pydantic（见 requirements.txt）。
核心算法位于 core/，均不依赖 FastAPI，可独立单元测试。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.dialogue import DialogueStateMachine  # noqa: E402
from core.loaders import load_routes, load_spots, load_tags_vocabulary  # noqa: E402
from core.recommendation import recommend  # noqa: E402

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError:  # 未安装 FastAPI 时仅暴露算法层，不启动服务
    FastAPI = None  # type: ignore
    BaseModel = object  # type: ignore

_VOCAB = load_tags_vocabulary()
_SPOTS = {s["spot_id"]: s for s in load_spots()}
_ROUTES = load_routes()

# 内存会话（M2 替换为持久化/服务端会话存储）
_sessions: Dict[str, DialogueStateMachine] = {}


def get_session(session_id: str) -> DialogueStateMachine:
    if session_id not in _sessions:
        _sessions[session_id] = DialogueStateMachine(_VOCAB)
    return _sessions[session_id]


if FastAPI is not None:

    class ChatRequest(BaseModel):
        session_id: str
        text: str
        origin: Optional[Dict[str, float]] = None

    app = FastAPI(title="BlindBoxTravelAI API")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/chat/turn")
    def chat_turn(req: ChatRequest) -> dict:
        sm = get_session(req.session_id)
        result = sm.process(req.text)
        payload = {
            "kind": result.kind,
            "message": result.message,
            "quick_options": result.quick_options,
            "turn_count": result.turn_count,
            "forced": result.forced,
        }
        if result.kind == "generate" and result.intent is not None:
            origin = req.origin or {"lat": 22.5431, "lng": 114.0579}
            payload["recommendations"] = recommend(
                _ROUTES, _SPOTS, origin,
                matched_tags=result.intent.matched_tags,
                duration_days=result.intent.duration_days,
                max_distance_km=result.intent.max_distance_km,
            )
        return payload

    @app.get("/routes/masked")
    def routes_masked() -> List[dict]:
        return [
            {
                "route_id": r["route_id"],
                "blind_route_title": r["blind_route_title"],
                "duration_days": r["duration_days"],
                "route_type": r["route_type"],
            }
            for r in _ROUTES
        ]
else:
    app = None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
