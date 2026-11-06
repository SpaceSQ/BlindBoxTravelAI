import XCTest
@testable import BlindBoxCore

final class EvolutionSyncTests: XCTestCase {
    var store: DataStore!

    override func setUpWithError() throws {
        store = DataStore.load(directory: Self.dataDirectory())
    }

    static func dataDirectory() -> URL {
        var url = URL(fileURLWithPath: #filePath)
        for _ in 0 ..< 5 { url.deleteLastPathComponent() }
        return url.appendingPathComponent("data")
    }

    // MARK: - Metrics 模型

    func testMetricsDecodeFromSeedData() throws {
        let url = Self.dataDirectory().appendingPathComponent("evolution_metrics.json")
        let data = try Data(contentsOf: url)
        let metrics = try EvolutionMetrics.decode(data)
        XCTAssertEqual(metrics.spotsMetrics.count, 5)
        XCTAssertEqual(metrics.routesMetrics.count, 9)
        XCTAssertEqual(metrics.stats(spotId: "SP001").planMarkCount, 0)
    }

    func testApplyingDeltasAccumulates() {
        let metrics = EvolutionMetrics()
        let deltas = [
            EvolutionDelta(scope: .spot, id: "SP001", planMarkIncrement: 1),
            EvolutionDelta(scope: .spot, id: "SP001", reviewIncrement: 1),
            EvolutionDelta(scope: .route, id: "RT001", planMarkIncrement: 1),
        ]
        let updated = metrics.applying(deltas)
        XCTAssertEqual(updated.stats(spotId: "SP001").planMarkCount, 1)
        XCTAssertEqual(updated.stats(spotId: "SP001").reviewCount, 1)
        XCTAssertEqual(updated.stats(routeId: "RT001").planMarkCount, 1)
    }

    func testApplyingToRoutesOverridesStats() {
        let metrics = EvolutionMetrics(routesMetrics: ["RT001": EvolutionStats(planMarkCount: 5, reviewCount: 3)])
        let overridden = metrics.applying(to: store.routes)
        let target = overridden.first { $0.id == "RT001" }!
        XCTAssertEqual(target.evolutionStats.planMarkCount, 5)
        XCTAssertEqual(target.evolutionStats.reviewCount, 3)
    }

    // MARK: - 增量工厂

    func testPlanOrderDeltasCoverRouteAndSpots() {
        let route = store.routes.first { $0.spotIds.contains("SP001") }!
        let spots = route.spotIds.compactMap { store.spotsById[$0] }
        let deltas = EvolutionDeltaFactory.planOrderDeltas(route: route, spots: spots)
        // 1 条路线 + N 个景点
        XCTAssertEqual(deltas.count, 1 + spots.count)
        XCTAssertTrue(deltas.contains { $0.scope == .route && $0.id == route.id && $0.planMarkIncrement == 1 })
        for spot in spots {
            XCTAssertTrue(deltas.contains { $0.scope == .spot && $0.id == spot.id && $0.planMarkIncrement == 1 })
        }
    }

    func testReviewDeltasIncrementReviewOnly() {
        let route = store.routes.first { $0.spotIds.contains("SP001") }!
        let spots = route.spotIds.compactMap { store.spotsById[$0] }
        let deltas = EvolutionDeltaFactory.reviewDeltas(route: route, spots: spots)
        XCTAssertTrue(deltas.allSatisfy { $0.planMarkIncrement == 0 && $0.reviewIncrement == 1 })
    }

    // MARK: - 同步引擎

    @MainActor
    func testRecordAppliesLocallyAndQueues() {
        let engine = EvolutionSyncEngine(metrics: EvolutionMetrics(), transport: nil)
        engine.record([EvolutionDelta(scope: .spot, id: "SP001", planMarkIncrement: 1)])
        XCTAssertEqual(engine.metrics.stats(spotId: "SP001").planMarkCount, 1)
        XCTAssertEqual(engine.pendingCount, 1)
    }

    @MainActor
    func testFlushWithoutTransportKeepsQueue() async {
        let engine = EvolutionSyncEngine(metrics: EvolutionMetrics(), transport: nil)
        engine.record([EvolutionDelta(scope: .spot, id: "SP001", planMarkIncrement: 1)])
        let flushed = await engine.flush()
        XCTAssertFalse(flushed)  // 无 transport，保持离线入队
        XCTAssertEqual(engine.pendingCount, 1)
    }

    @MainActor
    func testFlushWithTransportDrainsQueue() async {
        let transport = MockTransport(remoteMetrics: EvolutionMetrics())
        let engine = EvolutionSyncEngine(metrics: EvolutionMetrics(), transport: transport)
        engine.record([EvolutionDelta(scope: .spot, id: "SP001", planMarkIncrement: 1)])
        let flushed = await engine.flush()
        XCTAssertTrue(flushed)
        XCTAssertEqual(engine.pendingCount, 0)
        let calls = await transport.pushCallCount
        XCTAssertEqual(calls, 1)
        // 合并后本地 metrics 已反映增量
        XCTAssertEqual(engine.metrics.stats(spotId: "SP001").planMarkCount, 1)
    }

    @MainActor
    func testFlushMergesRemoteState() async {
        // 远端已含 4 次计划标注，本地又有 1 次待同步 → 合并后应为 5
        let remote = EvolutionMetrics(spotsMetrics: ["SP001": EvolutionStats(planMarkCount: 4, reviewCount: 0)])
        let transport = MockTransport(remoteMetrics: remote)
        let engine = EvolutionSyncEngine(metrics: EvolutionMetrics(), transport: transport)
        engine.record([EvolutionDelta(scope: .spot, id: "SP001", planMarkIncrement: 1)])
        let flushed = await engine.flush()
        XCTAssertTrue(flushed)
        XCTAssertEqual(engine.metrics.stats(spotId: "SP001").planMarkCount, 5)
        let pushed = await transport.lastPushedMetrics
        XCTAssertEqual(pushed?.stats(spotId: "SP001").planMarkCount, 5)
    }

    @MainActor
    func testQueuePersistenceRoundTrip() async throws {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("pending_evolution_deltas_test_\(UUID().uuidString).json")
        defer { try? FileManager.default.removeItem(at: url) }

        let engine = EvolutionSyncEngine(metrics: EvolutionMetrics(), transport: nil, queueURL: url)
        engine.record([EvolutionDelta(scope: .spot, id: "SP001", planMarkIncrement: 1)])
        engine.persistQueueIfNeeded()

        let loaded = try EvolutionSyncEngine.loadQueue(from: url)
        XCTAssertEqual(loaded.count, 1)
        XCTAssertEqual(loaded.first?.id, "SP001")
    }
}

/// 内存 mock 传输层。
private actor MockTransport: EvolutionSyncTransport {
    var remoteMetrics: EvolutionMetrics
    var pushCallCount = 0
    var lastPushedMetrics: EvolutionMetrics?

    init(remoteMetrics: EvolutionMetrics) {
        self.remoteMetrics = remoteMetrics
    }

    func fetchCurrentState() async throws -> (sha: String, metrics: EvolutionMetrics) {
        ("sha_0", remoteMetrics)
    }

    func push(metrics: EvolutionMetrics, sha: String) async throws -> String {
        pushCallCount += 1
        lastPushedMetrics = metrics
        remoteMetrics = metrics
        return "sha_\(pushCallCount)"
    }
}
