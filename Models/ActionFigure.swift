//
//  ActionFigure.swift
//  ActionFigureTracker
//
//  Data model for action figures
//

import Foundation

/// The different action figure lines your son collects
enum FigureLine: String, CaseIterable, Codable, Identifiable {
    case dcMultiverse = "DC Multiverse"
    case mastersOfTheUniverse = "Masters of the Universe"
    case marvelLegends = "Marvel Legends"
    
    var id: String { rawValue }
    
    /// Fun emoji for each line
    var emoji: String {
        switch self {
        case .dcMultiverse: return "🦇"
        case .mastersOfTheUniverse: return "⚔️"
        case .marvelLegends: return "🕷️"
        }
    }
    
    /// Brand color for each line
    var colorName: String {
        switch self {
        case .dcMultiverse: return "DCBlue"
        case .mastersOfTheUniverse: return "MOTUGold"
        case .marvelLegends: return "MarvelRed"
        }
    }
}

/// Collection status - simple for kids!
enum CollectionStatus: String, Codable, CaseIterable {
    case want = "I Want It!"
    case have = "I Have It!"
    
    var emoji: String {
        switch self {
        case .want: return "⭐"
        case .have: return "✅"
        }
    }
}

/// Main action figure model
struct ActionFigure: Identifiable, Codable {
    let id: UUID
    var name: String
    var line: FigureLine
    var wave: String?           // e.g., "Wave 1", "BAF Bane Wave"
    var imageName: String       // Name of image in Assets
    var status: CollectionStatus
    var notes: String
    var isFavorite: Bool
    var dateAdded: Date
    
    init(
        id: UUID = UUID(),
        name: String,
        line: FigureLine,
        wave: String? = nil,
        imageName: String,
        status: CollectionStatus = .want,
        notes: String = "",
        isFavorite: Bool = false,
        dateAdded: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.line = line
        self.wave = wave
        self.imageName = imageName
        self.status = status
        self.notes = notes
        self.isFavorite = isFavorite
        self.dateAdded = dateAdded
    }
}
