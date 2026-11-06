"""Offline reproducible official-catalog candidate builder; no repository writes."""
from pathlib import Path
import json,hashlib,re,itertools,difflib
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import openpyxl
B=Path(__file__).resolve().parents[1];D=B/'data/search_batches/13/shijiazhuang_1301_batch01';D.mkdir(parents=True,exist_ok=True)
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def norm(x):return re.sub(r'\s+','',str(x or '')).strip()
areas=[a for a in json.loads((B/'inputs/areas_search_matrix.json').read_text()) if a['cityCode']=='1301']
city=next(c for c in json.loads((B/'inputs/cities_search_matrix.json').read_text()) if c['code']=='1301')
allowed={t for c in json.loads((B/'inputs/tags_500.json').read_text())['categories'] for t in c['tags']}
selected={'130123','130131'}
plan=[]
for unit,tier in [(city,'city_level')]+[(a,'area_level') for a in areas]:
 for q in unit['searchQueries']:
  initial=unit['code']=='1301' or unit['code'] in selected
  plan.append({'query':q,'unit_code':unit['code'],'unit_name':unit['name'],'search_tier':tier,'phase':'initial_41' if initial else 'expansion_308','status':'attempted_no_results' if q=='石家庄市 旅游景区' else 'not_executed_engine_unavailable','engines_attempted':['Google','Baidu'] if q=='石家庄市 旅游景区' else [],'baidu_url':'https://www.baidu.com/s?'+urlencode({'wd':q}),'google_url':'https://www.google.com/search?'+urlencode({'q':q,'num':10})})
save(D/'query_plan.json',plan)
probes=[]
for engine,file,status,url in [('Google','google_probe.html','javascript_interstitial_no_results','https://www.google.com/search?'+urlencode({'q':'石家庄市 旅游景区','num':10})),('Baidu','baidu_probe.html','baidu_security_verification_network_error','https://www.baidu.com/s?'+urlencode({'wd':'石家庄市 旅游景区'}))]:
 p=B/'raw'/file;s=BeautifulSoup(p.read_bytes(),'html.parser')
 probes.append({'engine':engine,'query':'石家庄市 旅游景区','requested_url':url,'http_status':200,'outcome':status,'result_count':0,'raw_path':str(p.relative_to(B)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'visible_text':s.get_text(' ',strip=True),'followup':'stopped_no_captcha_bypass_no_other_queries_executed'})
save(D/'engine_attempts.json',probes)
manifest=[]
for p in sorted((B/'raw').iterdir()):
 if p.suffix not in {'.html','.xlsx'}:continue
 mpath=B/'logs'/f'{p.stem}.json';meta=json.loads(mpath.read_text()) if mpath.exists() else {}
 meta.update(source_id=p.stem,raw_path=str(p.relative_to(B)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
 meta['capture_file_mtime_asia_shanghai']=datetime.fromtimestamp(p.stat().st_mtime,ZoneInfo('Asia/Shanghai')).isoformat()
 meta['capture_time_note']='filesystem mtime recorded separately, not substituted for an exact HTTP timestamp'
 if p.stem=='google_probe':meta.update(url=probes[0]['requested_url'],status=200)
 if p.suffix=='.html':
  soup=BeautifulSoup(p.read_bytes(),'html.parser');meta['title']=soup.title.get_text(strip=True) if soup.title else None
  dates=re.findall(r'(?:发布时间[：:]?|来源[：:]?)\s*(\d{4}-\d{2}-\d{2})',soup.get_text(' ',strip=True));meta['publication_date']=dates[0] if dates else None
 manifest.append(meta)
# Snapshot identities, not a hardcoded '500' whitelist.
save(B/'inputs/snapshot_hashes.json',[{'path':str(p.relative_to(B)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted((B/'inputs').glob('*.json')) if p.name!='snapshot_hashes.json'])
save(D/'source_manifest.json',manifest)
urls={m['source_id']:m.get('url') for m in manifest}
urls['official_sjz']='https://wglj.sjz.gov.cn/columns/78ae016a-9b7c-4e84-9855-358e950c4b6b/201909/29/e180a7a4-1769-4748-b305-ad6cea23d762.html'
urls['official_province_xlsx']='https://whly.hebei.gov.cn/c/2026-01-30/584097.html'
def area_match(text):
 matches=[a for a in areas if a['name'] in text]
 return matches[0] if len(matches)==1 else None
def rows(id):
 s=BeautifulSoup((B/'raw'/f'{id}.html').read_bytes(),'html.parser')
 return [[norm(c.get_text(' ',strip=True)) for c in tr.select('td,th')] for tr in s.select('table')[0].select('tr')]
obs=[]
def add(id,rowno,name,loc,kind,grade=None,extra=None):
 if not name:return
 a=area_match(loc);ev={'name':name,'location_text':loc,'catalog_kind':kind,'grade':grade or None,**(extra or {})}
 obs.append({'observation_id':f'{id}:{rowno}','full_name':name,'source_id':id,'source_url':urls[id],'source_row_number':rowno,'source_excerpt':ev,'source_kind':'official_catalog_row','area_code':a['code'] if a else None,'area_name':a['name'] if a else None,'entity_type':'spot','search_query':None,'matched_search_keyword':None,'verification_status':'catalog_indexed_pending_enrich'})
for i,r in enumerate(rows('official_sjz')[1:],2):
 if len(r)>=6:add('official_sjz',i,r[1],r[3],'A级旅游景区',r[2],{'operating_note':r[5] or None})
for i,r in enumerate(rows('official_red')[1:],2):
 if len(r)>=5:add('official_red',i,r[1],r[3],'红色旅游景区（点）',r[2])
for i,r in enumerate(rows('official_industrial')[1:],2):
 if len(r)>=3:add('official_industrial',i,r[0],r[1],'工业旅游示范点',extra={'public_access_status':None})
for i,r in enumerate(rows('official_rural')[1:],2):
 if len(r)>=8:
  name=r[6] if r[6] else r[5]
  add('official_rural',i,name,''.join(r[3:7]),'乡村旅游重点村镇',extra={'designation_type':r[1],'designation_level':r[2],'township_name':r[5] or None,'designation_year':r[7]})
w=openpyxl.load_workbook(B/'raw/official_province_xlsx.xlsx',data_only=True)
export=[]
for sheet in w:
 for i,r in enumerate(sheet.values,1):
  export.append({'sheet':sheet.title,'excel_row':i,'values':list(r)})
  if i>3 and isinstance(r[0],int) and '石家庄市' in str(r[2]):add('official_province_xlsx',i,norm(r[1]),norm(r[2]),'河北省A级旅游景区',norm(r[3]),{'operating_note':r[5]})
save(D/'province_workbook_all_rows.json',export)
save(D/'source_observations.json',obs)
# Exact spelling + explicit geographic identity only. Variant names are never silently merged.
known_by_name={}
for o in obs:
 if o['area_code']:known_by_name.setdefault(o['full_name'],set()).add(o['area_code'])
groups={}
for o in obs:
 known=known_by_name.get(o['full_name'],set())
 inferred_scope=next(iter(known)) if o['area_code'] is None and len(known)==1 else o['area_code']
 key=(o['full_name'],inferred_scope)
 groups.setdefault(key,[]).append(o)
def blind(name):
 ids=[i for i,c in enumerate(name) if '\u4e00'<=c<='\u9fff'];keep=set(sorted(ids,key=lambda i:hashlib.sha256(f'{name}:{i}'.encode()).hexdigest())[:2]);return ''.join(c if i in keep else '*' for i,c in enumerate(name))
records=[]
for (name,ac),os in sorted(groups.items(),key=lambda v:(v[0][0],str(v[0][1]))):
 ev=' '.join([name]+[o['source_excerpt']['catalog_kind'] for o in os]);tags=[]
 for needle,tag in [('红色旅游','红色旅游'),('温泉','温泉'),('博物馆','博物馆'),('纪念馆','纪念馆'),('寺','寺庙'),('露营','露营'),('古道','古道'),('湿地','湿地'),('森林','森林'),('长城','长城')]:
  if needle in ev and tag in allowed:tags.append({'name':tag,'type':'strong','evidence':'explicit catalog kind or exact full name'})
 r={'raw_id':'HB1301_'+hashlib.sha256((name+'|'+str(ac)).encode()).hexdigest()[:14],'entity_type':'spot','full_name':name,'blind_name':blind(name),'province_code':'13','province_name':'河北省','city_code':'1301','city_name':'石家庄市','area_code':ac,'area_name':next((o['area_name'] for o in os if o['area_code']==ac and o['area_name']),None),'township_name':next((o['source_excerpt'].get('township_name') for o in os if o['source_excerpt'].get('township_name')),None),'matched_search_keyword':None,'matched_search_keywords':[],'search_tier':'city_official_catalog','search_query':None,'location':{'lat':None,'lng':None,'coord_source':None},'tags':tags[:3],'tagging_status':'evidence_tags_partial' if tags else 'pending_evidence','summary_100w':None,'description':None,'adult_ticket_price':None,'image_url':None,'source_url':os[0]['source_url'],'source_observation_ids':[o['observation_id'] for o in os],'verification_status':'catalog_indexed_pending_enrich','parent_id':None,'sub_spots':[],'parent_child_status':'unresolved','physical_entity_uniqueness':'not_asserted','exact_name_dedup_rule':'same full name; merge unknown admin only if exactly one explicit official admin exists for this name; never merge across distinct known areas','public_access_status':None}
 records.append(r)
# Possible names/aliases are audit suggestions, not resolved parent-child facts.
review=[]
for a,b in itertools.combinations(records,2):
 if a['area_code'] and b['area_code'] and a['area_code']!=b['area_code']:continue
 n1,n2=a['full_name'],b['full_name'];ratio=difflib.SequenceMatcher(None,n1,n2).ratio()
 if n1 in n2 or n2 in n1 or ratio>=.65:review.append({'a':a['raw_id'],'a_name':n1,'b':b['raw_id'],'b_name':n2,'reason':'exact_name_different_admin' if n1==n2 else 'possible_alias_or_parent_child','action':'review_only_no_merge'})
save(D/'alias_parent_child_review.json',review)
save(D/'city_candidates.json',records)
projections=[]
for a in areas:
 rs=[dict(r,search_tier='area_official_catalog_projection',projection_of=r['raw_id']) for r in records if r['area_code']==a['code']]
 projections.extend(rs);(D/'area_candidates').mkdir(exist_ok=True);save(D/'area_candidates'/f"{a['code']}.json",rs)
save(D/'county_candidates.json',projections);save(D/'route_candidates.json',[])
summaries=[]
for a in areas:
 rs=[r for r in records if r['area_code']==a['code']]
 summaries.append({'area_code':a['code'],'area_name':a['name'],'query_prefix':a['searchAreaPrefix'],'planned_combos':14,'executed_combos':0,'actual_source_supported_candidate_names':len(rs),'route_candidates':0,'target_min_entries':1000,'target_met':False,'provenance':'catalog_projection_not_county_search'})
summary={'province':'河北省','city':'石家庄市','snapshot_area_units':len(areas),'standard_or_county_units_including_matrix_辛集市':len([a for a in areas if a['code'] not in {'130171','130172'}]),'extension_units':2,'warning_area_scope':'以输入矩阵24个单元为准，不是16区县；矩阵含辛集市和2个扩展区，不另行臆改隶属关系。','initial_planned_queries':41,'initial_city_keywords':13,'initial_selected_counties':['正定县','平山县'],'full_matrix_planned_queries':len(plan),'distinct_queries_attempted':1,'engine_requests':2,'successful_engine_result_pages':0,'engine_extracted_names':0,'unexecuted_initial_queries':40,'source_observations':len(obs),'source_counts':{id:sum(o['source_id']==id for o in obs) for id in sorted(set(o['source_id'] for o in obs))},'city_exact_name_admin_candidates':len(records),'county_catalog_projections':len(projections),'area_unknown_candidates':len(records)-len(projections),'route_candidates':0,'official_formal_routes':0,'review_pairs':len(review),'new_master_records':0,'target_min_entries_city':1000,'target_met':False,'status':'partial_official_catalog_candidate_batch_engines_unavailable','per_area':summaries,'warnings':['No matrix completion claimed: 1/41 initial distinct queries attempted, 0 usable pages.','Official row extraction is not Baidu/Google search completion. WebSearch was discovery only.','Exact name/admin grouping is not verified distinct geographic entity count.','Industrial enterprises are official tourism demonstration entries, not asserted currently open attractions.','No city/county master or Phase1/Beijing/Mac/Git files changed.','Names preserve official abbreviations and parenthetical titles; variants await review.']}
save(D/'summary.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k!='per_area'},ensure_ascii=False,indent=2))
