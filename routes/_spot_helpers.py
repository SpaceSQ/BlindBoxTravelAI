#!/usr/bin/env python3
"""Side-effect-free helpers copied from build_spots_phase1 for route spot merge."""
from __future__ import annotations
import json, re
from pathlib import Path
ROOT = Path('/workspace/blindbox-travel')
HAN = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff]')
tags_doc = json.loads((ROOT / 'data/tags_500.json').read_text())
VALID = set(t for c in tags_doc['categories'] for t in c['tags'])

# Default tag packs by keyword heuristics
def default_tags(name, province):
  packs = []
  # returns (strong, weak, sensitive_extra)
  if any(k in name for k in ["古城","古镇","古村落","宏村","西递","朱家角","同里","乌镇","西塘","凤凰","大理","丽江","阆中","黄姚"]):
    return ["古镇","寻古","出片"], ["慢生活","烟火气","文艺","情侣"], []
  if any(k in name for k in ["石窟","莫高","云冈","龙门","大足"]):
    return ["石窟","寻古","博物馆"], ["历史爱好者","研学","震撼"], []
  if any(k in name for k in ["土楼","碉楼","苗寨","侗寨"]):
    return ["非遗","民族风","出片"], ["小众","摄影发烧友","寻幽"], []
  if any(k in name for k in ["海","岛","湾","珊瑚","蜈支","涠洲","鼓浪","维多利亚","垦丁","普陀"]):
    return ["海岸线","看海","出片"], ["情侣","阳光沙滩","热带风情"] if "热带" in name or "三亚" in name or "蜈支" in name or "呀诺达" in name or "垦丁" in name else ["情侣","微风","热门"], []
  if any(k in name for k in ["山","峰","岭","武当","泰山","华山","黄山","峨眉","长白","丹霞","武陵","张家界","天柱","衡山","崂山","玉龙","雪"]):
    return ["登山","奇峰","震撼"], ["体力怪","云海","避暑"], []
  if any(k in name for k in ["湖","潭","湿地","盐湖","青海湖","茶卡","赛里木","纳木","西湖","瘦西","净月","镜泊"]):
    return ["湖泊","治愈","出片"], ["慢生活","日落","情侣"], []
  if any(k in name for k in ["瀑布","黄果","德天"]):
    return ["瀑布","震撼","湿润"], ["亲子游","出片","避暑"], []
  if any(k in name for k in ["沙漠","沙坡","响沙","雅丹","丹霞","魔鬼"]):
    return ["沙漠","苍凉","出片"], ["日落","摄影发烧友","干燥"], []
  if any(k in name for k in ["草原","呼伦","那拉提","巴音"]):
    return ["草原","放空","星空"], ["夏季宜人" if False else "微风","情侣","自驾相关" if False else "骑行"], []
  if any(k in name for k in ["寺","庙","佛","塔尔","布达拉","大雁","南山文化"]):
    return ["寺庙","朝圣","静谧"], ["银发游","禅意","历史爱好者"], []
  if any(k in name for k in ["博物馆","科技馆","兵马俑","伪满"]):
    return ["博物馆","寻古","研学"], ["亲子游","历史爱好者","热门"], []
  if any(k in name for k in ["森林","湿地","植物园","呀诺达","神农"]):
    return ["森林","洗肺","避暑"], ["亲子游","康养","负氧离子"], []
  if any(k in name for k in ["外滩","维多利亚","太平山顶"]):
    return ["海岸线","出片","夜景相关" if False else "浪漫"], ["热门","情侣","城市漫步" if False else "烟火气"], []
  if "喀斯特" in name or "武隆" in name or "荔波" in name or "漓江" in name:
    return ["喀斯特","峰林","出片"], ["游船相关" if False else "漂流","避暑","摄影发烧友"], []
  if "火山" in name or "五大连池" in name:
    return ["火山","地质奇观相关" if False else "猎奇","震撼"], ["研学","摄影发烧友","小众"], []
  if province in ["香港特别行政区","澳门特别行政区","台湾省"]:
    return ["出片","历史名城","慢生活"], ["情侣","美食家","热门"], []
  return ["寻幽","出片","治愈"], ["慢生活","热门","亲子游"], []

# Fix invalid tags from heuristic - filter to VALID only
def sanitize_tags(strong, weak):
  strong = [t for t in strong if t in VALID]
  weak = [t for t in weak if t in VALID]
  # pad from safe pool if short
  pool_s = ["出片","震撼","治愈","寻古","静谧","浪漫","神秘","史诗感"]
  pool_w = ["慢生活","热门","亲子游","情侣","银发游","摄影发烧友","文艺","洗肺"]
  for t in pool_s:
    if len(strong) >= 2: break
    if t in VALID and t not in strong and t not in weak: strong.append(t)
  while len(strong) < 2:
    for t in VALID:
      if t not in strong and t not in weak:
        strong.append(t); break
  for t in pool_w:
    if len(weak) >= 2: break
    if t in VALID and t not in weak and t not in strong: weak.append(t)
  strong = strong[:4]
  weak = weak[:5]
  assert 2 <= len(strong) <= 4 and 2 <= len(weak) <= 5
  assert all(t in VALID for t in strong+weak)
  return strong, weak

def make_blind(full: str) -> str:
  idxs = [i for i,c in enumerate(full) if HAN.fullmatch(c)]
  assert len(idxs) >= 2, full
  # pick two chars away from being the whole famous head: prefer mid/late Han indices
  if len(idxs) >= 5:
    a, b = idxs[2], idxs[min(4, len(idxs)-1)]
    if a == b: b = idxs[-1]
  elif len(idxs) == 4:
    a, b = idxs[1], idxs[3]
  elif len(idxs) == 3:
    a, b = idxs[0], idxs[2]
  else:
    a, b = idxs[0], idxs[1]
  if a == b:
    a, b = idxs[0], idxs[-1]
  out = []
  for i,c in enumerate(full):
    if i in (a,b):
      out.append(c)
    else:
      out.append('*')
  blind = ''.join(out)
  # validate
  lit = [i for i,c in enumerate(blind) if c != '*']
  assert len(blind) == len(full)
  assert len(lit) == 2
  assert all(HAN.fullmatch(blind[i]) for i in lit)
  assert all(full[i] == blind[i] for i in lit)
  return blind

def to_hant(hans: str, province: str) -> str:
  # minimal mapping for HK/MO/TW display names; else same
  mapping = {
    "香港维多利亚港":"香港維多利亞港",
    "香港大屿山昂坪":"香港大嶼山昂坪",
    "香港太平山顶":"香港太平山頂",
    "澳门历史城区":"澳門歷史城區",
    "澳门大三巴牌坊":"澳門大三巴牌坊",
    "台北故宫博物院":"臺北故宮博物院",
    "日月潭":"日月潭",
    "垦丁国家公园":"墾丁國家公園",
    "阿里山国家风景区":"阿里山國家風景區",
  }
  if province in ("香港特别行政区","澳门特别行政区","台湾省"):
    return mapping.get(hans, hans)
  return hans

def climate_for(province: str):
  # seasonal reference, not realtime
  table = {
    "海南省": ("22-33°C（冬暖夏热）","高湿","热带季风，夏秋需关注台风","强","台风与暴晒预警（季节性）"),
    "新疆维吾尔自治区": ("夏20-32°C / 冬严寒","干燥","盆地与山地风况差异大","强","高海拔与强紫外；冬季防寒"),
    "西藏自治区": ("昼夜温差大，夏季凉爽","偏低","高原风","极强","高原反应与强紫外预警"),
    "黑龙江省": ("夏18-28°C / 冬严寒","冬干","冬季风强","中","严寒与路面结冰"),
    "香港特别行政区": ("20-32°C","高湿","夏秋台风季","强","台风与暴雨需关注"),
    "澳门特别行政区": ("20-32°C","高湿","夏秋台风季","强","台风与暴雨需关注"),
    "台湾省": ("18-32°C","湿润","夏秋台风、山区多雾","强","台风与山区天气突变"),
  }
  for k,v in table.items():
    if province.startswith(k[:2]) or province == k:
      t,h,w,u,a = v
      return {"temp":t,"humidity":h,"wind":w,"uv_index":u,"alert":a,"evidence_basis":"公开气候带描述，非实时气象"}
  if province in ("广东省","广西壮族自治区","福建省"):
    return {"temp":"冬暖夏热，约12-33°C","humidity":"偏湿","wind":"沿海季风明显","uv_index":"强","alert":"夏秋关注台风与强对流","evidence_basis":"华南气候公开描述"}
  if province in ("云南省","贵州省","四川省","重庆市"):
    return {"temp":"高原/盆地差异大，多在10-28°C","humidity":"湿润或干湿季分明","wind":"山区阵风","uv_index":"中到强","alert":"山区天气多变，注意道路与落石信息","evidence_basis":"西南气候公开描述"}
  if province in ("甘肃省","青海省","宁夏回族自治区","陕西省","内蒙古自治区"):
    return {"temp":"昼夜温差大，冬寒夏凉","humidity":"偏干燥","wind":"风力常偏大","uv_index":"强","alert":"防风沙与强紫外；高海拔注意缺氧","evidence_basis":"西北/高原气候公开描述"}
  return {"temp":"四季分明，约-5-32°C（因城而异）","humidity":"中等","wind":"季风影响","uv_index":"中到强","alert":"按季节防暑或防寒防滑","evidence_basis":"中国东部季风区公开气候描述"}

def char_len(s): return len(s)

def fit_desc(province, city, theme_bits, strong):
  # 200-300 chars, no full name
  base = (
    f"这里位于{province}{city}一带，是公开旅游信息中常被提起的目的地之一。"
    f"周边交通与开放安排以官方最新公告为准，建议出发前复核票务与预约规则。"
    f"现场以{theme_bits}见长，适合用步行或景区内交通串联主要观览面。"
    f"人流在节假日往往上升，错峰更能保留观察细节的节奏。"
    f"气候随季节变化明显，请按当季穿衣并预留体力缓冲。"
    f"本条描述只保留省域与城市方位，不展开可直接指认的专名细节。"
  )
  # adjust length
  while char_len(base) < 200:
    base += "公共导览与安全提示应以景区管理部门发布内容为优先依据。"
  if char_len(base) > 300:
    base = base[:300]
  # ensure 200-300
  if char_len(base) < 200:
    base = base + "（资料核对中。）"
  return base

def fit_summary(province, city, hook):
  s = f"地处{province}{city}，{hook}。建议提前查官方开放与交通，错峰前往，按体力选择路线。"
  while char_len(s) < 80:
    s += "出发前再核票价与预约。"
  if char_len(s) > 120:
    s = s[:120]
  return s

def interp_for(tag, province, city):
  # 100-150 chars each, blinded, no full spot name
  templates = {
    "古建": f"【古建】在{province}{city}的历史街区尺度里，屋脊、梁架与庭院秩序仍可读出传统营造逻辑。建议放慢脚步对照公开导览理解形制层级，避免只拍照不看结构。午后光线有助于观察斗栱与屋面细节，注意保护文物、不触碰警示区域。",
    "博物馆": f"【博物馆】{province}{city}这一馆类场所把器物、档案与叙事并置，适合按主题展线参观。公开须知通常强调预约与包袋安检，请预留安检时间。讲解或语音导览能降低“只看热闹”的信息损失，摄影是否允许以现场标识为准。",
    "历史名城": f"【历史名城】{province}{city}的街巷肌理与公共节点彼此咬合，适合用步行串联城墙、河道或纪念性广场。早或晚人流较可控，也更易观察居民日常节奏。请尊重祭祀与居住空间，不打断地方仪式。",
    "长城": f"【长城】在{province}北缘山地，墙体随脊线起伏，台阶落差大。公开行程建议量力而行并注意防滑，风大时收纳好帽绳与无人机。日出前后光影层次更清楚，但请遵守封闭段落禁入规定。",
    "登山": f"【登山】{province}{city}周边山体线路常见台阶与索道组合，体力分配比“登顶口号”更重要。携带饮水与防风层，雷雨临时下撤。官方风险提示与关闭通知优先于口头传闻。",
    "震撼": f"【震撼】尺度与纵深会在转角处突然打开，{province}一带的地貌或建筑群常带来强烈第一眼印象。建议先找观景平台建立方位，再进入细部。保持安全距离，不翻越护栏追取景。",
    "园林": f"【园林】在{province}{city}的园景传统里，借景、障景与水岸廊道相互配合。雨后苔石湿滑，请穿防滑鞋。沿主游线走完再岔入小径，不容易漏掉经典对景。",
    "湖泊": f"【湖泊】水面倒影与岸线植被是{province}{city}常见的舒缓界面。黄昏风向转强时浪花更大，游船是否开航看当日公告。环湖骑行或步行都能降低交通折返成本。",
    "海岸线": f"【海岸线】{province}沿海段落潮汐与季风影响明显，晨昏对比度高。注意礁石湿滑与浪高警告旗。防晒与补水比“打卡时长”更关键，夜间临海请走灯光明亮段。",
    "看海": f"【看海】把视线放到海平线，城市噪声会被风声替换。{province}沿海能见度受雾与阵雨影响，可备薄外套。不进入未开放滩涂，不追赶涨潮线。",
    "古镇": f"【古镇】街巷尺度紧凑，烟火与旅拍需求并存。{province}{city}同类目的地建议早进晚出，避开主街高峰钻支巷。消费前确认标价，尊重居民生活区域的拍摄边界。",
    "寻古": f"【寻古】把碑刻、老桥、旧码头放进时间轴看，比单点打卡更有收获。{province}公共文保说明牌是第一手线索，可与博物馆叙事交叉验证。禁止拓印或刻画。",
    "石窟": f"【石窟】洞窟光环境弱，色温变化快。{province}相关遗产地通常限制闪光与触摸。跟随指定路线，听讲解理解年代层位，比追“网红窟号”更稳妥。",
    "非遗": f"【非遗】工艺与节庆是活态的，{province}{city}现场体验以官方或社区公开排期为准。参与体验时问清是否可拍照，付费项目索取票据。把“看热闹”升级为“看门道”。",
    "民族风": f"【民族风】服饰、音乐与建筑装饰构成强烈视觉识别。在{province}请先观察礼仪再互动，不强行邀拍。购买手作优先标明产地与材质的摊位，拒绝来路不明的野生动物制品。",
    "寺庙": f"【寺庙】香火与园林并存，进入殿堂保持安静。{province}同类场所常有着装与摄影限制，请服从现场管理。清晨氛围更静，也便于理解中轴线序列。",
    "朝圣": f"【朝圣】把行程节奏放慢，关注呼吸与海拔适应。{province}高海拔或长距离朝线路段需预留缓冲日。尊重转经与礼拜空间，不抢道、不高声。",
    "瀑布": f"【瀑布】水汽重、地面湿，设备需防水。{province}雨季流量大但险段可能关闭。观景台拍照即可，不靠近警戒线下的湿岩。",
    "喀斯特": f"【喀斯特】峰丛、洼地与地下河构成立体地貌。{province}相关景区船步结合常见，救生衣按规定穿戴。溶洞内注意温差与头顶滴水。",
    "峰林": f"【峰林】远观轮廓、近看岩性纹理。{province}能见度受雾影响大，可改走博物馆或地质说明点。无人机是否开放看公告。",
    "沙漠": f"【沙漠】风沙与强光同时出现，护目与口罩有用。{province}西北沙漠景区多有滑沙/驼队项目，以正规运营商安全说明为准，不擅自离开标识区。",
    "苍凉": f"【苍凉】空旷界面让人重新校准时间感。{province}这类地貌早晚温差大，备一层抓绒。摄影时注意沙尘对器材的磨损。",
    "草原": f"【草原】天际线低、天气翻脸快。{province}夏季是常见出行窗，仍要防紫外与阵雨。不进入未开放牧场，不惊扰牲畜。",
    "星空": f"【星空】光污染低的开阔地更易看见银河轮廓。{province}高海拔或干旱区常见，但夜间保暖与回程交通要先计划。遵守景区夜游规定。",
    "火山": f"【火山】熔岩台地与湖沼并置，地质科普牌值得细读。{province}相关园区多有木栈道，请勿踩踏脆弱植被。雨后岩石更滑。",
    "森林": f"【森林】负氧离子与荫蔽步道适合放慢心率。{province}林区蚊虫与潮湿需准备。遇恶劣天气以关闭通知为准，不抄近道。",
    "洗肺": f"【洗肺】把城市颗粒物抛在山风之后。选择清晨或雨后空气更清的时段，在{province}林区或湖岸做低强度步行即可，无需高强度打卡。",
    "避暑": f"【避暑】海拔或水体能拉低体感温度。{province}夏季仍可能暴晒，防晒不能省。午间安排室内展陈或荫蔽段。",
    "出片": f"【出片】光比与前景遮幅决定成片。{province}{city}热门机位人多，可前后错开15-20分钟。不阻塞通道，不踩踏草坪花境。",
    "治愈": f"【治愈】把日程留白，允许发呆。{province}的水岸、林窗或庭园边角比主街更适合恢复注意力。手机飞行模式一小时会很值。",
    "浪漫": f"【浪漫】黄昏色温对两人行程更友好。{province}{city}滨水或山脊步道常见，注意防风与安全返程时间。预约晚餐避免空腹赶路。",
    "静谧": f"【静谧】人声降下去，材料与风声才出现。尽量选择非节假日清晨进入{province}相关场所，关闭外放音乐。",
    "寻幽": f"【寻幽】支线步道与肩季节是关键。在{province}先完成主环线再岔入，带够水电。告知同行预计返回点。",
    "研学": f"【研学】带着问题清单进场：年代、材料、功能、保护措施。{province}公共讲解与官方手册优先，网络传言次之。",
    "奇峰": f"【奇峰】垂直节理与云雾共同塑造轮廓。{province}山区索道与步道换乘要预留排队时间，关注雷电预警。",
    "云海": f"【云海】需要水汽与逆温配合，无法保证每天出现。{province}山岳区凌晨到上午概率更高，保暖与头灯要备。",
    "漂流": f"【漂流】以正规漂流段与救生配置为准，听指挥。{province}雨后水位上涨可能停漂，不要自行下水。",
    "慢生活": f"【慢生活】把交通换成步行，把购物换成观察。{province}{city}老街区适合这种节奏，午后茶歇也能算行程的一部分。",
  }
  if tag in templates:
    text = templates[tag]
  else:
    text = (
      f"【{tag}】在{province}{city}的旅行语境里，这一标签指向可感知的氛围与活动方式，而不是口号。"
      f"建议结合官方导览与现场标识安排停留，保持安全距离与礼仪。"
      f"把拍照放在理解之后，行程会更稳。"
      f"气候与开放状态请出发前再核。"
    )
  # clamp 100-150
  if char_len(text) < 100:
    text += "资料以公开渠道为准，不替代现场管理规定。"
  if char_len(text) > 150:
    # trim carefully at char boundary
    text = text[:150]
  # ensure still has 【tag】
  if f"【{tag}】" not in text:
    text = f"【{tag}】" + text
  return text

# Theme hooks for summary (blinded)
HOOKS = {
"故宫博物院":"以明清宫城格局与馆藏展览为核心的城市文化目的地",
"八达岭长城":"京北山地长城步道与城台视野具有代表性",
"颐和园":"以大型皇家园林水岸与廊道游线闻名",
}

def theme_bits_for(name, strong):
  return "、".join(strong[:3])
