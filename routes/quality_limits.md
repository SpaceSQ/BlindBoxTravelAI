# Routes correction gaps — 2026-11-06T17:20:00+08:00 (Asia/Shanghai)

## Counts
- routes: **60** (was 55; added RT056–RT060)
- duration histogram: {1: 22, 2: 21, 3: 9, 4: 2, 5: 1, 6: 2, 7: 3}
- 6+ day routes: 5 (7-day: 3)
- source_ref statuses: {'reachable_http_ok': 59, 'ref_source_unverified': 41}
- spot_sensitive_terms entries: 107

## Corrections done
1. Long routes RT056 北疆7日 / RT057 川西7日 / RT058 滇西北7日 / RT059 东北6日 / RT060 港澳6日
2. strong_tags_optional prose→synthesis_note; tags filtered to tags_500 exact names
3. blind_highlights rewritten + sensitive alias blocklist
4. curl-based ref_status on source_refs

## Impossible / blocked this box
- Cannot prove all source URLs globally reachable (egress 500/TLS/403/404)
- Cannot Mac-automate Ctrip or login-wall social
- Cannot bind spot_ids without Spots library merge

## advice_revalidate_before_release = true
Parent must re-curl failing domains from Mac, remap spot_ids, and human-edit templated highlights before seed publish.
