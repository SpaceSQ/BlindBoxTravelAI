# BackendService — 核心算法层与辅助推理服务（Milestone 1 + 4）

盲盒旅行AI（BlindBoxTravelAI）的后端核心算法与数据底座验证层。

## 目录结构

```text
BackendService/
├── core/                  # 核心算法（纯标准库，无第三方依赖）
│   ├── haversine.py       #   Haversine 球面距离（500~6000km 距离筛选）
│   ├── blind_masker.py    #   盲盒名自动脱敏 + 校验 + 简介去全名
│   ├── tag_matcher.py     #   强弱标签匹配(3.0/1.0) + 进化加权 + 季节适配 + 随机温度
│   ├── dialogue.py        #   ≥2汉字触发 + 1~4轮强制收敛对话状态机
│   ├── recommendation.py  #   距离筛选 + 综合打分 + 前3条（首条重点推荐）
│   ├── evolution_sync.py  #   GitHub 进化变量同步（原子 GET→合并→PUT）
│   └── loaders.py         #   data/ 种子数据加载与索引
├── scripts/
│   ├── fix_tags_500.py    #   一次性迁移：标签库修正为真正 500 个去重标签
│   └── validate_data.py   #   数据底座校验 CLI（check-blindbox）
├── tests/                 # 单元测试（unittest，39 项）
├── demo_cli.py            # 端到端演示（标准库）
├── main.py                # FastAPI 辅助推理服务骨架（Milestone 2 启用）
└── requirements.txt
```

## 运行

```bash
cd /Users/David1/BlindBoxTravelAI
python3 -m unittest discover -s BackendService/tests -t BackendService -v   # 测试
python3 BackendService/demo_cli.py                                          # 演示
python3 BackendService/scripts/validate_data.py                             # 数据校验
```

## 进化变量同步（Milestone 4）

匿名将 `plan_mark_count` / `review_count` 增量原子化推送至 GitHub：

```bash
python3 -m core.evolution_sync \
  --repo SpaceSQ/BlindBoxTravelAI \
  --path data/evolution_metrics.json \
  --deltas '{"spot": {"SP001": [1, 0]}, "route": {"RT001": [1, 0]}}' \
  --token "$GITHUB_TOKEN"
```

`--deltas` 格式：`{"spot"|"route": {"<id>": [plan_increment, review_increment]}}`。
严格零溯源：不读取、不写入任何 UserID / 设备 UUID / IP / 昵称。

> Swift 侧对应实现位于 `BlindBoxTravelApp/BlindBoxCore/Sources/BlindBoxCore/Core/EvolutionSync.swift`
> 与 `EvolutionMetrics.swift`，由 App 在“生成计划行程”与“标注点评”时匿名记录增量，
> 离线入队 `pending_evolution_deltas.json`，在线批量合并推送。
