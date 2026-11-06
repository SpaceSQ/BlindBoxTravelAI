# 北京首批：官方公园薄目录试点（非旅游终版）

工作目录 `/workspace/blindbox-travel-v20`；仅 box 产物，未修改 Mac、Git 或远程仓库。

## 实收与证据
- 北京市园林绿化局《北京市公园名录（2026年度）》64页 PDF 全表解析，序号1—1136完整、无跳号或重号。
- 市级独立文件1136条；16个区独立分片合计1132条；跨级同来源行ID融合后1136个目录实体，路线0。
- 这不是2268个不同景点，也不是两个独立来源交叉验证：两级分别从同一官方原始表筛选物化。百度/Google全矩阵、乡镇下钻和五渠道全覆盖均未执行，待后批。
- 城市目标1000条已达到（仅公园口径）；所有区均不足1000，真实缺口见表，未凑数。
- 查询来源：`北京市 2026 公园名录 各区 地址 公园`；记录内 query 是实际官方目录筛选，不伪装成逐条搜索引擎命中。
- PDF: https://yllhj.beijing.gov.cn/zwgk/2024nzcwj/2024nqtwj/202610/P020261020575226021358.pdf
- 通知: https://yllhj.beijing.gov.cn/zwgk/2024nzcwj/2024nqtwj/202610/t20261020_4911597.shtml
- 实际取得：2026-11-07T00:49:50.188818+08:00（Asia/Shanghai）。每条保留PDF页、原始序号、来源URL、检索式、取得时间、SHA-256。
- 官方页元数据成文/发布日期存在先后矛盾；仅把2026年度作为目录版本，不用页面日期推导运营有效期。

## 数量
|区|条数|距1000缺口|
|--|--:|--:|
|东城区|75|925|
|西城区|95|905|
|朝阳区|90|910|
|丰台区|121|879|
|石景山区|68|932|
|海淀区|144|856|
|门头沟区|33|967|
|房山区|86|914|
|通州区|71|929|
|顺义区|41|959|
|昌平区|52|948|
|大兴区|78|922|
|怀柔区|62|938|
|平谷区|43|957|
|密云区|47|953|
|延庆区|26|974|

4条经开区公园保留市级记录，不猜归属：国际企业文化园、博大公园、通明湖公园、海棠公园。其来源地址均仅写“北京经济技术开发区”，不擅自塞入大兴/通州。

## 字段质量及未完成事项
- 全量有真实名称、官方公园分类/级别、地址、来源逐行定位；全量缺经纬度、票价、图片、长文案，均为null，状态为 `catalog_indexed_pending_enrich`。
- 没有真实坐标就不编造区中心点、不声称Haversine精确；不能进入距离筛选正式流。
- 盲名逐字符等长，恰保留2个汉字；非汉字一律星号。它不能保证全球唯一，也不能单靠两字规则保证不可猜；独立ID才是主键。
- 标签仅取原标签表合法名称，每条2强2弱；属于基于公园类型/名称的编辑规则建议（`editorial_rules_pending_review`），不是官方旅游体验事实，须后续复审；未生成无依据的百字沉浸文案。
- 正式JSON没有作者、用户ID、头像、昵称、联系人或电话字段；原始政府PDF原样留作出处，含官方咨询电话，不能当作下游用户资料导入。`raw/pages/`、`official_catalog_rows.json`已剔除所有电话列。
- Overpass首探TLS EOF失败；无坐标产出，无重试、无换端点绕过、无墙内采集；改用用户允许的另一公开官方来源。
- 结构与证据链验证18文件/3404个记录实例0错误；不意味着“资料完整无警告”，缺口如上。

## 去重审计
用户原 `dedup_and_merge_resources.py` 已逐字CopyToBox保存 `inputs/`，未擅改。隔离诊断输出 `diagnostics/*DO_NOT_IMPORT.json`，它会把1136个官方序号实体压为1117，额外压掉19条，包含朝阳公园/海淀公园/顺义公园/昌平公园被归为“公园”等明显高风险跨区词干碰撞。11个风险组逐项列于 `logs/supplied_dedup_collision_audit.json`。
正式 master 使用“同目录版本+原始序号”精确身份，只合并1132个跨级重复实例；相同名称的3组跨区实体保留，人工复核，不按名称和后缀直接合并。无坐标不做空间聚类，无路线不假作路线去重。保留原目录分期/分园条目；1136是官方目录实体数，不承诺全是彼此独立地理景区。

## 产物
- `data/cities_db/11_1101.json` + `data/cities_db/index.json`
- `data/areas_db/11/{areaCode}.json` ×16 + `data/areas_db/index.json`
- `data/市级_cities.json`、`data/县级_areas.json`、`data/national_spots_master.json`、`data/national_routes_master.json`（空，不虚构路线）
- `data/evolution_metrics.json` 对每个正式spot_id初始化0
- `logs/validation_report.json`、`independent_validation.json`、`resume.jsonl`、`acquisition.jsonl`、去重及区归属待核清单
- `inputs/`原两级矩阵、原用户去重脚本、原标签库、北京下一轮query计划（标明未运行）

## 可续跑
```bash
cd /workspace/blindbox-travel-v20
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/acquire_official_source.py
.venv/bin/python scripts/build_beijing_catalog.py
.venv/bin/python scripts/validate_catalog.py
```
已实测缓存恢复后结果及字段验证不变。PDF64页4进程并发解析、县分片4线程并发；逐页检查点与逐区完成日志。一个官方PDF只下载一次，未用高并发轰击公共接口。若SHA变动拒绝复用旧检查点，需人工审查版本。下一批优先官方文保/博物馆/景区名录和可靠坐标证据，再开展路线与乡镇搜索，不伪装已完成。
