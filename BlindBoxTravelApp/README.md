# BlindBoxTravelApp — Apple 三端通用工程（Milestone 3）

盲盒旅行AI 的 SwiftUI 跨端应用（iPhone / iPad / Mac），与本地核心算法包 `BlindBoxCore` 协同。

## 目录结构

```text
BlindBoxTravelApp/
├── project.yml              # XcodeGen 工程定义（`xcodegen generate` 生成 .xcodeproj）
├── App/
│   ├── BlindBoxTravelApp.swift
│   ├── ContentView.swift    # sheet / alert 编排（升级、订单、分享、共创）
│   └── AppState.swift       # 对话引擎 / 会员 / 订单 / 分享与共创流程
├── Views/
│   ├── ChatView.swift               # ≥2 字对话区 + 距离下拉 + 订单中心/会员入口
│   ├── BlindBoxCardsView.swift      # 3 条盲盒卡片（首条重点推荐，隐去真名与票价）
│   ├── UnlockCeremonyView.swift     # 开盲盒 → 生成正式订单 → 分享/导出
│   ├── PlanOrderCenterView.swift    # 订单管理（已出行/改变/取消/删除 + 标注点评）
│   ├── PaywallView.swift            # Pro 订阅墙（¥28/月、¥252/年）
│   ├── ShareSheetView.swift         # 普通分享（ImageRenderer 长图 + 系统分享面板）
│   └── CoCreationJoinView.swift     # 亲友打开 .bbx：申请加入 / 克隆创建
├── Support/                 # L10n（简繁）、Theme（跨平台色）、Info.plist
├── Resources/               # 种子数据 + zh-Hans/zh-Hant 语言包
└── BlindBoxCore/            # 本地 Swift Package：Models + 核心算法（独立 `swift test`）
    ├── Sources/BlindBoxCore/Core/
    │   ├── Membership.swift        # 会员分级 + 免费 1 槽位 + .bbx 导出门禁
    │   ├── OrderStore.swift        # 订单仓库（状态机 + 持久化 + 匿名点评）
    │   └── BBXCodec.swift          # .bbx 编解码（zlib + SHA256 完整性校验 + 深链）
    └── Tests/               # 42 项测试
```

## 构建

```bash
cd BlindBoxTravelApp
xcodegen generate
xcodebuild -project BlindBoxTravelApp.xcodeproj -scheme BlindBoxTravelApp \
  -destination 'generic/platform=iOS Simulator' -configuration Debug build
```

## 测试核心算法

```bash
cd BlindBoxCore
swift test    # 42 项测试
```

## 本里程碑（M3）实现要点

- **订单管理**：`PlanOrderStore` 维护 `planned/completed/modified/cancelled/deleted` 状态机；
  免费会员仅 1 个活跃槽位，删除后释放；标注/点评严格无身份字段。
- **商业化**：`MembershipGatekeeper`（¥28/月、¥252/年）+ 订阅墙 + 槽位拦截双选项模态框
  （升级 Pro / 前往订单管理删除）。注：IAP 为演示直通，真实产品接 StoreKit2。
- **分享体系**：普通分享（`ShareSheetView` + `ImageRenderer`）免费/Pro 通用；
  `.bbx` 专有格式（`BBXCodec`：JSON → zlib → SHA256 完整性签名）Pro 专属导出。
- **亲友共创**：`CoCreationJoinView` 打开 `.bbx` 直接明文，支持
  【申请加入对方行程】/【创建一份自己的行程（改日期/出发地/交通方式）】。

## 本里程碑（M4）实现要点

- **GitHub 进化变量同步**：`EvolutionMetrics`（匿名统计库）+ `EvolutionSyncEngine`
  （离线入队 + 在线原子 GET→合并→PUT）+ `GitHubRESTTransport`（Contents API）。
- **接入推荐排序**：启动时将 GitHub 最新计数覆盖到景点/路线 `evolutionStats`，
  推荐引擎的 `log(1+plan+2·review)` 热度项即时生效。
- **匿名增量来源**：生成计划行程 → `plan_mark_count +1`；标注点评 → `review_count +1`；
  全程不采集任何 UserID / 设备 UUID / IP / 昵称。

## 待办

- 真实 StoreKit2 IAP 收据验证（当前订阅为演示直通）。
- `main.py` FastAPI 端点完善与 Grok Bot 采集数据入库校验。
- CI（GitHub Actions）跑 `swift test` + `python -m unittest`。
