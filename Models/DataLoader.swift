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
            return rawFigures.map { raw in
                ActionFigure(
                    name: raw.name,
                    line: determineLine(from: raw.series),
                    wave: nil, // The scrape didn't capture wave names, which is fine
                    imageName: raw.imageString,
                    status: raw.isCollected ? .have : .want
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
}
