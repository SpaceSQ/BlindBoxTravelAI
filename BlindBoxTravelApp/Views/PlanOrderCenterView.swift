import SwiftUI
import BlindBoxCore

/// 旅行计划管理中心：已出行 / 计划改变 / 计划取消 / 删除 + 标注点评。
struct PlanOrderCenterView: View {
    @EnvironmentObject private var appState: AppState

    private var orders: [PlanOrder] {
        appState.orderStore.orders.sorted { $0.departureConfig.departureDate > $1.departureConfig.departureDate }
    }

    var body: some View {
        Group {
            if orders.isEmpty {
                emptyState
            } else {
                List {
                    Section {
                        Text(appState.membershipTier == .pro
                             ? "Pro 会员 · 无限量行程"
                             : "免费会员 · 已用 \(appState.orderStore.activeOrders.count)/1 槽位")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                        Text(syncStatusText)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                    ForEach(orders) { order in
                        OrderRow(order: order)
                    }
                }
            }
        }
        .navigationTitle("旅行计划")
    }

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "tray")
                .font(.system(size: 44))
                .foregroundStyle(.secondary)
            Text("还没有计划行程，去拆一个盲盒吧～")
                .foregroundStyle(.secondary)
        }
    }

    private var syncStatusText: String {
        let pending = appState.evolution.pendingCount
        if pending == 0 { return "进化变量已同步（零溯源匿名统计）" }
        return "进化变量待同步 \(pending) 条（联网后自动推送至 GitHub）"
    }
}

struct OrderRow: View {
    let order: PlanOrder

    @EnvironmentObject private var appState: AppState
    @State private var showAnnotation = false

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(order.departureConfig.originCity + " → " + order.spots.joined(separator: " · "))
                    .font(.subheadline.weight(.semibold))
                Spacer()
                statusBadge(order.orderStatus)
            }

            Text("出发 \(formattedDate(order.departureConfig.departureDate)) · \(order.departureConfig.transportMode.rawValue)")
                .font(.caption)
                .foregroundStyle(.secondary)

            if let ann = order.userAnnotation {
                HStack(spacing: 4) {
                    ForEach(0 ..< ann.ratingStars, id: \.self) { _ in
                        Image(systemName: "star.fill").foregroundStyle(.yellow)
                    }
                    Text(ann.commentText)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }
            }

            HStack(spacing: 12) {
                statusMenu
                Button(order.userAnnotation == nil ? "标注/点评" : "修改点评") {
                    showAnnotation = true
                }
                .font(.caption)
                .buttonStyle(.bordered)
                Button {
                    appState.share(order)
                } label: {
                    Label("分享", systemImage: "square.and.arrow.up")
                }
                .font(.caption)
                .buttonStyle(.bordered)
                Button {
                    appState.exportBBX(order)
                } label: {
                    Label("导出 .bbx", systemImage: "doc.badge.gearshape")
                }
                .font(.caption)
                .buttonStyle(.bordered)
            }
        }
        .padding(.vertical, 6)
        .sheet(isPresented: $showAnnotation) {
            AnnotationView(order: order)
                .environmentObject(appState)
        }
    }

    private var statusMenu: some View {
        Menu {
            Button("标记已出行") { appState.orderStore.markCompleted(id: order.id) }
            Button("计划改变") { appState.orderStore.markModified(id: order.id) }
            Button("计划取消") { appState.orderStore.markCancelled(id: order.id) }
            Button("删除订单", role: .destructive) { appState.orderStore.delete(id: order.id) }
        } label: {
            Label("状态", systemImage: "ellipsis.circle")
        }
        .font(.caption)
        .buttonStyle(.bordered)
    }

    private func statusBadge(_ status: OrderStatus) -> some View {
        Text(statusLabel(status))
            .font(.caption2.weight(.bold))
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(statusColor(status), in: Capsule())
            .foregroundStyle(.primary)
    }

    private func statusLabel(_ s: OrderStatus) -> String {
        switch s {
        case .planned: return "待出行"
        case .completed: return "已出行"
        case .modified: return "计划改变"
        case .cancelled: return "已取消"
        case .deleted: return "已删除"
        }
    }

    private func statusColor(_ s: OrderStatus) -> Color {
        switch s {
        case .planned: return .blue.opacity(0.15)
        case .completed: return .green.opacity(0.2)
        case .modified: return .orange.opacity(0.2)
        case .cancelled: return .gray.opacity(0.2)
        case .deleted: return .red.opacity(0.15)
        }
    }

    private func formattedDate(_ d: Date) -> String {
        d.formatted(date: .abbreviated, time: .omitted)
    }
}

/// 匿名标注/点评表单（严格不含任何身份字段）。
struct AnnotationView: View {
    let order: PlanOrder

    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    @State private var rating = 5
    @State private var comment = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("评分") {
                    Picker("星级", selection: $rating) {
                        ForEach(1 ... 5, id: \.self) { Text("\($0) 星").tag($0) }
                    }
                    .pickerStyle(.segmented)
                }
                Section("点评（随分享发出，绝不溯源显示来源）") {
                    TextEditor(text: $comment)
                        .frame(minHeight: 100)
                }
            }
            .navigationTitle("标注/点评")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("保存") {
                        appState.orderStore.annotate(id: order.id, ratingStars: rating, commentText: comment)
                        appState.recordReview(routeId: order.routeId)
                        dismiss()
                    }
                }
            }
            .onAppear {
                if let ann = order.userAnnotation {
                    rating = ann.ratingStars
                    comment = ann.commentText
                }
            }
        }
    }
}

#Preview {
    NavigationStack { PlanOrderCenterView() }
        .environmentObject(AppState())
}
