import XCTest
@testable import BlindBoxCore

final class DialogueEngineTests: XCTestCase {
    let vocab = ["雪山", "滑雪", "重装徒步", "嗦粉", "辣", "治愈", "亲子", "情侣", "独自旅行", "赶海", "看海"]

    func testHanziCount() {
        XCTAssertEqual(IntentExtractor.hanziCount("看海"), 2)
        XCTAssertEqual(IntentExtractor.hanziCount("啊"), 1)
        XCTAssertEqual(IntentExtractor.hanziCount("Go!"), 0)
    }

    func testRejectUnderTwoHanzi() {
        var sm = DialogueEngine(vocab: vocab)
        let r = sm.process("啊")
        XCTAssertEqual(r.kind, .reject)
        XCTAssertEqual(sm.turnCount, 0)
    }

    func testCasualGenerateTurn1() {
        var sm = DialogueEngine(vocab: vocab)
        let r = sm.process("随便推荐一个")
        XCTAssertEqual(r.kind, .generate)
        XCTAssertEqual(r.turnCount, 1)
    }

    func testSpecificGenerateTurn1() {
        var sm = DialogueEngine(vocab: vocab)
        let r = sm.process("想看雪山，想滑雪，3天，500公里内")
        XCTAssertEqual(r.kind, .generate)
        XCTAssertEqual(r.turnCount, 1)
    }

    func testFollowUpThenForcedGenerateTurn4() {
        var sm = DialogueEngine(vocab: vocab)
        let inputs = ["想出去玩", "开心一点的", "风景好的", "就这些吧"]
        for (i, text) in inputs.enumerated() {
            let r = sm.process(text)
            if i < 3 {
                XCTAssertEqual(r.kind, .followUp, "turn \(i + 1)")
                XCTAssertFalse(r.quickOptions.isEmpty, "turn \(i + 1) 应提供快捷选项")
            } else {
                XCTAssertEqual(r.kind, .generate, "turn \(i + 1)")
                XCTAssertTrue(r.forced, "第 4 轮必须强制收敛")
                XCTAssertEqual(r.turnCount, 4)
            }
        }
    }

    func testExtractIntentSlots() {
        let it = IntentExtractor.extract("想和闺蜜去赶海看海，玩两天，1000公里内", vocab: vocab)
        XCTAssertTrue(it.matchedTags.contains("赶海"))
        XCTAssertTrue(it.matchedTags.contains("看海"))
        XCTAssertEqual(it.durationDays, 2)
        XCTAssertEqual(it.maxDistanceKm, 1000)
        XCTAssertEqual(it.companion, "闺蜜")
        XCTAssertGreaterThanOrEqual(IntentExtractor.specificity(it), 0.75)
    }

    func testSpecificityLowForVague() {
        let it = IntentExtractor.extract("想出去玩", vocab: vocab)
        XCTAssertTrue(it.matchedTags.isEmpty)
        XCTAssertLessThan(IntentExtractor.specificity(it), 0.75)
    }
}
