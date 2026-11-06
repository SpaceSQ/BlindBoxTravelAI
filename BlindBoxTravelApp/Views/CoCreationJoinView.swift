import SwiftUI
import BlindBoxCore

/// 亲友在 APP 中打开 `.bbx` / 分享行程后的交互视图：
/// - 所有汉字直接明文呈现，并展示分享者标注/点评；
/// - 底部两个核心行动：【申请加入对方行程】 / 【创建一份自己的行程】。
struct CoCreationJoinView: View {
    let package: BBXPackage

    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss

    @State private var showCloneSheet = false
    @State private var cloned = false

    private var spots: [Spot] { package.spots }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        Text("好友分享的明文行程")
                            .font(.headline)
                            .foregroundStyle(.secondary)

                        ForEach(spots) { spot in
                            VStack(alignment: .leading, spacing: 6) {
                                Text(spot.fullName)
                                    .font(.headline)
                                Text("\(spot.province) · \(spot.city) · 门票 ¥\(spot.adultTicketPrice)")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.secondaryBackground, in: RoundedRectangle(cornerRadius: 14))
                        }

                        if let ann = package.order.userAnnotation {
                            VStack(alignment: .leading, spacing: 6) {
                                Text("分享者点评")
                                    .font(.caption.weight(.bold))
                                    .foregroundStyle(.secondary)
                                HStack(spacing: 4) {
                                    ForEach(0 ..< ann.ratingStars, id: \.self) { _ in
                                        Image(systemName: "star.fill").foregroundStyle(.yellow)
                                    }
                                    Text(ann.commentText)
                                        .font(.subheadline)
                                }
                            }
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.secondaryBackground, in: RoundedRectangle(cornerRadius: 14))
                        }
                    }
                    .padding()
                }

                Divider()

                VStack(spacing: 10) {
                    Button {
                        appState.orderStore.addParticipant(id: package.order.id, name: "好友A(已申请加入)")
                        dismiss()
                    } label: {
                        Label("申请加入对方行程", systemImage: "person.badge.plus")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)

                    Button {
                        showCloneSheet = true
                    } label: {
                        Label("创建一份自己的行程", systemImage: "doc.on.doc")
                            .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                }
                .padding()
            }
            .navigationTitle("行程共创")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button(L10n.back) { dismiss() }
                }
            }
            .sheet(isPresented: $showCloneSheet) {
                CloneOrderSheet(package: package)
                    .environmentObject(appState)
            }
        }
    }
}

/// 以明文行程为模板克隆新建，允许修改出发日期、出发地、交通方式。
struct CloneOrderSheet: View {
    let package: BBXPackage

    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    @State private var departureDate = Date()
    @State private var originCity = ""
    @State private var transport = TransportMode.highSpeedRail

    var body: some View {
        NavigationStack {
            Form {
                Section("修改你的出发参数") {
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
            }
            .navigationTitle("创建自己的行程")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("保存") {
                        let order = appState.importFromPackage(package, departureDate: departureDate, originCity: originCity, transport: transport)
                        dismiss()
                        appState.share(order)
                    }
                }
            }
            .onAppear { originCity = appState.defaultOriginCity }
        }
    }
}

#Preview {
    CoCreationJoinView(package: BBXPackage(
        format: "com.spacesq.blindboxtravel.bbx", version: 1,
        order: PlanOrder(
            id: "ORD_1", routeId: "RT001", durationDays: 2, routeType: .singleSpot,
            isFeatured: false, isUnlocked: true, spots: ["SP001"],
            departureConfig: DepartureConfig(departureDate: Date(), originCity: "深圳市",
                                             originLat: 22.5431, originLng: 114.0579, transportMode: .highSpeedRail)
        ),
        spots: [], createdAt: Date(), integrityHash: "abc"
    ))
    .environmentObject(AppState())
}
