import XCTest
@testable import BlindBoxCore

final class DataStoreTests: XCTestCase {
    func dataDirectory() -> URL {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0 ..< 5 { url.deleteLastPathComponent() }
        return url.appendingPathComponent("data")
    }

    func testLoadsRealSeedDataAndDecodes() {
        let store = DataStore.load(directory: dataDirectory())

        // 500 标签去重
        XCTAssertEqual(store.tags.count, 500)
        XCTAssertEqual(Set(store.tags).count, 500)

        // 景点盲盒脱敏合规且无全称泄露
        for s in store.spots {
            let (ok, errs) = BlindMasker.validateBlindName(s.fullName, s.blindName)
            XCTAssertTrue(ok, "\(s.id): \(errs)")
            XCTAssertFalse(BlindMasker.containsFullName(s.description, s.fullName))
            XCTAssertFalse(BlindMasker.containsFullName(s.summary100w, s.fullName))
            for t in s.tags {
                XCTAssertTrue(store.tags.contains(t.name), "\(s.id):\(t.name)")
            }
        }

        // 路线引用有效、天数 1~7、日程条数一致
        let spotIds = Set(store.spots.map(\.id))
        for r in store.routes {
            XCTAssertTrue(spotIds.isSuperset(of: r.spotIds), r.id)
            XCTAssertTrue((1 ... 7).contains(r.durationDays), r.id)
            XCTAssertEqual(r.dailySchedule.count, r.durationDays, r.id)
        }
    }

    func testTagMatcherAgainstRealData() {
        let store = DataStore.load(directory: dataDirectory())
        let route = store.routes.first { $0.spotIds.contains("SP001") }!
        let match = TagMatcher.tagMatch(route, spotsById: store.spotsById, matchedTags: ["雪山", "重装徒步"])
        XCTAssertEqual(match, 6.0) // 两个 strong 标签
    }
}
