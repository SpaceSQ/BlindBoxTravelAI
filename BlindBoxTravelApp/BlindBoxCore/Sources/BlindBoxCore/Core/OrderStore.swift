import Foundation
import Combine

/// 旅行计划订单仓库：创建、状态流转、删除与持久化。
///
/// 活跃订单 = 状态不为 `.deleted` 的订单；免费会员删除后 `activeOrders.count` 归零、恢复额度。
public final class PlanOrderStore: ObservableObject {
    @Published public private(set) var orders: [PlanOrder]

    public init(orders: [PlanOrder] = []) {
        self.orders = orders
    }

    /// 活跃订单（状态不为 deleted）。
    public var activeOrders: [PlanOrder] {
        orders.filter { $0.orderStatus != .deleted }
    }

    /// 依据会员等级判断是否还能新建计划行程单。
    public func canCreate(tier: MembershipTier) -> Bool {
        MembershipGatekeeper.canCreateOrder(tier: tier, activeOrderCount: activeOrders.count)
    }

    @discardableResult
    public func create(_ order: PlanOrder) -> PlanOrder {
        orders.append(order)
        return order
    }

    public func order(id: String) -> PlanOrder? {
        orders.first { $0.id == id }
    }

    @discardableResult
    public func setStatus(id: String, to status: OrderStatus) -> Bool {
        guard let i = orders.firstIndex(where: { $0.id == id }) else { return false }
        orders[i].orderStatus = status
        return true
    }

    @discardableResult
    public func markCompleted(id: String) -> Bool { setStatus(id: id, to: .completed) }

    @discardableResult
    public func markModified(id: String) -> Bool { setStatus(id: id, to: .modified) }

    @discardableResult
    public func markCancelled(id: String) -> Bool { setStatus(id: id, to: .cancelled) }

    /// 删除订单：标记 deleted，释放免费会员槽位。
    @discardableResult
    public func delete(id: String) -> Bool { setStatus(id: id, to: .deleted) }

    /// 为订单写入匿名标注/点评（严格不含任何身份字段）。
    @discardableResult
    public func annotate(id: String, ratingStars: Int, commentText: String, at date: Date = Date()) -> Bool {
        guard let i = orders.firstIndex(where: { $0.id == id }) else { return false }
        orders[i].userAnnotation = UserAnnotation(ratingStars: ratingStars, commentText: commentText, annotatedAt: date)
        return true
    }

    @discardableResult
    public func addParticipant(id: String, name: String) -> Bool {
        guard let i = orders.firstIndex(where: { $0.id == id }) else { return false }
        if !orders[i].participants.contains(name) {
            orders[i].participants.append(name)
        }
        return true
    }

    // MARK: - 持久化

    public func encoded() throws -> Data {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        return try encoder.encode(orders)
    }

    public func save(to url: URL) throws {
        try encoded().write(to: url, options: .atomic)
    }

    public static func load(from url: URL) throws -> PlanOrderStore {
        let data = try Data(contentsOf: url)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let orders = try decoder.decode([PlanOrder].self, from: data)
        return PlanOrderStore(orders: orders)
    }
}

/// 订单 ID 生成器。
public enum OrderID {
    public static func generate(now: Date = Date()) -> String {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "yyyyMMdd"
        let suffix = String(format: "%03d", Int.random(in: 0 ... 999))
        return "ORD_\(f.string(from: now))_\(suffix)"
    }
}
