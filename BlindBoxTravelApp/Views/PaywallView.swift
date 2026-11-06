import SwiftUI
import BlindBoxCore

/// Pro 会员订阅墙（¥28/月、¥252/年）。
struct PaywallView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    @State private var selectedProduct: SubscriptionProduct?

    private var products: [SubscriptionProduct] { MembershipGatekeeper.products }

    var body: some View {
        VStack(spacing: 24) {
            Spacer()
            Image(systemName: "crown.fill")
                .font(.system(size: 56))
                .foregroundStyle(.yellow)
            Text("升级 Pro 会员")
                .font(.largeTitle.weight(.bold))
            Text("无限量行程 · .bbx 专有格式导出 · 无水印高清分享")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            VStack(spacing: 12) {
                ForEach(products) { product in
                    productCard(product)
                }
            }
            .padding(.horizontal)

            Button {
                appState.upgradeToPro()
                dismiss()
            } label: {
                Text(selectedProduct.map { "开通 \($0.name) ¥\(Int($0.priceYuan))" } ?? "选择套餐后开通")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(selectedProduct == nil)
            .padding(.horizontal)

            Button("暂不需要") { dismiss() }
                .foregroundStyle(.secondary)
            Spacer()
        }
        .padding()
        .onAppear { selectedProduct = products.first }
    }

    private func productCard(_ product: SubscriptionProduct) -> some View {
        let isSelected = selectedProduct?.id == product.id
        return Button {
            selectedProduct = product
        } label: {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(product.name)
                        .font(.headline)
                    Text(product.period == .yearly ? "折合 ¥21/月" : "按月订阅")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                Text("¥\(Int(product.priceYuan))")
                    .font(.title3.weight(.bold))
            }
            .padding()
            .background(Color.secondaryBackground, in: RoundedRectangle(cornerRadius: 14))
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    PaywallView()
        .environmentObject(AppState())
}
