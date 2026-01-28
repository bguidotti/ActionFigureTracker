//
//  FigureDataStore.swift
//  ActionFigureTracker
//
//  Manages all figure data with persistence
//

import Foundation
import SwiftUI
import Combine

class FigureDataStore: ObservableObject {
    @Published var figures: [ActionFigure] = []
    
    init() {
        loadFigures()
        
        // If no saved data, load from the JSON file
        if figures.isEmpty {
            figures = DataLoader.loadFigures()
            saveFigures()
        } else {
            // Migrate existing data: add year information from JSON if missing
            migrateYearDataIfNeeded()
        }
    }
    
    /// Migrate existing saved data to include year information from JSON
    private func migrateYearDataIfNeeded() {
        // Check if any figures are missing year data
        let needsMigration = figures.contains { $0.year == nil }
        
        if needsMigration {
            // Load fresh data from JSON to get year information
            let jsonFigures = DataLoader.loadFigures()
            
            // Create a lookup by name and line
            var yearLookup: [String: Int] = [:]
            for jsonFig in jsonFigures {
                if let year = jsonFig.year {
                    let key = "\(jsonFig.name)|\(jsonFig.line.rawValue)"
                    yearLookup[key] = year
                }
            }
            
            // Update existing figures with year data
            var updated = false
            for i in 0..<figures.count {
                let key = "\(figures[i].name)|\(figures[i].line.rawValue)"
                if figures[i].year == nil, let year = yearLookup[key] {
                    figures[i].year = year
                    // Also update dateAdded based on year to ensure proper sorting
                    let calendar = Calendar.current
                    var components = DateComponents()
                    components.year = year
                    components.month = 1
                    components.day = 1
                    if let newDate = calendar.date(from: components) {
                        figures[i].dateAdded = newDate.addingTimeInterval(TimeInterval(i % 86400))
                    }
                    updated = true
                }
            }
            
            if updated {
                saveFigures()
                print("✅ Migrated year data for existing figures")
            }
        }
    }
    
    // MARK: - Filtering
    
    func figures(for line: FigureLine?) -> [ActionFigure] {
        guard let line = line else { return figures }
        return figures.filter { $0.line == line }
    }
    
    func figures(with status: CollectionStatus) -> [ActionFigure] {
        figures.filter { $0.status == status }
    }
    
    func figures(for line: FigureLine?, status: CollectionStatus?) -> [ActionFigure] {
        var result = figures
        
        if let line = line {
            result = result.filter { $0.line == line }
        }
        
        if let status = status {
            result = result.filter { $0.status == status }
        }
        
        // Don't sort here - let the views handle sorting based on user preference
        return result
    }
    
    func favorites() -> [ActionFigure] {
        figures.filter { $0.isFavorite }
    }
    
    // MARK: - Counts
    
    func count(for line: FigureLine, status: CollectionStatus) -> Int {
        figures.filter { $0.line == line && $0.status == status }.count
    }
    
    var totalHave: Int {
        figures.filter { $0.status == .have }.count
    }
    
    var totalWant: Int {
        figures.filter { $0.status == .want }.count
    }
    
    // MARK: - Actions
    
    func toggleStatus(for figure: ActionFigure) {
        if let index = figures.firstIndex(where: { $0.id == figure.id }) {
            figures[index].status = figures[index].status == .have ? .want : .have
            saveFigures()
        }
    }
    
    func toggleFavorite(for figure: ActionFigure) {
        if let index = figures.firstIndex(where: { $0.id == figure.id }) {
            figures[index].isFavorite.toggle()
            saveFigures()
        }
    }
    
    func updateNotes(for figure: ActionFigure, notes: String) {
        if let index = figures.firstIndex(where: { $0.id == figure.id }) {
            figures[index].notes = notes
            saveFigures()
        }
    }
    
    func addFigure(_ figure: ActionFigure) {
        figures.append(figure)
        saveFigures()
    }
    
    func deleteFigure(_ figure: ActionFigure) {
        figures.removeAll { $0.id == figure.id }
        saveFigures()
    }
    
    // MARK: - Persistence
    
    private func saveFigures() {
        // Save to iCloud (with local fallback)
        iCloudPersistence.shared.save(figures)
    }
    
    private func loadFigures() {
        // Try to load from iCloud/local storage
        if let savedFigures = iCloudPersistence.shared.load() {
            figures = savedFigures
        }
    }
    
    /// Reset to mock data (useful for testing)
    /// Reset to data from JSON file
    func resetToMockData() {
        figures = DataLoader.loadFigures()
        saveFigures()
    }
    
    /// Manually sync from iCloud (useful if data changed on another device)
    func syncFromiCloud() {
        loadFigures()
    }
    
    /// Get iCloud status info
    var iCloudStatus: (isAvailable: Bool, location: String) {
        (
            isAvailable: iCloudPersistence.shared.isiCloudAvailable,
            location: iCloudPersistence.shared.storageLocation
        )
    }
}
