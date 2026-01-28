//
//  DataLoader.swift
//  ActionFigureTracker
//
//  Loads action figure data from all_figures.json
//

import Foundation

class DataLoader {
    static func loadFigures() -> [ActionFigure] {
        // 1. Find the file in your app bundle
        guard let url = Bundle.main.url(forResource: "all_figures", withExtension: "json") else {
            print("❌ Could not find all_figures.json in bundle.")
            return []
        }
        
        do {
            // 2. Load the data
            let data = try Data(contentsOf: url)
            let decoder = JSONDecoder()
            
            // 3. Decode into a temporary struct that matches your JSON exactly
            let rawFigures = try decoder.decode([RawFigure].self, from: data)
            
            // 4. Convert to your app's ActionFigure format
            // Use year field to preserve CSV order, or position for figures without year
            let calendar = Calendar.current
            let baseDateForNoYear = Date()
            
            return rawFigures.enumerated().map { index, raw in
                // Create date based on year (preserves CSV order) or use position for figures without year
                let dateAdded: Date
                if let year = raw.year {
                    // Use year to create a date - this preserves the CSV order
                    // Use January 1st of that year, with a small offset based on index to maintain order within same year
                    var components = DateComponents()
                    components.year = year
                    components.month = 1
                    components.day = 1
                    components.hour = 0
                    components.minute = 0
                    components.second = index % 86400 // Small offset to maintain order within same year
                    dateAdded = calendar.date(from: components) ?? baseDateForNoYear.addingTimeInterval(TimeInterval(-index))
                } else {
                    // For figures without year, use a date far in the future so they appear after dated figures
                    // But maintain their relative order
                    dateAdded = baseDateForNoYear.addingTimeInterval(TimeInterval(1000000 - index))
                }
                
                return ActionFigure(
                    name: raw.name,
                    line: determineLine(from: raw.series),
                    wave: raw.wave, // Preserve wave from CSV
                    imageName: raw.imageString,
                    status: raw.isCollected ? .have : .want,
                    accessories: raw.accessories, // Preserve accessories from CSV
                    dateAdded: dateAdded,
                    year: raw.year // Preserve year from CSV
                )
            }
        } catch {
            print("❌ Error decoding JSON: \(error)")
            return []
        }
    }
    
    // Helper to map the JSON strings to your Enums
    static func determineLine(from seriesString: String) -> FigureLine {
        let lower = seriesString.lowercased()
        
        // Check for MOTU Origins first (most specific)
        if lower.contains("masters-of-the-universe-origins") || lower == "masters-of-the-universe-origins" {
            return .motuOrigins
        }
        
        // Check for MOTU Masterverse
        if lower.contains("masters-of-the-universe-masterverse") || lower == "masters-of-the-universe-masterverse" || lower.contains("masterverse") {
            return .motuMasterverse
        }
        
        // Check for DC Page Punchers
        if lower == "dc-page-punchers" || lower.contains("dc-page-punchers") || lower.contains("page-punchers") {
            return .dcPagePunchers
        }
        
        // Check for DC Super Powers
        if lower == "dc-super-powers" || lower.contains("dc-super-powers") {
            return .dcSuperPowers
        }
        
        // Check for DC Retro
        if lower == "dc-retro" || lower.contains("dc-retro") {
            return .dcRetro
        }
        
        // Check for DC Direct
        if lower == "dc-direct" || lower.contains("dc-direct") {
            return .dcDirect
        }
        
        // Check for Star Wars Black Series
        if lower == "star-wars-black-series" || lower.contains("star-wars-black-series") {
            return .starWarsBlackSeries
        }
        
        // Check for Marvel Legends
        if lower == "marvel-legends" || lower.contains("marvel-legends") {
            return .marvelLegends
        }
        
        // Default to DC Multiverse (handles "dc-multiverse")
        return .dcMultiverse
    }
}

// This matches the specific format of your scraped file
struct RawFigure: Codable {
    let id: Int
    let name: String
    let series: String
    let imageString: String
    let isCollected: Bool
    let year: Int?          // Optional: Year from CSV
    let wave: String?       // Optional: Wave from CSV
    let accessories: String? // Optional: Accessories from CSV
}
