import Foundation

/// 轻量本地化辅助：以简体中文为 key（缺失时回退为简体原文）。
enum L10n {
    static func tr(_ key: String) -> String {
        NSLocalizedString(key, comment: "")
    }

    // 常用文案
    static let appName = tr("盲盒旅行AI")
    static let start = tr("开始盲盒旅行")
    static let needMoreHanzi = tr("再多说两个字，让我捕捉你的旅行灵感~")
    static let send = tr("发送")
    static let distanceRange = tr("距离范围")
    static let originCity = tr("出发地（默认当前城市）")
    static let recommendedRoutes = tr("推荐路线")
    static let featured = tr("重点推荐")
    static let priceHidden = tr("选定行程后揭晓")
    static let generateOrder = tr("生成计划行程单")
    static let departureDate = tr("出发日期")
    static let transportMode = tr("出发交通方式")
    static let unlock = tr("开盲盒")
    static let unlocked = tr("盲盒已开启，为你揭晓完整行程")
    static let ticket = tr("门票")
    static let restart = tr("重新开始")
    static let back = tr("返回")
    static let chatTab = tr("盲盒对话")
    static let inspiration = tr("旅行灵感")
}
