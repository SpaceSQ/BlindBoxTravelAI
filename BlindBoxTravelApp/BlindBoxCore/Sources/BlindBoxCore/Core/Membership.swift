import Foundation

/// 会员等级：免费 / Pro。
public enum MembershipTier: String, Codable, Sendable, Equatable, CaseIterable {
    case free
    case pro
}

/// 订阅商品（StoreKit 产品描述）。
public struct SubscriptionProduct: Identifiable, Sendable, Equatable {
    public enum Period: String, Sendable, Equatable {
        case monthly
        case yearly
    }

    public let id: String
    public let tier: MembershipTier
    public let name: String
    public let priceYuan: Double
    public let period: Period

    public init(id: String, tier: MembershipTier, name: String, priceYuan: Double, period: Period) {
        self.id = id
        self.tier = tier
        self.name = name
        self.priceYuan = priceYuan
        self.period = period
    }
}

/// 会员权限门禁（交底书 §3.4 / PRD §2.3）。
public enum MembershipGatekeeper {
    /// 免费会员同时可持有的有效计划行程数上限。
    public static let maxFreeActiveOrders = 1
    public static let monthlyPriceYuan = 28.0
    public static let yearlyPriceYuan = 252.0

    /// 订阅商品列表（Pro 会员）。
    public static let products: [SubscriptionProduct] = [
        SubscriptionProduct(
            id: "com.spacesq.blindboxtravel.pro.monthly",
            tier: .pro, name: "Pro 月卡", priceYuan: monthlyPriceYuan, period: .monthly
        ),
        SubscriptionProduct(
            id: "com.spacesq.blindboxtravel.pro.yearly",
            tier: .pro, name: "Pro 年卡", priceYuan: yearlyPriceYuan, period: .yearly
        ),
    ]

    /// 是否可生成新的计划行程单（免费会员受 1 槽位限制）。
    public static func canCreateOrder(tier: MembershipTier, activeOrderCount: Int) -> Bool {
        tier == .pro || activeOrderCount < maxFreeActiveOrders
    }

    /// 是否可导出自有专有格式 `.bbx`（Pro 专属）。
    public static func canExportBBX(tier: MembershipTier) -> Bool {
        tier == .pro
    }
}
