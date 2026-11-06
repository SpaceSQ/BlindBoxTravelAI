#!/usr/bin/env python3
"""Fetch three public government pages once; never persist contact columns."""
import requests,json,hashlib,re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
B=Path(__file__).resolve().parents[1]
SOURCES=[
('scenic','https://whlyj.beijing.gov.cn/ggfw/ly/202511/t20251119_4287815.html','北京市 A级旅游景区 名录 2026 名称 区', '北京市文化和旅游局_旅游_北京旅游网景点链接列表'),
('museums','https://whlyj.beijing.gov.cn/ggfw/ly/202511/t20251119_4287849.html','北京市 文物局 2025 博物馆 名录 名称 地址 一览表','北京市文化和旅游局_旅游_北京旅游网博物馆链接列表'),
('walks','https://whlyj.beijing.gov.cn/zwgk/xwzx/gzdt/202607/t20260729_4796963.html','site.beijing.gov.cn 2026 文旅 主题 游览线路 线路一 线路二','一轴贯古今，漫步读京城 10条“北京中轴线最美漫步道”主题线路')]
for sid,url,query,title in SOURCES:
 out=B/'raw'/f'{sid}.json';ev=B/'evidence'/f'{sid}.json'
 if out.exists() and ev.exists():
  m=json.loads(ev.read_text());assert hashlib.sha256(out.read_bytes()).hexdigest()==m['sanitized_sha256'];print('cache verified',sid);continue
 r=requests.get(url,timeout=65,headers={'User-Agent':'BlindBoxTravelAI public-directory-research/2.0'});r.raise_for_status()
 soup=BeautifulSoup(r.content,'html.parser')
 # government pages declare UTF-8; BeautifulSoup detects original encoding
 text=soup.get_text(' ',strip=True)
 dates=re.findall(r'(?:发布日期|日期)[：:]?\s*(\d{4}-\d{2}-\d{2})',text)
 rows=[]
 if sid in ('scenic','museums'):
  for tr in soup.select('tr'):
   cells=tr.find_all(['td','th'],recursive=False)
   v=[x.get_text(' ',strip=True) for x in cells]
   if len(v)<3 or not re.fullmatch(r'\d+',v[0]):continue
   name=v[1];link=cells[-1].find('a',href=True)
   row={'row':int(v[0]),'name':name,'detail_url':requests.compat.urljoin(url,link['href']) if link else None}
   if sid=='scenic':
    assert len(v)>=4
    row.update(grade=v[2],area=v[3])
   rows.append(row)
 else:
  # keep only published title, actual node order, and length: no commercial recommendations/contact info
  ps=[p.get_text(' ',strip=True) for p in soup.find_all(['p'])]
  for i,p in enumerate(ps):
   h=re.search(r'线路[一二三四五六七八九十]+[：:]\s*(.+)',p)
   if h and len(p)<100:
    follow=ps[i+1:];seq=next((x for x in follow if x.startswith('线路经过')),None)
    length=next((x for x in follow if x.startswith('漫步长度')),None)
    assert seq
    rows.append({'row':len(rows)+1,'name':h.group(1),'node_sequence_text':re.sub(r'^线路经过[：:]\s*','',seq),'length_text':length})
 assert len(rows)>0,(sid,text[:300])
 out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 meta={'source_id':sid,'url':url,'title':title,'actual_discovery_tool':'WebSearch','actual_query':query,'retrieved_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'source_display_dates':list(dict.fromkeys(dates)),'http_status':r.status_code,'response_content_sha256':hashlib.sha256(r.content).hexdigest(),'sanitized_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'evidence_file':str(out.relative_to(B)),'sanitization':'Only official row number, entity name, grade/area, public detail URL or route node order/length retained. Contact columns and page chrome discarded in memory. Original response not persisted.','license_status':'Publicly readable government directory; no explicit reuse license verified; no image or prose reuse rights inferred.','rows':len(rows)}
 ev.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(sid,len(rows),dates)
