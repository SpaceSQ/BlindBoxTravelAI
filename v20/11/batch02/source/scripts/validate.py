#!/usr/bin/env python3
"""Independent structural/evidence and exact projection checks. Completeness stays pending."""
import json,hashlib,re
from pathlib import Path
from collections import Counter
B=Path(__file__).resolve().parents[1];P=B.parents[3]
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
errors=[];tests=0
def check(condition,message):
 global tests
 tests+=1
 if not condition:errors.append(message)
city=load(B/'cities_db/11_1101.json');obs=load(B/'official_source_observations.json')
legal={t for c in load(P/'inputs/tags_500.json')['categories'] for t in c['tags']}
checks=[('scenic',205,'天坛公园景区','北京市延庆区双秀湖星谷景区'),('museums',203,'故宫博物院','清华大学科学博物馆'),('walks',10,'探胡同文艺，听暮鼓晨钟','敬天坛礼制，访农耕文化')]
for s,n,first,last in checks:
 rows=load(B/'raw'/f'{s}.json');m=load(B/'evidence'/f'{s}.json')
 check(len(rows)==n,f'{s} row count');check([r['row'] for r in rows]==list(range(1,n+1)),f'{s} contiguous rows')
 check(rows[0]['name']==first and rows[-1]['name']==last,f'{s} extraction endpoints')
 check(sha(B/m['evidence_file'])==m['sanitized_sha256'],f'{s} sanitized hash')
 check(m['http_status']==200 and len(m['response_content_sha256'])==64,f'{s} response provenance')
 check(m['retrieved_at'].endswith('+08:00') and bool(m['source_display_dates']),f'{s} time and date')
 for r in rows:check(set(r)<=({'row','name','detail_url','grade','area'} if s!='walks' else {'row','name','node_sequence_text','length_text'}),f'{s} no contact/user fields')
check(len({o['observation_id'] for o in obs})==408,'source observation uniqueness')
all_observation_ids={o['observation_id'] for o in obs}
used=[]
for r in city:
 rid=r['spot_id'];used+=r['observation_ids']
 check(r['source_entity_id']==rid,'stable source identity '+rid)
 check(len(r['blind_name'])==len(r['full_name']) and len(re.findall(r'[\u3400-\u9fff]',r['blind_name']))==2,'blind rule '+rid)
 check(all(t['name'] in legal for t in r['tags']),'legal tags '+rid)
 check(Counter(t['type'] for t in r['tags'])=={'strong':2,'weak':2},'tag counts '+rid)
 check(len(r['evidence'])==len(r['observation_ids']),'provenance cardinality '+rid)
 check(r['location']['lat'] is None and r['location']['lng'] is None,'no invented coordinates '+rid)
 check(all(r[k] is None for k in ['description','summary_100w','image_url','adult_ticket_price','mock_weather','ai_strategy']),'no invented enrichment '+rid)
 for e in r['evidence']:
  m=load(B/'evidence'/f'{e["source_id"]}.json');source=load(B/m['evidence_file'])
  check(source[e['source_row']-1]['name'] in r['name_variants'],'row-level name evidence '+rid)
  check(e['source_sha256']==m['response_content_sha256'],'row hash evidence '+rid)
check(len(used)==len(set(used)) and set(used)<=all_observation_ids,'no source row counted twice in batch')
check(len({r['spot_id'] for r in city})==len(city),'no duplicate batch entity IDs')
check(city==load(B/'other_official_spots.json'),'canonical and city projections identical')
area_ids=[]
for f in (B/'areas_db/11').glob('*.json'):
 rows=load(f)
 for r in rows:
  area_ids.append(r['spot_id']);check(r['area_code']==f.stem,'district shard membership')
  c=next(x for x in city if x['spot_id']==r['spot_id']);check({k:v for k,v in r.items() if k not in ['raw_id','search_tier','query']}=={k:v for k,v in c.items() if k not in ['raw_id','search_tier','query']},'county is exact projection '+r['spot_id'])
check(set(area_ids)=={r['spot_id'] for r in city if r['area_code']} and len(area_ids)==len(set(area_ids)),'county projection cardinality')
clean=load(B/'promotion_candidates_NOT_MASTER.json');check(all(r['merge_status']=='new_catalog_candidate' for r in clean),'promotion candidates quarantines')
check(len(clean)==169 and sum(bool(r['area_code']) for r in clean)==122,'additive candidate count')
walks=load(B/'official_named_route_candidates.json')
seqs=[]
for r in walks:
 check(r['entity_type']=='route_candidate' and r['duration_days'] is None,'no invented production route')
 check(len(r['node_sequence'])>=2,'ordered real nodes')
 check('→'.join(r['node_sequence'])==load(B/'raw/walks.json')[r['source_row']-1]['node_sequence_text'],'route node extraction')
 seqs.append(tuple(r['node_sequence']))
check(len(seqs)==len(set(seqs)),'no duplicate published node sequences')
check(load(B/'routes_seed.json')==[],'production routes honest zero')
for rel,h in load(B/'logs/protected_baseline_sha256.json').items():check(sha(P/rel)==h,'protected original unchanged '+rel)
report={'checks':tests,'structural_errors':errors,'error_count':len(errors),'status':'PASS' if not errors else 'FAIL','not_a_completeness_pass':True,'quality_warnings':['338 thin nonpark directory entities, not guaranteed distinct geographic spots','172 unknown districts; all coordinates, prices, images, prose and access status pending','169 conservative lexical additive candidates; final physical-net count not certified','169 held for exact prior/nested/alias/compound review; no automatic old-data merges','10 official ordered walking candidates; 0 production Routes','No explicit reuse license verified; no official directory text or images relicensed','No Google/Baidu matrix run, app/social access or geocoding attempted']}
(B/'logs/validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
