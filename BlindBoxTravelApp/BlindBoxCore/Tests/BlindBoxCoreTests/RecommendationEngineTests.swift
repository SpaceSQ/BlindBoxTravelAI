import XCTest
@testable import BlindBoxCore

final class RecommendationEngineTests: XCTestCase {
    let origin = (lat: 22.5431, lng: 114.0579) // 深圳

    var store: DataStore!
    var spotsById: [String: Spot] { store.spotsById }
    var routes: [Route] { store.routes }

    override func setUpWithError() throws {
        store = try Self.makeStore()
    }

    static func makeStore() throws -> DataStore {
        let dir = try Self.dataDirectory()
        return DataStore.load(directory: dir)
    }

    static func dataDirectory() throws -> URL {
        // 测试文件路径：.../BlindBoxTravelApp/BlindBoxCore/Tests/BlindBoxCoreTests/RecommendationEngineTests.swift
        // 向上 4 级到仓库根，再进 data/
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0 ..< 5 { url.deleteLastPathComponent() }
        return url.appendingPathComponent("data")
    }

    func testDataLoaded() {
        XCTAssertGreaterThanOrEqual(routes.count, 3)
        XCTAssertGreaterThanOrEqual(spotsById.count, 5)
    }

    func testFirstStopDistanceReasonable() {
        let dDC = Haversine.distanceKm(lat1: origin.lat, lng1: origin.lng, lat2: 28.4124, lng2: 100.2078)
        XCTAssertGreaterThan(dDC, 1000)
        let dLZ = Haversine.distanceKm(lat1: origin.lat, lng1: origin.lng, lat2: 24.2386, lng2: 109.2847)
        XCTAssertLessThan(dLZ, 1000)
    }

    func testFilterByDistance() {
        let within = RecommendationEngine.filterByDistance(routes, spotsById: spotsById, originLat: origin.lat, originLng: origin.lng, maxKm: 1000)
        XCTAssertFalse(within.isEmpty)
        for r in within {
            XCTAssertLessThanOrEqual(
                RecommendationEngine.firstStopDistanceKm(r, spotsById: spotsById, originLat: origin.lat, originLng: origin.lng), 1000
            )
        }
    }

    func testRecommendReturnsThreeWithFirstFeatured() {
        let recs = RecommendationEngine.recommend(
            routes: routes, spotsById: spotsById,
            originLat: origin.lat, originLng: origin.lng,
            matchedTags: ["嗦粉"], applyRandom: false
        )
        XCTAssertEqual(recs.count, 3)
        XCTAssertTrue(recs[0].isFeatured)
        XCTAssertFalse(recs[1].isFeatured)
        XCTAssertFalse(recs[2].isFeatured)
    }

    func testRecommendTagMatchRankedTop() {
        let recs = RecommendationEngine.recommend(
            routes: routes, spotsById: spotsById,
            originLat: origin.lat, originLng: origin.lng,
            matchedTags: ["嗦粉"], applyRandom: false
        )
        XCTAssertTrue(recs[0].spotIds.contains("SP002"))
    }

    func testRecommendRandomModeStillThree() {
        let recs = RecommendationEngine.recommend(
            routes: routes, spotsById: spotsById,
            originLat: origin.lat, originLng: origin.lng,
            matchedTags: [], specificity: 0.0, seed: 7
        )
        XCTAssertEqual(recs.count, 3)
    }

    func testRecommendRespectsDurationPreference() {
        let recs = RecommendationEngine.recommend(
            routes: routes, spotsById: spotsById,
            originLat: origin.lat, originLng: origin.lng,
            matchedTags: [], durationDays: 1, applyRandom: false
        )
        XCTAssertEqual(recs[0].durationDays, 1)
    }
}
