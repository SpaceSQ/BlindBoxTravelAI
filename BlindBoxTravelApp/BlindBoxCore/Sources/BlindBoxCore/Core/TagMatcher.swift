import Foundation

/// 强弱标签匹配、进化变量加权、季节适配与动态随机温度（PRD §2.1 Step 3）。
public enum TagMatcher {
    public static let strongWeight = 3.0
    public static let weakWeight = 1.0

    static let seasonTags: [String: Set<String>] = [
        "春": ["踏青", "赏梅", "樱花季", "花海", "梯田放水"],
        "夏": ["避暑", "溯溪", "漂流", "戏水", "看海", "赶海", "溶洞避暑"],
        "秋": ["赏秋", "红叶", "银杏黄了", "观潮", "赏月"],
        "冬": ["看雪", "滑雪", "雾凇", "冰雕", "温泉", "暖冬", "避寒", "冰天雪地", "玩雪"],
    ]

    public static func tagWeight(_ type: TagType) -> Double {
        type == .strong ? strongWeight : weakWeight
    }

    /// 将月份映射到季节（北半球）。
    public static func seasonForMonth(_ month: Int) -> String {
        switch month {
        case 3 ... 5: return "春"
        case 6 ... 8: return "夏"
        case 9 ... 11: return "秋"
        default: return "冬"
        }
    }

    /// 汇总路线所有景点的标签，返回 {标签名: 类型}；同名标签取更高级别（strong 优先）。
    public static func collectRouteTags(_ route: Route, spotsById: [String: Spot]) -> [String: TagType] {
        var tags: [String: TagType] = [:]
        for sid in route.spotIds {
            guard let spot = spotsById[sid] else { continue }
            for t in spot.tags {
                if tags[t.name] == nil || t.type == .strong {
                    tags[t.name] = t.type
                }
            }
        }
        return tags
    }

    /// 路线与用户意图标签的重合度：strong=3.0、weak=1.0 的加权和。
    public static func tagMatch(_ route: Route, spotsById: [String: Spot], matchedTags: [String]) -> Double {
        let tags = collectRouteTags(route, spotsById: spotsById)
        var score = 0.0
        for mt in matchedTags {
            if let t = tags[mt] {
                score += tagWeight(t)
            }
        }
        return score
    }

    /// 季节适配度：命中本季标签 1.0、无季节标签 0.5、命中他季标签 0.2。
    public static func seasonFit(_ route: Route, spotsById: [String: Spot], month: Int) -> Double {
        let season = seasonForMonth(month)
        let tags = Set(collectRouteTags(route, spotsById: spotsById).keys)
        if let current = seasonTags[season], !tags.isDisjoint(with: current) {
            return 1.0
        }
        let allSeason = seasonTags.values.reduce(into: Set<String>()) { $0.formUnion($1) }
        if !tags.isDisjoint(with: allSeason) {
            return 0.2
        }
        return 0.5
    }

    /// 进化变量热度：log(1 + plan + 2·review)。
    public static func popularity(_ stats: EvolutionStats) -> Double {
        log1p(Double(stats.planMarkCount) + 2.0 * Double(stats.reviewCount))
    }

    /// 随机温度系数：specificity 0→0.85，1→0.15，线性插值。
    public static func temperature(specificity: Double) -> Double {
        let s = min(1.0, max(0.0, specificity))
        return 0.85 - 0.7 * s
    }
}
