//
//  ImageSearchView.swift
//  ActionFigureTracker
//
//  Image picker with multiple source options - like Plex Posters
//

import SwiftUI

struct ImageSearchView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    @Environment(\.dismiss) var dismiss
    
    let figure: ActionFigure
    
    @State private var imageURL: String = ""
    @State private var isValidURL: Bool = false
    @State private var showingPreview: Bool = false
    @State private var previewImageURL: String = ""
    @State private var searchResults: [ImageResult] = []
    @State private var isSearching: Bool = false
    @State private var selectedSource: ImageSource = .actionfigure411
    @State private var errorMessage: String?
    
    enum ImageSource: String, CaseIterable {
        case actionfigure411 = "ActionFigure411"
        case legendsverse = "LegendsVerse"
        case mcfarlane = "McFarlane"
        case google = "Google Images"
        
        var icon: String {
            switch self {
            case .actionfigure411: return "star.fill"
            case .legendsverse: return "globe"
            case .mcfarlane: return "building.2"
            case .google: return "magnifyingglass"
            }
        }
        
        var color: Color {
            switch self {
            case .actionfigure411: return .orange
            case .legendsverse: return .blue
            case .mcfarlane: return .green
            case .google: return .red
            }
        }
        
        func searchURL(for figureName: String) -> URL? {
            let encoded = figureName.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? figureName
            switch self {
            case .actionfigure411:
                return URL(string: "https://www.actionfigure411.com/?s=\(encoded)")
            case .legendsverse:
                return URL(string: "https://legendsverse.com/?s=\(encoded)")
            case .mcfarlane:
                return URL(string: "https://mcfarlane.com/search/?q=\(encoded)")
            case .google:
                return URL(string: "https://www.google.com/search?tbm=isch&q=\(encoded)+action+figure")
            }
        }
    }
    
    struct ImageResult: Identifiable {
        let id = UUID()
        let url: String
        let source: ImageSource
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                CollectorTheme.background.ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 24) {
                        // Current Image Section
                        currentImageSection
                        
                        // Quick Search Sources
                        quickSearchSection
                        
                        // Manual URL Entry
                        manualURLSection
                        
                        // Preview Section
                        if showingPreview {
                            previewSection
                        }
                        
                        Spacer(minLength: 50)
                    }
                    .padding()
                }
            }
            .navigationTitle("Change Image")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .foregroundStyle(CollectorTheme.textSecondary)
                }
            }
        }
    }
    
    // MARK: - Current Image Section
    
    private var currentImageSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader(title: "CURRENT IMAGE", icon: "photo")
            
            HStack(spacing: 16) {
                // Thumbnail of current image
                AsyncImage(url: URL(string: figure.imageName)) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    case .failure:
                        placeholderImage
                    case .empty:
                        ProgressView()
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    @unknown default:
                        placeholderImage
                    }
                }
                .frame(width: 100, height: 140)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                )
                
                VStack(alignment: .leading, spacing: 8) {
                    Text(figure.name)
                        .font(.system(.headline, design: .default, weight: .semibold))
                        .foregroundStyle(CollectorTheme.textPrimary)
                        .lineLimit(3)
                    
                    Text(figure.line.rawValue)
                        .font(.system(.caption, design: .default, weight: .medium))
                        .foregroundStyle(CollectorTheme.textSecondary)
                    
                    if !figure.imageName.isEmpty {
                        Text("Has image")
                            .font(.caption2)
                            .foregroundStyle(CollectorTheme.statusHave)
                    } else {
                        Text("No image")
                            .font(.caption2)
                            .foregroundStyle(CollectorTheme.statusWant)
                    }
                }
                
                Spacer()
            }
            .padding()
            .background(CollectorTheme.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius)
                    .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
            )
        }
    }
    
    // MARK: - Quick Search Section
    
    private var quickSearchSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader(title: "SEARCH SOURCES", icon: "magnifyingglass")
            
            Text("Tap to open in Safari, then copy the image URL")
                .font(.caption)
                .foregroundStyle(CollectorTheme.textSecondary)
            
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                ForEach(ImageSource.allCases, id: \.self) { source in
                    Button {
                        openSearch(source: source)
                    } label: {
                        HStack(spacing: 8) {
                            Image(systemName: source.icon)
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundStyle(source.color)
                            
                            Text(source.rawValue)
                                .font(.system(.subheadline, design: .default, weight: .medium))
                                .foregroundStyle(CollectorTheme.textPrimary)
                            
                            Spacer()
                            
                            Image(systemName: "arrow.up.right")
                                .font(.caption)
                                .foregroundStyle(CollectorTheme.textSecondary)
                        }
                        .padding(.horizontal, 14)
                        .padding(.vertical, 12)
                        .background(CollectorTheme.surfaceBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(source.color.opacity(0.3), lineWidth: 1)
                        )
                    }
                }
            }
        }
    }
    
    // MARK: - Manual URL Section
    
    private var manualURLSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader(title: "PASTE IMAGE URL", icon: "link")
            
            HStack(spacing: 12) {
                TextField("https://...", text: $imageURL)
                    .font(.system(.body, design: .monospaced))
                    .foregroundStyle(CollectorTheme.textPrimary)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .padding(14)
                    .background(CollectorTheme.surfaceBackground)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
                    )
                    .onChange(of: imageURL) { _, newValue in
                        validateURL(newValue)
                    }
                
                // Paste button
                Button {
                    if let clipboardString = UIPasteboard.general.string {
                        imageURL = clipboardString
                        validateURL(clipboardString)
                    }
                } label: {
                    Image(systemName: "doc.on.clipboard")
                        .font(.title3)
                        .foregroundStyle(CollectorTheme.accentGold)
                        .padding(14)
                        .background(CollectorTheme.surfaceBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .overlay(
                            RoundedRectangle(cornerRadius: 12)
                                .stroke(CollectorTheme.accentGold.opacity(0.3), lineWidth: 1)
                        )
                }
            }
            
            // Preview Button
            if isValidURL {
                Button {
                    previewImageURL = imageURL
                    withAnimation(.spring(response: 0.3)) {
                        showingPreview = true
                    }
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "eye")
                        Text("Preview Image")
                    }
                    .font(.system(.subheadline, design: .default, weight: .semibold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .foregroundStyle(CollectorTheme.textPrimary)
                    .background(CollectorTheme.accentGold.opacity(0.2))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(CollectorTheme.accentGold.opacity(0.4), lineWidth: 1)
                    )
                }
            }
            
            if let error = errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
    }
    
    // MARK: - Preview Section
    
    private var previewSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            sectionHeader(title: "PREVIEW", icon: "photo.artframe")
            
            ZStack {
                AsyncImage(url: URL(string: previewImageURL)) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                    case .failure:
                        VStack(spacing: 8) {
                            Image(systemName: "exclamationmark.triangle")
                                .font(.largeTitle)
                                .foregroundStyle(.red)
                            Text("Failed to load image")
                                .font(.caption)
                                .foregroundStyle(CollectorTheme.textSecondary)
                        }
                    case .empty:
                        ProgressView()
                            .scaleEffect(1.5)
                    @unknown default:
                        placeholderImage
                    }
                }
                .frame(maxWidth: .infinity)
                .frame(minHeight: 300)
            }
            .clipShape(RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius))
            .overlay(
                RoundedRectangle(cornerRadius: CollectorTheme.cardCornerRadius)
                    .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
            )
            
            // Save Button
            Button {
                saveImage()
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "checkmark.circle.fill")
                    Text("Use This Image")
                }
                .font(.system(.headline, design: .default, weight: .semibold))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .foregroundStyle(.white)
                .background(CollectorTheme.statusHave)
                .clipShape(RoundedRectangle(cornerRadius: 14))
                .shadow(color: CollectorTheme.statusHave.opacity(0.4), radius: 8, x: 0, y: 4)
            }
        }
    }
    
    // MARK: - Helpers
    
    private var placeholderImage: some View {
        ZStack {
            CollectorTheme.surfaceBackground
            Image(systemName: "photo")
                .font(.largeTitle)
                .foregroundStyle(CollectorTheme.textSecondary.opacity(0.5))
        }
    }
    
    private func sectionHeader(title: String, icon: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 12, weight: .semibold))
                .foregroundStyle(CollectorTheme.accentGold)
            
            Text(title)
                .font(.system(.caption, design: .default, weight: .semibold))
                .textCase(.uppercase)
                .tracking(1)
                .foregroundStyle(CollectorTheme.textSecondary)
        }
    }
    
    private func openSearch(source: ImageSource) {
        if let url = source.searchURL(for: figure.name) {
            UIApplication.shared.open(url)
        }
    }
    
    private func validateURL(_ urlString: String) {
        errorMessage = nil
        
        guard !urlString.isEmpty else {
            isValidURL = false
            return
        }
        
        // Check if it's a valid URL
        guard let url = URL(string: urlString),
              let scheme = url.scheme,
              ["http", "https"].contains(scheme.lowercased()) else {
            isValidURL = false
            errorMessage = "Please enter a valid image URL starting with http:// or https://"
            return
        }
        
        // Check if it looks like an image URL
        let imageExtensions = ["jpg", "jpeg", "png", "gif", "webp"]
        let pathExtension = url.pathExtension.lowercased()
        
        // Either has image extension or we'll try to load it anyway
        isValidURL = true
        
        if !imageExtensions.contains(pathExtension) && !urlString.contains("image") {
            // Warning but still valid - some image URLs don't have extensions
            errorMessage = "URL may not be an image. Preview to verify."
        }
    }
    
    private func saveImage() {
        dataStore.updateImage(for: figure, imageURL: previewImageURL)
        dismiss()
    }
}

#Preview {
    ImageSearchView(figure: ActionFigure(
        name: "Batman (Detective Comics #1000)",
        line: .dcMultiverse,
        imageName: "https://www.actionfigure411.com/dc/images/batman-4950.jpg"
    ))
    .environmentObject(FigureDataStore())
}
