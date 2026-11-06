import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            ChatView()
        }
        .sheet(isPresented: $appState.showCards) {
            BlindBoxCardsView()
                .environmentObject(appState)
        }
        .sheet(item: $appState.unlockedRoute) { route in
            UnlockCeremonyView(route: route)
                .environmentObject(appState)
        }
        .sheet(item: $appState.shareOrder) { order in
            ShareSheetView(order: order)
                .environmentObject(appState)
        }
        .sheet(item: $appState.coCreationPackage) { package in
            CoCreationJoinView(package: package)
                .environmentObject(appState)
        }
        .sheet(isPresented: $appState.showPaywall) {
            PaywallView()
                .environmentObject(appState)
        }
        .sheet(isPresented: $appState.showOrderCenter) {
            NavigationStack { PlanOrderCenterView() }
                .environmentObject(appState)
        }
        // 免费会员槽位限制：双选项模态框
        .alert("升级 Pro 会员", isPresented: $appState.showSlotLimitAlert) {
            Button("升级 Pro（¥28/月 或 ¥252/年）") { appState.handleSlotLimitUpgrade() }
            Button("前往订单管理删除已有行程") { appState.handleSlotLimitManageOrders() }
            Button("取消", role: .cancel) { appState.pendingUnlockRoute = nil }
        } message: {
            Text("免费会员仅能同时持有 1 个计划行程。升级 Pro 解锁无限量行程与专有格式导出，或删除已有行程后继续免费使用。")
        }
    }
}

#Preview {
    ContentView()
        .environmentObject(AppState())
}
