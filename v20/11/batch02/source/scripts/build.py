#!/usr/bin/env python3
"""Isolated data ETL. No writes outside this batch; fuzzy matches are review-only."""
import json,re,hashlib,unicodedata,copy,itertools
from pathlib import Path
from collections import Counter
B=Path(__file__).resolve().parents[1];P=B.parents[3]
def load(p):return json.loads(p.read_text())
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[p for p in (P/'data').rglob('*.json') if 'batches' not in p.parts]+list((P/'inputs').glob('*.json'))
snapshot={str(p.relative_to(P)):sha(p) for p in protected}
write(B/'logs/protected_baseline_sha256.json',snapshot)
areas={a['name']:a['code'] for a in load(P/'inputs/areas_search_matrix.json') if a['provinceCode']=='11'}
old=load(P/'data/cities_db/11_1101.json')
metas={x:load(B/'evidence'/f'{x}.json') for x in ('scenic','museums','walks')}
raw={x:load(B/'raw'/f'{x}.json') for x in metas}
# Preserve public source anomalies literally: no corrections to 世界公园30景区 etc.
def norm(n):
 n=unicodedata.normalize('NFKC',n);n=re.sub(r'\s+','',n)
 # Anchored administrative prefixes and a single terminal scenic designation only.
 for prefix in ['北京市','北京']:
  if n.startswith(prefix):n=n[len(prefix):];break
 for area in sorted(areas,key=len,reverse=True):
  if n.startswith(area):n=n[len(area):];break
 for suffix in ['旅游景区','旅游风景区','自然风景区','风景区','文化景区','景区','旅游区']:
  if n.endswith(suffix):n=n[:-len(suffix)];break
 return n

def jac(a,b):
 a={a[i:i+2] for i in range(len(a)-1)};b={b[i:i+2] for i in range(len(b)-1)}
 return len(a&b)/len(a|b) if a|b else 0

def blind(n):
 pos=[i for i,c in enumerate(n) if '\u3400'<=c<='\u9fff'];assert len(pos)>=2
 show={pos[0],pos[-1]};return ''.join(c if i in show else '*' for i,c in enumerate(n))
def evidence(s,r):
 m=metas[s]
 return {'source_id':s,'source_row':r['row'],'source_url':m['url'],'detail_url_unfetched':r.get('detail_url'),'actual_query':m['actual_query'],'query_type':'actual_WebSearch_discovery_then_official_directory_filter','retrieved_at':m['retrieved_at'],'source_display_dates':m['source_display_dates'],'source_sha256':m['response_content_sha256'],'sanitized_sha256':m['sanitized_sha256'],'evidence_file':m['evidence_file']}
obs=[]
for s in ('scenic','museums'):
 assert [r['row'] for r in raw[s]]==list(range(1,len(raw[s])+1))
 for r in raw[s]:
  explicit=[a for a in areas if a in r['name']]
  area=r.get('area') or (explicit[0] if len(explicit)==1 else None)
  obs.append({'observation_id':f'BJ02_{s.upper()}_{r["row"]:04d}','name':r['name'],'normalized_name':norm(r['name']),'area_name':area,'area_code':areas.get(area),'area_basis':'official_area_column' if s=='scenic' else ('explicit_district_name_in_entity_name' if area else 'unknown_not_in_source'),'category':'A_rated_attraction' if s=='scenic' else 'museum_directory_entity','grade':r.get('grade'),'evidence':evidence(s,r)})
write(B/'official_source_observations.json',obs)
# Unique normalized names across two official tables can cross-link an unknown district,
# but never a known conflicting district. All original variants and source rows survive.
groups=[];links=[]
for o in obs:
 hits=[g for g in groups if g[0]['normalized_name']==o['normalized_name'] and (not o['area_code'] or not g[0]['area_code'] or g[0]['area_code']==o['area_code'])]
 if len(hits)==1:
  hits[0].append(o);links.append({'observation_id':o['observation_id'],'canonical_observation_id':hits[0][0]['observation_id'],'reason':'exact_normalized_name_unique_compatible_district'})
 else:groups.append([o])
records=[];park_exclusions=[];prior_links=[];possible=[]
for g in groups:
 o=g[0];known=[q for q in g if q['area_code']];geo=known[0] if known else o
 name=o['name'];nn=o['normalized_name']
 prior=[p for p in old if norm(p['full_name'])==nn and (not geo['area_code'] or p['area_code']==geo['area_code'])]
 # Non-park scope: official museum entities are retained even if their name contains 公园.
 park_scope=not any(q['category']=='museum_directory_entity' for q in g) and bool(re.search('公园|艺园|花园|动物园|植物园|花卉大观园|京城梨园',name))
 status='new_catalog_candidate'
 if prior:status='exact_prior_name_match_review' # cross-category overlap is not automatically a physical-identity merge
 if park_scope:
  park_exclusions.append({'observations':g,'prior_matches':[p['source_entity_id'] for p in prior],'reason':'park_type_outside_bj02_nonpark_scope'});continue
 rec={'raw_id':o['observation_id'],'source_entity_id':o['observation_id'],'spot_id':o['observation_id'],'entity_type':'spot','full_name':name,'blind_name':blind(name),'name_variants':list(dict.fromkeys(q['name'] for q in g)),'province_code':'11','province_name':'北京市','city_code':'1101','city_name':'北京市','area_code':geo['area_code'],'area_name':geo['area_name'],'area_assignment_basis':geo['area_basis'] if geo is o else 'unique_exact_normalized_name_cross_table_official_area','township_name':None,'address':None,'search_tier':'city_level','matched_search_keyword':'博物馆' if any(q['category']=='museum_directory_entity' for q in g) else 'A级旅游景区','matched_search_keywords':list(dict.fromkeys(q['category'] for q in g)),'query':o['evidence']['actual_query'],'query_type':'official_directory_filter','location':{'lat':None,'lng':None,'coord_source':None,'coordinate_status':'not_attempted_prior_batch_TLS_failure_respected'},'official_attraction_grade':next((q['grade'] for q in g if q['grade']),None),'official_categories':list(dict.fromkeys(q['category'] for q in g)),'tags':[],'tagging_status':'editorial_rules_pending_review','tagging_basis':{'rule_inputs':['official_directory_category','full_name'],'not_claimed_as_official_experience_fact':True},'summary_100w':None,'description':None,'adult_ticket_price':None,'image_url':None,'mock_weather':None,'events_and_discounts':None,'ai_strategy':None,'tag_interpretation':None,'source_url':o['evidence']['source_url'],'source_row':o['evidence']['source_row'],'source_sha256':o['evidence']['source_sha256'],'retrieved_at':o['evidence']['retrieved_at'],'source_channels':['Official_Site'],'evidence':[q['evidence'] for q in g],'observation_ids':[q['observation_id'] for q in g],'verification_status':'catalog_indexed_pending_enrich','merge_status':status,'license_status':'public_government_directory_no_explicit_reuse_license_verified','pending_enrich':['coordinates','district' if not geo['area_code'] else 'address','ticket_price','image','description','tag_review','access_and_safety','identity_review'],'evolution_stats':{'plan_mark_count':0,'review_count':0}}
 if 'museum_directory_entity' in rec['official_categories'] or re.search('博物|纪念馆|艺术馆|展览馆',name):ts=['博物馆','看展','研学','文青']
 elif re.search('寺|庙|故居|长城|陵|古城|古道|塔|遗址',name):ts=['寻古','古建','历史爱好者','怀古']
 else:ts=['摄影','打卡','体验派','随遇而安']
 rec['tags']=[{'name':t,'type':'strong' if i<2 else 'weak'} for i,t in enumerate(ts)]
 if prior:prior_links.append({'spot_id':rec['spot_id'],'matches':[p['source_entity_id'] for p in prior],'reason':'normalized_name_compatible_district_same_or_nested_entity_needs_review'})
 for p in old:
  if geo['area_code'] and p['area_code']!=geo['area_code']:continue
  pn=norm(p['full_name']);score=jac(nn,pn)
  if (nn!=pn and (score>=.55 or (min(len(nn),len(pn))>=3 and (nn in pn or pn in nn)))):
   possible.append({'spot_id':rec['spot_id'],'prior_id':p['source_entity_id'],'name':name,'prior_name':p['full_name'],'area_code':geo['area_code'],'prior_area_code':p['area_code'],'bigram_jaccard':round(score,4),'action':'review_only_no_auto_merge','geo_test':'unavailable_both_coordinates_null'})
   if rec['merge_status']=='new_catalog_candidate':rec['merge_status']='possible_prior_overlap_review'
 records.append(rec)
# Intra-batch near matches and multi-institution source rows are quarantined for additive counts.
intra=[]
for a,b in itertools.combinations(records,2):
 if a['area_code'] and b['area_code'] and a['area_code']!=b['area_code']:continue
 an,bn=norm(a['full_name']),norm(b['full_name']);score=jac(an,bn)
 if an!=bn and (score>=.55 or (min(len(an),len(bn))>=3 and (an in bn or bn in an))):
  intra.append({'a':a['spot_id'],'b':b['spot_id'],'a_name':a['full_name'],'b_name':b['full_name'],'bigram_jaccard':round(score,4),'action':'review_only_no_auto_merge'})
  for x in (a,b):
   if x['merge_status']=='new_catalog_candidate':x['merge_status']='possible_within_batch_overlap_review'
for r in records:
 if '、' in r['full_name']:
  r['merge_status']='compound_directory_entity_review'
write(B/'other_official_spots.json',records);write(B/'cities_db/11_1101.json',records)
for area,code in areas.items():
 rs=[]
 for r in records:
  if r['area_code']==code:
   a=copy.deepcopy(r);a['raw_id']='AREA_'+a['raw_id'];a['search_tier']='county_level';a['query']=a['query']+'; 官方目录区级筛选='+area;rs.append(a)
 write(B/'areas_db/11'/f'{code}.json',rs)
write(B/'logs/intra_batch_exact_crosslinks.json',links);write(B/'logs/park_scope_exclusions.json',park_exclusions);write(B/'logs/prior_exact_name_review.json',prior_links);write(B/'logs/prior_fuzzy_review.json',possible);write(B/'logs/intra_batch_fuzzy_review.json',intra)
routes=[]
for r in raw['walks']:
 nodes=r['node_sequence_text'].split('→');assert len(nodes)>=2
 routes.append({'candidate_id':f'BJ02_WALK_{r["row"]:02d}','entity_type':'route_candidate','full_route_title':r['name'],'node_sequence':nodes,'duration_days':None,'distance_m':int(re.search(r'(\d+)米',r['length_text'])[1]),'source_row':r['row'],'evidence':evidence('walks',r),'verification_status':'official_named_ordered_walk_pending_duration_and_node_linking','not_production_route_reason':'No explicit day allocation, travel time, transit links or resolved node IDs in extracted source; no invented day count. July source not a current availability guarantee.'})
write(B/'official_named_route_candidates.json',routes);write(B/'routes_seed.json',[])
write(B/'evolution_metrics.json',{r['spot_id']:{'plan_mark_count':0,'review_count':0} for r in records})
clean=[r for r in records if r['merge_status']=='new_catalog_candidate']
write(B/'promotion_candidates_NOT_MASTER.json',clean)
summary={'raw_spot_source_observations':len(obs),'scenic_source_rows':len(raw['scenic']),'museum_source_rows':len(raw['museums']),'exact_cross_table_links':len(links),'all_source_name_groups_before_scope_filter':len(groups),'park_scope_groups_excluded':len(park_exclusions),'batch_nonpark_city_directory_entities':len(records),'county_materialized_same_entities':sum(bool(r['area_code']) for r in records),'district_unresolved_city_only':sum(not r['area_code'] for r in records),'prior_city_directory_entities':len(old),'prior_county_materializations':1132,'merge_status_counts':dict(Counter(r['merge_status'] for r in records)),'unambiguous_additive_catalog_candidates_not_final_physical_identity':len(clean),'additive_county_candidates':sum(bool(r['area_code']) for r in clean),'prior_plus_unambiguous_candidate_city_count_not_promoted':len(old)+len(clean),'official_named_ordered_walk_candidates':len(routes),'production_routes':0,'county_counts':{a:sum(r['area_code']==c for r in records) for a,c in areas.items()},'important':'City and county files are projections of the same identities; never add their counts. Source rows and normalized directory groups are not guarantees of independent geographic spots. Final unique physical-net count withheld until aliases/nested sites review. No master or prior city file changed.'}
write(B/'logs/summary.json',summary)
assert all(sha(P/k)==v for k,v in snapshot.items())
print(json.dumps(summary,ensure_ascii=False,indent=2))
