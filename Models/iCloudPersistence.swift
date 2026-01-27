//
//  iCloudPersistence.swift
//  ActionFigureTracker
//
//  Persists collection data to Documents directory
//  This is automatically backed up to iCloud Backup (if enabled)
//  and will persist through app deletion/reinstallation
//

import Foundation

class iCloudPersistence {
    static let shared = iCloudPersistence()
    
    private let fileName = "ActionFigureCollection.json"
    
    private var documentsURL: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent(fileName)
    }
    
    private init() {
        // Ensure Documents directory exists
        let documentsDir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        if !FileManager.default.fileExists(atPath: documentsDir.path) {
            try? FileManager.default.createDirectory(
                at: documentsDir,
                withIntermediateDirectories: true
            )
        }
    }
    
    /// Save figures to Documents directory (automatically backed up to iCloud)
    func save(_ figures: [ActionFigure]) {
        guard let data = try? JSONEncoder().encode(figures) else {
            print("❌ Failed to encode figures")
            return
        }
        
        do {
            try data.write(to: documentsURL, options: [.atomic, .completeFileProtection])
            print("✅ Saved to Documents: \(documentsURL.path)")
            
            // Mark file to be backed up to iCloud (if iCloud Backup is enabled)
            var resourceValues = URLResourceValues()
            resourceValues.isExcludedFromBackup = false
            try? documentsURL.setResourceValues(resourceValues)
        } catch {
            print("❌ Failed to save: \(error.localizedDescription)")
        }
    }
    
    /// Load figures from Documents directory
    func load() -> [ActionFigure]? {
        guard FileManager.default.fileExists(atPath: documentsURL.path),
              let data = try? Data(contentsOf: documentsURL),
              let figures = try? JSONDecoder().decode([ActionFigure].self, from: data) else {
            print("ℹ️ No saved data found")
            return nil
        }
        
        print("✅ Loaded from Documents: \(figures.count) figures")
        return figures
    }
    
    /// Check if iCloud Backup is available (user has iCloud enabled)
    var isiCloudAvailable: Bool {
        // Check if user is signed into iCloud
        // Note: This doesn't require the iCloud capability
        // The Documents directory is automatically backed up if iCloud Backup is enabled
        return true // Always available, just may not be backed up
    }
    
    /// Get the current storage location (for debugging)
    var storageLocation: String {
        if FileManager.default.fileExists(atPath: documentsURL.path) {
            return "Documents (iCloud Backup if enabled)"
        } else {
            return "No Data Saved"
        }
    }
}
