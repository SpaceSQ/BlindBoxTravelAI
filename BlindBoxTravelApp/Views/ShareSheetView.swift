import SwiftUI
import BlindBoxCore

/// 普通社交媒体分享（免费 & Pro 通用）：将明文计划行程单渲染为高颜值长图，
/// 调用系统 ShareSheet 分享至微信朋友圈、小红书、抖音。
struct ShareSheetView: View {
    let order: PlanOrder

    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    private var spots: [Spot] {
        order.spots.compactMap { appState.store.spotsById[$0] }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                shareCard
                Button {
                    // 使用系统分享面板分享长图（此演示分享文字摘要；长图渲染见 ImageRenderer）
                    shareImage()
                } label: {
                    Label("分享至微信 / 小红书 / 抖音", systemImage: "square.and.arrow.up")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            }
            .padding()
            .navigationTitle("分享行程")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(L10n.back) { dismiss() }
                }
            }
        }
    }

    private var shareCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("🎁 我的盲盒旅行计划")
                .font(.title3.weight(.bold))
            ForEach(spots) { spot in
                VStack(alignment: .leading, spacing: 4) {
                    Text(spot.fullName)
                        .font(.headline)
                    Text("\(spot.province) · \(spot.city) · 门票 ¥\(spot.adultTicketPrice)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            Divider()
            HStack {
                Text("出发 \(order.departureConfig.departureDate.formatted(date: .abbreviated, time: .omitted))")
                Spacer()
                Text(order.departureConfig.transportMode.rawValue)
            }
            .font(.subheadline)
            if let ann = order.userAnnotation {
                HStack(spacing: 4) {
                    ForEach(0 ..< ann.ratingStars, id: \.self) { _ in
                        Image(systemName: "star.fill").foregroundStyle(.yellow)
                    }
                    Text(ann.commentText)
                        .font(.caption)
                }
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(Color.secondaryBackground)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 20)
                .stroke(Color.accentColor.opacity(0.3), lineWidth: 1)
        )
    }

    private func shareImage() {
        #if os(macOS)
        // macOS 无 UIActivityViewController，演示中跳过系统分享
        dismiss()
        #else
        let renderer = ImageRenderer(content: shareCard)
        if let image = renderer.uiImage {
            let activity = UIActivityViewController(activityItems: [image], applicationActivities: nil)
            if let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
               let root = scene.windows.first?.rootViewController {
                root.present(activity, animated: true)
            }
        }
        #endif
    }
}

#Preview {
    ShareSheetView(order: PlanOrder(
        id: "ORD_1", routeId: "RT001", durationDays: 2, routeType: .singleSpot,
        isFeatured: false, isUnlocked: true, spots: ["SP001"],
        departureConfig: DepartureConfig(departureDate: Date(), originCity: "深圳市",
                                         originLat: 22.5431, originLng: 114.0579, transportMode: .highSpeedRail)
    ))
    .environmentObject(AppState())
}
