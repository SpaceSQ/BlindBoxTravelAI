import XCTest
@testable import BlindBoxCore

final class HaversineTests: XCTestCase {
    func testSamePointIsZero() {
        XCTAssertEqual(Haversine.distanceKm(lat1: 39.9042, lng1: 116.4074, lat2: 39.9042, lng2: 116.4074), 0.0, accuracy: 1e-6)
    }

    func testBeijingShanghaiDistance() {
        let d = Haversine.distanceKm(lat1: 39.9042, lng1: 116.4074, lat2: 31.2304, lng2: 121.4737)
        XCTAssertGreaterThan(d, 1000)
        XCTAssertLessThan(d, 1200)
        XCTAssertEqual(d, 1067, accuracy: 40)
    }

    func testSymmetry() {
        let a = (28.4124, 100.2078)
        let b = (41.523, 113.1118)
        XCTAssertEqual(
            Haversine.distanceKm(lat1: a.0, lng1: a.1, lat2: b.0, lng2: b.1),
            Haversine.distanceKm(lat1: b.0, lng1: b.1, lat2: a.0, lng2: a.1),
            accuracy: 1e-9
        )
    }

    func testShortDistanceOrder() {
        let sz = (22.5431, 114.0579)
        let gz = (23.1291, 113.2644)
        let bj = (39.9042, 116.4074)
        let dSZ2GZ = Haversine.distanceKm(lat1: sz.0, lng1: sz.1, lat2: gz.0, lng2: gz.1)
        let dSZ2BJ = Haversine.distanceKm(lat1: sz.0, lng1: sz.1, lat2: bj.0, lng2: bj.1)
        XCTAssertLessThan(dSZ2GZ, dSZ2BJ)
    }
}
