//
//  StatsView.swift
//  ActionFigureTracker
//
//  Fun stats page showing collection progress!
//

import SwiftUI

struct StatsView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    @State private var showingReset = false
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
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
                    
                    // Reset button (hidden at bottom)
                    Button(action: { showingReset = true }) {
                        Text("Reset to Sample Data")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.top, 40)
                }
                .padding()
            }
            .navigationTitle("My Stats! 📊")
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
        VStack(spacing: 16) {
            Text("🏆 Total Collection 🏆")
                .font(.title2)
                .fontWeight(.bold)
            
            // Progress ring
            ZStack {
                Circle()
                    .stroke(Color.gray.opacity(0.3), lineWidth: 20)
                
                Circle()
                    .trim(from: 0, to: progress)
                    .stroke(
                        LinearGradient(colors: [.green, .blue], 
                                      startPoint: .topLeading, 
                                      endPoint: .bottomTrailing),
                        style: StrokeStyle(lineWidth: 20, lineCap: .round)
                    )
                    .rotationEffect(.degrees(-90))
                    .animation(.spring(response: 0.5), value: progress)
                
                VStack {
                    Text("\(have)")
                        .font(.system(size: 48, weight: .bold))
                    Text("of \(total)")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(width: 180, height: 180)
            
            // Stats row
            HStack(spacing: 40) {
                StatItem(value: have, label: "Got It!", color: .green, emoji: "✅")
                StatItem(value: want, label: "Want It!", color: .orange, emoji: "⭐")
            }
        }
        .padding(24)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 24))
        .shadow(color: .black.opacity(0.1), radius: 10, x: 0, y: 5)
    }
}

struct StatItem: View {
    let value: Int
    let label: String
    let color: Color
    let emoji: String
    
    var body: some View {
        VStack(spacing: 4) {
            Text(emoji)
                .font(.title)
            Text("\(value)")
                .font(.title)
                .fontWeight(.bold)
                .foregroundStyle(color)
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
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
        // DC Lines
        case .dcMultiverse: return .blue
        case .dcSuperPowers: return .purple
        case .dcRetro: return .cyan
        case .dcDirect: return .indigo
        
        // MOTU Lines
        case .motuOrigins: return .orange
        case .motuMasterverse: return .yellow
        
        // Marvel
        case .marvelLegends: return .red
        
        // Star Wars
        case .starWarsBlackSeries: return .black
        }
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(line.emoji)
                    .font(.title)
                Text(line.rawValue)
                    .font(.headline)
                    .fontWeight(.bold)
                Spacer()
                Text("\(have)/\(total)")
                    .font(.title3)
                    .fontWeight(.bold)
                    .foregroundStyle(lineColor)
            }
            
            // Progress bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(Color.gray.opacity(0.2))
                    
                    RoundedRectangle(cornerRadius: 10)
                        .fill(lineColor)
                        .frame(width: geometry.size.width * progress)
                        .animation(.spring(response: 0.5), value: progress)
                }
            }
            .frame(height: 20)
        }
        .padding(20)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 4)
    }
}

// MARK: - Favorites Section

struct FavoritesSection: View {
    let favorites: [ActionFigure]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("❤️ My Favorites")
                    .font(.title2)
                    .fontWeight(.bold)
                Spacer()
            }
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 16) {
                    ForEach(favorites) { figure in
                        VStack {
                            FigureImageView(imageName: figure.imageName)
                                .frame(width: 80, height: 80)
                                .clipShape(Circle())
                            Text(figure.name)
                                .font(.caption)
                                .lineLimit(1)
                        }
                        .frame(width: 90)
                    }
                }
            }
        }
        .padding(20)
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 4)
    }
}

#Preview {
    StatsView()
        .environmentObject(FigureDataStore())
}
