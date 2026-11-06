#!/usr/bin/env python3
"""Acquire one whitelisted government PDF politely; never retries failures or bypasses TLS.
Cached source reuse is logged; HTTP 429/403 or any other error stops this job.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib,urllib.request
R=Path(__file__).resolve().parents[1]
u='https://yllhj.beijing.gov.cn/zwgk/2024nzcwj/2024nqtwj/202610/P020261020575226021358.pdf'
p=R/'raw/beijing_parks_2026.pdf'
state={'at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'source_url':u,'query':'北京市 2026 公园名录 各区 地址 公园','method':'official_PDF_download'}
try:
 if p.exists():state['status']='cached_resume'
 else:
  req=urllib.request.Request(u,headers={'User-Agent':'BlindBoxTravelAI-public-catalog-pilot/0.1'})
  with urllib.request.urlopen(req,timeout=60) as resp:body=resp.read(10*1024*1024)
  if not body.startswith(b'%PDF'):raise ValueError('not PDF; stop for manual review')
  p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.part');tmp.write_bytes(body);tmp.replace(p)
  state['status']='downloaded'
 state['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
except Exception as e:
 state.update(status='failed_no_retry',error=str(e));raise
finally:
 (R/'logs').mkdir(exist_ok=True)
 with (R/'logs/acquisition.jsonl').open('a') as f:f.write(json.dumps(state,ensure_ascii=False)+'\n')
 print(json.dumps(state,ensure_ascii=False))
