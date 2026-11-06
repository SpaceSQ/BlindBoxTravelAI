import Foundation

/// GitHub 进化变量同步器（交底书 §3.6 / PRD §2.5）。
///
/// 职责：
/// 1. 将匿名增量（plan_mark / review）写入本地待同步队列 `pending_evolution_deltas.json`，
///    并立即应用到本地 metrics（供推荐排序即时反映热度）；
/// 2. 在线时原子化完成：GET 读取远端 sha 与内容 → 将待同步增量合并进远端 → PUT 提交；
/// 3. 离线或未配置 Token 时仅入队，联网后批量合并推送。
///
/// 严格零溯源：本模块不收集、不上传任何 UserID / 设备 UUID / IP / 昵称。

/// 传输层协议（可注入 mock 以便无网络测试）。
public protocol EvolutionSyncTransport: Sendable {
    /// 读取远端当前状态（文件 sha + 解析后的 metrics）。
    func fetchCurrentState() async throws -> (sha: String, metrics: EvolutionMetrics)
    /// 以 `sha` 为乐观锁提交合并后的 metrics，返回提交后新的 sha。
    func push(metrics: EvolutionMetrics, sha: String) async throws -> String
}

public enum EvolutionSyncError: Error, Equatable {
    case noToken
    case offline
    case requestFailed(status: Int)
    case conflict
    case invalidResponse
}

/// 基于 GitHub Contents API 的传输层实现。
///
/// 原子流程：GET 文件取 `sha` + 内容 → 本地合并 → PUT 覆盖（带 `sha` 与 commit message）。
public struct GitHubRESTTransport: EvolutionSyncTransport {
    public let repository: String   // "SpaceSQ/BlindBoxTravelAI"
    public let filePath: String     // "data/evolution_metrics.json"
    public let token: String
    public let branch: String

    public init(repository: String, filePath: String, token: String, branch: String = "main") {
        self.repository = repository
        self.filePath = filePath
        self.token = token
        self.branch = branch
    }

    private var apiBase: URL {
        URL(string: "https://api.github.com/repos/\(repository)/contents/\(filePath)?ref=\(branch)")!
    }

    private func authorizedRequest(_ method: String) -> URLRequest {
        var request = URLRequest(url: apiBase)
        request.httpMethod = method
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/vnd.github+json", forHTTPHeaderField: "Accept")
        request.setValue("2022-11-28", forHTTPHeaderField: "X-GitHub-Api-Version")
        return request
    }

    public func fetchCurrentState() async throws -> (sha: String, metrics: EvolutionMetrics) {
        let (data, response) = try await URLSession.shared.data(for: authorizedRequest("GET"))
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200 ... 299).contains(status) else {
            throw EvolutionSyncError.requestFailed(status: status)
        }
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let sha = json["sha"] as? String,
              let contentB64 = json["content"] as? String,
              let contentData = Data(base64Encoded: contentB64.replacingOccurrences(of: "\n", with: "")) else {
            throw EvolutionSyncError.invalidResponse
        }
        let metrics = try EvolutionMetrics.decode(contentData)
        return (sha, metrics)
    }

    public func push(metrics: EvolutionMetrics, sha: String) async throws -> String {
        var request = authorizedRequest("PUT")
        let body: [String: Any] = [
            "message": "chore(evolution): anonymous metric increment",
            "content": try metrics.encoded().base64EncodedString(),
            "sha": sha,
            "branch": branch,
        ]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200 ... 299).contains(status) else {
            throw EvolutionSyncError.requestFailed(status: status)
        }
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let content = json["content"] as? [String: Any],
              let newSHA = content["sha"] as? String else {
            throw EvolutionSyncError.invalidResponse
        }
        return newSHA
    }
}

/// 同步引擎：维护本地 metrics + 待同步队列，负责离线入队与在线原子推送。
@MainActor
public final class EvolutionSyncEngine: ObservableObject {
    @Published public private(set) var metrics: EvolutionMetrics
    @Published public private(set) var pendingDeltas: [EvolutionDelta] = []

    public let transport: EvolutionSyncTransport?
    private let queueURL: URL?

    public init(metrics: EvolutionMetrics, transport: EvolutionSyncTransport? = nil, queueURL: URL? = nil) {
        self.metrics = metrics
        self.transport = transport
        self.queueURL = queueURL
        if let queueURL { pendingDeltas = (try? Self.loadQueue(from: queueURL)) ?? [] }
    }

    /// 记录增量：本地立即生效（供推荐排序），并入队待同步。
    public func record(_ deltas: [EvolutionDelta], now: Date = Date()) {
        metrics = metrics.applying(deltas, now: now)
        pendingDeltas.append(contentsOf: deltas)
        persistQueueIfNeeded()
    }

    /// 尝试原子推送：GET 远端 → 合并待同步增量 → PUT。返回是否成功。
    public func flush() async -> Bool {
        guard !pendingDeltas.isEmpty else { return true }
        guard let transport else { return false }  // 未配置 Token，保持离线入队
        do {
            let (sha, remoteMetrics) = try await transport.fetchCurrentState()
            let merged = remoteMetrics.applying(pendingDeltas)
            _ = try await transport.push(metrics: merged, sha: sha)
            metrics = merged
            pendingDeltas.removeAll()
            persistQueueIfNeeded()
            return true
        } catch {
            return false
        }
    }

    public var pendingCount: Int { pendingDeltas.count }

    // MARK: - 队列持久化

    public func persistQueueIfNeeded() {
        guard let queueURL else { return }
        try? Self.saveQueue(pendingDeltas, to: queueURL)
    }

    public static func saveQueue(_ deltas: [EvolutionDelta], to url: URL) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        try encoder.encode(deltas).write(to: url, options: .atomic)
    }

    public static func loadQueue(from url: URL) throws -> [EvolutionDelta] {
        let data = try Data(contentsOf: url)
        return try JSONDecoder().decode([EvolutionDelta].self, from: data)
    }
}
