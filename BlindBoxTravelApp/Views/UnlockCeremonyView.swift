import SwiftUI
import BlindBoxCore

/// 选定盲盒 → 填写【出发日期、出发地、交通方式】→ 开盲盒明文解锁动效 → 生成正式订单。
struct UnlockCeremonyView: View {
    let route: Route

    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    @State private var departureDate = Date()
    @State private var originCity = ""
    @State private var transport = TransportMode.highSpeedRail
    @State private var isUnlocked = false
    @State private var confirmedOrder: PlanOrder?

    private var spots: [Spot] {
        route.spotIds.compactMap { appState.store.spotsById[$0] }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    routeTitle
                    formSection
                    if isUnlocked {
                        unlockedContent
                        if let order = confirmedOrder {
                            orderActions(order)
                        }
                    } else {
                        unlockButton
                    }
                }
                .padding()
            }
            .navigationTitle(L10n.generateOrder)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(L10n.back) { dismiss() }
                }
            }
            .onAppear { originCity = appState.defaultOriginCity }
        }
    }

    private var routeTitle: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(isUnlocked ? fullRouteTitle : route.blindRouteTitle)
                .font(.title3.weight(.bold))
            Text("\(route.durationDays) 天 · \(route.regionTag)")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var fullRouteTitle: String {
        spots.map(\.fullName).joined(separator: " · ")
    }

    private var formSection: some View {
        Group {
            DatePicker(L10n.departureDate, selection: $departureDate, displayedComponents: .date)
            HStack {
                Text(L10n.originCity)
                Spacer()
                TextField(L10n.originCity, text: $originCity)
                    .multilineTextAlignment(.trailing)
            }
            Picker(L10n.transportMode, selection: $transport) {
                ForEach(TransportMode.allCases) { mode in
                    Text(mode.rawValue).tag(mode)
                }
            }
        }
        .disabled(isUnlocked)
    }

    private var unlockButton: some View {
        Button { playUnlock() } label: {
            Label(L10n.unlock, systemImage: "shippingbox.fill")
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.borderedProminent)
        .controlSize(.large)
    }

    private var unlockedContent: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(L10n.unlocked)
                .font(.headline)
                .foregroundStyle(.green)

            ForEach(spots) { spot in
                VStack(alignment: .leading, spacing: 6) {
                    Text(spot.fullName)
                        .font(.headline)
                    Text("\(spot.province) · \(spot.city)")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Text("\(L10n.ticket)：¥\(spot.adultTicketPrice)")
                        .font(.subheadline)
                    if !spot.eventsAndDiscounts.isEmpty {
                        Text(spot.eventsAndDiscounts)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.secondaryBackground, in: RoundedRectangle(cornerRadius: 14))
                .transition(.scale.combined(with: .opacity))
            }
        }
    }

    private func orderActions(_ order: PlanOrder) -> some View {
        VStack(spacing: 10) {
            Button {
                appState.share(order)
            } label: {
                Label("分享行程", systemImage: "square.and.arrow.up")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)

            Button {
                appState.exportBBX(order)
            } label: {
                Label(appState.membershipTier == .pro ? "导出 .bbx 专有格式" : "导出 .bbx（Pro 专属）", systemImage: "doc.badge.gearshape")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .tint(.indigo)

            Button {
                dismiss()
            } label: {
                Text("完成")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.bordered)
        }
    }

    private func playUnlock() {
        withAnimation(.easeInOut(duration: 1.5)) {
            isUnlocked = true
        }
        confirmedOrder = appState.confirmOrder(route: route, departureDate: departureDate, originCity: originCity, transport: transport)
    }
}

#Preview {
    UnlockCeremonyView(route: Route(
        id: "RT001", fullRouteTitle: "甘孜稻城亚丁风景区·两日神山朝圣游",
        blindRouteTitle: "**稻**丁***·两日神山朝圣游",
        durationDays: 2, routeType: .singleSpot, spotIds: ["SP001"],
        regionTag: "西南秘境", searchKeywordsMatched: [], dailySchedule: []
    ))
    .environmentObject(AppState())
}
