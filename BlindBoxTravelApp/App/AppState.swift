import Foundation
import SwiftUI
import Combine
import BlindBoxCore

/// 单条对话气泡。
struct ChatMessage: Identifiable, Equatable {
    enum Role: Equatable {
        case user
        case assistant
    }

    let id = UUID()
    let role: Role
    let text: String
    let quickOptions: [String]
}

/// 应用级状态：数据、对话引擎、会员、订单与分享/共创流程。
@MainActor
final class AppState: ObservableObject {
    // MARK: - 数据与对话
    @Published var store: DataStore
    @Published var messages: [ChatMessage] = []
    @Published var recommendations: [Route] = []
    @Published var selectedDistanceKm: Int = 6000
    @Published var unlockedRoute: Route?
    @Published var showCards = false

    // MARK: - 会员与订单
    @Published var membershipTier: MembershipTier = .free
    @Published var orderStore = PlanOrderStore()
    @Published var pendingUnlockRoute: Route?
    @Published var showSlotLimitAlert = false
    @Published var showPaywall = false
    @Published var showOrderCenter = false

    // MARK: - 分享 / 共创
    @Published var shareOrder: PlanOrder?
    @Published var coCreationPackage: BBXPackage?

    // MARK: - 进化变量同步（零溯源）
    @Published var evolution: EvolutionSyncEngine

    private var engine: DialogueEngine
    private var hasTriggered = false
    private var cancellables = Set<AnyCancellable>()

    /// 默认出发地（深圳）。真实产品中应读取 CoreLocation 当前坐标。
    let defaultOriginLat = 22.5431
    let defaultOriginLng = 114.0579
    let defaultOriginCity = "深圳市"

    init() {
        let store = DataStore.load(bundle: .main)
        self.store = store
        self.engine = DialogueEngine(vocab: store.tags)
        // 从种子 data 初始化进化变量（离线可用；在线时由 sync 拉取最新）
        let metrics = DataStore.loadEvolutionMetrics(bundle: .main) ?? EvolutionMetrics()
        self.evolution = EvolutionSyncEngine(metrics: metrics, transport: Self.makeTransport())
        // 将最新热度覆盖到推荐数据源。
        self.store = DataStore(
            spots: metrics.applying(to: store.spots),
            routes: metrics.applying(to: store.routes),
            tags: store.tags
        )
        // 转发订单仓库与同步引擎的变更，驱动 SwiftUI 刷新。
        orderStore.objectWillChange
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in self?.objectWillChange.send() }
            .store(in: &cancellables)
        evolution.objectWillChange
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in self?.objectWillChange.send() }
            .store(in: &cancellables)
        greet()
    }

    /// 构建 GitHub 同步传输（Token 缺省时返回 nil，保持离线入队）。
    private static func makeTransport() -> EvolutionSyncTransport? {
        guard let token = ProcessInfo.processInfo.environment["GITHUB_TOKEN"], !token.isEmpty else {
            return nil
        }
        return GitHubRESTTransport(
            repository: "SpaceSQ/BlindBoxTravelAI",
            filePath: "data/evolution_metrics.json",
            token: token
        )
    }

    private func greet() {
        messages.append(ChatMessage(
            role: .assistant,
            text: "嗨，我是你的盲盒旅行定制师～告诉我一点点心情、玩法或想去的地方，我就为你拆出惊喜行程。",
            quickOptions: ["想吃辣去嗦粉", "看雪山", "周末去玩", "随便推荐"]
        ))
    }

    // MARK: - 对话

    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        messages.append(ChatMessage(role: .user, text: trimmed, quickOptions: []))

        let result = engine.process(trimmed)
        messages.append(ChatMessage(role: .assistant, text: result.message, quickOptions: result.quickOptions))

        switch result.kind {
        case .reject, .followUp:
            break
        case .generate:
            runRecommendation()
        }
    }

    func sendQuick(_ option: String) { send(option) }

    private func runRecommendation() {
        let intent = engine.intent
        recommendations = RecommendationEngine.recommend(
            routes: store.routes,
            spotsById: store.spotsById,
            originLat: defaultOriginLat,
            originLng: defaultOriginLng,
            matchedTags: intent.matchedTags,
            maxDistanceKm: selectedDistanceKm,
            durationDays: intent.durationDays,
            month: Calendar.current.component(.month, from: Date()),
            specificity: IntentExtractor.specificity(intent)
        )
        hasTriggered = true
        withAnimation(.spring()) { showCards = true }
    }

    func applyDistanceFilter(_ km: Int) {
        selectedDistanceKm = km
        if hasTriggered { runRecommendation() }
    }

    func restart() {
        engine.reset()
        messages.removeAll()
        recommendations = []
        hasTriggered = false
        showCards = false
        unlockedRoute = nil
        greet()
    }

    // MARK: - 开盒与订单

    /// 用户选定盲盒。先做会员槽位校验：免费会员已有活跃订单 → 弹升级/管理双选项。
    func select(_ route: Route) {
        if membershipTier == .free && !orderStore.canCreate(tier: .free) {
            pendingUnlockRoute = route
            showSlotLimitAlert = true
            return
        }
        unlockedRoute = route
    }

    func dismissUnlock() { unlockedRoute = nil }

    /// 开盒成功 → 生成正式计划行程单并入库（is_unlocked = true，明文态）。
    func confirmOrder(route: Route, departureDate: Date, originCity: String, transport: TransportMode) -> PlanOrder {
        let order = PlanOrder(
            id: OrderID.generate(),
            routeId: route.id,
            durationDays: route.durationDays,
            routeType: route.routeType,
            isFeatured: route.isFeatured,
            isUnlocked: true,
            spots: route.spotIds,
            departureConfig: DepartureConfig(
                departureDate: departureDate,
                originCity: originCity,
                originLat: defaultOriginLat,
                originLng: defaultOriginLng,
                transportMode: transport
            )
        )
        orderStore.create(order)
        recordPlanDeltas(route: route)
        return order
    }

    /// 匿名记录“被标注成计划”进化增量。
    private func recordPlanDeltas(route: Route) {
        let spots = route.spotIds.compactMap { store.spotsById[$0] }
        evolution.record(EvolutionDeltaFactory.planOrderDeltas(route: route, spots: spots))
    }

    /// 匿名记录“被点评”进化增量（供订单标注点评后调用）。
    func recordReview(routeId: String) {
        guard let route = store.routesById[routeId] else { return }
        let spots = route.spotIds.compactMap { store.spotsById[$0] }
        evolution.record(EvolutionDeltaFactory.reviewDeltas(route: route, spots: spots))
    }

    // MARK: - 会员

    func upgradeToPro() {
        membershipTier = .pro
        showPaywall = false
        if let route = pendingUnlockRoute {
            pendingUnlockRoute = nil
            unlockedRoute = route
        }
    }

    func handleSlotLimitUpgrade() {
        showSlotLimitAlert = false
        showPaywall = true
    }

    func handleSlotLimitManageOrders() {
        showSlotLimitAlert = false
        showOrderCenter = true
    }

    func isBlockedFromGenerating() -> Bool {
        membershipTier == .free && !orderStore.canCreate(tier: .free)
    }

    // MARK: - 分享 / 共创

    /// 唤起系统分享（免费 & Pro 通用：普通分享）。
    func share(_ order: PlanOrder) {
        shareOrder = order
    }

    /// 尝试导出 `.bbx`：免费会员触发 Pro 升级；Pro 会员生成专有格式文件分享。
    func exportBBX(_ order: PlanOrder) {
        guard MembershipGatekeeper.canExportBBX(tier: membershipTier) else {
            showPaywall = true
            return
        }
        let spots = order.spots.compactMap { store.spotsById[$0] }
        let package = BBXCodec.makePackage(order: order, spots: spots)
        coCreationPackage = package
    }

    func dismissCoCreation() { coCreationPackage = nil }

    /// 亲友从 `.bbx` 打开 → “创建一份自己的行程”（克隆为独立订单，可改日期/出发地/交通方式）。
    func importFromPackage(_ package: BBXPackage, departureDate: Date, originCity: String, transport: TransportMode) -> PlanOrder {
        let src = package.order
        let order = PlanOrder(
            id: OrderID.generate(),
            routeId: src.routeId,
            durationDays: src.durationDays,
            routeType: src.routeType,
            isFeatured: false,
            isUnlocked: true,
            spots: src.spots,
            departureConfig: DepartureConfig(
                departureDate: departureDate,
                originCity: originCity,
                originLat: defaultOriginLat,
                originLng: defaultOriginLng,
                transportMode: transport
            )
        )
        orderStore.create(order)
        return order
    }
}
