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
    
    private let columns = [
        GridItem(.flexible(), spacing: 16),
        GridItem(.flexible(), spacing: 16)
    ]
    
    var filteredFigures: [ActionFigure] {
        var result = dataStore.figures(for: selectedLine, status: nil)
        
        if !searchText.isEmpty {
            result = result.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }
        
        return result
    }
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Line Picker - Big buttons for kids!
                LinePickerView(selectedLine: $selectedLine)
                    .padding(.horizontal)
                    .padding(.top, 8)
                
                // Figure Grid
                ScrollView {
                    LazyVGrid(columns: columns, spacing: 20) {
                        ForEach(filteredFigures) { figure in
                            NavigationLink(destination: FigureDetailView(figure: figure)) {
                                FigureCardView(figure: figure)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding()
                }
            }
            .navigationTitle("My Action Figures! 🦸")
            .searchable(text: $searchText, prompt: "Find a figure...")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
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
        case .starWarsBlackSeries: return .black
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
            // Figure Image
            ZStack(alignment: .topTrailing) {
                FigureImageView(imageName: figure.imageName)
                    .frame(height: 180)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                
                // Status Badge
                StatusBadge(status: figure.status)
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

// MARK: - Figure Image

// MARK: - Figure Image (Upgraded for Web URLs)

struct FigureImageView: View {
    let imageName: String
    
    var body: some View {
        Group {
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
                            .aspectRatio(contentMode: .fit)
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
                    .aspectRatio(contentMode: .fit)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(
            // Placeholder gradient
            LinearGradient(
                colors: [.purple.opacity(0.3), .blue.opacity(0.3)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
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
