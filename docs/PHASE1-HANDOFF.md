# BlindBoxTravelAI Phase 1 数据交付交底

封存日期：2026-11-06（Asia/Shanghai）

## 1. 已完成

- `data/spots_seed.json`：186 个景点，覆盖中国大陆及港澳台 34 个省级行政区。
- `data/routes_seed.json`：60 条路线；1 日 22、2 日 21、3 日 9、4 日 2、5 日 1、6 日 2、7 日 3。
- 包括 116 条审核锁定基础景点，和为路线合并/补全生成的 70 个站点（SP117–SP186）。同一站名的别名已复用，107 处路线引用不存在悬空 ID。
- `data/evolution_metrics.json`：186 个 spot ID 与 60 个 route ID 均有 plan_mark_count=0、review_count=0；不是按 ID 追加一次计数的演变日志。
- 正式构建：`python3 scripts/build_phase1_seed.py .`；复验：`python3 scripts/validate_blindbox_seed.py .`。
- 最新验证：186 spots、60 routes、34 provinces、0 unbound references、0 errors、0 warnings。原始输出保存在 `docs/phase1-validation.txt`。
- 2–4 个 strong、2–5 个 weak，白名单检索，盲名等长、恰留两个汉字，文案长度与强标签解读长度，以及 full_name/已知别名的破盲检查均由脚本执行。
- 未记录社交作者昵称、头像、账号 ID、联系方式或个人主页；不保存原始爬取页面到成品。

## 2. 重要边界：不是全渠道采集和全部事实核实完成版

本批是结构化、脱敏与标签映射达标的公开信息编辑合成版本。**没有执行 Mac 携程 APP 数据采集；没有登录墙内的小红书/抖音；没有覆盖马蜂窝正文、深圳磨房、8264、两步路的实测路线及 GPX 轨迹。** 因此五渠道任务尚未全部完成，不能把 0 errors 当作全网采集或字段事实已经逐条核验。

来源字段已做防冒领：186 条全部含 Search_Engine；仅 4 条含 Official_Site，为故宫博物院、八达岭、颐和园、五大连池。其余 182 条不因查到百科或公开地理信息即标“官方渠道”。路线是编辑合成，不宣称来自指定社交平台直采。

路线来源账本 `routes/source_ledger.json`：30 条 public_itinerary、4 条 official_line、26 条 geo_synthesis；其中来源 ref 有 71 个 HTTP 可达记录、29 个 still-unverified。“可达”不代表内容逐字证明当前全部日程；“地理合成”不代表实地踩线。该账本分类不能替代五渠道来源字段。

- 图片 `image_url`：186 条均 null，未伪造或擅用来源不明的图片。
- `adult_ticket_price`：只有 SP001、SP002、SP003 各保留一个带证据的当前参考值，其余全部 null。**null 不是免费，0 元也不能随意代替未核实票价。** 新增条目的 current-events 文案不应视作实时节庆核验。
- 经纬度多由公开地理编码获得，是景区/片区级定位，非检票口实测；不承诺精确入口或 Haversine 绝对零误差。
- `mock_weather`：静态季节性参考，不是实时天气预报、风险保证或安全建议。
- `ai_strategy`：编辑建议与部分公开路书提炼，不冒充每点的指定社媒直采；出发、开放范围、交通、活动、安全须查当日权威发布。

## 3. 原始标签库审计

`tags_500.json` 原样保留：声明 500，实际 475 项，471 个唯一名称；重复：探险、溯溪、赶海、穷游。七维度的声明数量也与数组不完全一致。脚本以实际数组作为白名单，未自造标签补满 500。详见 `docs/tags-audit.json`。

## 4. 构造与兼容约定

- 主数据集为顶层 JSON 数组，与交底模板一致。计数器文件是 spots_metrics/routes_metrics 两本字典。
- `single_spot`：1–2 天、恰一个景点。为满足交底的一日游要求，`multi_spot` 扩展为 1–7 天、至少两个景点。
- 一个城市一日游需要多节点时，采用 `schedule_schema="day_segments_v1"`，一个 day 内放 `segments`，而不是虚构额外过夜。常规的 daily_schedule/day/spot_id/blind_highlights 结构仍保留。
- RT019、RT020、RT056、RT059、RT060 中未实际走访的节点已从路线列表剔除；这些景点仍保留在 Spots。
- `source_aliases` 仅作同源别名与泄漏复核，不是向用户暴露真名的新字段。
- 契约、绑定使用的名字、每个日节点的审计与六大标签语义复核一并附在 docs/routes。

## 5. 同步与 Git 的当前事实

封存时 Mac `ba88beda-38f3-4265-b3d8-dbf9c180ae0b` 离线。已完成的是盒内 `/workspace/blindbox-travel/` 的构建、校验与交付包。**最终数据尚未同步到 `/Users/David1/BlindBoxTravelAI/data/`，未在 Mac 上跑复验，未推送 GitHub，没有本批 commit。**

机器恢复在线后：先读 git status、当前仓库 origin 与已有同名文件，保留已有项目变更；将本包中的 `data/`、`scripts/`、`docs/` 和必要的 `routes/` 审计增量放入 `/Users/David1/BlindBoxTravelAI`（交底里保留盒内说明可改为本机数据状态），再运行验证器。远端读取可见 main 当时只为 README、tip=69c5d1e7172374581409e60a252eb4d88354c55f，但该已有内容必须保留。只有写入已走正式 Git、远端 head 回读后，才可以报告 commit 与推送成功。

## 6. 交付包内容

- data/：三个正式 JSON、原标签库，以及 province_coverage.json。
- scripts/：正式构建和验收脚本。
- docs/：字段契约、标签审计、最新验证报告、本文件、SHA-256 清单。
- spots/：基础景点锁定审核与来源/人工编辑报告。
- routes/：路线锁定审核、映射、新站点与标签复核、来源账本及状态记录。

此包可作为下一阶段真实渠道补齐的基线，而不是“携程 / 社交 / 户外实测都已完成”的终版。正式应用上线前的票价、图片授权与可用性、活动、实时气象与实地安全，仍需专项更新。
