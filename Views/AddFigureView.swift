//
//  AddFigureView.swift
//  ActionFigureTracker
//
//  Premium form for adding new figures
//

import SwiftUI

struct AddFigureView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    @Environment(\.dismiss) var dismiss
    
    @State private var name = ""
    @State private var selectedLine: FigureLine = .dcMultiverse
    @State private var wave = ""
    @State private var status: CollectionStatus = .want
    @State private var notes = ""
    @State private var showingSuccess = false
    
    var isValid: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                CollectorTheme.background
                    .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Figure Name
                        FormSectionView(title: "NAME", icon: "person.fill") {
                            TextField("Figure Name", text: $name)
                                .font(.system(.body, design: .monospaced))
                                .foregroundStyle(CollectorTheme.textPrimary)
                                .padding(14)
                                .background(CollectorTheme.surfaceBackground)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                                )
                        }
                        
                        // Figure Line
                        FormSectionView(title: "LINE", icon: "tag.fill") {
                            Menu {
                                ForEach(FigureLine.allCases) { line in
                                    Button {
                                        selectedLine = line
                                    } label: {
                                        HStack {
                                            Text(line.emoji)
                                            Text(line.rawValue)
                                        }
                                    }
                                }
                            } label: {
                                HStack {
                                    Text(selectedLine.emoji)
                                    Text(selectedLine.rawValue)
                                        .font(.system(.body, design: .default))
                                    Spacer()
                                    Image(systemName: "chevron.up.chevron.down")
                                        .font(.caption)
                                        .foregroundStyle(CollectorTheme.textSecondary)
                                }
                                .foregroundStyle(CollectorTheme.textPrimary)
                                .padding(14)
                                .background(CollectorTheme.surfaceBackground)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                                )
                            }
                        }
                        
                        // Wave (optional)
                        FormSectionView(title: "WAVE", icon: "number") {
                            TextField("Wave (optional)", text: $wave)
                                .font(.system(.body, design: .default))
                                .foregroundStyle(CollectorTheme.textPrimary)
                                .padding(14)
                                .background(CollectorTheme.surfaceBackground)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                                )
                        }
                        
                        // Status
                        FormSectionView(title: "STATUS", icon: "checkmark.circle") {
                            HStack(spacing: 12) {
                                ForEach(CollectionStatus.allCases, id: \.self) { statusOption in
                                    Button {
                                        status = statusOption
                                    } label: {
                                        HStack(spacing: 8) {
                                            Circle()
                                                .fill(statusOption == .have ? CollectorTheme.statusHave : CollectorTheme.statusWant)
                                                .frame(width: 8, height: 8)
                                                .shadow(
                                                    color: status == statusOption
                                                        ? (statusOption == .have ? CollectorTheme.statusHaveGlow.opacity(0.6) : CollectorTheme.statusWant.opacity(0.5))
                                                        : .clear,
                                                    radius: 4
                                                )
                                            
                                            Text(statusOption == .have ? "OWNED" : "WISHLIST")
                                                .font(.system(.caption, design: .default, weight: .semibold))
                                                .textCase(.uppercase)
                                                .tracking(0.5)
                                        }
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 12)
                                        .background(
                                            status == statusOption
                                                ? (statusOption == .have ? CollectorTheme.statusHave.opacity(0.15) : CollectorTheme.statusWant.opacity(0.15))
                                                : CollectorTheme.surfaceBackground
                                        )
                                        .foregroundStyle(
                                            status == statusOption
                                                ? (statusOption == .have ? CollectorTheme.statusHave : CollectorTheme.statusWant)
                                                : CollectorTheme.textSecondary
                                        )
                                        .clipShape(RoundedRectangle(cornerRadius: 10))
                                        .overlay(
                                            RoundedRectangle(cornerRadius: 10)
                                                .stroke(
                                                    status == statusOption
                                                        ? (statusOption == .have ? CollectorTheme.statusHave.opacity(0.3) : CollectorTheme.statusWant.opacity(0.3))
                                                        : CollectorTheme.cardStrokeColor,
                                                    lineWidth: 1
                                                )
                                        )
                                    }
                                }
                            }
                        }
                        
                        // Notes
                        FormSectionView(title: "NOTES", icon: "pencil") {
                            TextField("Notes (optional)", text: $notes, axis: .vertical)
                                .lineLimit(3...6)
                                .font(.system(.body, design: .default))
                                .foregroundStyle(CollectorTheme.textPrimary)
                                .padding(14)
                                .background(CollectorTheme.surfaceBackground)
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                                )
                        }
                        
                        // Add Button
                        Button(action: addFigure) {
                            HStack(spacing: 10) {
                                Image(systemName: "plus.circle.fill")
                                    .font(.title3)
                                Text("ADD FIGURE")
                                    .font(.system(.subheadline, design: .default, weight: .semibold))
                                    .textCase(.uppercase)
                                    .tracking(1)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .background(isValid ? CollectorTheme.accentGold : CollectorTheme.surfaceBackground)
                            .foregroundStyle(isValid ? CollectorTheme.background : CollectorTheme.textSecondary)
                            .clipShape(RoundedRectangle(cornerRadius: 14))
                            .overlay(
                                RoundedRectangle(cornerRadius: 14)
                                    .stroke(
                                        isValid ? CollectorTheme.accentGold.opacity(0.5) : CollectorTheme.cardStrokeColor,
                                        lineWidth: 1
                                    )
                            )
                        }
                        .disabled(!isValid)
                        .padding(.top, 10)
                    }
                    .padding()
                }
            }
            .navigationTitle("Add Figure")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .foregroundStyle(CollectorTheme.textSecondary)
                }
            }
            .overlay(
                // Success animation
                Group {
                    if showingSuccess {
                        VStack(spacing: 16) {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 60))
                                .foregroundStyle(CollectorTheme.statusHave)
                            
                            Text("ADDED")
                                .font(.system(.headline, design: .default, weight: .semibold))
                                .textCase(.uppercase)
                                .tracking(CollectorTheme.trackingWide)
                                .foregroundStyle(CollectorTheme.textPrimary)
                        }
                        .padding(40)
                        .background(.ultraThinMaterial)
                        .clipShape(RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius))
                        .overlay(
                            RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius)
                                .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                        )
                        .transition(.scale.combined(with: .opacity))
                    }
                }
            )
        }
    }
    
    private func addFigure() {
        let newFigure = ActionFigure(
            name: name.trimmingCharacters(in: .whitespaces),
            line: selectedLine,
            wave: wave.isEmpty ? nil : wave,
            imageName: "placeholder", // User can add images later
            status: status,
            notes: notes
        )
        
        dataStore.addFigure(newFigure)
        
        // Show success animation
        withAnimation(.spring(response: 0.3)) {
            showingSuccess = true
        }
        
        // Dismiss after delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            dismiss()
        }
    }
}

// MARK: - Form Section View

struct FormSectionView<Content: View>: View {
    let title: String
    let icon: String
    let content: () -> Content
    
    init(title: String, icon: String, @ViewBuilder content: @escaping () -> Content) {
        self.title = title
        self.icon = icon
        self.content = content
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.caption)
                    .foregroundStyle(CollectorTheme.textSecondary)
                
                Text(title)
                    .font(.system(.caption, design: .default, weight: .semibold))
                    .textCase(.uppercase)
                    .tracking(1)
                    .foregroundStyle(CollectorTheme.textSecondary)
            }
            
            content()
        }
    }
}

#Preview {
    AddFigureView()
        .environmentObject(FigureDataStore())
}
