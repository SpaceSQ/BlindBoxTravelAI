# 标签语义复核 tag_semantic_review

范围：仅修改 `routes/spots_route_additions.json` 中语义错标签及其对应 `tag_interpretation`；来源/ID/坐标/票价/图片未改；父锁定基础、路线、`data/`、Git、Mac 未触碰。

## 六处强制纠偏（新旧 tags）

### SP120 厦门沙坡尾

| | tags |
|---|---|
| 旧 | [{"name": "沙漠", "type": "strong"}, {"name": "苍凉", "type": "strong"}, {"name": "出片", "type": "strong"}, {"name": "日落", "type": "weak"}, {"name": "摄影发烧友", "type": "weak"}, {"name": "干燥", "type": "weak"}] |
| 新 | [{"name": "海岸线", "type": "strong"}, {"name": "寻幽", "type": "strong"}, {"name": "出片", "type": "strong"}, {"name": "日落", "type": "weak"}, {"name": "摄影发烧友", "type": "weak"}, {"name": "微风", "type": "weak"}] |

- 纠偏要点：已去除错误地貌/建筑类型标签，并重写全部 strong 对应解读（各约 100–150 字），不再保留“因本轮要求保留错误标签”表述。

### SP141 西安城墙

| | tags |
|---|---|
| 旧 | [{"name": "古建", "type": "strong"}, {"name": "长城", "type": "strong"}, {"name": "历史名城", "type": "strong"}, {"name": "骑行", "type": "weak"}, {"name": "出片", "type": "weak"}, {"name": "热门", "type": "weak"}] |
| 新 | [{"name": "古建", "type": "strong"}, {"name": "历史名城", "type": "strong"}, {"name": "寻古", "type": "strong"}, {"name": "骑行", "type": "weak"}, {"name": "出片", "type": "weak"}, {"name": "热门", "type": "weak"}] |

- 纠偏要点：已去除错误地貌/建筑类型标签，并重写全部 strong 对应解读（各约 100–150 字），不再保留“因本轮要求保留错误标签”表述。

### SP154 景山公园

| | tags |
|---|---|
| 旧 | [{"name": "登山", "type": "strong"}, {"name": "奇峰", "type": "strong"}, {"name": "震撼", "type": "strong"}, {"name": "体力怪", "type": "weak"}, {"name": "云海", "type": "weak"}, {"name": "避暑", "type": "weak"}] |
| 新 | [{"name": "园林", "type": "strong"}, {"name": "寻幽", "type": "strong"}, {"name": "出片", "type": "strong"}, {"name": "寻古", "type": "strong"}, {"name": "历史爱好者", "type": "weak"}, {"name": "慢生活", "type": "weak"}, {"name": "文青", "type": "weak"}] |

- 纠偏要点：已去除错误地貌/建筑类型标签，并重写全部 strong 对应解读（各约 100–150 字），不再保留“因本轮要求保留错误标签”表述。

### SP156 婺源篁岭

| | tags |
|---|---|
| 旧 | [{"name": "登山", "type": "strong"}, {"name": "奇峰", "type": "strong"}, {"name": "震撼", "type": "strong"}, {"name": "体力怪", "type": "weak"}, {"name": "云海", "type": "weak"}, {"name": "避暑", "type": "weak"}] |
| 新 | [{"name": "梯田", "type": "strong"}, {"name": "赏秋", "type": "strong"}, {"name": "出片", "type": "strong"}, {"name": "摄影", "type": "weak"}, {"name": "亲子", "type": "weak"}, {"name": "农家乐", "type": "weak"}] |

- 纠偏要点：已去除错误地貌/建筑类型标签，并重写全部 strong 对应解读（各约 100–150 字），不再保留“因本轮要求保留错误标签”表述。

### SP167 香港故宫文化博物馆

| | tags |
|---|---|
| 旧 | [{"name": "博物馆", "type": "strong"}, {"name": "寻古", "type": "strong"}, {"name": "古建", "type": "strong"}, {"name": "研学", "type": "weak"}, {"name": "热门", "type": "weak"}, {"name": "银发游", "type": "weak"}] |
| 新 | [{"name": "博物馆", "type": "strong"}, {"name": "寻古", "type": "strong"}, {"name": "沉浸式", "type": "strong"}, {"name": "研学", "type": "weak"}, {"name": "热门", "type": "weak"}, {"name": "银发游", "type": "weak"}] |

- 纠偏要点：已去除错误地貌/建筑类型标签，并重写全部 strong 对应解读（各约 100–150 字），不再保留“因本轮要求保留错误标签”表述。

### SP172 巴音布鲁克景区

| | tags |
|---|---|
| 旧 | [{"name": "草原", "type": "strong"}, {"name": "湖泊", "type": "strong"}, {"name": "星空", "type": "strong"}, {"name": "自驾", "type": "weak"}, {"name": "日落", "type": "weak"}, {"name": "苍凉", "type": "weak"}] |
| 新 | [{"name": "草原", "type": "strong"}, {"name": "湿地", "type": "strong"}, {"name": "星空", "type": "strong"}, {"name": "自驾", "type": "weak"}, {"name": "日落", "type": "weak"}, {"name": "牧家乐", "type": "weak"}] |

- 纠偏要点：已去除错误地貌/建筑类型标签，并重写全部 strong 对应解读（各约 100–150 字），不再保留“因本轮要求保留错误标签”表述。

## 抽检

### SP137 天门山旅游景区

- 结论：**真实匹配，未改**
- 当前 tags：`[{"name": "奇峰", "type": "strong"}, {"name": "登山", "type": "strong"}, {"name": "震撼", "type": "strong"}, {"name": "缆车", "type": "weak"}, {"name": "云海", "type": "weak"}, {"name": "体力怪", "type": "weak"}]`
- 说明：山岳景区，奇峰/登山/震撼 + 缆车/云海/体力怪 与陡峭山体及转场设施相符；文案已区分体力和云雾不确定性。

### SP142 西安钟鼓楼

- 结论：**语义偏弱，已一并纠**
- 旧 tags：`[{"name": "寻幽", "type": "strong"}, {"name": "出片", "type": "strong"}, {"name": "治愈", "type": "strong"}, {"name": "慢生活", "type": "weak"}, {"name": "热门", "type": "weak"}, {"name": "亲子游", "type": "weak"}]`
- 新 tags：`[{"name": "古建", "type": "strong"}, {"name": "历史名城", "type": "strong"}, {"name": "出片", "type": "strong"}, {"name": "热门", "type": "weak"}, {"name": "烟火气", "type": "weak"}, {"name": "打卡", "type": "weak"}]`
- 说明：原强标签偏情绪（寻幽/治愈），对中心传统楼阁表达不足；改为古建/历史名城/出片，弱标签热门/烟火气/打卡，并重写解读。

### SP185 柳州螺蛳粉小镇

- 结论：**真实匹配，未改**
- 当前 tags：`[{"name": "嗦粉", "type": "strong"}, {"name": "碳水之都", "type": "strong"}, {"name": "逛吃", "type": "strong"}, {"name": "烟火气", "type": "weak"}, {"name": "出片", "type": "weak"}, {"name": "热门", "type": "weak"}, {"name": "亲子游", "type": "weak"}]`
- 说明：美食主题空间，嗦粉/碳水之都/逛吃 与地方饮食体验一致；弱标签烟火气/出片/热门/亲子游合理。

### SP186 乌兰察布火山地质公园

- 结论：**真实匹配，未改**
- 当前 tags：`[{"name": "火山", "type": "strong"}, {"name": "猎奇", "type": "strong"}, {"name": "震撼", "type": "strong"}, {"name": "苍凉", "type": "weak"}, {"name": "废土风", "type": "weak"}, {"name": "出片", "type": "weak"}, {"name": "干燥", "type": "weak"}, {"name": "研学", "type": "weak"}]`
- 说明：火山地质公园，火山/猎奇/震撼 与锥形山体、裸岩草地反差相符；弱标签苍凉/废土风/出片/干燥/研学在 2–5 范围内且贴合风貌。

## 校验备忘

- 每条均为 2–4 strong + 2–5 weak；名称均取自 `data/tags_500.json` 真实数组（只读核对，未改该文件）。
- `description` / `summary_100w`：六条正文此前已按正确地貌书写，本轮未做大改；仅标签与解读纠语义。
- SP141 未使用库外「城防」字样，第三强标签选用库内「寻古」表达城垣寻访。
- SP156 库无「徒步」标签，弱标签采用「摄影 / 亲子 / 农家乐」。
- SP172 第三弱标签选用「牧家乐」，贴合草原风貌；已去掉不精确的强标签「湖泊」。
