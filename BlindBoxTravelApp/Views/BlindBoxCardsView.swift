import SwiftUI
import BlindBoxCore

/// 3 条盲盒推荐卡片（首条重点推荐，隐去真名与票价）。
struct BlindBoxCardsView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    ForEach(Array(appState.recommendations.enumerated()), id: \.element.id) { index, route in
                        BlindBoxCard(route: route, featured: route.isFeatured, rank: index + 1)
                            .onTapGesture { appState.select(route) }
                    }
                }
                .padding()
            }
            .navigationTitle(L10n.recommendedRoutes)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(L10n.back) { dismiss() }
                }
            }
        }
    }
}

struct BlindBoxCard: View {
    let route: Route
    let featured: Bool
    let rank: Int

    @EnvironmentObject private var appState: AppState

    private var firstSpot: Spot? {
        guard let id = route.spotIds.first else { return nil }
        return appState.store.spotsById[id]
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                if featured {
                    Label(L10n.featured, systemImage: "star.fill")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(Color.orange, in: Capsule())
                } else {
                    Text("推荐 \(rank)")
                        .font(.caption.weight(.bold))
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(Color.secondaryBackground, in: Capsule())
                }
                Spacer()
                Text("\(route.durationDays) 天 · \(route.regionTag)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Text(route.blindRouteTitle)
                .font(.title3.weight(.bold))

            if let spot = firstSpot {
                HStack(spacing: 8) {
                    ForEach(spot.tags.prefix(4), id: \.name) { tag in
                        Text(tag.name)
                            .font(.caption2)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(tagColor(tag.type), in: Capsule())
                            .foregroundStyle(.primary)
                    }
                }
                HStack {
                    Text("\(spot.province) · \(spot.city)")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text("🎫 \(L10n.priceHidden)")
                        .font(.footnote.weight(.medium))
                        .foregroundStyle(.secondary)
                }
            }

            Button {
                appState.select(route)
            } label: {
                Text(L10n.generateOrder)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(featured ? .orange : .accentColor)
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .fill(Color.secondaryBackground)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(featured ? Color.orange : Color.clear, lineWidth: 2)
        )
    }

    private func tagColor(_ type: TagType) -> Color {
        type == .strong ? Color.accentColor.opacity(0.15) : Color.gray.opacity(0.15)
    }
}

#Preview {
    BlindBoxCardsView()
        .environmentObject(AppState())
}
