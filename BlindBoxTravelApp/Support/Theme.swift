import SwiftUI

/// 跨平台（iOS / iPadOS / macOS）语义色。
extension Color {
    /// 次级背景色：卡片、气泡等。
    static var secondaryBackground: Color {
        #if os(macOS)
        Color(nsColor: .controlBackgroundColor)
        #else
        Color(uiColor: .secondarySystemBackground)
        #endif
    }
}
