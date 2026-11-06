#!/usr/bin/env python3
"""Independent structural/provenance checks; not a claim of editorial completeness."""
import json,re,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
def load(p):return json.loads((R/p).read_text())
legal={n for c in load('inputs/tags_500.json')['categories'] for n in c['tags']}
files=[p for p in (R/'data/cities_db').glob('*.json') if p.name!='index.json']+list((R/'data/areas_db/11').glob('*.json'))+[R/'data/national_spots_master.json']
errors=[];checked=0
for p in files:
 records=json.loads(p.read_text());ids=[]
 for r in records:
  checked+=1;ids.append(r['raw_id']);n=r['full_name'];b=r['blind_name']
  checks={'blind_length':len(n)==len(b),'two_hanzi':len(re.findall('[\u3400-\u9fff]',b))==2,
   'blind_alignment':all(c=='*' or c==n[i] for i,c in enumerate(b)),
   'source_url':r['source_url'].startswith('https://yllhj.beijing.gov.cn/'),
   'retrieved_at':r['retrieved_at'].endswith('+08:00'),
   'row_range':1<=r['source_row']<=1136,'page_range':1<=r['source_page']<=64,
   'tag_names':all(t['name'] in legal for t in r['tags']),
   'tag_counts':2<=sum(t['type']=='strong' for t in r['tags'])<=4 and 2<=sum(t['type']=='weak' for t in r['tags'])<=5,
   'area_code':r['area_code'] is None or r['area_code'].startswith('1101'),
   'no_guessed_coords':r['location']['lat'] is None and r['location']['lng'] is None,
   'no_fabricated_price_or_image':r['adult_ticket_price'] is None and r['image_url'] is None,
   'no_unsupported_copy':r['description'] is None and r['summary_100w'] is None,
   'no_contact_fields':not any(k in r for k in ['phone','email','author','user_id','avatar','nickname']),
   'source_hash':r['source_sha256']==hashlib.sha256((R/'raw/beijing_parks_2026.pdf').read_bytes()).hexdigest()}
  for k,v in checks.items():
   if not v:errors.append({'file':str(p.relative_to(R)),'id':r['raw_id'],'check':k})
 if len(ids)!=len(set(ids)):errors.append({'file':str(p),'check':'duplicate_raw_id'})
master=load('data/national_spots_master.json')
assert len(master)==len(set(r['source_entity_id'] for r in master))==1136
assert len(load('data/areas_db/index.json'))==16
assert sum(x['count'] for x in load('data/areas_db/index.json'))==1132
result={'checked_records':checked,'checked_files':len(files),'errors':errors,'assertions_passed':not errors,'caveat':'Pass is structure/provenance only; 100% coordinates/tickets/images/copy remain missing; editorial tag review pending.'}
(R/'logs/independent_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(bool(errors))
