#!/usr/bin/env python3
"""BlindBoxTravelAI Phase 1 validator: no input data rewritten by this script."""
import argparse, collections, datetime, hashlib, json, re, sys
from pathlib import Path
HAN = re.compile(r'[㐀-䶿一-鿿]')
URL = re.compile(r'^https?://\S+$')
EXPECTED_PROVINCES = 34

def fn(path): return path.split('/')[-1]
def mask_report(name, mask, errors):
 labels=[]
 for c in name:
  labels.append(c if HAN.fullmatch(c) else ('OTHER' if c!='*' else '*'))
 if len(name)!=len(mask): errors.append('blind_name length differs')
 ke=[i for i,c in enumerate(mask) if c!='*']
 if len(ke)!=2: errors.append(f'blind_name literal chars={len(ke)} expected 2')
 if any(not HAN.fullmatch(mask[i]) for i in ke): errors.append('non-Han chars exposed')
 if any((labels[i]=='OTHER' or labels[i]=='*') for i in ke): errors.append('mask reveals literal other character/asterisk')
 if any((HAN.fullmatch(c) and mask[i]==c) for i,c in enumerate(name) if i not in ke): errors.append('masked position exposes Han')
 if any(name[i]==mask[i] and HAN.fullmatch(name[i]) for i in ke) is False: errors.append('selected Han do not match original')
 if any(c=='*' for c in name): errors.append('input name contains star')

def validate(path, allow_counts=True):
    def arr(name, wrapper):
        data=json.loads((path/'data'/name).read_text())
        return data.get(wrapper, data.get('items', [])) if isinstance(data,dict) else data
    spots=arr('spots_seed.json','spots')
    routes=arr('routes_seed.json','routes')
    tags=json.loads((path/'data/tags_500.json').read_text())
    metrics=json.loads((path/'data/evolution_metrics.json').read_text())
    valid={t for c in tags['categories'] for t in c['tags']}
    errors=[];warnings=[];ids={};byname={}
    required=['full_name','blind_name','province','city','location','tags','description','summary_100w','image_url','adult_ticket_price','mock_weather','events_and_discounts','ai_strategy','tag_interpretation','source_channels','evolution_stats']
    for i,spot in enumerate(spots):
        label=spot.get('spot_id',f'row{i+1}')
        ids[label]=spot;byname[spot.get('full_name','')]=label
        for field in required:
            if field not in spot:errors.append(f'{label}: missing {field}')
        mask_report(spot.get('full_name',''),spot.get('blind_name',''),errors)
        text=' '.join(spot.get(field,'') for field in ['description','summary_100w','tag_interpretation'])
        if spot.get('full_name','') in text:errors.append(f'{label}: full name disclosed in visible copy')
        for alias in spot.get('sensitive_terms',[]):
            if alias and alias in text:errors.append(f'{label}: sensitive term {alias!r} in visible copy')
        try:
            lat,lng=spot['location']['lat'],spot['location']['lng']
            if not(-90<=lat<=90 and -180<=lng<=180):errors.append(f'{label}: invalid coordinate range')
        except (TypeError,KeyError):errors.append(f'{label}: invalid location')
        strong={t.get('name','') for t in spot.get('tags',[]) if t.get('type')=='strong'}
        weak={t.get('name','') for t in spot.get('tags',[]) if t.get('type')=='weak'}
        if not 2<=len(strong)<=4:errors.append(f'{label}: needs 2-4 strong tags')
        if not 2<=len(weak)<=5:errors.append(f'{label}: needs 2-5 weak tags')
        for tag in spot.get('tags',[]):
            if tag.get('name') not in valid:errors.append(f'{label}: unknown tag {tag.get("name")}')
        for name in strong:
            if f'【{name}】' not in spot.get('tag_interpretation',''):errors.append(f'{label}: missing interpretation {name}')
        for name,part in re.findall(r'【([^】]+)】([^【]+)',spot.get('tag_interpretation','')):
            if name not in strong:errors.append(f'{label}: undeclared interpretation {name}')
            elif not 100<=len(part.strip())<=150:warnings.append(f'{label}: interpretation {name} {len(part.strip())} chars outside 100-150')
        if not 200<=len(spot.get('description',''))<=300:warnings.append(f'{label}: description outside 200-300')
        if not 80<=len(spot.get('summary_100w',''))<=120:warnings.append(f'{label}: summary outside 80-120')
        if spot.get('adult_ticket_price') is not None and not isinstance(spot.get('adult_ticket_price'),(int,float)):errors.append(f'{label}: nonnumeric ticket')
        if spot.get('image_url') is not None and not URL.match(spot.get('image_url','')):errors.append(f'{label}: malformed image URL')
        if not spot.get('source_channels'):errors.append(f'{label}: no source channels')
        evidence_channels={ref.get('channel') for ref in spot.get('source_refs',[])}
        for channel in spot.get('source_channels',[]):
            if channel not in evidence_channels:errors.append(f'{label}: unsupported source channel {channel}')
        if not spot.get('source_refs'):errors.append(f'{label}: no evidence entries')
        for ref in spot.get('source_refs',[]):
            if not URL.match(ref.get('url','')):errors.append(f'{label}: malformed source URL')
            if ref.get('channel') not in spot.get('source_channels',[]):errors.append(f'{label}: evidence has undeclared channel {ref.get("channel")}')
        for field in ['description','summary_100w','tag_interpretation']:
            for filler in ['行程节奏宜留白','开放与安全以现场管理为准','出发前再核','资料以公开渠道为准']:
                if spot.get(field,'').count(filler)>1:errors.append(f'{label}: repeated filler {filler!r} in {field}')
        if any(spot.get('evolution_stats',{}).get(k,-1)!=0 for k in ['plan_mark_count','review_count']):errors.append(f'{label}: counters not zero')
    route_ids={};node_refs=set()
    for i,route in enumerate(routes):
        label=route.get('route_id',f'row{i+1}');route_ids[label]=route
        schedule=route.get('daily_schedule',[]);days=route.get('duration_days')
        if days not in range(1,8) or len(schedule)!=days:errors.append(f'{label}: invalid duration')
        mask_report(route.get('full_route_title',''),route.get('blind_route_title',''),errors)
        if route.get('route_type')=='single_spot':
            if not 1<=days<=2 or len(set(route.get('spot_ids',[])))!=1:errors.append(f'{label}: single route must be 1-2d one spot')
        elif route.get('route_type')=='multi_spot':
            if not 1<=days<=7 or len(set(route.get('spot_ids',[])))<2:errors.append(f'{label}: multi route must be 1-7d 2+ spots')
        else:errors.append(f'{label}: invalid route type')
        for d in schedule:
            segments=d.get('segments')
            if segments is not None:
                if not isinstance(segments,list) or not segments:errors.append(f'{label}: empty day segments')
                for seg in segments:
                    if 'spot_id' not in seg or 'blind_highlights' not in seg:errors.append(f'{label}: incomplete day segment')
            elif d.get('spot_id') is not None:
                d['segments']=[{'spot_id':d['spot_id'],'blind_highlights':d.get('blind_highlights','')}]
        text=' '.join(seg.get('blind_highlights','') for d in schedule for seg in d.get('segments',[]))
        blind=route.get('blind_route_title','')+' '+text
        for sid in route.get('spot_ids',[]):
            node_refs.add(sid)
            if sid not in ids:errors.append(f'{label}: dangling {sid}')
            for alias in ids.get(sid,{}).get('source_aliases',ids.get(sid,{}).get('sensitive_terms',[])):
                if alias and len(alias)>=2 and alias in blind:errors.append(f'{label}: alias leaked {alias!r}')
        for d in schedule:
            if d.get('day') not in range(1,days+1):errors.append(f'{label}: invalid day')
            for seg in d.get('segments',[]):
                sid=seg.get('spot_id')
                if sid not in ids:errors.append(f'{label}: missing daily spot ID')
                if sid not in route.get('spot_ids',[]):errors.append(f'{label}: daily node not declared')
                for alias in ids.get(sid,{}).get('sensitive_terms',[]):
                    if alias and alias in text:errors.append(f'{label}: sensitive daily text {alias!r}')
        if not route.get('source_refs',route.get('sources',[])):errors.append(f'{label}: no route sources')
        for ref in route.get('source_refs',route.get('sources',[])):
            if not URL.match(ref.get('url','')):errors.append(f'{label}: invalid route URL')
        if any(route.get('evolution_stats',{}).get(k,-1)!=0 for k in ['plan_mark_count','review_count']):errors.append(f'{label}: counters not zero')
    if len(ids)!=len(spots):errors.append('duplicate spot_id')
    if len(route_ids)!=len(routes):errors.append('duplicate route_id')
    if len(byname)!=len(spots):errors.append('duplicate full_name')
    if len(spots)<100:errors.append('Phase 1 requires >=100 spots')
    if len({s.get('province') for s in spots})!=EXPECTED_PROVINCES:errors.append('Phase 1 requires 34 province-level regions')
    if len(routes)<50:errors.append('Phase 1 requires >=50 routes')
    for k in range(1,8):
        if not any(r.get('duration_days')==k for r in routes):errors.append(f'Phase 1 requires duration {k} days')
    for group,expected in [('spots_metrics',ids),('routes_metrics',route_ids)]:
        actual=metrics.get(group,{})
        if set(actual)!=set(expected):errors.append(f'{group}: mismatched IDs')
        for key,c in actual.items():
            if any(c.get(k,-1)!=0 for k in ['plan_mark_count','review_count']):errors.append(f'{group} {key}: counters not zero')
    actual=[t for c in tags['categories'] for t in c['tags']]
    return {'spots':len(spots),'routes':len(routes),'provinces':len({s.get('province') for s in spots}),'actual_tag_entries':len(actual),'unique_tags':len(valid),'declared_tags':tags.get('total_count'),'unbound_spot_refs':len(node_refs-set(ids)),'errors':errors,'warnings':warnings,'source_channel_counts':dict(collections.Counter(c for s in spots for c in s.get('source_channels',[]))),'duration_counts':dict(collections.Counter(str(r.get('duration_days')) for r in routes))}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('root',nargs='?',default='.')
 args=ap.parse_args();p=Path(args.root)
 try:report=validate(p)
 except (FileNotFoundError,json.JSONDecodeError,TypeError) as e:print(json.dumps({'errors':[str(e)]},ensure_ascii=False,indent=2));raise SystemExit(1)
 (p/'validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False,indent=2))
 raise SystemExit(bool(report['errors']))
if __name__=='__main__':main()
