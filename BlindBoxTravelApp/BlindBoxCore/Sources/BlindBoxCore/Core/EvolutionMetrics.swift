import Foundation

/// 进化算法匿名统计变量库（`data/evolution_metrics.json` 结构）。
///
/// 严格零溯源：仅记录每个景点/路线被标注成计划(plan_mark_count)与被点评(review_count)
/// 的匿名累计次数，绝不包含任何用户身份或点评来源字段。
public struct EvolutionMetrics: Codable, Equatable, Sendable {
    public var lastUpdated: Date
    public var spotsMetrics: [String: EvolutionStats]
    public var routesMetrics: [String: EvolutionStats]

    public init(
        lastUpdated: Date = Date(),
        spotsMetrics: [String: EvolutionStats] = [:],
        routesMetrics: [String: EvolutionStats] = [:]
    ) {
        self.lastUpdated = lastUpdated
        self.spotsMetrics = spotsMetrics
        self.routesMetrics = routesMetrics
    }

    enum CodingKeys: String, CodingKey {
        case lastUpdated = "last_updated"
        case spotsMetrics = "spots_metrics"
        case routesMetrics = "routes_metrics"
    }

    // MARK: - 读取

    public func stats(spotId: String) -> EvolutionStats {
        spotsMetrics[spotId] ?? EvolutionStats()
    }

    public func stats(routeId: String) -> EvolutionStats {
        routesMetrics[routeId] ?? EvolutionStats()
    }

    // MARK: - 应用增量

    /// 将匿名增量合并进本库，返回新的 metrics（纯函数）。
    public func applying(_ deltas: [EvolutionDelta], now: Date = Date()) -> EvolutionMetrics {
        var result = self
        for delta in deltas {
            switch delta.scope {
            case .spot:
                var stats = result.spotsMetrics[delta.id] ?? EvolutionStats()
                stats.planMarkCount += delta.planMarkIncrement
                stats.reviewCount += delta.reviewIncrement
                result.spotsMetrics[delta.id] = stats
            case .route:
                var stats = result.routesMetrics[delta.id] ?? EvolutionStats()
                stats.planMarkCount += delta.planMarkIncrement
                stats.reviewCount += delta.reviewIncrement
                result.routesMetrics[delta.id] = stats
            }
        }
        result.lastUpdated = now
        return result
    }

    /// 将库中最新计数覆盖到景点列表（供推荐排序读取最新热度）。
    public func applying(to spots: [Spot]) -> [Spot] {
        spots.map { spot in
            var s = spot
            s.evolutionStats = stats(spotId: spot.id)
            return s
        }
    }

    /// 将库中最新计数覆盖到路线列表（供推荐排序读取最新热度）。
    public func applying(to routes: [Route]) -> [Route] {
        routes.map { route in
            var r = route
            r.evolutionStats = stats(routeId: route.id)
            return r
        }
    }

    // MARK: - 序列化

    public func encoded() throws -> Data {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.sortedKeys]
        return try encoder.encode(self)
    }

    public static func decode(_ data: Data) throws -> EvolutionMetrics {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(EvolutionMetrics.self, from: data)
    }

    /// 从 data/evolution_metrics.json 的原始结构（含 repository/privacy_policy/description 顶层字段）解码。
    /// 宽容处理：顶层附加字段被忽略。
    public static func decode(seedData data: Data) throws -> EvolutionMetrics {
        try decode(data)
    }
}

/// 单条匿名增量：对某个景点或路线累加 plan_mark / review 计数。
public struct EvolutionDelta: Codable, Equatable, Sendable {
    public enum Scope: String, Codable, Sendable, Equatable {
        case spot
        case route
    }

    public let scope: Scope
    public let id: String
    public var planMarkIncrement: Int
    public var reviewIncrement: Int

    /// 唯一标识（跨 scope 唯一）。
    public var deltaID: String { "\(scope.rawValue)_\(id)" }

    public init(scope: Scope, id: String, planMarkIncrement: Int = 0, reviewIncrement: Int = 0) {
        self.scope = scope
        self.id = id
        self.planMarkIncrement = planMarkIncrement
        self.reviewIncrement = reviewIncrement
    }
}

/// 从“生成计划行程单”行为推导匿名增量：路线 + 沿途每个景点各 plan_mark +1。
public enum EvolutionDeltaFactory {
    public static func planOrderDeltas(route: Route, spots: [Spot]) -> [EvolutionDelta] {
        var deltas: [EvolutionDelta] = [
            EvolutionDelta(scope: .route, id: route.id, planMarkIncrement: 1),
        ]
        for spot in spots {
            deltas.append(EvolutionDelta(scope: .spot, id: spot.id, planMarkIncrement: 1))
        }
        return deltas
    }

    /// 从“标注/点评”行为推导匿名增量：路线 + 沿途每个景点各 review +1。
    public static func reviewDeltas(route: Route, spots: [Spot]) -> [EvolutionDelta] {
        var deltas: [EvolutionDelta] = [
            EvolutionDelta(scope: .route, id: route.id, reviewIncrement: 1),
        ]
        for spot in spots {
            deltas.append(EvolutionDelta(scope: .spot, id: spot.id, reviewIncrement: 1))
        }
        return deltas
    }
}
