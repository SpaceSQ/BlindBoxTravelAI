import Foundation

// MARK: - 意图槽位

public struct Intent: Sendable, Equatable {
    public var matchedTags: [String]
    public var durationDays: Int?
    public var maxDistanceKm: Int?
    public var companion: String?
    public var casual: Bool

    public init(
        matchedTags: [String] = [],
        durationDays: Int? = nil,
        maxDistanceKm: Int? = nil,
        companion: String? = nil,
        casual: Bool = false
    ) {
        self.matchedTags = matchedTags
        self.durationDays = durationDays
        self.maxDistanceKm = maxDistanceKm
        self.companion = companion
        self.casual = casual
    }
}

public enum TurnKind: String, Sendable, Equatable {
    case reject
    case generate
    case followUp
}

public struct TurnResult: Sendable, Equatable {
    public let kind: TurnKind
    public let message: String
    public let quickOptions: [String]
    public let forced: Bool
    public let turnCount: Int
    public let intent: Intent
}

// MARK: - 意图提取器（M1 阶段用关键词/词汇库匹配替代本地大模型）

public enum IntentExtractor {
    public static let minHanzi = 2
    public static let specificityThreshold = 0.75

    static let casualTerms = [
        "随便", "随缘", "直接推荐", "直接给我", "直接来", "推荐一个",
        "看着来", "周末去玩", "随便去玩", "随便推荐", "都行", "都可以",
    ]
    static let companionTerms = [
        "亲子", "带娃", "情侣", "闺蜜", "兄弟", "姐妹", "独自", "一个人",
        "全家", "毕业旅行", "蜜月", "团建", "银发", "独行", "全家出游",
    ]
    static let chineseNumeral: [Character: Int] = [
        "一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "半": 1,
    ]

    public static func hanziCount(_ text: String) -> Int {
        BlindMasker.hanziCount(text)
    }

    public static func extract(_ text: String, vocab: [String]) -> Intent {
        var intent = Intent()

        for tag in vocab.sorted(by: { $0.count > $1.count }) where text.contains(tag) {
            intent.matchedTags.append(tag)
        }

        if casualTerms.contains(where: text.contains) {
            intent.casual = true
        }

        intent.durationDays = extractDuration(text)
        intent.maxDistanceKm = extractDistanceKm(text)
        intent.companion = companionTerms.first(where: text.contains)
        return intent
    }

    static func extractDuration(_ text: String) -> Int? {
        let pattern = #"(\d|[一二两三四五六七半])\s*[天日]"#
        guard let raw = firstGroup(pattern, in: text) else { return nil }
        if let d = Int(raw) {
            return min(7, max(1, d))
        }
        if let ch = raw.first, let d = chineseNumeral[ch] {
            return d
        }
        return nil
    }

    static func extractDistanceKm(_ text: String) -> Int? {
        let pattern = #"(\d+(?:\.\d+)?)\s*(?:公里|千米|km)"#
        guard let raw = firstGroup(pattern, in: text, options: [.caseInsensitive]),
              let d = Double(raw), d > 0 else { return nil }
        return Int(d)
    }

    static func firstGroup(_ pattern: String, in text: String, options: NSRegularExpression.Options = []) -> String? {
        guard let regex = try? NSRegularExpression(pattern: pattern, options: options) else { return nil }
        let ns = text as NSString
        let range = NSRange(location: 0, length: ns.length)
        guard let m = regex.firstMatch(in: text, options: [], range: range) else { return nil }
        guard m.numberOfRanges >= 2 else { return nil }
        let g = m.range(at: 1)
        guard g.location != NSNotFound else { return nil }
        return ns.substring(with: g)
    }

    /// 意图明确度（0.0 ~ 1.0）。
    public static func specificity(_ intent: Intent) -> Double {
        var s = 0.0
        let nTags = Set(intent.matchedTags).count
        if nTags >= 1 { s += 0.3 }
        if nTags >= 2 { s += 0.2 }
        if intent.durationDays != nil { s += 0.25 }
        if intent.maxDistanceKm != nil { s += 0.25 }
        if intent.companion != nil { s += 0.15 }
        return min(1.0, s)
    }

    static func merge(_ target: inout Intent, _ incoming: Intent) {
        target.casual = target.casual || incoming.casual
        for t in incoming.matchedTags where !target.matchedTags.contains(t) {
            target.matchedTags.append(t)
        }
        if target.durationDays == nil { target.durationDays = incoming.durationDays }
        if target.maxDistanceKm == nil { target.maxDistanceKm = incoming.maxDistanceKm }
        if target.companion == nil { target.companion = incoming.companion }
    }
}

// MARK: - 对话状态机（1~4 轮强制收敛）

public struct DialogueEngine: Sendable {
    public private(set) var turnCount: Int
    public private(set) var intent: Intent
    private let vocab: [String]

    public init(vocab: [String]) {
        self.vocab = vocab
        self.turnCount = 0
        self.intent = Intent()
    }

    public mutating func reset() {
        turnCount = 0
        intent = Intent()
    }

    /// 处理一轮用户输入。不足 2 个汉字返回 reject 且不计入有效轮次。
    public mutating func process(_ text: String) -> TurnResult {
        if IntentExtractor.hanziCount(text) < IntentExtractor.minHanzi {
            return TurnResult(
                kind: .reject,
                message: "再多说两个字，让我捕捉你的旅行灵感~",
                quickOptions: [], forced: false,
                turnCount: turnCount, intent: intent
            )
        }

        turnCount += 1
        IntentExtractor.merge(&intent, IntentExtractor.extract(text, vocab: vocab))

        // 第 1 轮：宽松信号或足够明确 → 直接出盒
        if turnCount == 1 && (intent.casual || IntentExtractor.specificity(intent) >= IntentExtractor.specificityThreshold) {
            return TurnResult(
                kind: .generate,
                message: "捕捉到你的旅行灵感了，这就为你拆出 3 份盲盒行程~",
                quickOptions: [], forced: false,
                turnCount: turnCount, intent: intent
            )
        }

        // 硬性红线：第 4 轮强制收敛
        if turnCount >= 4 {
            return TurnResult(
                kind: .generate,
                message: "好的，就按现在这份心情，为你揭晓 3 份盲盒行程~",
                quickOptions: [], forced: true,
                turnCount: turnCount, intent: intent
            )
        }

        return TurnResult(
            kind: .followUp,
            message: nextQuestion(),
            quickOptions: nextOptions(), forced: false,
            turnCount: turnCount, intent: intent
        )
    }

    private func nextQuestion() -> String {
        if intent.durationDays == nil {
            return "这趟盲盒想拆几天呀？（1~7 天都可以哦）"
        }
        if intent.maxDistanceKm == nil {
            return "想走多远去拆这份惊喜呢？"
        }
        return "这次和谁一起出发呀？"
    }

    private func nextOptions() -> [String] {
        if intent.durationDays == nil {
            return ["1天", "2天", "3天", "4天及以上"]
        }
        if intent.maxDistanceKm == nil {
            return ["500km内", "1000km内", "3000km内", "多远都行"]
        }
        return ["独自", "情侣", "闺蜜", "亲子"]
    }
}
