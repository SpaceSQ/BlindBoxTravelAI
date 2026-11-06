import Foundation

/// 数据加载器：从 Bundle 或目录读取 data/ 种子数据并构建内存索引。
public struct DataStore: Sendable {
    public let spots: [Spot]
    public let routes: [Route]
    public let tags: [String]
    public let spotsById: [String: Spot]
    public let routesById: [String: Route]

    public init(spots: [Spot], routes: [Route], tags: [String]) {
        self.spots = spots
        self.routes = routes
        self.tags = tags
        self.spotsById = Dictionary(uniqueKeysWithValues: spots.map { ($0.id, $0) })
        self.routesById = Dictionary(uniqueKeysWithValues: routes.map { ($0.id, $0) })
    }

    /// 从 App Bundle 加载（数据文件以资源形式打包在 Bundle 根目录）。
    public static func load(bundle: Bundle = .main) -> DataStore {
        let decoder = JSONDecoder()

        let spots: [Spot] = decodeFile("spots_seed", in: bundle, decoder: decoder) ?? []
        let routes: [Route] = decodeFile("routes_seed", in: bundle, decoder: decoder) ?? []
        let tagLibrary: TagLibrary? = decodeFile("tags_500", in: bundle, decoder: decoder)
        let tags = tagLibrary?.allTags ?? []

        return DataStore(spots: spots, routes: routes, tags: tags)
    }

    /// 从目录加载（测试 / 开发用）。目录内应含 spots_seed.json、routes_seed.json、tags_500.json。
    public static func load(directory: URL) -> DataStore {
        let decoder = JSONDecoder()

        func read<T: Decodable>(_ name: String) -> T? {
            let url = directory.appendingPathComponent("\(name).json")
            guard let data = try? Data(contentsOf: url) else { return nil }
            return try? decoder.decode(T.self, from: data)
        }

        let spots: [Spot] = read("spots_seed") ?? []
        let routes: [Route] = read("routes_seed") ?? []
        let tags: [String] = (read("tags_500") as TagLibrary?)?.allTags ?? []

        return DataStore(spots: spots, routes: routes, tags: tags)
    }

    /// 从目录加载进化变量库（evolution_metrics.json）。
    public static func loadEvolutionMetrics(directory: URL) -> EvolutionMetrics? {
        let url = directory.appendingPathComponent("evolution_metrics.json")
        guard let data = try? Data(contentsOf: url) else { return nil }
        return try? EvolutionMetrics.decode(data)
    }

    /// 从 App Bundle 加载进化变量库。
    public static func loadEvolutionMetrics(bundle: Bundle = .main) -> EvolutionMetrics? {
        guard let url = bundle.url(forResource: "evolution_metrics", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? EvolutionMetrics.decode(data)
    }

    private static func decodeFile<T: Decodable>(_ name: String, in bundle: Bundle, decoder: JSONDecoder) -> T? {
        guard let url = bundle.url(forResource: name, withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return nil }
        return try? decoder.decode(T.self, from: data)
    }
}
