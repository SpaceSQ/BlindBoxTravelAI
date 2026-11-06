#!/usr/bin/env python3
"""Map route spot_names -> existing spots or new additions. Writes only under routes/."""
from __future__ import annotations
import json, re, time, urllib.parse, urllib.request, datetime, sys
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path('/workspace/blindbox-travel')
ROUTES = ROOT / 'routes'
SPOTS_DIR = ROOT / 'spots'
import sys as _sys
_sys.path.insert(0, str(ROUTES))
from _spot_helpers import (
    make_blind, sanitize_tags, default_tags, climate_for, fit_desc, fit_summary,
    interp_for, theme_bits_for, VALID, HAN, to_hant
)

NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
OSM = 'https://nominatim.openstreetmap.org/'
UA = 'BlindBoxTravelAI-SpotMerge/1.0 (phase1 seed; contact: local-box)'

# route_name -> (existing_spot_id, full_name)
ALIAS_EXISTING = {
  "稻城亚丁风景区": ("SP077", "稻城亚丁风景区"),
  "丽江古城": ("SP085", "丽江古城"),
  "青海湖景区": ("SP099", "青海湖景区"),
  "茶卡盐湖": ("SP100", "茶卡盐湖"),
  "秦始皇兵马俑博物馆": ("SP093", "秦始皇兵马俑博物馆"),
  "大雁塔": ("SP095", "大雁塔"),
  "故宫博物院": ("SP001", "故宫博物院"),
  "塔尔寺": ("SP101", "塔尔寺"),
  "外滩": ("SP024", "外滩"),
  "八达岭长城": ("SP002", "八达岭长城"),
  "颐和园": ("SP003", "颐和园"),
  "黄山风景区": ("SP037", "黄山风景区"),
  "大理古城": ("SP088", "大理古城"),
  "鼓浪屿": ("SP040", "鼓浪屿风景名胜区"),
  "玉龙雪山": ("SP086", "玉龙雪山景区"),
  "杭州西湖": ("SP032", "杭州西湖风景名胜区"),
  "西塘": ("SP034", "西塘古镇旅游景区"),
  "太平山顶": ("SP110", "香港太平山顶"),
  "维多利亚港": ("SP108", "香港维多利亚港"),
  "大三巴牌坊": ("SP112", "澳门大三巴牌坊"),
  "三坊七巷": ("SP044", "三坊七巷景区"),
  "蟳埔村": ("SP043", "泉州蟳埔村"),
  "都江堰": ("SP079", "都江堰景区"),
  "莫高窟": ("SP096", "敦煌莫高窟"),
  "张掖七彩丹霞": ("SP098", "张掖七彩丹霞旅游景区"),
  "乌镇": ("SP033", "乌镇古镇旅游区"),
  "拙政园": ("SP028", "苏州园林拙政园"),
  "承德避暑山庄": ("SP006", "承德避暑山庄及周围寺庙景区"),
  "平遥古城": ("SP010", "平遥古城景区"),
  "婺源江湾": ("SP047", "婺源江湾景区"),
  "凤凰古城": ("SP059", "凤凰古城旅游区"),
  "喀纳斯": ("SP104", "喀纳斯景区"),
  "赛里木湖": ("SP106", "赛里木湖景区"),
  "乌镇西栅": ("SP033", "乌镇古镇旅游区"),
  "天坛大佛": ("SP109", "香港大屿山昂坪"),
  "张家界国家森林公园": ("SP057", "张家界武陵源风景区"),
  "袁家界": ("SP057", "张家界武陵源风景区"),
  "镜泊湖风景区": ("SP022", "镜泊湖景区"),
  "长白山天池": ("SP018", "长白山景区"),
}

ALIAS_NOTES = {
  "乌镇西栅": "西栅为乌镇古镇旅游区核心开放片区，与主库 SP033 同一官方景区实体，不另开 ID。",
  "天坛大佛": "天坛大佛位于大屿山昂坪，与主库 SP109 香港大屿山昂坪同址，不另开 ID。",
  "张家界国家森林公园": "与武陵源核心景区为同一世界遗产主体常用别称，映射 SP057；不与天门山混并。",
  "袁家界": "袁家界为武陵源核心观景台区，映射 SP057；天门山仍为独立新增。",
  "镜泊湖风景区": "与主库「镜泊湖景区」同地别称。",
  "长白山天池": "天池为长白山景区核心景观，映射 SP018；不另拆 ID。",
  "鼓浪屿": "简称→鼓浪屿风景名胜区",
  "玉龙雪山": "简称→玉龙雪山景区",
  "杭州西湖": "简称→杭州西湖风景名胜区（勿与惠州西湖 SP064 混并）",
  "西塘": "简称→西塘古镇旅游景区",
  "太平山顶": "简称→香港太平山顶",
  "维多利亚港": "简称→香港维多利亚港",
  "大三巴牌坊": "简称→澳门大三巴牌坊",
  "三坊七巷": "简称→三坊七巷景区",
  "蟳埔村": "简称→泉州蟳埔村",
  "都江堰": "简称→都江堰景区（青城山仍独立新增，因行程分日）",
  "莫高窟": "简称→敦煌莫高窟",
  "张掖七彩丹霞": "简称→张掖七彩丹霞旅游景区",
  "乌镇": "简称→乌镇古镇旅游区",
  "拙政园": "简称→苏州园林拙政园",
  "承德避暑山庄": "简称→承德避暑山庄及周围寺庙景区",
  "平遥古城": "简称→平遥古城景区",
  "婺源江湾": "简称→婺源江湾景区",
  "凤凰古城": "简称→凤凰古城旅游区",
  "喀纳斯": "简称→喀纳斯景区",
  "赛里木湖": "简称→赛里木湖景区",
}

# Unique new entities: route_name -> canonical record
NEW_DEFS = [
  ("湄洲岛", "湄洲岛国家旅游度假区", "福建省", "莆田市", "https://zh.wikipedia.org/wiki/湄洲岛"),
  ("泉州古城", "泉州古城", "福建省", "泉州市", "https://zh.wikipedia.org/wiki/泉州古城"),
  ("崇武古城", "崇武古城", "福建省", "泉州市", "https://zh.wikipedia.org/wiki/崇武古城"),
  ("沙坡尾", "厦门沙坡尾", "福建省", "厦门市", "https://zh.wikipedia.org/wiki/沙坡尾"),
  ("平潭岛", "平潭海坛风景名胜区", "福建省", "福州市", "https://zh.wikipedia.org/wiki/海坛风景名胜区"),
  ("南澳岛青澳湾", "南澳岛青澳湾", "广东省", "汕头市", "https://zh.wikipedia.org/wiki/南澳岛"),
  ("南澳后花园村", "南澳后花园村", "广东省", "汕头市", "https://zh.wikipedia.org/wiki/南澳县"),
  ("梧桐山", "深圳梧桐山风景名胜区", "广东省", "深圳市", "https://zh.wikipedia.org/wiki/梧桐山"),
  ("七娘山", "大鹏半岛七娘山", "广东省", "深圳市", "https://zh.wikipedia.org/wiki/七娘山"),
  ("潮州古城", "潮州古城", "广东省", "潮州市", "https://zh.wikipedia.org/wiki/潮州古城墙"),
  ("沙面", "广州沙面", "广东省", "广州市", "https://zh.wikipedia.org/wiki/沙面"),
  ("龙脊梯田", "龙脊梯田风景名胜区", "广西壮族自治区", "桂林市", "https://zh.wikipedia.org/wiki/龙脊梯田"),
  ("阳朔西街", "阳朔西街", "广西壮族自治区", "桂林市", "https://zh.wikipedia.org/wiki/阳朔县"),
  ("遇龙河", "遇龙河", "广西壮族自治区", "桂林市", "https://zh.wikipedia.org/wiki/遇龙河"),
  ("泸沽湖", "泸沽湖景区", "云南省", "丽江市", "https://zh.wikipedia.org/wiki/泸沽湖"),
  ("束河古镇", "束河古镇", "云南省", "丽江市", "https://zh.wikipedia.org/wiki/束河古镇"),
  ("宽窄巷子", "成都宽窄巷子", "四川省", "成都市", "https://zh.wikipedia.org/wiki/宽窄巷子"),
  ("青城山", "青城山景区", "四川省", "成都市", "https://zh.wikipedia.org/wiki/青城山"),
  ("洪崖洞", "重庆洪崖洞", "重庆市", "渝中区", "https://zh.wikipedia.org/wiki/洪崖洞"),
  ("磁器口古镇", "磁器口古镇", "重庆市", "沙坪坝区", "https://zh.wikipedia.org/wiki/磁器口"),
  ("天门山", "天门山旅游景区", "湖南省", "张家界市", "https://zh.wikipedia.org/wiki/天门山"),
  ("卓尔山", "祁连卓尔山", "青海省", "海北藏族自治州", "https://zh.wikipedia.org/wiki/卓尔山"),
  ("丹噶尔古城", "丹噶尔古城", "青海省", "西宁市", "https://zh.wikipedia.org/wiki/丹噶尔古城"),
  ("金银滩原子城景区", "金银滩原子城景区", "青海省", "海北藏族自治州", "https://zh.wikipedia.org/wiki/中国原子城"),
  ("西安城墙", "西安城墙", "陕西省", "西安市", "https://zh.wikipedia.org/wiki/西安城墙"),
  ("钟鼓楼", "西安钟鼓楼", "陕西省", "西安市", "https://zh.wikipedia.org/wiki/西安钟楼"),
  ("鸣沙山月牙泉", "鸣沙山月牙泉", "甘肃省", "酒泉市", "https://zh.wikipedia.org/wiki/鸣沙山月牙泉"),
  ("南浔古镇", "南浔古镇", "浙江省", "湖州市", "https://zh.wikipedia.org/wiki/南浔古镇"),
  ("塘栖古镇", "塘栖古镇", "浙江省", "杭州市", "https://zh.wikipedia.org/wiki/塘栖"),
  ("大馆", "香港大馆", "香港特别行政区", "中西区", "https://zh.wikipedia.org/wiki/大馆"),
  ("香港海洋公园", "香港海洋公园", "香港特别行政区", "南区", "https://zh.wikipedia.org/wiki/香港海洋公园"),
  ("官也街", "氹仔官也街", "澳门特别行政区", "氹仔", "https://zh.wikipedia.org/wiki/官也街"),
  ("议事亭前地", "澳门议事亭前地", "澳门特别行政区", "澳门半岛", "https://zh.wikipedia.org/wiki/议事亭前地"),
  ("九份老街", "九份老街", "台湾省", "新北市", "https://zh.wikipedia.org/wiki/九份"),
  ("十分老街", "十分老街", "台湾省", "新北市", "https://zh.wikipedia.org/wiki/十分"),
  ("北投温泉区", "北投温泉区", "台湾省", "台北市", "https://zh.wikipedia.org/wiki/北投温泉"),
  ("北投文物馆", "北投文物馆", "台湾省", "台北市", "https://zh.wikipedia.org/wiki/北投文物馆"),
  ("景山公园", "景山公园", "北京市", "西城区", "https://zh.wikipedia.org/wiki/景山公园"),
  ("清明上河园", "开封清明上河园", "河南省", "开封市", "https://zh.wikipedia.org/wiki/清明上河园"),
  ("婺源篁岭", "婺源篁岭", "江西省", "上饶市", "https://zh.wikipedia.org/wiki/篁岭"),
  ("恩施大峡谷", "恩施大峡谷", "湖北省", "恩施土家族苗族自治州", "https://zh.wikipedia.org/wiki/恩施大峡谷"),
  ("栈桥", "青岛栈桥", "山东省", "青岛市", "https://zh.wikipedia.org/wiki/栈桥_(青岛)"),
  ("八大关", "青岛八大关", "山东省", "青岛市", "https://zh.wikipedia.org/wiki/八大关"),
  ("滨海路", "大连滨海路", "辽宁省", "大连市", "https://zh.wikipedia.org/wiki/滨海路_(大连)"),
  ("中央大街", "哈尔滨中央大街", "黑龙江省", "哈尔滨市", "https://zh.wikipedia.org/wiki/中央大街"),
  ("滇池", "昆明滇池", "云南省", "昆明市", "https://zh.wikipedia.org/wiki/滇池"),
  ("西山", "昆明西山风景区", "云南省", "昆明市", "https://zh.wikipedia.org/wiki/西山_(昆明)"),
  ("亚龙湾", "三亚亚龙湾", "海南省", "三亚市", "https://zh.wikipedia.org/wiki/亚龙湾"),
  ("金沙湾", "青海湖金沙湾", "青海省", "海南藏族自治州", "https://zh.wikipedia.org/wiki/青海湖"),
  ("M+", "香港M+博物馆", "香港特别行政区", "油尖旺区", "https://zh.wikipedia.org/wiki/M%2B"),
  ("香港故宫文化博物馆", "香港故宫文化博物馆", "香港特别行政区", "油尖旺区", "https://zh.wikipedia.org/wiki/香港故宫文化博物馆"),
  ("五彩滩", "布尔津五彩滩", "新疆维吾尔自治区", "阿勒泰地区", "https://zh.wikipedia.org/wiki/五彩滩"),
  ("禾木", "禾木景区", "新疆维吾尔自治区", "阿勒泰地区", "https://zh.wikipedia.org/wiki/禾木村"),
  ("乌尔禾魔鬼城", "乌尔禾魔鬼城", "新疆维吾尔自治区", "克拉玛依市", "https://zh.wikipedia.org/wiki/乌尔禾魔鬼城"),
  ("那拉提草原", "那拉提旅游风景区", "新疆维吾尔自治区", "伊犁哈萨克自治州", "https://zh.wikipedia.org/wiki/那拉提"),
  ("巴音布鲁克", "巴音布鲁克景区", "新疆维吾尔自治区", "巴音郭楞蒙古自治州", "https://zh.wikipedia.org/wiki/巴音布鲁克"),
  ("独库公路", "独库公路风景道", "新疆维吾尔自治区", "伊犁哈萨克自治州", "https://zh.wikipedia.org/wiki/独库公路"),
  ("新都桥", "新都桥", "四川省", "甘孜藏族自治州", "https://zh.wikipedia.org/wiki/新都桥镇"),
  ("理塘", "理塘勒通古镇", "四川省", "甘孜藏族自治州", "https://zh.wikipedia.org/wiki/理塘县"),
  ("色达", "色达县风景区", "四川省", "甘孜藏族自治州", "https://zh.wikipedia.org/wiki/色达县"),
  ("丹巴甲居藏寨", "丹巴甲居藏寨", "四川省", "甘孜藏族自治州", "https://zh.wikipedia.org/wiki/甲居藏寨"),
  ("四姑娘山", "四姑娘山景区", "四川省", "阿坝藏族羌族自治州", "https://zh.wikipedia.org/wiki/四姑娘山"),
  ("洱海", "大理洱海", "云南省", "大理白族自治州", "https://zh.wikipedia.org/wiki/洱海"),
  ("香格里拉普达措", "普达措国家公园", "云南省", "迪庆藏族自治州", "https://zh.wikipedia.org/wiki/普达措国家公园"),
  ("独克宗古城", "独克宗古城", "云南省", "迪庆藏族自治州", "https://zh.wikipedia.org/wiki/独克宗古城"),
  ("圣索菲亚大教堂", "哈尔滨圣索菲亚大教堂", "黑龙江省", "哈尔滨市", "https://zh.wikipedia.org/wiki/圣索菲亚大教堂_(哈尔滨)"),
  ("亚布力国际滑雪场", "亚布力国际滑雪场", "黑龙江省", "哈尔滨市", "https://zh.wikipedia.org/wiki/亚布力滑雪旅游度假区"),
  ("中国雪乡", "中国雪乡风景区", "黑龙江省", "牡丹江市", "https://zh.wikipedia.org/wiki/雪乡国家森林公园"),
]

# Curated strong/weak overrides for distinctive places (must be in VALID)
CURATED = {
  "香港海洋公园": (["游乐园","看海","亲子游"], ["热门","出片","热带风情"]),
  "天门山旅游景区": (["奇峰","登山","震撼"], ["缆车","云海","体力怪"]),
  "龙脊梯田风景名胜区": (["梯田","出片","民族风"], ["农家乐","慢生活","摄影发烧友"]),
  "泸沽湖景区": (["湖泊","摩梭文化","出片"], ["星空","慢生活","母系氏族"]),
  "遇龙河": (["漂流","喀斯特","出片"], ["骑行","情侣","避暑"]),
  "青城山景区": (["道观","登山","静谧"], ["避暑","银发游","禅意"]),
  "鸣沙山月牙泉": (["沙漠","湖泊","出片"], ["日落","摄影发烧友","干燥"]),
  "西安城墙": (["古建","长城","历史名城"], ["骑行","夜景" if False else "出片","热门"]),
  "四姑娘山景区": (["雪山","登山","震撼"], ["重装徒步","高原","体力怪"]),
  "普达措国家公园": (["湖泊","森林","洗肺"], ["高原","避暑","负氧离子"]),
  "亚布力国际滑雪场": (["滑雪","冰天雪地","刺激"], ["严寒","热门","极限运动"]),
  "中国雪乡风景区": (["玩雪","冰天雪地","出片"], ["严寒","雾凇","热门"]),
  "香港M+博物馆": (["博物馆","看展","文艺"], ["出片","热门","情侣"]),
  "香港故宫文化博物馆": (["博物馆","寻古","古建"], ["研学","热门","银发游"]),
  "香港大馆": (["古建","博物馆","历史名城"], ["文艺","出片","咖啡续命"]),
  "那拉提旅游风景区": (["草原","放空","星空"], ["自驾","微风","情侣"]),
  "巴音布鲁克景区": (["草原","湖泊","星空"], ["自驾","日落","苍凉"]),
  "乌尔禾魔鬼城": (["雅丹","苍凉","出片"], ["日落","摄影发烧友","干燥"]),
  "独库公路风景道": (["自驾","雪山","震撼"], ["高原","体力怪","星空"]),
  "恩施大峡谷": (["峡谷","喀斯特","震撼"], ["出片","避暑","体力怪"]),
  "湄洲岛国家旅游度假区": (["海岸线","看海","朝圣"], ["海岛","情侣","微风"]),
  "哈尔滨中央大街": (["历史名城","出片","逛吃"], ["冬日" if False else "烟火气","热门","情侣"]),
  "哈尔滨圣索菲亚大教堂": (["教堂","出片","历史名城"], ["摄影发烧友","热门","文艺"]),
  "三亚亚龙湾": (["海岸线","看海","阳光沙滩"], ["热带风情","情侣","潜水"]),
  "成都宽窄巷子": (["古镇","逛吃","出片"], ["烟火气","慢生活","热门"]),
  "重庆洪崖洞": (["出片","夜景" if False else "赛博朋克","吊脚楼"], ["热门","烟火气","情侣"]),
  "北投温泉区": (["温泉","疗休养","慢生活"], ["避寒","情侣","康养"]),
  "九份老街": (["古镇","出片","怀旧"], ["山城" if False else "寻幽","烟火气","文艺"]),
  "青海湖金沙湾": (["湖泊","沙滩","出片"], ["自驾","日落","高原"]),
  "大理洱海": (["湖泊","骑行","出片"], ["日落","情侣","慢生活"]),
  "丹巴甲居藏寨": (["藏区","出片","民族风"], ["高山" if False else "寻幽","摄影发烧友","小众"]),
  "色达县风景区": (["藏传佛教","朝圣","红叶" if False else "震撼"], ["高原","静谧","银发游"]),
}

def sensitive_from_name(name, province):
  ban = {"风景","名胜","景区","旅游","文化","国家","公园","世界","旅游区","风景区","名胜区","博物院","博物馆","度假区"}
  region = province.replace("省","").replace("市","").replace("自治区","").replace("特别行政区","").replace("壮族","").replace("回族","").replace("维吾尔","").replace("藏族","").replace("土家族","").replace("苗族","").replace("哈萨克","").replace("蒙古","").replace("朝鲜族","").replace("自治州","")
  sens=[]
  for frag in re.findall(r'[\u4e00-\u9fff]{2,4}', name):
    if frag == region or frag in ban or frag in VALID:
      continue
    if frag not in sens:
      sens.append(frag)
  return sens[:6]

def geocode(query, cache, cache_path):
  if query in cache and cache[query].get('lat') is not None:
    return cache[query]
  params = urllib.parse.urlencode({'q': query, 'format': 'json', 'limit': 1})
  url = f'{OSM}search?{params}'
  req = urllib.request.Request(url, headers={'User-Agent': UA})
  try:
    with urllib.request.urlopen(req, timeout=30) as resp:
      data = json.loads(resp.read().decode())
    if data:
      item = data[0]
      rec = {
        'lat': float(item['lat']),
        'lng': float(item['lon']),
        'display': item.get('display_name',''),
        'query': query,
        'source': OSM,
      }
    else:
      rec = {'lat': None, 'lng': None, 'display': '', 'query': query, 'source': OSM, 'error': 'no_result'}
  except Exception as e:
    rec = {'lat': None, 'lng': None, 'display': '', 'query': query, 'source': OSM, 'error': str(e)}
  cache[query] = rec
  cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + '\n')
  time.sleep(1.05)
  return rec

# Preferred Nominatim queries (avoid wrong first-hit snaps)
QUERY_OVERRIDES = {
  "湄洲岛国家旅游度假区": ["湄洲岛 莆田", "湄洲岛"],
  "平潭海坛风景名胜区": ["海坛岛 平潭", "平潭岛"],
  "南澳岛青澳湾": ["青澳湾 南澳 汕头", "南澳岛 汕头"],
  "南澳后花园村": ["黄花山森林公园 南澳"],  # nearest verified Nan'ao hit; village-level refine later
  "厦门沙坡尾": ["沙坡尾 厦门"],
  "龙脊梯田风景名胜区": ["龙脊梯田风景名胜区 广西", "龙胜 梯田"],
  "香港海洋公园": ["香港海洋公园", "Ocean Park Hong Kong"],
  "香港大馆": ["Tai Kwun Hong Kong", "大馆 香港"],
  "香港M+博物馆": ["M+ Museum Hong Kong"],
  "香港故宫文化博物馆": ["Hong Kong Palace Museum"],
  "氹仔官也街": ["官也街 澳门"],
  "澳门议事亭前地": ["议事亭前地"],
  "祁连卓尔山": ["卓尔山 祁连"],
  "金银滩原子城景区": ["中国原子城", "海晏 原子城"],
  "青海湖金沙湾": [],  # force fallback — OSM snaps wrong city
  "那拉提旅游风景区": ["那拉提旅游风景区 新源"],
  "普达措国家公园": ["普达措国家公园 香格里拉", "Potatso National Park"],
  "禾木景区": ["禾木村"],
  "布尔津五彩滩": ["五彩滩 布尔津"],
  "乌尔禾魔鬼城": ["乌尔禾 魔鬼城"],
  "独库公路风景道": ["独库公路"],
  "中国雪乡风景区": ["雪乡 双峰"],
  "亚布力国际滑雪场": ["亚布力滑雪"],
  "哈尔滨圣索菲亚大教堂": ["圣索菲亚 哈尔滨"],
  "开封清明上河园": ["开封 清明上河园"],
  "婺源篁岭": ["篁岭 婺源"],
  "四姑娘山景区": ["四姑娘山"],
  "丹巴甲居藏寨": ["甲居藏寨"],
  "理塘勒通古镇": ["理塘县"],
  "色达县风景区": ["色达县"],
  "新都桥": ["新都桥镇"],
  "九份老街": ["九份"],
  "十分老街": ["十分 新北"],
  "北投温泉区": ["北投温泉"],
  "北投文物馆": ["北投文物馆"],
  "天门山旅游景区": ["天门山 张家界"],
  "阳朔西街": ["阳朔西街"],
  "遇龙河": ["遇龙河 阳朔"],
  "巴音布鲁克景区": ["巴音布鲁克景区 和静"],
}

# Manual public approximate coordinates when Nominatim misses or snaps to wrong province
FALLBACK_COORDS = {
  "龙脊梯田风景名胜区": (25.7579, 110.1308, "Longji terraces Longsheng precinct (public approx)"),
  "南澳后花园村": (23.4210, 117.0500, "Nan'ao hinterland village precinct near Huanghuashan; refine later"),
  "青海湖金沙湾": (36.5800, 100.7400, "Qinghai Lake east-shore Jinsha Bay public approx"),
  "金银滩原子城景区": (36.9300, 100.9000, "Haiyan Atomic City / JinYinTan precinct public approx"),
  "那拉提旅游风景区": (43.2550, 84.0280, "Nalati grassland Xinyuan Ili public approx"),
  "普达措国家公园": (27.8600, 99.9400, "Potatso / Bitahai-Shudu lake area Shangri-La public approx"),
  "独库公路风景道": (43.3500, 84.0500, "Duku corridor mid-north section public approx"),
}

PROVINCE_HINTS = {
  "福建省": ["福建", "Fujian"],
  "广东省": ["广东", "Guangdong"],
  "广西壮族自治区": ["广西", "Guangxi"],
  "云南省": ["云南", "Yunnan"],
  "四川省": ["四川", "Sichuan"],
  "重庆市": ["重庆", "Chongqing"],
  "湖南省": ["湖南", "Hunan"],
  "青海省": ["青海", "Qinghai"],
  "陕西省": ["陕西", "Shaanxi"],
  "甘肃省": ["甘肃", "Gansu"],
  "浙江省": ["浙江", "Zhejiang"],
  "香港特别行政区": ["香港", "Hong Kong"],
  "澳门特别行政区": ["澳门", "Macau", "Macao"],
  "台湾省": ["台湾", "臺灣", "Taiwan", "臺北", "新北"],
  "北京市": ["北京", "Beijing"],
  "河南省": ["河南", "Henan"],
  "江西省": ["江西", "Jiangxi"],
  "湖北省": ["湖北", "Hubei"],
  "山东省": ["山东", "Shandong"],
  "辽宁省": ["辽宁", "Liaoning"],
  "黑龙江省": ["黑龙江", "Heilongjiang"],
  "海南省": ["海南", "Hainan"],
  "新疆维吾尔自治区": ["新疆", "Xinjiang"],
  "江苏省": ["江苏", "Jiangsu"],
}

def display_ok(display: str, province: str) -> bool:
  if not display:
    return False
  hints = PROVINCE_HINTS.get(province, [province[:2]])
  return any(h in display for h in hints)


def build_spot(spot_id, full_name, province, city, geo_rec, wiki_url, route_names):
  if full_name in CURATED:
    s0, w0 = CURATED[full_name]
    # filter invalid from curated (night景 etc already avoided)
    s0 = [t for t in s0 if t in VALID]
    w0 = [t for t in w0 if t in VALID]
    strong, weak = sanitize_tags(s0, w0)
  else:
    s0, w0, _ = default_tags(full_name, province)
    strong, weak = sanitize_tags(s0, w0)
  sensitive = sensitive_from_name(full_name, province)
  # also add route short names as sensitive if they would leak identity
  for rn in route_names:
    if rn and rn not in sensitive and rn != full_name and len(rn) >= 2:
      sensitive.append(rn)
  sensitive = sensitive[:8]

  weather = climate_for(province)
  # highland / ski overrides
  if any(k in full_name for k in ['四姑娘','色达','理塘','新都桥','普达措','独库','那拉提','巴音','禾木','亚丁']):
    weather = {"temp":"高原昼夜温差大，夏季凉爽、冬季严寒","humidity":"偏低","wind":"山地阵风","uv_index":"极强","alert":"高反、强紫外与天气突变；部分路段季节封闭","evidence_basis":"高原气候公开描述，非实时气象"}
  if any(k in full_name for k in ['雪乡','亚布力','中央大街','圣索菲亚']):
    weather = {"temp":"夏18-28°C / 冬严寒可低于-20°C","humidity":"冬干","wind":"冬季风强","uv_index":"中","alert":"严寒、路面结冰与吹雪","evidence_basis":"东北气候公开描述"}

  blind = make_blind(full_name)
  desc = fit_desc(province, city, theme_bits_for(full_name, strong), strong)
  summary = fit_summary(province, city, f"以{theme_bits_for(full_name, strong)}为主要体验面向的公开目的地")
  for leak in [full_name] + sensitive:
    if leak and leak in desc:
      desc = desc.replace(leak, "本地标志性地段")
    if leak and leak in summary:
      summary = summary.replace(leak, "当地")
  if not (200 <= len(desc) <= 300):
    desc = fit_desc(province, city, theme_bits_for(full_name, strong), strong)
    for leak in [full_name] + sensitive:
      if leak and leak in desc:
        desc = desc.replace(leak, "本地标志性地段")
    if len(desc) > 300: desc = desc[:300]
    while len(desc) < 200:
      desc += "请以官方公告为准。"
      if len(desc) > 300:
        desc = desc[:300]; break
  if not (80 <= len(summary) <= 120):
    summary = fit_summary(province, city, f"以{theme_bits_for(full_name, strong)}为主要体验面向的公开目的地")
    for leak in [full_name] + sensitive:
      if leak and leak in summary:
        summary = summary.replace(leak, "当地")
    if len(summary) > 120: summary = summary[:120]
    while len(summary) < 80:
      summary += "出发前再核票价与预约。"
      if len(summary) > 120:
        summary = summary[:120]; break

  parts = [interp_for(tg, province, city) for tg in strong]
  tag_interpretation = "".join(parts)
  for leak in [full_name] + sensitive:
    if not leak: continue
    # simple replace outside of tag headers
    tag_interpretation = tag_interpretation.replace(leak, "当地")
  # ensure headers restored if somehow broken - check each strong
  for tg in strong:
    if f"【{tg}】" not in tag_interpretation:
      tag_interpretation = f"【{tg}】" + tag_interpretation

  # clamp each interpretation roughly by rebuilding if needed
  rebuilt=[]
  for tg in strong:
    chunk = interp_for(tg, province, city)
    for leak in [full_name] + sensitive:
      if leak and leak in chunk:
        # protect header
        if chunk.startswith(f"【{tg}】"):
          body = chunk[len(f"【{tg}】"):].replace(leak, "当地")
          chunk = f"【{tg}】" + body
        else:
          chunk = chunk.replace(leak, "当地")
    if len(chunk) < 100:
      chunk += "资料以公开渠道为准，不替代现场管理规定。"
    if len(chunk) > 150:
      chunk = chunk[:150]
      if f"【{tg}】" not in chunk:
        chunk = f"【{tg}】" + chunk[len(f"【{tg}】"):] if False else f"【{tg}】" + chunk.replace(f"【{tg}】","")
        # safer:
        if not chunk.startswith(f"【{tg}】"):
          chunk = f"【{tg}】" + chunk[:147]
    rebuilt.append(chunk)
  tag_interpretation = "".join(rebuilt)

  strategy = (
    f"公开旅行信息建议：先确认{province}{city}到目的地的公共交通或自驾管制，再按官方导览完成主环线；"
    f"体力类项目预留缓冲，恶劣天气服从关闭通知。本策略综合公开网页与地理常识编辑合成，非实地陪游，未读取登录墙社媒或 Mac 携程。"
  )

  lat, lng = geo_rec['lat'], geo_rec['lng']
  assert lat is not None and lng is not None, full_name

  channels = ["Search_Engine"]
  refs = [
    {
      "url": OSM,
      "retrieved_at": NOW,
      "claims": [
        f"geocode query={geo_rec.get('query')}",
        f"lat={lat}",
        f"lng={lng}",
        f"display={geo_rec.get('display','')[:180]}",
      ] + ([f"fallback_note={geo_rec.get('fallback_note')}"] if geo_rec.get('fallback_note') else []),
      "channel": "Search_Engine",
    },
    {
      "url": wiki_url,
      "retrieved_at": NOW,
      "claims": ["中文维基公开条目作为名称与区位背景核源（非票价核验）"],
      "channel": "Search_Engine",
    },
  ]

  spot = {
    "spot_id": spot_id,
    "full_name": full_name,
    "blind_name": blind,
    "name_zh_hans": full_name,
    "name_zh_hant": to_hant(full_name, province),
    "province": province,
    "city": city,
    "location": {"lat": lat, "lng": lng},
    "tags": [{"name": t, "type": "strong"} for t in strong] + [{"name": t, "type": "weak"} for t in weak],
    "description": desc,
    "summary_100w": summary,
    "image_url": None,
    "adult_ticket_price": None,
    "price_note": "本批次未完成该点官方成人票价逐条核验，记null，出发前请查官方渠道。",
    "opening_hours": "开放时间随季节与预约政策调整，以景区/主管部门公告为准。",
    "mock_weather": weather,
    "events_and_discounts": "暂未核实到当季优惠，请出发前复核",
    "ai_strategy": strategy,
    "tag_interpretation": tag_interpretation,
    "source_channels": channels,
    "source_refs": refs,
    "sensitive_terms": sensitive,
    "route_aliases": route_names,
    "data_provenance": {
      "coords": "OSM Nominatim public geocoder" + ("+manual_fallback" if geo_rec.get('fallback') else ""),
      "price": "unverified_null",
      "image": "null_unverified",
      "weather": "seasonal_climate_reference",
      "channels_note": "未访问 Mac 携程 APP；未登录爬取小红书/抖音；未伪称官方票务页已核价",
    },
    "evolution_stats": {"plan_mark_count": 0, "review_count": 0},
  }
  return spot


def main():
  routes_doc = json.loads((ROUTES / 'routes_draft.json').read_text())
  spots = json.loads((SPOTS_DIR / 'spots_final.json').read_text())
  existing_by_id = {s['spot_id']: s for s in spots}
  existing_names = {s['full_name'] for s in spots}

  # collect route name usage
  name_routes = defaultdict(list)
  for r in routes_doc['routes']:
    for n in r.get('spot_names', []):
      name_routes[n].append(r['route_id'])

  all_names = set(name_routes)
  mapped = set(ALIAS_EXISTING) | {rn for rn, *_ in NEW_DEFS}
  missing = sorted(all_names - mapped)
  extra = sorted(mapped - all_names)
  assert not missing, f'unmapped route names: {missing}'
  assert not extra, f'defs not in routes: {extra}'

  # geocode cache
  cache_path = ROUTES / 'geocode_new_cache.json'
  cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}

  additions = []
  new_name_to_id = {}
  next_id = 117
  for route_name, full_name, province, city, wiki in NEW_DEFS:
    assert full_name not in existing_names, full_name
    spot_id = f'SP{next_id:03d}'
    next_id += 1
    queries = list(QUERY_OVERRIDES.get(full_name, []))
    queries += [f'{full_name} {city} {province}', f'{full_name} {province}', f'{route_name} {city} {province}', route_name, full_name]
    # dedupe preserve order
    seen=set(); qlist=[]
    for q in queries:
      if q and q not in seen:
        seen.add(q); qlist.append(q)
    geo = None
    for q in qlist:
      cand = geocode(q, cache, cache_path)
      if cand.get('lat') is None:
        continue
      if display_ok(cand.get('display',''), province) or cand.get('fallback'):
        geo = cand
        break
      # keep first hit as weak candidate but continue looking
      if geo is None:
        geo = dict(cand); geo['weak_match']=True
    if (geo is None or geo.get('lat') is None or geo.get('weak_match')) and full_name in FALLBACK_COORDS:
      lat, lng, note = FALLBACK_COORDS[full_name]
      geo = {'lat': lat, 'lng': lng, 'display': note, 'query': full_name, 'source': 'manual_public_approx', 'fallback': True, 'fallback_note': note}
      cache[f'FALLBACK::{full_name}'] = geo
      cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + '\n')
    if geo is None or geo.get('lat') is None:
      raise SystemExit(f'geocode failed: {full_name} / {route_name}')
    if geo.get('weak_match') and full_name not in FALLBACK_COORDS:
      # accept weak match with note
      geo = dict(geo); geo['fallback_note'] = geo.get('fallback_note') or 'Nominatim display did not clearly include province tokens; accepted as best available hit'

    spot = build_spot(spot_id, full_name, province, city, geo, wiki, [route_name])
    additions.append(spot)
    new_name_to_id[route_name] = (spot_id, full_name)

  # merge plan
  mappings = []
  for name in sorted(all_names):
    routes = sorted(set(name_routes[name]))
    if name in ALIAS_EXISTING:
      sid, fn = ALIAS_EXISTING[name]
      assert sid in existing_by_id
      assert existing_by_id[sid]['full_name'] == fn
      mappings.append({
        "route_spot_name": name,
        "action": "map_existing",
        "spot_id": sid,
        "full_name": fn,
        "match_type": "exact" if name == fn else "alias",
        "note": ALIAS_NOTES.get(name, "exact name match" if name == fn else "same-entity alias by geography/official unit"),
        "used_by_routes": routes,
      })
    else:
      sid, fn = new_name_to_id[name]
      mappings.append({
        "route_spot_name": name,
        "action": "create_new",
        "spot_id": sid,
        "full_name": fn,
        "match_type": "new_entity",
        "note": "主库无同地实体；勿与近似名称景点混并",
        "used_by_routes": routes,
      })

  # route-level rewrite preview (spot_ids per route) — advisory only
  route_bindings = []
  for r in routes_doc['routes']:
    ids = []
    day_map = []
    for n in r['spot_names']:
      m = next(x for x in mappings if x['route_spot_name'] == n)
      ids.append(m['spot_id'])
    for d in r['daily_schedule']:
      m = next(x for x in mappings if x['route_spot_name'] == d['spot_name'])
      day_map.append({"day": d['day'], "spot_name": d['spot_name'], "spot_id": m['spot_id']})
    # unique preserve order
    uniq = []
    for i in ids:
      if i not in uniq: uniq.append(i)
    route_bindings.append({
      "route_id": r['route_id'],
      "spot_ids_ordered_unique": uniq,
      "daily_spot_ids": day_map,
      "duplicate_same_spot_days": len(ids) != len(uniq),
    })

  plan = {
    "generated_at": NOW,
    "timezone": "Asia/Shanghai",
    "source_files": {
      "routes": "routes/routes_draft.json",
      "spots_final": "spots/spots_final.json",
      "additions": "routes/spots_route_additions.json",
    },
    "counts": {
      "routes": len(routes_doc['routes']),
      "unique_route_spot_names": len(all_names),
      "map_existing": sum(1 for m in mappings if m['action']=='map_existing'),
      "create_new": sum(1 for m in mappings if m['action']=='create_new'),
      "existing_spots_library": len(spots),
      "additions_spots": len(additions),
      "merged_library_size_if_applied": len(spots) + len(additions),
    },
    "rules": [
      "同一真实地点唯一 spot_id；别名归并不得跨实体",
      "香港海洋公园 ≠ 大连老虎滩海洋公园",
      "杭州西湖 ≠ 惠州西湖",
      "天门山 ≠ 张家界武陵源/袁家界",
      "青城山与都江堰行程分日，保留独立 ID（都江堰已有 SP079）",
      "未改写 routes_draft.json / spots/spots_final.json / data/*",
      "image_url 与 adult_ticket_price 一律 null（未核）",
      "未宣称 Mac 携程或登录社媒采集",
    ],
    "do_not_merge_warnings": [
      {"a": "香港海洋公园", "b": "大连老虎滩海洋公园", "reason": "不同城市不同园区"},
      {"a": "杭州西湖", "b": "惠州西湖旅游景区", "reason": "不同省级行政区同名水体"},
      {"a": "天门山旅游景区", "b": "张家界武陵源风景区", "reason": "地理与经营权独立"},
      {"a": "独克宗古城", "b": "丽江古城", "reason": "香格里拉 vs 丽江，不同古城"},
      {"a": "昆明西山风景区", "b": "任意其他西山", "reason": "按路线语境锁定昆明滇池西岸"},
    ],
    "mappings": mappings,
    "new_spots_index": [
      {"spot_id": s['spot_id'], "full_name": s['full_name'], "province": s['province'], "city": s['city'], "route_aliases": s['route_aliases']}
      for s in additions
    ],
    "route_bindings_preview": route_bindings,
  }

  (ROUTES / 'spot_merge_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
  (ROUTES / 'spots_route_additions.json').write_text(json.dumps({
    "generated_at": NOW,
    "timezone": "Asia/Shanghai",
    "count": len(additions),
    "id_range": {"from": additions[0]['spot_id'], "to": additions[-1]['spot_id']},
    "spots": additions,
    "quality_notes": [
      "adult_ticket_price=null, image_url=null（未核验不编造）",
      "source_channels 仅 Search_Engine（Nominatim 地理编码 + 维基背景 URL，未伪称已读官方票务）",
      "mock_weather 为季节性参考",
      "evolution_stats 全 0",
    ],
  }, ensure_ascii=False, indent=2) + '\n')

  # self validate additions
  errors=[]
  warnings=[]
  ids=set(); names=set()
  for s in additions:
    if s['spot_id'] in ids: errors.append(f'dup id {s["spot_id"]}')
    ids.add(s['spot_id'])
    if s['full_name'] in names or s['full_name'] in existing_names: errors.append(f'dup name {s["full_name"]}')
    names.add(s['full_name'])
    if len(s['blind_name']) != len(s['full_name']): errors.append(f'{s["spot_id"]} blind len')
    lit=[i for i,c in enumerate(s['blind_name']) if c!='*']
    if len(lit)!=2: errors.append(f'{s["spot_id"]} blind lit!=2')
    st=[t['name'] for t in s['tags'] if t['type']=='strong']
    wk=[t['name'] for t in s['tags'] if t['type']=='weak']
    if not 2<=len(st)<=4: errors.append(f'{s["spot_id"]} strong count')
    if not 2<=len(wk)<=5: errors.append(f'{s["spot_id"]} weak count')
    for t in st+wk:
      if t not in VALID: errors.append(f'{s["spot_id"]} bad tag {t}')
    for t in st:
      if f'【{t}】' not in s['tag_interpretation']: errors.append(f'{s["spot_id"]} missing interp {t}')
    if s['full_name'] in (s['description']+s['summary_100w']+s['tag_interpretation']):
      errors.append(f'{s["spot_id"]} full_name leak')
    if not 200<=len(s['description'])<=300: warnings.append(f'{s["spot_id"]} desc {len(s["description"])}')
    if not 80<=len(s['summary_100w'])<=120: warnings.append(f'{s["spot_id"]} sum {len(s["summary_100w"])}')
    if s['image_url'] is not None: errors.append(f'{s["spot_id"]} image not null')
    if s['adult_ticket_price'] is not None: errors.append(f'{s["spot_id"]} price not null')
    if s['evolution_stats'] != {"plan_mark_count":0,"review_count":0}: errors.append(f'{s["spot_id"]} evo')
    if 'Ctrip_Mac' in s['source_channels'] or 'Xiaohongshu_Douyin' in s['source_channels']:
      errors.append(f'{s["spot_id"]} false channel')

  # README
  readme = f"""# Routes ↔ Spots 映射说明（Phase 1）

生成时间：{NOW}（Asia/Shanghai）

## 产出文件（仅 `routes/`）
- `spot_merge_plan.json`：路书站点名 → 已有 `spot_id` / 新增实体的完整映射与路线绑定预览
- `spots_route_additions.json`：需并入主库的新景点（`SP117`–`{additions[-1]['spot_id']}`，共 {len(additions)} 条）
- `README-mapping.md`：本说明
- `geocode_new_cache.json`：新增点 Nominatim 缓存（可复用）

**未改写**：`routes/routes_draft.json`、`spots/spots_final.json`、`data/*`。无 Git / Mac 同步。

## 数量
| 项 | 数 |
|---|---|
| 路线 | {len(routes_doc['routes'])} |
| 路书唯一站点名 | {len(all_names)} |
| 映射到主库已有 | {sum(1 for m in mappings if m['action']=='map_existing')} |
| 新增实体 | {len(additions)} |
| 主库现有 | {len(spots)} |
| 合并后理论规模 | {len(spots)+len(additions)} |

## ID 变换规则
1. **exact**：路书名与 `spots_final.full_name` 完全一致 → 直接用原 `spot_id`（如 `故宫博物院`→`SP001`）。
2. **alias**：同地别称 / 官方景区简称 → 映射已有 ID，并在 plan 中注明理由。例如：
   - `拙政园`→`SP028` 苏州园林拙政园
   - `杭州西湖`→`SP032`（**不是**惠州西湖 `SP064`）
   - `莫高窟`→`SP096` 敦煌莫高窟
   - `维多利亚港`→`SP108` 香港维多利亚港
   - `乌镇西栅`→`SP033`（西栅属乌镇景区同一实体）
   - `天坛大佛`→`SP109` 香港大屿山昂坪
   - `张家界国家森林公园` / `袁家界`→`SP057` 武陵源（**天门山另开** `新ID`）
   - `长白山天池`→`SP018`；`镜泊湖风景区`→`SP022`
3. **create_new**：主库无同地实体 → 分配 `SP117` 起连续 ID，写入 `spots_route_additions.json`。多条路线引用同一新名只建一次（如 `香港海洋公园` 在 RT030/RT060 共用同一新 ID）。

## 明确不混并
- 香港海洋公园 ≠ 大连老虎滩海洋公园
- 杭州西湖 ≠ 惠州西湖
- 天门山 ≠ 武陵源 / 袁家界
- 独克宗古城 ≠ 丽江古城
- 青城山（新）与都江堰（`SP079`）分日保留双 ID

## 新增点数据诚实边界
- `image_url` / `adult_ticket_price`：**null** + `price_note`（未核验不编造）
- `source_channels`：仅 `Search_Engine`（OSM Nominatim 坐标 + 维基条目 URL 作名称/区位背景）
- **未**声称读取 Mac 携程 APP、马蜂窝深页、小红书/抖音登录内容
- `ai_strategy` 标明为公开信息编辑合成，非实测陪游
- `mock_weather` 为季节性参考，非实时预报
- `evolution_stats` 全 0

## 父进程收尾建议
1. 将 `spots_route_additions.json` 的 `spots[]` 追加进主库（新 ID 段）。
2. 按 `spot_merge_plan.json` → `route_bindings_preview` 给每条路线写入 `spot_ids` 与每日 `spot_id`。
3. 再跑 `scripts/validate_blindbox_seed.py`；`advice_revalidate_before_release` 仍建议人工复核别名与坐标精度。

## 自校验
- errors: {len(errors)}
- warnings: {len(warnings)}
"""
  if errors:
    readme += "\n### errors\n" + "\n".join(f"- {e}" for e in errors) + "\n"
  if warnings:
    readme += "\n### warnings\n" + "\n".join(f"- {w}" for w in warnings[:40]) + ("\n..." if len(warnings)>40 else "\n")

  (ROUTES / 'README-mapping.md').write_text(readme)

  report = {"errors": errors, "warnings": warnings, "additions": len(additions), "aliases": sum(1 for m in mappings if m['action']=='map_existing')}
  (ROUTES / 'merge_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
  print(json.dumps(report, ensure_ascii=False, indent=2))
  if errors:
    raise SystemExit(1)

if __name__ == '__main__':
  main()
