import XCTest
@testable import BlindBoxCore

final class OrderStoreTests: XCTestCase {
    func makeOrder(id: String) -> PlanOrder {
        PlanOrder(
            id: id,
            routeId: "RT001",
            durationDays: 2,
            routeType: .singleSpot,
            isFeatured: false,
            isUnlocked: true,
            spots: ["SP001"],
            departureConfig: DepartureConfig(
                departureDate: Date(timeIntervalSince1970: 1_700_000_000),
                originCity: "深圳市", originLat: 22.5431, originLng: 114.0579,
                transportMode: .highSpeedRail
            )
        )
    }

    func testActiveOrdersExcludesDeleted() {
        let store = PlanOrderStore()
        store.create(makeOrder(id: "A"))
        store.create(makeOrder(id: "B"))
        store.delete(id: "A")
        XCTAssertEqual(store.activeOrders.count, 1)
        XCTAssertEqual(store.activeOrders.first?.id, "B")
        XCTAssertEqual(store.orders.count, 2) // 删除 = 标记，不物理移除
    }

    func testFreeTierBlockedAfterFirstActive() {
        let store = PlanOrderStore()
        XCTAssertTrue(store.canCreate(tier: .free))
        store.create(makeOrder(id: "A"))
        XCTAssertFalse(store.canCreate(tier: .free))
        // 取消（cancelled）仍为活跃订单，不释放槽位
        store.markCancelled(id: "A")
        XCTAssertFalse(store.canCreate(tier: .free))
        // 删除后释放
        store.delete(id: "A")
        XCTAssertTrue(store.canCreate(tier: .free))
    }

    func testProTierAlwaysCanCreate() {
        let store = PlanOrderStore()
        store.create(makeOrder(id: "A"))
        XCTAssertTrue(store.canCreate(tier: .pro))
    }

    func testStatusTransitions() {
        let store = PlanOrderStore()
        store.create(makeOrder(id: "A"))
        XCTAssertTrue(store.markCompleted(id: "A"))
        XCTAssertEqual(store.order(id: "A")?.orderStatus, .completed)
        XCTAssertTrue(store.markModified(id: "A"))
        XCTAssertEqual(store.order(id: "A")?.orderStatus, .modified)
        XCTAssertFalse(store.markCompleted(id: "NONEXISTENT"))
    }

    func testAnnotateAndParticipants() {
        let store = PlanOrderStore()
        store.create(makeOrder(id: "A"))
        XCTAssertTrue(store.annotate(id: "A", ratingStars: 5, commentText: "氧气瓶提前买好"))
        XCTAssertEqual(store.order(id: "A")?.userAnnotation?.ratingStars, 5)
        XCTAssertEqual(store.order(id: "A")?.userAnnotation?.commentText, "氧气瓶提前买好")
        XCTAssertTrue(store.addParticipant(id: "A", name: "好友A"))
        XCTAssertEqual(store.order(id: "A")?.participants, ["好友A"])
    }

    func testSaveLoadRoundTrip() throws {
        let store = PlanOrderStore()
        store.create(makeOrder(id: "A"))
        store.annotate(id: "A", ratingStars: 4, commentText: "很震撼")

        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("orderstore_test_\(UUID().uuidString).json")
        defer { try? FileManager.default.removeItem(at: url) }

        try store.save(to: url)
        let loaded = try PlanOrderStore.load(from: url)
        XCTAssertEqual(loaded.orders.count, 1)
        XCTAssertEqual(loaded.order(id: "A")?.userAnnotation?.ratingStars, 4)
        XCTAssertEqual(loaded.order(id: "A")?.userAnnotation?.commentText, "很震撼")
        XCTAssertEqual(loaded.order(id: "A")?.departureConfig.originCity, "深圳市")
    }

    func testOrderIDFormat() {
        let id = OrderID.generate(now: Date(timeIntervalSince1970: 1_700_000_000))
        XCTAssertTrue(id.hasPrefix("ORD_"))
    }
}
