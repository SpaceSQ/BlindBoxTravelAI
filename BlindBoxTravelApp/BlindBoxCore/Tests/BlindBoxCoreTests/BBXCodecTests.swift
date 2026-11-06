import XCTest
@testable import BlindBoxCore

final class BBXCodecTests: XCTestCase {
    var store: DataStore!

    override func setUpWithError() throws {
        store = DataStore.load(directory: Self.dataDirectory())
    }

    static func dataDirectory() -> URL {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0 ..< 5 { url.deleteLastPathComponent() }
        return url.appendingPathComponent("data")
    }

    func makeOrder(route: Route) -> PlanOrder {
        PlanOrder(
            id: "ORD_TEST_001",
            routeId: route.id,
            durationDays: route.durationDays,
            routeType: route.routeType,
            isFeatured: false,
            isUnlocked: true,
            spots: route.spotIds,
            departureConfig: DepartureConfig(
                departureDate: Date(timeIntervalSince1970: 1_700_000_000),
                originCity: "深圳市", originLat: 22.5431, originLng: 114.0579,
                transportMode: .flight
            )
        )
    }

    func testEncodeDecodeRoundTrip() throws {
        let route = store.routes.first { $0.spotIds.contains("SP001") }!
        let spots = route.spotIds.compactMap { store.spotsById[$0] }
        var order = makeOrder(route: route)
        order.userAnnotation = UserAnnotation(ratingStars: 5, commentText: "牛奶海太震撼了", annotatedAt: Date(timeIntervalSince1970: 1_700_100_000))

        let package = BBXCodec.makePackage(order: order, spots: spots)
        XCTAssertTrue(BBXCodec.verify(package))

        let data = try BBXCodec.encode(package)
        let decoded = try BBXCodec.decode(data)

        XCTAssertEqual(decoded.order.id, order.id)
        XCTAssertEqual(decoded.order.spots, route.spotIds)
        XCTAssertEqual(decoded.order.userAnnotation?.commentText, "牛奶海太震撼了")
        XCTAssertEqual(decoded.spots.map(\.fullName), spots.map(\.fullName))
        // 编解码经 millisecondsSince1970 往返，仅保留毫秒精度
        XCTAssertEqual(decoded.createdAt.timeIntervalSince1970, package.createdAt.timeIntervalSince1970, accuracy: 0.001)
        XCTAssertTrue(BBXCodec.verify(decoded))
    }

    func testVerifyDetectsTampering() {
        let route = store.routes[0]
        let spots = route.spotIds.compactMap { store.spotsById[$0] }
        let order = makeOrder(route: route)
        let good = BBXCodec.makePackage(order: order, spots: spots)

        // 用不同 order 却复用旧 hash → 校验失败
        let bad = BBXPackage(
            format: good.format, version: good.version,
            order: PlanOrder(
                id: "ORD_HACKED", routeId: route.id, durationDays: route.durationDays,
                routeType: route.routeType, isFeatured: false, isUnlocked: true, spots: route.spotIds,
                departureConfig: order.departureConfig
            ),
            spots: spots, createdAt: good.createdAt, integrityHash: good.integrityHash
        )
        XCTAssertFalse(BBXCodec.verify(bad))
    }

    func testDecodeRejectsCorruptedData() {
        let route = store.routes[0]
        let spots = route.spotIds.compactMap { store.spotsById[$0] }
        let data = try! BBXCodec.encode(BBXCodec.makePackage(order: makeOrder(route: route), spots: spots))
        // 破坏字节
        var corrupted = [UInt8](data)
        corrupted[corrupted.count / 2] ^= 0xFF
        XCTAssertThrowsError(try BBXCodec.decode(Data(corrupted)))
    }

    func testDeepLinkRoundTrip() throws {
        let route = store.routes[0]
        let spots = route.spotIds.compactMap { store.spotsById[$0] }
        let package = BBXCodec.makePackage(order: makeOrder(route: route), spots: spots)

        let url = try BBXCodec.deepLink(package: package)
        XCTAssertEqual(url.scheme, "blindboxtravel")
        XCTAssertEqual(url.host, "import")

        let parsed = try BBXCodec.parseDeepLink(url)
        XCTAssertEqual(parsed.order.id, package.order.id)
        XCTAssertEqual(parsed.spots.map(\.fullName), spots.map(\.fullName))
    }

    func testParseDeepLinkRejectsForeignURL() {
        let url = URL(string: "https://example.com/import?payload=abc")!
        XCTAssertThrowsError(try BBXCodec.parseDeepLink(url))
    }
}
