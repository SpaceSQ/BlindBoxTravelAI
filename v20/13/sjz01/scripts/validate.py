from pathlib import Path
import json,hashlib,re
B=Path(__file__).resolve().parents[1];D=B/'data/search_batches/13/shijiazhuang_1301_batch01'
def load(n):return json.loads((D/n).read_text())
checks=0
def check(b,msg):
 global checks
 checks+=1
 if not b:raise AssertionError(msg)
rs=load('city_candidates.json');obs=load('source_observations.json');oo={o['observation_id']:o for o in obs};ss=load('source_manifest.json');sm={s['source_id']:s for s in ss};ar=json.loads((B/'inputs/shijiazhuang_areas_matrix.json').read_text());aa={a['code']:a for a in ar};tags={t for c in json.loads((B/'inputs/tags_500.json').read_text())['categories'] for t in c['tags']}
for m in ss:check(hashlib.sha256((B/m['raw_path']).read_bytes()).hexdigest()==m['sha256'],'raw sha')
check(len(oo)==len(obs),'unique observation ids');check(len({r['raw_id'] for r in rs})==len(rs),'unique ids')
check(len(rs)==205,'exact candidates');check(len(obs)==221,'official observations');check(len(load('county_candidates.json'))==201,'county projections')
for r in rs:
 check(r['province_code']=='13' and r['city_code']=='1301','admin scope')
 check(r['location']=={'lat':None,'lng':None,'coord_source':None},'no fabricated coords')
 check(all(r[k] is None for k in ['adult_ticket_price','image_url','summary_100w','description','search_query','matched_search_keyword']),'unknown nullable fields')
 check(len(r['blind_name'])==len(r['full_name']),'blind length')
 check(sum(c!='*' for c in r['blind_name'])==min(2,sum('\u4e00'<=c<='\u9fff' for c in r['full_name'])),'two blind characters')
 check(all(t['name'] in tags for t in r['tags']),'fresh whitelist')
 check(all(o in oo for o in r['source_observation_ids']),'evidence ids')
 for id in r['source_observation_ids']:
  o=oo[id];check(o['full_name']==r['full_name'],'exact name evidence');check(o['source_id'] in sm,'source known');check(o['source_url'].startswith('https://'),'url known')
 if r['area_code']:
  check(r['area_code'] in aa and r['area_name']==aa[r['area_code']]['name'],'area code/name match')
  check(any(oo[id]['area_code']==r['area_code'] for id in r['source_observation_ids']),'not assigned from query')
 check(not any(re.search('phone|contact|email|handle',k,re.I) for k in r),'no structured contacts')
for o in obs:check(not any(re.search(r'1[3-9][0-9]{9}|0311[-－][0-9]{7,8}',str(v)) for v in o['source_excerpt'].values()),'no phone in parsed evidence')
q=load('query_plan.json');check(len(q)==349,'all matrix plan');check(sum(x['phase']=='initial_41' for x in q)==41,'initial scope');check(sum(x['status']=='attempted_no_results' for x in q)==1,'only one executed combination');check(sum(len(x['engines_attempted']) for x in q)==2,'two actual engine requests');check(len(load('route_candidates.json'))==0,'no fabricated routes')
for a in ar:check(sum(x['unit_code']==a['code'] for x in q)==14,'14 per unit plan')
result={'status':'passed','assertions':checks,'official_observations':len(obs),'city_candidate_names':len(rs),'county_catalog_projections':201,'fresh_tag_whitelist_unique':len(tags),'routes':0,'search_result_pages':0,'note':'Offline schema/evidence and raw SHA checks, not independent physical-entity verification.'}
(D/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
