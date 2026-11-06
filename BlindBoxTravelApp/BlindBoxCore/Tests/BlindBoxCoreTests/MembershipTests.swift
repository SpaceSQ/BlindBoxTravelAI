import XCTest
@testable import BlindBoxCore

final class MembershipTests: XCTestCase {
    func testFreeTierSlotLimit() {
        XCTAssertTrue(MembershipGatekeeper.canCreateOrder(tier: .free, activeOrderCount: 0))
        XCTAssertFalse(MembershipGatekeeper.canCreateOrder(tier: .free, activeOrderCount: 1))
        XCTAssertFalse(MembershipGatekeeper.canCreateOrder(tier: .free, activeOrderCount: 2))
    }

    func testProTierUnlimited() {
        XCTAssertTrue(MembershipGatekeeper.canCreateOrder(tier: .pro, activeOrderCount: 0))
        XCTAssertTrue(MembershipGatekeeper.canCreateOrder(tier: .pro, activeOrderCount: 5))
        XCTAssertTrue(MembershipGatekeeper.canCreateOrder(tier: .pro, activeOrderCount: 100))
    }

    func testBBXExportProOnly() {
        XCTAssertFalse(MembershipGatekeeper.canExportBBX(tier: .free))
        XCTAssertTrue(MembershipGatekeeper.canExportBBX(tier: .pro))
    }

    func testProductsPricing() {
        let monthly = MembershipGatekeeper.products.first { $0.period == .monthly }!
        let yearly = MembershipGatekeeper.products.first { $0.period == .yearly }!
        XCTAssertEqual(monthly.priceYuan, 28)
        XCTAssertEqual(yearly.priceYuan, 252)
        XCTAssertEqual(MembershipGatekeeper.products.count, 2)
    }
}
