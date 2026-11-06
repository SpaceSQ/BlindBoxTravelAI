#!/usr/bin/env python3
"""Bind human-reviewed route nodes to the spot library; no fabricated fields."""
import json, sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else '/workspace/blindbox-travel')
def load(p): return json.loads((root/p).read_text())
spots=load('spots/spots_editorial_locked.json')
plan=load('routes/spot_merge_plan.json')
additions=load('routes/spots_route_additions.json')
if isinstance(additions,dict): additions=additions.get('spots',additions.get('items',[]))
base_ids={x['spot_id'] for x in spots}
for x in additions:
    if x['spot_id'] in base_ids: raise ValueError('Duplicate addition '+x['spot_id'])
    spots.append({**x,'evolution_stats':{'plan_mark_count':0,'review_count':0}})
raw_mapping=plan.get('mappings',plan.get('mapping',plan)) if isinstance(plan,dict) else plan
lookup={x['full_name']: x for x in spots}
for x in spots:
    x['source_aliases']=sorted(set(x.get('source_aliases',[])+x.get('sensitive_terms',[])+[x['full_name']]))
mapping={}
for v in raw_mapping:
    k=v['route_spot_name']; full=v['full_name']
    if v.get('action')=='map_existing' and full not in lookup: raise ValueError('Missing existing '+full)
    if v.get('action')=='create_new' and full not in lookup: raise ValueError('Missing addition '+full)
    mapping[k]=full
    aliases={a for a in [k,v['full_name']] if len(a)>=2}
    lookup[full]['source_aliases']=sorted(set(lookup[full].get('source_aliases',[]))|aliases)
for k,v in mapping.items():
    if v not in lookup: raise ValueError(f'Unmapped target: {k} -> {v}')
routes=load('routes/routes_editorial_locked.json')['routes']
for r in routes:
    names={x['spot_name'] for x in r['daily_schedule']}
    if set(r['spot_names']) != names: raise ValueError(f"Mismatched spot_names: {r['route_id']}")
    r['spot_ids']=[]
    r['daily_spot_nodes']=[]
    for name in r['spot_names']:
        full=mapping.get(name,name)
        if full not in lookup: raise ValueError(f"Missing mapping {name} in {r['route_id']}")
        s=lookup[full]
        if s['spot_id'] not in r['spot_ids']: r['spot_ids'].append(s['spot_id'])
        r['daily_spot_nodes'].append({'name':name,'spot_id':s['spot_id']})
    for d in r['daily_schedule']:
        d['spot_id']=lookup[mapping.get(d['spot_name'],d['spot_name'])]['spot_id']
        d.pop('spot_name',None)
    if r['route_type']=='single_spot':
        if set(r['spot_ids']) != {r['daily_schedule'][0]['spot_id']}: raise ValueError('Single route node drift '+r['route_id'])
    r.pop('spot_names',None)
    r['source_channels']=['Search_Engine']
    r['source_rights']='public page knowledge only; excludes social-user profiles'
extra=load('routes/source_ledger.json')
(root/'data/spots_seed.json').write_text(json.dumps(spots,ensure_ascii=False,indent=2)+'\n')
(root/'data/routes_seed.json').write_text(json.dumps(routes,ensure_ascii=False,indent=2)+'\n')
metrics={'version':'phase1','plan_mark_count_scope':'app local counter','spots_metrics':{},'routes_metrics':{}}
for x in spots: metrics['spots_metrics'][x['spot_id']]={'plan_mark_count':0,'review_count':0}
for x in routes: metrics['routes_metrics'][x['route_id']]={'plan_mark_count':0,'review_count':0}
(root/'data/evolution_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'spots':len(spots),'routes':len(routes),'added':len(additions)},ensure_ascii=False))
