import Foundation

// MARK: - 共享枚举

/// 标签权重类型：strong 权重 3.0，weak 权重 1.0。
public enum TagType: String, Codable, Sendable, Equatable {
    case strong
    case weak
}

/// 行程路线类型：单一景点路线 或 多景点串联路线。
public enum RouteType: String, Codable, Sendable, Equatable {
    case singleSpot = "single_spot"
    case multiSpot = "multi_spot"
}

/// 订单状态：待出行 / 已出行 / 计划改变 / 计划取消 / 已删除。
public enum OrderStatus: String, Codable, Sendable, Equatable {
    case planned
    case completed
    case modified
    case cancelled
    case deleted
}

/// 出发交通方式。
public enum TransportMode: String, Codable, CaseIterable, Identifiable, Sendable {
    case selfDrive = "自驾"
    case highSpeedRail = "高铁动车"
    case flight = "飞机"
    case bus = "大巴"
    case cycling = "骑行"

    public var id: String { rawValue }
}

// MARK: - 景点（Spot）

public struct SpotLocation: Codable, Sendable, Equatable {
    public let lat: Double
    public let lng: Double

    public init(lat: Double, lng: Double) {
        self.lat = lat
        self.lng = lng
    }
}

public struct MockWeather: Codable, Sendable, Equatable {
    public let temp: String
    public let humidity: String
    public let wind: String
    public let uvIndex: String
    public let alert: String

    enum CodingKeys: String, CodingKey {
        case temp, humidity, wind, alert
        case uvIndex = "uv_index"
    }
}

/// 进化算法匿名统计变量（严格无溯源）。
public struct EvolutionStats: Codable, Sendable, Equatable {
    public var planMarkCount: Int
    public var reviewCount: Int

    public init(planMarkCount: Int = 0, reviewCount: Int = 0) {
        self.planMarkCount = planMarkCount
        self.reviewCount = reviewCount
    }

    enum CodingKeys: String, CodingKey {
        case planMarkCount = "plan_mark_count"
        case reviewCount = "review_count"
    }
}

public struct SpotTag: Codable, Sendable, Equatable, Hashable {
    public let name: String
    public let type: TagType
}

public struct Spot: Codable, Sendable, Identifiable, Equatable {
    public let id: String          // spot_id
    public let fullName: String
    public let blindName: String
    public let province: String
    public let city: String
    public let location: SpotLocation
    public let tags: [SpotTag]
    public let description: String
    public let summary100w: String
    public let imageUrl: String
    public let adultTicketPrice: Int
    public let mockWeather: MockWeather
    public let eventsAndDiscounts: String
    public let aiStrategy: String
    public let tagInterpretation: String
    public var evolutionStats: EvolutionStats

    enum CodingKeys: String, CodingKey {
        case id = "spot_id"
        case fullName = "full_name"
        case blindName = "blind_name"
        case province, city, location, tags, description
        case summary100w = "summary_100w"
        case imageUrl = "image_url"
        case adultTicketPrice = "adult_ticket_price"
        case mockWeather = "mock_weather"
        case eventsAndDiscounts = "events_and_discounts"
        case aiStrategy = "ai_strategy"
        case tagInterpretation = "tag_interpretation"
        case evolutionStats = "evolution_stats"
    }
}

// MARK: - 路线（Route）

public struct DailyScheduleItem: Codable, Sendable, Equatable {
    public let day: Int
    public let spotId: String
    public let blindHighlights: String

    enum CodingKeys: String, CodingKey {
        case day
        case spotId = "spot_id"
        case blindHighlights = "blind_highlights"
    }
}

public struct Route: Codable, Sendable, Identifiable, Equatable {
    public let id: String            // route_id
    public let fullRouteTitle: String
    public let blindRouteTitle: String
    public let durationDays: Int
    public let routeType: RouteType
    public let spotIds: [String]
    public let regionTag: String
    public let searchKeywordsMatched: [String]
    public let dailySchedule: [DailyScheduleItem]
    public var evolutionStats: EvolutionStats

    /// 推荐态标记（非 JSON 字段，由推荐引擎写入）。
    public var isFeatured: Bool = false

    public init(
        id: String,
        fullRouteTitle: String,
        blindRouteTitle: String,
        durationDays: Int,
        routeType: RouteType,
        spotIds: [String],
        regionTag: String,
        searchKeywordsMatched: [String],
        dailySchedule: [DailyScheduleItem],
        evolutionStats: EvolutionStats = EvolutionStats(),
        isFeatured: Bool = false
    ) {
        self.id = id
        self.fullRouteTitle = fullRouteTitle
        self.blindRouteTitle = blindRouteTitle
        self.durationDays = durationDays
        self.routeType = routeType
        self.spotIds = spotIds
        self.regionTag = regionTag
        self.searchKeywordsMatched = searchKeywordsMatched
        self.dailySchedule = dailySchedule
        self.evolutionStats = evolutionStats
        self.isFeatured = isFeatured
    }

    enum CodingKeys: String, CodingKey {
        case id = "route_id"
        case fullRouteTitle = "full_route_title"
        case blindRouteTitle = "blind_route_title"
        case durationDays = "duration_days"
        case routeType = "route_type"
        case spotIds = "spot_ids"
        case regionTag = "region_tag"
        case searchKeywordsMatched = "search_keywords_matched"
        case dailySchedule = "daily_schedule"
        case evolutionStats = "evolution_stats"
    }
}

// MARK: - 标签库（tags_500.json）

public struct TagCategory: Codable, Sendable, Equatable {
    public let categoryId: String
    public let nameZh: String
    public let nameEn: String
    public let count: Int
    public let tags: [String]

    enum CodingKeys: String, CodingKey {
        case categoryId = "category_id"
        case nameZh = "name_zh"
        case nameEn = "name_en"
        case count, tags
    }
}

public struct TagLibrary: Codable, Sendable, Equatable {
    public let version: String
    public let totalCount: Int
    public let categories: [TagCategory]

    enum CodingKeys: String, CodingKey {
        case version
        case totalCount = "total_count"
        case categories
    }

    /// 扁平化为 500 个标签字符串（供意图提取使用）。
    public var allTags: [String] { categories.flatMap(\.tags) }
}

// MARK: - 计划订单（PlanOrder）

public struct DepartureConfig: Codable, Sendable, Equatable {
    public var departureDate: Date
    public var originCity: String
    public var originLat: Double
    public var originLng: Double
    public var transportMode: TransportMode

    public init(departureDate: Date, originCity: String, originLat: Double, originLng: Double, transportMode: TransportMode) {
        self.departureDate = departureDate
        self.originCity = originCity
        self.originLat = originLat
        self.originLng = originLng
        self.transportMode = transportMode
    }
}

/// 用户标注/点评（严禁包含 user_id / nickname / device_id 等任何身份字段）。
public struct UserAnnotation: Codable, Sendable, Equatable {
    public var ratingStars: Int
    public var commentText: String
    public var annotatedAt: Date

    public init(ratingStars: Int, commentText: String, annotatedAt: Date) {
        self.ratingStars = ratingStars
        self.commentText = commentText
        self.annotatedAt = annotatedAt
    }
}

public struct PlanOrder: Codable, Sendable, Identifiable, Equatable {
    public let id: String
    public let routeId: String
    public let durationDays: Int
    public let routeType: RouteType
    public let isFeatured: Bool
    public let isUnlocked: Bool
    public let spots: [String]
    public let departureConfig: DepartureConfig
    public var orderStatus: OrderStatus
    public var userAnnotation: UserAnnotation?
    public var participants: [String]

    public init(
        id: String,
        routeId: String,
        durationDays: Int,
        routeType: RouteType,
        isFeatured: Bool,
        isUnlocked: Bool,
        spots: [String],
        departureConfig: DepartureConfig,
        orderStatus: OrderStatus = .planned,
        userAnnotation: UserAnnotation? = nil,
        participants: [String] = []
    ) {
        self.id = id
        self.routeId = routeId
        self.durationDays = durationDays
        self.routeType = routeType
        self.isFeatured = isFeatured
        self.isUnlocked = isUnlocked
        self.spots = spots
        self.departureConfig = departureConfig
        self.orderStatus = orderStatus
        self.userAnnotation = userAnnotation
        self.participants = participants
    }

    enum CodingKeys: String, CodingKey {
        case id = "order_id"
        case routeId = "route_id"
        case durationDays = "duration_days"
        case routeType = "route_type"
        case isFeatured = "is_featured"
        case isUnlocked = "is_unlocked"
        case spots
        case departureConfig = "departure_config"
        case orderStatus = "order_status"
        case userAnnotation = "user_annotation"
        case participants
    }
}
