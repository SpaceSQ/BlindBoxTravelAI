"""Bounded public official-page identity research; no account, no images, no personal contacts."""
import concurrent.futures,datetime,hashlib,json,pathlib,re,requests
from bs4 import BeautifulSoup
P=pathlib.Path(__file__).parent
plan=json.loads((P/'detail_plan.json').read_text()); urls=sorted({x['url'] for x in plan}); assert len(urls)<50
out=P/'detail_evidence';out.mkdir(exist_ok=True)
def get(u):
 f=out/(u.rsplit('/',1)[-1]+'.json')
 if f.exists(): return json.loads(f.read_text())
 d={'requested_url':u,'retrieved_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'source_kind':'Beijing_tourism_official_linked_detail','image_reuse_license_verified':False,'display_image_url':None}
 try:
  r=requests.get(u,timeout=35);d.update(http_status=r.status_code,final_url=r.url,response_sha256=hashlib.sha256(r.content).hexdigest());r.encoding='utf-8'
  s=BeautifulSoup(r.text,'html.parser'); title=s.select_one('h3.title');desc=s.select_one('.desc')
  d['title']=title.get_text(' ',strip=True) if title else None
  # Short identity quotations, not copied display introductions or full HTML.
  ps=desc.find_all('p',recursive=False) if desc else []
  text=' '.join(p.get_text(' ',strip=True) for p in ps)
  sentences=[v.strip() for v in re.split(r'(?<=[。！？])',text) if v.strip()]
  snippets=[]
  for sent in sentences[:2]+[v for v in sentences if any(k in v for k in ['位于','坐落','隶属','园内','馆内','更名','又名','又称','海淀区','西城区','东城区','朝阳区','丰台区'])]:
   if sent not in snippets: snippets.append(sent[:260])
  d['identity_excerpt_quotes']=snippets[:7]
  d['description_block_found']=bool(desc);d['description_character_count']=len(text)
  d['fetch_state']='usable_identity_page' if r.status_code==200 and title and text else 'no_identity_description'
 except requests.RequestException as e: d.update(fetch_state='request_failed_no_conclusion',error_type=type(e).__name__)
 f.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');return d
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex: results=list(ex.map(get,urls))
(P/'details_manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
for d in results: print(d['requested_url'],d.get('http_status'),d.get('title'),json.dumps(d.get('identity_excerpt_quotes',[]),ensure_ascii=False))
print('TOTAL',len(results))
