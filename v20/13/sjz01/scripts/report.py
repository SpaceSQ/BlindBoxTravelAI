from pathlib import Path
import json,csv,hashlib,zipfile
from datetime import datetime
from zoneinfo import ZoneInfo
B=Path(__file__).resolve().parents[1];D=B/'data/search_batches/13/shijiazhuang_1301_batch01'
s=json.loads((D/'summary.json').read_text());r=json.loads((D/'city_candidates.json').read_text());v=json.loads((D/'validation.json').read_text());sources=json.loads((D/'source_manifest.json').read_text())
with (D/'candidate_names.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['raw_id','full_name','entity_type','area_code','area_name','source_observation_ids','status'])
 for x in r:w.writerow([x['raw_id'],x['full_name'],x['entity_type'],x['area_code'],x['area_name'],';'.join(x['source_observation_ids']),x['verification_status']])
md=f'''# 河北石家庄首批：官方目录候选隔离包（部分完成）

生成时间：{datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')} Asia/Shanghai（UTC+8）。

## 本批实收，不等于正式新增

- 5份官方目录：221条来源观察；按“同全名＋有依据区属”归并为205组候选名称身份。
- 201组有明确区属，4组待核；县级文件为市级官方目录的**区属投影**，不是县级搜索独立实收。
- 路线候选0、正式路线0、正式主库净增0。55对疑似别名／父子／名称重叠保留人工待核，不自动合并。
- 市级目标1000条尚未达到，县级目标也均未达到，不能宣布河北省完成。
- 例：西柏坡、西柏坡景区、西柏坡纪念馆景区（中共中央旧址）分别保留原目录名称，等待别名／父子审核，不能宣称3个不同地理景点。
- 工业企业仅作为官网“工业旅游示范点”目录身份，不保证现时对外开放。

## 百度／Google 执行实账

初始计划：石家庄市13词＋正定县14词＋平山县14词＝41个组合。实际仅尝试 **石家庄市 旅游景区** 一组，分别请求Google、百度，共2次；可用结果页0，搜索结果提取名称0。

Google HTTP200返回JavaScript跳转／启用脚本中间页，未得到可解析搜索结果；百度HTTP200返回“百度安全验证／网络不给力，请稍后重试”。已保留原HTML和SHA。遇安全验证即停，没有绕验证码、改用隐藏接口或将WebSearch冒称百度／Google。

余下市级12词、正定县14词、平山县14词**未执行**。完整矩阵349组合只列计划，不算完成。查询状态和具体引擎URL见query_plan.json、engine_attempts.json。一次通用WebSearch用于寻找官方目录，不计搜索引擎矩阵完成量。

## 区划依据

原输入矩阵1301有24单元，非16个：22个标准县区市记录（含输入矩阵的辛集市）＋2个扩展区。仅沿用输入快照，不自行修订辛集市现行管理隶属。两个扩展区查询前缀原本是“河北省＋区名”，照原矩阵保留。初始41组合外，其余22单元308组合均未执行。

## 官方来源

| 来源 | 实际来源观察 | 页面发布日期 | 原始证据 |
|---|---:|---|---|
'''
for id in ['official_sjz','official_province_xlsx','official_red','official_rural','official_industrial']:
 m=next(x for x in sources if x['source_id']==id);date=m.get('publication_date') or ('2026-01-30（下载入口页）' if id=='official_province_xlsx' else '见原页');md+=f"|{id}|{s['source_counts'][id]}|{date}|{m.get('url','')}|\n"
md+='''
省级Excel完整存档，并导出全部工作表行，但只将其中39条石家庄明确记录作为本批来源观察。市级A级页面表格实际41行，不采用搜索摘要所称42行。

## 各单元候选名称（非净增景点数）

| 编码 | 单元 | 实收候选名称 | 路线候选 | 已执行区县组合 |
|---|---|---:|---:|---:|
'''
for a in s['per_area']:md+=f"|{a['area_code']}|{a['area_name']}|{a['actual_source_supported_candidate_names']}|0|0|\n"
md+=f'''
## 字段、排重与核验

- 最新tags_500.json已从指定Mac原样CopyToBox复制；唯一合法标签{v['fresh_tag_whitelist_unique']}个，SHA见inputs/snapshot_hashes.json。只按名称或官方目录类别提供证据标签；证据不足时tags=[]并标记pending_evidence，不为凑标签虚构玩法。
- 记录保留full_name、盲名、区划、来源行号、原始来源链接和证据摘录；未知坐标、门票、许可图片、简介、描述均null。盲名仅保留2个汉字，其余等长星号。
- 仅合并同全名且区属不冲突的来源；无区属来源仅在该名称全部已知区属唯一时借用官方证据补全。不同村同名、名称变体不武断合并。55对复核项并非全部真实别名。
- 结构化候选和摘录不含电话、邮箱、社交账号；raw完整官方网页留有原网页公开电话／站点联系信息，仅为原文证据，不作为实体联系字段入库。未下载任何非许可图片。
- {v['assertions']}项离线断言通过：SHA、引用、名称、区划来源、空值、标签、盲名和搜索账。不是独立实地核验／正式去重评审。
- 未改Mac任何文件、北京、Phase 1或Git；本目录位于独立box工作区，不是仓库改动。

## 文件与复现

`data/search_batches/13/shijiazhuang_1301_batch01/`：source_observations.json、city_candidates.json、county_candidates.json、24个area_candidates/分片、route_candidates.json、candidate_names.csv、source_manifest.json、alias_parent_child_review.json、query_plan.json、engine_attempts.json、summary.json、validation.json。

原网页／省级Excel在raw/；来源请求日志在logs/；输入矩阵与最新标签快照在inputs/。离线复现：

```
python3 scripts/build_batch.py
python3 scripts/validate.py
python3 scripts/report.py
```

依赖Python3、requests、beautifulsoup4、openpyxl。fetch_official.py只会重新下载其中4份官网资料，不会重跑搜索引擎，也不会触及Mac或Git。引擎错误应待访问恢复后继续，不能把本批包说成41组合已跑完。
'''
(B/'README.md').write_text(md);(D/'REPORT.md').write_text(md)
(B/'logs/discovery_websearch.json').write_text(json.dumps({'tool':'WebSearch','query':'石家庄市 2026 A级旅游景区 名录 2025 site.gov.cn','role':'official URL discovery, NOT actual Baidu/Google matrix completion','discovered_official_urls':['https://wglj.sjz.gov.cn/columns/78ae016a-9b7c-4e84-9855-358e950c4b6b/201909/29/e180a7a4-1769-4748-b305-ad6cea23d762.html','https://wglj.sjz.gov.cn/columns/78ae016a-9b7c-4e84-9855-358e950c4b6b/index.html','https://whly.hebei.gov.cn/c/2026-01-30/584097.html'],'warning':'Search synthesis said 42 scenic rows; direct official HTML table has 41, and only direct table is used.'},ensure_ascii=False,indent=2))
paths=[p for p in B.rglob('*') if p.is_file() and p.name!='SHA256SUMS'];(B/'SHA256SUMS').write_text(''.join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(B)}\n" for p in sorted(paths)))
archive=B.parent/'blindbox-hebei-shijiazhuang-batch01-20261107.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(B.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(B.parent))
print(archive,archive.stat().st_size,hashlib.sha256(archive.read_bytes()).hexdigest())
