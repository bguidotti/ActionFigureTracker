//
//  FigureGridView.swift
//  ActionFigureTracker
//
//  Grid view showing all figures with filtering
//

import SwiftUI
import Combine

struct FigureGridView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    @State private var selectedLine: FigureLine? = nil
    @State private var searchText = ""
    @State private var sortOption: SortOption = .newestFirst
    
    private let columns = [
        GridItem(.flexible(), spacing: 16)
    ]
    
    var filteredFigures: [ActionFigure] {
        var result = dataStore.figures(for: selectedLine, status: nil)
        
        if !searchText.isEmpty {
            result = result.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
        
        // Apply sorting
        return sortFigures(result, by: sortOption)
    }
    
    private func sortFigures(_ figures: [ActionFigure], by option: SortOption) -> [ActionFigure] {
        switch option {
        case .newestFirst:
            // Create indexed array to preserve original order
            let indexed = figures.enumerated().map { (index: $0.offset, figure: $0.element) }
            return indexed.sorted { first, second in
                // Primary sort: by year (if available), then by date
                if let year1 = first.figure.year, let year2 = second.figure.year {
                    if year1 != year2 {
                        return year1 > year2 // Newest year first
                    }
                } else if first.figure.year != nil {
                    return true // Figures with year come before those without
                } else if second.figure.year != nil {
                    return false
                }
                
                // Secondary sort: by date
                if first.figure.dateAdded != second.figure.dateAdded {
                    return first.figure.dateAdded > second.figure.dateAdded
                }
                
                // Tertiary sort: preserve original order (use index)
                return first.index < second.index
            }.map { $0.figure }
        case .oldestFirst:
            // Create indexed array to preserve original order
            let indexed = figures.enumerated().map { (index: $0.offset, figure: $0.element) }
            return indexed.sorted { first, second in
                // Primary sort: by year (if available), then by date
                if let year1 = first.figure.year, let year2 = second.figure.year {
                    if year1 != year2 {
                        return year1 < year2 // Oldest year first
                    }
                } else if first.figure.year != nil {
                    return true // Figures with year come before those without
                } else if second.figure.year != nil {
                    return false
                }
                
                // Secondary sort: by date
                if first.figure.dateAdded != second.figure.dateAdded {
                    return first.figure.dateAdded < second.figure.dateAdded
                }
                
                // Tertiary sort: preserve original order (use index)
                return first.index < second.index
            }.map { $0.figure }
        case .alphabetical:
            return figures.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
        case .reverseAlphabetical:
            return figures.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedDescending }
        }
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Dark background
                CollectorTheme.background
                    .ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // Line Picker - Premium style
                    LinePickerView(selectedLine: $selectedLine)
                        .padding(.horizontal)
                        .padding(.top, 8)
                    
                    // Figure Grid
                    ScrollViewReader { proxy in
                        ScrollView {
                            LazyVGrid(columns: columns, spacing: 16) {
                                ForEach(filteredFigures) { figure in
                                    NavigationLink(destination: FigureDetailView(figure: figure)) {
                                        FigureCardView(figure: figure)
                                    }
                                    .buttonStyle(.plain)
                                    .id(figure.id)
                                }
                            }
                            .padding()
                            .id("top")
                        }
                        .onChange(of: selectedLine) { _, _ in
                            withAnimation {
                                proxy.scrollTo("top", anchor: .top)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Collection")
            .searchable(text: $searchText, prompt: "Search figures...")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    HStack(spacing: 12) {
                        // Sort menu
                        Menu {
                            Picker("Sort", selection: $sortOption) {
                                ForEach(SortOption.allCases, id: \.self) { option in
                                    Label(option.rawValue, systemImage: option.icon)
                                        .tag(option)
                                }
                            }
                        } label: {
                            Image(systemName: "arrow.up.arrow.down.circle")
                                .font(.title2)
                                .foregroundStyle(CollectorTheme.accentGold)
                        }
                        
                        // Add button
                        NavigationLink(destination: AddFigureView()) {
                            Image(systemName: "plus.circle.fill")
                                .font(.title2)
                                .foregroundStyle(CollectorTheme.accentGold)
                        }
                    }
                }
            }
        }
    }
}

// MARK: - Line Picker (Big Buttons!)

struct LinePickerView: View {
    @Binding var selectedLine: FigureLine?
    
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 10) {
                // All button
                LineButton(
                    title: "All",
                    emoji: "🌟",
                    isSelected: selectedLine == nil,
                    color: CollectorTheme.accentGold
                ) {
                    selectedLine = nil
                }
                
                // Each figure line
                ForEach(FigureLine.allCases) { line in
                    LineButton(
                        title: line.rawValue,
                        emoji: line.emoji,
                        isSelected: selectedLine == line,
                        color: colorForLine(line)
                    ) {
                        selectedLine = line
                    }
                }
            }
            .padding(.vertical, 8)
        }
    }
    
    private func colorForLine(_ line: FigureLine) -> Color {
        switch line {
        case .dcMultiverse: return Color(hex: "4A90D9")
        case .dcPagePunchers: return Color(hex: "6B8DD6")
        case .dcSuperPowers: return Color(hex: "9B59B6")
        case .dcRetro: return Color(hex: "00BCD4")
        case .dcDirect: return Color(hex: "5C6BC0")
        case .motuOrigins: return Color(hex: "FF9800")
        case .motuMasterverse: return Color(hex: "FFC107")
        case .marvelLegends: return Color(hex: "E53935")
        case .starWarsBlackSeries: return Color(hex: "607D8B")
        }
    }
}

struct LineButton: View {
    let title: String
    let emoji: String
    let isSelected: Bool
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Text(emoji)
                    .font(.title2)
                Text(title)
                    .font(.system(.caption2, design: .default, weight: .semibold))
                    .textCase(.uppercase)
                    .tracking(0.5)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
            }
            .frame(minWidth: 75)
            .padding(.vertical, 10)
            .padding(.horizontal, 10)
            .background(
                isSelected 
                    ? color.opacity(0.3)
                    : CollectorTheme.surfaceBackground
            )
            .foregroundStyle(isSelected ? color : CollectorTheme.textSecondary)
            .clipShape(RoundedRectangle(cornerRadius: 14))
            .overlay(
                RoundedRectangle(cornerRadius: 14)
                    .stroke(
                        isSelected ? color.opacity(0.6) : CollectorTheme.cardStrokeColor,
                        lineWidth: isSelected ? 1.5 : 1
                    )
            )
        }
        .scaleEffect(isSelected ? 1.02 : 1.0)
        .animation(.spring(response: 0.25), value: isSelected)
    }
}

// MARK: - Figure Card (Bento Style)

struct FigureCardView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    let figure: ActionFigure
    @State private var showingConfetti = false
    
    var body: some View {
        VStack(spacing: 12) {
            // Figure Image with gradient overlay
            ZStack(alignment: .bottom) {
                FigureImageView(imageName: figure.imageName)
                    .frame(maxWidth: .infinity)
                    .frame(minHeight: 320)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .contentShape(Rectangle())
                
                // Gradient overlay for text readability
                LinearGradient(
                    colors: [
                        .clear,
                        .clear,
                        CollectorTheme.cardBackground.opacity(0.7),
                        CollectorTheme.cardBackground.opacity(0.95)
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .frame(height: 120)
                .clipShape(
                    RoundedRectangle(cornerRadius: 16)
                        .offset(y: 60)
                )
                
                // Bottom content overlay
                VStack(alignment: .leading, spacing: 6) {
                    // Series • Year (year as plain digits, no comma)
                    if let year = figure.year {
                        Text("\(figure.line.rawValue) • \(String(year))")
                            .seriesLabelStyle()
                    } else {
                        Text(figure.line.rawValue)
                            .seriesLabelStyle()
                    }
                    
                    // Wave so you can tell figures apart
                    if let wave = figure.wave, !wave.isEmpty {
                        Text("Wave: \(wave)")
                            .font(.system(.caption, design: .default, weight: .medium))
                            .foregroundStyle(CollectorTheme.textSecondary.opacity(0.9))
                    }
                    
                    // Name (most descriptive title)
                    Text(figure.name)
                        .font(.system(.headline, design: .monospaced))
                        .fontWeight(.bold)
                        .lineLimit(2)
                        .foregroundStyle(CollectorTheme.textPrimary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 12)
                .padding(.bottom, 12)
                
                // Status indicator pill (top-left)
                VStack {
                    HStack {
                        CollectionStatusPill(status: figure.status)
                        Spacer()
                        if figure.isPlatinum {
                            PlatinumBadge()
                        }
                    }
                    Spacer()
                }
                .padding(10)
            }
        }
        .padding(10)
        .bentoCard()
        .overlay(
            ConfettiView(isShowing: showingConfetti)
        )
    }
}

// MARK: - Collection Status Pill

struct CollectionStatusPill: View {
    let status: CollectionStatus
    
    var body: some View {
        HStack(spacing: 6) {
            // Glowing dot
            Circle()
                .fill(status == .have ? CollectorTheme.statusHave : CollectorTheme.statusWant)
                .frame(width: 8, height: 8)
                .shadow(
                    color: status == .have ? CollectorTheme.statusHaveGlow.opacity(0.8) : CollectorTheme.statusWant.opacity(0.6),
                    radius: 4,
                    x: 0,
                    y: 0
                )
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(.ultraThinMaterial.opacity(0.8))
        .clipShape(Capsule())
        .overlay(
            Capsule()
                .stroke(
                    status == .have ? CollectorTheme.statusHave.opacity(0.3) : CollectorTheme.statusWant.opacity(0.3),
                    lineWidth: 1
                )
        )
    }
}

// MARK: - Status Badge (Legacy - kept for compatibility)

struct StatusBadge: View {
    let status: CollectionStatus
    
    var body: some View {
        CollectionStatusPill(status: status)
    }
}

// MARK: - Platinum Badge

struct PlatinumBadge: View {
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "sparkles")
                .font(.system(size: 8))
            Text("PLATINUM")
                .font(.system(size: 8, weight: .bold, design: .default))
                .tracking(0.5)
        }
        .foregroundStyle(CollectorTheme.accentPlatinum)
        .padding(.horizontal, 8)
        .padding(.vertical, 5)
        .background(
            LinearGradient(
                colors: [
                    Color(hex: "4A4A5A").opacity(0.9),
                    Color(hex: "3A3A4A").opacity(0.9)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .clipShape(Capsule())
        .overlay(
            Capsule()
                .stroke(
                    LinearGradient(
                        colors: [CollectorTheme.accentPlatinum.opacity(0.4), CollectorTheme.accentPlatinum.opacity(0.1)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 1
                )
        )
        .shadow(color: CollectorTheme.accentPlatinum.opacity(0.2), radius: 4, x: 0, y: 0)
    }
}

// MARK: - Figure Image

// MARK: - Figure Image (Upgraded for Web URLs with Premium Styling)

struct FigureImageView: View {
    let imageName: String
    @StateObject private var imageLoader = CachedImageLoader()
    
    var body: some View {
        // Check if it's a web URL or a local asset
        if imageName.hasPrefix("http"), let url = URL(string: imageName) {
            Group {
                if let image = imageLoader.image {
                    Image(uiImage: image)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(maxWidth: .infinity)
                        .frame(maxHeight: .infinity)
                } else if imageLoader.isLoading {
                    ZStack {
                        CollectorTheme.surfaceBackground
                        ProgressView()
                            .tint(CollectorTheme.textSecondary)
                    }
                } else {
                    placeholder
                }
            }
            .contentShape(Rectangle())
            .onAppear {
                imageLoader.load(url: url)
            }
            .onChange(of: imageName) { oldValue, newValue in
                // URL changed - reload with new URL
                if let newURL = URL(string: newValue), newValue.hasPrefix("http") {
                    imageLoader.reset()
                    imageLoader.load(url: newURL)
                }
            }
        } else {
            // Fallback for local assets (if you still have any)
            Image(imageName)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(maxWidth: .infinity)
                .frame(maxHeight: .infinity)
                .contentShape(Rectangle())
        }
    }
    
    // A simple placeholder if the image fails to load
    var placeholder: some View {
        ZStack {
            CollectorTheme.surfaceBackground
            VStack(spacing: 8) {
                Image(systemName: "photo")
                    .font(.largeTitle)
                    .foregroundStyle(CollectorTheme.textSecondary.opacity(0.5))
                Text("No Image")
                    .font(.caption)
                    .foregroundStyle(CollectorTheme.textSecondary.opacity(0.3))
            }
        }
        .contentShape(Rectangle())
    }
}

// MARK: - Cached Image Loader

class CachedImageLoader: ObservableObject {
    @Published var image: UIImage?
    @Published var isLoading = false
    
    private var currentURL: URL?
    
    func load(url: URL, forceRefresh: Bool = false) {
        // Don't reload if already loading this URL (unless forcing)
        if !forceRefresh && currentURL == url && image != nil {
            return
        }
        
        // If URL changed, reset state
        if currentURL != url {
            image = nil
        }
        
        currentURL = url
        isLoading = true
        
        Task {
            // If force refresh, invalidate the old cached image first
            if forceRefresh {
                ImageCache.shared.invalidate(url: url)
            }
            
            // Try to get from cache (or download and cache)
            let cachedImage = await ImageCache.shared.getImage(url: url)
            
            await MainActor.run {
                self.image = cachedImage
                self.isLoading = false
            }
        }
    }
    
    func reset() {
        image = nil
        currentURL = nil
        isLoading = false
    }
}

#Preview {
    FigureGridView()
        .environmentObject(FigureDataStore())
}
