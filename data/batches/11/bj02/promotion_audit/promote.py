#!/usr/bin/env python3
"""Standalone, offline, conservative BJ02 directory projection, NOT geographic dedup.
Writes only a separate snapshot. Never calls Git, a Mac, a geocoder or the network.
"""
import argparse,copy,hashlib,json,re,shutil,unicodedata
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
DEFAULT_SOURCE=Path('/workspace/blindbox-travel-v20')
DEFAULT_TARGET=Path('/workspace/blindbox-travel-v20-promoted')

def load(p):return json.loads(Path(p).read_text())
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def strict_name(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s or '')).casefold()
DISTRICTS=['东城区','西城区','朝阳区','丰台区','石景山区','海淀区','门头沟区','房山区','通州区','顺义区','昌平区','大兴区','怀柔区','平谷区','密云区','延庆区']
SUFFIXES=['旅游风景区','自然风景区','旅游景区','风景名胜区','文化景区','风景区','景区','旅游区']
def proper_key(s):
 s=strict_name(s)
 for pref in ['北京市','北京']:
  if s.startswith(pref):s=s[len(pref):];break
 for pref in sorted(DISTRICTS,key=len,reverse=True):
  if s.startswith(pref):s=s[len(pref):];break
 for suf in SUFFIXES:
  if s.endswith(suf):s=s[:-len(suf)];break
 return s

def containment_key(s):
 # Review trigger only. Never an identity key, and NEVER fall back to a generic key.
 s=proper_key(s)
 for suf in ['国家森林公园','国家湿地公园','郊野公园','森林公园','湿地公园','公园']:
  if s.endswith(suf):s=s[:-len(suf)];break
 return s if len(s)>=2 else ''

def compatible_area(a,b):return bool(a.get('area_code') and b.get('area_code') and a['area_code']==b['area_code'])
def identity_action(a,b,official_identity_assertion=False):
 """No missing-coordinate, synonym or name-only auto-merge, even same district."""
 if not proper_key(a.get('full_name')) or not proper_key(b.get('full_name')):return 'review_empty_key'
 if a.get('area_code') and b.get('area_code') and a['area_code']!=b['area_code']:return 'review_cross_district'
 if official_identity_assertion:return 'link_official_catalog_assertion_not_geo_merge'
 if not all(x.get('location',{}).get(k) is not None for x in [a,b] for k in ['lat','lng']):return 'review_missing_coordinates'
 return 'review_no_automatic_identity_merge'

def collision_flags(r,baseline,allrows):
 a=containment_key(r['full_name']);out=[]
 if not a:return [{'reason':'empty_or_generic_key'}]
 for other in baseline+allrows:
  if other['source_entity_id']==r['source_entity_id']:continue
  b=containment_key(other['full_name'])
  if not b:continue
  # Exact proper names in different districts are not merged; uncertain identity stays review.
  if strict_name(r['full_name'])==strict_name(other['full_name']) or proper_key(r['full_name'])==proper_key(other['full_name']):
   out.append({'reason':'exact_name_identity_review','source_entity_id':other['source_entity_id'],'full_name':other['full_name'],'area_code':other.get('area_code')});continue
  if r.get('area_code') and other.get('area_code') and r['area_code']!=other['area_code']:continue
  if a in b or b in a:
   out.append({'reason':'containment_or_shared_park_root_review','source_entity_id':other['source_entity_id'],'full_name':other['full_name'],'area_code':other.get('area_code')})
 return out

def area_evidence(r,obs):
 out=[]
 for oid in r['observation_ids']:
  o=obs[oid]
  if o.get('area_code')!=r.get('area_code') or not o.get('area_code'):continue
  if o['area_basis']=='official_area_column' or (o['area_basis']=='explicit_district_name_in_entity_name' and o['area_name'] in o['name']):
   out.append({'observation_id':oid,'official_name_verbatim':o['name'],'area_name_verbatim':o['area_name'],'area_code':o['area_code'],'area_basis':o['area_basis'],'source_url':o['evidence']['source_url'],'source_row':o['evidence']['source_row'],'sanitized_evidence_file':'data/batches/11/bj02/'+o['evidence']['evidence_file'],'sanitized_sha256':o['evidence']['sanitized_sha256']})
 return out

UMBRELLA={'BJ02_SCENIC_0032':'umbrella_resort_and_child_park_scope_review','BJ02_SCENIC_0046':'multi_site_township_scenic_scope_review','BJ02_SCENIC_0075':'multi_site_landscape_corridor_scope_review','BJ02_SCENIC_0119':'multi_segment_historic_trail_scope_review','BJ02_SCENIC_0123':'multi_village_scenic_scope_review'}

def run(source,target,evidence_dir):
 source=Path(source).resolve();target=Path(target).resolve();evidence_dir=Path(evidence_dir).resolve()
 assert source!=target and source not in target.parents and target not in source.parents, 'Separate non-nested target required'
 assert (source/'data/cities_db/11_1101.json').exists()
 # Protect the entire source snapshot (not just master). No writes occur there.
 protected={str(p.relative_to(source)):sha(p) for p in source.rglob('*') if p.is_file() and '.venv' not in p.parts and '.git' not in p.parts}
 B=source/'data/batches/11/bj02';records=load(B/'other_official_spots.json');base=load(source/'data/national_spots_master.json');obs={x['observation_id']:x for x in load(B/'official_source_observations.json')};candidates=load(B/'promotion_candidates_NOT_MASTER.json');cids={r['source_entity_id'] for r in candidates};assert len(cids)==169 and len(base)==1136 and len(records)==338
 bybase={x['source_entity_id']:x for x in base};byrec={x['source_entity_id']:x for x in records}
 manual=load(evidence_dir/'manual_identity_decisions.json');details=load(evidence_dir/'details_manifest.json');byurl={d['requested_url']:d for d in details}
 assert len(byurl)<50
 existing={d['source_entity_id']:d for d in manual['existing_destination_links']};children={d['source_entity_id']:d for d in manual['child_venues']};distinct={d['source_entity_id']:d for d in manual.get('distinct_named_venues',[])}
 for m in list(existing.values())+list(children.values())+list(distinct.values()):
  r=byrec[m['source_entity_id']];assert m.get('parent_source_entity_id',m.get('compared_prior_source_entity_id')) in bybase
  d=byurl[m['detail_url']];assert d.get('http_status')==200 and d['fetch_state']=='usable_identity_page' and m['quote'] in d['identity_excerpt_quotes']
  assert m['detail_url'] in [e['detail_url_unfetched'] for e in r['evidence']]
  if m['relation']=='same_official_directory_destination':assert compatible_area(r,bybase[m['parent_source_entity_id']])
 marker=target/'PROMOTED-SNAPSHOT.json'
 if target.exists():assert marker.exists() and load(marker)['source_snapshot']==str(source),'Refuse to overwrite unrelated target'
 else:
  shutil.copytree(source,target,ignore=shutil.ignore_patterns('.venv','.git'))
 # Keep original scripts/dedup untouched. All new work is in an isolated directory.
 delivery=target/'data/batches/11/bj02/promotion_audit';delivery.mkdir(parents=True,exist_ok=True)
 for name in ['detail_plan.json','details_manifest.json','manual_identity_decisions.json']:
  
  if (evidence_dir/name).resolve()!=(delivery/name).resolve():shutil.copy2(evidence_dir/name,delivery/name)
 if (evidence_dir/'detail_evidence').resolve()!=(delivery/'detail_evidence').resolve():shutil.copytree(evidence_dir/'detail_evidence',delivery/'detail_evidence',dirs_exist_ok=True)
 write(delivery/'source_snapshot_sha256.json',protected)
 audit=[];promoted=[];linked=[]
 exact_literal=sum(any(strict_name(r['full_name'])==strict_name(b['full_name']) for b in base) for r in records)
 for r0 in records:
  r=copy.deepcopy(r0);sid=r['source_entity_id'];ae=area_evidence(r,obs)
  a={'source_entity_id':sid,'observation_ids':r['observation_ids'],'full_name':r['full_name'],'original_merge_status':r['merge_status'],'in_original_169_candidate_set':sid in cids,'area_code':r['area_code'],'area_name':r['area_name'],'official_area_evidence':ae,'detail_evidence_refs':[f'data/batches/11/bj02/promotion_audit/detail_evidence/{u.rsplit("/",1)[-1]}.json' for u in dict.fromkeys(e['detail_url_unfetched'] for e in r['evidence']) if u in byurl],'geographic_net_addition_verified':False}
  if sid in existing:
   m=existing[sid];a.update(outcome='linked_existing_catalog',reason='individually_reviewed_official_catalog_identity',identity_assertion=m,canonical_spot_id=bybase[m['parent_source_entity_id']]['spot_id']);linked.append(a)
  else:
   reasons=[];flags=[]
   if sid not in children and sid not in distinct:
    if sid not in cids:reasons.append('original_overlap_or_alias_unresolved')
    if not r['area_code'] or not ae:reasons.append('no_explicit_official_district_city_review_only')
    if sid in UMBRELLA:reasons.append(UMBRELLA[sid])
    if re.search('、|管理处|管理中心|保护中心|保管所|文化艺术中心',r['full_name']):reasons.append('administrative_or_compound_institution_scope_review')
    if len(proper_key(r['full_name']))<3:reasons.append('proper_name_too_generic')
    flags=collision_flags(r,base,records)
    if flags:reasons.append('additional_exact_or_containment_collision_review')
   else:
    a['manual_distinct_venue_assertion']=distinct[sid] if sid in distinct else None
    if sid in children:a['child_assertion']=children[sid]
    # No inferred district. A firm child identity can be retained in city-only catalog.
    if sid in children:assert r['full_name']!=bybase[children[sid]['parent_source_entity_id']]['full_name']
    if sid in distinct:
     assert r['area_code'] and ae
     dm=distinct[sid];other=obs[dm['contrast_official_observation_id']];assert other['name']!=r['full_name'] and other['area_code']==r['area_code']
     assert dm['contrast_detail_url']!=dm['detail_url'] and byurl[dm['contrast_detail_url']]['fetch_state']=='usable_identity_page'
   if reasons:a.update(outcome='review',reason=reasons[0],review_reasons=reasons,collision_evidence=flags)
   else:
    r['spot_id']='SP_'+sid;r['raw_id']='CITY_'+sid;r['raw_ids']=['CITY_'+sid]+(['AREA_'+sid] if r['area_code'] else []);r['search_tiers']=['city_level']+(['county_level'] if r['area_code'] else [])
    r['verification_status']='catalog_identity_reviewed_pending_enrich';r['merge_status']='conservative_catalog_increment_not_geographic_net';r['catalog_promotion_basis']='official_unique_named_venue_and_explicit_district_no_detected_collision' if sid not in children else 'official_distinct_named_child_venue_preserved'
    
    if sid in distinct:r['catalog_promotion_basis']='individually_reviewed_distinct_official_catalog_venue';r['distinct_venue_evidence']=distinct[sid]
    r['official_area_evidence']=ae;r['geographic_net_addition_verified']=False;r['eligible_for_blindbox_display']=False
    r['verified_fields']=['official_directory_name','source_row_identity']+(['official_district'] if ae else [])
    r['pending_enrich']=[x for x in r['pending_enrich'] if x!='identity_review']+['geographic_identity_and_footprint']
    r['evolution_stats']={'plan_mark_count':0,'review_count':0}
    if sid in children:
     m=children[sid];r['parent_spot_id']=bybase[m['parent_source_entity_id']]['spot_id'];r['catalog_relation']='child_of';r['parent_relation_evidence']=m;r['verified_fields'].append('official_parent_locative_statement')
    else:r['catalog_relation']='named_catalog_venue_geographic_relations_unverified'
    a.update(outcome='promoted_new_catalog',reason=r['catalog_promotion_basis'],canonical_spot_id=r['spot_id']);promoted.append(r)
  audit.append(a)
 # Existing source IDs/metrics remain, and alias observations are attached without duplicate master rows.
 master=copy.deepcopy(base);bm={r['source_entity_id']:r for r in master}
 for a in linked:
  r=byrec[a['source_entity_id']];p=bm[a['identity_assertion']['parent_source_entity_id']]
  p.setdefault('bj02_catalog_evidence_links',[]).append({'source_entity_id':r['source_entity_id'],'observation_ids':r['observation_ids'],'name_variants':r['name_variants'],'evidence':r['evidence'],'identity_assertion':a['identity_assertion']})
 for r in promoted:
  if r.get('parent_spot_id'):
   pid=children[r['source_entity_id']]['parent_source_entity_id'];bm[pid].setdefault('sub_spots',[]).append({'spot_id':r['spot_id'],'source_entity_id':r['source_entity_id'],'full_name':r['full_name'],'relationship':'catalog_child_of','evidence_ref':f'data/batches/11/bj02/promotion_audit/detail_evidence/{children[r["source_entity_id"]]["detail_url"].rsplit("/",1)[-1]}.json'})
 master+=promoted
 write(target/'data/national_spots_master.json',master)
 # City/county are projections of identities, never added to master as independent places.
 def project(m,tier):
  x=copy.deepcopy(m);sid=x['source_entity_id'];x['raw_id']=('CITY_' if tier=='city_level' else 'AREA_')+sid;x['search_tier']=tier
  return x
 city=[project(x,'city_level') for x in master if x['city_code']=='1101'];write(target/'data/cities_db/11_1101.json',city)
 index=load(source/'data/cities_db/index.json')
 for row in index:
  if row['city_code']=='1101':row['count']=len(city);row['shortfall']=max(0,row['target']-row['count'])
 write(target/'data/cities_db/index.json',index)
 ai=load(source/'data/areas_db/index.json')
 for row in ai:
  rs=[project(x,'county_level') for x in city if x.get('area_code')==row['area_code']];write(target/row['path'],rs);row['count']=len(rs);row['shortfall']=max(0,row['target']-len(rs))
 write(target/'data/areas_db/index.json',ai)
 metrics=load(source/'data/evolution_metrics.json')
 for r in promoted:metrics.setdefault(r['spot_id'],{'plan_mark_count':0,'review_count':0})
 write(target/'data/evolution_metrics.json',metrics)
 # All original route texts preserved; only literal/anchored exact node lookups, no duration invention.
 routes=load(B/'official_named_route_candidates.json');rr=[]
 for r in routes:
  nodes=[]
  for n in r['node_sequence']:
   hits=[m['spot_id'] for m in master if proper_key(m['full_name']) and proper_key(m['full_name'])==proper_key(n)]
   nodes.append({'source_node_text':n,'possible_master_ids':hits,'resolution':'unique_exact_catalog_name_not_geographic_validation' if len(hits)==1 else 'ambiguous_or_unresolved','resolved_spot_id':hits[0] if len(hits)==1 else None})
  rr.append({'candidate_id':r['candidate_id'],'full_route_title':r['full_route_title'],'duration_days':None,'formal_route_promoted':False,'reason':'source_has_no_explicit_day_count_or_daily_allocation_or_complete_transit; no estimated one-day conversion','nodes_in_source_order':nodes,'evidence':r['evidence']})
 write(delivery/'route_node_review.json',rr)
 detail_reviews=[];audit_byid={a['source_entity_id']:a for a in audit}
 for plan in load(evidence_dir/'detail_plan.json'):
  sid=plan['source_entity_id'];d=byurl[plan['url']];a=audit_byid[sid]
  note=manual.get('detail_case_notes',{}).get(sid)
  if not note:note=(a.get('identity_assertion') or a.get('child_assertion') or {}).get('basis') or ('Official named directory venue retained with literal district evidence; geographic relations remain unverified.' if a['outcome']=='promoted_new_catalog' else 'Actual official linked page read, but identity/scope is not resolved by title or shared URL alone. Keep review.')
  detail_reviews.append({'source_entity_id':sid,'directory_name':plan['full_name'],'official_detail_url':plan['url'],'actual_page_title':d.get('title'),'fetch_state':d['fetch_state'],'http_status':d.get('http_status'),'identity_quotes':d.get('identity_excerpt_quotes',[]),'outcome':a['outcome'],'individual_review_note':note,'not_a_2026_opening_or_price_guarantee':True})
 write(delivery/'individual_detail_identity_review.json',detail_reviews)
 write(delivery/'governance_not_spatial_identity.json',manual.get('governance_not_geographic_identity',[]))
 write(delivery/'all_338_decisions.json',audit);write(delivery/'promoted_catalog_entities.json',promoted);write(delivery/'review_remaining.json',[a for a in audit if a['outcome']=='review']);write(delivery/'existing_catalog_links.json',linked)
 # Complete disposition of every original observation, including excluded park scope.
 omap={oid:{'source_entity_id':a['source_entity_id'],'outcome':a['outcome'],'canonical_spot_id':a.get('canonical_spot_id')} for a in audit for oid in a['observation_ids']}
 for g in load(B/'logs/park_scope_exclusions.json'):
  for o in g['observations']:
   assert o['observation_id'] not in omap;omap[o['observation_id']]={'outcome':'original_park_scope_exclusion_retained','prior_matches':g['prior_matches']}
 assert set(omap)==set(obs)
 write(delivery/'all_408_observation_dispositions.json',omap)
 outcome=Counter(a['outcome'] for a in audit);candidate_outcomes=Counter(a['outcome'] for a in audit if a['in_original_169_candidate_set']);review=[a for a in audit if a['outcome']=='review']
 report={'scope':'official_directory_increment_not_verified_independent_geographic_spots','original_baseline_catalog_count':1136,'batch_official_observations':408,'batch_nonpark_entities':338,'original_lexical_candidate_count_NOT_net':169,'original_candidate_outcomes':dict(candidate_outcomes),'actual_promoted_new_catalog_entities':len(promoted),'promoted_from_original_169':sum(r['source_entity_id'] in cids for r in promoted),'promoted_from_original_review_set':sum(r['source_entity_id'] not in cids for r in promoted),'confirmed_catalog_links_existing_no_new_identity':len(linked),'literal_full_name_overlap_with_prior_count':exact_literal,'original_normalized_exact_overlap_review_count':17,'new_child_venues_preserved':sum(r.get('catalog_relation')=='child_of' for r in promoted),'promoted_city_only_unknown_district':sum(not r['area_code'] for r in promoted),'promoted_with_explicit_official_district':sum(bool(r['area_code']) for r in promoted),'remaining_review_entities':len(review),'review_primary_reason_counts':dict(Counter(a['reason'] for a in review)),'review_all_reason_counts_nonadditive':dict(Counter(z for a in review for z in a['review_reasons'])),'result_master_catalog_count':len(master),'result_city_count':len(city),'result_county_projection_total':sum(x['count'] for x in ai),'result_county_unknown_city_only':sum(not r.get('area_code') for r in city),'official_detail_unique_urls_actually_requested':len(details),'official_detail_usable_identity_pages':sum(d['fetch_state']=='usable_identity_page' for d in details),'official_detail_fetch_failures':sum(d['fetch_state']!='usable_identity_page' for d in details),'last_official_detail_read_at_Asia_Shanghai':max(d['retrieved_at'] for d in details),'route_candidates_retained':len(routes),'new_formal_routes':0,'route_nodes_exact_unique_catalog_matches':sum(n['resolved_spot_id'] is not None for r in rr for n in r['nodes_in_source_order']),'route_nodes_total':sum(len(r['nodes_in_source_order']) for r in rr),'verified_coordinate_count_new':0,'verified_ticket_prices_new':0,'licensed_images_new':0,'geographic_net_additions':None,'geographic_net_additions_reason':'No coordinates/footprint validation. Child venues overlap parent geography. Directory counts must never be sold as geographic net counts.','warnings':['Not production-ready: all new descriptions, prices, coordinates and licensed images remain null.','Original 169 candidate count is not net additions; use actual catalog increment only.','Unknown district child venues stay city-only; no parent district inference.','Shared detail URL alone never authorizes alias/office/child merging.','All unmatched observations and excluded park-scope records retained.','No Mac, Git, network or destructive dedup performed by promote.py.']}
 write(delivery/'report.json',report)
 write(marker,{'source_snapshot':str(source),'mode':'separate_box_snapshot_no_git_no_mac','audit':'data/batches/11/bj02/promotion_audit/report.json'})
 assert all(sha(source/k)==v for k,v in protected.items()),'Source snapshot changed'
 return report

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',default=str(DEFAULT_SOURCE));a.add_argument('--target',default=str(DEFAULT_TARGET));a.add_argument('--evidence-dir',default=str(HERE));args=a.parse_args();print(json.dumps(run(args.source,args.target,args.evidence_dir),ensure_ascii=False,indent=2))
