# Routes ↔ Spots 映射说明（Phase 1）

生成时间：2026-11-06T17:25:47+08:00（Asia/Shanghai）

## 产出文件（仅 `routes/`）
- `spot_merge_plan.json`：路书站点名 → 已有 `spot_id` / 新增实体的完整映射与路线绑定预览
- `spots_route_additions.json`：需并入主库的新景点（`SP117`–`SP184`，共 68 条）
- `README-mapping.md`：本说明
- `geocode_new_cache.json`：新增点 Nominatim 缓存（可复用）

**未改写**：`routes/routes_draft.json`、`spots/spots_final.json`、`data/*`。无 Git / Mac 同步。

## 数量
| 项 | 数 |
|---|---|
| 路线 | 60 |
| 路书唯一站点名 | 107 |
| 映射到主库已有 | 39 |
| 新增实体 | 68 |
| 主库现有 | 116 |
| 合并后理论规模 | 184 |

## ID 变换规则
1. **exact**：路书名与 `spots_final.full_name` 完全一致 → 直接用原 `spot_id`（如 `故宫博物院`→`SP001`）。
2. **alias**：同地别称 / 官方景区简称 → 映射已有 ID，并在 plan 中注明理由。例如：
   - `拙政园`→`SP028` 苏州园林拙政园
   - `杭州西湖`→`SP032`（**不是**惠州西湖 `SP064`）
   - `莫高窟`→`SP096` 敦煌莫高窟
   - `维多利亚港`→`SP108` 香港维多利亚港
   - `乌镇西栅`→`SP033`（西栅属乌镇景区同一实体）
   - `天坛大佛`→`SP109` 香港大屿山昂坪
   - `张家界国家森林公园` / `袁家界`→`SP057` 武陵源（**天门山另开** `新ID`）
   - `长白山天池`→`SP018`；`镜泊湖风景区`→`SP022`
3. **create_new**：主库无同地实体 → 分配 `SP117` 起连续 ID，写入 `spots_route_additions.json`。多条路线引用同一新名只建一次（如 `香港海洋公园` 在 RT030/RT060 共用同一新 ID）。

## 明确不混并
- 香港海洋公园 ≠ 大连老虎滩海洋公园
- 杭州西湖 ≠ 惠州西湖
- 天门山 ≠ 武陵源 / 袁家界
- 独克宗古城 ≠ 丽江古城
- 青城山（新）与都江堰（`SP079`）分日保留双 ID

## 新增点数据诚实边界
- `image_url` / `adult_ticket_price`：**null** + `price_note`（未核验不编造）
- `source_channels`：仅 `Search_Engine`（OSM Nominatim 坐标 + 维基条目 URL 作名称/区位背景）
- **未**声称读取 Mac 携程 APP、马蜂窝深页、小红书/抖音登录内容
- `ai_strategy` 标明为公开信息编辑合成，非实测陪游
- `mock_weather` 为季节性参考，非实时预报
- `evolution_stats` 全 0

## 父进程收尾建议
1. 将 `spots_route_additions.json` 的 `spots[]` 追加进主库（新 ID 段）。
2. 按 `spot_merge_plan.json` → `route_bindings_preview` 给每条路线写入 `spot_ids` 与每日 `spot_id`。
3. 再跑 `scripts/validate_blindbox_seed.py`；`advice_revalidate_before_release` 仍建议人工复核别名与坐标精度。

## 自校验
- errors: 0
- warnings: 0


## 修订（2026-11-06T17:34:10+08:00 Asia/Shanghai）
- 只重写 `spots_route_additions.json` 内容字段：去掉 summary 票价重复尾、description 统一脱敏套话、interpretation 重复免责句；每条 strong 解读 100–150 字。
- 样例补录 **SP185 柳州螺蛳粉小镇**、**SP186 乌兰察布火山地质公园**（Nominatim 坐标；票价/图 null；Search_Engine）。
- count=**70**（SP117–SP186）。未改路线；未触发合并；未碰 `spots_final` / `*_editorial_locked.json`。

