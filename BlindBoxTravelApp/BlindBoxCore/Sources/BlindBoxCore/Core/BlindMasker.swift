import Foundation

/// 盲盒名称自动脱敏器与明文还原校验器（交底书 §3.3 / Grok 交底书 §2.2、§2.3）。
///
/// 规则：
/// - 仅保留 2 个“非直白暴露全称”的汉字，其余汉字用 '*' 一对一**等长**替换；
/// - blind_name 长度严格等于 full_name 长度，且保留的明文汉字数严格为 2；
/// - description / summary_100w 不得出现 full_name（允许保留省市区位）。
public enum BlindMasker {
    /// 正文泄露全称时的脱敏代称。
    public static let defaultPlaceholder = "这座秘境"

    static func isHanzi(_ scalar: Unicode.Scalar) -> Bool {
        (0x4E00 ... 0x9FFF).contains(scalar.value)
    }

    public static func isHanzi(_ ch: Character) -> Bool {
        let scalars = ch.unicodeScalars
        return !scalars.isEmpty && scalars.allSatisfy(isHanzi)
    }

    /// 返回所有汉字的字符下标（0 基，按 Character 计数）。
    public static func hanziIndices(_ text: String) -> [Int] {
        Array(text).indices.filter { isHanzi(Array(text)[$0]) }
    }

    public static func hanziCount(_ text: String) -> Int {
        hanziIndices(text).count
    }

    /// 默认保留 2 个汉字：取约 1/3 与 2/3 位置，制造悬念提示且不直白暴露全称。
    static func defaultKeepIndices(_ indices: [Int]) -> [Int] {
        let n = indices.count
        if n == 0 { return [] }
        if n <= 2 { return indices }
        let first = indices[n / 3]
        var second = indices[2 * n / 3]
        if first == second { second = indices[(2 * n / 3 + 1) % n] }
        return [first, second]
    }

    /// 将 full_name 脱敏为 blind_name（仅保留 2 个汉字，其余汉字替换为 '*'）。
    public static func maskFullName(_ fullName: String, keepIndices: [Int]? = nil) -> String {
        let chars = Array(fullName)
        let hanzi = chars.indices.filter { isHanzi(chars[$0]) }
        guard !hanzi.isEmpty else { return fullName }
        let keep = keepIndices.map(Set.init) ?? Set(defaultKeepIndices(hanzi))
        var out: [Character] = []
        for (i, ch) in chars.enumerated() {
            if isHanzi(ch) && !keep.contains(i) {
                out.append("*")
            } else {
                out.append(ch)
            }
        }
        return String(out)
    }

    /// 校验 blind_name 是否符合脱敏规范，返回 (是否合规, 错误原因列表)。
    public static func validateBlindName(_ fullName: String, _ blindName: String) -> (ok: Bool, errors: [String]) {
        var errors: [String] = []
        let fc = Array(fullName)
        let bc = Array(blindName)
        if fc.count != bc.count {
            errors.append("长度不匹配：full=\(fc.count)，blind=\(bc.count)")
        }
        let kept = bc.indices.filter { isHanzi(bc[$0]) }
        if kept.count != 2 {
            errors.append("保留汉字数应为 2，实际为 \(kept.count)")
        }
        for i in kept {
            if i >= fc.count {
                errors.append("位置 \(i) 越界")
            } else if bc[i] != fc[i] {
                errors.append("位置 \(i) 保留字 '\(bc[i])' 与原文 '\(fc[i])' 不符")
            }
        }
        return (errors.isEmpty, errors)
    }

    public static func containsFullName(_ text: String, _ fullName: String) -> Bool {
        !fullName.isEmpty && text.contains(fullName)
    }

    /// 将正文中出现的禁用词（景点全称等）替换为代称。
    public static func sanitize(_ text: String, forbidden: [String], placeholder: String = defaultPlaceholder) -> String {
        var out = text
        for word in forbidden where !word.isEmpty {
            out = out.replacingOccurrences(of: word, with: placeholder)
        }
        return out
    }
}
