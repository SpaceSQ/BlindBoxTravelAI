import XCTest
@testable import BlindBoxCore

final class BlindMaskerTests: XCTestCase {
    let seedCases: [(String, String)] = [
        ("甘孜稻城亚丁风景区", "**稻**丁***"),
        ("柳州螺蛳粉小镇", "*州**粉**"),
        ("泉州蟳埔村", "泉***村"),
        ("乌兰察布火山地质公园", "**察**山****"),
        ("长沙橘子洲头", "*沙**洲*"),
    ]

    func testSeedBlindNamesValid() {
        for (full, blind) in seedCases {
            let (ok, errs) = BlindMasker.validateBlindName(full, blind)
            XCTAssertTrue(ok, "\(full) -> \(blind): \(errs)")
        }
    }

    func testMaskPreservesLengthAndTwoHanzi() {
        for full in ["甘孜稻城亚丁风景区", "泉州蟳埔村", "乌兰察布火山地质公园"] {
            let blind = BlindMasker.maskFullName(full)
            let (ok, errs) = BlindMasker.validateBlindName(full, blind)
            XCTAssertTrue(ok, errs.joined(separator: "; "))
            XCTAssertEqual(blind.count, full.count)
        }
    }

    func testMaskWithExplicitIndices() {
        XCTAssertEqual(BlindMasker.maskFullName("甘孜稻城亚丁风景区", keepIndices: [2, 5]), "**稻**丁***")
        XCTAssertEqual(BlindMasker.maskFullName("泉州蟳埔村", keepIndices: [0, 4]), "泉***村")
    }

    func testValidateRejectsBad() {
        XCTAssertFalse(BlindMasker.validateBlindName("长沙橘子洲头", "长沙橘子洲头").ok)
        XCTAssertFalse(BlindMasker.validateBlindName("长沙橘子洲头", "*沙*").ok)
        XCTAssertFalse(BlindMasker.validateBlindName("长沙橘子洲头", "泉***村").ok)
    }

    func testContainsFullName() {
        XCTAssertTrue(BlindMasker.containsFullName("去甘孜稻城亚丁风景区玩", "甘孜稻城亚丁风景区"))
        XCTAssertFalse(BlindMasker.containsFullName("去这座秘境玩", "甘孜稻城亚丁风景区"))
    }

    func testSanitizeReplacesFullName() {
        let cleaned = BlindMasker.sanitize("这里是甘孜稻城亚丁风景区，欢迎你来。", forbidden: ["甘孜稻城亚丁风景区"])
        XCTAssertFalse(cleaned.contains("甘孜稻城亚丁风景区"))
        XCTAssertTrue(cleaned.contains("这座秘境"))
    }
}
