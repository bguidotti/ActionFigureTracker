//
//  DataLoader.swift
//  ActionFigureTracker
//
//  Created by guidotti on 1/25/26.
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
                    status: .want
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
        if lower.contains("master") || lower.contains("motu") { return .mastersOfTheUniverse }
        if lower.contains("marvel") { return .marvelLegends }
        return .dcMultiverse // Default to DC
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
