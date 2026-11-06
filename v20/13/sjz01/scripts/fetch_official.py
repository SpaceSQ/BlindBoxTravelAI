import requests,json,hashlib,concurrent.futures
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
B=Path(__file__).resolve().parents[1]
S={
'official_red':'https://wglj.sjz.gov.cn/columns/78ae016a-9b7c-4e84-9855-358e950c4b6b/202404/22/cde915e1-e3a0-40f6-a8c6-74161055dc7d.html',
'official_rural':'https://wglj.sjz.gov.cn/columns/78ae016a-9b7c-4e84-9855-358e950c4b6b/201909/29/27c7cbd1-7bf7-4b4e-a8b9-7ae02b0cad6b.html',
'official_industrial':'https://wglj.sjz.gov.cn/columns/78ae016a-9b7c-4e84-9855-358e950c4b6b/201909/29/4950b767-8d94-42e4-a321-36ea715221d7.html',
'official_province_xlsx':'https://whly.hebei.gov.cn/zwf/ui/contentcore/resource/download?ID=48084'}
def fetch(item):
 id,u=item; m={'source_id':id,'url':u,'retrieved_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}
 try:
  r=requests.get(u,timeout=40);ext='xlsx' if id.endswith('xlsx') else 'html';p=B/'raw'/f'{id}.{ext}';p.write_bytes(r.content);m.update(status=r.status_code,final_url=r.url,sha256=hashlib.sha256(r.content).hexdigest(),bytes=len(r.content),raw_path=str(p.relative_to(B)))
  if ext=='html':
   r.encoding=r.apparent_encoding;s=BeautifulSoup(r.text,'html.parser');m['title']=s.title.get_text(strip=True) if s.title else None;(B/'raw'/f'{id}.txt').write_text(s.get_text('\n',strip=True)); print(id,r.status_code,len(r.content),s.get_text(' ',strip=True)[200:650])
  else:print(id,r.status_code,len(r.content),r.headers.get('Content-Type'))
 except Exception as e:m['error']=str(e)
 (B/'logs'/f'{id}.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(fetch,S.items()))
