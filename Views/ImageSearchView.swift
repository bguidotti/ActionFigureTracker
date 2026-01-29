//
//  ImageSearchView.swift
//  ActionFigureTracker
//
//  Image picker with search from multiple sources - like Plex Posters
//

import SwiftUI
import UIKit

// MARK: - API Response Models

struct ImageSearchResponse: Codable {
    let query: String
    let count: Int
    let results: [ImageResult]
}

struct ImageResult: Codable, Identifiable {
    var id: String { url }
    let url: String
    let title: String
    let source: String
    let source_icon: String
    
    var sourceColor: Color {
        switch source {
        case "ActionFigure411": return .orange
        case "LegendsVerse": return .blue
        case "McFarlane": return .green
        case "Google": return .red
        default: return .gray
        }
    }
}

// MARK: - Image Search View

struct ImageSearchView: View {
    @EnvironmentObject var dataStore: FigureDataStore
    @Environment(\.dismiss) var dismiss
    
    let figure: ActionFigure
    
    // Configuration - Change this to your server's address
    private let apiBaseURL = "http://192.168.1.39:5050"  // Your local IP
    
    @State private var searchQuery: String = ""
    @State private var searchResults: [ImageResult] = []
    @State private var isSearching: Bool = false
    @State private var errorMessage: String?
    @State private var selectedImage: ImageResult?
    
    // Source filters
    @State private var enabledSources: Set<String> = ["ActionFigure411", "Google"]
    
    // Manual URL fallback
    @State private var showManualEntry: Bool = false
    @State private var manualURL: String = ""
    
    var body: some View {
        NavigationStack {
            ZStack {
                CollectorTheme.background.ignoresSafeArea()
                
                VStack(spacing: 0) {
                    // Search Header
                    searchHeader
                    
                    // Source Filters
                    sourceFilters
                    
                    // Results or States
                    if isSearching {
                        loadingView
                    } else if let error = errorMessage {
                        errorView(message: error)
                    } else if searchResults.isEmpty {
                        emptyStateView
                    } else {
                        resultsGrid
                    }
                }
            }
            .navigationTitle("Find Image")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .foregroundStyle(CollectorTheme.textSecondary)
                }
                
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        showManualEntry.toggle()
                    } label: {
                        Image(systemName: "link.badge.plus")
                            .foregroundStyle(CollectorTheme.accentGold)
                    }
                }
            }
            // Use .sheet(item:) for reliable data binding to sheet
            .sheet(item: $selectedImage) { selected in
                ImagePreviewSheet(
                    imageResult: selected,
                    onConfirm: {
                        saveImage(url: selected.url)
                    },
                    onCancel: {
                        selectedImage = nil
                    }
                )
                .id(selected.id) // Force fresh view for each image
            }
            .sheet(isPresented: $showManualEntry) {
                ManualURLSheet(
                    figure: figure,
                    apiBaseURL: apiBaseURL,
                    onSave: { url in
                        saveImage(url: url)
                    }
                )
                .environmentObject(dataStore)
            }
            .onAppear {
                // Pre-fill search with figure name + line context for better matching
                var query = figure.name
                    .replacingOccurrences(of: "(", with: "")
                    .replacingOccurrences(of: ")", with: "")
                    .trimmingCharacters(in: .whitespaces)
                
                // Add line-specific context to help distinguish results
                switch figure.line {
                case .dcMultiverse:
                    query += " Multiverse"
                case .dcPagePunchers:
                    query += " Page Punchers"
                case .dcSuperPowers:
                    query += " Super Powers"
                case .dcRetro:
                    query += " Retro"
                case .motuOrigins:
                    query += " Origins"
                case .motuMasterverse:
                    query += " Masterverse"
                default:
                    break
                }
                
                searchQuery = query
                
                // Automatically search on appear
                performSearch()
            }
        }
    }
    
    // MARK: - Search Header
    
    private var searchHeader: some View {
        VStack(spacing: 12) {
            // Figure info
            HStack(spacing: 12) {
                AsyncImage(url: URL(string: figure.imageName)) { phase in
                    if let image = phase.image {
                        image.resizable().aspectRatio(contentMode: .fill)
                    } else {
                        CollectorTheme.surfaceBackground
                    }
                }
                .frame(width: 50, height: 70)
                .clipShape(RoundedRectangle(cornerRadius: 8))
                
                VStack(alignment: .leading, spacing: 4) {
                    Text(figure.name)
                        .font(.system(.subheadline, design: .default, weight: .semibold))
                        .foregroundStyle(CollectorTheme.textPrimary)
                        .lineLimit(2)
                    
                    Text(figure.line.rawValue)
                        .font(.caption)
                        .foregroundStyle(CollectorTheme.textSecondary)
                    
                    if let wave = figure.wave, !wave.isEmpty {
                        Text("Wave: \(wave)")
                            .font(.caption2)
                            .foregroundStyle(CollectorTheme.textSecondary.opacity(0.9))
                    }
                }
                
                Spacer()
            }
            .padding(.horizontal)
            
            // Search field
            HStack(spacing: 12) {
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(CollectorTheme.textSecondary)
                    
                    TextField("Search for images...", text: $searchQuery)
                        .foregroundStyle(CollectorTheme.textPrimary)
                        .autocorrectionDisabled()
                        .textInputAutocapitalization(.never)
                        .onSubmit {
                            performSearch()
                        }
                    
                    if !searchQuery.isEmpty {
                        Button {
                            searchQuery = ""
                        } label: {
                            Image(systemName: "xmark.circle.fill")
                                .foregroundStyle(CollectorTheme.textSecondary)
                        }
                    }
                }
                .padding(12)
                .background(CollectorTheme.surfaceBackground)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                
                Button {
                    performSearch()
                } label: {
                    Image(systemName: "arrow.right.circle.fill")
                        .font(.title2)
                        .foregroundStyle(CollectorTheme.accentGold)
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 12)
        .background(CollectorTheme.cardBackground)
    }
    
    // MARK: - Source Filters
    
    private var sourceFilters: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(["ActionFigure411", "Google"], id: \.self) { source in
                    SourceFilterChip(
                        name: source,
                        isEnabled: enabledSources.contains(source),
                        color: colorForSource(source)
                    ) {
                        if enabledSources.contains(source) {
                            enabledSources.remove(source)
                        } else {
                            enabledSources.insert(source)
                        }
                    }
                }
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
        }
        .background(CollectorTheme.cardBackground.opacity(0.5))
    }
    
    // MARK: - Results Grid
    
    private var resultsGrid: some View {
        ScrollView {
            LazyVGrid(columns: [
                GridItem(.flexible(), spacing: 12),
                GridItem(.flexible(), spacing: 12),
                GridItem(.flexible(), spacing: 12)
            ], spacing: 12) {
                ForEach(searchResults) { result in
                    ImageResultCard(result: result) {
                        selectedImage = result
                    }
                }
            }
            .padding()
        }
    }
    
    // MARK: - State Views
    
    private var loadingView: some View {
        VStack(spacing: 16) {
            Spacer()
            ProgressView()
                .scaleEffect(1.5)
                .tint(CollectorTheme.accentGold)
            Text("Searching...")
                .font(.subheadline)
                .foregroundStyle(CollectorTheme.textSecondary)
            Spacer()
        }
    }
    
    private func errorView(message: String) -> some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 48))
                .foregroundStyle(.orange)
            
            Text("Search Error")
                .font(.headline)
                .foregroundStyle(CollectorTheme.textPrimary)
            
            Text(message)
                .font(.subheadline)
                .foregroundStyle(CollectorTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            
            Button("Try Again") {
                performSearch()
            }
            .buttonStyle(.bordered)
            .tint(CollectorTheme.accentGold)
            
            Spacer()
        }
    }
    
    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Spacer()
            Image(systemName: "photo.on.rectangle.angled")
                .font(.system(size: 48))
                .foregroundStyle(CollectorTheme.textSecondary.opacity(0.5))
            
            Text("Search for Images")
                .font(.headline)
                .foregroundStyle(CollectorTheme.textPrimary)
            
            Text("Enter a search term and tap the arrow to find images from action figure websites")
                .font(.subheadline)
                .foregroundStyle(CollectorTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            
            // Quick search button
            Button {
                performSearch()
            } label: {
                HStack {
                    Image(systemName: "magnifyingglass")
                    Text("Search \"\(figure.name.prefix(20))...\"")
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .background(CollectorTheme.accentGold.opacity(0.2))
                .foregroundStyle(CollectorTheme.accentGold)
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            
            Spacer()
        }
    }
    
    // MARK: - Helpers
    
    private func colorForSource(_ source: String) -> Color {
        switch source {
        case "ActionFigure411": return .orange
        case "LegendsVerse": return .blue
        case "McFarlane": return .green
        case "Google": return .red
        default: return .gray
        }
    }
    
    private func performSearch() {
        guard !searchQuery.isEmpty else { return }
        
        isSearching = true
        errorMessage = nil
        searchResults = []
        
        // Build sources parameter
        let sources = enabledSources.map { $0.lowercased().replacingOccurrences(of: " ", with: "") }.joined(separator: ",")
        
        // Include the figure's line for better matching
        let lineParam = figure.line.rawValue.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
        
        guard let encodedQuery = searchQuery.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed),
              let url = URL(string: "\(apiBaseURL)/api/search?q=\(encodedQuery)&sources=\(sources)&line=\(lineParam)") else {
            errorMessage = "Invalid search query"
            isSearching = false
            return
        }
        
        Task {
            do {
                let (data, response) = try await URLSession.shared.data(from: url)
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    throw URLError(.badServerResponse)
                }
                
                if httpResponse.statusCode == 200 {
                    let searchResponse = try JSONDecoder().decode(ImageSearchResponse.self, from: data)
                    
                    await MainActor.run {
                        searchResults = searchResponse.results
                        isSearching = false
                    }
                } else {
                    throw URLError(.badServerResponse)
                }
            } catch {
                await MainActor.run {
                    if (error as NSError).domain == NSURLErrorDomain && (error as NSError).code == -1004 {
                        errorMessage = "Cannot connect to image server.\n\nMake sure the ImageServer is running:\ncd ImageServer && python app.py"
                    } else {
                        errorMessage = "Failed to search: \(error.localizedDescription)"
                    }
                    isSearching = false
                }
            }
        }
    }
    
    private func saveImage(url: String) {
        // Invalidate old cached image
        if let oldURL = URL(string: figure.imageName) {
            ImageCache.shared.invalidate(url: oldURL)
        }
        
        dataStore.updateImage(for: figure, imageURL: url)
        dismiss()
    }
}

// MARK: - Source Filter Chip

struct SourceFilterChip: View {
    let name: String
    let isEnabled: Bool
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 6) {
                Circle()
                    .fill(isEnabled ? color : CollectorTheme.textSecondary.opacity(0.3))
                    .frame(width: 8, height: 8)
                
                Text(name)
                    .font(.system(.caption, design: .default, weight: .medium))
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(isEnabled ? color.opacity(0.15) : CollectorTheme.surfaceBackground)
            .foregroundStyle(isEnabled ? color : CollectorTheme.textSecondary)
            .clipShape(Capsule())
            .overlay(
                Capsule()
                    .stroke(isEnabled ? color.opacity(0.3) : CollectorTheme.cardStrokeColor, lineWidth: 1)
            )
        }
    }
}

// MARK: - Image Result Card

struct ImageResultCard: View {
    let result: ImageResult
    let onSelect: () -> Void
    
    @State private var isLoaded = false
    
    var body: some View {
        Button(action: onSelect) {
            VStack(spacing: 0) {
                // Image
                AsyncImage(url: URL(string: result.url)) { phase in
                    switch phase {
                    case .success(let image):
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                            .onAppear { isLoaded = true }
                    case .failure:
                        ZStack {
                            CollectorTheme.surfaceBackground
                            Image(systemName: "photo.badge.exclamationmark")
                                .font(.title2)
                                .foregroundStyle(CollectorTheme.textSecondary.opacity(0.5))
                        }
                    case .empty:
                        ZStack {
                            CollectorTheme.surfaceBackground
                            ProgressView()
                                .tint(CollectorTheme.textSecondary)
                        }
                    @unknown default:
                        CollectorTheme.surfaceBackground
                    }
                }
                .frame(height: 140)
                .clipped()
                
                // Source badge
                HStack {
                    Circle()
                        .fill(result.sourceColor)
                        .frame(width: 6, height: 6)
                    
                    Text(result.source)
                        .font(.system(size: 10, weight: .medium))
                        .foregroundStyle(CollectorTheme.textSecondary)
                    
                    Spacer()
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 6)
                .background(CollectorTheme.cardBackground)
            }
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(CollectorTheme.cardStrokeColor, lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Image Preview Sheet

struct ImagePreviewSheet: View {
    let imageResult: ImageResult
    let onConfirm: () -> Void
    let onCancel: () -> Void
    
    // Use @State with .task modifier - Apple's recommended pattern for async work
    @State private var loadedImage: UIImage?
    @State private var isLoading = true
    @State private var errorMessage: String?
    @State private var retryCount = 0
    
    var body: some View {
        NavigationStack {
            ZStack {
                CollectorTheme.background.ignoresSafeArea()
                
                VStack(spacing: 20) {
                    // Large preview
                    Group {
                        if let uiImage = loadedImage {
                            Image(uiImage: uiImage)
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                        } else if isLoading {
                            VStack(spacing: 12) {
                                ProgressView()
                                    .scaleEffect(1.5)
                                Text("Loading image...")
                                    .font(.caption)
                                    .foregroundStyle(CollectorTheme.textSecondary)
                            }
                        } else if let error = errorMessage {
                            VStack(spacing: 12) {
                                Image(systemName: "exclamationmark.triangle")
                                    .font(.largeTitle)
                                    .foregroundStyle(.red)
                                Text("Failed to load")
                                    .foregroundStyle(CollectorTheme.textSecondary)
                                Text(error)
                                    .font(.caption2)
                                    .foregroundStyle(CollectorTheme.textSecondary.opacity(0.7))
                                
                                Button("Retry") {
                                    retryCount += 1
                                }
                                .buttonStyle(.bordered)
                                .tint(CollectorTheme.accentGold)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .frame(minHeight: 350)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .padding(.horizontal)
                    
                    // Info
                    VStack(spacing: 8) {
                        HStack {
                            Circle()
                                .fill(imageResult.sourceColor)
                                .frame(width: 10, height: 10)
                            Text("From \(imageResult.source)")
                                .font(.subheadline)
                                .foregroundStyle(CollectorTheme.textSecondary)
                        }
                        
                        Text(imageResult.title)
                            .font(.caption)
                            .foregroundStyle(CollectorTheme.textSecondary.opacity(0.7))
                            .lineLimit(2)
                            .multilineTextAlignment(.center)
                    }
                    
                    Spacer()
                    
                    // Buttons
                    VStack(spacing: 12) {
                        Button(action: onConfirm) {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                Text("Use This Image")
                            }
                            .font(.headline)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .foregroundStyle(.white)
                            .background(CollectorTheme.statusHave)
                            .clipShape(RoundedRectangle(cornerRadius: 14))
                        }
                        .disabled(loadedImage == nil)
                        .opacity(loadedImage == nil ? 0.5 : 1)
                        
                        Button(action: onCancel) {
                            Text("Choose Different Image")
                                .font(.subheadline)
                                .foregroundStyle(CollectorTheme.textSecondary)
                        }
                    }
                    .padding(.horizontal)
                    .padding(.bottom)
                }
            }
            .navigationTitle("Preview")
            .navigationBarTitleDisplayMode(.inline)
            // Use .task - Apple's recommended async pattern for SwiftUI
            // It automatically starts when view appears and cancels on disappear
            .task(id: retryCount) {
                await loadImage()
            }
        }
    }
    
    /// Load image using URLSession - follows Apple's async/await best practices
    private func loadImage() async {
        let urlString = imageResult.url
        print("🖼️ [ImagePreview] Starting load for: \(urlString)")
        
        guard let url = URL(string: urlString) else {
            print("🖼️ [ImagePreview] ERROR: Invalid URL")
            errorMessage = "Invalid URL"
            isLoading = false
            return
        }
        
        isLoading = true
        errorMessage = nil
        loadedImage = nil
        
        do {
            var request = URLRequest(url: url)
            request.setValue("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", forHTTPHeaderField: "User-Agent")
            request.setValue("image/webp,image/apng,image/*,*/*;q=0.8", forHTTPHeaderField: "Accept")
            request.setValue("en-US,en;q=0.9", forHTTPHeaderField: "Accept-Language")
            request.cachePolicy = .reloadIgnoringLocalCacheData
            request.timeoutInterval = 30
            
            print("🖼️ [ImagePreview] Sending request...")
            let (data, response) = try await URLSession.shared.data(for: request)
            print("🖼️ [ImagePreview] Got response, data size: \(data.count) bytes")
            
            // Check for cancellation
            try Task.checkCancellation()
            
            if let httpResponse = response as? HTTPURLResponse {
                print("🖼️ [ImagePreview] HTTP status: \(httpResponse.statusCode)")
                guard httpResponse.statusCode == 200 else {
                    errorMessage = "HTTP \(httpResponse.statusCode)"
                    isLoading = false
                    return
                }
            }
            
            guard let rawImage = UIImage(data: data) else {
                print("🖼️ [ImagePreview] ERROR: Could not create UIImage from data")
                errorMessage = "Invalid image data"
                isLoading = false
                return
            }
            
            print("🖼️ [ImagePreview] Created UIImage: \(rawImage.size)")
            
            // Prepare for display off main thread (Apple recommended)
            let displayImage = await rawImage.byPreparingForDisplay()
            
            try Task.checkCancellation()
            
            loadedImage = displayImage ?? rawImage
            isLoading = false
            print("🖼️ [ImagePreview] SUCCESS - Image loaded!")
            
        } catch is CancellationError {
            print("🖼️ [ImagePreview] Task was cancelled")
        } catch {
            print("🖼️ [ImagePreview] ERROR: \(error)")
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }
}

// MARK: - Manual URL Sheet

struct McFarlaneProductResponse: Codable {
    let title: String
    let images: [String]
}

struct ManualURLSheet: View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var dataStore: FigureDataStore
    
    let figure: ActionFigure
    let apiBaseURL: String
    let onSave: (String) -> Void
    
    @State private var urlText: String = ""
    @State private var showPreview: Bool = false
    
    @State private var mcfarlaneImages: [String] = []
    @State private var mcfarlaneLoading: Bool = false
    @State private var mcfarlaneError: String?
    @State private var mcfarlaneTitle: String = ""
    
    private var isMcFarlaneProductURL: Bool {
        urlText.contains("mcfarlane.com/toys/")
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                CollectorTheme.background.ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 20) {
                        // Instructions
                        VStack(alignment: .leading, spacing: 8) {
                            Text("PASTE IMAGE OR PRODUCT URL")
                                .font(.caption)
                                .fontWeight(.semibold)
                                .foregroundStyle(CollectorTheme.textSecondary)
                            
                            Text("Paste a direct image URL, or a McFarlane product page (e.g. mcfarlane.com/toys/...) to pull images from the page")
                                .font(.caption)
                                .foregroundStyle(CollectorTheme.textSecondary.opacity(0.7))
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal)
                        
                        // URL Input
                        HStack {
                            TextField("https://...", text: $urlText)
                                .font(.system(.body, design: .monospaced))
                                .foregroundStyle(CollectorTheme.textPrimary)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                            
                            Button {
                                if let clipboard = UIPasteboard.general.string {
                                    urlText = clipboard
                                }
                            } label: {
                                Image(systemName: "doc.on.clipboard")
                                    .foregroundStyle(CollectorTheme.accentGold)
                            }
                        }
                        .padding()
                        .background(CollectorTheme.surfaceBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .padding(.horizontal)
                        
                        // McFarlane product: "Get images from this page"
                        if isMcFarlaneProductURL && mcfarlaneImages.isEmpty && !mcfarlaneLoading {
                            Button {
                                fetchMcFarlaneProductImages()
                            } label: {
                                HStack {
                                    Image(systemName: "photo.stack")
                                    Text("Get images from this McFarlane page")
                                }
                                .font(.subheadline.weight(.medium))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 14)
                                .foregroundStyle(.green)
                                .background(Color.green.opacity(0.15))
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                            }
                            .padding(.horizontal)
                        }
                        
                        if mcfarlaneLoading {
                            HStack(spacing: 8) {
                                ProgressView()
                                    .scaleEffect(0.9)
                                Text("Loading images from McFarlane...")
                                    .font(.caption)
                                    .foregroundStyle(CollectorTheme.textSecondary)
                            }
                            .padding()
                        }
                        
                        if let err = mcfarlaneError {
                            Text(err)
                                .font(.caption)
                                .foregroundStyle(.red)
                                .padding(.horizontal)
                        }
                        
                        // McFarlane images grid
                        if !mcfarlaneImages.isEmpty {
                            VStack(alignment: .leading, spacing: 8) {
                                if !mcfarlaneTitle.isEmpty {
                                    Text(mcfarlaneTitle)
                                        .font(.caption)
                                        .fontWeight(.medium)
                                        .foregroundStyle(CollectorTheme.textSecondary)
                                        .lineLimit(2)
                                }
                                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                                    ForEach(mcfarlaneImages, id: \.self) { imageURL in
                                        Button {
                                            onSave(imageURL)
                                            dismiss()
                                        } label: {
                                            AsyncImage(url: URL(string: imageURL)) { phase in
                                                if let image = phase.image {
                                                    image
                                                        .resizable()
                                                        .aspectRatio(contentMode: .fill)
                                                } else {
                                                    CollectorTheme.surfaceBackground
                                                }
                                            }
                                            .frame(height: 120)
                                            .clipShape(RoundedRectangle(cornerRadius: 8))
                                        }
                                        .buttonStyle(.plain)
                                    }
                                }
                            }
                            .padding(.horizontal)
                        }
                        
                        // Preview (direct image URL)
                        if showPreview && !urlText.isEmpty && mcfarlaneImages.isEmpty {
                        AsyncImage(url: URL(string: urlText)) { phase in
                            if let image = phase.image {
                                image
                                    .resizable()
                                    .aspectRatio(contentMode: .fit)
                            } else if phase.error != nil {
                                VStack {
                                    Image(systemName: "exclamationmark.triangle")
                                        .font(.largeTitle)
                                        .foregroundStyle(.red)
                                    Text("Failed to load")
                                        .font(.caption)
                                        .foregroundStyle(CollectorTheme.textSecondary)
                                }
                            } else {
                                ProgressView()
                            }
                        }
                        .frame(height: 250)
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                        .padding(.horizontal)
                    }
                    
                            // Buttons (direct image URL)
                            if !mcfarlaneImages.isEmpty {
                                Text("Tap an image above to use it")
                                    .font(.caption)
                                    .foregroundStyle(CollectorTheme.textSecondary)
                            } else {
                                VStack(spacing: 12) {
                                    if !showPreview {
                                        Button {
                                            showPreview = true
                                        } label: {
                                            HStack {
                                                Image(systemName: "eye")
                                                Text("Preview")
                                            }
                                            .frame(maxWidth: .infinity)
                                            .padding(.vertical, 14)
                                            .background(CollectorTheme.surfaceBackground)
                                            .foregroundStyle(CollectorTheme.textPrimary)
                                            .clipShape(RoundedRectangle(cornerRadius: 12))
                                        }
                                        .disabled(urlText.isEmpty)
                                    } else {
                                        Button {
                                            onSave(urlText)
                                            dismiss()
                                        } label: {
                                            HStack {
                                                Image(systemName: "checkmark.circle.fill")
                                                Text("Use This Image")
                                            }
                                            .font(.headline)
                                            .frame(maxWidth: .infinity)
                                            .padding(.vertical, 16)
                                            .foregroundStyle(.white)
                                            .background(CollectorTheme.statusHave)
                                            .clipShape(RoundedRectangle(cornerRadius: 14))
                                        }
                                    }
                                }
                                .padding(.horizontal)
                            }
                            
                            Spacer(minLength: 24)
                            
                            // Quick links
                            VStack(alignment: .leading, spacing: 8) {
                                Text("OPEN IN SAFARI")
                                    .font(.caption)
                                    .fontWeight(.semibold)
                                    .foregroundStyle(CollectorTheme.textSecondary)
                                
                                HStack(spacing: 12) {
                                    QuickLinkButton(name: "AF411", color: .orange) {
                                        openURL("https://www.actionfigure411.com/?s=\(figure.name.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")")
                                    }
                                    QuickLinkButton(name: "McF", color: .green) {
                                        openURL("https://mcfarlane.com/search/?q=\(figure.name.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")")
                                    }
                                    QuickLinkButton(name: "Google", color: .red) {
                                        openURL("https://www.google.com/search?tbm=isch&q=\(figure.name.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")+action+figure")
                                    }
                                }
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding()
                            .background(CollectorTheme.cardBackground)
                        .padding(.top)
                    }
                }
            }
            }
            .navigationTitle("Manual Entry")
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
    
    private func fetchMcFarlaneProductImages() {
        guard let base = URL(string: apiBaseURL),
              var components = URLComponents(url: base.appendingPathComponent("api/mcfarlane-product"), resolvingAgainstBaseURL: false) else {
            mcfarlaneError = "Invalid URL"
            return
        }
        components.queryItems = [URLQueryItem(name: "url", value: urlText)]
        guard let url = components.url else {
            mcfarlaneError = "Invalid URL"
            return
        }
        mcfarlaneLoading = true
        mcfarlaneError = nil
        mcfarlaneImages = []
        mcfarlaneTitle = ""
        
        Task {
            do {
                let (data, response) = try await URLSession.shared.data(from: url)
                guard let http = response as? HTTPURLResponse else { return }
                await MainActor.run {
                    mcfarlaneLoading = false
                    if http.statusCode == 200 {
                        if let decoded = try? JSONDecoder().decode(McFarlaneProductResponse.self, from: data) {
                            mcfarlaneTitle = decoded.title
                            mcfarlaneImages = decoded.images
                            if decoded.images.isEmpty {
                                mcfarlaneError = "No images found on this page. The carousel may load via JavaScript."
                            }
                        } else {
                            mcfarlaneError = "Could not read response"
                        }
                    } else {
                        mcfarlaneError = "Server returned \(http.statusCode)"
                    }
                }
            } catch {
                await MainActor.run {
                    mcfarlaneLoading = false
                    if (error as NSError).code == -1004 {
                        mcfarlaneError = "Cannot connect to image server. Is it running?"
                    } else {
                        mcfarlaneError = error.localizedDescription
                    }
                }
            }
        }
    }
    
    private func openURL(_ urlString: String) {
        if let url = URL(string: urlString) {
            UIApplication.shared.open(url)
        }
    }
}

struct QuickLinkButton: View {
    let name: String
    let color: Color
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Text(name)
                .font(.caption)
                .fontWeight(.medium)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(color.opacity(0.15))
                .foregroundStyle(color)
                .clipShape(Capsule())
        }
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
