# Editorial review — BlindBoxTravelAI spots_final.json

Time: Asia/Shanghai (box clock). Pass focus: channel honesty, anti-boilerplate, semantic tag fixes, seed-spot care.

## Verdict (honest)
**Not perfect.** Deep rewrites cover the worst template failures and channel mislabels; remaining ~90 entries got a **light** de-boilerplate pass (still thinner than a full per-spot field investigation). Images remain null; most ticket prices remain null on purpose. Routes are out of scope for this pass (validator still flags empty routes).

## Channel policy after repair
| Channel | Spots declaring it | Rule applied |
|---|---:|---|
| Search_Engine | 116 | OSM Nominatim geocode + zh.wikipedia topic URL + Xinhua 5A list page |
| Official_Site | **4** | Only where a scenic official / gov tourism URL was actually attempted this pass |

Official_Site set (with `access_status` / notes on each ref):
- SP001 故宫博物院 — `dpm.org.cn` Visit +票务页（Visit WebFetch ok）
- SP002 八达岭长城 — `badaling.cn`（fetch 空正文）+ VisitBeijing 景点页摘要
- SP003 颐和园 — `summerpalace-china.com`（504）+ 官网票务摘要
- SP021 五大连池 — `chinawdlc.org.cn`（500）+ 管委会门户摘要

**Corrected:** wikipedia / OpenStreetMap / news.cn **no longer** labeled `Official_Site`.

MCT `sjfw.mct.gov.cn` was previously mass-attached as Official_Site without per-spot page reads — **removed** from default Official_Site claims this pass (名录交叉改留在 Search_Engine 的新华报道)。

## Seed-example care (reference/spots_seed.json)
| Seed | In corpus? | Action |
|---|---|---|
| 甘孜稻城亚丁风景区 | SP077 稻城亚丁风景区 | Deep rewrite: 雪山/重装徒步/高原；脱敏去掉神山专名；策略保留短线适应+长线逻辑（公开常识级，非冒充陪游） |
| 柳州螺蛳粉小镇 | **缺失** | Not in 116 list — logged as gap |
| 泉州蟳埔村 | SP043 | Deep rewrite: 非遗/渔村巷弄/妆饰体验；敏感词簪花/蚵壳厝已屏蔽 |
| 乌兰察布火山地质公园 | **缺失** | Not in list — gap（近义有响沙湾等沙漠/地质向条目） |
| 长沙橘子洲头 | SP058 岳麓山橘子洲旅游区 | Deep rewrite: 江心洲+西岸联合游线；红色旅游/江河/散步 |

Seed JSON itself still contains leaky proper nouns and unverified promotional tone — **not copied verbatim** into production fields.

## Deep rewrite set
['SP001', 'SP002', 'SP003', 'SP004', 'SP005', 'SP006', 'SP007', 'SP008', 'SP009', 'SP010', 'SP011', 'SP012', 'SP013', 'SP014', 'SP015', 'SP016', 'SP017', 'SP018', 'SP019', 'SP020', 'SP021', 'SP023', 'SP025', 'SP043', 'SP058', 'SP077']

Count: 26 (includes first-20 Beijing→Jilin block, plus 五大连池/太阳岛/上海科技馆, plus seed-related SP043/SP058/SP077).

Highlights of semantic fixes:
- 响沙湾: 海岸线/看海 → **沙漠/苍凉/出片**
- 太阳岛: 海岸线/看海 → **湿地/避暑/出片**
- 上海科技馆: 海岸线 → **博物馆/亲子/研学**
- 承德避暑山庄: 登山/奇峰 → **园林/行宫/寻古**
- 故宫: 历史名城（城池河道套话）→ **沉浸式**；古建/博物馆中段重写

## Light pass / not deeply rewritten
Light de-boilerplate: 93 ids  
Tag-fix-only extras: ['SP023', 'SP025']  
These still read thinner (province+theme skeleton). **Do not treat as field-verified prose.**

## Prices / images
- Verified numeric prices kept/updated only where official/gov tourism evidence exists: 故宫60（旺季）、八达岭40（旺季公开摘要）、颐和园30（旺季公开摘要）
- All `image_url` remain **null** (no fabricated CDN)
- Unverified fares stay null + `price_note`

## Validator
- Spot-level errors: none after repair (channels match ledger)
- Warnings: none after interp body 100–150 clamp
- Remaining errors are **route Phase-1 requirements** (empty routes_seed) — other agent scope
- Note: validator had a transient IndentationError mid-edit; syntax restored for this run

## Gaps / next
1. Add missing seed spots 柳州螺蛳粉小镇、乌兰察布火山地质公园 if product still wants them
2. Per-spot official homepage fetch for remaining 112 (only then raise Official_Site)
3. Replace light-pass copy with source-grounded unique paragraphs
4. Do not claim Ctrip_Mac / social / outdoor forums until those pages are actually read
