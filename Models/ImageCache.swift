//
//  ImageCache.swift
//  ActionFigureTracker
//
//  Caches images locally to avoid repeated web requests
//

import Foundation
import SwiftUI

class ImageCache: ObservableObject {
    static let shared = ImageCache()
    
    private let cacheDirectory: URL
    private let fileManager = FileManager.default
    
    // In-memory cache for quick access
    private var memoryCache: [String: UIImage] = [:]
    private let maxMemoryCacheSize = 50 // Max images in memory
    
    private init() {
        // Create cache directory in app's documents
        let documentsPath = fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
        cacheDirectory = documentsPath.appendingPathComponent("ImageCache", isDirectory: true)
        
        // Create directory if it doesn't exist
        if !fileManager.fileExists(atPath: cacheDirectory.path) {
            try? fileManager.createDirectory(at: cacheDirectory, withIntermediateDirectories: true)
        }
        
        // Clean up old cache on init (optional - can be removed if you want to keep all images)
        // cleanOldCache()
    }
    
    /// Get cached image URL or download and cache it
    func getImage(url: URL) async -> UIImage? {
        let cacheKey = url.absoluteString
        
        // Check memory cache first
        if let cachedImage = memoryCache[cacheKey] {
            return cachedImage
        }
        
        // Check disk cache
        if let cachedImage = loadFromDisk(key: cacheKey) {
            // Add to memory cache
            addToMemoryCache(key: cacheKey, image: cachedImage)
            return cachedImage
        }
        
        // Download and cache
        guard let downloadedImage = await downloadImage(from: url) else {
            return nil
        }
        
        // Save to disk and memory
        saveToDisk(key: cacheKey, image: downloadedImage)
        addToMemoryCache(key: cacheKey, image: downloadedImage)
        
        return downloadedImage
    }
    
    /// Load image from disk cache
    private func loadFromDisk(key: String) -> UIImage? {
        let fileName = sanitizeFileName(key)
        let fileURL = cacheDirectory.appendingPathComponent(fileName)
        
        guard fileManager.fileExists(atPath: fileURL.path),
              let data = try? Data(contentsOf: fileURL),
              let image = UIImage(data: data) else {
            return nil
        }
        
        return image
    }
    
    /// Save image to disk cache
    private func saveToDisk(key: String, image: UIImage) {
        let fileName = sanitizeFileName(key)
        let fileURL = cacheDirectory.appendingPathComponent(fileName)
        
        guard let data = image.jpegData(compressionQuality: 0.8) else {
            return
        }
        
        try? data.write(to: fileURL)
    }
    
    /// Download image from URL
    private func downloadImage(from url: URL) async -> UIImage? {
        do {
            let (data, _) = try await URLSession.shared.data(from: url)
            return UIImage(data: data)
        } catch {
            print("❌ Error downloading image: \(error.localizedDescription)")
            return nil
        }
    }
    
    /// Add to memory cache (with size limit)
    private func addToMemoryCache(key: String, image: UIImage) {
        // If cache is full, remove oldest entry
        if memoryCache.count >= maxMemoryCacheSize {
            if let firstKey = memoryCache.keys.first {
                memoryCache.removeValue(forKey: firstKey)
            }
        }
        memoryCache[key] = image
    }
    
    /// Sanitize URL to create valid filename
    private func sanitizeFileName(_ urlString: String) -> String {
        // Create a hash of the URL for the filename
        let hash = urlString.hash
        // Also include last path component for debugging
        let lastComponent = URL(string: urlString)?.lastPathComponent ?? "image"
        let sanitized = lastComponent.replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: ":", with: "_")
            .replacingOccurrences(of: "?", with: "_")
        
        return "\(abs(hash))_\(sanitized).jpg"
    }
    
    /// Clear all cached images (useful for debugging or if cache gets too large)
    func clearCache() {
        memoryCache.removeAll()
        try? fileManager.removeItem(at: cacheDirectory)
        try? fileManager.createDirectory(at: cacheDirectory, withIntermediateDirectories: true)
    }
    
    /// Get cache size in MB
    func getCacheSize() -> Double {
        guard let files = try? fileManager.contentsOfDirectory(at: cacheDirectory, includingPropertiesForKeys: [.fileSizeKey]) else {
            return 0
        }
        
        let totalSize = files.reduce(0) { total, url in
            let size = (try? url.resourceValues(forKeys: [.fileSizeKey]))?.fileSize ?? 0
            return total + size
        }
        
        return Double(totalSize) / (1024 * 1024) // Convert to MB
    }
}
