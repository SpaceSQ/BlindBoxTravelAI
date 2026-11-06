# BJ02 conservative promotion：审查回执与使用说明

## 计数口径

| 对象 | 数量 |
|---|---:|
| 原始官方来源观察 | 408 |
| 原非公园实体组 | 338 |
| 原词法候选（不是净增） | 169 |
| 上述候选中推广 / 关联旧身份 / 待核 | 104 / 1 / 64 |
| 原复核组内额外推广 | 2 |
| 实际目录增量 / 关联旧身份 / 待核 | 106 / 22 / 210 |
| 新 master / 市级 / 区级物化 | 1242 / 1242 / 1233 |
| 新增有明确区名 / 新增未知区仅市级 | 101 / 5 |
| 新子场馆（计入106，不能再相加） | 6 |
| 实际详情URL / 涉及目录实体 | 49 / 54 |
| 正式新增路线 | 0 |

原始 full_name 字面（仅NFKC/空白/casefold）对旧库相同有6组；原脚本带行政前缀和景区后缀处理的精确碰撞17组。本轮22个关联为17个逐项复核同名目录 + 5个逐项确认的目录别称（大运河、野鸭湖、抗战雕塑园、上方山、汉石桥），不采用任何无坐标的通用自动同物合并。

### 目录增量不等于独立地理净增

本轮唯一承诺为可追溯的具名目录身份增加。缺少坐标与边界验证，不能声称地理去重完成。目录内部可以有有据可查的父子包含关系，正因此不能把园内博物馆误删，也不能把它计为与整园互斥的地理范围。

### 重点人工判读

1. 北京海洋馆 → 北京动物园；颐和园博物馆 → 颐和园；圆明园展览馆 → 圆明园遗址公园；慈悲庵 → 陶然亭公园；香山双清别墅 → 香山公园；北京金台艺术馆 → 朝阳公园。均有实际打开详情中的位置引文。保留孩子自己的 source_entity_id / 新 spot_id，父母保留旧 spot_id，通过 parent_spot_id 和 sub_spots 双向链接。5个孩子区属仍 null，不从父公园推断入县。
2. 中国人民抗日战争纪念馆和雕塑园为同一官方景区表的第26行、第107行，且分别打开了不同详情：一个是专题纪念馆，一个是雕塑园。保留不同目录身份，不按共同抗战主题词合并，也没有猜测两者精确包含关系。
3. 北京天文馆为西直门主馆；古观象台有独立建国门详情且明确隶属天文馆管理。管理关系不是同一地理场馆。古观象台本轮仍市级待核；机构/管理处样式名称仍需机构与场馆边界证据。
4. 云居寺石经博物馆、明十三陵博物馆、恭王府博物馆以及故居/博物馆管理机构等，只有共用泛景区URL的，不能据此直接合并或另造净增。香山革命纪念馆详情只说紧邻香山公园，未连成园内子点。中央电视塔与塔北侧公园、麋鹿苑与南海子公园等范围不明的也待核。
5. 南宫、十渡、百里山水画廊、京西古道、爨柏等综合/多节点范围保守留待核。新增检测到的简单包含冲突只触发 review，绝不删除。

## 来源和许可

保留原批3个官方列表/线路的来源行、显示发布日期、原响应指纹、清洗件哈希及408观察身份；详情读取时间截止 **2026-11-07 01:02:11（Asia/Shanghai）**。`details_manifest.json` 和49个 `detail_evidence/*.json` 包含实际HTTP状态、标题、短篇身份引文、响应指纹及取得时间。没有保存原响应HTML，所以响应哈希是过程指纹，不能在盒内以完整原件复算；JSON交付件哈希可以复算。

未下载图片，未确认任何图片再利用许可，image_url 保持 null。也未把详情页票价/开放时间直接标记为“2026已核实”或生产票价；description、summary_100w 均 null，不把未许可长文直接搬入展示字段。未接触社交媒体账户或用户标识。

## 核心文件

- `report.json`：全部计数与质量警告。
- `all_338_decisions.json`：每组去向、原候选归属、逐ID区名证据和判读指针。
- `all_408_observation_dispositions.json`：每条原观察去向；原公园范围排除项也保留，未丢记录。
- `promoted_catalog_entities.json`：106个真正写入副本 master 的新目录身份。
- `existing_catalog_links.json`：22个关联原身份的源记录，作为证据附到旧 master，未多发master ID。
- `review_remaining.json`：210个待核，不删除；包含/同名/机构范围有单独原因和碰撞对。
- `manual_identity_decisions.json`：显式人工审查断言，不是靠名称词干或共用URL猜同物。
- `individual_detail_identity_review.json`：54个实体的逐项详情判读；`governance_not_spatial_identity.json`记录管理关系不等于空间同物。
- `route_node_review.json`：原序35节点的精确名候选匹配；无天数，未入正式Routes。
- `source_snapshot_sha256.json`：原快照全部非虚拟环境文件哈希，验证原数据和代码未变。
- `promote.py`、`verify.py`、`test_promote.py`：独立离线ETL及验收，不运行旧去重器。`fetch_details.py`只是本次有界公开读取缓存复现器，不是推广必需步骤。

## 离线复现

```bash
A=/workspace/blindbox-travel-v20-promoted/data/batches/11/bj02/promotion_audit
python3 "$A/promote.py" --evidence-dir "$A"
python3 "$A/verify.py"
python3 "$A/test_promote.py"
```

脚本要求原1136基线和原169候选仍在源快照；只接受单独非嵌套target，拒绝覆盖无本次标记的目录。每次从原始身份投影，不把上次副本再当新增来源，所以静态快照重复执行输出不变。它是种子快照构建器，不是活跃业务计数迁移工具；不要对已经产生用户演化统计的数据库运行。原master旧ID和计数逐字段保留，新ID为 `SP_` + 原 source_entity_id，初始计数均0。未知区仅市级。

测试包括朝阳/海淀公园不误并、同名异区保留复核、空词干不全局兜底、大小写/全角规范化、无坐标与别称不自动合并、父子保留、管理关系不作空间关系、共用URL不自动别名、纪念馆与雕塑园分开、未知区不县级物化以及重复构建哈希不变。验收有明确质量警告，不得宣传零警告终版。

## 待核主原因（互斥合计210）

- `original_overlap_or_alias_unresolved`：146
- `umbrella_resort_and_child_park_scope_review`：1
- `multi_site_township_scenic_scope_review`：1
- `additional_exact_or_containment_collision_review`：12
- `multi_site_landscape_corridor_scope_review`：1
- `proper_name_too_generic`：3
- `multi_segment_historic_trail_scope_review`：1
- `multi_village_scenic_scope_review`：1
- `no_explicit_official_district_city_review_only`：43
- `administrative_or_compound_institution_scope_review`：1

同一条记录可能另有多个次要原因；`review_all_reason_counts_nonadditive` 不可相加算实体数。详情可读不等于身份/范围已解决，更不等于已验证当前营业。

## 同步边界

仅副本 master、evolution_metrics、市级及区级文件/索引增加投影，并新增promotion_audit。原BJ02名录和候选169文件保留原样，原脚本/inputs不改。本次没有Mac/Git写入，父代理负责复验与最后同步提交。不要对市县物化文件再做一次无坐标名称去重；它们只是同一身份的视图。
