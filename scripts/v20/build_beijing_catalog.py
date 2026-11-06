#!/usr/bin/env python3
"""Box-only official directory pilot; no repo access, no fabricated prices/coordinates.
Run: .venv/bin/python scripts/build_beijing_catalog.py
64 page extractions checkpoint independently; 4 local workers; no concurrent HTTP fan-out.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,re,os,collections
import pdfplumber
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT/'raw/beijing_parks_2026.pdf'
URL='https://yllhj.beijing.gov.cn/zwgk/2024nzcwj/2024nqtwj/202610/P020261020575226021358.pdf'
LANDING='https://yllhj.beijing.gov.cn/zwgk/2024nzcwj/2024nqtwj/202610/t20261020_4911597.shtml'
def write(path,obj):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
def read(path):return json.loads(Path(path).read_text())
def log(stage,**kw):
 with (ROOT/'logs/resume.jsonl').open('a') as f:f.write(json.dumps({'at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'stage':stage,**kw},ensure_ascii=False)+'\n')
def clean(s):return re.sub(r'\s+','',s or '')
def parse_page(i):
 target=ROOT/f'raw/pages/{i+1:03d}.json'
 if target.exists():return read(target)
 result=[]
 with pdfplumber.open(PDF) as doc:
  for table in doc.pages[i].extract_tables():
   for row in table:
    if len(row)!=8 or not clean(row[0]).isdigit():continue
    # Deliberately never persist telephone or named contacts.
    n,unit,name,kind,grade,address=map(clean,row[:6])
    result.append(dict(serial=int(n),unit=unit,name=name,kind=kind,grade=grade,address=address,page=i+1))
 write(target,result);return result
def blind(name):
 idx=[i for i,c in enumerate(name) if re.fullmatch('[\u3400-\u9fff]',c)]
 if len(idx)<2:raise ValueError(name)
 rank=sorted(idx,key=lambda i:hashlib.sha256((name+str(i)).encode()).digest())[:2]
 return ''.join(c if i in rank else '*' for i,c in enumerate(name))
def tags(row):
 # These are explicitly editorial rule suggestions, NOT official classification facts.
 strong=['园林','感受自然'];weak=['慢生活','体验派']
 if row['kind']=='历史名园':strong=['寻古','园林'];weak=['历史爱好者','怀古']
 if '森林' in row['name']:strong=['森林','感受自然']
 if '湿地' in row['name']:strong=['湿地','感受自然']
 if '遗址' in row['name']:strong=['遗址公园','寻古'];weak=['历史爱好者','怀古']
 return [{'name':x,'type':t} for t,xs in [('strong',strong),('weak',weak)] for x in xs]
def main():
 (ROOT/'logs').mkdir(exist_ok=True)
 retrieved=datetime.fromtimestamp(PDF.stat().st_mtime,ZoneInfo('Asia/Shanghai')).isoformat()
 source_hash=hashlib.sha256(PDF.read_bytes()).hexdigest()
 manifest_path=ROOT/'raw/pages/manifest.json'
 if manifest_path.exists() and read(manifest_path).get('sha256')!=source_hash:
  raise RuntimeError('source changed: move page checkpoints aside explicitly before rebuild')
 write(manifest_path,{'sha256':source_hash,'source_url':URL,'retrieved_at':retrieved})
 log('start',source_sha256=source_hash)
 with pdfplumber.open(PDF) as doc:npages=len(doc.pages)
 with ProcessPoolExecutor(max_workers=4) as ex:pages=list(ex.map(parse_page,range(npages)))
 rows=[r for p in pages for r in p]
 serials=[r['serial'] for r in rows]
 assert len(rows)==1136 and sorted(serials)==list(range(1,1137)), 'table extraction completeness failed'
 write(ROOT/'raw/official_catalog_rows.json',rows)
 log('extract_complete',pages=npages,rows=len(rows))
 areas=[a for a in read(ROOT/'inputs/areas_search_matrix.json') if a['provinceCode']=='11']
 city=[c for c in read(ROOT/'inputs/cities_search_matrix.json') if c['provinceCode']=='11']
 assert len(areas)==16 and len(city)==1
 amap={a['name']:a for a in areas}
 valid={t for c in read(ROOT/'inputs/tags_500.json')['categories'] for t in c['tags']}
 def assign(row):
  if row['unit'] in amap:return amap[row['unit']], 'directory_district_column'
  matches=[a for n,a in amap.items() if row['address'].startswith(n)]
  if len(matches)==1:return matches[0],'address_explicit_prefix'
  return None,'unresolved_nonstandard_management_unit'
 def rec(row,tier,area=None):
  assigned,basis=assign(row)
  if area is not None:assert assigned and assigned['code']==area['code']
  # Distinct provenance identity, not fuzzy-name or citywide suffix stripping.
  eid=f'BJ_PARKS_2026_{row["serial"]:04d}'
  a=assigned
  name=row['name']
  out={'raw_id':f'{"CITY" if tier=="city_level" else "AREA"}_{eid}', 'source_entity_id':eid,
   'entity_type':'spot','full_name':name,'blind_name':blind(name),
   'province_code':'11','province_name':'北京市','city_code':'1101','city_name':'北京市',
   'area_code':a['code'] if a else None,'area_name':a['name'] if a else None,
   'area_assignment_basis':basis,'township_name':None,'address':row['address'],
   'matched_search_keyword':'公园','matched_search_keywords':['公园'],'search_tier':tier,
   'query':f'北京市公园名录（2026年度） PDF; '+('全市名录' if area is None else f'所属区={area["name"]};市属/经开区按地址显式区名前缀匹配'),
   'query_type':'official_directory_filter','location':{'lat':None,'lng':None,'coord_source':None,'coordinate_status':'not_in_source'},
   'tags':tags(row),'tagging_status':'editorial_rules_pending_review',
   'tagging_basis':{'official_park_type':row['kind'],'rule_inputs':['official_park_type','full_name']},
   'summary_100w':None,'description':None,'adult_ticket_price':None,'image_url':None,
   'source_url':URL+f'#page={row["page"]}','source_landing_url':LANDING,
   'source_page':row['page'],'source_row':row['serial'],'source_sha256':source_hash,'retrieved_at':retrieved,
   'source_channels':['Official_Site'],'official_park_type':row['kind'],'official_park_grade':row['grade'],
   'verification_status':'catalog_indexed_pending_enrich',
   'pending_enrich':['coordinates','ticket_price','image','description','tag_review','access_and_safety'],
   'evolution_stats':{'plan_mark_count':0,'review_count':0}}
  assert all(t['name'] in valid for t in out['tags'])
  return out
 city_records=[rec(r,'city_level') for r in rows]
 write(ROOT/'data/cities_db/11_1101.json',city_records)
 def county(a):
  # independent tier materialization from public source rows; not copied city records.
  selected=[r for r in rows if assign(r)[0] and assign(r)[0]['code']==a['code']]
  records=[rec(r,'county_level',a) for r in selected]
  path=f'data/areas_db/11/{a["code"]}.json';write(ROOT/path,records)
  log('county_complete',area_code=a['code'],count=len(records))
  return {'area_code':a['code'],'area_name':a['name'],'path':path,'count':len(records),'target':1000,'shortfall':max(0,1000-len(records))},records
 with ThreadPoolExecutor(max_workers=4) as ex:county_results=list(ex.map(county,areas))
 area_records=[r for _,rs in county_results for r in rs]
 write(ROOT/'data/cities_db/index.json',[{'city_code':'1101','city_name':'北京市','path':'data/cities_db/11_1101.json','count':len(city_records),'target':1000,'shortfall':max(0,1000-len(city_records))}])
 write(ROOT/'data/areas_db/index.json',[i for i,_ in county_results])
 write(ROOT/'data/市级_cities.json',city_records);write(ROOT/'data/县级_areas.json',area_records)
 master={};merges=[]
 for r in city_records+area_records:
  k=r['source_entity_id']
  if k not in master:
   m=dict(r);m['spot_id']='SP_'+k;m['raw_ids']=[r['raw_id']];m['search_tiers']=[r['search_tier']];master[k]=m
  else:
   m=master[k];m['raw_ids'].append(r['raw_id']);m['search_tiers']=sorted(set(m['search_tiers']+[r['search_tier']]))
   merges.append({'master_id':m['spot_id'],'incoming_id':r['raw_id'],'rule':'same_official_directory_row_identity'})
 # Same name across different entries is only a REVIEW candidate, never an automatic merge.
 byname=collections.defaultdict(list)
 for r in master.values():byname[r['full_name']].append(r['source_entity_id'])
 candidates=[{'name':n,'source_entity_ids':ids,'action':'retain_pending_review'} for n,ids in byname.items() if len(ids)>1]
 write(ROOT/'data/national_spots_master.json',list(master.values()));write(ROOT/'data/national_routes_master.json',[])
 write(ROOT/'data/evolution_metrics.json',{m['spot_id']:m['evolution_stats'] for m in master.values()})
 write(ROOT/'logs/dedup_merges.json',merges);write(ROOT/'logs/dedup_review_candidates.json',candidates)
 unresolved=[r for r in city_records if r['area_code'] is None]
 write(ROOT/'logs/unresolved_districts.json',unresolved)
 errors=[]
 for r in city_records+area_records+list(master.values()):
  b=r['blind_name'];n=r['full_name']
  if len(b)!=len(n) or len(re.findall('[\u3400-\u9fff]',b))!=2:errors.append([r['raw_id'],'blind'])
  if any(c!='*' and c!=n[i] for i,c in enumerate(b)):errors.append([r['raw_id'],'alignment'])
  for field in ['summary_100w','description']:
   if r[field] and n in r[field]:errors.append([r['raw_id'],'privacy_text'])
  if not r['source_url'].startswith('https://') or not r['source_row']:errors.append([r['raw_id'],'evidence'])
  if any(t['name'] not in valid for t in r['tags']):errors.append([r['raw_id'],'tags'])
 assert not errors, errors[:10]
 summary={'province':'北京市','scope':'official_park_catalog_only','city_records':len(city_records),
  'county_records':len(area_records),'county_shards':16,'unique_spots':len(master),'unique_routes':0,
  'cross_tier_merges':len(merges),'name_collision_review_groups':len(candidates),'unresolved_districts':len(unresolved),
  'with_coords':0,'with_ticket_price':0,'with_image':0,'with_long_description':0,
  'validated_records_including_master':len(city_records)+len(area_records)+len(master),'validation_errors':errors,
  'county_counts':[i for i,_ in county_results],'source_url':URL,'source_sha256':source_hash,'retrieved_at':retrieved,
  'two_tiers_share_same_primary_source':True,'not_independent_cross_source_corroboration':True,
  'baidu_google_matrix_executed':False,'limitations':['Not full tourism inventory','No routes synthesized without evidence','OSM SSL probe failed; no bypass or retry','Coordinates not available in source; kept null','Tags editorial suggestions, not official endorsement']}
 write(ROOT/'logs/validation_report.json',summary)
 write(ROOT/'inputs/beijing_query_plan.json',{'city':city,'counties':areas,'execution_status':'pending_search_engine_batches; official parks directory pilot completed'})
 log('validated',city=len(city_records),county=len(area_records),unique=len(master),errors=0)
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
