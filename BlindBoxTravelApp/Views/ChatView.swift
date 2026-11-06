import SwiftUI

struct ChatView: View {
    @EnvironmentObject private var appState: AppState
    @State private var input = ""
    @FocusState private var inputFocused: Bool

    private let distanceOptions = [500, 1000, 2000, 3000, 4000, 5000, 6000]

    var body: some View {
        VStack(spacing: 0) {
            toolbar
            Divider()
            messageList
            inputBar
        }
        .navigationTitle(L10n.chatTab)
    }

    private var toolbar: some View {
        HStack {
            Text(L10n.distanceRange)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Spacer()
            Picker(L10n.distanceRange, selection: Binding(
                get: { appState.selectedDistanceKm },
                set: { appState.applyDistanceFilter($0) }
            )) {
                ForEach(distanceOptions, id: \.self) { km in
                    Text("\(km) km").tag(km)
                }
            }
            .pickerStyle(.menu)
            NavigationLink {
                PlanOrderCenterView()
            } label: {
                Image(systemName: "doc.text.magnifyingglass")
            }
            Button {
                appState.upgradeToPro() // 演示直接开通 Pro；真实产品走 StoreKit
            } label: {
                Image(systemName: appState.membershipTier == .pro ? "crown.fill" : "crown")
                    .foregroundStyle(appState.membershipTier == .pro ? .yellow : .secondary)
            }
            Button(L10n.restart) {
                appState.restart()
            }
            .buttonStyle(.borderless)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
    }

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 12) {
                    ForEach(appState.messages) { message in
                        bubble(message)
                            .id(message.id)
                    }
                }
                .padding()
            }
            .onChange(of: appState.messages.count) { _ in
                if let last = appState.messages.last {
                    withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                }
            }
        }
    }

    @ViewBuilder
    private func bubble(_ message: ChatMessage) -> some View {
        VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 8) {
            HStack {
                if message.role == .user { Spacer(minLength: 48) }
                Text(message.text)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        message.role == .user
                            ? Color.accentColor
                            : Color.secondaryBackground
                    )
                    .foregroundStyle(message.role == .user ? Color.white : Color.primary)
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                if message.role == .assistant { Spacer(minLength: 48) }
            }

            if message.role == .assistant && !message.quickOptions.isEmpty {
                HStack {
                    ForEach(message.quickOptions, id: \.self) { option in
                        Button(option) { appState.sendQuick(option) }
                            .buttonStyle(.bordered)
                            .font(.subheadline)
                    }
                    Spacer()
                }
                .padding(.leading, 4)
            }
        }
        .frame(maxWidth: .infinity, alignment: message.role == .user ? .trailing : .leading)
    }

    private var inputBar: some View {
        HStack(spacing: 10) {
            TextField(L10n.inspiration, text: $input, axis: .vertical)
                .lineLimit(1 ... 4)
                .textFieldStyle(.roundedBorder)
                .focused($inputFocused)
                .onSubmit { send() }

            Button(L10n.send) { send() }
                .buttonStyle(.borderedProminent)
                .disabled(input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
        .padding()
    }

    private func send() {
        let text = input
        input = ""
        inputFocused = true
        appState.send(text)
    }
}

#Preview {
    NavigationStack { ChatView() }
        .environmentObject(AppState())
}
