import Foundation

/// 可复现的确定性伪随机数发生器（测试与“每日种子”使用）。
public struct SeededGenerator: RandomNumberGenerator {
    private var state: UInt64

    public init(seed: UInt64) {
        state = seed &+ 0x9E37_79B9_7F4A_7C15
    }

    public mutating func next() -> UInt64 {
        state = state &* 6364136223846793005 &+ 1442695040888963407
        return state
    }
}

/// 推荐引擎：距离筛选 + 综合打分 + 动态随机 + 前 3 条（首条重点推荐）。
///
/// 流程（PRD §2.1 Step 1~4）：
/// 1. 距离筛选：多景点路线以首站景点距离满足阈值为准（交底书 §3.2.3）；
/// 2. 综合打分 = w_tag·TagMatch + w_season·SeasonFit + w_pop·Popularity + 天数软加分；
/// 3. 叠加与具体度成反比的随机扰动 ε_random；
/// 4. 取前 3 条，第 1 条 is_featured=true；距离内候选不足 3 条时自动放宽距离补齐。
public enum RecommendationEngine {
    public static let defaultMaxDistanceKm = 6000
    public static let distanceOptionsKm = [500, 1000, 2000, 3000, 4000, 5000, 6000]

    static let wTag = 1.0
    static let wSeason = 0.6
    static let wPop = 0.4
    static let wDuration = 0.3

    /// 路线首站景点到出发地的距离（公里）。
    public static func firstStopDistanceKm(_ route: Route, spotsById: [String: Spot], originLat: Double, originLng: Double) -> Double {
        guard let firstId = route.spotIds.first, let first = spotsById[firstId] else {
            return .greatestFiniteMagnitude
        }
        return Haversine.distanceKm(lat1: originLat, lng1: originLng, lat2: first.location.lat, lng2: first.location.lng)
    }

    /// 返回首站距离 ≤ maxKm 的路线（保持原顺序）。
    public static func filterByDistance(
        _ routes: [Route],
        spotsById: [String: Spot],
        originLat: Double,
        originLng: Double,
        maxKm: Double
    ) -> [Route] {
        routes.filter {
            firstStopDistanceKm($0, spotsById: spotsById, originLat: originLat, originLng: originLng) <= maxKm
        }
    }

    /// 确定性综合打分（不含随机扰动）。
    public static func baseScore(
        _ route: Route,
        spotsById: [String: Spot],
        matchedTags: [String],
        month: Int,
        durationDays: Int?
    ) -> Double {
        let tagMatch = TagMatcher.tagMatch(route, spotsById: spotsById, matchedTags: matchedTags)
        let seasonFit = TagMatcher.seasonFit(route, spotsById: spotsById, month: month)
        let pop = TagMatcher.popularity(route.evolutionStats)

        var durationBonus = 0.0
        if let durationDays {
            let diff = abs(route.durationDays - durationDays)
            durationBonus = max(0.0, 1.0 - 0.5 * Double(diff))
        }

        return wTag * tagMatch + wSeason * seasonFit + wPop * pop + wDuration * durationBonus
    }

    /// 生成最多 3 条推荐（首条 is_featured）。
    ///
    /// - Parameters:
    ///   - specificity: 意图具体度（0~1），越高随机扰动越小。
    ///   - seed: 提供时使用确定性随机（便于测试/每日种子），否则使用系统随机。
    ///   - applyRandom: 关闭后为纯确定性排序。
    public static func recommend(
        routes: [Route],
        spotsById: [String: Spot],
        originLat: Double,
        originLng: Double,
        matchedTags: [String] = [],
        maxDistanceKm: Int? = nil,
        durationDays: Int? = nil,
        month: Int? = nil,
        specificity: Double = 0.5,
        seed: UInt64? = nil,
        applyRandom: Bool = true
    ) -> [Route] {
        let month = month ?? 6
        let maxDist = Double(maxDistanceKm ?? defaultMaxDistanceKm)

        var inRange: [Route] = []
        var outOfRange: [Route] = []
        for route in routes {
            if firstStopDistanceKm(route, spotsById: spotsById, originLat: originLat, originLng: originLng) <= maxDist {
                inRange.append(route)
            } else {
                outOfRange.append(route)
            }
        }

        func scored(_ items: [Route], generator: inout some RandomNumberGenerator) -> [(score: Double, route: Route)] {
            var rows: [(score: Double, route: Route)] = []
            for route in items {
                var base = baseScore(route, spotsById: spotsById, matchedTags: matchedTags, month: month, durationDays: durationDays)
                if applyRandom {
                    let eps = TagMatcher.temperature(specificity: specificity) * Double.random(in: -1.0 ... 1.0, using: &generator)
                    base += eps
                }
                rows.append((base, route))
            }
            rows.sort { $0.score > $1.score }
            return rows
        }

        let top: [Route]
        if let seed {
            var gen = SeededGenerator(seed: seed)
            top = scored(inRange, generator: &gen).prefix(3).map(\.route)
        } else {
            var gen = SystemRandomNumberGenerator()
            top = scored(inRange, generator: &gen).prefix(3).map(\.route)
        }

        var result = top
        if result.count < 3 {
            let remaining: [Route]
            if let seed {
                var gen = SeededGenerator(seed: seed &+ 1)
                remaining = scored(outOfRange, generator: &gen).map(\.route)
            } else {
                var gen = SystemRandomNumberGenerator()
                remaining = scored(outOfRange, generator: &gen).map(\.route)
            }
            for route in remaining where result.count < 3 {
                result.append(route)
            }
        }

        return result.enumerated().map { i, route in
            var r = route
            r.isFeatured = (i == 0)
            return r
        }
    }
}
