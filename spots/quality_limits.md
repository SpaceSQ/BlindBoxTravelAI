# BlindBoxTravelAI Phase-1 Spots Quality Limits

Generated_at: 2026-11-06T17:21:48+08:00 (Asia/Shanghai)

## Counts
- spots: 116
- provinces covered: 34 / 34
- provinces: 上海市, 云南省, 内蒙古自治区, 北京市, 台湾省, 吉林省, 四川省, 天津市, 宁夏回族自治区, 安徽省, 山东省, 山西省, 广东省, 广西壮族自治区, 新疆维吾尔自治区, 江苏省, 江西省, 河北省, 河南省, 浙江省, 海南省, 湖北省, 湖南省, 澳门特别行政区, 甘肃省, 福建省, 西藏自治区, 贵州省, 辽宁省, 重庆市, 陕西省, 青海省, 香港特别行政区, 黑龙江省

## Tags inventory honesty
- tags_500.json declared total_count: 500
- actual tag entries: 475
- unique tags used as vocabulary: 471
- **Did not invent filler tags to pad to 500.** See `tags_actual_inventory.json`.

## Source channels (actually read)
- Counts: {"Official_Site": 116, "Search_Engine": 116}
- **Ctrip_Mac: NOT claimed** (no Mac Ctrip app scrape this run)
- **Mafengwo_Doyouhike / Xiaohongshu_Douyin: NOT claimed** (no authenticated social/outdoor crawl this run)
- Used: OSM Nominatim geocoding + public MCT/Xinhua 5A list pages + selective official pages (e.g. dpm.org.cn for 故宫票务) + zh.wikipedia topic URLs as background refs

## Verified vs null
- adult_ticket_price verified numeric: 1 (others null + price_note)
- image_url null (unverified): 116 / 116 — refused to invent CDN links
- mock_weather: seasonal climate references with evidence_basis, not live weather
- events_and_discounts: default「暂未核实到当季优惠，请出发前复核」unless verified

## Mask / leak rules
- blind_name: exactly 2 literal Han, all other positions `*`, length==full_name
- description 200-300 / summary 80-120 targeted; strong tags each have 【tag】 interpretation
- sensitive_terms + full_name leak-guard applied on visible copy

## Geocode caveats
- Some 5A bundled names resolved via shorter OSM queries (alt=true in cache)
- 太阳岛 query snapped near 冰雪大世界 on island precinct — acceptable precinct-level seed, refine later
- 长白山 resolved near 池北/天池管理区 — precinct-level

## Validator wiring
- Also mirrored to `data/spots_seed.json` for `scripts/validate_blindbox_seed.py`
- routes_seed.json may be empty stub until routes agent delivers
- No git push performed


## Editorial repair addendum
- See `editorial_review.md` for honest scope (deep vs light).
- Channels now: Official_Site≈4 spots, Search_Engine=116; wikipedia/OSM demoted from Official_Site.
- No git push; routes untouched.

