# 给 Claude Code 的工程开发交底书（Engineering Handoff Specification）

> **致 Claude Code**：  
> 我们正在 `/Users/David1/BlindBoxTravelAI` 目录下从零开启全新的 **“盲盒旅行AI（BlindBoxTravelAI）”** 项目（请完全忽略任何历史旧版本的残留记忆，以本交底书与同目录下的 `01_盲盒旅行AI_项目开发需求书_PRD.md` 为唯一工程准绳）。  
> **代码托管仓库**：`https://github.com/SpaceSQ/BlindBoxTravelAI`  
> **目标交付物**：面向 Apple App Store（中国版，含简体/繁体中文）的 **iPhone + iPad + Mac** 跨端应用及配套 AI 推理与 GitHub 进化变量同步服务。

---

## 一、 工程目录结构规范

请在 `/Users/David1/BlindBoxTravelAI` 下按照以下模块化结构初始化并组织代码：

```text
/Users/David1/BlindBoxTravelAI/
├── CLAUDE.md                                     # Claude Code 核心上下文与命令速查
├── 01_盲盒旅行AI_项目开发需求书_PRD.md              # 产品需求书 (PRD)
├── 02_Claude_Code_工程开发交底书.md                # 本工程开发交底书
├── 03_Grok_Bot_千里眼任务交底书.md                 # Grok Bot 数据采集交底书
├── data/                                         # 核心种子数据与进化算法变量库
│   ├── tags_500.json                             # 7大维度500个核心旅游标签库（强/弱权重）
│   ├── spots_seed.json                           # 初始景点盲盒种子数据（SP001~SP005及扩展）
│   ├── routes_seed.json                          # 1~7天单景点及多景点串联行程路线库
│   └── evolution_metrics.json                    # 保存在 GitHub 仓库的进化算法统计变量（计划次数/点评次数）
├── BlindBoxTravelApp/                            # Apple 三端通用工程 (SwiftUI: iOS / iPadOS / macOS)
│   ├── App/                                      # 应用入口、Universal Links 与 .bbx 文件注册
│   ├── Core/
│   │   ├── AIEngine/                             # 中文旅行词汇库匹配 + 本地/混合大模型 1~4轮对话状态机
│   │   ├── Recommendation/                       # Haversine 距离计算 + 强弱标签匹配 + 进化变量加权引擎
│   │   ├── BlindMasker/                          # 汉字盲盒脱敏器与明文解锁渲染器
│   │   ├── ProprietaryFormat/                    # .bbx 自有专有格式序列化、签名、导入导出与分享器
│   │   ├── GitHubEvolutionSync/                  # 基于 GitHub REST API 的无溯源热度变量读写器
│   │   └── StoreKitManager/                      # 免费会员槽位限制 vs Pro会员(28元/月, 252元/年) IAP 管理
│   ├── Models/                                   # SwiftData / Codable 模型定义 (Tag, Spot, Route, PlanOrder)
│   ├── Views/
│   │   ├── ChatView/                             # ≥2汉字触发对话区 + 距离下拉框 + 1~4轮引导交互
│   │   ├── BlindBoxCardsView/                    # 3条盲盒推荐卡片（首条重点推荐，隐去真名与票价）
│   │   ├── UnlockCeremonyView/                   # 选定盲盒 -> 填日期/出发地/交通方式 -> 开盲盒明文解锁动效
│   │   ├── PlanOrderCenterView/                  # 旅行计划管理（已出行/计划改变/计划取消/删除释放槽位）
│   │   ├── CoCreationJoinView/                   # 亲友打开分享行程：申请加入对方行程 / 克隆创建自己行程
│   │   └── PaywallView/                          # Pro 会员订阅墙 (¥28/月, ¥252/年)
│   └── Resources/
│       ├── zh-Hans.lproj/Localizable.strings     # 简体中文语言包
│       └── zh-Hant.lproj/Localizable.strings     # 繁体中文语言包（自动转换标签与文案）
└── BackendService/                               # 轻量级 Python/FastAPI 或 Node.js 辅助推理与爬虫入库接口
    ├── main.py                                   # 自然语言转标签、路线合成与 Grok Bot 数据校验入库 API
    └── tests/                                    # 核心算法单元测试（距离筛选、脱敏逻辑、4轮收敛保障）
```

---

## 二、 核心数据结构与 Schema 定义

### 2.1 标签表（`Tags` 模型）
读取 `data/tags_500.json`，包含 7 大维度共 500 个标签：
```json
{
  "tag_id": "TAG_EMO_001",
  "name_zh_hans": "治愈",
  "name_zh_hant": "治癒",
  "category": "Emotion & Mood",
  "default_weight_type": "strong" // "strong" (权重 3.0) 或 "weak" (权重 1.0)
}
```

### 2.2 景点盲盒表（`Spots` 模型）
读取 `data/spots_seed.json`，严格遵循附件 JSON 结构并扩展进化变量字段：
```json
{
  "spot_id": "SP001",
  "full_name": "甘孜稻城亚丁风景区",
  "blind_name": "**稻**丁***",
  "province": "四川省",
  "city": "甘孜藏族自治州",
  "location": { "lat": 28.4124, "lng": 100.2078 },
  "tags": [
    { "name": "眼睛在天堂", "type": "strong" },
    { "name": "雪山", "type": "strong" },
    { "name": "重装徒步", "type": "strong" },
    { "name": "缺氧", "type": "weak" },
    { "name": "洗涤心灵", "type": "weak" },
    { "name": "蓝色星球", "type": "weak" }
  ],
  "description": "脱敏详细介绍（严禁出现 full_name，但保留省市区位）...",
  "summary_100w": "100字以内脱敏精华摘要...",
  "image_url": "https://example.com/images/daocheng.jpg",
  "adult_ticket_price": 266,
  "mock_weather": {
    "temp": "5°C - 15°C",
    "humidity": "45%",
    "wind": "西北风 4级",
    "uv_index": "极强 (9)",
    "alert": "高原反应预警：海拔超4000米，请注意防寒保暖，切勿剧烈运动。"
  },
  "events_and_discounts": "【活动通知】...",
  "ai_strategy": "AI 行程动线与避坑建议...",
  "tag_interpretation": "强标签深度解读...",
  "evolution_stats": {
    "plan_mark_count": 0,
    "review_count": 0
  }
}
```

### 2.3 盲盒行程路线与计划订单模型（`PlanOrder` 模型）
支持 **单景点行程（1~2天）** 与 **多景点串联行程（2~7天，至少包含 2 个景点）**：
```json
{
  "order_id": "ORD_20261106_001",
  "route_id": "RT_SW_001",
  "duration_days": 3,
  "route_type": "multi_spot", // "single_spot" (单一景点路线) | "multi_spot" (≥2个景点多日路线)
  "is_featured": true,        // 三条推荐中的第一条重点推荐为 true
  "is_unlocked": false,       // false: 盲盒脱敏态; true: 已选定或已分享的明文态
  "spots": ["SP001", "SP006"],
  "departure_config": {
    "departure_date": "2026-11-15",
    "origin_city": "深圳市",
    "origin_location": { "lat": 22.5431, "lng": 114.0579 },
    "transport_mode": "飞机+自驾" // 自驾 | 高铁动车 | 飞机 | 大巴 | 骑行
  },
  "order_status": "planned",  // "planned"(待出行) | "completed"(已出行) | "modified"(计划改变) | "cancelled"(计划取消)
  "user_annotation": {
    "rating_stars": 5,
    "comment_text": "氧气瓶一定要提前买好，牛奶海太震撼了！",
    "annotated_at": "2026-11-20T10:00:00Z"
    // 注意：严禁包含任何 user_id / nickname / device_id 字段，确保绝对隐私！
  },
  "participants": ["创建者", "好友A(已申请加入)"]
}
```

---

## 三、 六大核心工程逻辑实现细则（必读）

### 3.1 对话状态机与“1~4轮强制收敛生成3条盲盒订单”
1. **输入门槛校验**：
   - 使用正则 `[\u4e00-\u9fa5]{2,}` 校验用户输入是否包含至少 2 个汉字。若不足 2 个汉字，轻量提示“再多说两个字，让我捕捉你的旅行灵感~”。
2. **对话轮次计数器（`turn_count`: 1 ~ 4）**：
   - **本地大模型 + 500词汇库协同架构**：优先使用 Apple 端侧模型（CoreML / MLX 本地量化模型或配置的 LLM API）结合 `tags_500.json` 进行意图槽位提取（提取维度：`MatchedTags`、`DurationDays(1-7)`、`MaxDistanceKm`、`CompanionType`）。
   - **收敛判定逻辑**：
     - 计算当前意图明确度 `SpecificityScore`（0.0 ~ 1.0）。
     - 若 `turn_count == 1` 且用户直接表达“随便/周末去玩/直接推荐”或 `SpecificityScore >= 0.75`，立即在 **第 1 轮** 触发盲盒生成。
     - 若 `1 <= turn_count < 4` 且 `SpecificityScore < 0.75`，生成 1 句简短、有引导性的追问（同时提供 3~4 个快捷胶囊选项供用户一键点击），引导收敛到具体路线。
     - **硬性红线**：当 `turn_count == 4` 时，**严禁继续追问**！必须利用已有的显式输入 + 隐式条件（当前 GPS 位置、当前日期对应的季节）立即输出 **3 条盲盒行程路线订单**（其中第 1 条 `is_featured = true` 重点推荐）。
3. **动态随机性算法**：
   - 用户输入越宽泛（`SpecificityScore` 越低），随机温度系数 `Temperature` 越高（最高 0.85），从符合当前所在地距离范围与当季气候的景点/多日路线库中随机碰撞出 3 条惊喜路线；
   - 用户输入越具体（`SpecificityScore` 越高），随机温度系数越低（最低 0.15），严格按强标签（权重 3.0）与弱标签（权重 1.0）重合度排序输出最匹配的 3 条路线。

### 3.2 距离筛选器与 Haversine 球面距离计算
1. UI 顶部提供距离筛选器：`Dropdown(500km, 1000km, 2000km, 3000km, 4000km, 5000km, 6000km)`。
2. 实现标准 Haversine 公式计算用户当前坐标 $(\text{lat}_1, \text{lng}_1)$ 与景点坐标 $(\text{lat}_2, \text{lng}_2)$ 的距离 $d$：
   ```swift
   func haversineDistance(lat1: Double, lng1: Double, lat2: Double, lng2: Double) -> Double {
       let R = 6371.0 // 地球平均半径 (km)
       let dLat = (lat2 - lat1) * .pi / 180.0
       let dLng = (lng2 - lng1) * .pi / 180.0
       let a = sin(dLat / 2) * sin(dLat / 2) +
               cos(lat1 * .pi / 180.0) * cos(lat2 * .pi / 180.0) *
               sin(dLng / 2) * sin(dLng / 2)
       let c = 2 * atan2(sqrt(a), sqrt(1 - a))
       return R * c
   }
   ```
3. 对于由多个景点组成的多日行程路线（`multi_spot`），以路线首站景点距离满足用户所选距离阈值（且相邻景点间车程合理，构成 2~7 天顺畅动线）为准。

### 3.3 盲盒脱敏算法与“选定/分享即明文”状态切换
1. **自动汉字脱敏生成器（供新入库景点/路线使用）**：
   - 输入完整名称 `full_name`（长度 $L$），随机或按非核心字规则保留 **2 个汉字**，其余全部替换为 `*`。
   - 脱敏校验器：自动扫描 `description` 和 `summary_100w`，确保其中不包含 `full_name` 或核心专有名词（若出现则自动替换为“这座秘境”、“该目的地”等代称），但保留 `province` 与 `city`。
2. **渲染层严格门禁**：
   - 当 `order.is_unlocked == false`（未选定盲盒态）：
     - 标题展示：`spot.blind_name`
     - 门票价格：隐藏 `adult_ticket_price`（渲染为 `"🎫 选定行程后揭晓"`）
     - 点评按钮：禁用（置灰提示“生成计划行程后可标注/点评”）
   - 当用户选定某条盲盒，填写完 **【出发日期、出发地、出发交通方式】** 并点击确认生成【计划行程单】后，或者当该行程单是通过 **分享 / `.bbx` 导入** 获得时：
     - 立即将 `order.is_unlocked` 设为 `true`；
     - 播放 1.5 秒“盲盒开启”粒子/卡片翻转动画；
     - **全局切换为明文**：所有景点名称展示 `spot.full_name`，路线名称展示完整明文，揭晓 `adult_ticket_price`，激活“标注/点评”与“分享/导出”功能。

### 3.4 旅行计划管理（订单状态机）与会员商业化拦截
1. **免费会员 vs Pro 会员权限拦截器（`MembershipGatekeeper`）**：
   - 查询当前持久化的活跃订单列表：`activeOrders = orders.filter { $0.orderStatus != .deleted }`（或根据业务策略，免费会员在未删除已有订单前仅限持有 1 份计划行程单）。
   - 若 `user.tier == .free && activeOrders.count >= 1`：
     - 当用户尝试生成第 2 个计划行程单时，拦截请求并弹出双选项模态框：
       - **主按钮**：【升级 Pro 会员（¥28/月 或 ¥252/年）—— 解锁无限量行程与专有格式导出】
       - **次按钮**：【前往订单管理删除已有行程，继续免费生成】
2. **订单处理操作（旅行计划管理页）**：
   - 每个计划行程单提供状态切换菜单：
     - **标记为“已出行”**：记录完结状态，鼓励用户填写标注与点评。
     - **“计划改变”**：打开编辑抽屉，允许修改出发日期、出发地、交通方式或重新召唤 AI 调整天数（1~7天），生成更新后的计划行程单。
     - **“计划取消” / “删除订单”**：将状态标记为已取消或从本地列表中删除（免费会员删除后，`activeOrders.count` 归零，恢复免费生成额度）。

### 3.5 分享体系、`.bbx` 自有专有格式与亲友同行/克隆机制
1. **社交媒体普通分享（免费 & Pro 通用）**：
   - 使用 SwiftUI `ImageRenderer` 将明文【计划行程单】（包含明文景点名称、每日路线、出发日期/地点/交通方式，以及用户填写的**标注/点评**）渲染为高颜值长图，调用系统 ShareSheet 分享至微信朋友圈、小红书、抖音。
2. **自有专有格式 `.bbx`（Pro 会员专属保存/输出）**：
   - 当用户点击【以专有格式保存/输出 (`.bbx`)】时：
     - 若为免费会员，弹出 Pro 升级订阅墙（28元/月，252元/年）。
     - 若为 Pro 会员，将 `PlanOrder` + 关联的明文 `Spots` 数据 + `user_annotation`（标注/点评）序列化为 JSON 并打包为 `.bbx` 文件（同时支持生成带 Base64 压缩载荷的深链 `blindboxtravel://import?payload=...`）。
3. **亲友在 APP 中打开 `.bbx` / 分享行程后的交互视图（`CoCreationJoinView`）**：
   - 亲属好友在自己的 APP 中打开该行程后，**所有汉字直接以明文呈现**，并展示分享者的标注/点评。
   - 底部固定提供两个核心行动按钮：
     - **【申请加入对方行程】**：点击后将该亲友加入此行程的同行人列表，同步行程日程。
     - **【创建一份自己的行程】**：以当前明文行程为模板实例化新订单，弹出配置面板允许亲友修改自己的 **出发日期、出发地、出发交通方式**，保存后成为亲友自己的计划行程单，且同样支持再次分享。

### 3.6 隐私保护与 GitHub 仓库进化算法变量同步器（`GitHubEvolutionSync`）
1. **零溯源隐私设计**：
   - 本地与云端同步的数据结构中，**严禁收集或上传任何用户身份标识（无 UserID、无设备 UUID、无 IP 记录）**。用户写的点评文本仅保存在用户本地订单及用户主动发出的分享文件中，前端展示景点/路线时仅显示热度统计，**绝不溯源显示点评来源**。
2. **GitHub 仓库变量持久化方案**：
   - 目标仓库：`https://github.com/SpaceSQ/BlindBoxTravelAI`
   - 目标文件路径：`data/evolution_metrics.json`
   - 文件结构：
     ```json
     {
       "last_updated": "2026-11-06T08:30:00Z",
       "spots_metrics": {
         "SP001": { "plan_mark_count": 128, "review_count": 45 },
         "SP002": { "plan_mark_count": 96, "review_count": 38 }
       },
       "routes_metrics": {
         "RT_SW_001": { "plan_mark_count": 64, "review_count": 21 }
       }
     }
     ```
   - **同步机制**：
     - 当用户将某盲盒生成计划行程单（`plan_mark_count + 1`）或对其进行标注/点评（`review_count + 1`）时，调用 `GitHubEvolutionSync` 服务。
     - 通过 GitHub REST API (`PUT /repos/SpaceSQ/BlindBoxTravelAI/contents/data/evolution_metrics.json`，需在环境变量或安全配置中配置 `GITHUB_TOKEN`) 原子化读取当前 `sha`、累加计数并提交 Commit（Commit Message 如 `chore(evolution): anonymous metric increment for SP001`）。
     - 若离线或未配置 Token，先写入本地待同步队列 `pending_evolution_deltas.json`，联网或执行同步脚本时批量合并推送至 GitHub 仓库。

---

## 四、 分阶段开发执行路线图（Claude Code Action Plan）

请按照以下 4 个 Milestone 依次推进开发与自测：

- **Milestone 1：数据底座与后端/核心算法层验证**
  1. 校验 `data/tags_500.json` 与 `data/spots_seed.json`，并构建 `data/routes_seed.json`（包含单景点 1~2 日路线与 ≥2 景点 2~7 日串联路线）及 `data/evolution_metrics.json`。
  2. 编写核心引擎模块（Haversine 距离筛选、强弱标签匹配 + 进化变量加权 + 动态随机度评分、1~4轮对话强制收敛状态机、盲盒名自动脱敏与明文还原器），并通过单元测试验证。
- **Milestone 2：Apple 三端通用 UI 与盲盒核心心流（iPhone / iPad / Mac）**
  1. 搭建 SwiftUI Universal 工程，配置简繁体中文（`zh-Hans` / `zh-Hant`）双语支持。
  2. 实现 ≥2 汉字触发的 AI 对话页、距离下拉筛选器（500km~6000km）、1~4 轮引导式交互及 3 条盲盒行程卡片（首条重点推荐、隐去真名与票价）。
  3. 实现选定盲盒后的参数设定弹窗（出发日期、出发地、交通方式）与“开盲盒”明文解锁动效。
- **Milestone 3：订单管理、Pro 商业化订阅与专有格式社交共创**
  1. 实现旅行计划管理中心（已出行、计划改变、计划取消/删除）及免费会员 1 个行程槽位限制逻辑。
  2. 实现 Pro 会员订阅页（28元/月，252元/年）与权限门禁。
  3. 实现普通社交媒体分享卡片导出（含用户标注/点评）与 Pro 专属 `.bbx` 格式导出/导入，以及亲友打开后的“申请加入对方行程”与“创建一份自己的行程（改日期/出发地/交通方式）”全流程。
- **Milestone 4：GitHub 进化算法变量同步与全链路联调**
  1. 实现 `GitHubEvolutionSync` 模块，将 `plan_mark_count` 与 `review_count` 匿名更新至 `https://github.com/SpaceSQ/BlindBoxTravelAI` 仓库，并接入推荐排序权重。
  2. 运行全套自动化测试并提交代码至 GitHub 仓库。
