//
//  FigureDetailView.swift
//  ActionFigureTracker
//
//  Premium detail view for a single figure
//

import SwiftUI

struct FigureDetailView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    @Environment(\.dismiss) var dismiss
    
    let figure: ActionFigure
    @State private var notes: String = ""
    @State private var showingConfetti = false
    @State private var showingDeleteAlert = false
    @State private var showingImagePicker = false
    
    // Get the current figure from dataStore for live updates
    var currentFigure: ActionFigure {
        dataStore.figures.first { $0.id == figure.id } ?? figure
    }
    
    var body: some View {
        ZStack {
            CollectorTheme.background
                .ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 20) {
                    // Big Image with gradient
                    ZStack(alignment: .bottom) {
                        // Background
                        RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius)
                            .fill(CollectorTheme.surfaceBackground)
                            .frame(minHeight: 420)
                        
                        FigureImageView(imageName: currentFigure.imageName)
                            .frame(maxWidth: .infinity)
                            .frame(minHeight: 420)
                            .clipShape(RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius))
                        
                        // Gradient overlay
                        LinearGradient(
                            colors: [
                                .clear,
                                .clear,
                                CollectorTheme.cardBackground.opacity(0.5),
                                CollectorTheme.cardBackground.opacity(0.9)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                        .frame(height: 150)
                        .clipShape(RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius))
                        
                        // Badges overlay (top)
                        VStack {
                            HStack {
                                // Status pill
                                CollectionStatusPill(status: currentFigure.status)
                                
                                Spacer()
                                
                                // Platinum badge
                                if currentFigure.isPlatinum {
                                    PlatinumBadge()
                                }
                                
                                // Edit Image button
                                Button(action: {
                                    showingImagePicker = true
                                }) {
                                    Image(systemName: "photo.badge.arrow.down")
                                        .font(.title3)
                                        .foregroundStyle(CollectorTheme.accentGold)
                                        .padding(12)
                                        .background(.ultraThinMaterial.opacity(0.8))
                                        .clipShape(Circle())
                                        .overlay(
                                            Circle()
                                                .stroke(CollectorTheme.accentGold.opacity(0.3), lineWidth: 1)
                                        )
                                }
                                
                                // Favorite button
                                Button(action: {
                                    withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                                        dataStore.toggleFavorite(for: figure)
                                    }
                                }) {
                                    Image(systemName: currentFigure.isFavorite ? "heart.fill" : "heart")
                                        .font(.title3)
                                        .foregroundStyle(currentFigure.isFavorite ? .red : CollectorTheme.textSecondary)
                                        .padding(12)
                                        .background(.ultraThinMaterial.opacity(0.8))
                                        .clipShape(Circle())
                                        .overlay(
                                            Circle()
                                                .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                                        )
                                }
                            }
                            Spacer()
                        }
                        .padding(12)
                    }
                    .bentoCard()
                    
                    // Name and Line
                    VStack(spacing: 10) {
                        // Series label (year without locale formatting — e.g. 2025 not 2,025)
                        HStack(spacing: 8) {
                            Text(currentFigure.line.emoji)
                                .font(.title3)
                            
                            if let year = currentFigure.year {
                                Text("\(currentFigure.line.rawValue) • \(String(year))")
                                    .seriesLabelStyle()
                            } else {
                                Text(currentFigure.line.rawValue)
                                    .seriesLabelStyle()
                            }
                        }
                        
                        // Name (most descriptive title)
                        Text(currentFigure.name)
                            .font(.system(.title2, design: .monospaced, weight: .bold))
                            .foregroundStyle(CollectorTheme.textPrimary)
                            .multilineTextAlignment(.center)
                        
                        // Wave descriptor so you can tell figures apart
                        if let wave = currentFigure.wave, !wave.isEmpty {
                            Text("Wave: \(wave)")
                                .font(.system(.subheadline, design: .default, weight: .medium))
                                .foregroundStyle(CollectorTheme.textSecondary)
                        }
                    }
                    .padding(.horizontal)
                    
                    // Status Toggle Button
                    Button(action: {
                        withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                            if currentFigure.status == .want {
                                showingConfetti = true
                                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                                    showingConfetti = false
                                }
                            }
                            dataStore.toggleStatus(for: figure)
                        }
                    }) {
                        HStack(spacing: 10) {
                            Circle()
                                .fill(currentFigure.status == .have ? CollectorTheme.statusHave : CollectorTheme.statusWant)
                                .frame(width: 10, height: 10)
                                .shadow(
                                    color: currentFigure.status == .have ? CollectorTheme.statusHaveGlow.opacity(0.6) : CollectorTheme.statusWant.opacity(0.5),
                                    radius: 4,
                                    x: 0,
                                    y: 0
                                )
                            
                            Text(currentFigure.status == .have ? "IN COLLECTION" : "ADD TO COLLECTION")
                                .font(.system(.subheadline, design: .default, weight: .semibold))
                                .textCase(.uppercase)
                                .tracking(1)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(
                            currentFigure.status == .have
                                ? CollectorTheme.statusHave.opacity(0.15)
                                : CollectorTheme.statusWant.opacity(0.15)
                        )
                        .foregroundStyle(
                            currentFigure.status == .have
                                ? CollectorTheme.statusHave
                                : CollectorTheme.statusWant
                        )
                        .clipShape(RoundedRectangle(cornerRadius: 14))
                        .overlay(
                            RoundedRectangle(cornerRadius: 14)
                                .stroke(
                                    currentFigure.status == .have
                                        ? CollectorTheme.statusHave.opacity(0.3)
                                        : CollectorTheme.statusWant.opacity(0.3),
                                    lineWidth: 1
                                )
                        )
                    }
                    .scaleEffect(showingConfetti ? 1.02 : 1.0)
                    .animation(.spring(response: 0.3), value: showingConfetti)
                    .padding(.horizontal)
                    
                    // Accessories Section (if available)
                    if let accessories = currentFigure.accessories, !accessories.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("ACCESSORIES")
                                .font(.system(.subheadline, design: .default, weight: .semibold))
                                .textCase(.uppercase)
                                .tracking(CollectorTheme.trackingWide)
                                .foregroundStyle(CollectorTheme.textSecondary)
                            
                            Text(accessories)
                                .font(.system(.body, design: .default))
                                .foregroundStyle(CollectorTheme.textPrimary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(14)
                                .background(CollectorTheme.surfaceBackground)
                                .clipShape(RoundedRectangle(cornerRadius: 14))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 14)
                                        .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                                )
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal)
                    }
                    
                    // Notes Section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("NOTES")
                            .font(.system(.subheadline, design: .default, weight: .semibold))
                            .textCase(.uppercase)
                            .tracking(CollectorTheme.trackingWide)
                            .foregroundStyle(CollectorTheme.textSecondary)
                        
                        TextEditor(text: $notes)
                            .font(.system(.body, design: .default))
                            .foregroundStyle(CollectorTheme.textPrimary)
                            .scrollContentBackground(.hidden)
                            .frame(minHeight: 100)
                            .padding(14)
                            .background(CollectorTheme.surfaceBackground)
                            .clipShape(RoundedRectangle(cornerRadius: 14))
                            .overlay(
                                RoundedRectangle(cornerRadius: 14)
                                    .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                            )
                            .onChange(of: notes) { _, newValue in
                                dataStore.updateNotes(for: figure, notes: newValue)
                            }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
                    
                    Spacer(minLength: 50)
                }
                .padding(.vertical)
            }
        }
        .overlay(
            ConfettiView(isShowing: showingConfetti)
        )
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button(role: .destructive) {
                    showingDeleteAlert = true
                } label: {
                    Image(systemName: "trash")
                        .foregroundStyle(Color(hex: "E53935"))
                }
            }
        }
        .alert("Delete Figure?", isPresented: $showingDeleteAlert) {
            Button("Cancel", role: .cancel) { }
            Button("Delete", role: .destructive) {
                dataStore.deleteFigure(figure)
                dismiss()
            }
        } message: {
            Text("Are you sure you want to remove \(currentFigure.name) from your collection?")
        }
        .onAppear {
            notes = currentFigure.notes
        }
        .sheet(isPresented: $showingImagePicker) {
            ImageSearchView(figure: figure)
                .environmentObject(dataStore)
        }
    }
}

#Preview {
    NavigationStack {
        FigureDetailView(figure: MockData.dcMultiverseFigures[0])
            .environmentObject(FigureDataStore())
    }
}
