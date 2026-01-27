//
//  FigureGridView.swift
//  ActionFigureTracker
//
//  Grid view showing all figures with filtering
//

import SwiftUI

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
            return figures.sorted { $0.dateAdded < $1.dateAdded }
        case .oldestFirst:
            return figures.sorted { $0.dateAdded > $1.dateAdded }
        case .alphabetical:
            return figures.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
        case .reverseAlphabetical:
            return figures.sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedDescending }
        }
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Line Picker - Big buttons for kids!
                LinePickerView(selectedLine: $selectedLine)
                    .padding(.horizontal)
                    .padding(.top, 8)
                
                // Figure Grid
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVGrid(columns: columns, spacing: 20) {
                            ForEach(filteredFigures) { figure in
                                NavigationLink(destination: FigureDetailView(figure: figure)) {
                                    FigureCardView(figure: figure)
                                }
                                .buttonStyle(.plain)
                                .id(figure.id)
                            }
                        }
                        .padding()
                        .id("top") // Add ID to top of content for scrolling
                    }
                    .onChange(of: selectedLine) { _, _ in
                        // Reset scroll to top when category changes
                        withAnimation {
                            proxy.scrollTo("top", anchor: .top)
                        }
                    }
                }
            }
            .navigationTitle("My Action Figures! 🦸")
            .searchable(text: $searchText, prompt: "Find a figure...")
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
                                .foregroundStyle(.purple)
                        }
                        
                        // Add button
                        NavigationLink(destination: AddFigureView()) {
                            Image(systemName: "plus.circle.fill")
                                .font(.title2)
                                .foregroundStyle(.purple)
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
            HStack(spacing: 12) {
                // All button
                LineButton(
                    title: "All",
                    emoji: "🌟",
                    isSelected: selectedLine == nil,
                    color: .purple
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
        case .starWarsBlackSeries: return Color(red: 0.2, green: 0.2, blue: 0.3) // Dark blue-gray instead of black
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
                    .font(.title)
                Text(title)
                    .font(.caption)
                    .fontWeight(.bold)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
            }
            .frame(minWidth: 80)
            .padding(.vertical, 8)
            .padding(.horizontal, 12)
            .background(isSelected ? color : color.opacity(0.2))
            .foregroundStyle(isSelected ? .white : color)
            .clipShape(RoundedRectangle(cornerRadius: 16))
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .stroke(color, lineWidth: 2)
            )
        }
        .scaleEffect(isSelected ? 1.05 : 1.0)
        .animation(.spring(response: 0.3), value: isSelected)
    }
}

// MARK: - Figure Card

struct FigureCardView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    let figure: ActionFigure
    @State private var showingConfetti = false
    
    var body: some View {
        VStack(spacing: 8) {
            // Figure Image - Larger for better visibility
            ZStack(alignment: .topTrailing) {
                // Background to help images stand out
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color.gray.opacity(0.1))
                    .frame(height: 280)
                
                FigureImageView(imageName: figure.imageName)
                    .frame(height: 280)
                    .frame(maxWidth: .infinity)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                
                // Badges overlay
                VStack(alignment: .trailing, spacing: 4) {
                    // Platinum badge
                    if figure.isPlatinum {
                        PlatinumBadge()
                    }
                    // Status Badge
                    StatusBadge(status: figure.status)
                }
                .padding(8)
            }
            
            // Name
            Text(figure.name)
                .font(.headline)
                .fontWeight(.bold)
                .lineLimit(2)
                .multilineTextAlignment(.center)
                .foregroundStyle(.primary)
            
            // Quick toggle button
            Button(action: {
                withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                    if figure.status == .want {
                        showingConfetti = true
                        // Hide confetti after delay
                        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                            showingConfetti = false
                        }
                    }
                    dataStore.toggleStatus(for: figure)
                }
            }) {
                HStack {
                    Image(systemName: figure.status == .have ? "checkmark.circle.fill" : "star.fill")
                    Text(figure.status == .have ? "Got It!" : "Want It!")
                        .fontWeight(.bold)
                }
                .font(.subheadline)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(figure.status == .have ? Color.green : Color.orange)
                .foregroundStyle(.white)
                .clipShape(Capsule())
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 4)
        .overlay(
            // Confetti overlay
            ConfettiView(isShowing: showingConfetti)
        )
    }
}

// MARK: - Status Badge

struct StatusBadge: View {
    let status: CollectionStatus
    
    var body: some View {
        Text(status.emoji)
            .font(.title)
            .padding(8)
            .background(.ultraThinMaterial)
            .clipShape(Circle())
    }
}

// MARK: - Platinum Badge

struct PlatinumBadge: View {
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "sparkles")
                .font(.caption)
            Text("PLATINUM")
                .font(.system(size: 8, weight: .bold))
        }
        .foregroundStyle(.white)
        .padding(.horizontal, 6)
        .padding(.vertical, 4)
        .background(
            LinearGradient(
                colors: [Color(red: 0.7, green: 0.7, blue: 0.9), Color(red: 0.5, green: 0.5, blue: 0.7)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
        .clipShape(Capsule())
        .shadow(color: .black.opacity(0.3), radius: 2, x: 0, y: 1)
    }
}

// MARK: - Figure Image

// MARK: - Figure Image (Upgraded for Web URLs)

struct FigureImageView: View {
    let imageName: String
    
    var body: some View {
        // Check if it's a web URL or a local asset
        if imageName.hasPrefix("http") {
            AsyncImage(url: URL(string: imageName)) { phase in
                switch phase {
                case .empty:
                    ZStack {
                        Color.gray.opacity(0.1)
                        ProgressView() // Spinner while loading
                    }
                case .success(let image):
                    image
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                        .clipped()
                case .failure:
                    placeholder
                @unknown default:
                    placeholder
                }
            }
        } else {
            // Fallback for local assets (if you still have any)
            Image(imageName)
                .resizable()
                .aspectRatio(contentMode: .fill)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .clipped()
        }
    }
    
    // A simple placeholder if the image fails to load
    var placeholder: some View {
        ZStack {
            Color.gray.opacity(0.1)
            Image(systemName: "photo")
                .font(.largeTitle)
                .foregroundStyle(.gray.opacity(0.5))
        }
    }
}

#Preview {
    FigureGridView()
        .environmentObject(FigureDataStore())
}
