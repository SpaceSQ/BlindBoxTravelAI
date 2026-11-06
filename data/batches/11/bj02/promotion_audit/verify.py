#!/usr/bin/env python3
"""Independent structural/evidence checks of conservative BJ02 snapshot, no writes."""
import argparse,hashlib,json
from pathlib import Path

def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify(target):
 T=Path(target);A=T/'data/batches/11/bj02/promotion_audit';S=Path(load(T/'PROMOTED-SNAPSHOT.json')['source_snapshot']);checks=0
 def check(v,msg):
  nonlocal checks
  checks+=1
  if not v:raise AssertionError(msg)
 snap=load(A/'source_snapshot_sha256.json')
 for name,h in snap.items():check(sha(S/name)==h,'Source changed: '+name)
 base=load(S/'data/national_spots_master.json');master=load(T/'data/national_spots_master.json');bm={r['spot_id']:r for r in base};mm={r['spot_id']:r for r in master};city=load(T/'data/cities_db/11_1101.json');new=load(A/'promoted_catalog_entities.json');dec=load(A/'all_338_decisions.json');report=load(A/'report.json');metrics=load(T/'data/evolution_metrics.json')
 check(len(mm)==len(master),'Duplicate master spot ID');check(len({r['source_entity_id'] for r in master})==len(master),'Duplicate source entity ID');check(set(bm)<=set(mm),'Lost baseline IDs');check(len(master)==len(base)+len(new),'Incorrect increment');check(len(city)==len(master),'City/master count mismatch');check({r['source_entity_id'] for r in city}=={r['source_entity_id'] for r in master},'City/master identity mismatch');check(set(metrics)==set(mm),'Metrics IDs differ')
 for r in base:
  for k,v in r.items():check(mm[r['spot_id']][k]==v,'Original field altered: '+r['spot_id']+' '+k)
 check(len(dec)==338 and len({a['source_entity_id'] for a in dec})==338,'Decision coverage')
 check(sum(a['in_original_169_candidate_set'] for a in dec)==169,'Original candidate denominator')
 check(len(load(A/'review_remaining.json'))+len(new)+len(load(A/'existing_catalog_links.json'))==338,'Disposition totals')
 obs=load(T/'data/batches/11/bj02/official_source_observations.json');disp=load(A/'all_408_observation_dispositions.json');check(len(disp)==408 and set(disp)=={o['observation_id'] for o in obs},'Observation lost');used=[oid for d in dec for oid in d['observation_ids']];check(len(used)==len(set(used)),'Observation linked twice')
 for r in new:
  check(r['spot_id'] in mm,'New ID missing');check(r['evolution_stats']=={'plan_mark_count':0,'review_count':0} and metrics[r['spot_id']]==r['evolution_stats'],'Initial metrics not zero');check(r['location']['lat'] is None and r['location']['lng'] is None,'Invented coordinates');check(not r['geographic_net_addition_verified'] and not r['eligible_for_blindbox_display'],'False production/geographic assertion')
  for k in ['description','summary_100w','image_url','adult_ticket_price','ai_strategy','tag_interpretation','mock_weather','events_and_discounts']:check(r[k] is None,'Unsupported display field: '+k)
  if r.get('area_code'):check(bool(r['official_area_evidence']),'No explicit district evidence')
  for e in r['official_area_evidence']:
   check(e['area_code']==r['area_code'] and e['area_name_verbatim']==r['area_name'],'Area mismatch');check(sha(T/e['sanitized_evidence_file'])==e['sanitized_sha256'],'Raw list hash mismatch');raw=load(T/e['sanitized_evidence_file']);item=next(x for x in raw if x['row']==e['source_row']);check(item['name']==e['official_name_verbatim'],'Name evidence mismatch');check(item.get('area')==r['area_name'] or r['area_name'] in item['name'],'No literal official district support')
  if r.get('parent_spot_id'):
   check(r['parent_spot_id'] in mm,'Dangling parent');p=mm[r['parent_spot_id']];check(any(x['spot_id']==r['spot_id'] for x in p['sub_spots']),'Missing reverse sub_spots');check(p['spot_id']!=r['spot_id'],'Self parent');check(r['parent_relation_evidence']['relation']=='catalog_child_of','Wrong child relation')
 for a in load(A/'existing_catalog_links.json'):
  check(a['canonical_spot_id'] in bm,'Existing link created new ID');check(a['source_entity_id'] not in {r['source_entity_id'] for r in new},'Alias duplicated as new master');check(any(x['source_entity_id']==a['source_entity_id'] for x in mm[a['canonical_spot_id']]['bj02_catalog_evidence_links']),'Missing original alias evidence')
 index=load(T/'data/areas_db/index.json');area_total=0;area_ids=[]
 for i in index:
  rows=load(T/i['path']);area_total+=len(rows);area_ids += [r['spot_id'] for r in rows];check(i['count']==len(rows),'County index count');check(i['shortfall']==max(0,i['target']-len(rows)),'County shortfall')
  for r in rows:check(r['area_code']==i['area_code'] and r['search_tier']=='county_level','Wrong county projection');check(r['spot_id'] in mm and r['source_entity_id']==mm[r['spot_id']]['source_entity_id'],'County identity changed')
 check(len(area_ids)==len(set(area_ids)),'Identity assigned to two districts');check(area_total==sum(bool(r.get('area_code')) for r in city),'Unknown district incorrectly materialized');check(all(r['spot_id'] not in area_ids for r in new if not r['area_code']),'Unknown district inferred from parent')
 for i in load(T/'data/cities_db/index.json'):check(i['count']==len(city),'City index count')
 details=load(A/'details_manifest.json');check(len(details)==len({d['requested_url'] for d in details})<50,'Unbounded detail research');check(len(details)==report['official_detail_unique_urls_actually_requested'],'Detail count mismatch')
 for d in details:
  check(load(A/'detail_evidence'/(d['requested_url'].rsplit('/',1)[-1]+'.json'))==d,'Detail manifest mismatch');check(d['display_image_url'] is None and not d['image_reuse_license_verified'],'Unlicensed image propagated')
 routes=load(A/'route_node_review.json');original=load(T/'data/batches/11/bj02/official_named_route_candidates.json');check(len(routes)==10,'Route candidates lost');check(load(T/'data/batches/11/bj02/routes_seed.json')==[],'Invented formal route');check(sha(T/'data/national_routes_master.json')==sha(S/'data/national_routes_master.json'),'Baseline routes changed')
 for r,o in zip(routes,original):
  check(r['duration_days'] is None and not r['formal_route_promoted'],'Invented one-day assignment');check([n['source_node_text'] for n in r['nodes_in_source_order']]==o['node_sequence'],'Source route order changed')
 check(report['actual_promoted_new_catalog_entities']==len(new) and report['result_master_catalog_count']==len(master),'Report count mismatch');check(report['geographic_net_additions'] is None,'Directory sold as physical net');check(report['remaining_review_entities']==sum(a['outcome']=='review' for a in dec),'Review count mismatch')
 # Existing scripts and inputs never replaced, even inside the output snapshot.
 for p in list((S/'scripts').rglob('*'))+list((S/'inputs').rglob('*')):
  if p.is_file():check(sha(p)==sha(T/p.relative_to(S)),'Original dedup/code/input modified')
 return {'checks_passed':checks,'structure_errors':0,'new_catalog_entities':len(new),'master_catalog_entities':len(master),'review_remaining':report['remaining_review_entities'],'quality_warnings':report['warnings']}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--target',default='/workspace/blindbox-travel-v20-promoted');a=p.parse_args();print(json.dumps(verify(a.target),ensure_ascii=False,indent=2))
