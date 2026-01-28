//
//  StatsView.swift
//  ActionFigureTracker
//
//  Premium analytics dashboard for collectors
//

import SwiftUI

struct StatsView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    @State private var showingReset = false
    
    var body: some View {
        NavigationStack {
            ZStack {
                CollectorTheme.background
                    .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Overall stats
                        OverallStatsCard(dataStore: dataStore)
                        
                        // Stats by line
                        ForEach(FigureLine.allCases) { line in
                            LineStatsCard(line: line, dataStore: dataStore)
                        }
                        
                        // Favorites section
                        if !dataStore.favorites().isEmpty {
                            FavoritesSection(favorites: dataStore.favorites())
                        }
                        
                        // iCloud Status
                        iCloudStatusCard()
                        
                        // Reset button (hidden at bottom)
                        Button(action: { showingReset = true }) {
                            Text("Reset to Sample Data")
                                .font(.caption)
                                .foregroundStyle(CollectorTheme.textSecondary.opacity(0.5))
                        }
                        .padding(.top, 40)
                    }
                    .padding()
                }
            }
            .navigationTitle("Analytics")
            .alert("Reset Collection?", isPresented: $showingReset) {
                Button("Cancel", role: .cancel) { }
                Button("Reset", role: .destructive) {
                    dataStore.resetToMockData()
                }
            } message: {
                Text("This will replace your collection with sample data.")
            }
        }
    }
}

// MARK: - Overall Stats Card

struct OverallStatsCard: View {
    @ObservedObject var dataStore: FigureDataStore
    
    var total: Int { dataStore.figures.count }
    var have: Int { dataStore.totalHave }
    var want: Int { dataStore.totalWant }
    var progress: Double { total > 0 ? Double(have) / Double(total) : 0 }
    
    var body: some View {
        VStack(spacing: 20) {
            Text("COLLECTION OVERVIEW")
                .font(.system(.subheadline, design: .default, weight: .semibold))
                .textCase(.uppercase)
                .tracking(CollectorTheme.trackingWide)
                .foregroundStyle(CollectorTheme.textSecondary)
            
            // Progress ring
            ZStack {
                Circle()
                    .stroke(CollectorTheme.surfaceBackground, lineWidth: 16)
                
                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(
                        LinearGradient(
                            colors: [CollectorTheme.statusHave, CollectorTheme.accentGold],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        style: StrokeStyle(lineWidth: 16, lineCap: .round)
                    )
                    .rotationEffect(.degrees(-90))
                    .animation(.spring(response: 0.5), value: progress)
                
                VStack(spacing: 4) {
                    Text("\(have)")
                        .font(.system(size: 44, weight: .bold, design: .monospaced))
                        .foregroundStyle(CollectorTheme.textPrimary)
                    Text("of \(total)")
                        .font(.system(.subheadline, design: .monospaced))
                        .foregroundStyle(CollectorTheme.textSecondary)
                }
            }
            .frame(width: 160, height: 160)
            
            // Stats row
            HStack(spacing: 40) {
                StatItem(value: have, label: "OWNED", color: CollectorTheme.statusHave, emoji: "")
                StatItem(value: want, label: "WISHLIST", color: CollectorTheme.statusWant, emoji: "")
            }
        }
        .padding(24)
        .bentoCard()
    }
}

struct StatItem: View {
    let value: Int
    let label: String
    let color: Color
    let emoji: String
    
    var body: some View {
        VStack(spacing: 6) {
            // Glowing indicator dot
            Circle()
                .fill(color)
                .frame(width: 10, height: 10)
                .shadow(color: color.opacity(0.6), radius: 4, x: 0, y: 0)
            
            Text("\(value)")
                .font(.system(.title, design: .monospaced, weight: .bold))
                .foregroundStyle(color)
            
            Text(label)
                .font(.system(.caption2, design: .default, weight: .semibold))
                .textCase(.uppercase)
                .tracking(1)
                .foregroundStyle(CollectorTheme.textSecondary)
        }
    }
}

// MARK: - Line Stats Card

struct LineStatsCard: View {
    let line: FigureLine
    @ObservedObject var dataStore: FigureDataStore
    
    var have: Int { dataStore.count(for: line, status: .have) }
    var want: Int { dataStore.count(for: line, status: .want) }
    var total: Int { have + want }
    var progress: Double { total > 0 ? Double(have) / Double(total) : 0 }
    
    var lineColor: Color {
        switch line {
        case .dcMultiverse: return Color(hex: "4A90D9")
        case .dcPagePunchers: return Color(hex: "6B8DD6")  // Lighter blue for Page Punchers
        case .dcSuperPowers: return Color(hex: "9B59B6")
        case .dcRetro: return Color(hex: "00BCD4")
        case .dcDirect: return Color(hex: "5C6BC0")
        case .motuOrigins: return Color(hex: "FF9800")
        case .motuMasterverse: return Color(hex: "FFC107")
        case .marvelLegends: return Color(hex: "E53935")
        case .starWarsBlackSeries: return Color(hex: "607D8B")
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text(line.emoji)
                    .font(.title2)
                
                Text(line.rawValue)
                    .font(.system(.subheadline, design: .default, weight: .semibold))
                    .textCase(.uppercase)
                    .tracking(0.8)
                    .foregroundStyle(CollectorTheme.textPrimary)
                
                Spacer()
                
                Text("\(have)/\(total)")
                    .font(.system(.subheadline, design: .monospaced, weight: .bold))
                    .foregroundStyle(lineColor)
            }
            
            // Progress bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(CollectorTheme.surfaceBackground)
                    
                    RoundedRectangle(cornerRadius: 6)
                        .fill(
                            LinearGradient(
                                colors: [lineColor, lineColor.opacity(0.7)],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: geometry.size.width * progress)
                        .animation(.spring(response: 0.5), value: progress)
                        .shadow(color: lineColor.opacity(0.4), radius: 4, x: 0, y: 0)
                }
            }
            .frame(height: 8)
        }
        .padding(18)
        .bentoCard()
    }
}

// MARK: - Favorites Section

struct FavoritesSection: View {
    let favorites: [ActionFigure]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("FAVORITES")
                .font(.system(.subheadline, design: .default, weight: .semibold))
                .textCase(.uppercase)
                .tracking(CollectorTheme.trackingWide)
                .foregroundStyle(CollectorTheme.textSecondary)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 14) {
                    ForEach(favorites) { figure in
                        VStack(spacing: 8) {
                            FigureImageView(imageName: figure.imageName)
                                .frame(width: 70, height: 70)
                                .clipShape(Circle())
                                .overlay(
                                    Circle()
                                        .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                                )
                            
                            Text(figure.name)
                                .font(.system(.caption2, design: .monospaced))
                                .foregroundStyle(CollectorTheme.textSecondary)
                                .lineLimit(1)
                        }
                        .frame(width: 85)
                    }
                }
            }
        }
        .padding(18)
        .bentoCard()
    }
}

// MARK: - iCloud Status Card

struct iCloudStatusCard: View {
    @State private var storageLocation = iCloudPersistence.shared.storageLocation
    @State private var isiCloudAvailable = iCloudPersistence.shared.isiCloudAvailable
    
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Image(systemName: isiCloudAvailable ? "icloud.fill" : "icloud.slash.fill")
                    .font(.title3)
                    .foregroundStyle(isiCloudAvailable ? Color(hex: "4A90D9") : CollectorTheme.textSecondary)
                
                Text("DATA STORAGE")
                    .font(.system(.subheadline, design: .default, weight: .semibold))
                    .textCase(.uppercase)
                    .tracking(0.8)
                    .foregroundStyle(CollectorTheme.textPrimary)
                
                Spacer()
            }
            
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("Status")
                        .font(.caption)
                        .foregroundStyle(CollectorTheme.textSecondary)
                    Spacer()
                    Text(storageLocation)
                        .font(.system(.caption, design: .monospaced, weight: .semibold))
                        .foregroundStyle(isiCloudAvailable ? Color(hex: "4A90D9") : CollectorTheme.statusWant)
                }
                
                Text("Your collection is saved in the app's Documents folder. If you have iCloud Backup enabled, it will be automatically backed up and restored when you reinstall the app.")
                    .font(.caption2)
                    .foregroundStyle(CollectorTheme.textSecondary.opacity(0.7))
                    .lineSpacing(2)
            }
        }
        .padding(18)
        .bentoCard()
    }
}

#Preview {
    StatsView()
        .environmentObject(FigureDataStore())
}
